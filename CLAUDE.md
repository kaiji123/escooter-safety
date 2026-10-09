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
- DECIDED 2026-10-08: Part A uses **all three recordings** (rec01-rec03): 100 impacts over
  6.08 km ridden; per ride and pooled (pooled = descriptive; rides not independent).
  Vehicles: all three rides on Voiager 5, confirmed by Voi customer support (personal
  communications: rec01 on 2026-10-03, key voi2026support_rec01; rec02/rec03 on 2026-10-08,
  key voi2026support_rec0203; model only, not wheel sizes).
  Vehicle IDs (Voi app): rec01 SZ22, rec02 UPAR, rec03 BTLZ (given by the user 2026-10-08).
  Three different scooters.
- Ride 1 alone: 40 impacts over 2.9 km; one spot hit on three passes (near 51.7522, -1.2377).
- Across rides: 10 spots hit on 2+ rides, 2 on all three (Marston Road).
- Remaining desk work: Street View check (`outputs/combined/spot_links.csv`, SPOT_CHECK.md).

**Road bumps: in the paper as Appendix D (user reversed the earlier "not in the paper"
decision on 2026-10-08).** Exploratory only; sources SIMULATION_METHODS 3.15/4.9,
DOCUMENTATION 6.8, bump clips in animations.html.

**Part B: what a larger front wheel would change** (a model; no physical scooter needed)
- Geometry model (next to build, in Python): how far the wheel drops into a pothole and
  how hard it hits the far edge, for (1) current Voi wheels, (2) larger front wheel
  only, (3) larger wheels front and back.
- Optional dynamics model: a simple scooter and rider in MuJoCo or PyBullet.
- Consistency check: predicted jolts for the current wheel should fall in the range of
  the measured impacts. Without measured pothole depths this is a consistency check,
  not a validation; describe it that way.
- OpenSCAD/Blender only for design figures; they are not evidence of stability.

**Part C: what should change** (argument decided 2026-10-07; full version in
DOCUMENTATION.md section 12, use it for the paper's intro and conclusion)
- Thesis: London requires front >= 11 in (TfL 2022), national trial rules set no minimum,
  so older smaller-fronted models (Voiager 5, reported 10 in) stay in service outside
  London (Oxford; Essex 2025). The model suggests a larger front delays falls -> extend a
  front-wheel minimum to all trials. Plus a call for physical testing.
- Say "outside London", not "rural"; name examples, never claim fleet numbers.
- Voiager 5 sizes: use the reported 10/10 as a stated assumption (user's decision; no
  company email for now).
- OPEN: which Voi model runs in London. If it's the Voiager 5, the 10 in reports and the
  thesis must be revisited (DOCUMENTATION.md 12.4).
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
- Ridden vehicle SZ22 = Voiager 5 (confirmed by Voi customer support 2026-10-03; UPAR and
  BTLZ confirmed 2026-10-08; model only). Wheels reported as
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
- [ ] Voiager 5 front AND rear tyre sidewall sizes (user, parked scooter). If the front is
      larger, the "10/10 = Voiager 5" sim baseline must be relabelled.
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

### Road bump results (`--bumps [--suspension]`, outputs/scooter_sim/[suspension/]bumps/; done 2026-10-07)
EXPLORATORY, unvalidated (no bumps measured on the ride). Report as model observations
with uncertainties (DOCUMENTATION.md 6.8), never as findings about real scooters.
- Sharp-edged bumps (defects: proud covers, patches, lifted slabs; legal humps may not
  have vertical faces > 6 mm) 20-100 mm x 300/600/1000 mm; round-top humps (3.7 m UK
  standard per TAL 2/96; 600 mm car-park bump) on the profile contact only.
- No fork: more model falls on sharp bumps than same-size potholes (10/10 22 vs 15 of
  81); fewer with larger fronts (22/13/14/4); rear size alone changed nothing.
- With fork: falls 1/2/1/2, only 300 mm at 15 km/h, all met after the rear-wheel strike;
  in a small check larger rears raised falling height 5-15 mm (10/14 none). Treat as an
  open question that the front-only hypothesis may not cover every obstacle, NOT as
  "bigger rear wheels are more stable". No bump sensitivity runs yet.
- Round-top humps: 0 falls anywhere. Contact models agree on 91-95% of bump falls (vs
  100% potholes); bump jolts unvalidated. Roadblocks: SIMULATION_METHODS.md 5.1.
- Bump clips are in the same `animations.html` (BUMP_ANIMATION_SETS; `--bumps --animate`
  reuses existing GIFs).
- Paper figures from animations: `scooter_sim.py --keyframes` (KEYFRAME_SETS, potholes only)
  -> outputs/scooter_sim/keyframes/ -> paper/figures/fig_b5/b6 (copied by paper_part_a.py).

### Sensor Logger validity (SENSOR_VALIDITY.md; done 2026-10-07; exploratory)
- Motion sensors 99.72 Hz, no gaps/timestamp faults in any recording. True rest only in
  rec02: noise ~0.001 g, static magnitude 0.994 g. Other recordings' noise = upper bounds.
- rec02 sustained walking from 10:46:47 (first step; 275 s, 2.04 steps/s). References
  (data/ground_truth.csv, 1-min precision): user "after 10 minutes" (-19 s) and Voi app
  rental end 10:46 (riding ends 10:45:54; order consistent). Minute-level agreement only.
  The 8 s burst at 10:45:58 resembles the false positives; not treated as walking start.
- rec01/rec03 confirmed no walking: 0 walking bouts; 6 s / 8 s isolated labels (0.7%/1.2%),
  all after the ride ended. Thresholds were NOT changed after seeing this.
- Of 1,126 GPS-riding windows (>= 12 km/h), none met the walking criteria.
- GPS reported speed under-reads walking (3.0 vs >= 4.6 km/h from positions), sometimes
  riding (4/6 segments, 0.2-3.2 km/h); 12 s GPS lag at walk onset. May affect the 7 km/h
  impact gate (not quantified).

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
- [ ] Street View check (user): now `outputs/combined/spot_links.csv` + rules in SPOT_CHECK.md 5.
      Older rec01 page: `outputs/recordings/2026-10-03_1830_rec01/streetview_check.html` (25 spots, 360 links
      facing direction of travel, record form, Export CSV -> data/streetview_observations.csv), incl. hotspot 21: hit 3 times at up to
      2.68 g although a pothole 6 m away was marked "Fixed" in Jan 2026
- [ ] Proper literature search (Google Scholar; papers citing the Imperial 2022 study)
- [ ] Write the paper together. 2026-10-08: `paper/part_a_measured_impacts.md` (section 2,
      three rides combined, Tables 1-3, Figures 1-5 incl. speed-vs-severity scatter; LaTeX numbers figures automatically) and `paper/appendix_recordings.md`
      (A: each ride, B: recording quality/walking, C: spot check method; results pending).
      Figures + every quoted number: `scripts/paper_part_a.py` -> paper/figures/ and
      part_a_numbers.json. Part B tables renumbered 4-8; key-frame Figures 5-6 added.
      Next: intro, discussion/conclusion (after the London-model check), abstract.
      2026-10-08: paper moved to LaTeX (plain preprint, LuaLaTeX + biblatex authoryear/Biber,
      Libertinus fonts). Edit paper/main.tex + paper/sections/*.tex (the .tex files ARE the
      paper; Markdown drafts archived in paper/drafts_md/, converted once with
      scripts/md_to_latex.py). Build: `python paper/build.py` (MiKTeX in
      %LOCALAPPDATA%/Programs/MiKTeX, auto-installs packages; reports undefined refs,
      missing glyphs, overfull boxes). Bibliography = ../references.bib directly. Check pages
      visually (pymupdf renders PDF pages). Figures are generated at print width (~7 in).
      Introduction, Discussion, Conclusion drafted 2026-10-08 (01_introduction.tex,
      05_discussion.tex; depend on the reported 10 in front, see header comments).
      Author: Kai Yi Ji (given 2026-10-08). Abstract written 2026-10-08.
      No affiliation/contact footnote (removed 2026-10-08: hobby project, so no university
      name that could imply endorsement).
      Started 2026-10-07: `paper/part_b_methods_results.md`
      (Part B methods + results, Pandoc citations from references.bib; every number taken
      from outputs/, source file noted in HTML comments). Next: Part A methods/results,
      then intro/discussion from DOCUMENTATION.md section 12.
      Now LaTeX in paper/ (`python paper/build.py`). User wants ALL figures and data in
      the paper (appendix if not main text); never silently drop outputs. But tables that
      only repeat a figure or public data are padding: propose leaving them out, explain why,
      and let the user decide (split into main + supplement was offered, not yet decided). Appendix A: per
      ride trace, severity, speed, impact map, FMS map; B: full sensor validity; C: spot
      links + QR; D: bumps; E: all other model figures (`SIM_FIGURES` in paper_part_a.py).

The user has said measuring potholes on foot is too much work; don't plan around
fieldwork measurements. Rides and desk work are fine.

## Scope and claims
- Can claim: the smartphone method works; measured exposure on this ride; geometric
  effect of wheel size; that the results justify a larger study.
- Cannot claim: Voi scooters proven unsafe (one ride, one rider); bigger wheels proven
  to prevent falls (unvalidated model); anything about injury risk or other riders.
- The 1.0 g impact threshold, severity bands and 1.5x wobble ratio are analyst choices,
  not established criteria; always say so.
- Plain e-scooter vs bicycle vibration comparisons already exist (e.g. Ventura et al. 2024 "Italy",
  ISO 2631 comfort). The new angles are discrete impacts rather than comfort vibration,
  the front-wheel-only question, unreported hazards, and measured vs felt risk.

## Documentation
- `DOCUMENTATION.md`: full record of the project and results.
- `SENSOR_VALIDITY.md`: methods/results/limitations of the Sensor Logger check (paper-ready).
- `SPOT_CHECK.md`: method for checking impact spots in street-level imagery (tiers, link
  formats, recording rules fixed before checking: categories, 15 m search area).
- `REFERENCES.md` + `references.bib`: master bibliography (papers, software with versions,
  data/map services, vehicle and policy sources). Add an entry whenever a new library,
  dataset or source is used; [to verify] items must be checked before citing.
- `SIMULATION_METHODS.md`: methods for both wheel models. Keep it in sync with
  `scripts/scooter_sim.py` and `scripts/wheel_geometry.py` when they change.

## Literature
`notes.md` holds the user's literature notes (Posirisuk, Baker and Ghajari, Accident
Analysis & Prevention: 10-inch wheels, no falls at 3 cm, 75% falls at 6 cm; a 2026
Machines paper on front/rear tyre stiffness; Swifty tests; patents). These came from
another chat. Checked 2026-10-07 (see REFERENCES.md): Imperial paper = 180 sims, 41/60
falls at 6 cm ("75%" is the news release, 6+9 cm); Machines 2026 = Vaca Michilena &
Cano-Moreno, comfort not stability. Swifty tests and patents not found; verify before citing.
Check Mazdak Ghajari's current title on his Imperial profile (the 2022 news release says
"Dr"). Treat Swifty as commercial, not neutral, evidence.
Literature search 2026-10-08 (REFERENCES.md, "Literature search ..."): verified keys paudel2025
(experiments: small wheels less stable; recommends >= 14 in wheels + front suspension),
nathania2026 (review: falls most common, multifactorial), fournier2023 (curb-strike falls),
leoni2022, eriksson2008, zang2018, cicchino2021, anke2025, lee2024fall, dft2026factsheet
(GB 2025: 10 riders killed, ~410 serious; 28% single-vehicle; heavy under-reporting; no
road-surface factors). Do NOT cite "67% of DC falls due to bad roads" (not in Cicchino).
Swifty pothole tests exist (company blog): commercial, not peer reviewed.
London Voi model: still not found 2026-10-08; decisive check = Oxford V5 front tyre size
(sidewall) or ask Voi support (DOCUMENTATION.md 12.4).
`literature/wheel_size_industry_cases.md`: industry cases of bigger wheels (Voi, Lime,
Bird, mullet MTBs, 29er, plus tyres, penny-farthing, cars) with bibliography for Part C;
items marked [unchecked] still need verifying.
`literature/uk_fleet_wheel_sizes.md`: UK rules and fleet models (2026-10-07). No checked
source shows a UK model with equal wheels; Beryl (OKAI ES400, 12/9-10), Lime Gen4 and TIER
have larger fronts; TfL London requires front >= 11 in, rear >= 9 in; DfT sets no size.
Voiager 5 front/rear split unknown.

## Study roads
Marston Road, Headington Road (incl. Headington Hill), Old Road (Headington) and
Morrell Avenue. Cheney Lane was dropped (not ridden). A different "Old Road" exists at
Forest Hill / Shotover; the study bounding box in `scripts/impact_report.py` excludes it.

## Data
- Recorded with Sensor Logger on an **iPhone 11 Pro Max** (not Android), handlebar mount.
- Raw recordings: `data/raw/<YYYY-MM-DD>_<HHMM local>_recNN/` (see `data/README.md`). Never
  modify them. rec01 = 2026-10-03 18:30 pilot ride (moved from the root 2026-10-07, checksums
  identical); rec02 = 2026-10-07 10:37 ride then walk; rec03 = 2026-10-07 13:38 ride. Zips as
  received in `data/raw/archive/`. Part A uses all three recordings (decided 2026-10-08).
- Sensor Logger metadata `recording time` is UTC; use the ns `time` column -> Europe/London.
- `data/ground_truth.csv`: rider-supplied reference events (precision noted per row).
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
  hotspots, speed vs severity) to `outputs/recordings/<recording>/impact_report.html` plus CSV/JSON/figures.
- `scripts/streetview_page.py`: builds `outputs/recordings/<recording>/streetview_check.html` from
  that folder's `impacts_vs_fms.csv` (Google Street View pano links; no API key, so no embed).
- `scripts/fms_compare.py`: impacts vs FixMyStreet road-surface reports
  (`outputs/recordings/<recording>/fms_comparison.html`, `fms_map.html`). Main comparison uses only
  reports made in the 365 days before the ride, always against a route baseline:
  reports since 2009 are so dense that ~70-80% of route points are near one.
  Reports cached per recording in `data/fixmystreet/reports_<recording>.csv` + `.bbox.json`
  (area); the script refuses a cache that does not cover the route (`--refresh` to
  download; ~15 polite requests; for anything bigger ask mySociety for bulk data).
- Consistency check reference (scooter_sim.py MEASURED_G) = three rides: 99/100 impacts
  1.0-2.97 g, median 1.27 g, one 6.28 g outlier. Criterion (1-3 g) unchanged; results unchanged.
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
  `--bumps` runs the road bump study (OBSTACLE/BUMP_SHAPE globals; run the main sweep
  first, it is read in for the bump-vs-pothole comparison).
- `scripts/sensor_validity.py`: Sensor Logger data quality (sampling, clock, raw vs fused,
  noise in quietest 5% of windows, GPS) and walking/scooting/stationary/unclear segmentation
  (4 s windows; step-band power share 1.2-2.8 Hz, step-lag autocorrelation, GPS speed;
  analyst-chosen thresholds) with first-step onset refinement. All recordings in data/raw ->
  `outputs/sensor_validity/report.html`. Methods + results: `SENSOR_VALIDITY.md`.
- `scripts/paper_tables.py`: appendix summary tables from outputs/ CSVs
  In the paper: appendix_model_tables.tex = E1-E3 (no-fork thresholds, sensitivity),
  appendix_bump_tables.tex = D3-D4, appendix_impact_list.tex = all 100 impacts without
  coordinates, ratio_fall_counts.tex = main-text Table 9 (ratio-study fall counts; the
  appendix figures show depths, not counts). Removed from the paper 2026-10-08 (user agreed: they repeat figures,
  captions or public data) but still generated into paper/supplement/: FMS report list,
  geometry/consistency/key-frame tables, ratio and soft-edge thresholds. Back matter:
  paper/sections/06_statements.tex (ethics, data availability; DOI TBD).
  Rerun after any scooter_sim.py run.
- `scripts/outputs_index.py`: `outputs/index.html`, overview of all recordings.
- `scripts/combined_outputs.py`: `outputs/combined/` (impacts_all.csv, summary, by_road with
  rates blank < 0.2 km, hotspots_all with number of rides hitting each spot, combined map with
  a layer per recording). Pooled numbers are descriptive: rides are not independent.
  Two Marston Road spots hit on all 3 rides (51.75427,-1.23588; 51.75268,-1.23665).
- `scripts/spot_links.py`: `outputs/combined/spot_links.csv/.html`, 33 spots ranked by tier
  with Google Street View/Maps/Mapillary links (Maps URLs, no key; no scraping/downloading
  Google imagery). Fill-in columns survive reruns. Panoramax: no coverage; KartaView: 2017/2021
  only. This supersedes rec01's streetview_check page for new checks.
  NO Street View screenshots in the paper or any print (Google geo guidelines, checked
  2026-10-08); report findings + links only; images only from Mapillary (CC BY-SA) or own photos.
  Paper Table C1 = generated spot list with clickable links (paper_part_a.py -> sections/
  appendix_spot_links.tex, landscape, styled like spot_links.html). Spots in trimmed route
  ends (P9, P16, P30, P31) are named only; the map also omits their circles (privacy).
  Each row has a QR code (Street View link) for print; verify with zxing-cpp after changes
  (all 29 decode at 150 dpi).
  `impact_map.py` draws walking bouts from walking_onsets.csv (dashed orange) if present.
- Speed gate matters: rec02's walk had 11 peaks >= 1 g (max 1.19 g), all excluded by the
  7 km/h gate. rec02 impacts 25-37 = regular series (unchecked); rec03 6.28 g cluster is
  ~20 m from a rec02 hotspot (51.7508, -1.2389): Street View candidate.
- Run: `python scripts/impact_map.py` then `python scripts/impact_report.py`
  then `python scripts/fms_compare.py`
  (defaults: `--data-dir data/raw/2026-10-03_1830_rec01`; outputs to
  `outputs/recordings/<recording folder>/` unless `--out-dir` is given).
- Outputs layout (`outputs/README.md`): `index.html` overview; `recordings/<recording>/` per
  ride (rec01 moved there 2026-10-07, identical); `combined/` all rides; `sensor_validity/`;
  `scooter_sim/`; `wheel_model/`. Nothing per-recording at the root of `outputs/`.
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
