"""
Dataset of map links for every impact spot over all recordings, for checking spots by
eye in Google Street View, Google Maps or Mapillary.

Spots come from the pooled hotspots of combined_outputs.py (single linkage, 30 m):
    tier 1  hit on two or more separate recordings (strongest candidates)
    tier 2  two or more impacts, all from one recording
    tier 3  single impacts
sorted by tier, then number of recordings, impacts and peak g.

Links use Google's documented Maps URLs (no API key; they open Google Maps as if
navigated by hand, nothing is downloaded): Street View facing the direction of travel
at the spot and tilted towards the road, a plain map pin for spots without Street View,
and Mapillary (open, CC BY-SA imagery). Street View images carry their own capture date,
which can be before or after the ride; record it.

Writes outputs/combined/spot_links.csv (with empty columns to fill in: imagery_date,
what_visible, notes) and outputs/combined/spot_links.html (clickable list).
Run after combined_outputs.py.

Usage
    python scripts/spot_links.py
"""

import html
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import impact_map as im                         # noqa: E402
import streetview_page as sv                    # noqa: E402  (heading_at, links)

COMBINED = Path("outputs/combined")
RAW = Path("data/raw")
TIER_TEXT = {1: "Hit on 2+ separate rides", 2: "2+ impacts on one ride", 3: "Single impact"}


def fms_fields(g):
    """Nearest recent FixMyStreet road-surface report to any impact of the spot (from
    each recording's fms_compare.py match; recent = within 365 days before that ride)."""
    if "nearest_report_m" not in g or g["nearest_report_m"].isna().all():
        return {"fms_recent_within_25m": "", "fms_nearest_recent_m": "", "fms_state": "", "fms_url": ""}
    k = g["nearest_report_m"].idxmin()
    return {"fms_recent_within_25m": bool(g["fms_recent_report_within_25m"].fillna(False).any()),
            "fms_nearest_recent_m": round(float(g.loc[k, "nearest_report_m"]), 1),
            "fms_state": g.loc[k, "nearest_report_state"], "fms_url": g.loc[k, "nearest_report_url"]}


def build_spots():
    imps = pd.read_csv(COMBINED / "impacts_all.csv")
    rough = {rec: im.analyse(RAW / rec)["rough"] for rec in imps["recording"].unique()}
    imps["heading"] = [sv.heading_at(r.seconds_elapsed, rough[r.recording]) for r in imps.itertuples()]
    rows = []
    for h, g in imps.groupby("hotspot_all"):
        n_rec = g["recording"].nunique()
        tier = 1 if n_rec >= 2 else 2 if len(g) >= 2 else 3
        first = g.sort_values(["recording", "seconds_elapsed"]).iloc[0]   # earliest ride's first hit
        rows.append({"tier": tier, "rides_hitting": n_rec, "impacts": len(g),
                     "max_g": round(g["peak_abs_g"].max(), 2), "median_g": round(g["peak_abs_g"].median(), 2),
                     "road": g["road"].mode().iloc[0], "lat": round(g["lat"].mean(), 6),
                     "lon": round(g["lon"].mean(), 6), "heading_deg": round(first["heading"]),
                     "recordings": ", ".join(sorted(g["recording"].unique())),
                     "first_seen_local": g["local_time"].min(),
                     "events": "; ".join(f"{r.recording[-5:]}#{r.event_id}" for r in g.itertuples()),
                     **fms_fields(g)})
    spots = pd.DataFrame(rows).sort_values(["tier", "rides_hitting", "impacts", "max_g"],
                                           ascending=[True, False, False, False]).reset_index(drop=True)
    spots.insert(0, "spot", [f"P{i}" for i in range(1, len(spots) + 1)])
    urls = [sv.links({"lat": r.lat, "lon": r.lon, "heading": r.heading_deg}) for r in spots.itertuples()]
    spots["google_streetview_url"] = [u[0] for u in urls]
    spots["google_maps_url"] = [u[1] for u in urls]
    spots["mapillary_url"] = [u[2] for u in urls]
    for c in ("imagery_date", "what_visible", "notes"):
        spots[c] = ""
    return spots


def fms_cell(r):
    if r.fms_nearest_recent_m in ("", None) or pd.isna(r.fms_nearest_recent_m):
        return '<span class="muted">not compared</span>'
    d = float(r.fms_nearest_recent_m)
    if d == float("inf"):
        return '<span class="muted">none in area</span>'
    link = f'<a href="{html.escape(str(r.fms_url))}" target="_blank" rel="noopener">{d:.0f} m</a>'
    return (f"report {link} ({html.escape(str(r.fms_state))})" if d <= 25
            else f'<span class="muted">none &le; 25 m (nearest {link})</span>')


def write_html(spots, path):
    blocks = []
    for tier, g in spots.groupby("tier"):
        rows = "".join(
            f"<tr><td><b>{r.spot}</b></td><td>{r.impacts}</td><td>{r.rides_hitting}</td>"
            f"<td>{r.max_g:.2f}</td><td>{html.escape(r.road)}</td>"
            f"<td><a href=\"{html.escape(r.google_streetview_url)}\" target=\"_blank\" rel=\"noopener\">Street View</a> · "
            f"<a href=\"{html.escape(r.google_maps_url)}\" target=\"_blank\" rel=\"noopener\">Map</a> · "
            f"<a href=\"{html.escape(r.mapillary_url)}\" target=\"_blank\" rel=\"noopener\">Mapillary</a></td>"
            f"<td>{fms_cell(r)}</td>"
            f"<td class=\"muted\">{r.lat:.5f}, {r.lon:.5f} · facing {r.heading_deg:.0f}°</td>"
            f"<td class=\"muted\">{html.escape(r.events)}</td></tr>"
            for r in g.itertuples())
        blocks.append(f"<h2>Tier {tier}: {TIER_TEXT[tier]} ({len(g)})</h2><div class=\"wrap\"><table>"
                      f"<tr><th>Spot</th><th>Impacts</th><th>Rides</th><th>Max g</th><th>Road</th>"
                      f"<th>Open</th><th>FixMyStreet (recent)</th><th>Location</th><th>Events (recording#impact)</th></tr>"
                      f"{rows}</table></div>")
    path.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Impact Spot Links</title>
<style>
body{{margin:0;background:#fafaf8;color:#222;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1150px;margin:0 auto;padding:28px 16px 48px}} h1{{font-size:24px;margin:0 0 6px}}
h2{{font-size:19px;margin:28px 0 6px}} .sub,.muted{{color:#6b6b6b}} .muted{{font-size:13px}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;font-size:14px}}
th,td{{padding:6px 9px;border-bottom:1px solid #e3e2de;text-align:left;white-space:nowrap}} a{{color:#1c5cab}}
</style></head><body><main>
<h1>Impact spots: map links</h1>
<p class="sub">{len(spots)} spots over all recordings, most important first. Street View opens facing the
direction of travel, tilted towards the road; if there is no Street View there, use Map. Note each image's
capture date (shown in Street View): it may be before or after the ride. Fill in what you see in
<code>spot_links.csv</code> (columns imagery_date, what_visible, notes). <a href="combined_report.html">Combined report</a>
· <a href="combined_map.html">combined map</a>.</p>
<div style="background:#fff;border:1px solid #e3e2de;border-radius:8px;padding:10px 14px;margin:14px 0">
<b>Recording rules</b> (fixed before checking; method in <code>SPOT_CHECK.md</code>)
<ol style="margin:6px 0 0;padding-left:20px">
<li><code>imagery_date</code>: capture month/year shown in the viewer (newest if several).</li>
<li><code>what_visible</code>: one or more of {' · '.join(f"<code>{html.escape(c)}</code>" for c in sv.OBSERVATION_CHOICES if c)},
separated by <code>;</code></li>
<li>Count a feature only within about <b>15 m</b> of the pin, where a scooter would ride.</li>
<li>Anything else goes in <code>notes</code>; do not change the categories once started.</li>
</ol></div>
{''.join(blocks)}
</main></body></html>""", encoding="utf-8")


def main():
    spots = build_spots()
    out_csv = COMBINED / "spot_links.csv"
    if out_csv.exists():   # keep anything already filled in, matched on rounded location
        old = pd.read_csv(out_csv, dtype=str).fillna("")
        key = lambda df: df["lat"].astype(float).round(4).astype(str) + "," + df["lon"].astype(float).round(4).astype(str)
        filled = old.set_index(key(old))[["imagery_date", "what_visible", "notes"]]
        k = key(spots)
        for c in filled.columns:
            spots[c] = k.map(filled[c]).fillna("")
    spots.to_csv(out_csv, index=False)
    write_html(spots, COMBINED / "spot_links.html")
    print(spots.groupby("tier").size().rename(index=TIER_TEXT).to_string())
    print(spots.head(12)[["spot", "tier", "rides_hitting", "impacts", "max_g", "road", "lat", "lon",
                          "heading_deg"]].to_string(index=False))
    print(f"\nWrote {out_csv.resolve()} and spot_links.html")


if __name__ == "__main__":
    main()
