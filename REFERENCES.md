# References (master bibliography)

Every source, dataset, software package and app used in this project, in Harvard style.
BibTeX versions of the same entries are in `references.bib`.

Compiled 2026-10-07. "Checked" means the entry's details were confirmed that day against
Crossref or Europe PMC (papers) or the publisher's own page. **[to verify]** means it has not
been confirmed yet and must be checked before it goes into the paper. All URLs accessed
7 October 2026 unless stated.

Part C industry and fleet sources have their own full bibliographies, which are part of
this one:
- `literature/wheel_size_industry_cases.md` (bigger-wheel successes and failures)
- `literature/uk_fleet_wheel_sizes.md` (UK rules, operators, models and wheel sizes)

---

## 1. Research literature

| Key | Used for | Status |
|-----|----------|--------|
| Posirisuk et al. 2022 | Fall thresholds, rider sizes, pitch-over mechanism; basis of the sim | Checked |
| Imperial College London 2022 | "75 per cent" figure; plain-language summary | Checked |
| Ventura et al. 2024 | Prior e-scooter vs e-bike vibration work | Checked |
| Cano-Moreno et al. 2022 | Prior e-scooter comfort vibration work | Checked |
| Vaca Michilena and Cano-Moreno 2026 | Front/rear tyre stiffness asymmetry | Checked |
| ISO 2631-1:1997 | Comfort vibration standard used by the two *Machines* papers | Standard details checked; not used for analysis |
| Spearman 1904 | Rank correlation, speed vs severity | Checked |
| Sibson 1973 | Single-linkage clustering, hotspots | Checked |
| Alsalkini 2023 | Voiager wheel size (weak) | Checked earlier in project |

Cano-Moreno, J.D., Cabanellas Becerra, J.M., Arenas Reina, J.M. and Islán Marcos, M.E.
(2022) 'Analysis of e-scooter vibrations risks for riding comfort based on real
measurements', *Machines*, 10(8), 688. doi:10.3390/machines10080688.

Imperial College London (2022) 'E-scooter simulations highlight head injury risk to riders
from falls', *Imperial News*, 25 January. Available at:
https://www.imperial.ac.uk/news/233378/e-scooter-simulations-highlight-head-injury-risk

International Organization for Standardization (1997) *ISO 2631-1:1997 Mechanical
vibration and shock: evaluation of human exposure to whole-body vibration. Part 1:
General requirements*. Geneva: ISO.

Posirisuk, P., Baker, C. and Ghajari, M. (2022) 'Computational prediction of head-ground
impact kinematics in e-scooter falls', *Accident Analysis & Prevention*, 167, 106567.
doi:10.1016/j.aap.2022.106567. PMID 35033967.

Sibson, R. (1973) 'SLINK: an optimally efficient algorithm for the single-link cluster
method', *The Computer Journal*, 16(1), pp. 30–34. doi:10.1093/comjnl/16.1.30.

Spearman, C. (1904) 'The proof and measurement of association between two things', *The
American Journal of Psychology*, 15(1), pp. 72–101. doi:10.2307/1412159.

Vaca Michilena, E.X. and Cano-Moreno, J.D. (2026) 'Multibody dynamic analysis of an
e-scooter considering asymmetric tire stiffness, speed, and surface roughness',
*Machines*, 14(1), 120. doi:10.3390/machines14010120.

Ventura, R., Ghirardi, A., Vetturi, D., Maternini, G. and Barabino, B. (2024) 'Comparing
the vibrational behavior of e-kick scooters and e-bikes: evidence from Italy',
*International Journal of Transportation Science and Technology*, 16, pp. 68–86.
doi:10.1016/j.ijtst.2023.10.010. (Online 2023; an SSRN preprint exists:
doi:10.2139/ssrn.4072708.)

Alsalkini, A. (2023) *The influence of e-scooters on urban mobility and transport related
emissions*. Master's thesis. Chalmers University of Technology. Available at:
https://odr.chalmers.se/server/api/core/bitstreams/2d2b9c13-ea55-44e3-aa07-ac1eb8a65968/content

### What the papers actually say (checked against the abstracts)
- **Posirisuk et al. 2022:** 180 simulations, three human body models (5th percentile
  female, 50th and 95th percentile male), 10 in wheels. 3 cm potholes: no falls; 6 cm:
  **41 falls out of 60 cases** (68%). The "75 per cent" figure is from the Imperial news
  release and covers 6 cm **and** 9 cm together. Cite the paper for numbers, the news
  release only for its wording.
- **Vaca Michilena and Cano-Moreno 2026:** comfort (ISO 2631-1), not stability. Speed and
  roughness explain 98.9% of the comfort response and tyre stiffness 1.1%; best case was
  pneumatic tyres with slightly higher front pressure (+2.9 to 4.35 psi). The abstract says
  nothing about wheel diameter; the claim in `notes.md` that it says larger wheels improve
  stability is **[to verify]** in the full text.
- **Ventura et al. 2024** is the "Italy 2023" paper in earlier notes: published 2024
  (volume 16), online 2023.

### Mentioned in notes.md, not yet found **[to verify]**
- Swifty pothole tests (16 in vs 8 in scooter; 72 mm pothole). No public source found on
  2026-10-07. Swifty sells large-wheel scooters, so treat as commercial evidence.
- Scooter patents on front-wheel angle of attack. No patent number recorded; find one on
  Google Patents or Espacenet before citing.
- Mazdak Ghajari's current academic title (the 2022 release says "Dr"; his Imperial
  profile was not reachable).

---

### Sensor validity and walking detection (`SENSOR_VALIDITY.md`; checked 2026-10-07)

DOIs, volumes and pages checked against Crossref; content checked against abstracts or
publisher pages, as noted. Each is cited only for what is noted here.

| Key | Used for | What was checked |
|-----|----------|------------------|
| kwapisz2011 | Prior work: phone accelerometers distinguish walking from other activities | Crossref metadata |
| reddy2010 | Prior work: phone GPS + accelerometer distinguish walking, biking, motorised transport (decision tree + HMM, 93.6% on 16 people) | Crossref metadata; abstract summary |
| mizell2003 | Orientation-independent vertical acceleration by projecting onto the gravity direction (Mizell estimates gravity as a window mean; here iOS supplies it) | Crossref metadata; method as described in later citing work, **paper itself not read** |
| moenilssen2004 | Step regularity and cadence from the autocorrelation of trunk acceleration | Crossref metadata; abstract |
| pachi2005 | Typical walking step frequency (mean 1.8 Hz on footbridges, 2.0 Hz on shopping floors) and step length (mean 0.75 m men, 0.67 m women), 800 measurements | Publisher page and search summaries; **page numbers not verified** |
| welch1967 | Welch power-spectrum method | Crossref metadata |
| butterworth1930 | Butterworth filter | Journal index and secondary sources (no DOI) |
| merry2019 | Smartphone (iPhone 6) horizontal position accuracy in an urban area, 7–13 m on average | Crossref metadata; abstract |
| witte2004 | GPS speed accuracy (dedicated receiver on a bicycle, not a phone): 45% of values within 0.2 m/s, a further 19% within 0.4 m/s; errors grow on curved paths through a tendency to underestimate speed | Crossref metadata; full abstract (Europe PMC) |
| apple_cmacceleration | iOS raw acceleration is reported in G (1 G = 9.81 m/s²) | Apple Developer Documentation |

Butterworth, S. (1930) 'On the theory of filter amplifiers', *Experimental Wireless and
the Wireless Engineer*, 7, pp. 536–541.

Kwapisz, J.R., Weiss, G.M. and Moore, S.A. (2011) 'Activity recognition using cell phone
accelerometers', *ACM SIGKDD Explorations Newsletter*, 12(2), pp. 74–82.
doi:10.1145/1964897.1964918.

Merry, K. and Bettinger, P. (2019) 'Smartphone GPS accuracy study in an urban
environment', *PLOS ONE*, 14(7), e0219890. doi:10.1371/journal.pone.0219890.

Mizell, D. (2003) 'Using gravity to estimate accelerometer orientation', in *Proceedings
of the Seventh IEEE International Symposium on Wearable Computers (ISWC 2003)*,
pp. 252–253. doi:10.1109/ISWC.2003.1241424.

Moe-Nilssen, R. and Helbostad, J.L. (2004) 'Estimation of gait cycle characteristics by
trunk accelerometry', *Journal of Biomechanics*, 37(1), pp. 121–126.
doi:10.1016/S0021-9290(03)00233-1.

Pachi, A. and Ji, T. (2005) 'Frequency and velocity of people walking', *The Structural
Engineer*, 83(3). **[to verify: page numbers]**

Reddy, S., Mun, M., Burke, J., Estrin, D., Hansen, M. and Srivastava, M. (2010) 'Using
mobile phones to determine transportation modes', *ACM Transactions on Sensor Networks*,
6(2), pp. 1–27. doi:10.1145/1689239.1689243.

Welch, P.D. (1967) 'The use of fast Fourier transform for the estimation of power
spectra: a method based on time averaging over short, modified periodograms', *IEEE
Transactions on Audio and Electroacoustics*, 15(2), pp. 70–73. doi:10.1109/TAU.1967.1161901.

Witte, T.H. and Wilson, A.M. (2004) 'Accuracy of non-differential GPS for the
determination of speed over ground', *Journal of Biomechanics*, 37(12), pp. 1891–1898.
doi:10.1016/j.jbiomech.2004.02.031.

Apple Inc. (n.d.) *CMAcceleration*, Apple Developer Documentation. Available at:
https://developer.apple.com/documentation/coremotion/cmacceleration (accessed 7 October 2026).

### Literature search for introduction and discussion (2026-10-08)

Metadata from Crossref/OpenAlex; content checked against each abstract (Semantic
Scholar, OpenAlex or PubMed). Cite each only for the "use for" column.

| Key | Use for | Checked against | Do **not** use for |
|-----|---------|-----------------|--------------------|
| paudel2025 | Experimental tests of 8 small-wheeled e-scooters/e-bikes: small-wheel compact devices less stable than larger-wheeled ones; risks in obstacle interaction; recommends minimum 14 in wheels, front suspension, turn lights, mirrors | Abstract and highlights (OpenAlex) | Pothole-specific results (not reported in the abstract); rental scooters |
| nathania2026 | Systematic review (PRISMA, Haddon matrix): falls are the most common e-scooter accident type and are multifactorial (human, vehicle, environment) | Abstract | Any percentage for road-surface causes (none in abstract) |
| fournier2023 | Multibody model of e-scooter falls from wheel-curb collision, compared with a crash test; 162 scenarios; high head-injury risk | Abstract | Potholes |
| leoni2022 | Instrumented tests of 7 e-scooters in Milan; stability and comfort metrics mapped to vehicle specifications | Abstract | Wheel-size effects (not stated in abstract) |
| eriksson2008 | Pothole Patrol: vehicle-mounted accelerometers and GPS detect potholes; >90% of reported spots had anomalies | Abstract | Phones or scooters (used dedicated in-car sensors on taxis) |
| zang2018 | Bicycle-mounted smartphone GPS + accelerometer: roughness (IRI) correlated with professional instruments; pothole/hump recognition | Abstract | E-scooters |
| cicchino2021 | 105 injured e-scooter riders, Washington DC, 2019: injuries on the road about twice as likely to be AIS 2+ as elsewhere (RR 1.96) | PubMed abstract | **"67% of falls due to bad roads"**: a search-engine summary attached this to the study; it is **not** in the abstract |
| anke2025 | Survey and focus groups of regular riders: infrastructure hazards are among the hazards riders perceive; actions for maintenance and vehicle design | Abstract | Measured exposure |
| lee2024fall | IMU-based pre-impact fall detection while riding e-scooters (20 participants, worn IMU) | Abstract | Phone on handlebar |
| dft2026factsheet | GB 2025: 10 e-scooter riders killed, about 410 seriously injured; 384 of 1,377 e-scooter collisions involved no other vehicle (28%); e-scooter casualties among the most under-reported | GOV.UK factsheet (published 30 July 2026) | Road-surface contributory factors (not in the factsheet) |
| roadcc2022voiager5 | Voiager 5 UK launch (Liverpool, Bristol, Bath, June 2022); "larger front wheel, increased tread depth and greater shock absorption" | Article text | Wheel size in inches (not given) |
| tfl2023launch | London Phase 2 launched 25 Sept 2023 with Dott, Lime and Voi; strict safety requirements | Press release (search summary + earlier TfL sources) | Which model Voi runs in London (not stated) |

Considered and not used: Salgado et al. 2024, *Legal Medicine* (car-to-scooter collisions,
not falls); Chen et al. 2025 (gaze behaviour); Swifty Scooters' pothole tests (8 in vs
16 in wheels, 36/54/72 mm deep; found on the company blog, commercial and not peer
reviewed: mention only as industry material, if at all).

## 2. Software

| Software | Version used | Used in |
|----------|--------------|---------|
| Python | 3.11.9 | All scripts |
| NumPy | 2.3.4 | All scripts |
| pandas | 2.3.3 | All analysis scripts |
| SciPy | 1.17.1 | `find_peaks` (impact detection, step peaks), `linkage`/`fcluster` (hotspots), `spearmanr`, `welch`, `butter`/`sosfiltfilt` (walking detection) |
| Matplotlib | 3.11.2 | All figures; `FuncAnimation` for the simulation animations |
| Pillow | 12.3.0 | GIF encoding of the animations (Matplotlib `PillowWriter`) |
| MiKTeX / LuaHBTeX | 25.12 / 1.24.0 | Typesetting the paper (`paper/main.tex`, built by `paper/build.py`) |
| biblatex / Biber | 3.21 / 2.21 | Paper bibliography (author-year) from `references.bib` |
| qrcode (LaTeX package) | 1.51 | QR codes in Table C1 (Street View links for printed copies) |
| Pandoc | 3.12 | One-time conversion of the Markdown drafts to LaTeX (`scripts/md_to_latex.py`) |
| PyMuPDF | 1.28.2 | Rendering PDF pages to check layout; reading link targets |
| zxing-cpp | 3.1.1 | Decoding the printed QR codes to verify each one (all 29 correct at 150 dpi) |
| MuJoCo | 3.14.0 | Dynamics simulation |
| folium (with branca) | 0.20.0 (0.8.2) | Impact and FixMyStreet maps |
| Leaflet | 1.9.3 (bundled by folium); 1.9.4 (Street View page, from cdnjs) | All HTML maps |
| Sensor Logger (iOS) | 1.67.1 on iOS 26.6.2, iPhone 11 Pro Max | Data recording |
| Apple Core Motion | iOS 26.6.2 | Source of the gravity / user-acceleration split |

Agafonkin, V. and Leaflet contributors (2023) *Leaflet: an open-source JavaScript library
for mobile-friendly interactive maps*, version 1.9.4. Available at: https://leafletjs.com

Apple Inc. (n.d.) *CMDeviceMotion*, Apple Developer Documentation (properties `gravity` and
`userAcceleration`). Available at: https://developer.apple.com/documentation/coremotion/cmdevicemotion

Choi, K.T.H. (2026) *Sensor Logger*, version 1.67.1 (iOS) [mobile app]. Logger Labs Ltd.
Zenodo. doi:10.5281/zenodo.20277979. Available at: https://www.tszheichoi.com/sensorlogger
(Checked 2026-10-07: citation, DOI and author from the developer's official CITATION.cff
and "How to Cite" section in the Awesome Sensor Logger repository,
https://github.com/tszheichoi/awesome-sensor-logger; App Store seller "Logger Labs LTD",
copyright "Tsz Hei Choi", https://apps.apple.com/gb/app/sensor-logger/id1531582925.
The developer asks papers to state the app version and platform in the methods: iOS,
1.67.1, iPhone 11 Pro Max, iOS 26.6.2.)

Clark, A. et al. (2026) *Pillow (PIL fork)*, version 12.3.0. Available at:
https://python-pillow.org

Harris, C.R., Millman, K.J., van der Walt, S.J. et al. (2020) 'Array programming with
NumPy', *Nature*, 585(7825), pp. 357–362. doi:10.1038/s41586-020-2649-2.

Hunter, J.D. (2007) 'Matplotlib: a 2D graphics environment', *Computing in Science &
Engineering*, 9(3), pp. 90–95. doi:10.1109/MCSE.2007.55.

McKinney, W. (2010) 'Data structures for statistical computing in Python', in *Proceedings
of the 9th Python in Science Conference*, pp. 56–61. doi:10.25080/Majora-92bf1922-00a.

The pandas development team (2025) *pandas-dev/pandas: Pandas*, version 2.3.3. Zenodo.
doi:10.5281/zenodo.3509134.

Python Software Foundation (2024) *Python*, version 3.11.9. Available at:
https://www.python.org

python-visualization (2025) *folium*, version 0.20.0. Available at:
https://python-visualization.github.io/folium/

Todorov, E., Erez, T. and Tassa, Y. (2012) 'MuJoCo: a physics engine for model-based
control', in *2012 IEEE/RSJ International Conference on Intelligent Robots and Systems*,
pp. 5026–5033. doi:10.1109/IROS.2012.6386109.

Google DeepMind (2026) *MuJoCo*, version 3.14.0. Available at: https://mujoco.org

Virtanen, P., Gommers, R., Oliphant, T.E. et al. (2020) 'SciPy 1.0: fundamental algorithms
for scientific computing in Python', *Nature Methods*, 17(3), pp. 261–272.
doi:10.1038/s41592-019-0686-2.

Tools considered but not used (no citation needed unless named in the paper): Project
Chrono/PyChrono (https://projectchrono.org), PyBullet (https://pybullet.org), OpenSCAD
(https://openscad.org), Blender (https://www.blender.org).

---

## 3. Data and map services

| Source | Used for | Licence / terms |
|--------|----------|-----------------|
| OpenStreetMap via Overpass API | Study road geometry (`data/osm_study_roads.json`); paper map background (`data/osm_paper_basemap.json`, downloaded 2026-10-08) | ODbL; attribute "© OpenStreetMap contributors" (shown on the paper map and in its caption) |
| Esri World Light Gray Canvas (Base + Reference) | Map background tiles | Esri terms; attribution shown on maps |
| FixMyStreet (mySociety) | Road-surface reports (`data/fixmystreet/reports_<recording>.csv`, one per ride's area) | mySociety terms; cite as below |
| Google Maps URLs (Street View panorama and map links) | Links in `streetview_check.html` and `spot_links` (`SPOT_CHECK.md`); no API key ("You don't need a Google API key to use Maps URLs"; checked 2026-10-08); no images downloaded | Google Maps terms |
| Mapillary | Alternative imagery links in both spot lists | Images CC BY-SA 4.0 (Mapillary help centre; licence changed from CC BY-NC on 29 April 2014) |
| KartaView | Imagery coverage check, 2026-10-08: 5 photos near spot P1, from 2017 and 2021 | CC BY-SA 4.0 |
| Panoramax | Imagery coverage check, 2026-10-08: no photos in the study area | Open licences per instance |

Esri (n.d.) *World Light Gray Base* and *World Light Gray Reference* [map services]. Sources:
Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community. Available at:
https://doc.arcgis.com/en/data-appliance/2022/maps/world-light-gray-base.htm

Google (n.d.) *Maps URLs*, Google Maps Platform documentation. Available at:
https://developers.google.com/maps/documentation/urls/get-started

Mapillary (n.d.) *Mapillary* [street-level imagery, CC BY-SA 4.0]. Available at: https://www.mapillary.com

KartaView (n.d.) *KartaView* [open street-level imagery, formerly OpenStreetCam]. Available at:
https://kartaview.org (API queried 2026-10-08)

Panoramax (n.d.) *Panoramax* [open street-level imagery]. Available at: https://panoramax.fr
(meta-catalogue API queried 2026-10-08)

mySociety (2026) *FixMyStreet* [online reporting service]. Data downloaded 2026-10-03
(ride 1 area) and 2026-10-08 (ride 2 and ride 3 areas).
Available at: https://www.fixmystreet.com

Olbricht, R. (n.d.) *Overpass API*. Endpoints used: https://overpass-api.de/api/interpreter
and https://overpass.kumi.systems/api/interpreter. Documentation:
https://wiki.openstreetmap.org/wiki/Overpass_API

OpenStreetMap contributors (2026) *OpenStreetMap* [database], extract retrieved via the
Overpass API on 3 October 2026. Licensed under the Open Database License (ODbL). Available at:
https://www.openstreetmap.org/copyright

---

## 4. Vehicle, operator and policy sources (Parts A–C)

Attwood, J. (2022) 'Voi launches new Voiager 5 rental e-scooter with upgraded safety tech',
*Move Electric*, 20 March. Available at:
https://www.moveelectric.com/e-scooters/voi-launches-new-voiager-5-rental-e-scooter-upgraded-safety-tech

Department for Transport (2024) *E-scooter trials: guidance for local areas and rental
operators*, updated 17 January. Available at:
https://www.gov.uk/government/publications/e-scooter-trials-guidance-for-local-areas-and-rental-operators/e-scooter-trials-guidance-for-local-areas-and-rental-operators
Checked 2026-10-10 (full page text): no minimum wheel size; "wheel" appears only in the
mudguard-brake rules and the stability-test procedure; no "diameter" or "inch". Tyres:
"pneumatic or non-pneumatic", "suitable having regard to the use". Key `dft2024guidance`.

UK Government (2020) *The Electric Scooter Trials and Use of Powered Transporters Order 2020*
(SI 2020/663). Available at: https://www.legislation.gov.uk/uksi/2020/663. Checked 2026-10-10
(current version): the definition of "electric scooter" requires two in-line wheels, motor
<= 500 W, mass <= 55 kg, design speed <= 15.5 mph, handlebars linked to the steered wheel; no
wheel size. Key `si2020_663`.

PACTS (2022) *The safety of private e-scooters in the UK* (report, March 2022).
**[to verify: PDF not found; known only from news coverage]** Reportedly recommends, for
private e-scooters if legalised, a minimum front wheel of 12 in (30.5 cm) and rear of 10 in
(25.5 cm), so that scooters are easier to control on poor road surfaces. Coverage: Fleet News
21 March 2022 (https://www.fleetnews.co.uk/news/car-industry-news/2022/03/21/pacts-calls-for-tougher-e-scooter-rules-as-15-riders-killed);
Boyes Turner (https://www.boyesturner.com/insights/new-recommendations-e-scooter-regulation-and-technical-standards);
Road Safety GB, 12 April 2022 (https://roadsafetygb.org.uk/?p=17943). Not a rule for rental
trials. Check the report on the PACTS website before citing; not in references.bib yet.

Department for Transport (2026) *E-scooter trials: guidance for users*, updated 7 July.
Available at: https://www.gov.uk/guidance/e-scooter-trials-guidance-for-users

Electrive (2025) 'Voi presents new electric scooter and two e-bikes', *electrive.com*,
18 March. Available at:
https://www.electrive.com/2025/03/18/voi-presents-new-electric-scooter-and-two-e-bikes/

Morley, R. (2024) 'Voi's new e-bike offers automatic gear changes and there's a new
e-scooter too', *ebiketips (road.cc)*, 10 April. Available at:
https://ebiketips.road.cc/content/news/vois-new-e-bike-offers-automatic-gear-changes-and-theres-a-new-e-scooter-too-5267

Transport for London (2023) 'TfL awards contracts to Dott, Lime and Voi to run the next
phase of London's rental e-scooter trial' [press release], July. Available at:
https://tfl.gov.uk/info-for/media/press-releases/2023/july/tfl-awards-contracts-to-dott-lime-and-voi-to-run-the-next-phase-of-london-s-rental-e-scooter-trial

VNV Global AB (2023) 'VNV Global's portfolio company Voi wins e-scooter tender in London'
[press release], 5 July. Available at:
https://storage.mfn.se/5e105080-042c-419c-83f0-a36340ad0e0e/vnv-globals-portfolio-company-voi-wins-e-scooter-tender-in-london.pdf

Future Transport News (n.d.) [Voiager 5 launch article, cited in DOCUMENTATION.md 6.1]
**[to verify: title and URL not recorded]**

Voi Technology (2026a) Customer support, personal communication to the author, 3 October
2026 (support chat). Confirmed that the scooter ridden for recording 1 (3 October 2026,
vehicle ID SZ22) was a Voiager 5. Key `voi2026support_rec01`.

Voi Technology (2026b) Customer support, personal communication to the author, 8 October
2026 (support chat). Confirmed that the scooters ridden for recordings 2 and 3 (7 October
2026, vehicle IDs UPAR and BTLZ) were Voiager 5. Key `voi2026support_rec0203`.

Both: **model only**; wheel sizes were not part of the confirmations. The records (chat
screenshots) are kept by the author, not published; ask Voi before quoting them.

Author's own observation (2026-10-09, not a citation key): photographs of the tyre sidewalls
of a parked Voiager 5 in Oxford, `tyre-images/IMG_8174-8183.jpeg` (front) and
`tyre-images/rear.jpeg` (rear). Front 60/55-8.5 (nominal 282 mm, 11.1 in), rear 60/55-7.5
(257 mm, 10.1 in). Shown as paper Figure 1 (`scripts/tyre_figure.py`). Contradicts the 10 in
reported by Levy and Alsalkini 2023 for the front wheel; those are now cited only for the
10/10 reference configuration. The photographed scooter is a Voiager 5, the model ridden (verified by the author, 2026-10-10).

Levy Electric (n.d.) *Voiager 5* [fleet specification]. Available at:
https://fleets.levyelectric.com/vehicles/voi-voiager-5 (aggregator; secondary)

Oxfordshire County Council (n.d.) *E-scooter trial in Oxford*. Available at:
https://www.oxfordshire.gov.uk/residents/roads-and-transport/connecting-oxfordshire/active-travel/e-scooter-trial

Oxfordshire County Council (2021) 'New electric scooter hire scheme for Oxford launched
with Voi'. Available at: https://news.oxfordshire.gov.uk/new-escooter-launch/
[search snippet only]

Startups Magazine (2024) 'Voi unveils new scooter: the Voiager 7', 12 April. Available at:
https://startupsmagazine.co.uk/article-voi-unveils-new-scooter-voiager-7

Transport for London (2022) *Electric Scooters (E-Scooters) Rental Trial 2 in London*, Find
a Tender notice 2022/S 000-033381, 24 November. Available at:
https://www.find-tender.service.gov.uk/Notice/033381-2022

Voi Technology AB (2026) 'Voi expands its vehicle family with three new models in 2026'
[press release]. Available at:
https://storage.mfn.se/d6c2e21d-02ff-400d-8d7a-ca158fbdeb4c/voi-expands-its-vehicle-family-with-three-new-models-in-2026.pdf

Zag Daily (2022) 'Voi releases next-generation e-scooter the Voiager 5', 15 March.
Available at: https://zagdaily.com/tech/voi-releases-next-generation-e-scooter-the-voiager-5/

**Road humps (bump simulations, checked 2026-10-07):**

Department of Transport (1996a) *75mm High Road Humps*, Traffic Advisory Leaflet 2/96,
April. Available at: https://tsrgd.co.uk/pdf/tal/1996/tal-2-96.pdf (states the round-top
humps studied were "a standard 3.7m long"; mirror of the DfT leaflet)

Department of Transport (1996b) *Highways (Road Humps) Regulations 1996*, Traffic Advisory
Leaflet 7/96, June. Available at: https://tsrgd.co.uk/pdf/tal/1996/tal-7-96.pdf (humps
"should be able to be negotiated by both cyclist and motorcyclists quite safely"; humps on
strategic routes normally not above 75 mm; cushion side ramps not steeper than 1:4)

*The Highways (Road Humps) Regulations 1999* (SI 1999/1025), regulation 4. Available at:
https://www.legislation.gov.uk/uksi/1999/1025/regulation/4/made (length >= 900 mm along
the carriageway; highest point 25-100 mm; no vertical face above 6 mm)

---

## 5. Attribution checklist for the paper
- Methods: name and cite Python, NumPy, pandas, SciPy, Matplotlib, MuJoCo (paper +
  version), folium/Leaflet, Pillow, Sensor Logger (with app version and phone model).
- Methods: say that acceleration was Core Motion's `userAcceleration` (gravity removed)
  and cite Apple's documentation.
- Every map figure: "Basemap: Esri, HERE, Garmin, © OpenStreetMap contributors" and
  "Road data © OpenStreetMap contributors (ODbL)". The HTML maps already show this.
- FixMyStreet: cite mySociety and give the download date and the 365-day window.
- Data/code availability statement: cite the repository (and archive it, e.g. Zenodo,
  for a DOI) and state that raw ride coordinates are withheld or trimmed.
- Check your university's required style (Harvard variants differ; Oxford departments
  often accept author-date or numeric). `references.bib` works with either in LaTeX.
