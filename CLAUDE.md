# E-scooter pothole impacts and front-wheel size (Oxford)

MSc student project (computer science background) by a regular Voi rider in Oxford.
Goal: a short paper giving evidence for safer e-scooter design, aimed at Voi,
Oxfordshire County Council, the DfT, the rider's MP and road safety groups (e.g. PACTS).

## Research question
Do pothole impacts on the current Voi e-scooter reach levels associated with loss of
stability, and would a larger front wheel reduce them?

Write it as a hypothesis that could turn out false, never as "proving Voi is unsafe".
Working hypothesis (from notes.md): because the front wheel both steers and takes the
peak load at impact, enlarging the front wheel alone gives most of the stability
benefit of larger wheels.

## Paper plan
**Part A: what riders experience on the road** (real sensor data, ridden legally on a Voi)
- Pilot ride so far: 40 impacts over 2.9 km, hotspots, and one spot hit on three
  separate passes (near 51.7522, -1.2377).
- Remaining desk work: FixMyStreet comparison and a Street View check of the hotspots.

**Part B: what a larger front wheel would change** (a model; no physical scooter needed)
- Geometry model (next to build, in Python): how far the wheel drops into a pothole and
  how hard it hits the far edge, for (1) current Voi wheels, (2) larger front wheel
  only, (3) larger wheels front and back.
- Optional dynamics model: a simple scooter and rider in MuJoCo or PyBullet.
- Consistency check: predicted jolts for the current wheel should fall in the range of
  the measured impacts. Without measured pothole depths this is a consistency check,
  not a validation; describe it that way.
- OpenSCAD/Blender only for design figures; they are not evidence of stability.

**Part C: what should change**
- Larger front wheel as a cost-effective design improvement, plus a call for physical
  testing by groups with test facilities.
- Only rental scooters in official trials are legal on UK roads (private e-scooters only
  on private land with permission), so operators and DfT trial rules set the design of
  every legal e-scooter. Recommendations therefore go to a small number of actors.

**Optional later:** a legal physical check rolling trolley or caster wheels of different
sizes over a pothole-shaped step, phone recording. Not part of the current paper.

### Voi wheel facts (searched 2026-10-03)
- Voiager 5: 10 in wheels, front spring (Levy fleet spec; tyre type disputed, see
  below); no source separates front and rear size. Launch coverage: "a larger front wheel with increased
  tyre tread depth" and raised ride height "to cope better over potholes" (larger than
  the previous model, not stated vs rear). Voi enlarged the front wheel for potholes on
  V5 and again on V7: strong industry precedent for the paper.
- Voiager 7 (2024): 12 in front tyre, "a size increase from its predecessors"; rear not
  stated. Voi has itself moved to a larger front wheel: cite as industry precedent.
- Voiager 9 (spring 2026): no wheel data in the press release.
- Ridden vehicle SZ22 = Voiager 5 (confirmed by the user 2026-10-03). Wheels reported as
  10 in by Levy spec and Alsalkini 2023 Chalmers thesis (Table 8; weak: cites a V3X
  video, no front/rear split; its 13 kg mass is a borrowed assumption, don't use).
  Tyre type DISPUTED (Levy: pneumatic; user-pasted summary: solid honeycomb); user to
  check for a valve. Stiffer tyres raise sim jolts, fall rankings unchanged.
  If confirmed honeycomb: set TYRE_TIMECONST to ~0.015 s (or stiffer) in
  scripts/scooter_sim.py, rerun all `--suspension` experiments and `--consistency`,
  and update SIMULATION_METHODS.md and DOCUMENTATION.md 6.6.
- No official Voi CAD is published; fan models are illustration only.

### Open tasks
- [x] Geometry model and figures (`scripts/wheel_geometry.py`)
- [x] Confirm Voi model: SZ22 is a Voiager 5
- [ ] Voiager 5 tyre type: pneumatic or honeycomb? (look for a valve) (user)
- [x] Dynamics model in MuJoCo (`scripts/scooter_sim.py`, done 2026-10-03)
- [x] Front suspension option (`--suspension`): consistency partial pass (300 mm
      potholes 1.9-2.4 g = in measured range; 600 mm 4.2-5.7 g = ~2x high). This is
      the more faithful model of the Voiager 5; present it as the main model.
- Rounded edges with MuJoCo's own collision FAIL (multi-contact stiffening; mesh didn't
  converge). Soft edges are done with the custom profile contact instead:
  `CONTACT_MODEL = "profile"`, `EDGE_WIDTH` (raised-cosine sloped edges), class
  ProfileTyres (point radial-spring contact via xfrc_applied). Validated: flat road
  0.01 g, 30/30 fall outcomes match MuJoCo contact on sharp edges, converges with
  PROFILE_DX. Its absolute jolts are too high (point contact, no enveloping; more
  damping made it worse) -> use it for falls/edge comparisons only; MuJoCo contact +
  suspension stays the jolt-size model. `--suspension --edges` runs 1296 runs on 4 cores.
- Soft-edge results: falls 10/10 8->4 from sharp to 100 mm edges; larger front helps at
  every edge width; 12/10 ~= 12/12 throughout.

### Simulation results with suspension (outputs/scooter_sim/suspension/)
- Falls in main sweep (81 runs each): 10/10 9, 12/10 6, 12/12 6, 14/10 1 (vs 15/14/14/11
  without suspension). Suspension itself is a big factor: recommend it with wheel size.
- 12/10 = 12/12 fall depths in all main-sweep cases and 8/9 sensitivity settings.
- 12 in front benefit is modest with suspension (speed loss 28% vs 26% at 60x600);
  14 in front nearly eliminates falls. All falls still front-impact pitch-overs.

### Simulation results without suspension (scooter_sim.py, 324 runs + sensitivity)
- 12/10 (larger front only) matches 12/12 (larger both) in every case: same fall depth,
  speed loss within ~2 points. Holds under all tyre/bracing sensitivity settings.
- Larger front wheel raises the falling depth by ~10 mm (e.g. 1000 mm pothole, 20 km/h:
  10/10 falls from 70 mm, 12/10 and 12/12 from 80 mm). 14/10 helps more.
- No falls for 300 mm long potholes; 600 mm only at 15 km/h (slower = drops deeper).
- Falls are pitch-over of scooter+rider about the front wheel, as in the Imperial study.
- Absolute fall depths depend on tyre stiffness (10/10: 60-70 mm); report the relative
  comparison, not absolute thresholds. 10 mm depth steps limit resolution.
- Ratio study (`--ratio`, 10/10 to 20/8): no "too big" point in this planar model;
  falls keep decreasing. ALL falls are front-impact pitch-overs (rear wheel lifted
  clear). With small front wheels the front impact lifts the rear (~140 mm) so the
  rear skips the hole; with big front wheels the rear drops in and gives a second jolt
  (rear-crossing speed loss up to 33% for 20/8) but caused no falls. Rear 8 vs 10 in
  and wheel-mass scaling made no difference. Steering, frame geometry and cost are not
  modelled, so recommend a moderate front increase (12-14 in).
- Fall cause is attributed to the rear only if the rear wheel dipped > 5 mm into the
  pothole before the fall (time-based phase labels mislabelled slow pitch-overs).
- `--animate` builds `outputs/scooter_sim/animations.html` from ANIMATION_SETS.
- [x] FixMyStreet comparison (`scripts/fms_compare.py`, done 2026-10-03)
- [ ] Street View check (user): use `outputs/streetview_check.html` (25 spots, 360 links
      facing direction of travel, record form, Export CSV -> data/streetview_observations.csv), incl. hotspot 21: hit 3 times at up to
      2.68 g although a pothole 6 m away was marked "Fixed" in Jan 2026
- [ ] Proper literature search (Google Scholar; papers citing the Imperial 2022 study)
- [ ] Write the paper together

The user has said measuring potholes on foot is too much work; don't plan around
fieldwork measurements. Rides and desk work are fine.

## Scope and claims
- Can claim: the smartphone method works; measured exposure on this ride; geometric
  effect of wheel size; that the results justify a larger study.
- Cannot claim: Voi scooters proven unsafe (one ride, one rider); bigger wheels proven
  to prevent falls (unvalidated model); anything about injury risk or other riders.
- The 1.0 g impact threshold, severity bands and 1.5x wobble ratio are analyst choices,
  not established criteria; always say so.
- Plain e-scooter vs bicycle vibration comparisons already exist (e.g. Italy 2023,
  ISO 2631 comfort). The new angles are discrete impacts rather than comfort vibration,
  the front-wheel-only question, unreported hazards, and measured vs felt risk.

## Documentation
- `DOCUMENTATION.md`: full record of the project and results.
- `SIMULATION_METHODS.md`: methods for both wheel models. Keep it in sync with
  `scripts/scooter_sim.py` and `scripts/wheel_geometry.py` when they change.

## Literature
`notes.md` holds the user's literature notes (Posirisuk, Baker and Ghajari, Accident
Analysis & Prevention: 10-inch wheels, no falls at 3 cm, 75% falls at 6 cm; a 2026
Machines paper on front/rear tyre stiffness; Swifty tests; patents). These came from
another chat and are **not yet checked against the papers**. Verify before citing.
Check Mazdak Ghajari's current title on his Imperial profile (the 2022 news release says
"Dr"). Treat Swifty as commercial, not neutral, evidence.

## Study roads
Marston Road, Headington Road (incl. Headington Hill), Old Road (Headington) and
Morrell Avenue. Cheney Lane was dropped (not ridden). A different "Old Road" exists at
Forest Hill / Shotover; the study bounding box in `scripts/impact_report.py` excludes it.

## Data
- Recorded with Sensor Logger on an **iPhone 11 Pro Max** (not Android), handlebar mount.
- Raw CSVs currently sit in the project root (one ride, 2026-10-03). Never modify them.
  Future rides go in their own folders, e.g. `data/raw/<date>_<name>/`.
- `Accelerometer.csv` is user acceleration with gravity removed, m/s^2, device frame;
  `Gravity.csv` is the gravity vector (same timestamps). Gyroscope ~100 Hz, GPS ~1 Hz.
  `Barometer.csv` and `Annotation.csv` are empty.
- `data/osm_study_roads.json`: cached OpenStreetMap road geometry; refreshes itself
  when the road list or bounding box changes.

## Scripts
- `scripts/impact_map.py`: impact detection (vertical acceleration from the gravity
  vector, peaks >= 1.0 g at >= 7 km/h, 0.5 s apart; gyro wobble ratio) and folium map.
  `analyse()` is shared with the report script.
- `scripts/impact_report.py`: statistics report (rates, severity, wobble, by road,
  hotspots, speed vs severity) to `outputs/impact_report.html` plus CSV/JSON/figures.
- `scripts/streetview_page.py`: builds `outputs/streetview_check.html` from
  `outputs/impacts_vs_fms.csv` (Google Street View pano links; no API key, so no embed).
- `scripts/fms_compare.py`: impacts vs FixMyStreet road-surface reports
  (`outputs/fms_comparison.html`, `outputs/fms_map.html`). Main comparison uses only
  reports made in the 365 days before the ride, always against a route baseline:
  reports since 2009 are so dense that ~70-80% of route points are near one.
  Reports cached in `data/fixmystreet/reports.csv` (`--refresh` to re-download; it
  makes ~15 polite requests, for anything bigger ask mySociety for bulk data).
- `scripts/wheel_geometry.py`: rigid wheel crossing a sharp-edged rectangular pothole;
  drop = min(depth, sag, ballistic 0.5 g (w/v)^2), edge angle cos(theta) = (R-h)/R,
  impact velocity v sin(theta), front speed loss v sin^2(theta). Relative comparison of
  wheel sizes only (no tyre stiffness/suspension). Outputs in `outputs/wheel_model/`.
- `scripts/scooter_sim.py`: planar MuJoCo model (chassis + 2 wheels + rider pinned at
  the feet with spring-damper), sharp rectangular pothole, coasting, no steering;
  optional front fork (`--suspension`, outputs in .../suspension/). Sweep of 4 wheel
  configs x depths x lengths x speeds; `--animate` GIFs; `--sensitivity` (tyre,
  bracing, and fork when suspended); `--consistency` vs the measured ride. Mass, wheelbase, tyre
  compliance and rider bracing are ASSUMED. Outputs in `outputs/scooter_sim/`.
- Run: `python scripts/impact_map.py` then `python scripts/impact_report.py`
  then `python scripts/fms_compare.py`
  (defaults: `--data-dir .`, `--out-dir outputs`).
- Python 3.11 with pandas, numpy, scipy, matplotlib, folium.

## Conventions
- Reproducible scripts, clear comments; the code will be cited in the paper.
- Figures: one blue sequential ramp for severity, thin marks, no dual axes.
- The user opens HTML maps from disk (file://). OpenStreetMap tiles return 403 and
  CARTO returns "API KEY REQUIRED" tiles there; use the Esri Light Gray Canvas layers
  (native max zoom 16). When testing a tile source, look at the image, not the status.
- Windows: a figure open in an image viewer can't be overwritten (Errno 22); close it.
- Maps and reports contain exact ride coordinates; keep them local unless the user
  asks to share, and suggest trimming ride start/end first.

## Ethics
Only the user's own rides. Other riders' data would need university ethics approval
and GDPR-compliant handling. Never interact with the phone while riding.
