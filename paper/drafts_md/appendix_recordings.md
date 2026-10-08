<!--
DRAFT v0.1 (2026-10-08). Appendices for Part A: individual recordings (A), recording
quality and walking detection (B), visual check of spots (C).
Numbers from outputs/recordings/<rec>/ (impact_stats.json, impacts_by_road.csv,
fms_match_rates.csv), outputs/sensor_validity/ and outputs/combined/; figures copied to
paper/figures/appendix/ by scripts/paper_part_a.py. Full methods: SENSOR_VALIDITY.md,
SPOT_CHECK.md.
-->

# Appendix A: Individual recordings

The main text reports the three rides together. This appendix gives each ride on its
own. Hotspots here are numbered separately within each ride (impacts within 30 m of
each other in that ride); the spots P1–P33 of the main text are formed from the pooled
impacts and are numbered differently. Rates per km are left blank (–) where less than
0.2 km was ridden on a road.

*Table A1. Impacts per ride.*

<!-- outputs/recordings/<rec>/impact_stats.json -->
| | Ride 1 | Ride 2 | Ride 3 |
|---|---|---|---|
| Date, start (local) | 3 Oct, 18:30 | 7 Oct, 10:37 | 7 Oct, 13:38 |
| Vehicle (Voiager 5) | SZ22 | UPAR | BTLZ |
| Distance ridden | 2.89 km | 1.48 km | 1.71 km |
| Riding time; mean riding speed | 9.6 min; 18.1 km/h | 5.9 min; 15.1 km/h | 6.3 min; 16.4 km/h |
| Impacts (per km; metres between) | 40 (13.8; 72 m) | 39 (26.4; 38 m) | 21 (12.3; 81 m) |
| Median peak (interquartile range) | 1.19 g (1.13–1.35) | 1.34 g (1.19–1.77) | 1.67 g (1.13–1.85) |
| Maximum | 2.80 g | 2.87 g | 6.28 g |
| ≥ 1.5 g; ≥ 2.0 g | 6; 4 | 15; 3 | 11; 5 |
| Marked wobble; also ≥ 1.5 g | 13; 3 | 11; 5 | 8; 4 |
| Speed vs peak, Spearman ρ (p) | 0.03 (0.88) | −0.63 (< 0.001) | −0.68 (0.001) |
| Hotspots within the ride (2+ impacts) | 11 | 6 | 3 |

*Table A2. Impacts per km by road and ride (km ridden in brackets).*

<!-- outputs/recordings/<rec>/impacts_by_road.csv -->
| Road | Ride 1 | Ride 2 | Ride 3 |
|---|---|---|---|
| Marston Road | 11.6 (0.95 km) | 15.8 (0.82 km) | 9.3 (0.75 km) |
| Morrell Avenue | 12.2 (0.98 km) | – (0.04 km, 3 impacts) | – (0.03 km, 0 impacts) |
| Old Road | 8.2 (0.24 km) | not ridden | not ridden |
| Headington Road | not ridden | – (0.02 km, 1 impact) | not ridden |
| Other roads | 21.0 (0.72 km) | 36.7 (0.60 km) | 15.1 (0.93 km) |

*Table A3. Impacts with a road-surface FixMyStreet report made in the 365 days before the
ride within 15, 25 and 50 m, against the same share for all points on the ridden route
(baseline).*

<!-- outputs/recordings/<rec>/fms_match_rates.csv -->
| Radius | Ride 1: impacts / baseline | Ride 2: impacts / baseline | Ride 3: impacts / baseline |
|---|---|---|---|
| 15 m | 5.0% / 7.7% | 15.4% / 20.7% | 28.6% / 19.4% |
| 25 m | 5.0% / 14.3% | 30.8% / 32.7% | 42.9% / 34.3% |
| 50 m | 17.5% / 28.2% | 69.2% / 53.1% | 66.7% / 54.0% |

Each ride was compared with reports downloaded for its own route's area (ride 1 on
3 October 2026, rides 2 and 3 on 8 October 2026). In ride 1, none of the six impacts of
1.5 g or more and one of its eleven hotspots had a recent report within 25 m.

**Notes per ride.**

- **Ride 1.** One hotspot (near 51.7522, −1.2377; spot P12 in the main text) was hit on
  three separate passes, up to 2.68 g. It lies 6 m from a pothole reported in January
  2026 and marked "fixed". The two strongest impacts (2.80 g and 2.68 g) came at low
  speed just after a stop.
- **Ride 2.** Thirteen impacts followed each other every 0.6–1.2 s at about 8 km/h over
  roughly 20 m (spot P3). The ride ended at 10:46 (Voi rental end); the walk that
  followed is excluded by the speed rule (Appendix B).
- **Ride 3.** The strongest impact of all rides, 6.28 g at 8.1 km/h, was followed by four
  more impacts of 1.8–3.0 g within about 4 s (spot P4).

![Figure A1. Ride 1: vertical acceleration (top) and GPS speed (bottom) over the
recording, with detected impacts. Dashed lines: ±1 g threshold and 7 km/h speed
rule.](figures/appendix/2026-10-03_1830_rec01_impact_trace.png)

![Figure A2. Ride 1: peak vertical acceleration of the 40 impacts.](figures/appendix/2026-10-03_1830_rec01_fig_severity_hist.png)

![Figure A3. Ride 2: vertical acceleration and GPS speed. The walk (about 580–900 s) and
the phone at rest afterwards produce no impacts because of the speed
rule.](figures/appendix/2026-10-07_1037_rec02_impact_trace.png)

![Figure A4. Ride 2: peak vertical acceleration of the 39 impacts.](figures/appendix/2026-10-07_1037_rec02_fig_severity_hist.png)

![Figure A5. Ride 3: vertical acceleration and GPS speed.](figures/appendix/2026-10-07_1338_rec03_impact_trace.png)

![Figure A6. Ride 3: peak vertical acceleration of the 21 impacts.](figures/appendix/2026-10-07_1338_rec03_fig_severity_hist.png)

# Appendix B: Recording quality and walking detection

<!-- SENSOR_VALIDITY.md; outputs/sensor_validity/ -->
**Data quality.** Table B1 summarises the checks (method in section 2.2; full detail in
the project's `SENSOR_VALIDITY.md`). They show internal consistency and plausibility,
not absolute accuracy: no reference instrument was used.

*Table B1. Data quality per recording.*

| Check | Ride 1 | Ride 2 | Ride 3 |
|---|---|---|---|
| Motion sensors: rate; gaps or timestamp faults | 99.72 Hz; none | 99.72 Hz; none | 99.72 Hz; none |
| Raw vs fused acceleration, median difference | 0.049 g | 0.007 g | 0.013 g |
| Phone truly at rest during recording | no (on handlebar) | yes, after the walk | no (on handlebar) |
| Noise at rest; raw magnitude at rest | – | 0.001 g; 0.994 g | – |
| GPS: reported horizontal accuracy, median (90th percentile) | 11.5 m (15.1 m) | 11.3 m (15.5 m) | 13.9 m (17.6 m) |
| GPS: gaps over 1.5 s; longest | 2; 17 s (both at start) | 144; 15 s (after the walk, indoors) | 0; 1 s |

**Walking detection rules.** In 4 s windows, 1 s apart: *stationary* if the vertical
acceleration SD was below 0.5 m/s² and GPS speed below 2 km/h; *walking* if the
step-period autocorrelation and the step-band power share (1.2–2.8 Hz) were both at
least 0.5 and GPS speed below 8 km/h; *riding* if GPS speed was at least 8 km/h and the
step-band share below 0.3; otherwise *unclear*. Labels were smoothed with a 5-window
majority filter; a walking bout is at least 10 s of walking. Its first step is the first
of a regular series of step peaks (0.35–0.85 s apart) leading into the bout. All
thresholds are analyst choices, set before the rider's references were known and not
changed afterwards.

*Table B2. Detected activity against the rider's references (one-minute precision).*

<!-- outputs/sensor_validity/ground_truth_comparison.csv -->
| Recording | Reference | Detected |
|---|---|---|
| Ride 1 | No walking | 0 walking bouts; 6 s of isolated walking labels after the ride ended |
| Ride 2 | Rental ended 10:46 (Voi app) | Last riding segment ends 10:45:54; walking starts 10:46:47 |
| Ride 2 | Walking "after 10 minutes" (10:47) | First step of sustained walking 10:46:47 (−19 s) |
| Ride 3 | No walking | 0 walking bouts; 8 s of isolated walking labels after the ride ended |

*Table B3. GPS-reported speed against speed from GPS positions (segments of at least
30 s, 15 s trimmed at each end). The straight-line speed is a lower bound on the true
speed.*

<!-- outputs/sensor_validity/gps_speed_by_activity.csv -->
| Ride | Activity | Reported median | Straight-line | Summed path |
|---|---|---|---|---|
| 1 | riding | 20.1 km/h | 19.0 | 20.8 |
| 1 | riding | 19.1 | 19.3 | 19.7 |
| 2 | riding | 17.9 | 19.2 | 19.5 |
| 2 | riding | 12.1 | 15.3 | 15.4 |
| 2 | **walking** | **3.0** | **4.6** | 5.5 |
| 3 | riding | 19.5 | 19.5 | 19.6 |
| 3 | riding | 17.5 | 19.1 | 19.5 |

With the straight-line speed, the walk's implied step length is at least 0.62 m, close
to measured means of 0.67 m (women) and 0.75 m (men) [@pachi2005]; with the reported
speed it would be 0.41 m.

![Figure B1. Ride 1: GPS speed, vertical acceleration SD, step regularity and activity
labels. Dotted lines: thresholds.](figures/appendix/2026-10-03_1830_rec01_activity_timeline.png)

![Figure B2. Ride 2: the ride, the walk from 10:46:47 and the phone at rest afterwards.
The repeated high step-regularity values after the walk come with almost no power in the
step band: a small periodic vibration, which the step-band rule correctly rejects.](figures/appendix/2026-10-07_1037_rec02_activity_timeline.png)

![Figure B3. Ride 3.](figures/appendix/2026-10-07_1338_rec03_activity_timeline.png)

# Appendix C: Visual check of spots in street-level imagery

<!-- SPOT_CHECK.md; outputs/combined/spot_links.csv -->
All 33 spots are listed with links that open Google Street View at the spot, facing the
direction of travel and tilted 25° towards the road, a Google Maps pin, and Mapillary
imagery. The links use Google's documented Maps URLs, which need no API key
[@googlemapsurls]; no imagery is downloaded. Open imagery was checked first:
Panoramax [@panoramax] had no photos in the study area, and KartaView [@kartaview] had
five photos near spot P1, from 2017 and 2021, too old to show the current surface.

Rules fixed before checking: record the imagery date shown in the viewer; record what is
visible within about 15 m of the spot (the phone's median GPS accuracy was 11–14 m) as
one or more of *pothole*, *crack or broken surface*, *patched or repaired surface*,
*drain or manhole cover*, *kerb or dropped kerb*, *speed hump or raised table*,
*nothing visible*, *no imagery*; do not change the categories once started. Imagery
dates differ from the ride dates, so a visible feature supports an impact but a clean
image does not rule a defect out.

**Results:** pending.
<!-- TODO: summarise outputs/combined/spot_links.csv by tier once checked -->
