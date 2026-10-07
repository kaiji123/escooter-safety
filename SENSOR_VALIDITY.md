# Sensor Logger validity: data quality and walking-vs-scooting differentiation

Methods and results for the paper's check of the recording method (Sensor Logger on an
iPhone 11 Pro Max). Code: `scripts/sensor_validity.py`. Outputs:
`outputs/sensor_validity/` (open `report.html`). Every number below is taken from those
outputs; rerun the script and re-check them if any recording or setting changes.
Citations use Pandoc keys from `references.bib`, e.g. [@moenilssen2004]; what each source
was checked for is listed in `REFERENCES.md` (section "Sensor validity and walking
detection").

Status (2026-10-07): exploratory, one rider, one phone, three recordings. Checked against
four reference statements from the rider (section 5):
- the walking onset agrees with the rider's account and with the Voi app's rental end
  time, to within the one-minute precision of those references;
- in the two recordings the rider confirmed contain no walking, no walking bout was
  detected (6 s and 8 s of isolated walking labels).
This is agreement at minute level on one walking episode, not a timing accuracy in
seconds or a detection rate.

---

## 1. Purpose

Part A of the paper measures impacts with a phone app. Two questions follow:

1. **Are the raw data internally sound?** Regular sampling, no gaps or timestamp faults,
   sensor streams consistent with each other, plausible noise and GPS accuracy.
2. **Do the data contain enough information to tell riding from walking?** If the
   accelerometer and GPS can separate a rider's walking from scooting, that supports
   using the same signals to characterise riding. It also gives a way to remove
   non-riding parts of a recording automatically.

Telling activities apart with phone sensors is established: phone accelerometers have
been used to recognise walking among other activities [@kwapisz2011], and phone GPS
combined with the accelerometer to separate walking, cycling and motorised transport
[@reddy2010]. This check does not propose a new classifier. It uses simple, transparent
rules built from established signal features (section 3.2) to test whether *this*
app and phone, mounted on a rental e-scooter, give data in which riding and walking are
distinguishable.

Neither question needs an external reference instrument, but neither proves
**absolute accuracy**. That needs a reference (a calibrated accelerometer, survey-grade
GNSS, or exactly timed events), which this study does not have.

## 2. Data

| Recording | Folder (`data/raw/`) | Start (Europe/London) | Length | Content (rider's account) |
|---|---|---|---|---|
| 1 | `2026-10-03_1830_rec01` | 2026-10-03 18:30:29 | 13.7 min | Voi ride (the Part A pilot ride); **no walking** |
| 2 | `2026-10-07_1037_rec02` | 2026-10-07 10:37:06 | 35.3 min | Ride; Voi rental ended at 10:46 (app); walking "after 10 minutes"; then the phone was mostly still |
| 3 | `2026-10-07_1338_rec03` | 2026-10-07 13:38:34 | 11.4 min | Ride; **no walking** |

All three were recorded with Sensor Logger 1.67.1 [@sensorlogger] on the same iPhone 11 Pro Max (iOS
26.6.2), sample interval 10 ms for the motion sensors and about 1 Hz GPS. The
recordings were not modified (section 7). The rider confirmed that only recording 2
contains walking.

Units, as checked: `Accelerometer.csv` (user acceleration, gravity removed) and
`Gravity.csv` are in m/s² in the device frame; they are the iOS Core Motion `userAcceleration`
and `gravity` outputs [@apple_cmdevicemotion], which Sensor Logger records in m/s².
`AccelerometerUncalibrated.csv` is the raw accelerometer in **g**, iOS's unit for raw
acceleration [@apple_cmacceleration]. The data confirm this: raw ÷ (user acceleration +
gravity) = 1/9.80665 on every axis. `Gyroscope*.csv` is in rad/s. `Location.csv` speed is in m/s,
with −1 = invalid. **Metadata `recording time` is UTC**; local times here are computed
from the nanosecond `time` column and converted to Europe/London.

## 3. Methods

### 3.1 Data quality (all recordings)

| Check | How | What it can show |
|---|---|---|
| Sampling | Intervals between consecutive timestamps: median, 1st/99th percentile, gaps (> 1.5× nominal), non-monotonic and duplicate timestamps | Dropped samples, irregular sampling |
| Clock | Absolute `time` (ns) vs `seconds_elapsed` | Two time bases disagreeing |
| Raw vs fused acceleration | Fused user acceleration + gravity, converted to g and **interpolated** to the raw sample times, compared with the raw accelerometer; magnitude of the difference | Internal consistency of the iOS fusion output with the raw sensor (not accuracy) |
| Noise floor and bias | Non-overlapping 4 s windows ranked by user-acceleration SD (largest axis); the quietest 5% are used. User-acceleration SD, gyroscope SD, raw acceleration magnitude (should be 1 g at rest), calibrated minus uncalibrated gyroscope mean | Sensor noise and static error, **if** the phone was truly still in those windows; otherwise upper bounds |
| Gravity magnitude | Mean and SD of the gravity vector's length | Reported only. It is fixed at 9.80665 m/s² by the fusion, so it is **not** an accuracy test |
| GPS | Fix interval and gaps; reported horizontal accuracy; reported speed vs position-derived speed; position scatter while standing | GPS availability, stated precision, internal consistency of speed |

### 3.2 Walking vs scooting

**Signal.** Vertical user acceleration: the user acceleration projected onto the gravity
direction, sign set so that up is positive. Projecting onto gravity to get a vertical
component that does not depend on how the phone is held follows Mizell [@mizell2003],
who estimated gravity as the mean acceleration over a window. Here the gravity vector
comes directly from the iOS sensor fusion [@apple_cmdevicemotion].

**Windows.** 4 s long, starting every 1 s. A 4 s window holds about 8 steps at a normal
cadence.

**Features** (per window):

| Feature | Definition | Rationale |
|---|---|---|
| `sd_v` | SD of vertical acceleration (m/s²) | Overall motion; near 0 when the phone is still |
| `step_frac` | Share of vertical-acceleration power (Welch spectrum [@welch1967], 256-sample segments) in **1.2–2.8 Hz**, out of 0.5–20 Hz | Walking concentrates power at the step frequency: mean step frequencies of 1.8 Hz (footbridges) and 2.0 Hz (shopping floors) were measured for 800 pedestrians [@pachi2005]. The band is set wider than these means (an analyst choice) to include slow and brisk walking. Road vibration on a scooter is broadband |
| `step_ac` | Highest normalised autocorrelation at lags of one step period, **0.36–0.83 s** | Autocorrelation of trunk acceleration at the step lag measures step regularity and gives cadence [@moenilssen2004]. Steps repeat regularly; vibration does not |
| `cadence` | 1 / that lag (steps/s) | Plausibility check on walking |
| `speed_kmh` | Median GPS-reported speed of the fixes in the window (no value if none valid) | Separates riding speed from walking speed |

**Rules**, applied in this order (thresholds are **analyst choices**, set from physical
reasoning and from inspecting recording 2 before the rider's account was known, not
fitted to labels):

1. **stationary**: `sd_v` < 0.5 m/s² and (speed < 2 km/h or no speed)
2. **walking**: `step_ac` ≥ 0.5 and `step_frac` ≥ 0.5 and (speed < 8 km/h or no speed)
3. **scooting**: speed ≥ 8 km/h and `step_frac` < 0.3
4. **unclear**: everything else (e.g. slow riding at junctions, handling the phone, getting on or off)

Labels are then smoothed with a centred 5-window majority filter. A **walking bout** is
at least 10 s of consecutive walking windows.

**Onset of a walking bout (first step).** The window rule only places a bout start to
within a few seconds, so it is refined using individual steps:

- Vertical acceleration is band-pass filtered (0.8–4 Hz, 2nd-order Butterworth
  [@butterworth1930], applied forwards and backwards for zero phase shift).
- Implementation: SciPy [@virtanen2020scipy] (`welch`, `butter`/`sosfiltfilt`,
  `find_peaks`).
- Steps are peaks with prominence ≥ 1 m/s² at least 0.35 s apart.
- Starting from the first step inside the bout, the method moves back over earlier peaks
  as long as successive intervals stay within one step period (0.35–0.85 s).
- The earliest peak reached is reported as the **first step**.

**GPS lag at onset.** The time from the first step until GPS speed exceeds 1.5 km/h on 3
consecutive fixes.

**Speed comparison by activity.** Every walking or scooting segment of at least 30 s is
trimmed by 15 s at each end. Its median reported GPS speed is compared with speed from
positions:

- **summed fix-to-fix distance**, which GPS jitter inflates;
- **straight-line distance** between the first and last fix, a **lower bound** on the
  distance travelled.

A reported speed below the straight-line speed therefore under-reads the true speed.

**Why two acceleration features.** In recording 2, after the walk, there are repeated
periods with high step-lag autocorrelation (~0.85) while the phone is almost still.
These periods have essentially **no** power in the step band (`step_frac` ≈ 0) and tiny
amplitude (`sd_v` ≈ 0.1 m/s²): a periodic vibration, not steps. Autocorrelation alone
would have labelled them walking.

## 4. Results

### 4.1 Data quality

| Measure | Rec. 1 | Rec. 2 | Rec. 3 |
|---|---|---|---|
| Motion sensors: rate | 99.72 Hz | 99.72 Hz | 99.72 Hz |
| Motion sensors: interval median (99th pct.) | 10.03 (10.03) ms | 10.03 (10.03) ms | 10.03 (10.03) ms |
| Motion sensors: gaps, non-monotonic, duplicates | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| Clock: `time` vs `seconds_elapsed`, max difference | 0.0 ms | 0.0 ms | 0.0 ms |
| Raw vs fused acceleration, median (95th pct.) | 0.049 (0.160) g | 0.007 (0.092) g | 0.013 (0.053) g |
| Quietest windows: user-accel. SD | 0.31 m/s² | **0.012 m/s²** | 0.19 m/s² |
| Quietest windows: gyro SD | 0.16 rad/s | **0.0035 rad/s** | 0.095 rad/s |
| Quietest windows: raw accel. magnitude | 1.002 g | **0.994 g** (SD 0.0009) | 1.003 g |
| Gyro calibrated − uncalibrated (x, y, z) | 0.002, 0.005, −0.002 rad/s | 0.002, 0.005, −0.002 rad/s | 0.002, 0.005, −0.002 rad/s |
| GPS fixes; gaps > 1.5 s; longest gap | 828; 2; 17.1 s | 1160; 144; 15.0 s | 686; 0; 1.0 s |
| GPS reported horizontal accuracy, median (90th pct.) | 11.5 (15.1) m | 11.3 (15.5) m | 13.9 (17.6) m |
| GPS position scatter while standing, median (90th pct.) | 0.7 (2.1) m | 0.1 (1.7) m | 0.5 (1.6) m |
| GPS speed: \|reported − position-derived\|, median | 0.38 m/s | 0.64 m/s | 0.52 m/s |

Interpretation:

- **Sampling and timing are clean**: no dropped samples, gaps or timestamp faults in any
  motion stream of any recording.
- **The phone was truly still only in recording 2** (lying still after the walk). There,
  noise is about 0.001 g and the static acceleration magnitude is 0.6% below 1 g.
  Both are small against the 1.0 g impact threshold used in Part A. In recordings 1
  and 3 the phone was on the handlebar throughout, so the "quietest window" values
  include vibration and are only upper bounds on noise.
- **Raw and fused acceleration agree most closely in recording 2** (mostly still: median
  0.007 g) and least closely in recording 1 (riding throughout: median 0.049 g, 95th
  percentile 0.16 g). The likely reasons are fast
  vibration (interpolation between samples taken at different instants) and filtering
  in the iOS fusion; this has not been tested further.
- **The gyroscope bias correction** applied by iOS is small and identical across
  recordings (same phone).
- **GPS horizontal accuracy** (median 11–14 m) is the phone's *own estimate*, not a
  measured error. For comparison only: the measured horizontal error of an iPhone 6 in
  an urban area averaged 7–13 m [@merry2019]. A different phone was tested there, and
  measured error is a different quantity, so this is context, not a check.
- **GPS gaps in recording 2** start at 1004.7 s (10:53:51), after the walk (phone
  indoors or covered). Both "gaps" in recording 1 are at its very start: the first fix
  is a cached position from 17 s before recording began.

### 4.2 Walking vs scooting

Time per label (smoothed):

| Recording | Scooting | Walking | Stationary | Unclear |
|---|---|---|---|---|
| 1 (ride) | 564 s | 6 s | 64 s | 187 s |
| 2 (ride + walk) | 321 s | **330 s** | 1103 s | 361 s |
| 3 (ride) | 347 s | 8 s | 100 s | 226 s |

**Walking detected in recording 2.**

| Bout | First step (local time) | Length | Steps | Median cadence | GPS lag at onset |
|---|---|---|---|---|---|
| 1 | **10:46:47.04** (580.6 s after recording start) | 275 s | 562 | 2.04 steps/s | 12.0 s |
| 2 | 10:51:25.21 | 37 s | 69 | 1.89 steps/s | 3.8 s |

The two bouts are probably one walk with a pause of a few seconds around 10:51:21–25.
This is not confirmed.

**The transition from riding to walking** (`fig_walk_onset_1.png`) is not a single switch:

| Time (approx.) | What the data show |
|---|---|
| ~10:45:52–10:45:57 | GPS speed falls from riding speed, ending in a sharp acceleration spike |
| 10:45:58–10:46:06 | A short, walking-like burst (8 s, decaying amplitude) |
| ~10:46:06–10:46:46 | About 40 s of standing or handling the phone (from ~10:46:16 the gravity vector shows the phone lying or held flat) |
| from 10:46:47 | Steady walking |

The Voi rental ended at 10:46 (app ride history: 10:46:00–10:46:59). The phone-handling
period overlaps that minute, which is consistent with the rental being ended on the
phone then, but the data cannot show this. The 8 s burst at 10:45:58 resembles the
confirmed false positives in recordings 1 and 3 (short, after riding, step regularity
below that of the real walk), so it is **not** treated as the start of walking. The
detected walking start is **10:46:47**, the first step of sustained walking.

**Feature separation** (independent check): in the 1,126 windows across all three
recordings where GPS speed alone was ≥ 12 km/h (riding, defined without the
acceleration features), none met the walking criteria. `step_ac` median was 0.18 (max
0.45) and `step_frac` median 0.010 (max 0.44). In the main walking bout, `step_ac` median
was 0.78 (IQR 0.76–0.80) and `step_frac` 0.83. These walking values come from the
detected bout itself, so they are not independent of the method.

**False positives in the two recordings without walking** (confirmed by the rider):

| Recording | Walking labels (smoothed) | Before smoothing | Walking bouts ≥ 10 s | While GPS ≥ 8 km/h |
|---|---|---|---|---|
| 1 | 6 s (0.7% of 821 windows): 18:43:53–55 and 18:44:06–10 | 9 windows | 0 | 0 |
| 3 | 8 s (1.2% of 681 windows): 13:49:08–16 | 9 windows | 0 | 0 |

All of these came after the ride had ended, with GPS speed below 1 km/h, and with step
regularity (`step_ac` 0.51–0.71) below the real walk's (median 0.78). In recording 1 they
fall in the last 20 s before the recording stopped, with the phone held flat (probably
handled). In recording 3 the phone was roughly in its mounted orientation, about 1.5 min
after riding ended. Their cause (e.g. handling the phone, moving or parking the scooter)
is not known. The 10 s minimum bout length was set before the script was first run on
recordings 1 and 3, and it excludes all of them. **No thresholds were changed after
seeing these results.**

### 4.3 GPS speed vs position-derived speed

| Recording | Activity | Segment (local) | Reported median | Straight-line (lower bound) | Summed path |
|---|---|---|---|---|---|
| 1 | scooting | 18:32:05–18:36:38 | 20.1 km/h | 19.0 | 20.8 |
| 1 | scooting | 18:39:59–18:43:00 | 19.1 | 19.3 | 19.7 |
| 2 | scooting | 10:37:43–10:40:31 | 17.9 | 19.2 | 19.5 |
| 2 | scooting | 10:44:57–10:45:54 | 12.1 | 15.3 | 15.4 |
| 2 | **walking** | 10:46:46–10:51:21 | **3.0** | **4.6** | 5.5 |
| 3 | scooting | 13:39:47–13:41:08 | 19.5 | 19.5 | 19.6 |
| 3 | scooting | 13:44:18–13:47:22 | 17.5 | 19.1 | 19.5 |

(The second recording-2 scooting segment is 26 s after trimming; the others are 50–244 s.)

- **While walking, the reported GPS speed is at least ~1.5 km/h (≥ 34%) below the speed
  implied by the positions.** With the straight-line speed (a lower bound), the
  implied step length is at least 4.6 km/h ÷ 2.04 steps/s ≈ 0.62 m. That is close to
  the mean step lengths of 0.67 m (women) and 0.75 m (men) measured by Pachi and Ji
  [@pachi2005]. With the reported speed it would be 0.41 m, well below those means. This
  supports the position-derived figure, but no independent reference was available.
- **While riding**, reported and position-derived speeds are closer, but in 4 of 6
  segments the reported speed is below the straight-line lower bound, by 0.2–3.2 km/h.
- **GPS lags the accelerometer at walking onset** by about 12 s.
- For context: a dedicated (non-phone) GPS receiver on a bicycle gave speeds within
  0.2 m/s of a calibrated speedometer for 45% of values (a further 19% within 0.4 m/s),
  with larger errors on curved paths through a tendency to underestimate speed
  [@witte2004]. Phone receivers and walking speeds were not tested there, so this
  neither explains nor confirms the under-reading found here.

**Relevance to Part A.** Impact detection keeps peaks only when GPS-reported speed is
≥ 7 km/h. Two consequences:

- **The speed gate is needed.** Walking alone produced 11 peaks of ≥ 1.0 g (max 1.19 g)
  in the 316 s walk of recording 2, and handling the phone afterwards 3 more (max 2.21 g).
  With the gate, none of these were counted as impacts: all 39 impacts in recording 2
  fall before 10:43:46, during the ride.
- **The gate depends on GPS speed.** If reported speed under-reads at low speeds, some
  slow-riding impacts may be excluded. This has not been quantified for the ride data.

The impact map of recording 2 (`outputs/recordings/2026-10-07_1037_rec02/impact_map.html`)
shows the detected walking bouts as a dashed orange line, for context.

## 5. Ground truth and accuracy

References are in `data/ground_truth.csv`; the comparison is
`outputs/sensor_validity/ground_truth_comparison.csv`.

| Recording | Reference (source) | Precision | Detected | Result |
|---|---|---|---|---|
| 1 | No walking (rider) | whole recording | 6 s of walking labels, 0 walking bouts | Isolated false-positive windows; no false bout |
| 2 | Walking started "after 10 minutes" = 10:47:06 (rider's recollection) | about a minute | First step of sustained walking 10:46:47.04 | −19 s, within the reference's precision |
| 2 | Voi rental ended 10:46 (Voi app ride history, read by the rider) | one minute (10:46:00–10:46:59) | Last scooting segment ends 10:45:54; walking starts 10:46:47.04 | Order consistent: riding ends before the minute closes, walking starts after it opens |
| 3 | No walking (rider) | whole recording | 8 s of walking labels, 0 walking bouts | Isolated false-positive windows; no false bout |

What this shows:

- **Timing.** Two independent references, the rider's recollection and the Voi app's
  rental end, both place the change from riding to walking within the same minute as the
  detection. Both references have one-minute precision, so the check shows agreement at
  minute level. It does not measure the timing error in seconds.
- **Specificity at bout level.** Across about 25 minutes of recordings without walking
  (rec. 1 and 3), no walking bout was detected and no window was labelled walking while
  riding. Isolated walking labels covered 0.7% and 1.2% of those recordings.
- **Sensitivity.** There is only one walking episode, and it was detected. One episode
  cannot give a detection rate.

The rental end marks the end of the hire, not the end of riding or the start of
walking. The data place riding ending about 6–65 s before it.

## 6. Limitations

- One rider, one phone model, one app version, three recordings, one walking episode
  (about 5 minutes), and about 25 minutes of recordings without walking.
  The method may behave differently with other people, gaits, phone positions (pocket,
  bag), or when walking while pushing the scooter.
- Thresholds are analyst choices and were set after looking at recording 2. They were
  not fitted to labels, but they are not blind either. The ride-only recordings
  (1 and 3) were not used to set them.
- The references have one-minute precision (a recollection and the app's HH:MM time),
  and the rider's account that recordings 1 and 3 contain no walking is not independently
  checked.
- No external reference for acceleration, rotation or position. The data-quality
  results show internal consistency and plausibility, not absolute accuracy.
- Where the phone was during the walk (in the hand, in a pocket, or still on the
  handlebar while pushing the scooter) is not known. The gravity direction during the
  walk was steady and similar to the mounted position.
- Walking with the phone loosely held or in a bag may give weaker step signals than
  here. Low-amplitude walking could then fall under the stationary rule.

## 7. Data organisation and integrity

- Raw recordings live in `data/raw/<YYYY-MM-DD_HHMM>_recNN/` (local start time). Every
  folder holds the unmodified Sensor Logger CSVs. See `data/README.md`.
- Recording 1 was moved from the project root with `git mv`. SHA-256 checksums of all
  ten files were identical before and after the move. Re-running `impact_map.analyse()`
  on the new folder gives the same 40 impacts.
- Recordings 2 and 3 were extracted from the zips the rider provided. Each file's CRC was
  checked during extraction. The zips are kept unchanged in `data/raw/archive/`.
- `data/ground_truth.csv` holds reference events supplied by the rider.

## 8. To strengthen this for the paper

1. **References to the second.** The Voi app's ride history shows only HH:MM (used
   here). Sensor Logger annotations can mark events to the second, e.g. a tap just
   before starting to walk, but **only while stopped, never while riding**. Possibly
   the Voi receipt email or data request gives seconds (not checked).
2. **More walking episodes**, including walking while pushing the scooter and with the
   phone in a pocket, to estimate how often walking is detected and how often it is
   falsely detected.
3. **A reference for speed**: a measured route segment walked and ridden at known times,
   to test the GPS under-reading at walking speed.
4. Optional: a second phone or app recording at the same time, to compare sensor outputs.

## 9. Reproduce

```
python scripts/sensor_validity.py                                  # all recordings in data/raw
python scripts/sensor_validity.py --recordings 2026-10-07_1037_rec02
```

Outputs in `outputs/sensor_validity/`:

| Output | Contents |
|---|---|
| `report.html` | All results with figures |
| `quality_summary.csv` | Data-quality measures, one column per recording |
| `segments_all.csv` | Labelled segments, all recordings |
| `walking_onsets.csv` | Walking bouts and their first steps |
| `gps_speed_by_activity.csv` | GPS reported vs position-derived speed |
| `ground_truth_comparison.csv` | Detections vs the rider's references (walking start, rental end, no-walking recordings) |
| `<recording>/` | `windows.csv` (per-window features and labels), `segments.csv`, `quality.json`, `fig_timeline.png`, `fig_walk_onset_*.png`, `gps_speed_by_activity.csv` |

Settings are the constants at the top of `scripts/sensor_validity.py`
(`ANALYST CHOICES`). Python 3.11 [@python311], NumPy [@harris2020numpy], pandas
[@mckinney2010pandas; @pandas2025], SciPy [@virtanen2020scipy] (Welch spectrum,
Butterworth filter, peak detection) and Matplotlib [@hunter2007matplotlib].

## 10. Development notes (problems found and fixed)

| Issue | Fix |
|---|---|
| The first "at rest" noise figures used windows labelled stationary, which include standing with the phone in hand (gyro SD 0.1–0.3 rad/s, far above sensor noise) | Noise and bias now come from the quietest 5% of windows, stated as upper bounds where the phone was never still |
| Raw-vs-fused comparison matched only 494 samples in recording 2: the streams are sampled at different instants, and nearest-match within 5 ms failed | Fused signal interpolated to raw timestamps (211,261 samples compared) |
| Autocorrelation alone flagged a periodic low-amplitude vibration as walking | Step-band power share required as well (section 3.2) |
| `DOCUMENTATION.md` gave recording 1's start as 17:30 local; Sensor Logger's metadata `recording time` is UTC (local 18:30:29 BST) | Documentation corrected; map caption now labels that time as UTC |
