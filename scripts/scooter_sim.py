"""
Planar (side-view) multibody simulation of an e-scooter and rider crossing a pothole.

Built with MuJoCo. Structure follows the Imperial College e-scooter fall study
(Posirisuk, Baker & Ghajari, Accident Analysis & Prevention, 2022: front wheel and the
rest of the scooter as rigid bodies joined at the axle), extended with a rear wheel and
a rider so that "larger front wheel only" and "larger wheels front and back" differ.

Bodies (all move in the x-z plane)
  chassis      deck + stem + handlebar, free to move in x, z and pitch
  front wheel  rigid cylinder, revolute joint at the front axle
  rear wheel   rigid cylinder, revolute joint at the rear axle
  rider        rigid body pinned to the deck at the feet; a rotational spring-damper
               at that pin stands for the rider bracing with legs and arms
No motor (the rider coasts through the pothole), no steering, no suspension: this is
a worst case for the pitch-over mechanism only. Steering loss is NOT modelled.

Road: flat, with a rectangular, sharp-edged pothole (depth d, length w along travel),
or with OBSTACLE = "bump" a raised bump instead: sharp-edged box, or round-top arc hump
(BUMP_SHAPE; arc needs the profile contact). See SIMULATION_METHODS.md 3.15.
Contact: MuJoCo soft contact; the solref time constant stands in for tyre compliance.

Outcomes per run
  rider_lean_max_deg     peak forward lean of the rider relative to the deck
  chassis_pitch_max_deg  peak nose-down pitch of the scooter
  speed_loss_pct         largest drop in chassis forward speed while crossing
  handlebar_peak_g       peak vertical acceleration at the handlebar (gravity removed),
                         averaged into 10 ms windows to mimic the phone's 100 Hz sampling
  fall                   rider lean > FALL_LEAN_DEG, or pitch > FALL_PITCH_DEG, or the
                         scooter stalls (forward speed < STALL_MS)
These criteria are set by the analyst, not taken from injury literature; the
comparison between wheel configurations is the result, not the absolute threshold.

Parameter values marked ASSUMED are not published by Voi.

Usage
    python scripts/scooter_sim.py                   # full sweep -> outputs/scooter_sim/
    python scripts/scooter_sim.py --animate         # also write GIFs of example runs
    python scripts/scooter_sim.py --bumps [--suspension]   # road bump study
"""

import argparse
import itertools
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np
import pandas as pd

G = 9.81
INCH = 0.0254

# ---- Vehicle and rider (ASSUMED unless noted) ----
SCOOTER_MASS = 32.0          # kg, ASSUMED (Voiager 7 is reported at 36 kg)
WHEELBASE = 0.95             # m, ASSUMED, typical for shared e-scooters
DECK_HEIGHT = 0.16           # m above ground with 10 in wheels, ASSUMED
HANDLEBAR_HEIGHT = 1.05      # m above ground, ASSUMED
WHEEL_MASS = 2.5             # kg per 10 in wheel incl. hub motor share, ASSUMED
SCALE_WHEEL_MASS = False     # True: wheel mass grows with diameter (sensitivity check)
WHEEL_WIDTH = 0.06           # m
RIDER_MASS = 76.0            # kg, 50th percentile male as in the Imperial study
RIDER_HEIGHT = 1.70          # m, as in the Imperial study
RIDER_COM_FRAC = 0.55        # CoM height as a fraction of stature (standing)
RIDER_FOOT_X = 0.0           # rider stands mid-deck (x relative to deck centre)
RIDER_STIFFNESS = 1500.0     # N m/rad at the feet: ~8 deg lean under 0.3 g braking
RIDER_DAMPING = 150.0        # N m s/rad
FRICTION = 0.9               # tyre-asphalt, dry
# MuJoCo contact time constant standing in for a pneumatic tyre. With tau = 0.025 s the
# contact behaves like a spring of ~m/tau^2: ~80 kN/m for ~50 kg on the front wheel and
# a static deflection of g*tau^2 ~ 6 mm, typical of a small pneumatic tyre. ASSUMED.
TYRE_TIMECONST = 0.025

# ---- Scenario ----
CONFIGS = [  # (label, front diameter in, rear diameter in)
    ("10/10 in (current, Voiager 5)", 10, 10),
    ("12/10 in (larger front only)", 12, 10),
    ("12/12 in (larger both)", 12, 12),
    ("14/10 in (larger front only)", 14, 10),
]
SPEEDS_KMH = [15.0, 20.0, 25.0]
DEPTHS_MM = [20, 30, 40, 50, 60, 70, 80, 90, 100]
LENGTHS_MM = [300, 600, 1000]
POTHOLE_X = 5.0              # m, start of pothole: ~1 s run-up so launch transients decay

# ---- Fall criteria (analyst-defined, fixed before running) ----
FALL_LEAN_DEG = 30.0
FALL_PITCH_DEG = 30.0
STALL_MS = 0.5

TIMESTEP = 0.0005

# ---- Front suspension option (off = original baseline model) ----
# Values fixed before any run with them, from typical small-scooter hardware. ASSUMED.
SUSPENSION = False           # front spring fork (the Voiager 5 has a front spring)
FORK_STIFFNESS = 25000.0     # N/m, typical small e-scooter fork spring
FORK_DAMPING_RATIO = 0.3     # light: spring forks have little damping
FORK_TRAVEL = 0.030          # m of compression available
PHONE_DT = 0.01              # s, average into windows like the 100 Hz phone log

# ---- Tyre-road contact model ----
# "mujoco":  MuJoCo's own collision between wheel cylinders and road boxes (original;
#            sharp-edged potholes only).
# "profile": our own tyre contact against a road height profile, so pothole edges can
#            have any shape. Each step, for each wheel, the nearest point of the profile
#            to the wheel centre is found; if the wheel overlaps the road by delta, a
#            force F = k*delta + c*delta_dot acts along the line from that point to the
#            centre (radial-spring point contact; no tangential force, i.e. free rolling).
#            One contact per wheel, so no multi-contact stiffening or facet effects.
CONTACT_MODEL = "mujoco"
EDGE_WIDTH = 0.0             # m, "profile" only: width of each sloped pothole edge (0 = sharp)
TYRE_STIFFNESS = 80000.0     # N/m, "profile" only: ~6.5 mm static deflection on the front, ASSUMED
TYRE_DAMPING = 500.0         # N s/m, "profile" only: light, as for a pneumatic tyre, ASSUMED
PROFILE_DX = 0.0005          # m, sampling of the road profile

# ---- Obstacle: a pothole (below the road) or a bump (above it) ----
# For a bump, simulate()'s depth_mm is the bump HEIGHT and length_mm its length along
# travel. Shapes:
#   "box": sharp-edged rectangular bump (raised patch or utility cover, lifted slab, tree
#          root ridge); either contact model, and EDGE_WIDTH ramps with "profile".
#   "arc": round-top hump, a circular arc from x0 to x1 (UK round-top road hump, short
#          car-park speed bump); "profile" contact only.
OBSTACLE = "pothole"         # "pothole" or "bump"
BUMP_SHAPE = "box"


def wheel_mass(d_in):
    """Wheel mass (kg): fixed, or proportional to diameter when SCALE_WHEEL_MASS."""
    return WHEEL_MASS * (d_in / 10) if SCALE_WHEEL_MASS else WHEEL_MASS



def road_geoms(x0, x1, depth):
    """Road with a sharp-edged rectangular pothole from x0 to x1 (three boxes), or, if
    OBSTACLE == "bump", a flat road with a box of height `depth` on top from x0 to x1.

    Rounded edges were tried (separate primitives, then a single convex mesh) and
    dropped: both gave numerical artefacts (stiffened multi-contacts; results changing
    with mesh resolution without converging). See SIMULATION_METHODS.md.
    """
    if OBSTACLE == "bump":
        if BUMP_SHAPE != "box":
            if CONTACT_MODEL != "profile":
                raise ValueError("MuJoCo contact supports box bumps only; use CONTACT_MODEL='profile'")
            # Wheels use the profile; the boxes only catch the deck, whose clearance
            # (>= 140 mm) exceeds every arc hump modelled (<= 100 mm): a flat road.
            return f'    <geom name="road" type="box" pos="{(x1 + 20) / 2} 0 -0.25" size="{(x1 + 40) / 2} 1 0.25"/>'
        return "\n".join("    " + x for x in (
            f'<geom name="road" type="box" pos="{(x1 + 20) / 2} 0 -0.25" size="{(x1 + 40) / 2} 1 0.25"/>',
            f'<geom name="bump" type="box" pos="{(x0 + x1) / 2} 0 {depth / 2}" '
            f'size="{(x1 - x0) / 2} 1 {depth / 2}"/>'))
    return "\n".join("    " + x for x in (
        f'<geom name="road_in"  type="box" pos="{(x0 - 10) / 2} 0 -0.25" size="{(x0 + 10) / 2} 1 0.25"/>',
        f'<geom name="hole"     type="box" pos="{(x0 + x1) / 2} 0 {-depth - 0.25}" '
        f'size="{(x1 - x0) / 2} 1 0.25"/>',
        f'<geom name="road_out" type="box" pos="{x1 + 15} 0 -0.25" size="15 1 0.25"/>'))


def road_profile(x0, x1, depth, edge_width=None, dx=None):
    """Road surface as sampled points (x, z), sorted by x, for the "profile" contact.

    The pothole runs from x0 to x1 (top opening) with depth `depth`; for a bump
    (OBSTACLE == "bump") the same shape is raised by `depth` instead, or, with
    BUMP_SHAPE == "arc", the bump is a circular arc of height `depth` over x0..x1.
    Each edge falls
    over a horizontal width b = edge_width with a raised-cosine shape (smooth, slope
    zero at top and bottom, steepest mid-way: max slope = pi*d/(2b)). b = 0 gives the
    original sharp, vertical edges; vertical wall points are then added so the wheel
    can also touch the walls. b is capped at half the pothole length.
    """
    b = EDGE_WIDTH if edge_width is None else edge_width
    dx = PROFILE_DX if dx is None else dx
    b = min(b, (x1 - x0) / 2)
    x = np.arange(-3.0, x1 + 40.0, dx)   # from behind the start to well past the run's end
    z = np.zeros_like(x)
    inside = (x > x0) & (x < x1)
    off = depth if OBSTACLE == "bump" else -depth    # height of the obstacle's surface
    if OBSTACLE == "bump" and BUMP_SHAPE == "arc":
        half, xc = (x1 - x0) / 2, (x0 + x1) / 2
        rho = (half ** 2 + depth ** 2) / (2 * depth)  # radius of the arc
        z[inside] = np.sqrt(rho ** 2 - (x[inside] - xc) ** 2) - (rho - depth)
        return x, z
    z[inside] = off
    if b > 0:
        e_in = (x >= x0) & (x <= x0 + b)
        z[e_in] = off * (1 - np.cos(np.pi * (x[e_in] - x0) / b)) / 2
        e_out = (x >= x1 - b) & (x <= x1)
        z[e_out] = off * (1 - np.cos(np.pi * (x1 - x[e_out]) / b)) / 2
        return x, z
    # Sharp edges: add the corners exactly and points along each vertical wall.
    wz = np.arange(0.0, off - 1e-12 * np.sign(off), dx * np.sign(off))
    wx = np.concatenate([np.full_like(wz, x0), np.full_like(wz, x1)])
    wz = np.concatenate([wz, wz])
    x, z = np.concatenate([x, wx]), np.concatenate([z, wz])
    order = np.argsort(x, kind="stable")
    return x[order], z[order]


class ProfileTyres:
    """Radial-spring point contact between the wheels and a road profile.

    Applies the contact force as an external force at each wheel centre
    (data.xfrc_applied), recomputed before every simulation step. The force acts along
    the line from the nearest road point to the wheel centre, so it has no moment about
    the axle (free rolling, no tangential friction).
    """

    def __init__(self, model, data, px, pz, wheels):
        self.m, self.d, self.px, self.pz = model, data, px, pz
        self.wheels = wheels                         # [(body_id, radius), ...]
        self._vel = np.zeros(6)

    def apply(self):
        for b, R in self.wheels:
            cx, cz = self.d.xpos[b][0], self.d.xpos[b][2]
            i = np.searchsorted(self.px, cx - R - 0.005)
            j = np.searchsorted(self.px, cx + R + 0.005)
            if j <= i:                                    # beyond the profile: flat road
                dxs, dzs = np.array([0.0]), np.array([cz])
            else:
                dxs, dzs = cx - self.px[i:j], cz - self.pz[i:j]
            dist = np.hypot(dxs, dzs)
            k = int(np.argmin(dist))
            delta = R - dist[k]
            self.d.xfrc_applied[b, :] = 0.0
            if delta <= 0:
                continue
            n = np.array([dxs[k], dzs[k]]) / dist[k]          # unit normal, road -> centre
            mujoco.mj_objectVelocity(self.m, self.d, mujoco.mjtObj.mjOBJ_BODY, b, self._vel, 0)
            v_n = self._vel[3] * n[0] + self._vel[5] * n[1]   # centre velocity along n
            f = max(0.0, TYRE_STIFFNESS * delta - TYRE_DAMPING * v_n)
            self.d.xfrc_applied[b, 0] = f * n[0]
            self.d.xfrc_applied[b, 2] = f * n[1]


def front_assembly(xf, Rf, d_front_in):
    """Front wheel, either fixed to the chassis or on a sprung fork (slide joint along
    z, compression positive). The spring is preloaded with the front's static load so
    the whole travel is available; the handlebar stays on the sprung chassis.
    With the fork, the wheel is no longer a direct child of the chassis, so their
    contact must be excluded explicitly (build_xml adds the <exclude>)."""
    wheel = (f'<joint name="front_axle" type="hinge" axis="0 1 0"/>\n'
             f'        <geom type="cylinder" size="{Rf} {WHEEL_WIDTH / 2}" zaxis="0 1 0" '
             f'mass="{wheel_mass(d_front_in)}"{wheel_collision()}/>')
    if not SUSPENSION:
        return f'<body name="front_wheel" pos="{xf} 0 {Rf}">\n        {wheel}\n      </body>'
    sprung = SCOOTER_MASS - 2 * WHEEL_MASS + RIDER_MASS
    load = 0.5 * sprung * G                      # front share of the sprung weight, ASSUMED 50%
    damping = 2 * FORK_DAMPING_RATIO * np.sqrt(FORK_STIFFNESS * 0.5 * sprung)
    return (f'<body name="fork" pos="{xf} 0 {Rf}">\n'
            f'        <joint name="fork" type="slide" axis="0 0 1" stiffness="{FORK_STIFFNESS}" '
            f'springref="{-load / FORK_STIFFNESS}" damping="{damping}" limited="true" '
            f'range="-0.005 {FORK_TRAVEL}"/>\n'
            f'        <inertial pos="0 0 0" mass="0.5" diaginertia="0.001 0.001 0.001"/>\n'
            f'        <body name="front_wheel" pos="0 0 0">\n          {wheel}\n        </body>\n'
            f'      </body>')


def wheel_collision():
    """With the profile contact, MuJoCo must not also collide the wheels with the road
    (the deck still collides with the road boxes)."""
    return ' contype="0" conaffinity="0"' if CONTACT_MODEL == "profile" else ""


def build_xml(d_front_in, d_rear_in, depth_m, length_m):
    Rf, Rr = d_front_in * INCH / 2, d_rear_in * INCH / 2
    L = WHEELBASE
    # Chassis frame origin: midway between axles at ground level (z = 0).
    xf, xr = L / 2, -L / 2
    deck_z = DECK_HEIGHT + (Rr + Rf) / 2 - 10 * INCH / 2  # deck rises with wheel size
    chassis_mass = SCOOTER_MASS - 2 * WHEEL_MASS  # frame mass fixed; wheels added on top
    rider_com_z = RIDER_HEIGHT * RIDER_COM_FRAC
    x0, x1 = POTHOLE_X, POTHOLE_X + length_m
    return f"""
<mujoco model="scooter">
  <option timestep="{TIMESTEP}" gravity="0 0 -{G}" integrator="implicitfast"/>
  <default>
    <geom friction="{FRICTION} 0.005 0.0001" solref="{TYRE_TIMECONST} 1" solimp="0.9 0.95 0.001"
          condim="3"/>
  </default>
  <worldbody>
{road_geoms(x0, x1, depth_m)}

    <body name="chassis" pos="0 0 0">
      <joint name="x"     type="slide" axis="1 0 0"/>
      <joint name="z"     type="slide" axis="0 0 1"/>
      <joint name="pitch" type="hinge" axis="0 1 0"/>
      <inertial pos="0.05 0 {deck_z + 0.15}" mass="{chassis_mass}" diaginertia="0.6 1.2 0.8"/>
      <geom name="deck" type="box" pos="0 0 {deck_z}" size="{L / 2 - 0.1} 0.08 0.02"
            contype="1" conaffinity="1" mass="0"/>
      <geom name="stem" type="capsule" fromto="{xf} 0 {Rf} {xf - 0.08} 0 {HANDLEBAR_HEIGHT}"
            size="0.02" contype="0" conaffinity="0" mass="0"/>
      <site name="handlebar" pos="{xf - 0.08} 0 {HANDLEBAR_HEIGHT}"/>

{front_assembly(xf, Rf, d_front_in)}
      <body name="rear_wheel" pos="{xr} 0 {Rr}">
        <joint name="rear_axle" type="hinge" axis="0 1 0"/>
        <geom type="cylinder" size="{Rr} {WHEEL_WIDTH / 2}" zaxis="0 1 0" mass="{wheel_mass(d_rear_in)}"{wheel_collision()}/>
      </body>

      <body name="rider" pos="{RIDER_FOOT_X} 0 {deck_z + 0.02}">
        <joint name="ankle" type="hinge" axis="0 1 0" stiffness="{RIDER_STIFFNESS}"
               damping="{RIDER_DAMPING}"/>
        <inertial pos="0 0 {rider_com_z - 0.02}" mass="{RIDER_MASS}" diaginertia="12 12 1"/>
        <geom type="capsule" fromto="0 0 0 0 0 {RIDER_HEIGHT - 0.1}" size="0.12"
              contype="0" conaffinity="0" mass="0"/>
      </body>
    </body>
  </worldbody>
{'<contact><exclude body1="chassis" body2="front_wheel"/></contact>' if SUSPENSION else ''}
  <sensor>
    <accelerometer name="bar_acc" site="handlebar"/>
  </sensor>
</mujoco>"""


def simulate(d_front_in, d_rear_in, depth_mm, length_mm, speed_kmh, record=False):
    depth, length, v = depth_mm / 1000, length_mm / 1000, speed_kmh / 3.6
    model = mujoco.MjModel.from_xml_string(build_xml(d_front_in, d_rear_in, depth, length))
    data = mujoco.MjData(model)
    Rf, Rr = d_front_in * INCH / 2, d_rear_in * INCH / 2
    jid = {n: model.joint(n).dofadr[0] for n in ("x", "z", "pitch", "front_axle", "rear_axle", "ankle")}

    tyres = None
    if CONTACT_MODEL == "profile":
        px, pz = road_profile(POTHOLE_X, POTHOLE_X + length, depth)
        tyres = ProfileTyres(model, data, px, pz,
                             [(model.body("front_wheel").id, Rf), (model.body("rear_wheel").id, Rr)])
        mujoco.mj_forward(model, data)

    def step():
        if tyres is not None:
            tyres.apply()
        mujoco.mj_step(model, data)

    # Settle on the road at rest, then launch at speed with rolling wheels.
    for _ in range(int(0.5 / TIMESTEP)):
        step()
    data.qvel[:] = 0
    data.qvel[jid["x"]] = v
    data.qvel[jid["front_axle"]] = v / Rf
    data.qvel[jid["rear_axle"]] = v / Rr
    x_start = data.qpos[model.joint("x").qposadr[0]]

    clear_x = POTHOLE_X + length + WHEELBASE + 1.0  # rear wheel well past the hole
    t_end = (clear_x - x_start) / max(v, 0.1) + 1.5
    site = model.site("handlebar").id
    qx, qp, qa = (model.joint(n).qposadr[0] for n in ("x", "pitch", "ankle"))

    t_log, ax_log, vx_log, pitch_log, lean_log, frames = [], [], [], [], [], []
    phase_log, near_pitch, near_lean, rear_z, rear_x = [], [], [], [], []
    rb = model.body("rear_wheel").id
    rear_z_rest = data.xpos[rb][2]
    # Bumps: horizontal distance at which a wheel of radius Rr first touches the bump's
    # leading face (step of height `depth`); used for phases and fall attribution.
    rear_reach = np.sqrt(Rr ** 2 - (Rr - min(depth, Rr)) ** 2)
    vx_min = v
    n_steps = int(t_end / TIMESTEP)
    for k in range(n_steps):
        step()
        vx = data.qvel[jid["x"]]
        pitch_log.append(np.degrees(data.qpos[qp]))       # +ve = nose down (about +y)
        lean_log.append(np.degrees(data.qpos[qa]))        # +ve = rider leans forward
        if data.qpos[qx] > POTHOLE_X - WHEELBASE:          # judge only near the hole, so
            vx_min = min(vx_min, vx)                      # the launch transient is ignored
            R = data.site_xmat[site].reshape(3, 3)
            a_world = R @ data.sensordata[:3]
            t_log.append(data.time)
            ax_log.append(a_world[2] - G)                 # vertical, gravity removed
            vx_log.append(vx)
            # Phase by the far edge, where the impacts happen: "front" until the front
            # wheel is half a wheelbase past it (front wheel's climb-out and its
            # aftermath), then "rear" (the rear wheel's climb-out).
            # Bumps: "rear" from the moment the rear tyre reaches the bump, since the
            # rear wheel's strike on the leading face is the second impact.
            if OBSTACLE == "bump":
                rear_on = data.xpos[rb][0] + rear_reach >= POTHOLE_X
                phase_log.append("rear" if rear_on else "front")
            else:
                front_x = data.qpos[qx] + WHEELBASE / 2
                phase_log.append("front" if front_x < POTHOLE_X + length + WHEELBASE / 2 else "rear")
            near_pitch.append(pitch_log[-1])
            near_lean.append(lean_log[-1])
            rear_z.append(data.xpos[rb][2])
            rear_x.append(data.xpos[rb][0])
        front_x = data.qpos[qx] + WHEELBASE / 2
        if (record and k % int(0.01 / TIMESTEP) == 0
                and POTHOLE_X - 1.0 < front_x < POTHOLE_X + length + WHEELBASE + 1.5):
            frames.append((data.qpos.copy(), data.time))   # only around the pothole
        if abs(pitch_log[-1]) > 80 or abs(lean_log[-1]) > 80:
            break                                         # clearly fallen; stop early

    a = np.array(ax_log)
    win = int(PHONE_DT / TIMESTEP)
    a_phone = a[: len(a) // win * win].reshape(-1, win).mean(1)
    lean_max = max(lean_log)
    pitch_max = max(pitch_log)
    stalled = vx_min < STALL_MS
    out = {
        "front_in": d_front_in, "rear_in": d_rear_in, "depth_mm": depth_mm,
        "length_mm": length_mm, "speed_kmh": speed_kmh,
        "rider_lean_max_deg": round(lean_max, 2), "chassis_pitch_max_deg": round(pitch_max, 2),
        "speed_loss_pct": round(min(100.0, 100 * (1 - vx_min / v)), 1),  # >100 = bounced back
        "handlebar_peak_g": round(np.abs(a_phone).max() / G, 2),
        "stalled": stalled,
        "fall": bool(lean_max > FALL_LEAN_DEG or pitch_max > FALL_PITCH_DEG or stalled),
        # Backward (nose-up / rider leaning back) extremes: not fall criteria, recorded
        # to check that bumps don't cause a backward failure the criteria would miss.
        "rider_lean_back_max_deg": round(-min(lean_log), 2),
        "chassis_pitch_up_max_deg": round(-min(pitch_log), 2),
        "obstacle": OBSTACLE if OBSTACLE == "pothole" else f"bump_{BUMP_SHAPE}",
    }
    # Per-phase outcomes: what the front wheel's crossing does vs the rear wheel's.
    ph = np.array(phase_log)
    vxa, pa, la = np.array(vx_log), np.array(near_pitch), np.array(near_lean)
    a_full = np.abs(a)
    # Which wheel's impact caused the fall: "rear" only if the rear wheel had actually
    # dropped into the pothole before the fall criterion was met; otherwise the fall is
    # the forward pitch-over started by the front-wheel impact (the rear wheel is lifted
    # clear). Classifying by time alone mislabels slow pitch-overs as "rear".
    fell_at = None
    bad = (la > FALL_LEAN_DEG) | (pa > FALL_PITCH_DEG) | (vxa < STALL_MS)
    if bad.any():
        i_fall = bad.argmax()
        if OBSTACLE == "bump":
            # A bump: "rear" only if the rear tyre had reached the bump's leading face
            # (horizontal reach of a wheel of radius Rr to a step of height h) before
            # the fall; the front impact lifts the rear rather than dropping it.
            fell_at = "rear" if max(rear_x[: i_fall + 1]) + rear_reach >= POTHOLE_X else "front"
        else:
            rz_before = np.array(rear_z[: i_fall + 1])
            fell_at = "rear" if rear_z_rest - rz_before.min() > 0.005 else "front"
    for name in ("front", "rear"):
        m = ph == name
        if m.any():
            v0 = vxa[m][0]
            out[f"{name}_speed_loss_pct"] = round(min(100.0, 100 * (1 - vxa[m].min() / v0)), 1)
            out[f"{name}_peak_g"] = round(a_full[m].max() / G, 2)   # unwindowed, relative use
            out[f"{name}_lean_max_deg"] = round(la[m].max(), 2)
        else:
            out[f"{name}_speed_loss_pct"] = out[f"{name}_peak_g"] = out[f"{name}_lean_max_deg"] = np.nan
    out["fall_phase"] = fell_at if out["fall"] else ""
    # How it fell: "stall" = the wheel could not get over the edge and the scooter
    # stopped (kerb strike) without the rider/scooter passing the angle limits first;
    # "pitch-over" = the lean or pitch limit was passed.
    out["fall_type"] = ("" if not out["fall"] else "pitch-over"
                        if lean_max > FALL_LEAN_DEG or pitch_max > FALL_PITCH_DEG else "stall")
    # Rear wheel: lifted off the road by the front impact (scooter pitching about the
    # front wheel), and how far it dipped into the pothole itself.
    rz = np.array(rear_z)
    out["rear_lift_mm"] = round(1000 * max(0.0, rz.max() - rear_z_rest), 1)
    out["rear_drop_mm"] = round(1000 * max(0.0, rear_z_rest - rz.min()), 1)
    if record:
        return out, model, frames, (Rf, Rr)
    return out


# --------------------------------------------------------------------------- figures
RAMP = {"10/10": "#86b6ef", "12/10": "#2a78d6", "12/12": "#eb6834", "14/10": "#0d366b"}
INK, MUTED = "#222222", "#6b6b6b"


def _key(r):
    return f"{int(r['front_in'])}/{int(r['rear_in'])}"


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#bbbbbb")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(color="#ececec", lw=0.6)
    ax.set_axisbelow(True)


def fig_metric(df, metric, ylabel, path, threshold=None, speed=20.0, noun="pothole",
               xlabel="Pothole depth (mm)"):
    """Metric vs depth, one panel per pothole length, one line per configuration."""
    fig, axes = plt.subplots(1, len(LENGTHS_MM), figsize=(10.5, 3.4), sharey=True)
    sub = df[df["speed_kmh"] == speed]
    for ax, w in zip(axes, LENGTHS_MM):
        for label, f, r in CONFIGS:
            s = sub[(sub["length_mm"] == w) & (sub["front_in"] == f) & (sub["rear_in"] == r)]
            k = f"{f}/{r}"
            ax.plot(s["depth_mm"], s[metric], color=RAMP[k], lw=2, marker="o", ms=4,
                    label=label, ls="--" if k == "12/12" else "-")
            f_ = s[s["fall"]]
            ax.plot(f_["depth_mm"], f_[metric], ls="none", marker="X", ms=9, color=RAMP[k],
                    markeredgecolor="white", markeredgewidth=1,
                    label="Fall" if (k == "10/10" and w == LENGTHS_MM[-1]) else None)
        if threshold is not None:
            ax.axhline(threshold, color="#999999", lw=0.9, ls=":")
        ax.set_title(f"{w} mm long {noun}", fontsize=9.5, color=INK, loc="left")
        ax.set_xlabel(xlabel)
        _style(ax)
    axes[0].set_ylabel(ylabel)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    if any(h.get_label() == "Fall" for h in axes[-1].get_lines()):
        axes[-1].legend(handles=[h for h in axes[-1].get_lines() if h.get_label() == "Fall"],
                        frameon=False, fontsize=8, loc="upper left")
    fig.suptitle(f"{speed:g} km/h, 76 kg rider", fontsize=9, color=MUTED, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fall_threshold_table(df):
    """Shallowest depth that produces a fall, per configuration, length and speed."""
    rows = []
    for (f, r, w, s), g in df.groupby(["front_in", "rear_in", "length_mm", "speed_kmh"]):
        falls = g[g["fall"]]["depth_mm"]
        rows.append({"config": f"{f}/{r} in", "length_mm": w, "speed_kmh": s,
                     "first_fall_depth_mm": falls.min() if len(falls) else np.nan})
    t = pd.DataFrame(rows).pivot_table(index=["length_mm", "speed_kmh"], columns="config",
                                       values="first_fall_depth_mm", dropna=False)
    return t


def animate(d_front_in, d_rear_in, depth_mm, length_mm, speed_kmh, path):
    """Side-view stick animation (GIF) of one run."""
    from matplotlib.animation import FuncAnimation, PillowWriter
    out, model, frames, (Rf, Rr) = simulate(d_front_in, d_rear_in, depth_mm, length_mm,
                                            speed_kmh, record=True)
    data = mujoco.MjData(model)
    d, w = depth_mm / 1000, length_mm / 1000
    fig, ax = plt.subplots(figsize=(7, 3.4))
    x0, x1 = POTHOLE_X, POTHOLE_X + w
    if CONTACT_MODEL == "profile":   # draw the actual road profile, thinned for speed
        prof_x, prof_z = road_profile(x0, x1, d, dx=0.005)

    def draw(i):
        qpos, t = frames[i]
        data.qpos[:] = qpos
        mujoco.mj_kinematics(model, data)
        ax.clear()
        if CONTACT_MODEL == "profile":
            ax.plot(prof_x, prof_z, color="#8a8984", lw=2)
        else:
            off = d if OBSTACLE == "bump" else -d
            ax.plot([-2, x0, x0, x1, x1, x1 + 4], [0, 0, off, off, 0, 0], color="#8a8984", lw=2)
        for name, R in (("front_wheel", Rf), ("rear_wheel", Rr)):
            c = data.xpos[model.body(name).id]
            ax.add_patch(plt.Circle((c[0], c[2]), R, fill=False, color="#2a78d6", lw=2))
        fw, rw = data.xpos[model.body("front_wheel").id], data.xpos[model.body("rear_wheel").id]
        hb = data.site_xpos[model.site("handlebar").id]
        ax.plot([rw[0], fw[0]], [rw[2], fw[2]], color=INK, lw=3)
        ax.plot([fw[0], hb[0]], [fw[2], hb[2]], color=INK, lw=2)
        rb = model.body("rider").id
        foot = data.xpos[rb]
        head = foot + data.xmat[rb].reshape(3, 3) @ np.array([0, 0, RIDER_HEIGHT - 0.1])
        ax.plot([foot[0], head[0]], [foot[2], head[2]], color="#eb6834", lw=6,
                solid_capstyle="round")
        ax.plot([head[0], hb[0]], [foot[2] + 0.75 * (head[2] - foot[2]), hb[2]],
                color="#eb6834", lw=2)
        cx = fw[0]
        ax.set_xlim(cx - 1.6, cx + 1.4)
        ax.set_ylim(-0.25, 2.0)
        ax.set_aspect("equal")
        ax.axis("off")
        what = ("pothole" if OBSTACLE == "pothole" else "round-top hump" if BUMP_SHAPE == "arc"
                else "bump")
        ax.set_title(f"{d_front_in}/{d_rear_in} in wheels · {depth_mm} mm × {length_mm} mm {what}\n"
                     f"{speed_kmh:g} km/h · {'front suspension · ' if SUSPENSION else ''}"
                     f"{(f'{EDGE_WIDTH * 1000:.0f} mm sloped edges · ' if EDGE_WIDTH > 0 else 'sharp edges · ') if CONTACT_MODEL == 'profile' and not (OBSTACLE == 'bump' and BUMP_SHAPE == 'arc') else ''}"
                     f"{'FALL' if out['fall'] else 'no fall'} · 4× slow motion",
                     fontsize=9, color=INK, loc="left")

    anim = FuncAnimation(fig, draw, frames=len(frames))
    anim.save(path, writer=PillowWriter(fps=25))  # 0.01 s frames at 25 fps = 4x slow motion
    plt.close(fig)
    return out


def sensitivity(out_dir):
    """Re-run the key comparison with softer/stiffer tyres and rider bracing.

    For each setting: shallowest falling depth on a 1000 mm pothole at 20 km/h, and
    forward speed lost on a 60 mm x 600 mm pothole at 20 km/h, per configuration.
    """
    global TYRE_TIMECONST, RIDER_STIFFNESS, FORK_STIFFNESS, FORK_DAMPING_RATIO
    base = (TYRE_TIMECONST, RIDER_STIFFNESS, FORK_STIFFNESS, FORK_DAMPING_RATIO)
    t, k0, fk, fz = base
    settings = [("baseline", t, k0, fk, fz),
                ("stiffer tyre (tau 0.015 s)", 0.015, k0, fk, fz),
                ("softer tyre (tau 0.035 s)", 0.035, k0, fk, fz),
                ("weaker bracing (1000 N m/rad)", t, 1000.0, fk, fz),
                ("stronger bracing (3000 N m/rad)", t, 3000.0, fk, fz)]
    if SUSPENSION:  # the fork's own assumed values
        settings += [("softer fork (15 kN/m)", t, k0, 15000.0, fz),
                     ("stiffer fork (40 kN/m)", t, k0, 40000.0, fz),
                     ("less fork damping (ratio 0.15)", t, k0, fk, 0.15),
                     ("more fork damping (ratio 0.5)", t, k0, fk, 0.5)]
    rows = []
    for name, tau, k, fork_k, fork_z in settings:
        TYRE_TIMECONST, RIDER_STIFFNESS, FORK_STIFFNESS, FORK_DAMPING_RATIO = tau, k, fork_k, fork_z
        for label, f, r in CONFIGS:
            first = next((d for d in DEPTHS_MM if simulate(f, r, d, 1000, 20.0)["fall"]), np.nan)
            loss = simulate(f, r, 60, 600, 20.0)["speed_loss_pct"]
            rows.append({"setting": name, "config": f"{f}/{r} in",
                         "first_fall_mm_1000mm_20kmh": first, "speed_loss_pct_60x600_20kmh": loss})
    TYRE_TIMECONST, RIDER_STIFFNESS, FORK_STIFFNESS, FORK_DAMPING_RATIO = base
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "sensitivity.csv", index=False)
    return df


# ---- Consistency check against the measured ride ----
MEASURED_G = (1.0, 2.8)       # range of impact peaks measured on the ride (detection floor 1 g)
MEASURED_MEDIAN_G = 1.19
COMMON_DEPTHS_MM = [20, 30, 40]   # "common" potholes for the check, fixed before running
COMMON_LENGTHS_MM = [300, 600]


def consistency(out_dir):
    """Handlebar peaks (10 ms windows, like the phone) for the current 10/10 scooter at
    20 km/h on common potholes, without and with the front suspension, compared with the
    measured range. Pass = inside roughly 1-3 g."""
    global SUSPENSION
    keep = SUSPENSION
    rows = []
    for susp in (False, True):
        SUSPENSION = susp
        for w in COMMON_LENGTHS_MM:
            for d in COMMON_DEPTHS_MM:
                rows.append({"model": "with front suspension" if susp else "no suspension",
                             "length_mm": w, "depth_mm": d,
                             "handlebar_peak_g": simulate(10, 10, d, w, 20.0)["handlebar_peak_g"]})
    SUSPENSION = keep
    df = pd.DataFrame(rows)
    df["within_1_to_3_g"] = df["handlebar_peak_g"].between(1.0, 3.0)
    df.to_csv(out_dir / "consistency.csv", index=False)

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.axhspan(*MEASURED_G, color="#eef4fc", zorder=0)
    ax.axhline(MEASURED_MEDIAN_G, color="#86b6ef", lw=1, ls=":")
    ax.text(0.99, MEASURED_G[1] + 0.08, "Shaded: measured on the ride (1.0-2.8 g), dotted = median",
            transform=ax.get_yaxis_transform(), fontsize=8.5, color=MUTED, va="bottom", ha="right")
    styles = {"no suspension": ("#b5b4ae", "o"), "with front suspension": ("#2a78d6", "s")}
    xt = [f"{d} mm\n{w} mm" for w in COMMON_LENGTHS_MM for d in COMMON_DEPTHS_MM]
    for name, (c, mk) in styles.items():
        sub = df[df["model"] == name]
        ax.plot(range(len(sub)), sub["handlebar_peak_g"], color=c, marker=mk, ms=8, lw=0,
                markeredgecolor="white", label=name)
    ax.set_xticks(range(len(xt)), xt, fontsize=8)
    ax.set_xlabel("Pothole depth / length · current 10/10 in wheels · 20 km/h")
    ax.set_ylabel("Simulated handlebar peak (g)")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0, 0.88))
    _style(ax)
    fig.tight_layout()
    fig.savefig(out_dir / "fig_consistency.png", dpi=150)
    plt.close(fig)
    return df


def write_animation_page(path, sections):
    """Self-contained HTML page of the simulation GIFs (embedded), in sections.

    sections: list of (heading, description, clips, obstacle); clips: list of
    (f, r, gif, res, note); obstacle: "pothole" or "bump" (captions).
    """
    import base64
    import html as _html
    blocks = []
    for heading, desc, clips, obstacle in sections:
        cards = []
        for f, r, gif, res, note in clips:
            b64 = base64.b64encode(gif.read_bytes()).decode()
            verdict = ("<b>No fall</b>" if not res["fall"] else
                       "<b>Falls</b>: rear wheel strikes the edge, scooter pitches forward"
                       if obstacle == "bump" and res["fall_phase"] == "rear"
                       else "<b>Falls</b>: pitches forward over the front wheel")
            if obstacle == "bump":
                rl = res["rear_speed_loss_pct"]
                rear = ("" if rl != rl else f"rear-wheel strike {rl:.0f}%") + \
                    f"{'' if rl != rl else ' · '}handlebar peak {res['handlebar_peak_g']:.1f} g"
                cards.append(f"""
        <figure>
          <img src="data:image/gif;base64,{b64}" alt="Side-view simulation, {f}/{r} inch wheels">
          <figcaption><b>{f}/{r} in</b> (front/rear) · {verdict}<br>
          Speed lost: front-wheel strike {res['front_speed_loss_pct']:.0f}% · {rear}
          {f'<br><span class="hint">{_html.escape(note)}</span>' if note else ''}</figcaption>
        </figure>""")
                continue
            else:
                rear = ("rear wheel lifted clear of the pothole" if res["rear_lift_mm"] > 20
                        and res["rear_drop_mm"] < 10 else
                        f"rear wheel dips {res['rear_drop_mm']:.0f} mm into the pothole")
            cards.append(f"""
        <figure>
          <img src="data:image/gif;base64,{b64}" alt="Side-view simulation, {f}/{r} inch wheels">
          <figcaption><b>{f}/{r} in</b> (front/rear) · {verdict}<br>
          Speed lost at front-wheel crossing {res['front_speed_loss_pct']:.0f}% ·
          {rear}{'' if res['fall'] else f", speed lost at rear crossing {res['rear_speed_loss_pct']:.0f}%"}
          {f'<br><span class="hint">{_html.escape(note)}</span>' if note else ''}</figcaption>
        </figure>""")
        blocks.append(f"""
<h2>{_html.escape(heading)}</h2>
<p class="sub">{desc}</p>
<div class="grid">{''.join(cards)}</div>""")
    path.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pothole and Bump Animations</title>
<style>
body{{margin:0;background:#fafaf8;color:#222;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1150px;margin:0 auto;padding:28px 16px 48px}}
h1{{font-size:24px;margin:0 0 6px}} h2{{font-size:19px;margin:34px 0 4px}}
.sub{{color:#6b6b6b;margin:0 0 14px}} .hint{{color:#6b6b6b}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}}
figure{{margin:0;background:#fff;border:1px solid #e3e2de;border-radius:8px;padding:10px}}
img{{width:100%;height:auto;display:block}} figcaption{{font-size:14px;margin-top:6px}}
.note{{color:#6b6b6b;font-size:13.5px;margin-top:26px}}
</style></head><body><main>
<h1>E-scooter pothole and road bump simulations</h1>
<p class="sub">MuJoCo side-view model · potholes, then road bumps further down · coasting · 76 kg rider ·
all clips 4× slower than real time, looping</p>
{''.join(blocks)}
<p class="note">Orange: rider (pinned at the feet, braced by a spring). Black: deck and stem. Blue: wheels.
Model assumptions (scooter mass, wheelbase, tyre softness, rider bracing) are listed in
scripts/scooter_sim.py. Steering and frame redesign are not modelled; front suspension only where stated. Absolute values are not
validated against measurements, so read these as comparisons between wheel sizes.</p>
</main></body></html>""", encoding="utf-8")


# Animation sets: (heading, description, depth_mm, length_mm, speed, [(f, r, note), ...])
ANIMATION_SETS = [
    # (heading, description, depth_mm, length_mm, speed_kmh, [(front, rear, note)], suspension)
    ("Voiager 5 with its front spring",
     "80 mm deep, 600 mm long, 15 km/h, front suspension modelled (the Voiager 5 has a front spring). "
     "The current 10 in wheels pitch over; a 12 in front wheel rolls out.",
     80, 600, 15.0, [(10, 10, "Voiager 5 (rear size assumed)"), (12, 10, "")], True),
    ("Soft-edged pothole (50 mm sloped edges): current vs larger front wheel",
     "80 mm deep, 600 mm long, each edge sloping down over 50 mm, 15 km/h, front suspension. The current "
     "Voiager 5 wheels pitch over; with a 12 in or 14 in front wheel the scooter rolls through.",
     80, 600, 15.0, [(10, 10, "Voiager 5 (current)", 50), (12, 10, "Larger front wheel", 50),
                     (14, 10, "Larger front wheel", 50)], True),
    ("Soft-edged pothole (100 mm sloped edges): current vs larger front wheel",
     "90 mm deep, 600 mm long, each edge sloping down over 100 mm, 15 km/h, front suspension. Same result "
     "with gentler edges: the current wheels pitch over, larger front wheels roll through.",
     90, 600, 15.0, [(10, 10, "Voiager 5 (current)", 100), (12, 10, "Larger front wheel", 100),
                     (14, 10, "Larger front wheel", 100)], True),
    ("Same pothole, larger front wheel",
     "70 mm deep, 1000 mm long, 20 km/h, no suspension. The current wheels pitch over; a 12 in front "
     "wheel rolls out.",
     70, 1000, 20.0, [(10, 10, ""), (12, 10, "")], False),
    ("When the front wheel is much bigger than the rear",
     "90 mm deep, 1000 mm long, 20 km/h, no suspension. Every fall in the simulations was a forward "
     "pitch-over started by the front-wheel impact; a very large front wheel prevents it here.",
     90, 1000, 20.0, [(10, 10, ""), (20, 10, "Front twice the rear")], False),
    ("Where the second jolt comes from",
     "40 mm deep, 600 mm long, 20 km/h, no suspension. With small front wheels the front impact lifts "
     "the rear clear of the hole. With a big front wheel the scooter isn't bucked, so the small rear "
     "wheel drops in and takes its own jolt. No run fell because of it.",
     40, 600, 20.0, [(10, 10, ""), (20, 8, "Front 2.5 times the rear")], False),
]


def _clip(gif, f, r, d, w, s, reuse):
    """Render one GIF, or with reuse=True keep an existing GIF and only re-run the
    simulation for its caption (same settings, so the same result)."""
    if reuse and gif.exists():
        return simulate(f, r, d, w, s)
    return animate(f, r, d, w, s, gif)


def build_animations(out_dir, reuse=False):
    """Render every ANIMATION_SETS entry (potholes), then every BUMP_ANIMATION_SETS
    entry, into one page, animations.html. A pothole case may be (front, rear, note) for
    MuJoCo's contact with sharp edges, or (front, rear, note, edge_mm) for the profile
    contact with sloped edges of that width (0 = sharp)."""
    global SUSPENSION, CONTACT_MODEL, EDGE_WIDTH, OBSTACLE, BUMP_SHAPE
    keep = (SUSPENSION, CONTACT_MODEL, EDGE_WIDTH, OBSTACLE, BUMP_SHAPE)
    OBSTACLE = "pothole"
    sections = []
    for heading, desc, d, w, s, cases, susp in ANIMATION_SETS:
        SUSPENSION = susp
        clips = []
        for case in cases:
            f, r, note = case[:3]
            edge = case[3] if len(case) > 3 else None
            CONTACT_MODEL = "mujoco" if edge is None else "profile"
            EDGE_WIDTH = 0.0 if edge is None else edge / 1000
            tag = ("_susp" if susp else "") + ("" if edge is None else f"_edge{edge}")
            gif = out_dir / f"anim_{f}_{r}_{d}x{w}mm_{s:g}kmh{tag}.gif"
            clips.append((f, r, gif, _clip(gif, f, r, d, w, s, reuse), note))
        sections.append((heading, desc, clips, "pothole"))
    for heading, desc, h, w, s, shape, contact, cases, susp in BUMP_ANIMATION_SETS:
        SUSPENSION, CONTACT_MODEL, EDGE_WIDTH, OBSTACLE, BUMP_SHAPE = susp, contact, 0.0, "bump", shape
        clips = []
        for f, r, note in cases:
            gif = out_dir / f"anim_bump_{shape}_{f}_{r}_{h}x{w}mm_{s:g}kmh{'_susp' if susp else ''}.gif"
            clips.append((f, r, gif, _clip(gif, f, r, h, w, s, reuse), note))
        sections.append((heading, desc, clips, "bump"))
    SUSPENSION, CONTACT_MODEL, EDGE_WIDTH, OBSTACLE, BUMP_SHAPE = keep
    write_animation_page(out_dir / "animations.html", sections)


# ---- Front/rear wheel-ratio study: what if the front wheel is much bigger? ----
RATIO_CONFIGS = [(10, 10), (12, 10), (14, 10), (16, 10), (20, 10), (16, 8), (20, 8)]
RATIO_RAMP = ["#b7d3f6", "#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]


def ratio_study(out_dir):
    """Sweep front/rear diameter ratios from 1.0 to 2.5 and locate where falls start,
    which wheel's crossing causes them, and what the rear wheel does."""
    rows = []
    runs = list(itertools.product(RATIO_CONFIGS, DEPTHS_MM, LENGTHS_MM, SPEEDS_KMH))
    for i, ((f, r), d, w, s) in enumerate(runs, 1):
        res = simulate(f, r, d, w, s)
        res["ratio"] = round(f / r, 2)
        rows.append(res)
        if i % 100 == 0:
            print(f"  {i}/{len(runs)} runs")
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "ratio_results.csv", index=False)

    # Shallowest falling depth and which phase caused it.
    t_rows = []
    for (f, r, w, s), g in df.groupby(["front_in", "rear_in", "length_mm", "speed_kmh"]):
        falls = g[g["fall"]].sort_values("depth_mm")
        t_rows.append({"config": f"{f}/{r}", "ratio": round(f / r, 2), "length_mm": w,
                       "speed_kmh": s,
                       "first_fall_mm": falls["depth_mm"].iloc[0] if len(falls) else np.nan,
                       "fall_phase": falls["fall_phase"].iloc[0] if len(falls) else ""})
    thr = pd.DataFrame(t_rows)
    thr.to_csv(out_dir / "ratio_fall_thresholds.csv", index=False)

    labels = [f"{f}/{r}" for f, r in RATIO_CONFIGS]

    # Figure 1: shallowest falling depth by configuration (no fall drawn at the top).
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6), sharey=True)
    speed_cols = {15.0: "#9ec5f4", 20.0: "#2a78d6", 25.0: "#0d366b"}
    for ax, w in zip(axes, (600, 1000)):
        for s in SPEEDS_KMH:
            t = thr[(thr["length_mm"] == w) & (thr["speed_kmh"] == s)].set_index("config").loc[labels]
            y = t["first_fall_mm"].fillna(110)
            ax.plot(range(len(labels)), y, color=speed_cols[s], lw=2, label=f"{s:g} km/h")
            for xi, (yi, ph) in enumerate(zip(y, t["fall_phase"])):
                hollow = yi == 110
                ax.plot(xi, yi, marker="s" if ph == "rear" else "o", ms=7,
                        mfc="white" if hollow else speed_cols[s], mec=speed_cols[s], mew=1.5)
        ax.set_xticks(range(len(labels)), [f"{l}\n×{f / r:.1f}" for l, (f, r) in zip(labels, RATIO_CONFIGS)],
                      fontsize=8)
        ax.set_title(f"{w} mm long pothole", fontsize=9.5, color=INK, loc="left")
        ax.set_xlabel("Front/rear wheel diameter (in) and ratio")
        ax.axhline(105, color="#dddddd", lw=0.8)
        _style(ax)
    axes[0].set_ylabel("Shallowest depth causing a fall (mm)")
    axes[0].set_yticks([20, 40, 60, 80, 100, 110], ["20", "40", "60", "80", "100", "none"])
    axes[0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.suptitle("Filled = falls (circle: caused by front-wheel impact, square: by rear-wheel impact) · hollow at top = "
                 "no fall up to 100 mm", fontsize=8.5, color=MUTED, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(out_dir / "fig_ratio_first_fall.png", dpi=150)
    plt.close(fig)

    # Figure 2: what the rear wheel does (20 km/h), by configuration.
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    sub = df[df["speed_kmh"] == 20.0]
    panels = [(600, "rear_drop_mm", "Rear wheel dip into pothole (mm)"),
              (600, "rear_lift_mm", "Rear wheel lifted off road (mm)"),
              (600, "rear_speed_loss_pct", "Speed lost at rear-wheel crossing (%)")]
    for ax, (w, col, lab) in zip(axes, panels):
        for (f, r), c in zip(RATIO_CONFIGS, RATIO_RAMP):
            s_ = sub[(sub["front_in"] == f) & (sub["rear_in"] == r) & (sub["length_mm"] == w)]
            ax.plot(s_["depth_mm"], s_[col], color=c, lw=2, label=f"{f}/{r}")
        ax.set_title(lab, fontsize=9.5, color=INK, loc="left")
        ax.set_xlabel(f"Pothole depth (mm) · {w} mm long, 20 km/h")
        _style(ax)
    axes[-1].legend(frameon=False, fontsize=8, title="front/rear (in)", title_fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "fig_ratio_rear_wheel.png", dpi=150)
    plt.close(fig)
    return df, thr


# ---- Soft-edged potholes (profile contact): does edge shape change the conclusions? ----
EDGE_WIDTHS_MM = [0, 25, 50, 100]     # 0 = sharp; otherwise width of each sloped edge
EDGE_COLS = {0: "#b5b4ae", 25: "#86b6ef", 50: "#2a78d6", 100: "#0d366b"}


def _edge_worker(job):
    """One run in a worker process (settings passed explicitly: globals don't carry over)."""
    (f, r, d, w, s), b_mm, settings = job
    g = globals()
    for k, v in settings.items():
        g[k] = v
    g["CONTACT_MODEL"], g["EDGE_WIDTH"] = "profile", b_mm / 1000
    res = simulate(f, r, d, w, s)
    res["edge_width_mm"] = b_mm
    return res


def edge_study(out_dir, processes=4):
    """Sweep pothole edge width with the profile contact model."""
    from multiprocessing import Pool
    settings = {"SUSPENSION": SUSPENSION, "TYRE_STIFFNESS": TYRE_STIFFNESS,
                "TYRE_DAMPING": TYRE_DAMPING, "PROFILE_DX": PROFILE_DX}
    jobs = [((f, r, d, w, s), b, settings)
            for b in EDGE_WIDTHS_MM for _, f, r in CONFIGS
            for d in DEPTHS_MM for w in LENGTHS_MM for s in SPEEDS_KMH]
    with Pool(processes) as pool:
        rows = []
        for i, res in enumerate(pool.imap(_edge_worker, jobs, chunksize=8), 1):
            rows.append(res)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)} runs")
    df = pd.DataFrame(rows)
    df["config"] = df["front_in"].astype(str) + "/" + df["rear_in"].astype(str)
    df.to_csv(out_dir / "edge_results.csv", index=False)

    # Shallowest falling depth per edge width, configuration, length, speed.
    thr = (df[df["fall"]].groupby(["edge_width_mm", "config", "length_mm", "speed_kmh"])["depth_mm"]
           .min().unstack("config"))
    thr = thr.reindex(pd.MultiIndex.from_product(
        [EDGE_WIDTHS_MM, LENGTHS_MM, SPEEDS_KMH], names=["edge_width_mm", "length_mm", "speed_kmh"]))
    thr = thr[[f"{f}/{r}" for _, f, r in CONFIGS]]
    thr.to_csv(out_dir / "edge_fall_thresholds.csv")
    falls = df.groupby(["edge_width_mm", "config"])["fall"].sum().unstack("config")[
        [f"{f}/{r}" for _, f, r in CONFIGS]]
    falls.to_csv(out_dir / "edge_fall_counts.csv")

    # Figure: front-wheel speed loss and handlebar peak vs depth, 600 mm, 20 km/h, 10/10,
    # one line per edge width; plus fall counts per configuration and edge width.
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    sub = df[(df["config"] == "10/10") & (df["length_mm"] == 600) & (df["speed_kmh"] == 20.0)]
    for b in EDGE_WIDTHS_MM:
        s_ = sub[sub["edge_width_mm"] == b].sort_values("depth_mm")
        lab = "sharp" if b == 0 else f"{b} mm sloped edges"
        axes[0].plot(s_["depth_mm"], s_["speed_loss_pct"], color=EDGE_COLS[b], lw=2, marker="o", ms=4, label=lab)
        axes[1].plot(s_["depth_mm"], s_["handlebar_peak_g"], color=EDGE_COLS[b], lw=2, marker="o", ms=4, label=lab)
    axes[0].set_ylabel("Forward speed lost (%)")
    axes[1].set_ylabel("Handlebar peak (g)")
    for ax in axes[:2]:
        ax.set_xlabel("Pothole depth (mm) · 600 mm long, 20 km/h, 10/10 in")
        _style(ax)
    axes[0].legend(frameon=False, fontsize=8)
    xs = np.arange(len(EDGE_WIDTHS_MM))
    bw = 0.2
    cfg_cols = {"10/10": "#86b6ef", "12/10": "#2a78d6", "12/12": "#eb6834", "14/10": "#0d366b"}
    for i, c in enumerate(falls.columns):
        axes[2].bar(xs + (i - 1.5) * bw, falls[c].values, width=bw - 0.03, color=cfg_cols[c], label=c)
    axes[2].set_xticks(xs, ["sharp" if b == 0 else f"{b} mm" for b in EDGE_WIDTHS_MM])
    axes[2].set_xlabel("Pothole edge")
    axes[2].set_ylabel(f"Falls (of {len(DEPTHS_MM) * len(LENGTHS_MM) * len(SPEEDS_KMH)} runs)")
    axes[2].legend(frameon=False, fontsize=8, title="front/rear (in)", title_fontsize=8)
    _style(axes[2])
    fig.tight_layout()
    fig.savefig(out_dir / "fig_edges.png", dpi=150)
    plt.close(fig)
    return df, thr, falls


# ---- Road bumps: raised obstacles instead of potholes ----
# (name, shape, contact model, lengths in mm). Heights are DEPTHS_MM (20-100 mm).
#   sharp bump:  raised patch, lifted slab or utility cover, tree-root ridge; same lengths
#                as the potholes so the two can be compared directly. MuJoCo contact =
#                the main model; the profile contact on the same bumps is a cross-check.
#   round-top:   circular-arc humps. 600 mm = short "speed bump" of the car-park kind;
#                3700 mm = a common UK round-top road hump length. Profile contact only.
BUMP_CASES = [
    ("sharp bump", "box", "mujoco", LENGTHS_MM),
    ("sharp bump (profile contact)", "box", "profile", LENGTHS_MM),
    ("round-top hump", "arc", "profile", [600, 3700]),
]
# Rear-size check: short sharp bumps, where (with the front fork) the falls come from the
# rear wheel's strike. Finer 5 mm height steps; rear-larger configurations included.
BUMP_REAR_CONFIGS = [(10, 10), (12, 10), (14, 10), (10, 12), (12, 12), (10, 14), (14, 14)]
BUMP_REAR_HEIGHTS_MM = list(range(50, 101, 5))
BUMP_COLS = {"pothole": "#b5b4ae", "sharp bump": "#0d366b",
             "sharp bump (profile contact)": "#5598e7", "round-top hump": "#eb6834"}


def _bump_worker(job):
    """One bump run in a worker process (settings passed explicitly)."""
    (f, r, h, w, s), (name, shape, contact), settings = job
    g = globals()
    for k, v in settings.items():
        g[k] = v
    g["OBSTACLE"], g["BUMP_SHAPE"], g["CONTACT_MODEL"], g["EDGE_WIDTH"] = "bump", shape, contact, 0.0
    res = simulate(f, r, h, w, s)
    res["case"] = name
    return res


def bump_study(out_dir, processes=4):
    """Sweep bump height, length and speed for every wheel configuration and bump case,
    and compare with the pothole sweep in the same output folder (sim_results.csv)."""
    from multiprocessing import Pool
    settings = {"SUSPENSION": SUSPENSION, "TYRE_STIFFNESS": TYRE_STIFFNESS,
                "TYRE_DAMPING": TYRE_DAMPING, "PROFILE_DX": PROFILE_DX}
    jobs = [((f, r, h, w, s), (name, shape, contact), settings)
            for name, shape, contact, lengths in BUMP_CASES for _, f, r in CONFIGS
            for h in DEPTHS_MM for w in lengths for s in SPEEDS_KMH]
    with Pool(processes) as pool:
        rows = []
        for i, res in enumerate(pool.imap(_bump_worker, jobs, chunksize=8), 1):
            rows.append(res)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)} runs")
    df = pd.DataFrame(rows).rename(columns={"depth_mm": "height_mm"})
    df["config"] = df["front_in"].astype(str) + "/" + df["rear_in"].astype(str)
    df.to_csv(out_dir / "bump_results.csv", index=False)
    cfgs = [f"{f}/{r}" for _, f, r in CONFIGS]

    # Pothole sweep from the same model (if it has been run), for comparison.
    pot = None
    if (out_dir.parent / "sim_results.csv").exists():
        pot = pd.read_csv(out_dir.parent / "sim_results.csv")
        pot["config"] = pot["front_in"].astype(str) + "/" + pot["rear_in"].astype(str)
        pot = pot.rename(columns={"depth_mm": "height_mm"}).assign(case="pothole")

    # Lowest falling height per case, configuration, length and speed (pothole alongside).
    both = pd.concat([df, pot]) if pot is not None else df
    thr = (both[both["fall"]].groupby(["case", "length_mm", "speed_kmh", "config"])["height_mm"]
           .min().unstack("config"))
    idx = [(c, w, s) for c, w in [(n, w) for n, _, _, ls in BUMP_CASES for w in ls]
           + ([("pothole", w) for w in LENGTHS_MM] if pot is not None else []) for s in SPEEDS_KMH]
    thr = thr.reindex(pd.MultiIndex.from_tuples(idx, names=["case", "length_mm", "speed_kmh"]))
    thr = thr.reindex(columns=cfgs)
    thr.to_csv(out_dir / "bump_fall_thresholds.csv")

    # Fall counts and how they happened, per case and length.
    cnt = (both.groupby(["case", "length_mm", "config"])
           .agg(runs=("fall", "size"), falls=("fall", "sum"),
                stalled=("stalled", "sum"))
           .reset_index())
    cnt.to_csv(out_dir / "bump_fall_counts.csv", index=False)

    # Figures for the main (MuJoCo-contact) sharp bumps, in the style of the pothole ones.
    main = df[df["case"] == "sharp bump"].rename(columns={"height_mm": "depth_mm"})
    fig_metric(main, "speed_loss_pct", "Forward speed lost (%)", out_dir / "fig_bump_speed_loss.png",
               noun="sharp bump", xlabel="Bump height (mm)")
    fig_metric(main, "handlebar_peak_g", "Peak handlebar vertical accel. (g)",
               out_dir / "fig_bump_handlebar_g.png", noun="sharp bump", xlabel="Bump height (mm)")

    # Figure: falls per configuration for each obstacle, sharp bump vs pothole of the
    # same size, plus round-top humps.
    groups = ([("pothole", w) for w in LENGTHS_MM] if pot is not None else []) + \
        [("sharp bump", w) for w in LENGTHS_MM] + [("round-top hump", w) for w in (600, 3700)]
    fig, ax = plt.subplots(figsize=(11, 3.8))
    bw = 0.2
    for gi, (case, w) in enumerate(groups):
        for i, c in enumerate(cfgs):
            row = cnt[(cnt["case"] == case) & (cnt["length_mm"] == w) & (cnt["config"] == c)]
            n = int(row["falls"].iloc[0]) if len(row) else 0
            ax.bar(gi + (i - 1.5) * bw, n, width=bw - 0.03, color=RAMP[c],
                   label=c if gi == 0 else None)
    n_runs = len(DEPTHS_MM) * len(SPEEDS_KMH)
    ax.set_xticks(range(len(groups)), [f"{c}\n{w} mm" for c, w in groups], fontsize=8)
    ax.set_ylabel(f"Falls (of {n_runs} runs each)")
    ax.legend(frameon=False, fontsize=8, title="front/rear (in)", title_fontsize=8)
    ax.set_title(f"Same depth/height range (20-100 mm) and speeds (15-25 km/h)"
                 f"{' · front suspension' if SUSPENSION else ' · no suspension'}",
                 fontsize=9, color=MUTED, loc="left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(out_dir / "fig_bump_falls.png", dpi=150)
    plt.close(fig)

    # Figure: bump vs pothole of the same size, 10/10 and 14/10, 20 km/h, speed lost.
    if pot is not None:
        fig, axes = plt.subplots(1, len(LENGTHS_MM), figsize=(10.5, 3.4), sharey=True)
        for ax, w in zip(axes, LENGTHS_MM):
            for c in ("10/10", "12/10", "14/10"):
                for case, ls in (("sharp bump", "-"), ("pothole", ":")):
                    s_ = both[(both["case"] == case) & (both["config"] == c) & (both["length_mm"] == w)
                              & (both["speed_kmh"] == 20.0)].sort_values("height_mm")
                    ax.plot(s_["height_mm"], s_["speed_loss_pct"], color=RAMP[c], lw=2 if ls == "-" else 1.4,
                            ls=ls, label=f"{c} {case}")
                    fl = s_[s_["fall"]]
                    ax.plot(fl["height_mm"], fl["speed_loss_pct"], ls="none", marker="X", ms=8,
                            color=RAMP[c], markeredgecolor="white")
            ax.set_title(f"{w} mm long", fontsize=9.5, color=INK, loc="left")
            ax.set_xlabel("Bump height / pothole depth (mm)")
            _style(ax)
        axes[0].set_ylabel("Forward speed lost (%)")
        axes[0].legend(frameon=False, fontsize=7.5, loc="upper left")
        fig.suptitle("20 km/h · solid = sharp bump, dotted = pothole · X = fall",
                     fontsize=9, color=MUTED, x=0.01, ha="left")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_bump_vs_pothole.png", dpi=150)
        plt.close(fig)

    # Rear-size check (300 mm sharp bump, MuJoCo contact): lowest falling height.
    jobs = [((f, r, h, 300, sp), ("sharp bump", "box", "mujoco"), settings)
            for f, r in BUMP_REAR_CONFIGS for h in BUMP_REAR_HEIGHTS_MM for sp in SPEEDS_KMH]
    with Pool(processes) as pool:
        rr = pd.DataFrame(pool.map(_bump_worker, jobs, chunksize=8)).rename(columns={"depth_mm": "height_mm"})
    rr["config"] = rr["front_in"].astype(str) + "/" + rr["rear_in"].astype(str)
    rr.to_csv(out_dir / "bump_rear_check.csv", index=False)
    rear = (rr[rr["fall"]].groupby(["speed_kmh", "config"])["height_mm"].min().unstack("config")
            .reindex(index=SPEEDS_KMH, columns=[f"{f}/{r}" for f, r in BUMP_REAR_CONFIGS]))
    rear.to_csv(out_dir / "bump_rear_check_thresholds.csv")
    return df, thr, cnt, rear


# Bump sections of animations.html: (heading, description, height_mm, length_mm, speed,
# shape, contact, [(front, rear, note)], suspension). Rendered by build_animations().
BUMP_ANIMATION_SETS = [
    ("Road bump: sharp-edged, no suspension (exploratory)",
     "90 mm high, 600 mm long idealised sharp-edged bump, 20 km/h, rigid fork. In this run the 10/10 "
     "model meets the fall criteria after the front-wheel strike; the 12 and 14 in front-wheel models "
     "do not.",
     90, 600, 20.0, "box", "mujoco", [(10, 10, "Current wheel sizes"), (12, 10, "Larger front wheel"),
                                      (14, 10, "Larger front wheel")], False),
    ("Road bump with the modelled front spring: falls after the rear-wheel strike (exploratory)",
     "90 mm high, 300 mm short idealised sharp-edged bump, 15 km/h, front suspension. In these runs the "
     "fall criteria are met after the rigid rear wheel strikes the edge. The 10/14 run does not meet "
     "them; this is one of very few such cases and is an open question, not a result about rear wheel "
     "size.",
     90, 300, 15.0, "box", "mujoco", [(10, 10, "Voiager 5 (current)"), (14, 10, "Larger front wheel only"),
                                      (10, 14, "Larger rear wheel only")], True),
    ("Round-top road hump (3.7 m long, 75 mm high)",
     "Circular-arc hump of the standard UK round-top length, 20 km/h, front suspension. No modelled "
     "round-top hump run up to 100 mm met the fall criteria.",
     75, 3700, 20.0, "arc", "profile", [(10, 10, "Voiager 5 (current)")], True),
    ("Short round speed bump (600 mm long, 100 mm high)",
     "Short circular-arc bump, 15 km/h, front suspension. Fall criteria not met; large modelled speed "
     "loss. Modelled jolt sizes for bumps are not validated.",
     100, 600, 15.0, "arc", "profile", [(10, 10, "Voiager 5 (current)"), (14, 10, "Larger front wheel")], True),
]


def main():
    ap = argparse.ArgumentParser(description="MuJoCo e-scooter pothole simulation")
    ap.add_argument("--out-dir", type=Path, default=Path("outputs/scooter_sim"))
    ap.add_argument("--animate", action="store_true", help="also write example GIFs")
    ap.add_argument("--sensitivity", action="store_true",
                    help="only run the tyre/rider sensitivity analysis")
    ap.add_argument("--ratio", action="store_true",
                    help="only run the front/rear wheel-ratio study (outputs in <out-dir>/ratio)")
    ap.add_argument("--suspension", action="store_true",
                    help="model the front spring fork; outputs go to <out-dir>/suspension")
    ap.add_argument("--consistency", action="store_true",
                    help="only run the consistency check against the measured ride")
    ap.add_argument("--bumps", action="store_true",
                    help="road bump study: sharp bumps and round-top humps "
                         "(outputs in <out-dir>[/suspension]/bumps); with --animate, only "
                         "add the bump clips to <out-dir>/animations.html")
    ap.add_argument("--edges", action="store_true",
                    help="soft-edged pothole study with the profile contact "
                         "(outputs in <out-dir>[/suspension]/soft_edges)")
    args = ap.parse_args()
    base_dir = args.out_dir           # animations.html lives here, whatever the study
    if args.consistency:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        c = consistency(args.out_dir)
        print(c.to_string(index=False))
        return
    if args.suspension:
        global SUSPENSION
        SUSPENSION = True
        args.out_dir = args.out_dir / "suspension"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.bumps:
        bdir = args.out_dir / "bumps"
        bdir.mkdir(exist_ok=True)
        if args.animate:   # add the bump clips to animations.html, keeping existing GIFs
            build_animations(base_dir, reuse=True)
            return
        df, thr, cnt, rear = bump_study(bdir)
        pd.set_option("display.width", 200)
        print("Falls per case, length and configuration:\n",
              cnt.pivot_table(index=["case", "length_mm"], columns="config",
                              values=["falls", "stalled"]).to_string())
        print("\nLowest falling height/depth (mm):\n", thr.dropna(how="all").to_string())
        print("\nRear-size check, 300 mm sharp bump, lowest falling height (mm; NaN = none "
              "up to 100):\n", rear.to_string())
        return

    if args.edges:
        edir = args.out_dir / "soft_edges"
        edir.mkdir(exist_ok=True)
        df, thr, falls = edge_study(edir)
        pd.set_option("display.width", 180)
        print("Falls per configuration and edge width:\n", falls.to_string())
        print("\nShallowest falling depth (mm):\n", thr.dropna(how="all").to_string())
        return

    if args.ratio:
        rdir = args.out_dir / "ratio"
        rdir.mkdir(exist_ok=True)
        df, thr = ratio_study(rdir)
        pd.set_option("display.width", 180)
        print(thr.pivot_table(index=["length_mm", "speed_kmh"], columns="config",
                              values="first_fall_mm", dropna=False)
              [[f"{f}/{r}" for f, r in RATIO_CONFIGS]].to_string())
        print("\nFall phase counts (all falling runs):")
        print(df[df["fall"]].groupby(["front_in", "rear_in"])["fall_phase"].value_counts()
              .unstack(fill_value=0).to_string())
        return

    if args.sensitivity:
        s = sensitivity(args.out_dir)
        pd.set_option("display.width", 180)
        print(s.pivot(index="setting", columns="config",
                      values=["first_fall_mm_1000mm_20kmh", "speed_loss_pct_60x600_20kmh"]).to_string())
        return

    runs = list(itertools.product(CONFIGS, DEPTHS_MM, LENGTHS_MM, SPEEDS_KMH))
    rows = []
    for i, ((label, f, r), d, w, s) in enumerate(runs, 1):
        res = simulate(f, r, d, w, s)
        res["config"] = label
        rows.append(res)
        if i % 50 == 0:
            print(f"  {i}/{len(runs)} runs")
    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "sim_results.csv", index=False)

    fig_metric(df, "rider_lean_max_deg", "Peak rider forward lean (deg)",
               args.out_dir / "fig_rider_lean.png", threshold=FALL_LEAN_DEG)
    fig_metric(df, "speed_loss_pct", "Forward speed lost (%)", args.out_dir / "fig_speed_loss.png")
    fig_metric(df, "handlebar_peak_g", "Peak handlebar vertical accel. (g)",
               args.out_dir / "fig_handlebar_g.png")
    thr = fall_threshold_table(df)
    thr.to_csv(args.out_dir / "fall_thresholds.csv")

    if args.animate:
        build_animations(base_dir)

    pd.set_option("display.width", 180)
    print("\nShallowest depth (mm) that causes a fall (NaN = no fall up to 100 mm):")
    print(thr.to_string())
    print(f"\nOutputs in {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()
