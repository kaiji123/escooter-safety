# Simulation methods

How the wheel-size models in Part B were built, run, checked and visualised. This
document is detailed enough to reproduce every result and to serve as the basis of the
paper's methods section. Results are summarised in `DOCUMENTATION.md` (sections 6.3–6.5).

Two models were built:

| Model | Script | Question it answers |
|---|---|---|
| Geometry model | `scripts/wheel_geometry.py` | How deep does a wheel drop into a pothole, and how hard does it hit the far edge, for each wheel size? |
| Dynamics simulation | `scripts/scooter_sim.py` | Does a scooter with a rider fall when crossing a pothole, and does a larger front wheel prevent it? |

---

## 1. Software and reproducibility

| Item | Version |
|---|---|
| Python | 3.11.9 (Windows 10) |
| MuJoCo (physics engine, Python bindings) | 3.14.0 |
| NumPy / pandas / SciPy | 2.3.4 / 2.3.3 / 1.17.1 |
| Matplotlib / Pillow (figures, GIFs) | 3.11.2 / 12.3.0 |

Cite in the paper: MuJoCo (Todorov, Erez and Tassa 2012, plus the version), NumPy (Harris
et al. 2020), SciPy (Virtanen et al. 2020), pandas (McKinney 2010; Zenodo DOI for the
version), Matplotlib (Hunter 2007; `FuncAnimation` drew the animations) and Pillow (GIF
encoding via Matplotlib's `PillowWriter`). Full entries are in `REFERENCES.md` and
`references.bib`. The rider sizes and fall thresholds compared against come from
Posirisuk, Baker and Ghajari (2022), doi:10.1016/j.aap.2022.106567.

- Both models are deterministic: a rerun on the same machine reproduces the results
  exactly. This was checked by rerunning the full 324-run sweep and the sensitivity
  analysis into a separate folder; all outcomes were identical.
- Runtime: about 95 s for the 324-run sweep, about 3 minutes for the 567-run ratio
  study, on an ordinary laptop.
- All parameters are constants at the top of each script. Values not published by Voi
  are marked `ASSUMED` in the code.

---

## 2. Geometry model (`wheel_geometry.py`)

### 2.1 Setup

A rigid wheel of radius R rolls at speed v across a rectangular pothole of depth d and
length w (along the direction of travel) with sharp, square edges. This is a worst case:
real pothole edges are usually broken or rounded, and tyres deform around them.

### 2.2 Equations

**Drop into the pothole.** While crossing, the wheel's lowest point sinks below road
level by

h = min( d,  R − √(R² − (w/2)²),  ½·g·(w/v)² )

- d: the wheel reaches the bottom of the hole.
- R − √(R² − (w/2)²): the wheel rests on both edges and can't sink further (the sag
  limit; w/2 is capped at R).
- ½·g·(w/v)²: how far the wheel can fall in the time it takes to cross. This assumes
  free fall, an upper bound; in reality the frame and rider slow the fall.

**Impact at the far edge.** With the wheel bottom h below road level, the edge touches
the tyre at an angle θ from vertical:

cos θ = (R − h) / R

Treating the wheel as a point mass at the axle with a plastic impact at the edge:

| Quantity | Formula | Meaning |
|---|---|---|
| Edge impact velocity | v·sin θ | Velocity component into the edge, lost in the impact (impact severity) |
| Front-wheel speed loss | v·sin² θ | Sudden forward deceleration of the axle (the pitch-over driver) |
| Upward velocity gained | v·sin θ·cos θ | Velocity redirected upwards to climb the edge |

If h ≥ R the edge is above the axle and the wheel can't roll over it.

A bigger wheel has a smaller θ for the same pothole, so every quantity falls.

### 2.3 Parameters

| Parameter | Values |
|---|---|
| Wheel diameters | 8, 10, 12, 14, 16 in (nominal size taken as tyre outer diameter; 10 in = 254 mm) |
| Configurations | 10/10 (Voiager 5), 12/10 (Voiager 7-style front), 14/10, 12/12 |
| Speeds | 15, 20 (main), 25 km/h |
| Depths | 0–120 mm in 1 mm steps |
| Lengths | 150, 300, 600 (main), 1000 mm |
| Key depths | 30, 60, 90 mm (the Imperial study's depths) |

### 2.4 Outputs

`outputs/wheel_model/`: `wheel_sweep.csv` (all combinations), `configurations.csv`
(front and rear wheel metrics per configuration at the key depths, with % change from
10/10), and four figures (schematic, impact velocity, speed loss, pothole length).

The schematic uses the static case (no time limit on the drop), labelled as such.

### 2.5 Limitation

Each wheel is analysed on its own. The model therefore gives identical front-wheel
results for "larger front only" and "larger both", and cannot say whether the scooter
falls. That needs the dynamics simulation.

---

## 3. Dynamics simulation (`scooter_sim.py`)

### 3.1 Approach

A planar (side-view) multibody model in MuJoCo, following the structure of the
Imperial College e-scooter fall study (Posirisuk, Baker & Ghajari, *Accident Analysis &
Prevention*, 2022), which modelled the scooter as two rigid bodies, the front wheel and
the rest of the scooter, joined at the axle. This model extends that structure with a
separate rear wheel, so that front-only and front-and-rear wheel changes can be
compared, and with a rider.

MuJoCo was chosen over PyChrono (harder to install on Windows), PyBullet (less
actively maintained) and Blender/OpenSCAD (no validated physics). It installs with
`pip install mujoco`.

### 3.2 Coordinate system and degrees of freedom

x is the direction of travel, z is up, y is the wheel axle direction. Everything moves
in the x–z plane. The model has 6 degrees of freedom:

| Joint | Type | Body | Meaning |
|---|---|---|---|
| `x` | slide | chassis | Forward position |
| `z` | slide | chassis | Height |
| `pitch` | hinge about y | chassis | Scooter pitch (positive = nose down) |
| `front_axle` | hinge about y | front wheel | Wheel rotation |
| `rear_axle` | hinge about y | rear wheel | Wheel rotation |
| `ankle` | hinge about y, with spring-damper | rider | Rider lean relative to the deck (positive = forward) |

### 3.3 Bodies and geometry

The chassis frame origin is midway between the axles at ground level. With wheel radii
Rf (front) and Rr (rear) and wheelbase L:

| Element | Definition |
|---|---|
| Front axle | x = +L/2, z = Rf |
| Rear axle | x = −L/2, z = Rr |
| Deck | Box, top at deck_z = 0.16 m + (Rf + Rr)/2 − 0.127 m (the deck rises with wheel size and stays level, i.e. the frame is assumed redesigned for each wheel combination); collides with the road |
| Stem | Capsule from the front axle to the handlebar, visual only (no collision) |
| Handlebar | Site at x = L/2 − 0.08 m, z = 1.05 m; carries the accelerometer |
| Wheels | Rigid cylinders, radius R, width 0.06 m |
| Rider | Body pinned at the feet, mid-deck, 0.02 m above deck_z; visual capsule 1.6 m tall, no collision |

### 3.4 Mass properties

| Body | Mass | Centre of mass | Inertia |
|---|---|---|---|
| Chassis | 32 − 2 × 2.5 = 27 kg | x = 0.05 m, z = deck_z + 0.15 m | diag(0.6, 1.2, 0.8) kg·m² (assumed) |
| Each wheel | 2.5 kg (or 2.5 × D/10 kg with `SCALE_WHEEL_MASS`) | Axle | From the cylinder shape (MuJoCo) |
| Rider | 76 kg | 0.55 × 1.70 m = 0.935 m above the feet | diag(12, 12, 1) kg·m² (assumed; a uniform 1.7 m, 76 kg rod would be ~18 kg·m²) |

### 3.5 Rider bracing

The rider is a rigid body pinned to the deck at the feet. A rotational spring
(1500 N·m/rad) and damper (150 N·m·s/rad) at the pin stand for the rider holding
themselves upright with legs and arms. The stiffness was chosen so that braking at
0.3 g leans the rider about 8° forward: lean ≈ m·a·h / k = 76 × 2.94 × 0.95 / 1500 ≈
0.14 rad. It must exceed m·g·h ≈ 710 N·m/rad for the rider to stand at all.

### 3.6 Road and pothole

Three boxes, each 0.5 m thick and 2 m wide:

| Box | Extent along x | Top surface |
|---|---|---|
| Approach road | −10 m to 5.0 m | z = 0 |
| Pothole floor | 5.0 m to 5.0 m + w | z = −d |
| Exit road | 5.0 m + w onwards (30 m) | z = 0 |

The pothole therefore has vertical walls and sharp edges. It starts 5 m ahead, giving
about 1 s of run-up.

### 3.7 Contact and tyre representation

| Setting | Value | Reason |
|---|---|---|
| Friction (sliding, torsional, rolling) | 0.9, 0.005, 0.0001 | Dry asphalt |
| `condim` | 3 | Normal force plus tangential friction |
| `solref` | (0.025 s, damping ratio 1) | Tyre compliance (below) |
| `solimp` | (0.9, 0.95, 0.001) | MuJoCo defaults |

Wheels are rigid shapes; the tyre's softness is represented by MuJoCo's soft-contact
parameters. A contact time constant τ behaves like a spring of about m/τ². With
τ = 0.025 s and about 50 kg on the front wheel this is about 80 kN/m, and the static
deflection is about g·τ² ≈ 6 mm, typical of a small pneumatic tyre. This value is
**assumed** and was tested in the sensitivity analysis (section 4.2).

Collisions: wheels and deck collide with the road. The rider and stem are visual only.
MuJoCo excludes parent–child contacts, so the wheels don't collide with the chassis.

### 3.8 Integration

Implicit-fast integrator, time step 0.5 ms, gravity 9.81 m/s².

### 3.9 Procedure for one run

1. Build the model description (MJCF XML) for the given front and rear diameter,
   pothole depth and length (`build_xml`).
2. **Settle:** simulate 0.5 s at rest so the tyres take up their static deflection.
3. **Launch:** set all velocities to zero, then set forward velocity v and each wheel's
   spin to v/R (rolling without slip). No motor torque is applied; the scooter coasts.
4. **Run** until the rear wheel is 1 m past the pothole plus 1.5 s, or stop early once
   the pitch or rider lean exceeds 80° (clearly fallen).
5. **Record** outcomes (section 3.10) only once the chassis is within one wheelbase of
   the pothole, so the launch transient is excluded.

### 3.10 Outcomes measured

| Outcome | How it's computed |
|---|---|
| `speed_loss_pct` | 100 × (1 − lowest chassis forward speed / launch speed), capped at 100 (a value over 100 means the scooter bounced backwards) |
| `chassis_pitch_max_deg` | Largest nose-down pitch |
| `rider_lean_max_deg` | Largest forward lean of the rider relative to the deck |
| `handlebar_peak_g` | Accelerometer at the handlebar, rotated into world coordinates, gravity subtracted, averaged over 10 ms windows to mimic the phone's 100 Hz log; largest absolute value, in g |
| `stalled` | Lowest forward speed below 0.5 m/s |
| `rear_lift_mm` | Highest point of the rear axle above its resting height (rear wheel lifted off the road) |
| `rear_drop_mm` | Lowest point of the rear axle below its resting height (rear wheel dipping into the pothole) |
| `front_*`, `rear_*` | Speed loss, peak handlebar acceleration (not windowed; relative use only) and peak lean, computed separately for the front and rear phases (below) |

**Phases.** The front phase lasts until the front wheel is half a wheelbase past the
far edge of the pothole; the rear phase covers the rest. Splitting at the far edge,
where the impacts happen, keeps the two wheels' crossings separate even when the
pothole is longer than the wheelbase. Speed loss in each phase is measured from the
speed at the start of that phase.

### 3.11 Fall definition and attribution

A run counts as a **fall** if any of these is met. The criteria were fixed before the
sweep was run and are analyst-defined, not taken from injury literature:

- rider lean more than 30° forward,
- scooter pitch more than 30° nose-down,
- the scooter stalls (forward speed below 0.5 m/s).

**Which wheel caused the fall:** the rear wheel is credited only if it dipped more than
5 mm into the pothole before the fall criterion was first met; otherwise the fall is
credited to the front-wheel impact. In every fall in every experiment the rear wheel
was lifted clear, so all falls are front-impact pitch-overs.

### 3.12 Front suspension option (`--suspension`)

The ridden vehicle (SZ22) is a **Voiager 5**, which has a front spring. The original
model has none, so a sprung fork was added as an option. With it off, the model is
exactly the original one (verified: randomly chosen runs reproduce to machine
precision).

| Element | Definition | Status |
|---|---|---|
| Fork | Body between chassis and front wheel, slide joint along the chassis z-axis (compression positive) | Structure |
| Spring stiffness | 25 kN/m | Assumed, typical small scooter fork |
| Damping | Damping ratio 0.3 of the sprung front mass (≈ 680 N·s/m) | Assumed; spring forks have little damping |
| Travel | 30 mm compression, 5 mm extension | Assumed |
| Preload | Spring preloaded with 50% of the sprung weight (chassis + rider), so the fork sits at its top-out at rest and the whole 30 mm travel is available | Assumed 50/50 load split |
| Fork mass | 0.5 kg | Assumed |
| Phone position | The handlebar site stays on the sprung chassis, as with the real handlebar mount | Structure |

The fork values were fixed **before** any run with them and were not adjusted
afterwards; their effect was tested in the sensitivity analysis instead (section 4.6).

Because the wheel is no longer a direct child of the chassis, MuJoCo would otherwise
generate contacts between the front wheel and the deck. These are excluded explicitly
(`<contact><exclude body1="chassis" body2="front_wheel"/></contact>`). At rest the fork
then sits at 0.6 mm compression with level pitch, as intended.

### 3.13 Rounded pothole edges with MuJoCo's own contact: tried and dropped

Real pothole edges are often broken or rounded, so a 15 mm edge radius was planned.
Two implementations using MuJoCo's built-in collision were tested and both rejected:

1. **Separate primitives** (a quarter-cylinder at each edge plus boxes for road and
   wall). Where the wheel met the edge it touched up to three shapes at once; MuJoCo
   treats each contact as its own spring, so the tyre was effectively stiffened two to
   three times at the moment of impact. Jolts went *up* (e.g. 11.8 g vs 4.9 g for a
   sharp edge), the opposite of the physical expectation.
2. **A single convex mesh** per road section with a rounded corner (one contact only).
   The results depended on how finely the curve was drawn and did not converge: for
   the same four cases, 6 segments gave up to 13.5 g, 96 gave 3.3–5.0 g, and 192, 384
   and 768 segments fluctuated between 3.2 and 8.5 g.

Neither gives trustworthy numbers. The root cause is that MuJoCo's collision system is
built for contact between simple rigid shapes; a smooth road edge has to be assembled
from several shapes (multiple simultaneous contacts) or from flat facets (contact
jumping between facets). This led to the custom contact model below.

### 3.14 Custom tyre–road contact for soft-edged potholes (`CONTACT_MODEL = "profile"`)

Vehicle-dynamics work commonly computes tyre–road contact directly against a road
profile instead of colliding solid shapes. This was implemented as a third option:

1. **Road profile.** The road is a sampled height profile z(x) (0.5 mm spacing,
   `road_profile`). The pothole (depth d, opening length w) has edges that fall over a
   horizontal width b with a raised-cosine shape: z = −d·(1 − cos(π·s/b))/2 across each
   edge, where s is the distance into the edge. The edge is smooth at top and bottom and
   steepest mid-way (maximum slope π·d/(2b)). b = 0 reproduces the sharp, vertical-walled
   pothole (wall points are then added to the profile). b is capped at w/2.
2. **Contact.** Before every time step, for each wheel, the profile point nearest the
   wheel centre is found. If the wheel overlaps the road by δ = R − distance, a force
   F = k·δ + c·δ̇ (never pulling) is applied at the wheel centre along the line from that
   point to the centre (`ProfileTyres`, via MuJoCo's `xfrc_applied`). There is exactly
   one contact per wheel, whatever the edge shape.
3. **Parameters (assumed):** k = 80 kN/m (static deflection ≈ 6.5–7 mm on each wheel),
   c = 500 N·s/m (light, as for a pneumatic tyre).
4. **Simplifications:** a point contact (no tyre enveloping of the edge), and no
   tangential force (free rolling, no friction or rolling resistance). MuJoCo's own
   wheel–road collision is switched off; the deck still collides with the road boxes.

**Validation before use:**

| Check | Result |
|---|---|
| Rest state | Tyre deflection 6.9 mm front / 6.4 mm rear; fork 0.6 mm; pitch 0.06° |
| Flat road | 0.01 g at the handlebar, 0% speed loss (after extending the profile beyond the end of the run, which initially caused a false jolt) |
| Cross-check vs MuJoCo contact, sharp edges (30 cases: 10/10 and 12/10, 20–100 mm, 300/600/1000 mm, 20 km/h, with suspension) | Fall / no-fall identical in **30 of 30** cases; speed loss within a median of 4.7 percentage points. Handlebar peaks are higher (e.g. 6–8 g vs 2 g on 300 mm potholes), attributed to the much lighter tyre damping than MuJoCo's critically damped contact |
| Convergence with profile resolution (2, 1, 0.5, 0.25 mm; sharp and 50 mm edges) | Converged: between 0.5 and 0.25 mm, outcomes change by under ~3% and falls are identical. This is the test the mesh approach failed |
| Physical direction | A 50 mm sloped edge lowers jolts and speed loss compared with a sharp edge (e.g. 26.8 → 17.5 g, 40.7 → 32.4% on an 80 × 1000 mm pothole) |

Because absolute handlebar peaks differ between the two contact models, soft-edge
results are compared **within** the profile model (sharp vs sloped edges under the same
contact), not against the MuJoCo-contact results.

---

### 3.15 Road bumps (`OBSTACLE = "bump"`, `--bumps`)

The same model can cross a raised obstacle instead of a pothole. `simulate()`'s depth
argument is then the bump **height** and the length is the bump's length along travel.
Two shapes (`BUMP_SHAPE`):

- **`"box"`: sharp-edged rectangular bump.** Vertical faces up and down. With MuJoCo's
  contact (the main model) this is a box geom on a continuous flat road; with the profile
  contact (section 3.14) the profile is raised instead of lowered, with points up each
  vertical face. Represents surface **defects**: a raised patch or reinstatement, a
  utility cover proud of the surface, a lifted slab edge, a tree-root ridge. Legal UK road
  humps may not have a vertical face above 6 mm (Highways (Road Humps) Regulations 1999,
  reg. 4), so this shape is not a legal road hump.
- **`"arc"`: round-top hump.** A circular arc of height h over the length L (radius
  rho = (L²/4 + h²)/2h). Profile contact only, since MuJoCo's own contact cannot follow
  curved surfaces reliably (section 3.13). 3700 mm long = the standard UK round-top road
  hump (DfT Traffic Advisory Leaflet 2/96); 600 mm = a short car-park style bump, below
  the 900 mm legal minimum for road humps on the highway. With the profile contact the
  MuJoCo road boxes only catch the deck; for the arc they are a flat road, because the
  deck clearance (>= 140 mm) exceeds every hump height modelled (<= 100 mm).

**Phases and fall attribution for bumps.** The pothole rules (section 3.10, 3.11) do not
transfer: the rear wheel climbs a bump rather than dipping into it, and the time-based
split put the rear wheel's strike into the "front" phase on bumps of 600 mm or more.
For bumps, the "rear" phase starts, and a fall is credited to the rear wheel, once the
rear wheel has reached the bump's leading face: its centre is within
sqrt(R² − (R − h)²) of the face (the horizontal reach of a wheel of radius R to a step
of height h).

**Extra outputs (all runs).** `rider_lean_back_max_deg` and `chassis_pitch_up_max_deg`
(backward extremes; not fall criteria, recorded to check that a bump does not cause a
backward failure the forward criteria would miss: the maximum in any bump run was 6°),
`obstacle`, and `fall_type` (`"stall"` if the scooter stopped without passing an angle
limit, else `"pitch-over"`). In practice every stalled run went on to pitch past 30°, so
`fall_type` was always "pitch-over"; the counts use the `stalled` flag (front or rear
wheel stopped dead at some point) instead.

## 4. Experiments

### 4.1 Main sweep (`python scripts/scooter_sim.py`)

| Factor | Levels |
|---|---|
| Wheel configuration (front/rear, in) | 10/10 (current, Voiager 5 assumed), 12/10, 12/12, 14/10 |
| Pothole depth | 20–100 mm in 10 mm steps |
| Pothole length | 300, 600, 1000 mm |
| Speed | 15, 20, 25 km/h |

4 × 9 × 3 × 3 = **324 runs**. For each configuration, length and speed, the shallowest
depth that caused a fall is recorded (`fall_thresholds.csv`). Depth resolution is
10 mm, so "70 vs 80 mm" means "somewhere in that interval".

### 4.2 Sensitivity analysis (`--sensitivity`)

The two least certain parameters were varied one at a time:

| Setting | Tyre time constant τ | Rider stiffness |
|---|---|---|
| Baseline | 0.025 s | 1500 N·m/rad |
| Stiffer tyre | 0.015 s | 1500 |
| Softer tyre | 0.035 s | 1500 |
| Weaker bracing | 0.025 s | 1000 |
| Stronger bracing | 0.025 s | 3000 |

For each setting and configuration: the shallowest falling depth on a 1000 mm pothole
at 20 km/h, and the speed loss on a 60 × 600 mm pothole at 20 km/h
(`sensitivity.csv`).

### 4.3 Front/rear ratio study (`--ratio`)

Configurations 10/10, 12/10, 14/10, 16/10, 20/10, 16/8 and 20/8 (front/rear diameter
ratios 1.0 to 2.5), over the same depth, length and speed grid: 7 × 81 = **567 runs**.
Outputs in `outputs/scooter_sim/ratio/`.

### 4.4 Wheel-mass check

With `SCALE_WHEEL_MASS = True`, wheel mass is 2.5 kg × (diameter / 10 in). The
shallowest falling depths for 10/10, 16/10, 20/10, 16/8 and 20/8 (1000 mm pothole, all
three speeds) were recomputed and were identical to the fixed-mass results. This check
was run from the command line, not saved as an output file; setting the flag and
rerunning `--ratio` reproduces it.

### 4.5 Animations (`--animate`)

Six comparisons are defined in `ANIMATION_SETS`, each with its own suspension setting.
A case given with an edge width uses the profile contact (section 3.14):

| Section | Pothole | Speed | Suspension | Configurations |
|---|---|---|---|---|
| Voiager 5 with its front spring | 80 × 600 mm | 15 km/h | Yes | 10/10 (falls), 12/10 (no fall) |
| Soft-edged pothole, 50 mm sloped edges | 80 × 600 mm | 15 km/h | Yes | 10/10 (falls), 12/10 and 14/10 (no fall), profile contact |
| Soft-edged pothole, 100 mm sloped edges | 90 × 600 mm | 15 km/h | Yes | 10/10 (falls), 12/10 and 14/10 (no fall), profile contact |
| Same pothole, larger front wheel | 70 × 1000 mm | 20 km/h | No | 10/10 (falls), 12/10 (no fall) |
| Front much bigger than rear | 90 × 1000 mm | 20 km/h | No | 10/10 (falls), 20/10 (no fall) |
| Where the second jolt comes from | 40 × 600 mm | 20 km/h | No | 10/10 (rear lifted clear), 20/8 (rear drops 47 mm) |

Files with suspension end in `_susp.gif`; profile-contact files end in `_edge<width>.gif`.
With the profile contact the animation draws the actual road profile.

Each case was chosen after checking the run outcomes, to show a clear contrast.

Rendering:

1. Run the simulation with recording on. The state is stored every 10 ms while the
   front wheel is between 1 m before the pothole and one wheelbase plus 1.5 m past it.
2. For each stored state, MuJoCo forward kinematics (`mj_kinematics`) gives body
   positions, drawn with Matplotlib as a stick figure: road and pothole (grey), wheels
   (blue circles), deck line between the axles and stem (black), rider (orange). The
   deck line joins the axles, so it slopes when the wheels differ in size; the simulated
   deck itself is level.
3. Frames are written to GIF with Pillow at 25 frames per second. 10 ms of simulation
   per frame shown for 40 ms gives 4× slow motion. The camera follows the front wheel.
4. `write_animation_page` embeds all GIFs (base64) in one self-contained HTML page,
   `outputs/scooter_sim/animations.html`, with captions generated from each run's
   outcomes.

### 4.6 Experiments with front suspension (`--suspension`)

The main sweep, sensitivity analysis and ratio study were all rerun with the fork
(outputs in `outputs/scooter_sim/suspension/` and `.../suspension/ratio/`). With
`--suspension`, the sensitivity analysis adds four fork settings: softer (15 kN/m) and
stiffer (40 kN/m) springs, and damping ratios 0.15 and 0.5.

### 4.7 Consistency check (`--consistency`)

Criterion, fixed before running: for the current 10/10 scooter at 20 km/h on "common"
potholes (20, 30, 40 mm deep; 300 and 600 mm long; an assumption about which potholes
are common), simulated handlebar peaks (10 ms windows, like the phone) should fall in
roughly **1–3 g**, consistent with the measured impacts: 1.0–2.97 g for 99 of 100
impacts over three rides (median 1.27 g; one at 6.28 g). Ride 1 alone: 1.0–2.8 g,
median 1.19 g; the reference was updated when Part A grew to three rides (2026-10-08),
the criterion was not. Both the
original and the suspension model are evaluated (`consistency.csv`,
`fig_consistency.png`).

### 4.8 Soft-edged potholes (`--suspension --edges`)

With the profile contact (section 3.14) and front suspension: edge widths 0 (sharp),
25, 50 and 100 mm × the four configurations × the main depth, length and speed grid
= 4 × 324 = **1296 runs**, run in parallel over 4 processor cores (`multiprocessing`;
settings are passed to each worker explicitly). Outputs in
`outputs/scooter_sim/suspension/soft_edges/`: `edge_results.csv`,
`edge_fall_thresholds.csv`, `edge_fall_counts.csv`, `fig_edges.png`.

**Tyre damping check for the profile contact.** Because the profile contact gives
higher handlebar peaks than MuJoCo's contact, the consistency cases were rerun with tyre
damping 500, 1500 and 3000 N·s/m and edge widths 0, 50 and 100 mm. More damping made
the peaks *higher* (e.g. up to 13–17 g at 3000 N·s/m), so light damping is not the
cause; the likely cause is the point contact itself, which cannot spread the load over
a contact patch or wrap around an edge as a real tyre does. Conclusion: the profile
contact is used for **falls and edge-shape comparisons** (it agrees with MuJoCo's
contact on every fall outcome and converges); MuJoCo's contact with suspension remains
the model for **absolute jolt sizes** (consistency check, section 4.7). The damping was
not changed from its pre-set 500 N·s/m.

---

### 4.9 Road bumps (`--bumps`, `--bumps --suspension`)

Cases (`BUMP_CASES`), each × the four configurations × heights 20–100 mm (10 mm steps) ×
15/20/25 km/h, run over 4 processor cores:

| Case | Shape | Contact | Lengths (mm) | Runs |
|---|---|---|---|---|
| sharp bump (main) | box | MuJoCo | 300, 600, 1000 (same as the potholes) | 324 |
| sharp bump, cross-check | box | profile | 300, 600, 1000 | 324 |
| round-top hump | arc | profile | 600, 3700 | 216 |

plus a **rear-size check** (`BUMP_REAR_CONFIGS`): 300 mm sharp bump, MuJoCo contact,
heights 50–100 mm in 5 mm steps, 3 speeds, configurations 10/10, 12/10, 14/10, 10/12,
12/12, 10/14, 14/14 (231 runs). It was added after the few suspended-model bump falls
were all met after the rear wheel's strike (DOCUMENTATION.md 6.8). It is a small,
exploratory check (one length; differences near the 5 mm grid resolution), not a test of
whether rear size improves stability.

Run without and with the front fork (1095 runs each). The pothole sweep in the parent
folder (`sim_results.csv`) is read in for the bump-vs-pothole comparison, so run the main
sweep first. Outputs in `outputs/scooter_sim/bumps/` and
`outputs/scooter_sim/suspension/bumps/`: `bump_results.csv`, `bump_fall_thresholds.csv`
(lowest falling height, potholes alongside), `bump_fall_counts.csv`,
`bump_rear_check.csv`, `bump_rear_check_thresholds.csv`, `fig_bump_falls.png`,
`fig_bump_vs_pothole.png`, `fig_bump_speed_loss.png`, `fig_bump_handlebar_g.png`.

**Contact-model cross-check.** On sharp bumps the two contact models gave the same fall /
no-fall outcome in 295/324 runs without the fork and 307/324 with it (potholes: 30/30 in
the original check). The disagreements go both ways (without fork: 25 MuJoCo-only falls,
4 profile-only; with fork: 6 and 11). A likely reason, not verified: the profile contact
has no tangential (friction) force, which matters when a wheel climbs a vertical face
but not when it drops into a hole. Bump fall counts are therefore less certain than
pothole ones; read them as comparisons between wheel configurations.

**Jolt sizes are not validated for bumps.** Sharp bumps give large simulated handlebar
peaks even with the fork (10/10, 600 mm, 20 km/h: 3.6 g at 20 mm, 8.4 g at 40 mm), above
the measured 1–2.97 g. The rides did not label bumps, so there is nothing to compare with.

### 4.11 Key-frame figures for print (`--keyframes`)

The animations cannot be printed, so `build_keyframes()` redraws selected runs as rows of
still frames (`outputs/scooter_sim/keyframes/`, copied into `paper/figures/` by
`scripts/paper_part_a.py`). One row per wheel configuration, one column per moment in
`KEYFRAME_TIMES` (−0.25, 0, +0.15, +0.3, +0.5 s), all relative to the moment the front
wheel reaches the pothole's far edge (front-wheel centre within half a radius of the
edge), so the rows can be compared column by column. The frames are drawn by
`draw_scene()`, the same function the GIFs use (refactored out of `animate()`; the GIF
drawing is unchanged). Each falling row is labelled with the time the fall criterion
(pitch or lean limit) is reached; a column after the simulation stopped shows the last
frame, marked. Sets (`KEYFRAME_SETS`, potholes only; road bumps are not in the paper):
80 × 600 mm at 15 km/h with suspension, sharp edges (10/10, 12/10, 12/12) and 50 mm
sloped edges (10/10, 12/10, 14/10). Fall criterion reached at +0.15 s and +0.42 s for
10/10; no other row falls (`keyframes_runs.csv`).

### 4.10 Animation page

`animations.html` holds the pothole clips (`ANIMATION_SETS`) and, below them, the bump
clips (`BUMP_ANIMATION_SETS`). `python scripts/scooter_sim.py --bumps --animate`
renders only missing GIFs (existing ones are reused; their captions come from re-running
the same simulation) and rewrites the page; `--animate` re-renders everything. The page
embeds every GIF and is about 15 MB.

## 5. Development history and calibration decisions

The model was developed iteratively. Each change below was made in response to a
specific check, not to steer the results towards a desired answer.

| Step | Observation | Change |
|---|---|---|
| 1. First runs | Contact time constant 0.006 s (near-rigid). A 30 mm pothole gave 6.5 g at the handlebar and 60 mm gave 48 g; measured impacts were 1–2.8 g | Contact softened to τ = 0.025 s, matched to pneumatic tyre stiffness (section 3.7). Falls at 60 × 600 mm disappeared, showing fall depth depends on tyre stiffness; hence the sensitivity analysis |
| 2. Baseline check | A "1 mm pothole" still showed 0.7–0.9 g | Pothole moved from 1.5 m to 5.0 m ahead for a longer run-up, and recording limited to near the pothole. A truly flat road then gave 0.04 g; the remaining 0.7 g came from the 1 mm sharp step itself |
| 3. Animations | The first animation was mostly run-up and showed a no-fall case for both configurations | Frames limited to the pothole region; cases chosen to show fall vs no fall; title split over two lines |
| 4. Phase split | Splitting phases when the rear wheel reached the pothole mislabelled the front wheel's impact as "rear" for potholes longer than the wheelbase | Split at the far edge plus half a wheelbase (section 3.10). A trace of wheel positions revealed the front impact lifting the rear wheel ~137 mm over the pothole |
| 5. Fall attribution | Falls were first credited by time, which labelled slow pitch-overs with big front wheels as "rear-wheel" falls | Credit by cause: rear only if the rear wheel had dipped into the pothole first (section 3.11). No fall was rear-caused |
| 6. Wheel mass | All wheels weighed 2.5 kg regardless of size | Optional scaling added; results unchanged (section 4.4) |
| 7. Front suspension | First version settled with the fork 29 mm over-extended and runs broke down | The wheel was colliding with the deck (no longer a direct child of the chassis); contact excluded (section 3.12) |
| 8. Rounded edges | Jolts rose instead of falling; mesh version did not converge | Feature dropped from MuJoCo's contact (section 3.13) |
| 10. Custom profile contact | Needed to simulate potholes without hard edges | Own tyre–road contact against a road profile (section 3.14). A first flat-road test showed a false 5.8 g jolt: the profile ended before the run did, so the wheel dropped off its end; profile extended to 40 m past the pothole. Then validated (rest state, flat road, cross-check, convergence) before use |
| 9. Vehicle confirmed | The user confirmed SZ22 is a Voiager 5 | 10 in front wheel and front spring confirmed; the suspension model is the more faithful one. Rear wheel size still assumed (10 in) |
| 11. Road bumps | Bumps added (section 3.15). Roadblocks and fixes are listed in section 5.1 | Position-based phases and fall attribution for bumps; arc humps on the profile contact only; rear-size check added |

The earliest stiff-contact runs happened to reproduce the Imperial study's pattern (no
fall at 30 mm, fall at 60 mm). The model was **not** tuned towards that pattern; after
the tyre correction the 60 × 600 mm case no longer falls at 20 km/h.

### 5.1 Road bumps: struggles and roadblocks (2026-10-07)

Recorded so the paper's methods and any reviewer questions can be answered honestly.

| # | Roadblock | What happened | Resolution / status |
|---|---|---|---|
| 1 | Curved humps with MuJoCo's contact | MuJoCo's own collision only handles the sharp box reliably (rounded shapes failed before, section 3.13) | Round-top humps run on the profile contact only; sharp bumps on both. The arc case has no MuJoCo cross-check |
| 2 | Pothole fall attribution doesn't transfer | "Rear-caused" meant "rear wheel dipped into the pothole", which a bump never causes | Bump rule: rear wheel had reached the bump's leading face before the fall (section 3.15) |
| 3 | Phase split mislabelled the rear strike | The time-based split (front wheel half a wheelbase past the far edge) put the rear wheel's strike into the "front" phase for 600/1000 mm bumps | Position-based split for bumps; both bump studies rerun. Fall outcomes were unaffected, only per-phase columns |
| 4 | "Stall" fall type never fired | Every run where a wheel stopped dead went on to pitch past 30°, so all falls were labelled "pitch-over" | Counts use the `stalled` flag instead; `fall_type` kept but documented as uninformative here |
| 5 | Plot crash after the first full sweep | The bump results rename `depth_mm` to `height_mm`, and the shared figure function expected `depth_mm`; the sweep finished, then the figure step failed | Renamed for the figure call; sweep rerun (~5 min) |
| 6 | Contact models disagree more on bumps | 91–95% agreement on fall outcomes vs 100% for potholes, in both directions | Reported as an uncertainty (section 4.9); comparisons between wheel sizes used, not absolute counts |
| 7 | A pattern that does not fit the working hypothesis | With the front fork, the few bump falls (1–2 per configuration, 300 mm bump, 15 km/h) were all met after the **rear** wheel's strike; in a small follow-up check, larger rear wheels raised the falling height by 5–15 mm (10/14: none up to 100 mm), front size did not | Reported as found, as an exploratory pattern and open question, not as a finding (DOCUMENTATION.md 6.8). Not tuned away. Would need bump sensitivity runs and a wider sweep before any statement about rear size |
| 8 | Jolt sizes can't be checked | Simulated bump jolts (3–15 g) are above the measured range, and the ride has no bump labels | Bump jolts not used as results; a labelled ride would be needed to check them |
| 12 | No bump sensitivity analysis | The fork changes bump outcomes far more than pothole outcomes (10/10: 22 -> 1 falls), but fork, tyre and bracing parameters were not varied for bumps | Open; listed as an uncertainty |
| 9 | Source for the hump profile | The 3.7 m round-top length was not in the first leaflet checked (TAL 7/96) | Found in TAL 2/96 ("a standard 3.7m long"); the 1999 Regulations (length >= 900 mm, 25–100 mm high, no vertical face > 6 mm) checked on legislation.gov.uk. Added to REFERENCES.md |
| 10 | Tooling (no effect on results) | Shell heredocs on Windows mangled `\n` and `·` in code patches (syntax error, failed matches); a `multiprocessing` check run from stdin hung for 10 min because Windows worker processes must re-import the script from a file | Patches written as UTF-8 files; the check moved into `scooter_sim.py` as the rear-size check |
| 11 | Rebuilding the animation page | Adding bump clips to the existing page would have re-rendered all pothole GIFs | `reuse` option: existing GIFs kept, captions recomputed from the same simulation |

---

## 6. Verification and validation

| Check | Result |
|---|---|
| Flat road (0 mm) | 0.04 g at the handlebar, no speed loss: no spurious impacts |
| Direction of effects | Deeper and longer potholes give more speed loss and more falls; larger wheels give less, consistent with the geometry model |
| Short potholes | No falls for 300 mm potholes, consistent with the geometry model's time-to-fall limit |
| Determinism | Full rerun of the main sweep and sensitivity analysis reproduced all outcomes exactly |
| Sensitivity | The comparison between configurations (12/10 = 12/12; larger front delays the fall) held under all five settings; absolute fall depths for 10/10 moved between 60 and 70 mm |
| Consistency with measurements, **no suspension: failed** | 4.9–9.8 g on the common potholes, against 1–2.97 g measured (99 of 100 impacts, three rides): about 3–5× too harsh |
| Consistency with measurements, **with suspension: partial pass** | 300 mm long potholes: 1.9–2.4 g (**inside** the measured range). 600 mm long: 4.2–5.7 g (about twice too high; only one of 100 measured impacts, 6.28 g, was higher) |

The model has **not been validated** against physical tests. Its results should be
reported as comparisons between wheel configurations under identical assumptions, not
as predictions of real fall depths or accelerations.

---

## 7. Limitations

- **Planar:** no steering, handlebar twist, roll or sideways falls. Loss of steering
  control, one of the two front-wheel dangers, is not represented.
- **Suspension is simplified:** an optional linear spring-damper fork with assumed
  values; no rear suspension; Voi's actual fork specification is unknown. Without it,
  absolute accelerations are 3–5× too high; with it, about right for short potholes
  and about 2× too high for 600 mm ones.
- **Pothole shape:** the main results use sharp rectangular potholes. Sloped edges are
  covered by the profile contact (sections 3.14, 4.8), whose point contact has no tyre
  enveloping, so its absolute jolts are too high; real potholes are also irregular,
  which neither model represents.
- **Rigid wheels with soft contact:** tyre enveloping of the edge is not modelled.
- **Simplified rider:** one rigid body with a fixed spring; no active balance, arm
  forces, knee bending or reaction to the impact.
- **Coasting only:** no motor torque or braking.
- **Assumed vehicle parameters:** scooter mass, wheelbase, deck and handlebar heights,
  inertias, tyre compliance and rider bracing are not published by Voi.
- **Redesigned frame assumed:** the deck is kept level for every wheel combination.
- **Fall criteria** are analyst-defined thresholds.
- **Depth resolution** is 10 mm.
- **Rear wheel size assumed:** the ridden vehicle (SZ22) is confirmed as a Voiager 5
  with a 10 in front wheel; its rear wheel size is not published and is assumed 10 in.

---

## 8. Reproducing everything

```
pip install mujoco numpy pandas scipy matplotlib pillow

python scripts/wheel_geometry.py                 # geometry model -> outputs/wheel_model/
python scripts/scooter_sim.py                    # main sweep (324 runs) -> outputs/scooter_sim/
python scripts/scooter_sim.py --sensitivity      # sensitivity analysis
python scripts/scooter_sim.py --ratio            # ratio study (567 runs) -> outputs/scooter_sim/ratio/
python scripts/scooter_sim.py --animate          # main sweep + animations + animations.html
python scripts/scooter_sim.py --consistency      # consistency check vs the measured ride
python scripts/scooter_sim.py --suspension                 # main sweep with front fork -> .../suspension/
python scripts/scooter_sim.py --suspension --sensitivity   # incl. fork stiffness/damping settings
python scripts/scooter_sim.py --suspension --ratio         # ratio study with front fork
python scripts/scooter_sim.py --suspension --edges         # soft-edged potholes (profile contact, 1296 runs, 4 cores)
python scripts/scooter_sim.py --bumps                      # road bumps, no fork (1095 runs, 4 cores) -> .../bumps/
python scripts/scooter_sim.py --bumps --suspension         # road bumps with front fork -> .../suspension/bumps/
python scripts/scooter_sim.py --bumps --animate            # add the bump clips to animations.html
```

To change a scenario, edit the constants at the top of `scooter_sim.py` (`CONFIGS`,
`DEPTHS_MM`, `LENGTHS_MM`, `SPEEDS_KMH`, `RATIO_CONFIGS`, `ANIMATION_SETS`) or a
parameter (e.g. `WHEELBASE`, `TYRE_TIMECONST`). On Windows, close any output figure
open in an image viewer before rerunning, or saving it will fail.

### Output files

| File | Contents |
|---|---|
| `outputs/scooter_sim/sim_results.csv` | One row per run of the main sweep, all outcomes including per-phase columns |
| `outputs/scooter_sim/fall_thresholds.csv` | Shallowest falling depth per configuration, length and speed |
| `outputs/scooter_sim/sensitivity.csv` | Sensitivity analysis |
| `outputs/scooter_sim/fig_speed_loss.png`, `fig_rider_lean.png`, `fig_handlebar_g.png` | Main sweep figures at 20 km/h (✕ = fall) |
| `outputs/scooter_sim/ratio/ratio_results.csv`, `ratio_fall_thresholds.csv` | Ratio study |
| `outputs/scooter_sim/ratio/fig_ratio_first_fall.png`, `fig_ratio_rear_wheel.png` | Ratio study figures |
| `outputs/scooter_sim/anim_*.gif`, `animations.html` | Animations and the page that shows them |
| `outputs/scooter_sim/consistency.csv`, `fig_consistency.png` | Consistency check |
| `outputs/scooter_sim/suspension/...` | The same outputs (sweep, sensitivity, ratio study) with front suspension |
| `outputs/scooter_sim/suspension/soft_edges/...` | Soft-edged pothole study (results, fall depths, fall counts, figure) |
| `outputs/scooter_sim/bumps/...`, `outputs/scooter_sim/suspension/bumps/...` | Road bump study without / with the front fork (section 4.9) |
| `outputs/scooter_sim/anim_bump_*.gif` | Bump clips, shown in `animations.html` |

---

## 9. Parameter summary

| Parameter | Value | Source |
|---|---|---|
| Front wheel, current | 10 in | Voiager 5 spec (Levy); ridden vehicle SZ22 confirmed as a Voiager 5 |
| Rear wheel, current | 10 in | Reported as 10 in without front/rear distinction (Levy; Alsalkini 2023) |
| Tyre type | Pneumatic (τ = 0.025 s) | Disputed: Levy says pneumatic, another summary says solid honeycomb; stiffer tyres raise simulated jolts but don't change fall rankings (checked τ = 0.015 and 0.010 s with suspension) |
| Front fork (optional) | 25 kN/m, damping ratio 0.3, 30 mm travel, preload 50% of sprung weight | Assumed (section 3.12) |
| Profile contact (optional) | Tyre 80 kN/m, 500 N·s/m; profile sampled every 0.5 mm; edge widths 0–100 mm (raised cosine) | Assumed (section 3.14) |
| Front wheel, Voiager 7 | 12 in | Voi / press (rear not published) |
| Scooter mass | 32 kg | Assumed (Voiager 7 reported at 36 kg) |
| Wheelbase | 0.95 m | Assumed |
| Deck height (10 in wheels) | 0.16 m | Assumed |
| Handlebar height | 1.05 m | Assumed |
| Wheel mass | 2.5 kg | Assumed |
| Wheel width | 0.06 m | Assumed |
| Rider | 76 kg, 1.70 m, CoM at 55% of height | Imperial study's 50th percentile male; CoM fraction assumed |
| Rider bracing | 1500 N·m/rad, 150 N·m·s/rad | Assumed (section 3.5) |
| Friction | 0.9 | Dry asphalt, assumed |
| Tyre compliance | τ = 0.025 s (~80 kN/m) | Assumed (section 3.7) |
| Time step | 0.5 ms | Numerical choice |
| Fall thresholds | 30° lean, 30° pitch, 0.5 m/s stall | Analyst-defined |
