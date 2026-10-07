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
roughly **1–3 g**, consistent with the measured 1.0–2.8 g (median 1.19 g). Both the
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

The earliest stiff-contact runs happened to reproduce the Imperial study's pattern (no
fall at 30 mm, fall at 60 mm). The model was **not** tuned towards that pattern; after
the tyre correction the 60 × 600 mm case no longer falls at 20 km/h.

---

## 6. Verification and validation

| Check | Result |
|---|---|
| Flat road (0 mm) | 0.04 g at the handlebar, no speed loss: no spurious impacts |
| Direction of effects | Deeper and longer potholes give more speed loss and more falls; larger wheels give less, consistent with the geometry model |
| Short potholes | No falls for 300 mm potholes, consistent with the geometry model's time-to-fall limit |
| Determinism | Full rerun of the main sweep and sensitivity analysis reproduced all outcomes exactly |
| Sensitivity | The comparison between configurations (12/10 = 12/12; larger front delays the fall) held under all five settings; absolute fall depths for 10/10 moved between 60 and 70 mm |
| Consistency with measurements, **no suspension: failed** | 4.9–9.8 g on the common potholes, against 1–2.8 g measured: about 3–5× too harsh |
| Consistency with measurements, **with suspension: partial pass** | 300 mm long potholes: 1.9–2.4 g (**inside** the measured range). 600 mm long: 4.2–5.7 g (about twice too high) |

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
