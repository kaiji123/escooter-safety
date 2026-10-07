<!--
DRAFT v0.1 (2026-10-07). Part B of the paper: wheel-size models, methods and results.
Citations use Pandoc keys from ../references.bib, e.g. [@posirisuk2022].
Build later with: pandoc part_b_methods_results.md --citeproc --bibliography ../references.bib -o part_b.docx
Every number below is taken from outputs/ (paths given in the HTML comments) or from
SIMULATION_METHODS.md. Re-check them if any simulation is rerun.
Wheel sizes for the Voiager 5 are the reported 10/10 (stated assumption; see DOCUMENTATION.md 12).
-->

# 3 Methods: modelling the effect of wheel size

## 3.1 Overview

Rental e-scooters are the only e-scooters that may legally be ridden on UK public roads,
so a scooter with modified wheels cannot be tested on the road. We therefore used two
models, in the same way as the Imperial College study of e-scooter falls this work builds
on [@posirisuk2022]:

1. a **geometry model**, which describes how far a single wheel drops into a pothole and
   how hard it strikes the far edge, and
2. a **planar multibody dynamics model** of scooter and rider in MuJoCo
   [@todorov2012mujoco], which predicts whether the scooter pitches over.

Both models compare wheel configurations under identical assumptions. They are not
validated against physical tests, so we report relative differences between
configurations, not real-world fall thresholds.

## 3.2 Wheel configurations

Configurations are written front/rear diameter in inches (nominal size taken as tyre
outer diameter).

| Configuration | Meaning |
|---|---|
| 10/10 | Current vehicle (Voi Voiager 5), using the reported 10 in wheel size [@levy_voiager5; @alsalkini2023]; the front/rear split is not published, so equal wheels are assumed |
| 12/10 | Larger front wheel only, as on Voi's Voiager 7 (12 in front) [@startups2024voiager7] |
| 12/12 | Larger wheels front and rear |
| 14/10 | Much larger front wheel only |

A front/rear ratio study added 16/10, 20/10, 16/8 and 20/8 (ratios up to 2.5).

## 3.3 Geometry model

A rigid wheel of radius $R$ rolls at speed $v$ across a rectangular pothole of depth $d$
and length $w$ with sharp edges. The wheel's lowest point sinks below road level by

$$h = \min\left(d,\; R - \sqrt{R^2 - (w/2)^2},\; \tfrac{1}{2} g \left(\tfrac{w}{v}\right)^2\right),$$

the smallest of the depth, the sag of a wheel resting on both edges, and the free-fall
distance in the time taken to cross (an upper bound). The far edge then meets the tyre at
an angle $\theta$ from vertical, with $\cos\theta = (R-h)/R$. Treating the impact as
plastic, the velocity lost into the edge is $v\sin\theta$ and the forward speed loss of
the axle is $v\sin^2\theta$. A larger wheel gives a smaller $\theta$ for the same pothole,
so both quantities fall. Each wheel is analysed separately, so this model cannot say
whether the scooter falls; that requires the dynamics model.

The geometry model was evaluated for 8–16 in wheels, speeds of 15, 20 and 25 km/h,
depths of 0–120 mm and lengths of 150–1000 mm (`scripts/wheel_geometry.py`).

## 3.4 Dynamics model

**Structure.** The model is planar (side view) with six degrees of freedom: forward
position, height and pitch of the chassis; rotation of each wheel; and forward lean of
the rider. It follows the structure of @posirisuk2022, who modelled the scooter as the
front wheel and the rest of the scooter joined at the axle, but adds a separate rear
wheel, so that front-only and front-and-rear changes can be compared, and a rider. The
rider is a single rigid body pinned to the deck at the feet; a rotational spring
(1500 N·m/rad) and damper (150 N·m·s/rad) represent the rider bracing with legs and arms,
chosen so that braking at 0.3 g leans the rider about 8° forward.

**Parameters.** Voi does not publish the vehicle's mass properties, so most parameters
are assumed (Table 1). The rider's mass and height match the median male model of
@posirisuk2022.

*Table 1. Main model parameters.*

| Parameter | Value | Source |
|---|---|---|
| Scooter mass | 32 kg | Assumed (Voiager 7 reported at 36 kg [@startups2024voiager7]) |
| Wheel mass | 2.5 kg each | Assumed; scaling with diameter did not change results |
| Wheelbase | 0.95 m | Assumed |
| Deck height | 0.16 m (10 in wheels), rising with wheel size; deck kept level | Assumed |
| Handlebar height | 1.05 m | Assumed |
| Rider | 76 kg, 1.70 m, centre of mass at 55% of height | @posirisuk2022; centre-of-mass fraction assumed |
| Tyre compliance | Contact time constant 0.025 s (≈80 kN/m, ≈6 mm static deflection) | Assumed, typical small pneumatic tyre |
| Front fork | 25 kN/m, damping ratio 0.3, 30 mm travel | Assumed; the Voiager 5 has a front spring [@levy_voiager5] |
| Friction | 0.9 | Dry asphalt, assumed |
| Integration | Implicit-fast, 0.5 ms time step | Numerical choice |

**Tyre contact.** Wheels are rigid cylinders whose contact with the road is softened
through MuJoCo's soft-contact parameters to represent tyre compliance.

**Front suspension.** Because the Voiager 5 has a front spring, the main results use a
sprung front fork (Table 1). Its values were fixed before any run and tested in the
sensitivity analysis. Results without suspension are reported for comparison.

**Pothole.** The main experiments use a rectangular pothole with vertical walls and sharp
edges, 5 m after the start, giving about 1 s of run-up. To test potholes with broken
edges, a second contact model computes tyre–road contact directly against a sampled road
profile in which each edge falls over a width $b$ with a raised-cosine shape (0, 25, 50 or
100 mm). It applies one radial spring-damper force per wheel. Before use, it was checked
on a flat road (0.01 g at the handlebar), for convergence with profile resolution, and
against MuJoCo's own contact on sharp edges, where fall outcomes agreed in 30 of 30 cases.
Its absolute accelerations are too high because a point contact cannot envelop an edge,
so it is used only to compare falls between edge shapes.

**Procedure.** Each run settles the model at rest for 0.5 s, sets the forward speed and
matching wheel spin, and lets the scooter coast (no motor or braking, no steering)
across the pothole.

**Outcomes.** Speed loss, maximum scooter pitch and rider lean, and peak acceleration at
the handlebar, where the phone was mounted. The handlebar acceleration is averaged over
10 ms windows to match the phone's 100 Hz sampling.

**Fall definition.** A run counts as a fall if the rider leans more than 30° forward,
the scooter pitches more than 30° nose-down, or forward speed drops below 0.5 m/s. These
thresholds are analyst-defined and were fixed before any experiment. A fall is attributed
to the rear wheel only if the rear wheel dipped more than 5 mm into the pothole before
the fall; otherwise it is attributed to the front-wheel impact.

## 3.5 Experiments

*Table 2. Simulation experiments.*

| Experiment | Design | Runs |
|---|---|---|
| Main sweep | 4 configurations × 9 depths (20–100 mm) × 3 lengths (300, 600, 1000 mm) × 3 speeds (15, 20, 25 km/h); with and without front suspension | 324 each |
| Sensitivity | Tyre stiffness (τ = 0.015, 0.035 s), rider bracing (1000, 3000 N·m/rad) and, with suspension, fork stiffness (15, 40 kN/m) and damping (ratio 0.15, 0.5), varied one at a time | 5 settings (9 with suspension) × 4 configurations |
| Front/rear ratio | 7 configurations from 10/10 to 20/8 on the main grid | 567 each |
| Soft edges | Profile contact with suspension; edge widths 0, 25, 50, 100 mm × main sweep | 1296 |
| Consistency check | 10/10 at 20 km/h on assumed common potholes (20–40 mm deep, 300 and 600 mm long) | 6 per model (with and without suspension) |

The depth grid has a 10 mm resolution, so a reported threshold of "80 mm" means a first
fall somewhere between 70 and 80 mm. All runs are deterministic; rerunning the main sweep
and sensitivity analysis reproduced every outcome exactly. Analysis used NumPy, pandas
and Matplotlib [@harris2020numpy; @mckinney2010pandas; @hunter2007matplotlib]; animations
were drawn with Matplotlib and encoded with Pillow [@pillow].

**Consistency check.** The criterion, fixed before running, was that simulated
handlebar peaks for the current scooter on common potholes should fall within roughly
1–3 g, the range measured on the ride (Part A: 1.0–2.8 g). Pothole depths along the
route were not measured, so this is a consistency check, not a validation.

# 4 Results: what a larger front wheel would change

## 4.1 Geometry

At 20 km/h on a 600 mm long pothole, a 12 in front wheel reduced the edge impact
velocity by 6.5–7.7% and the front-wheel speed loss by 12.6–14.8% compared with a 10 in
wheel; a 14 in wheel reduced them by 12.1–13.9% and 22.6–25.8% (Table 3). At speed, wheels barely dropped
into short potholes (about 3 mm into a 150 mm pothole at 20 km/h), so long potholes are
the more dangerous ones.

<!-- outputs/wheel_model/configurations.csv -->
*Table 3. Front-wheel edge impact at 20 km/h, 600 mm pothole (geometry model).*

| Front wheel | Depth 30 mm: impact velocity / speed loss | Depth 60 mm: impact velocity / speed loss |
|---|---|---|
| 10 in | 3.59 m/s / 41.7% | 4.64 m/s / 69.8% |
| 12 in | 3.31 m/s / 35.5% (−7.7% / −14.8%) | 4.34 m/s / 61.0% (−6.5% / −12.6%) |
| 14 in | 3.09 m/s / 30.9% (−13.9% / −25.8%) | 4.08 m/s / 54.0% (−12.1% / −22.6%) |

At 60 mm and deeper, the drop is limited by the time available to fall (57 mm), so the
60 and 90 mm results are identical.

## 4.2 Falls with the Voiager 5's front suspension

<!-- outputs/scooter_sim/suspension/sim_results.csv, fall_thresholds.csv -->
With front suspension, falls occurred in 9 of 81 runs for the current 10/10
configuration, 6 for 12/10, 6 for 12/12 and 1 for 14/10 (Table 4). No 300 mm long
pothole caused a fall at any depth up to 100 mm; 600 mm potholes caused falls only at
15 km/h, where the slower wheel has more time to drop.

*Table 4. Shallowest pothole depth (mm) causing a fall, with front suspension
(– = no fall up to 100 mm). Rows with no falls in any configuration are omitted.*

| Length, speed | 10/10 | 12/10 | 12/12 | 14/10 |
|---|---|---|---|---|
| 600 mm, 15 km/h | 80 | 90 | 90 | – |
| 1000 mm, 15 km/h | 90 | 100 | 100 | – |
| 1000 mm, 20 km/h | 90 | 90 | 90 | 100 |
| 1000 mm, 25 km/h | 90 | 100 | 100 | – |
| **Falls (of 81 runs)** | **9** | **6** | **6** | **1** |

Every fall in every configuration was a forward pitch-over of scooter and rider about the
front wheel, started by the front-wheel impact; the rear wheel was lifted clear and never
entered the pothole before a fall. This matches the mechanism reported by
@posirisuk2022.

The benefit of a 12 in front wheel was modest with suspension: it delayed the first fall
by 10 mm in three of the four cases above, and speed loss on a 60 × 600 mm pothole at
20 km/h was 25.5% against 27.6% for 10/10. A 14 in front wheel almost eliminated falls in
the tested range.

Without suspension, falls were more frequent (15, 14, 14 and 11 of 81 runs for 10/10,
12/10, 12/12 and 14/10), began at 70–80 mm for the current scooter, and the 12 in front
wheel delayed the fall by 10 mm on a 1000 mm pothole at 20 km/h (70 → 80 mm). The front
suspension itself therefore had a large effect, comparable to enlarging the front wheel.

## 4.3 A larger front wheel alone performs like larger wheels front and rear

The central comparison of the hypothesis is 12/10 against 12/12. In the main sweep they
had the same number of falls and the same shallowest falling depth in every case, both
with suspension (Table 4) and without. The reason is visible in the simulations: with
10–12 in wheels, the front-edge impact lifts the rear of the scooter so that the rear
wheel skips over the pothole, so its size makes almost no difference to whether the
scooter falls.

## 4.4 Sensitivity

<!-- outputs/scooter_sim/sensitivity.csv, outputs/scooter_sim/suspension/sensitivity.csv -->
Without suspension, the 12/10 configuration fell at the same depth as 12/12, and 10 mm
deeper than 10/10, under all five tyre and bracing settings; the current scooter's
first fall on a 1000 mm pothole at 20 km/h moved between 60 and 70 mm with tyre
stiffness. With suspension, 12/10 and 12/12 fell at the same depth in 8 of 9 settings
(the exception, more fork damping, differed by 10 mm). The ordering of configurations was
therefore robust, but absolute fall depths depend on assumed parameters and should not be
read as real-world thresholds.

## 4.5 Potholes without sharp edges

<!-- outputs/scooter_sim/suspension/soft_edges/edge_fall_counts.csv -->
*Table 5. Number of falls (of 81 runs) by edge width, profile contact with suspension.*

| Edge width | 10/10 | 12/10 | 12/12 | 14/10 |
|---|---|---|---|---|
| 0 mm (sharp) | 8 | 6 | 6 | 4 |
| 25 mm | 8 | 5 | 6 | 4 |
| 50 mm | 7 | 5 | 5 | 4 |
| 100 mm | 4 | 3 | 3 | 2 |

Sloped edges reduced falls (10/10: 8 to 4 from sharp to 100 mm edges). At every edge
width, the configurations with a larger front wheel fell less often than the current
scooter, and 12/10 stayed within one fall of 12/12.

## 4.6 How much larger should the front wheel be?

<!-- outputs/scooter_sim/ratio/, outputs/scooter_sim/suspension/ratio/ -->
In the ratio study, falls kept decreasing as the front wheel grew. Without suspension,
the 10/10, 12/10, 14/10, 16/10, 16/8, 20/10 and 20/8 configurations fell in 15, 14, 11,
9, 9, 1 and 1 of 81 runs; with suspension, in 9, 6, 1, 1, 1, 0 and 0. No front/rear ratio
up to 2.5 made falls more likely. With very large front wheels the front impact no
longer lifts the rear, so the rear wheel drops into the pothole and causes a second
jolt: the largest rear-crossing speed loss at 20 km/h (no suspension, runs without a
fall) rose from 19% for 10/10 to 27% for 20/10 and 33% for 20/8. This second jolt caused
no falls in the model, but it would affect comfort and control. Because the planar model
cannot represent steering, frame geometry, weight or cost, these results support a
moderate increase in front wheel size (12–14 in) rather than the largest possible wheel.

## 4.7 Consistency with the measured ride

<!-- outputs/scooter_sim/consistency.csv -->
With front suspension, simulated handlebar peaks for the current scooter on 300 mm long
potholes were 1.9–2.4 g, inside the measured range of 1.0–2.8 g. On 600 mm potholes they
were 4.2–5.7 g, about twice the largest measured value. Without suspension they were
4.9–9.8 g, three to five times too high. The suspension model is therefore the more
faithful representation of the Voiager 5 and is used for the main results, with the
caveat that its absolute accelerations are reliable only for short potholes.

## 4.8 Limitations of the models

- **Planar:** no steering, handlebar twist, roll or sideways falls. Loss of steering
  control, which a front-wheel impact can also cause, is not represented.
- **Assumed vehicle:** mass, inertias, wheelbase, tyre stiffness, fork and the rear wheel
  size are not published by Voi.
- **Simple rider:** one rigid body with a fixed spring; no active balance or reaction.
- **Idealised potholes:** rectangular, or with smooth sloped edges; real potholes are
  irregular.
- **Analyst-defined falls** and a 10 mm depth resolution.
- **Not validated** against physical tests; the consistency check is only a partial pass.

Within these limits, the models consistently show that the front wheel determines whether
the scooter pitches over, and that enlarging the front wheel alone gives the same benefit
in the model as enlarging both wheels.
