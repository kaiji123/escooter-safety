# Visual check of impact spots in street-level imagery

Method for checking the measured impact spots against street-level imagery (Google
Street View, Google Maps, Mapillary). Code: `scripts/spot_links.py`. Outputs:
`outputs/combined/spot_links.csv` (dataset to fill in) and `spot_links.html` (clickable
list). Citations use Pandoc keys from `references.bib`.

Status (2026-10-08): method and dataset ready; **no spot checked yet**. The recording
rules in section 5 were fixed before any spot was looked at.

---

## 1. Purpose and what it can show

The phone measures *that* the handlebar was jolted at a place, not *what* caused it. A
look at street-level imagery can show whether a visible surface feature (pothole, crack,
patch, cover, kerb, hump) is present near the measured spot. This supports, or fails to
support, reading the impacts as road-surface defects.

It cannot show:
- that the feature was present **on the ride day**: imagery is taken on other dates,
  before or after the rides;
- how **deep** a defect is: imagery shows the surface, not depth;
- that **no** defect exists: "nothing visible" can also mean low resolution, shadows,
  parked cars or a repair since the image date.

## 2. Spots

- **Source:** all impacts from all recordings (`outputs/combined/impacts_all.csv`, made
  by `scripts/combined_outputs.py`). Impacts are |vertical acceleration| ≥ 1.0 g at
  ≥ 7 km/h (analyst choices; see `DOCUMENTATION.md` section 3).
- **Clustering:** single-linkage clustering [@sibson1973] at 30 m, the same radius as
  the per-recording hotspots, applied to the pooled impacts. Each cluster is one spot,
  located at the mean position of its impacts.
- **Tiers** (ranking for checking order, not a severity scale):

| Tier | Definition | Spots (2026-10-08) |
|---|---|---|
| 1 | Impacts from two or more separate recordings | 10 |
| 2 | Two or more impacts, all from one recording | 10 |
| 3 | A single impact | 13 |

  Within a tier, spots are ordered by number of recordings, number of impacts, then
  peak g. A spot hit on separate rides is the strongest candidate for a fixed surface
  feature. The rides share one rider, phone and route, so repeated hits are repeated
  measurements of one place, not independent confirmations.
- **Direction of travel:** the bearing of the GPS track between 1 s before and 1 s after
  the first impact of the earliest recording that hit the spot (`heading_at()` in
  `scripts/streetview_page.py`). Where rides crossed a spot in different directions,
  this is the direction of the first; the viewer can turn the view.

## 3. Links

Every spot gets three links, built with documented URL formats; nothing is downloaded,
stored or scraped:

| Link | Format | Settings |
|---|---|---|
| Google Street View | Google Maps URLs, `map_action=pano` [@googlemapsurls] | `viewpoint` = spot; `heading` = direction of travel; `pitch` = −25° (tilted down towards the road); `fov` = 80° |
| Google Maps pin | Google Maps URLs, `search` with `query=lat,lon` [@googlemapsurls] | For spots without Street View |
| Mapillary | `mapillary.com/app/?lat=…&lng=…&z=19` [@mapillary] | Open, crowd-sourced imagery (CC BY-SA 4.0) |

Google's documentation states "You don't need a Google API key to use Maps URLs". Pitch
may range from −90° to 90° (default 0) and field of view from 10° to 100° (default 90°)
[@googlemapsurls]. The −25° pitch and 80° field of view are analyst choices that put the
road surface ahead in view.

Google's imagery is only viewed through these links, as a person would view it in the
browser. **No Street View images go in the paper**: Google's geo guidelines (checked
2026-10-08) state "Street View imagery may not be used for any print purposes" and "You may
not screenshot Street View imagery ... for any purpose". The paper reports the recorded
findings (categories, imagery dates, counts per tier); the links go in the supplementary
dataset. If an image is wanted: Mapillary photos (CC BY-SA 4.0, credit the contributor) or
the rider's own photos (taken while stopped; no faces or number plates). Downloading Street View images or analysing them automatically would need the
paid API and is restricted by Google's terms, so neither is done.

## 4. Open imagery availability (checked 2026-10-08)

| Source | Result in the study area | Use |
|---|---|---|
| Panoramax [@panoramax] (open, OpenStreetMap community) | No photos in the study bounding box (API search) | None |
| KartaView [@kartaview] (open, CC BY-SA) | 5 photos within 300 m of spot P1, taken 2017-08-15 and 2021-04-06 | Too old to show the current surface |
| Mapillary [@mapillary] | Not checked: the API needs a free access token | Links included; coverage and dates unknown |
| Google Street View | Not queried (no API used); imagery dates are shown in the viewer | Main source, viewed by hand |

## 5. Recording rules (fixed before checking)

For every spot, in `spot_links.csv`:

1. **`imagery_date`:** the capture month and year shown in Street View (or Mapillary).
   With several dates, use the newest, and note older ones if they differ.
2. **`what_visible`:** one or more of these labels, exactly as written, separated by
   `;`:
   `Pothole` · `Crack / broken surface` · `Patched or repaired surface` ·
   `Drain or manhole cover` · `Kerb / dropped kerb` · `Speed hump / raised table` ·
   `Nothing visible` · `No imagery here`
   These are the same categories as the earlier recording-1 checklist
   (`streetview_page.py`), so the two can be combined.
3. **Search area:** count a feature only if it lies **within about 15 m of the pin**
   along the road, in or next to the part of the carriageway or cycle lane a scooter
   would use. The 15 m is an analyst choice, covering the phone's median reported GPS
   accuracy of 11–14 m (`SENSOR_VALIDITY.md` section 4.1).
4. **`notes`:** anything that affects interpretation (e.g. "parked cars hide the
   surface", "resurfaced in newer image", "feature 20 m away, outside the area").
5. **Do not revise** the category list or the 15 m rule after starting. If a new kind
   of feature appears, record it in `notes`.

## 6. Reporting

- Per tier: the number of spots in each `what_visible` category, and how many images
  predate or postdate the rides (rides on 2026-10-03 and 2026-10-07).
- Main figure of interest: the share of tier-1 spots with a visible surface feature,
  compared with tier 3. This is descriptive: there is no control set of spots without
  impacts. A possible extension is to check an equal number of randomly chosen points
  on the ridden route without impacts, using the same rules, as a baseline.
- Reported as "a surface feature was visible near N of M spots in imagery dated …", not
  as "the defects were confirmed".

## 7. Limitations

- One person checks, and knows each spot's peak g and tier while checking (the list
  shows them). A second, independent checker for some spots, ideally without seeing
  peak g, would allow an agreement measure.
- Imagery dates differ from the ride dates, and the surface may have changed in between.
- GPS error (about 11–14 m reported) means the pin may be off the true impact point; the
  15 m search area is a compromise between missing the feature and counting an
  unrelated one.
- Tiers depend on the analyst-chosen impact threshold and the 30 m clustering radius.

## 8. In the paper

Table C1 (Appendix C, landscape pages) is generated by `scripts/paper_part_a.py`
(`spot_table_tex`) into `paper/sections/appendix_spot_links.tex`, styled after
`spot_links.html`: one block per tier, clickable Street View / Map / Mapillary links,
FixMyStreet status, location and events. Spots in the hidden first or last 200 m of a
route (currently P9, P16, P30, P31) are named in the caption but not listed, matching the
map's privacy trimming; the full list is the supplementary `spot_links.csv`.
For printed copies, every row also has a QR code (13 mm, error-correction level L)
encoding its Street View link; all 29 were decoded and checked against the links
(zxing-cpp, pages rendered at 150 dpi), and the coordinates are printed as a fallback. No Street
View images are reproduced (section 3).

## 9. Reproduce

```
python scripts/combined_outputs.py     # pooled impacts and hotspots
python scripts/spot_links.py           # outputs/combined/spot_links.csv and .html
```

Rerunning `spot_links.py` keeps any `imagery_date`, `what_visible` and `notes` already
filled in, matched on the spot location rounded to 4 decimal places (about 10 m).

The earlier recording-1 checklist (`outputs/recordings/2026-10-03_1830_rec01/streetview_check.html`,
25 spots with FixMyStreet status and an in-browser form) uses the same link format and
categories. It is kept for recording 1; new checks use `spot_links`.
