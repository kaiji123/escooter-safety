# E-scooter pothole impacts in Oxford: project documentation

Record of the work done on 3 October 2026: what was built, how it works, what it
found, which decisions were made along the way, and what is still open.

---

## 1. Aim

**Research question.** Do pothole impacts on the current Voi e-scooter reach levels
associated with loss of stability, and would a larger front wheel reduce them?

**Working hypothesis.** Because the front wheel both steers and takes the peak load at
impact, enlarging the front wheel alone gives most of the stability benefit of larger
wheels.

**Audience.** Voi, Oxfordshire County Council, the Department for Transport, the local
MP and road-safety groups such as PACTS.

The aim was reframed during the session: from "proving Voi scooters are unsafe" to a
hypothesis that the data could contradict. A test that could fail is more persuasive
to reviewers and policymakers than a conclusion fixed in advance.

### Planned paper structure

| Part | Content | Status |
|---|---|---|
| A. What riders experience | Measured impacts, hotspots, comparison with FixMyStreet | Done for one ride |
| B. What a larger front wheel would change | Geometry model and MuJoCo dynamics simulation | First versions done |
| C. What should change | Regulatory gap: London requires a larger front wheel, national trial rules do not; extend a front-wheel minimum to all trials; call for physical testing (section 12) | Argument decided 2026-10-07; to write |

Only rental scooters in official trials are legal on UK public roads; private
e-scooters are legal only on private land with permission. A modified scooter
therefore can't be tested on the road, which is why Part B uses simulation, as did
the Imperial College study the work builds on.

---

## 2. Data

### 2.1 Sensor recordings

Three recordings so far, all on the same phone (layout and details: `data/README.md`;
data quality and walking detection: section 2.4 and `SENSOR_VALIDITY.md`):

| Folder (`data/raw/`) | Start (local) | Length | Content |
|---|---|---|---|
| `2026-10-03_1830_rec01` | 2026-10-03 18:30:29 | 13.7 min | Voi ride: the Part A pilot ride, details below |
| `2026-10-07_1037_rec02` | 2026-10-07 10:37:06 | 35.3 min | Ride, then walking from ~10:46:47, then phone mostly still |
| `2026-10-07_1338_rec03` | 2026-10-07 13:38:34 | 11.4 min | Ride |

Part A results (sections 3-4) use recording 1 only. Recordings 2 and 3 have been run
through the same impact pipeline (outputs in `outputs/recordings/<recording>/`, overview
in `outputs/index.html`) but are not yet part of the Part A results; their vehicle IDs were
not recorded. First look, riding only (speed gate >= 7 km/h):

| Recording | km ridden | Impacts | per km | Median g | Max g |
|---|---|---|---|---|---|
| 1 | 2.89 | 40 | 13.8 | 1.19 | 2.80 |
| 2 | 1.48 | 39 | 26.4 | 1.34 | 2.87 |
| 3 | 1.71 | 21 | 12.3 | 1.67 | 6.28 |

Not checked yet:
- Recording 2's impacts 25-37 form a regular series (every ~0.6-1.2 s at ~8 km/h over
  ~20 m): possibly a periodic surface or pushing with a foot. They raise its per-km rate.
- Recording 3's strongest cluster (impacts 9-13, up to 6.28 g) lies within ~20 m of a
  recording 2 hotspot (51.7508, -1.2389): a candidate for the Street View check.
- The walk in recording 2 produced 11 peaks >= 1 g; the speed gate excluded all of them.

**Recording 1 (pilot ride)**

| Item | Value |
|---|---|
| Date | 3 October 2026, 18:30:29 BST (Europe/London); Sensor Logger's metadata shows 17:30:29 because it is UTC |
| Vehicle | Voi **Voiager 5**, vehicle ID SZ22 (confirmed by the rider): 10 in pneumatic front wheel, front spring |
| Phone | iPhone 11 Pro Max, handlebar mount, Sensor Logger app 1.67.1 |
| Duration | 13.7 min recorded, 9.6 min moving |
| Distance | 2.89 km, mean moving speed 18.1 km/h |

Files (in `data/raw/2026-10-03_1830_rec01/`, moved from the project root on 2026-10-07 with
identical checksums; raw data is only read, never modified):

| File | Contents |
|---|---|
| `Accelerometer.csv` | Acceleration with gravity removed, device frame, m/s², ~100 Hz |
| `Gravity.csv` | Gravity vector, device frame, m/s², same timestamps |
| `Gyroscope.csv` | Angular rate, rad/s, ~100 Hz |
| `Location.csv` | GPS, ~1 Hz |
| `Orientation.csv`, `*Uncalibrated.csv`, `Metadata.csv` | Supporting data |
| `Barometer.csv`, `Annotation.csv` | Empty |

The units were checked: `Accelerometer.csv` plus `Gravity.csv` reproduces the raw
uncalibrated reading. The project brief described an Android phone; the recording was
made on an iPhone, which the methods section must reflect.

### 2.2 Study roads

Marston Road, Headington Road (including Headington Hill), Old Road (Headington) and
Morrell Avenue. Cheney Lane, in the original brief, was dropped because it wasn't
ridden. A second "Old Road" exists at Forest Hill / Shotover; the study bounding box
excludes it.

This ride covered Marston Road, Morrell Avenue and part of Old Road. **It did not
include Headington Road.**

### 2.3 External data

| Source | Use | Stored as |
|---|---|---|
| OpenStreetMap (via Overpass API) | Road centrelines for the study roads | `data/osm_study_roads.json` |
| FixMyStreet (mySociety) | Public road-surface reports in the ride area | `data/fixmystreet/reports.csv` |
| Voi specifications and press | Wheel sizes | Section 6.1 |

Both downloads are cached so the analysis is reproducible offline. The FixMyStreet
download used about 16 small requests with pauses between them; anything larger should
go through mySociety's bulk data.

### 2.4 Sensor Logger validity and walking detection

Full methods and results: `SENSOR_VALIDITY.md` (code `scripts/sensor_validity.py`, outputs
`outputs/sensor_validity/report.html`). The method uses established features (projection
onto gravity, Mizell 2003; step-lag autocorrelation, Moe-Nilssen & Helbostad 2004;
walking step frequency, Pachi & Ji 2005); prior phone-based activity and transport-mode
detection: Kwapisz et al. 2011, Reddy et al. 2010 (references in `REFERENCES.md`). Summary:

- **Data quality** (all three recordings):
  - Motion sensors sampled at 99.72 Hz with 10.03 ms intervals; no gaps, timestamp
    faults or clock disagreement.
  - With the phone truly still (recording 2 only): noise about 0.001 g and static
    magnitude 0.994 g, both small against the 1 g impact threshold.
  - GPS reported accuracy about 11-14 m (median).
- **Walking vs scooting**:
  - Rules on 4 s windows combine step-band power share, step-period autocorrelation and
    GPS speed (thresholds are analyst choices).
  - Recording 2: sustained walking from **10:46:47** (first step), 275 s, 562 steps,
    2.04 steps/s. Short walking-like steps at ~10:45:58 after the ride ended, then about
    40 s standing.
  - Agrees with two references of one-minute precision: the rider's "after 10 minutes"
    (−19 s) and the Voi app's rental end at 10:46 (riding ends 10:45:54, walking starts
    after the rental-end minute opens). Minute-level agreement, not seconds.
  - In 1,126 windows where GPS alone showed riding (>= 12 km/h), none met the walking
    criteria.
  - Recordings 1 and 3 contain no walking (rider): no walking bout detected; isolated
    walking labels of 6 s and 8 s (0.7%, 1.2%), all after the ride ended.
- **GPS speed under-reads walking**: 3.0 km/h reported vs at least 4.6 km/h from
  positions. Reported speed is sometimes low while riding too (4 of 6 segments, by
  0.2-3.2 km/h). GPS took 12 s to register the start of walking. This may affect the
  7 km/h speed gate in impact detection (not yet quantified).

---

## 3. Part A: measured impacts

### 3.1 Method (`scripts/impact_map.py`)

1. **Vertical acceleration.** Each acceleration sample is projected onto the "up"
   direction given by the gravity vector. This removes the effect of how the phone is
   tilted on the handlebar.
2. **Impact detection.** Peaks in vertical acceleration of **1.0 g or more**, at least
   0.5 s apart, while moving at **7 km/h or more**. The speed rule excludes mounting,
   stopping and handling the phone. Two spikes above 3 g while stationary were
   correctly excluded.
3. **Post-impact wobble.** Handlebar rotation (gyroscope) in the 1.5 s after the
   impact, divided by the 2 s before it. A ratio of 1.5 or more counts as "marked
   wobble".
4. **Location.** GPS position interpolated to the impact time, discarding fixes with
   accuracy worse than 20 m.
5. **Route roughness.** Vertical acceleration averaged over each second, used to
   colour the route on the map.

The 1.0 g threshold, the severity bands and the 1.5× wobble ratio are analyst choices,
not established standards, and must be presented as such. A fixed threshold in g was
chosen over a per-ride statistical one so that rides and vehicles can be compared
directly.

### 3.2 Statistics (`scripts/impact_report.py`)

Adds rates, severity, a breakdown by road (a point counts as on a road within 20 m of
its centreline) and hotspots (impacts within 30 m of each other).

### 3.3 Results

| Measure | Value |
|---|---|
| Impacts | **40**, about 13.8 per km or 1 every 72 m |
| Median peak | 1.19 g (interquartile range 1.13–1.35 g) |
| Strongest | 2.80 g |
| Strong impacts (≥ 1.5 g) | 6, of which 4 were ≥ 2 g |
| Followed by marked wobble | 13 |
| Strong **and** followed by marked wobble | 3 |
| Speed vs severity | Spearman ρ = 0.03 (p = 0.88): no link in this ride |

| Road | km ridden | Impacts | Per km |
|---|---|---|---|
| Marston Road | 0.95 | 11 | 11.6 |
| Morrell Avenue | 0.98 | 12 | 12.2 |
| Old Road | 0.24 | 2 | 8.2 |
| Other roads | 0.72 | 15 | 21.0 |

- Almost every impact is a sudden downward jolt, consistent with a wheel dropping into
  a hole or off an edge.
- Eleven hotspots were found. **Hotspot 21** (near 51.7522, −1.2377) was hit on three
  separate passes at up to 2.68 g, which suggests a fixed hazard rather than noise.
- Morrell Avenue had many mild impacts (none ≥ 1.5 g); the strongest impacts were on
  roads outside the study list.
- Impacts #23 and #24 (2.80 g and 2.68 g) came at low speed just after a stop and
  should be checked on the ground.

---

## 4. Part A: comparison with FixMyStreet (`scripts/fms_compare.py`)

### 4.1 Method

- Downloaded the road-surface categories that can jolt a scooter: Pothole, Potholes
  and maintenance, Carriageway Defect, Roads and Carriageways, Manhole, and Damaged
  Gully or Catchpit Ironwork. Pavement categories were left out, because scooters
  aren't allowed on pavements.
- Two of those categories are catch-alls (they also hold road signs, leaves and
  walls). For those two only, a report is kept if its title describes the road
  surface. The word filter was spot-checked and tightened but will still make the odd
  mistake.
- An impact counts as **reported** if a road-surface report made in the **12 months
  before the ride** lies within **25 m**. Results are also given for 15 m and 50 m.
- Every match rate is shown next to a **baseline**: the same rate for all points along
  the ridden route, which is what chance alone would give.
- Report dates are submission dates (checked against a report's own page).

### 4.2 Why only recent reports

FixMyStreet holds reports back to 2009. With all of them, about 70–80% of random points
on the route lie within 25 m of some report, so any match is meaningless. An early
version of the analysis reported "33 of 40 impacts reported", which was a measure of
report density, not of reporting. The final analysis uses only reports from the year
before the ride and always shows the baseline.

### 4.3 Results

| Measure | Value |
|---|---|
| Impacts with a recent report within 25 m | **2 of 40** (5%) |
| Random route points with a recent report within 25 m (baseline) | 14% |
| Strong impacts (≥ 1.5 g) reported | **0 of 6** |
| Hotspots reported | **1 of 11** |
| Recent reports on the route where an impact was measured | 2 of 10 (all now closed or fixed) |

- **Main finding:** the hazards a scooter rider actually feels are largely missing from
  FixMyStreet. The difference between 5% and 14% shouldn't be read as meaningful with
  only 40 impacts.
- **Hotspot 21** is the only reported hotspot. It sits 6 m from a pothole reported in
  January 2026 and marked **"Fixed"**, yet it still produced impacts up to 2.68 g in
  October. Either the repair failed, the pothole re-formed, or a separate defect is
  there. This should be checked on Street View.

---

## 5. Literature and context

From web searches during the session (not a full literature review):

- **Imperial College e-scooter fall study** (Posirisuk, Baker and Ghajari, *Accident
  Analysis & Prevention* 167, 106567, 2022; doi:10.1016/j.aap.2022.106567): 180
  simulations, an e-scooter with 10-inch wheels, three rider sizes (5th percentile
  female, 50th and 95th percentile male), five speeds, 12 pothole sizes. 3 cm potholes
  caused no falls; 6 cm caused **41 falls out of 60 cases** (paper abstract). The
  Imperial news release gives "75 per cent" for 6 cm and 9 cm together; cite the paper
  for numbers. The scooter was modelled as two rigid bodies, the front wheel and the
  rest, joined at the axle.
- **E-scooter versus e-bike vibration** (Ventura et al., *Int. J. Transportation Science
  and Technology* 16, 2024, online 2023) and **e-scooter comfort vibration**
  (Cano-Moreno et al., *Machines* 10(8), 688, 2022) already exist. Comparing a scooter with a bicycle is
  therefore not new on its own.
- **What looks new here:** sudden impacts rather than comfort vibration; the
  front-wheel-only question; linking real-world data to the Imperial results; hazards
  missing from FixMyStreet; and, in future, measured versus felt risk.

`notes.md` holds the user's literature notes from another chat. Checked 2026-10-07: the
2026 *Machines* paper exists (Vaca Michilena and Cano-Moreno, *Machines* 14(1), 120;
front/rear tyre stiffness and **comfort**, not stability; best case slightly higher front
pressure). Its claim that larger wheels improve stability is not in the abstract and must
be checked in the full text. Swifty pothole tests and the patents were **not found** and
must be located before citing (see `REFERENCES.md`).
Mazdak Ghajari's current title should be checked on his Imperial profile (the 2022
news release says "Dr"). Swifty sells large-wheel scooters, so its tests are not
neutral evidence.

---

## 6. Part B: wheel-size models

Full methods for both models (equations, model construction, parameters, procedures,
development history, verification and how the animations were made) are in
**`SIMULATION_METHODS.md`**. This section summarises the results.

### 6.1 Voi wheel sizes

| Model | Front wheel | Rear wheel | Source |
|---|---|---|---|
| Voiager 5 | 10 in, pneumatic, front spring suspension | not stated | Levy fleet spec |
| Voiager 7 (2024) | **12 in**, "a size increase from its predecessors" | not stated | Startups Magazine |
| Voiager 9 (2026) | not stated | not stated | Voi press release |

- Voi has already enlarged the front wheel, specifically citing potholes: the Voiager 5
  launch describes "a larger front wheel with increased tyre tread depth" and a raised
  ride height "so that it can cope better over potholes" (Move Electric; Future Transport
  News), and the Voiager 7 went to 12 in. A strong industry precedent for the
  recommendation.
- Rear wheel: no source separates front and rear. Two secondary sources report the
  Voiager 5's wheels as 10 inches (Levy fleet spec; Alsalkini, Chalmers master's thesis,
  2023, Table 8, itself citing a 2020 Voi video about the Voiager 3X). Modelled as 10/10.
- **Tyre type is disputed:** the Levy spec says pneumatic; another (unverified) summary
  says solid honeycomb. Check a parked Voiager 5: honeycomb tyres show holes through the
  sidewall and have no valve; pneumatic tyres have a valve stem on the rim. With stiffer
  (solid-like) tyres the simulated jolts rise (300 mm potholes 2.6–4.5 g instead of
  1.9–2.4 g) but fall depths and the configuration ranking are unchanged.
- The ridden vehicle, SZ22, is a **Voiager 5** (confirmed by the rider). Its 10-inch
  front wheel and front spring match the modelling baseline. The rear wheel size is not
  published and is assumed to be 10 inches.
- Voi doesn't publish CAD models; fan-made models would be for illustration only.

### 6.2 Simulation tools considered

| Tool | Verdict |
|---|---|
| Python geometry (NumPy) | Stage 1, built |
| **MuJoCo** (free, installed, v3.14) | Stage 2, built |
| PyChrono (Project Chrono) | More detailed tyres and suspension, but hard to install on Windows; possible later |
| PyBullet | Similar to MuJoCo but less actively maintained |
| OpenSCAD / Blender | Shapes and rendering only; not evidence of stability; use for design figures |

### 6.3 Geometry model (`scripts/wheel_geometry.py`)

A rigid wheel rolls across a rectangular pothole with sharp edges.

- **Drop into the hole:** the smallest of the depth, the sag of a wheel resting on both
  edges, and how far it can fall in the time available, ½·g·(length/speed)². The last
  is an upper limit (free fall).
- **Hitting the far edge:** the edge meets the tyre at angle θ, where
  cos θ = (R − h)/R. Impact velocity is v·sin θ; the front wheel's speed loss is
  v·sin² θ.

Results at 20 km/h, 600 mm long pothole, compared with the 10-inch wheel:

| Front wheel | Edge impact velocity | Front-wheel speed loss |
|---|---|---|
| 12 in | 7–8% lower | 13–15% less |
| 14 in | 12–14% lower | 23–26% less |

- At speed, wheels barely drop into short potholes (about 3 mm for a 150 mm hole at
  20 km/h), so long potholes are the dangerous ones.
- Limitation: each wheel is treated alone, so this model can't separate "larger front
  only" from "larger both".

### 6.4 Dynamics simulation (`scripts/scooter_sim.py`)

A side-on (2D) MuJoCo model:

- **Scooter body** (deck, stem, handlebar) free to move forward, up/down and pitch.
- **Front and rear wheels** as rigid cylinders on axle joints.
- **Rider:** 76 kg, 1.7 m (the Imperial study's average rider), pinned to the deck at
  the feet with a spring-damper standing for bracing.
- **Road:** a rectangular pothole with sharp edges. The scooter coasts in with no motor,
  steering or suspension.
- **Fall** (analyst-defined, fixed before running): scooter pitch over 30° nose-down,
  rider lean over 30°, or forward speed below 0.5 m/s.

| Parameter | Value | Status |
|---|---|---|
| Scooter mass | 32 kg | Assumed (Voiager 7 reported at 36 kg) |
| Wheelbase | 0.95 m | Assumed |
| Tyre compliance | contact time constant 0.025 s (~80 kN/m, ~6 mm static deflection) | Assumed |
| Rider bracing | 1500 N·m/rad (~8° lean under 0.3 g braking) | Assumed |

The sweep covered 4 wheel setups (10/10, 12/10, 12/12, 14/10) × 9 depths (20–100 mm)
× 3 lengths (300, 600, 1000 mm) × 3 speeds (15, 20, 25 km/h): 324 runs.

**Shallowest pothole depth (mm) that caused a fall** (blank = no fall up to 100 mm):

| Length, speed | 10/10 | 12/10 | 12/12 | 14/10 |
|---|---|---|---|---|
| 600 mm, 15 km/h | 70 | 70 | 70 | 80 |
| 1000 mm, 15 km/h | 80 | 80 | 80 | 90 |
| 1000 mm, 20 km/h | 70 | 80 | 80 | 80 |
| 1000 mm, 25 km/h | 70 | 70 | 70 | 80 |

300 mm potholes caused no falls at any depth; 600 mm potholes only at 15 km/h.

**Findings:**

1. **A larger front wheel alone performs like larger wheels on both ends.** 12/10 and
   12/12 fell at the same depth in every case, with speed loss within about 2
   percentage points.
2. **A larger front wheel delays the fall** by about 10 mm of pothole depth in the
   cases where it differs; 14/10 helps most.
3. **Falls happen by the scooter and rider pitching forward over the front wheel**, the
   same mechanism as the Imperial study.
4. Slower speeds let the wheel drop deeper into medium-length potholes.

**Sensitivity analysis** (stiffer and softer tyres; weaker and stronger bracing): the
comparison between wheel setups held in every setting. The current scooter's absolute
fall depth moved between 60 and 70 mm with tyre stiffness, so the paper should report
the relative comparison, not absolute thresholds.

**Consistency check: failed.** Simulated handlebar jolts in no-fall runs are 3–19 g;
the measured impacts were 1–2.8 g. The model is about 3–5 times too harsh in absolute
terms (rigid frame, no front suspension, knife-sharp edges).

**Not modelled:** steering and handlebar twist, suspension, rider reactions,
three-dimensional effects.

### 6.5 Front/rear ratio study: what if the front wheel is much bigger?

`python scripts/scooter_sim.py --ratio` (567 runs; outputs in `outputs/scooter_sim/ratio/`).
Configurations from 10/10 (ratio 1.0) to 20/8 (ratio 2.5). The simulation now records
the front-wheel and rear-wheel crossings separately, which wheel's crossing triggered
a fall, how high the rear wheel was lifted, and how far it dipped into the pothole.

**Shallowest falling depth (mm), 1000 mm long pothole** (– = no fall up to 100 mm):

| Speed | 10/10 | 12/10 | 14/10 | 16/10 | 20/10 | 16/8 | 20/8 |
|---|---|---|---|---|---|---|---|
| 15 km/h | 80 | 80 | 90 | 100 | – | 100 | – |
| 20 km/h | 70 | 80 | 80 | 90 | 100 | 90 | 100 |
| 25 km/h | 70 | 70 | 80 | 80 | – | 80 | – |

| Configuration | 10/10 | 12/10 | 14/10 | 16/10 | 16/8 | 20/10 | 20/8 |
|---|---|---|---|---|---|---|---|
| Falls (of 81 runs each) | 15 | 14 | 11 | 9 | 9 | 1 | 1 |

**Findings:**

1. **No "too big" point appeared in this model.** Falls became rarer and needed
   deeper potholes as the front wheel grew, up to a ratio of 2.5.
2. **Every fall, in every configuration, was a forward pitch-over started by the
   front-wheel impact.** The rear wheel was lifted clear (it never dipped into the
   pothole before a fall). With bigger front wheels the pitch-over develops more
   slowly but has the same cause.
3. **Why rear size barely matters for falls:** with the current wheels, the
   front-edge impact bucks the scooter and lifts the rear wheel (up to ~140 mm without
   a fall), so the rear skips the pothole; this is why 12/10 and 12/12 behaved
   identically, and why 16/8 and 16/10 fell at the same depths.
4. **A second jolt appears with big front wheels.** The scooter isn't bucked, so the
   rear wheel drops into the pothole (up to ~45–57 mm) and loses speed at the far edge.
   Peak rear-crossing speed loss at 20 km/h in non-fall runs: 19% (10/10) rising to
   27% (20/10) and 33% (20/8). In this model it is a comfort and control issue, not a
   cause of falls.
5. **Robust to wheel weight:** scaling wheel mass with diameter (`SCALE_WHEEL_MASS`)
   gave identical fall depths.

*Correction:* an earlier version classified falls by the time they occurred and
reported most large-front-wheel falls as "rear-wheel" falls. Inspection showed the rear
wheel had never entered the pothole in any of them; falls are now attributed to the
rear wheel only if it dipped into the pothole beforehand (none did).

**What this model can't show** about oversized front wheels, all of which matter in
practice: steering (a heavier, larger front wheel has more steering inertia and
gyroscopic effect, and changes rake and trail), frame redesign (head-tube height and
keeping the deck level, which the model assumes), foot clearance, length, weight,
portability and cost. Very large ratios (≥ 2) are effectively a different vehicle,
closer to a kick-bike. The defensible recommendation from the simulation is a
**moderate** front increase (e.g. 12–14 in with a 10 in rear, in line with Voi's own
12 in front on the Voiager 7), not the largest possible wheel.

### 6.6 With the Voiager 5's front suspension

The ridden vehicle (SZ22) was confirmed as a **Voiager 5**, which has a front spring.
A sprung front fork (assumed 25 kN/m, damping ratio 0.3, 30 mm travel; details in
`SIMULATION_METHODS.md` section 3.12) was added as an option, and all experiments were
rerun with it (`outputs/scooter_sim/suspension/`). This is the more faithful model of
the ridden scooter.

**Consistency check** (current wheels, 20 km/h, 20–40 mm deep potholes):

| Model | 300 mm long | 600 mm long | Measured on the ride |
|---|---|---|---|
| No suspension | 4.9–6.5 g | 7.8–9.8 g | 1.0–2.8 g |
| With front suspension | **1.9–2.4 g** | 4.2–5.7 g | 1.0–2.8 g |

With suspension the model matches the measured range for short potholes and is about
twice too high for 600 mm ones: a **partial pass**, against a clear fail without it.

**Shallowest falling depth (mm) with suspension** (– = no fall up to 100 mm):

| Length, speed | 10/10 (Voiager 5) | 12/10 | 12/12 | 14/10 |
|---|---|---|---|---|
| 600 mm, 15 km/h | 80 | 90 | 90 | – |
| 1000 mm, 15 km/h | 90 | 100 | 100 | – |
| 1000 mm, 20 km/h | 90 | 90 | 90 | 100 |
| 1000 mm, 25 km/h | 90 | 100 | 100 | – |

| Falls in the main sweep (81 runs each) | 10/10 | 12/10 | 12/12 | 14/10 |
|---|---|---|---|---|
| No suspension | 15 | 14 | 14 | 11 |
| With suspension | 9 | 6 | 6 | 1 |

**Findings:**

1. **The suspension itself matters a lot:** falls for the Voiager 5 drop from 15 to 9,
   and every configuration needs deeper potholes to fall. Front suspension belongs in
   the recommendations alongside wheel size.
2. **Front only still equals front and back:** 12/10 and 12/12 fall at identical depths
   in every case of the main sweep, and in 8 of 9 sensitivity settings (with more fork
   damping 12/12 holds out 10 mm longer).
3. **A larger front wheel still helps, more modestly at 12 in:** 12/10 delays the fall by
   10 mm in 3 of 4 falling cases, but speed loss on a 60 × 600 mm pothole at 20 km/h
   barely changes (28% vs 26%). A 14 in front wheel nearly eliminates falls (1 of 81).
4. **Ratio study with suspension:** falls 9 (10/10), 6 (12/10), 1 (14/10, 16/10, 16/8),
   0 (20/10, 20/8). Every fall is still a front-impact pitch-over.
5. **Sensitivity:** fall depths for 10/10 range 80–90 mm across tyre, bracing and fork
   settings; the ranking of configurations holds.

### 6.7 Potholes without hard edges

Rounded edges could not be simulated with MuJoCo's built-in collision (numerical
artefacts; `SIMULATION_METHODS.md` section 3.13), so a custom tyre–road contact was
written that works against any road profile (section 3.14 there). It was validated
first: no false jolts on a flat road, correct tyre squash at rest, identical fall /
no-fall outcomes to MuJoCo's contact on all 30 sharp-edged test cases, and results that
converge as the road profile is made finer.

Potholes were then simulated with each edge sloping down over 0 (sharp), 25, 50 or
100 mm, with the Voiager 5's front suspension (1296 runs).

**Falls (of 81 runs per configuration):**

| Edge | 10/10 (Voiager 5) | 12/10 | 12/12 | 14/10 |
|---|---|---|---|---|
| Sharp | 8 | 6 | 6 | 4 |
| 25 mm sloped | 8 | 5 | 6 | 4 |
| 50 mm sloped | 7 | 5 | 5 | 4 |
| 100 mm sloped | 4 | 3 | 3 | 2 |

**Findings:**

1. **Softer edges are less dangerous:** with 100 mm sloped edges the Voiager 5 falls in
   half as many runs as with sharp edges, and falls need about 10 mm deeper potholes.
   Speed loss and jolts also fall (e.g. on a 600 mm pothole at 20 km/h, peak speed loss
   27% sharp vs 21% with 100 mm edges).
2. **The wheel-size conclusions hold for every edge shape:** a larger front wheel means
   fewer falls at every edge width (10/10 > 12/10 > 14/10), and the larger front wheel
   alone matches larger wheels front and back (12/10 vs 12/12: 6/6, 5/6, 5/5, 3/3).
3. **Policy angle:** how a pothole is cut and repaired matters, not only its depth.
   Sharp vertical edges (typical of fresh potholes and of square-cut repairs left
   unfilled) are the worst case for small-wheeled scooters.

The custom contact gives jolt sizes several times higher than measured (its single
contact point can't spread the load like a real tyre; more tyre damping made this
worse, not better), so it is used for falls and edge comparisons only; MuJoCo's contact
with suspension remains the model for jolt sizes (section 6.6).

---

### 6.8 Road bumps (exploratory)

**Status: exploratory model results, not findings about real scooters.** No bump was
measured or labelled on the ride, and no part of the bump model has been validated
against physical data. Everything below describes what this simulation produced under
its assumed parameters (`SIMULATION_METHODS.md` section 9) and the analyst-chosen fall
criteria (section 3.11 there).

**Why bumps.** Raised obstacles (for example a utility cover or patch standing proud of
the surface, a lifted slab, a tree-root ridge, or a traffic-calming hump) are a second
kind of road irregularity a rider may meet. Whether they matter for e-scooter riders in
practice is not tested here.

**What was simulated** (`SIMULATION_METHODS.md` sections 3.15 and 4.9; outputs in
`outputs/scooter_sim/[suspension/]bumps/`):

- **Sharp-edged rectangular bumps**, 20–100 mm high (10 mm steps), 300/600/1000 mm long
  (the pothole lengths). An idealised shape; real defects vary. Legal UK road humps may
  not have a vertical face above 6 mm (Highways (Road Humps) Regulations 1999, reg. 4), so
  this shape does not represent a hump built to the Regulations.
- **Round-top (circular-arc) humps**, 20–100 mm high: 3.7 m long, the round-top length
  reported as standard in DfT Traffic Advisory Leaflet 2/96, and 600 mm long (a short
  bump below the 900 mm legal minimum, as might be found off the highway). Real hump
  profiles were not surveyed.
- Speeds 15/20/25 km/h, coasting, wheel configurations 10/10, 12/10, 12/12, 14/10 (front/
  rear, in), each without and with the modelled front spring (2 × 1095 runs, including the
  rear-size check below).

**Falls in the model per configuration** (sharp bumps and potholes: of 81 runs; round-top
humps: of 54). "Fall" = the analyst-set lean/pitch/stall criteria:

| Obstacle | Fork | 10/10 | 12/10 | 12/12 | 14/10 |
|---|---|---|---|---|---|
| Pothole (sharp) | none | 15 | 14 | 14 | 11 |
| Sharp bump | none | 22 | 13 | 14 | 4 |
| Round-top hump | none | 0 | 0 | 0 | 0 |
| Pothole (sharp) | front spring | 9 | 6 | 6 | 1 |
| Sharp bump | front spring | 1 | 2 | 1 | 2 |
| Round-top hump | front spring | 0 | 0 | 0 | 0 |

**Rear-size check** (300 mm sharp bump, MuJoCo contact): lowest height (mm, 5 mm steps)
at which the model met the fall criteria; "none" = not met up to 100 mm:

| Fork | Speed | 10/10 | 12/10 | 14/10 | 10/12 | 12/12 | 10/14 | 14/14 |
|---|---|---|---|---|---|---|---|---|
| none | 15 km/h | 85 | 95 | none | 85 | 95 | 85 | none |
| none | 20 km/h | 80 | 90 | 100 | 80 | 90 | 80 | 100 |
| none | 25 km/h | 80 | 85 | 100 | 80 | 85 | 80 | 95 |
| front spring | 15 km/h | 85 | 85 | 85 | 90 | 95 | none | 100 |
| front spring | 20, 25 km/h | none | none | none | none | none | none | none |

**Observations (model only):**

1. *Without the front spring*, the model met the fall criteria in more sharp-bump runs
   than pothole runs of the same dimensions for the 10/10 configuration (22 vs 15 of 81).
   A plausible geometric explanation, not tested separately, is that a wheel meets the
   full height of a step but drops only part way into a short pothole. Fewer falls were
   recorded with larger front wheels (22, 13, 4 for 10, 12, 14 in); changing the rear
   size alone did not change the falling heights in the rear-size check.
2. *With the front spring*, bump falls were rare: 1–2 runs per configuration, all on the
   300 mm bump at 15 km/h. In each of these runs the fall criteria were met after the
   rear wheel struck the bump's leading edge (rear-strike speed loss 75–89%). In the
   rear-size check, configurations with a larger rear wheel reached the criteria at
   greater heights or not at all (10/12: 90 mm, 12/12: 95 mm, 14/14: 100 mm, 10/14: not
   up to 100 mm), while front size alone did not change the height (85 mm for 10/10,
   12/10 and 14/10). This pattern rests on very few runs (one bump length, one speed,
   differences of 5–15 mm, close to the 5 mm grid resolution) and on a model whose bump
   behaviour is not validated. **It should be read as a question for further work
   (does rear-wheel size or rear suspension matter on sprung scooters?), not as evidence
   that larger rear wheels are more stable.** It does indicate that the working
   hypothesis (front wheel alone) may not hold for every obstacle type, and the paper
   should say so.
3. No round-top hump run met the fall criteria in any configuration. This is consistent
   with, but not evidence for, DfT guidance that round-top and flat-top humps "should be
   able to be negotiated by both cyclist and motorcyclists quite safely" (TAL 7/96); that
   guidance was not written for e-scooters. The short 600 mm bump gave large modelled
   speed losses at 15 km/h (up to 47% with the fork) and rider lean up to 17°.
4. The front spring changed the bump results much more than the pothole results (10/10:
   22 -> 1 falls on bumps, 15 -> 9 on potholes), so the bump results depend strongly on
   the assumed fork stiffness, damping and travel, which were not varied for bumps.

**Uncertainties and what these results cannot show:**

- **Contact model.** On sharp bumps the two contact models agreed on fall outcomes in
  295/324 runs without the fork and 307/324 with it (potholes: 30/30), with disagreements
  in both directions. The cause is not established (the custom contact's lack of a
  tangential friction force is one candidate).
- **No validation.** Modelled bump jolts (e.g. 3.6–8.4 g at 20–40 mm, 600 mm, 20 km/h,
  with the fork) exceed the 1–2.8 g measured on the ride, and no bumps were identified on
  the ride to compare with.
- **No sensitivity analysis for bumps** (tyre, rider bracing, fork parameters) and no
  bump-specific runs at other rear sizes beyond the 300 mm check.
- **Simplifications** as for potholes: planar model, no steering, coasting, rigid rider
  pinned at the feet, idealised obstacle shapes, rear wheel size of the Voiager 5 assumed.
- **Not shown:** that real bumps cause falls, that bumps are more or less dangerous than
  potholes on the road, any injury risk, or that any wheel size is safe.

Roadblocks met while building this are listed in `SIMULATION_METHODS.md` section 5.1.
Animations: bump clips at the bottom of `outputs/scooter_sim/animations.html` (model
illustrations, not evidence).

## 7. Outputs

| File | Contents |
|---|---|
| `outputs/impact_map.html` | Map of the route (coloured by roughness) and impacts |
| `outputs/impact_report.html` | Statistics report |
| `outputs/impact_trace.png` | Vertical acceleration and speed over the ride, with detections |
| `outputs/fig_severity_hist.png`, `fig_impacts_per_km_by_road.png`, `fig_speed_vs_severity.png` | Paper figures for Part A |
| `outputs/impacts.csv`, `impacts_with_roads.csv`, `impacts_by_road.csv`, `impact_stats.json`, `impacts_params.json` | Data behind Part A |
| `outputs/fms_comparison.html`, `outputs/fms_map.html` | FixMyStreet comparison page and map |
| `outputs/streetview_check.html` (+ `.csv`) | 25 spots with 360° Street View links facing the direction of travel, FixMyStreet status and a record form (Export CSV) |
| `outputs/impacts_vs_fms.csv`, `fms_reports_on_route.csv` | Data behind the comparison |
| `outputs/wheel_model/` | Geometry model figures and tables |
| `outputs/scooter_sim/` | Simulation results, sensitivity, figures and animations |
| `outputs/scooter_sim/animations.html` | All animations in six sections (Voiager 5 with suspension; current vs larger front wheel on 50 mm and on 100 mm soft-edged potholes; larger front wheel; much larger front than rear; the rear wheel's second jolt); opens in any browser |
| `outputs/scooter_sim/consistency.csv`, `fig_consistency.png` | Simulated vs measured handlebar jolts |
| `outputs/scooter_sim/suspension/` | All simulation results with the front suspension |
| `outputs/scooter_sim/suspension/soft_edges/` | Soft-edged pothole study (`fig_edges.png`, fall counts and depths) |
| `outputs/sensor_validity/` | Sensor Logger data quality and walking detection (`report.html`; see `SENSOR_VALIDITY.md`) |
| `outputs/recordings/<recording>/` | Impact map, report, trace and tables for recordings 2 and 3 (recording 1's are in `outputs/`) |
| `outputs/index.html` | Overview of all recordings with links to every map, report and timeline |

The maps and reports contain exact ride coordinates, including where the ride started
and ended. Keep them local unless sharing is intended, and trim the start and end of
the route first.

---

## 8. Reproducing the analysis

Python 3.11 with pandas, numpy, scipy, matplotlib, folium and mujoco.

```
python scripts/impact_map.py          # impacts + map
python scripts/impact_report.py       # statistics report
python scripts/fms_compare.py         # FixMyStreet comparison (--refresh to re-download)
python scripts/streetview_page.py     # Street View checklist page
python scripts/wheel_geometry.py      # geometry model
python scripts/scooter_sim.py --animate       # dynamics sweep + animations
python scripts/scooter_sim.py --sensitivity   # sensitivity analysis
python scripts/scooter_sim.py --ratio         # front/rear wheel-ratio study
python scripts/sensor_validity.py            # data quality + walking detection, all recordings
python scripts/impact_map.py --data-dir data/raw/<recording> --out-dir outputs/recordings/<recording>
python scripts/impact_report.py --data-dir data/raw/<recording> --out-dir outputs/recordings/<recording>
python scripts/outputs_index.py               # outputs/index.html
```

Run `sensor_validity.py` before `impact_map.py`: the map then draws detected walking
bouts (`outputs/sensor_validity/walking_onsets.csv`) as a dashed orange line.

Defaults are `--data-dir data/raw/2026-10-03_1830_rec01` (recording 1) and `--out-dir outputs`. Parameters are constants at the
top of each script and are documented in its header.

Practical notes:

- Maps use Esri grey basemap tiles. OpenStreetMap tiles return 403 and CARTO tiles
  show "API KEY REQUIRED" when the HTML is opened from disk.
- On Windows a figure open in an image viewer can't be overwritten; close it before
  rerunning.

---

## 9. Corrections made during the work

| Issue | Fix |
|---|---|
| Basemap tiles blocked when opening the map from disk | Switched to Esri tiles, verified by viewing a downloaded tile |
| Cheney Lane listed as a study road but not ridden | Replaced by Morrell Avenue |
| FixMyStreet match of "33 of 40" reflected report density | Recent reports only, with a route baseline |
| Catch-all categories included signs, walls and leaves | Title filter for those two categories |
| Geometry diagram showed "sinks 0 mm" | Added a proper at-rest case |
| Simulation jolts far too high with near-rigid contact | Contact softness set to match a pneumatic tyre |
| Launch transient appeared as a jolt | Longer run-up; measurement only near the pothole |
| Bump study: pothole rules for phases and fall attribution mislabelled the rear-wheel strike | Position-based rules for bumps; studies rerun (full list of bump roadblocks: `SIMULATION_METHODS.md` 5.1) |
| Bump study: "stall" fall type never fired (every stall ended in a pitch-over) | Counts use the `stalled` flag |
| Recording 1's start was documented as 17:30 local; Sensor Logger's metadata time is UTC (local 18:30:29) | Corrected in 2.1; map caption labels it UTC |
| Raw CSVs lay in the project root | Moved to `data/raw/<date>_<time>_recNN/` (checksums identical, Part A results unchanged) |

---

## 10. Open tasks

- [x] Confirm the Voi model: SZ22 is a Voiager 5.
- [x] Voiager 5 wheels reported as 10 in (Levy; Alsalkini 2023); front/rear not separated.
- [ ] Check whether Voiager 5 tyres are pneumatic or solid honeycomb (look for a valve).
- [ ] **Which Voi model runs in London?** Decides the Part C argument (section 12.4).
      Desk options: news photos of Voi in London since Sept 2023; or ask Voi.
- [ ] Street View check with `outputs/streetview_check.html` (S1 = hotspot 21); export
      the CSV to `data/streetview_observations.csv`.
- [x] Add front suspension to the simulation (partial pass of the consistency check).
- [x] Potholes without hard edges (custom profile contact, section 6.7).
- [x] Road bumps: sharp-edged and round-top (section 6.8).
- [x] Organise recordings 2 and 3; data quality and walking detection (section 2.4).
- [x] Rider confirmed: only recording 2 has walking; Voi rental ended 10:46.
- [ ] References to the second (Sensor Logger annotation while stopped) and more walking
      episodes before stating detection rates (`SENSOR_VALIDITY.md` 8).
- [ ] Quantify whether GPS speed under-reading affects the 7 km/h gate in impact detection.
- [ ] Analyse recordings 2 and 3 for impacts (riding parts only); record vehicle IDs.
- [ ] Decide whether bumps go in the paper at all; if so, as exploratory model results with
      the 6.8 uncertainties, and the rear-wheel pattern (6.8 item 2) only as an open
      question / limitation of the front-wheel hypothesis.
- [ ] Optional, if bumps stay in: bump sensitivity runs (fork, tyre, bracing) and a wider
      rear-size sweep (more bump lengths and speeds) before saying anything about rear size.
- [ ] Optional: label bumps on a future ride (voice note or Street View check) so bump
      jolt sizes can be compared with measurements.
- [ ] Optional: a tyre model with enveloping (contact patch) so the soft-edge model's
      jolt sizes also match the measurements.
- [ ] More rides on all four study roads, including Headington Road; record the vehicle
      ID for each.
- [ ] Optional: a voice recording during rides to compare measured jolts with felt risk.
- [ ] A proper literature search, including papers citing the Imperial 2022 study, and
      verification of the claims in `notes.md`.
- [ ] Update the original project brief (iPhone, research question, study roads).
- [ ] Write the paper; seek feedback from an Oxford supervisor and, later, the Imperial
      group; publish as a preprint (engrXiv or OSF) with code and data on Zenodo.

---

## 11. Ethics

Only the author's own rides are used. Data from other riders would need university
ethics approval and GDPR-compliant handling of location data. The phone is never
touched while riding.

---

## 12. Part C: argument and conclusion (decided 2026-10-07)

This is the agreed framing for the paper's Part C, introduction and conclusion. Full
evidence and references: `literature/uk_fleet_wheel_sizes.md`, `REFERENCES.md`.

### 12.1 Thesis
> London's e-scooter trial requires a front wheel of at least 11 in, but national trial
> rules set no minimum, so older models with smaller front wheels can remain in service
> elsewhere, as in Oxford. Our model suggests a larger front wheel delays pothole falls,
> which supports extending a front-wheel minimum to all UK trials.

The wheel-size assumption stays as reported (Voiager 5 = 10 in, modelled 10/10; Levy n.d.;
Alsalkini 2023). The paper states it as an assumption and a limitation. The author decided
not to request a company measurement for now.

### 12.2 Evidence chain
| Step | Claim | Source |
|---|---|---|
| 1 | No national wheel-size requirement; DfT stability tests include a 5 cm deep, 1 m long depression | DfT 2024 |
| 2 | London requires front >= 11 in and rear >= 9 in (outer diameter incl. tread), relaxed in Nov 2022 from 12/10 | TfL 2022 |
| 3 | TfL says London rental vehicles have "high safety standards which go beyond the national standards ... larger wheels" | TfL 2023 |
| 4 | Voi has operated in London since late Sept 2023 (fleet cap 6,600 per operator) | TfL 2023; VNV Global 2023 |
| 5 | The Voiager 5's front wheel is reported as 10 in, i.e. below London's 11 in minimum | Levy n.d.; Alsalkini 2023 |
| 6 | The Voiager 5 is still in service outside London: Oxford (ridden 2026-10-03) and new deployment in Essex, Aug 2025 | Essex Highways 2025 |
| 7 | Voi's larger-front models did not come to the UK: Voiager 7 (12 in front) went to Germany, Italy and Norway; Voiager 8 to Finland, France, Germany, Norway, Spain and Sweden | Morley 2024; electrive 2025 |
| 8 | Model result: a larger front wheel delays falls by about 10 mm of pothole depth and 12/10 performs like 12/12; in the model without suspension, 10/10 falls start at 60-70 mm (1000 mm long potholes), just above the DfT test depth. With suspension, falls drop (10/10: 9 of 81 runs) and the larger front still helps | Sections 6.4-6.7 |
| 9 | Not all fleets outside London are small-fronted (Beryl: 12 in front in six areas); the point is that nothing requires it | Beryl 2020; ScootAPI 2022 |

### 12.3 Wording rules
- Say **"outside London"** or **"regional trial areas"**, never "rural": Oxford is a city.
- Give named examples (Oxford, Essex); do **not** claim how many older scooters remain.
  Operators do not publish fleet counts per model.
- Say the model "suggests"; the risk is not measured and the model is not validated.
- Say "reported 10 in", and give the sources; the front/rear split is not published.
- Do not say Voi breaks any rule: outside London no wheel rule applies.

### 12.4 Open check that can change this section
Which model Voi runs in London is not known.
- If it is a newer model with a front of 11 in or more: strongest version of the argument
  (same operator, London-compliant scooter in London, older one in Oxford).
- If it is the Voiager 5: the Voiager 5's front must measure >= 11 in, so the 10 in
  reports are wrong. Then revise step 5, the thesis, and the simulation baseline (10/10).

### 12.5 Recommendations to write up
1. DfT: add a front-wheel minimum (as London does) to national trial vehicle rules, and
   consider a stability test deeper than 5 cm.
2. Operators: when renewing fleets outside London, prioritise models with a larger front
   wheel; a larger front alone gives most of the benefit (Part B).
3. Councils (e.g. Oxfordshire): ask for London-equivalent vehicle standards when
   awarding or extending trial contracts.
4. Research groups with test facilities: physical tests of front-wheel size on potholes.

---

## Sources

The full bibliography (papers, software with versions, data and map services, vehicle and
policy sources) is in **`REFERENCES.md`** (Harvard) and **`references.bib`** (BibTeX).
Part C sources are in `literature/wheel_size_industry_cases.md` and
`literature/uk_fleet_wheel_sizes.md`. Entries marked [to verify] there still need checking.
