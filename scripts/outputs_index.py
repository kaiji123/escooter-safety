"""
Build outputs/index.html: one overview page linking every recording's outputs.

Recording 1 (the Part A pilot ride) keeps its outputs in outputs/ (the docs and paper
draft link to them); later recordings are in outputs/recordings/<recording>/. Run after
impact_map.py, impact_report.py and sensor_validity.py.

Usage
    python scripts/outputs_index.py
"""

import html
import json
from pathlib import Path

OUT = Path("outputs")
RECORDINGS = [  # (folder name, outputs folder relative to outputs/, note)
    ("2026-10-03_1830_rec01", ".", "Part A pilot ride (Voiager 5, vehicle SZ22). No walking."),
    ("2026-10-07_1037_rec02", "recordings/2026-10-07_1037_rec02",
     "Ride, Voi rental ended 10:46, then walking (shown on the map as a dashed orange line) and "
     "the phone mostly still; impact statistics count riding only (speed gate &ge; 7 km/h). Impacts 25&ndash;37 form a regular series "
     "(every ~0.6&ndash;1.2 s at ~8 km/h over ~20 m): a periodic surface or pushing with a foot "
     "is possible; not checked."),
    ("2026-10-07_1338_rec03", "recordings/2026-10-07_1338_rec03",
     "Ride. No walking. Strongest cluster (impacts 9&ndash;13, up to 6.28 g) lies within ~20 m of a "
     "recording 2 hotspot (51.7508, &minus;1.2389): a candidate for the Street View check."),
]


def row(name, rel, note):
    d = OUT / rel
    st = json.loads((d / "impact_stats.json").read_text())
    r, s = st["ride"], st["summary"]
    sv = f"sensor_validity/{name}/fig_timeline.png"
    links = " · ".join(
        f'<a href="{rel}/{f}">{lab}</a>' if (d / f).exists() else ""
        for f, lab in [("impact_map.html", "map"), ("impact_report.html", "report"),
                       ("impact_trace.png", "trace")])
    links += f' · <a href="{sv}">activity timeline</a>' if (OUT / sv).exists() else ""
    return f"""<tr><td><b>{html.escape(name)}</b><br><span class="note">{note}</span></td>
<td>{r['distance_km']:.2f}</td><td>{r['moving_min']:.1f}</td><td>{s['n_impacts']}</td>
<td>{s['per_km']:.1f}</td><td>{s['median_g']:.2f}</td><td>{s['max_g']:.2f}</td>
<td>{s['n_ge_1_5']}</td><td>{s['n_wobble']}</td><td class="links">{links}</td></tr>"""


def main():
    rows = "\n".join(row(*r) for r in RECORDINGS)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>E-scooter Recordings</title>
<style>
body{{margin:0;background:#fafaf8;color:#222;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1150px;margin:0 auto;padding:28px 16px 48px}} h1{{font-size:24px;margin:0 0 6px}}
h2{{font-size:19px;margin:30px 0 6px}} .sub,.note{{color:#6b6b6b}} .note{{font-size:13px}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;font-size:14px;width:100%}}
th,td{{padding:8px;border-bottom:1px solid #e3e2de;text-align:left;vertical-align:top}}
th{{font-weight:600;white-space:nowrap}} td.links{{white-space:nowrap}} a{{color:#1c5cab}}
ul{{padding-left:20px}}
</style></head><body><main>
<h1>E-scooter recordings: overview</h1>
<p class="sub">Sensor Logger on an iPhone 11 Pro Max, handlebar mount. Impacts: |vertical
acceleration| &ge; 1.0 g at &ge; 7 km/h (an analyst choice, not an established criterion).
Distance and time count riding speed only. Wobble = gyro ratio &ge; 1.5 after the impact.</p>
<div class="wrap"><table>
<tr><th>Recording</th><th>km ridden</th><th>min moving</th><th>Impacts</th><th>per km</th>
<th>Median g</th><th>Max g</th><th>&ge; 1.5 g</th><th>Wobble</th><th>Outputs</th></tr>
{rows}
</table></div>
<p class="note">Three rides by one rider on one phone; vehicle IDs for recordings 2 and 3 were
not recorded. Rates are not comparable as road-surface measures without knowing the routes,
speeds and vehicles; Part A results so far use recording 1 only.</p>
<h2>Across recordings</h2>
<ul>
<li><a href="sensor_validity/report.html">Sensor Logger validity: data quality and walking vs scooting</a></li>
<li><a href="fms_comparison.html">FixMyStreet comparison</a> and <a href="streetview_check.html">Street View check</a> (recording 1)</li>
<li><a href="scooter_sim/animations.html">Simulation animations</a> (Part B)</li>
</ul>
<p class="note">Maps and reports contain exact ride coordinates. Keep them local unless
sharing is decided, and trim the start and end of each route first.</p>
</main></body></html>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"Wrote {(OUT / 'index.html').resolve()}")


if __name__ == "__main__":
    main()
