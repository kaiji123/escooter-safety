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

## 2. Software

| Software | Version used | Used in |
|----------|--------------|---------|
| Python | 3.11.9 | All scripts |
| NumPy | 2.3.4 | All scripts |
| pandas | 2.3.3 | All analysis scripts |
| SciPy | 1.17.1 | `find_peaks` (impact detection), `linkage`/`fcluster` (hotspots), `spearmanr` |
| Matplotlib | 3.11.2 | All figures; `FuncAnimation` for the simulation animations |
| Pillow | 12.3.0 | GIF encoding of the animations (Matplotlib `PillowWriter`) |
| MuJoCo | 3.14.0 | Dynamics simulation |
| folium (with branca) | 0.20.0 (0.8.2) | Impact and FixMyStreet maps |
| Leaflet | 1.9.3 (bundled by folium); 1.9.4 (Street View page, from cdnjs) | All HTML maps |
| Sensor Logger (iOS) | 1.67.1 on iOS 26.6.2, iPhone 11 Pro Max | Data recording |
| Apple Core Motion | iOS 26.6.2 | Source of the gravity / user-acceleration split |

Agafonkin, V. and Leaflet contributors (2023) *Leaflet: an open-source JavaScript library
for mobile-friendly interactive maps*, version 1.9.4. Available at: https://leafletjs.com

Apple Inc. (n.d.) *CMDeviceMotion*, Apple Developer Documentation (properties `gravity` and
`userAcceleration`). Available at: https://developer.apple.com/documentation/coremotion/cmdevicemotion

Choi, T.H. (2026) *Sensor Logger*, version 1.67.1 [mobile app]. Apple App Store. Available
at: https://apps.apple.com/app/id1531582925 (developer listed as "Choi Tsz Hei"; check the
preferred citation on the app's website **[to verify]**).

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
| OpenStreetMap via Overpass API | Study road geometry (`data/osm_study_roads.json`) | ODbL; attribute "© OpenStreetMap contributors" |
| Esri World Light Gray Canvas (Base + Reference) | Map background tiles | Esri terms; attribution shown on maps |
| FixMyStreet (mySociety) | Road-surface reports (`data/fixmystreet/reports.csv`) | mySociety terms; cite as below |
| Google Maps URLs (Street View panorama links) | Links in `streetview_check.html`; no images downloaded | Google Maps terms |
| Mapillary | Alternative imagery links | Mapillary terms |

Esri (n.d.) *World Light Gray Base* and *World Light Gray Reference* [map services]. Sources:
Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community. Available at:
https://doc.arcgis.com/en/data-appliance/2022/maps/world-light-gray-base.htm

Google (n.d.) *Maps URLs*, Google Maps Platform documentation. Available at:
https://developers.google.com/maps/documentation/urls/get-started

Mapillary (n.d.) *Mapillary* [street-level imagery]. Available at: https://www.mapillary.com

mySociety (2026) *FixMyStreet* [online reporting service]. Data downloaded 2026-10-03.
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

Department for Transport (2026) *E-scooter trials: guidance for users*, updated 7 July.
Available at: https://www.gov.uk/guidance/e-scooter-trials-guidance-for-users

Future Transport News (n.d.) [Voiager 5 launch article, cited in DOCUMENTATION.md 6.1]
**[to verify: title and URL not recorded]**

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
