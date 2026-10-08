# Data

## Layout

```
data/
  raw/                              unmodified Sensor Logger recordings (read only)
    2026-10-03_1830_rec01/          Voi ride (Part A pilot ride)
    2026-10-07_1037_rec02/          ride, then walking from ~10:46:47, then phone mostly still
    2026-10-07_1338_rec03/          ride
    archive/                        the zips as received (recording2.zip, recording3.zip)
  ground_truth.csv                  reference events from the rider (e.g. walking start)
  fixmystreet/reports_<recording>.csv   cached FixMyStreet reports for that ride's area
  fixmystreet/reports_<recording>.bbox.json   area and date of that download
  osm_study_roads.json              cached OpenStreetMap geometry of the study roads
  osm_paper_basemap.json            cached OpenStreetMap streets/paths/parks/water for the paper map (2026-10-08)
```

Folder names are `<local start date>_<HHMM local start>_rec<NN>`. Local time is
Europe/London, computed from the nanosecond `time` column. Sensor Logger's
`Metadata.csv` field `recording time` is **UTC**, an hour behind in summer.

## Recordings

| Folder | Start (local) | Length | Content (rider's account) | Notes |
|---|---|---|---|---|
| `2026-10-03_1830_rec01` | 2026-10-03 18:30:29 | 13.7 min | Voi ride, vehicle SZ22 (Voiager 5); no walking | Moved from the project root 2026-10-07 (`git mv`, checksums identical) |
| `2026-10-07_1037_rec02` | 2026-10-07 10:37:06 | 35.3 min | Ride on UPAR (Voiager 5; Voi rental ended 10:46), then walking ("after 10 minutes") | GPS sparse after ~10:53:51 (indoors) |
| `2026-10-07_1338_rec03` | 2026-10-07 13:38:34 | 11.4 min | Ride on BTLZ (Voiager 5); no walking | |

All recordings: iPhone 11 Pro Max (iOS 26.6.2), Sensor Logger 1.67.1, phone on the
handlebar while riding, motion sensors at 10 ms, GPS about 1 Hz. All three rides were on
Voi **Voiager 5** scooters, confirmed by Voi customer support (personal communications, 3 October 2026 for ride 1 and 8 October 2026 for rides 2 and 3; model only). Vehicle IDs from the Voi app ride history: SZ22
(recording 1), UPAR (recording 2), BTLZ (recording 3); three different scooters.

## Files in each recording

| File | Contents |
|---|---|
| `Accelerometer.csv` | User acceleration (gravity removed), device frame, m/s² |
| `Gravity.csv` | Gravity vector, device frame, m/s² (same timestamps) |
| `AccelerometerUncalibrated.csv` | Raw accelerometer, **g** |
| `Gyroscope.csv`, `GyroscopeUncalibrated.csv` | Angular rate, rad/s |
| `Orientation.csv` | Attitude (quaternion, yaw/pitch/roll) |
| `Location.csv` | GPS fixes; `speed` in m/s, −1 = invalid; `horizontalAccuracy` in m |
| `Metadata.csv` | Device, app version, sample rates, start time (UTC) |
| `Barometer.csv`, `Annotation.csv` | Empty |

Columns: `time` (ns since Unix epoch), `seconds_elapsed`, then the sensor values.

## Rules

- Never modify files in `raw/`. A new recording goes in a new folder named as above.
- Record for each ride: the vehicle ID, and any exactly known times (e.g. the Voi app's
  rental end time) in `ground_truth.csv`.
- Ethics: only the rider's own recordings. Recordings contain exact locations; keep
  them local unless sharing is decided, and trim the start and end first.
