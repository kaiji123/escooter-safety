"""
Street View checklist for the measured impact locations.

Builds outputs/streetview_check.html: one card per spot (repeated-impact hotspots
first, then single impacts by strength) with
  - a link that opens Google Maps' 360-degree Street View at the spot, already facing
    the direction of travel and tilted down towards the road surface,
  - links to Google Maps and Mapillary (open, crowd-sourced street imagery),
  - the measured impact data and the nearest FixMyStreet report,
  - a short form to record what the imagery shows; entries are kept in the browser
    and can be exported as CSV (save it to data/streetview_observations.csv).

Street View imagery itself cannot be embedded without a Google Maps API key, so the
page links to it instead. Imagery dates vary; record the date shown in Street View.

The page contains exact ride coordinates: keep it local unless sharing is intended.

Usage
    python scripts/streetview_page.py --data-dir data/raw/2026-10-03_1830_rec01 --out outputs/streetview_check.html
"""

import argparse
import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import impact_map as im  # noqa: E402

STREETVIEW_PITCH = -25   # degrees: look down towards the road surface
STREETVIEW_FOV = 80
OBSERVATION_CHOICES = [
    "", "Pothole", "Crack / broken surface", "Patched or repaired surface",
    "Drain or manhole cover", "Kerb / dropped kerb", "Speed hump / raised table",
    "Nothing visible", "No imagery here",
]


def heading_at(t, rough):
    """Direction of travel (degrees from north) at time t, from GPS 1 s either side."""
    def pos(tt):
        return (np.interp(tt, rough["t"], rough["lat"]), np.interp(tt, rough["t"], rough["lon"]))
    (la1, lo1), (la2, lo2) = pos(t - 1.0), pos(t + 1.0)
    dx = (lo2 - lo1) * np.cos(np.radians((la1 + la2) / 2))
    dy = la2 - la1
    return float((np.degrees(np.arctan2(dx, dy)) + 360) % 360)


def spots_table(impacts, rough):
    """One row per spot: hotspots (2+ impacts) first, then single impacts."""
    sizes = impacts["hotspot"].map(impacts["hotspot"].value_counts())
    rows = []
    for hid, g in impacts[sizes >= 2].groupby("hotspot"):
        first = g.sort_values("seconds_elapsed").iloc[0]
        rows.append({"kind": "Hotspot", "events": ", ".join(map(str, g["event_id"])),
                     "n": len(g), "lat": g["lat"].mean(), "lon": g["lon"].mean(),
                     "max_g": g["peak_abs_g"].max(), "speed_kmh": g["speed_kmh"].mean(),
                     "road": g["road"].iloc[0], "heading": heading_at(first["seconds_elapsed"], rough),
                     "reported": bool(g["reported"].any()),
                     "nearest_report_m": g["nearest_report_m"].min(),
                     "report_title": g.loc[g["nearest_report_m"].idxmin(), "nearest_report_title"],
                     "report_state": g.loc[g["nearest_report_m"].idxmin(), "nearest_report_state"],
                     "report_url": g.loc[g["nearest_report_m"].idxmin(), "nearest_report_url"],
                     "report_any_date_m": g["report_any_date_m"].min()})
    rows.sort(key=lambda r: (-r["n"], -r["max_g"]))
    singles = impacts[sizes < 2].sort_values("peak_abs_g", ascending=False)
    for _, r in singles.iterrows():
        rows.append({"kind": "Single impact", "events": str(r["event_id"]), "n": 1,
                     "lat": r["lat"], "lon": r["lon"], "max_g": r["peak_abs_g"],
                     "speed_kmh": r["speed_kmh"], "road": r["road"],
                     "heading": heading_at(r["seconds_elapsed"], rough),
                     "reported": bool(r["reported"]), "nearest_report_m": r["nearest_report_m"],
                     "report_title": r["nearest_report_title"], "report_state": r["nearest_report_state"],
                     "report_url": r["nearest_report_url"], "report_any_date_m": r["report_any_date_m"]})
    df = pd.DataFrame(rows)
    df.insert(0, "spot", [f"S{i}" for i in range(1, len(df) + 1)])
    return df


def links(r):
    ll = f"{r['lat']:.6f},{r['lon']:.6f}"
    sv = (f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={ll}"
          f"&heading={r['heading']:.0f}&pitch={STREETVIEW_PITCH}&fov={STREETVIEW_FOV}")
    gm = f"https://www.google.com/maps/search/?api=1&query={ll}"
    mp = f"https://www.mapillary.com/app/?lat={r['lat']:.6f}&lng={r['lon']:.6f}&z=19"
    return sv, gm, mp


def build_page(spots, label):
    opts = "".join(f"<option>{html.escape(o)}</option>" for o in OBSERVATION_CHOICES)
    cards = []
    for _, r in spots.iterrows():
        sv, gm, mp = links(r)
        severity = "strong" if r["max_g"] >= 1.5 else "moderate"
        if r["reported"]:
            fms = (f'Reported nearby ({r["nearest_report_m"]:.0f} m): '
                   f'<a href="{html.escape(str(r["report_url"]))}" target="_blank" rel="noopener">'
                   f'{html.escape(str(r["report_title"]))}</a> · status now: {html.escape(str(r["report_state"]))}')
        else:
            fms = (f"<b>No FixMyStreet report</b> within 25 m in the year before the ride "
                   f"(any date: nearest {r['report_any_date_m']:.0f} m)")
        what = (f"{r['n']} impacts (events {r['events']})" if r["kind"] == "Hotspot"
                else f"Impact event {r['events']}")
        cards.append(f"""
  <article class="card" id="{r['spot']}" data-spot="{r['spot']}">
    <header>
      <span class="badge {severity}">{r['spot']}</span>
      <h3>{html.escape(r['kind'])} · {html.escape(str(r['road']))}</h3>
    </header>
    <p class="facts">{what} · strongest <b>{r['max_g']:.2f} g</b> · ~{r['speed_kmh']:.0f} km/h ·
      facing {r['heading']:.0f}° (direction of travel)</p>
    <p class="facts">{fms}</p>
    <p class="btns">
      <a class="btn primary" href="{sv}" target="_blank" rel="noopener">Open 360° Street View</a>
      <a class="btn" href="{gm}" target="_blank" rel="noopener">Google Maps</a>
      <a class="btn" href="{mp}" target="_blank" rel="noopener">Mapillary</a>
      <span class="coords">{r['lat']:.5f}, {r['lon']:.5f}</span>
    </p>
    <div class="form">
      <label>What is visible <select data-field="observation">{opts}</select></label>
      <label>Imagery date <input data-field="imagery_date" placeholder="e.g. Jun 2025"></label>
      <label class="wide">Notes <input data-field="notes" placeholder="size, lane position, anything else"></label>
    </div>
  </article>""")

    spots_js = json.dumps([{"spot": r["spot"], "lat": round(r["lat"], 6), "lon": round(r["lon"], 6),
                            "kind": r["kind"], "g": round(r["max_g"], 2), "reported": r["reported"],
                            "events": r["events"], "road": r["road"]}
                           for _, r in spots.iterrows()])
    n_hs = int((spots["kind"] == "Hotspot").sum())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Street View Spot Check</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
:root{{--bg:#fafaf8;--card:#fff;--ink:#222;--muted:#6b6b6b;--line:#e3e2de;--blue:#2a78d6;--navy:#0d366b}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:980px;margin:0 auto;padding:26px 16px 60px}}
h1{{font-size:24px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 14px}}
.note{{background:#eef4fc;border-left:3px solid var(--blue);padding:10px 14px;border-radius:4px;margin:0 0 16px}}
#map{{height:380px;border:1px solid var(--line);border-radius:8px;margin:0 0 10px}}
.toolbar{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:12px 0 18px}}
.progress{{color:var(--muted)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:0 0 12px}}
.card header{{display:flex;gap:10px;align-items:center}} .card h3{{margin:0;font-size:16px}}
.badge{{display:inline-block;min-width:34px;text-align:center;border-radius:12px;padding:1px 8px;color:#fff;font-weight:600;font-size:13px}}
.badge.strong{{background:var(--navy)}} .badge.moderate{{background:var(--blue)}}
.facts{{margin:6px 0;font-size:14px}} .coords{{color:var(--muted);font-size:13px;margin-left:4px}}
.btns{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}}
.btn{{display:inline-block;padding:6px 12px;border:1px solid var(--line);border-radius:6px;color:var(--ink);text-decoration:none;background:#fff;font-size:14px}}
.btn.primary{{background:var(--blue);border-color:var(--blue);color:#fff}}
button.btn{{cursor:pointer}}
.form{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;margin-top:6px}}
.form label{{font-size:13px;color:var(--muted);display:flex;flex-direction:column;gap:3px}}
.form .wide{{grid-column:1/-1}}
select,input{{font:inherit;color:var(--ink);padding:5px 7px;border:1px solid var(--line);border-radius:5px;background:#fff}}
.card.done{{border-left:4px solid #1baf7a}}
a{{color:#1c5cab}}
</style></head><body><main>
<h1>Street View spot check</h1>
<p class="sub">{html.escape(label)} · {len(spots)} spots: {n_hs} hotspots (repeated impacts) and
{len(spots) - n_hs} single impacts · S-numbers are strongest-first within each group</p>
<p class="note"><b>How to use.</b> Click <i>Open 360° Street View</i>: Google Maps opens at the spot, facing your
direction of travel and looking down at the road; drag to look around. Record what you see and the imagery date
shown in Street View (imagery may be older or newer than your ride, and potholes appear and get repaired).
Entries are saved in this browser as you type. When done, click <i>Export CSV</i> and save the file as
<code>data/streetview_observations.csv</code>. Mapillary is an open alternative where Google imagery is missing.</p>
<div id="map" role="img" aria-label="Map of the spots"></div>
<div class="toolbar">
  <button class="btn primary" id="export" type="button">Export CSV</button>
  <span class="progress" id="progress"></span>
</div>
{''.join(cards)}
<p class="sub">Generated by scripts/streetview_page.py. Map tiles © Esri, © OpenStreetMap contributors.
Contains exact ride coordinates: keep local unless sharing is intended.</p>
</main>
<script>
const SPOTS = {spots_js};
const KEY = "streetview-check-v1";
function load() {{ try {{ return JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{ return {{}}; }} }}
function save(d) {{ try {{ localStorage.setItem(KEY, JSON.stringify(d)); }} catch (e) {{}} }}
let data = load();
function refresh() {{
  let done = 0;
  document.querySelectorAll(".card").forEach(c => {{
    const v = data[c.dataset.spot] || {{}};
    const isDone = !!v.observation;
    c.classList.toggle("done", isDone); if (isDone) done++;
  }});
  document.getElementById("progress").textContent = done + " of " + SPOTS.length + " spots recorded";
}}
document.querySelectorAll(".card").forEach(c => {{
  const id = c.dataset.spot;
  c.querySelectorAll("[data-field]").forEach(el => {{
    const f = el.dataset.field;
    if (data[id] && data[id][f]) el.value = data[id][f];
    el.addEventListener("input", () => {{
      data[id] = data[id] || {{}}; data[id][f] = el.value; save(data); refresh();
    }});
  }});
}});
refresh();
document.getElementById("export").addEventListener("click", () => {{
  const cols = ["spot","kind","events","road","lat","lon","max_g","reported_on_fixmystreet","observation","imagery_date","notes"];
  const esc = s => '"' + String(s ?? "").replace(/"/g, '""') + '"';
  const lines = [cols.join(",")].concat(SPOTS.map(s => {{
    const v = data[s.spot] || {{}};
    return [s.spot, s.kind, s.events, s.road, s.lat, s.lon, s.g, s.reported, v.observation, v.imagery_date, v.notes].map(esc).join(",");
  }}));
  const blob = new Blob([lines.join("\\n")], {{type: "text/csv"}});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "streetview_observations.csv"; document.body.appendChild(a); a.click(); a.remove();
}});
try {{
  const map = L.map("map");
  const esri = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_";
  L.tileLayer(esri + "Base/MapServer/tile/{{z}}/{{y}}/{{x}}", {{maxNativeZoom: 16, maxZoom: 19,
    attribution: "Tiles © Esri — Esri, HERE, Garmin, © OpenStreetMap contributors"}}).addTo(map);
  L.tileLayer(esri + "Reference/MapServer/tile/{{z}}/{{y}}/{{x}}", {{maxNativeZoom: 16, maxZoom: 19}}).addTo(map);
  const pts = [];
  SPOTS.forEach(s => {{
    const hot = s.kind === "Hotspot";
    const m = L.circleMarker([s.lat, s.lon], {{radius: hot ? 9 : 6, color: "#fff", weight: 2,
      fillColor: s.g >= 1.5 ? "#0d366b" : "#2a78d6", fillOpacity: 0.95}}).addTo(map);
    m.bindTooltip(s.spot + (hot ? " (hotspot)" : ""), {{permanent: hot, direction: "top", offset: [0, -6]}});
    m.on("click", () => document.getElementById(s.spot).scrollIntoView({{behavior: "smooth", block: "start"}}));
    pts.push([s.lat, s.lon]);
  }});
  map.fitBounds(pts, {{padding: [25, 25]}});
}} catch (e) {{
  document.getElementById("map").textContent = "Map unavailable (no internet connection?). The links below still work.";
}}
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Street View checklist for impact spots")
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/2026-10-03_1830_rec01"))
    ap.add_argument("--impacts", type=Path, default=Path("outputs/impacts_vs_fms.csv"),
                    help="output of fms_compare.py (impacts with road, hotspot, FixMyStreet match)")
    ap.add_argument("--out", type=Path, default=Path("outputs/streetview_check.html"))
    args = ap.parse_args()

    impacts = pd.read_csv(args.impacts)
    res = im.analyse(args.data_dir)
    spots = spots_table(impacts, res["rough"])
    args.out.write_text(build_page(spots, res["label"]), encoding="utf-8")
    spots.to_csv(args.out.with_suffix(".csv"), index=False)
    print(spots[["spot", "kind", "events", "road", "max_g", "heading", "reported"]].to_string(index=False))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
