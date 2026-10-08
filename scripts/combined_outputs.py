"""
Combine the per-recording impact outputs into one view: outputs/combined/.

Reads, for every folder in outputs/recordings/ that has been through impact_map.py and
impact_report.py:
    impacts_with_roads.csv, impacts_by_road.csv, impact_stats.json
and the raw GPS track (data/raw/<recording>/Location.csv) for the map.

Writes
    impacts_all.csv          every impact, with recording, local time and road
    summary.csv              per recording and pooled: km ridden, impacts, rates, severity
    by_road.csv              impacts per km by road, per recording and pooled
    hotspots_all.csv         hotspots over all recordings (single linkage, same 30 m radius
                             as impact_report.py) with the number of separate recordings
                             that hit each one
    combined_map.html        one map, one switchable layer per recording, walking bouts,
                             and hotspots hit on more than one recording
    combined_report.html     the tables above with caveats

Caveats (also printed on the report): the recordings are not independent (one rider, one
phone, overlapping roads), so pooled rates are descriptive; impact thresholds are
analyst choices. All three rides were on Voiager 5 scooters (confirmed by Voi customer
support, personal communications of 3 October and 8 October 2026). Hotspots are computed on the pooled
impacts, so their numbering differs from the per-recording reports.

Usage
    python scripts/combined_outputs.py
"""

import html
import json
import sys
from pathlib import Path

import folium
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import impact_map as im                      # noqa: E402
import impact_report as ir                   # noqa: E402

TZ = "Europe/London"
REC_DIR = Path("outputs/recordings")
RAW_DIR = Path("data/raw")
OUT = Path("outputs/combined")
WALKS = Path("outputs/sensor_validity/walking_onsets.csv")
ROUTE_COLOUR = "#8a8984"       # neutral: recordings are told apart by layer and tooltip
HOTSPOT_RING = "#222222"
MIN_KM_FOR_RATE = 0.2          # analyst choice: no per-km rate for shorter distances


def recordings():
    return sorted(p.name for p in REC_DIR.iterdir()
                  if (p / "impacts_with_roads.csv").exists() and (p / "impact_stats.json").exists())


def load(rec):
    d = REC_DIR / rec
    imp = pd.read_csv(d / "impacts_with_roads.csv")
    meta = pd.read_csv(RAW_DIR / rec / "Metadata.csv").iloc[0]
    t0 = pd.Timestamp(int(meta["recording epoch time"]), unit="ms", tz="UTC")
    imp.insert(0, "recording", rec)
    imp.insert(2, "local_time", (t0 + pd.to_timedelta(imp["seconds_elapsed"], unit="s"))
               .dt.tz_convert(TZ).dt.strftime("%Y-%m-%d %H:%M:%S"))
    imp = imp.rename(columns={"hotspot": "hotspot_in_recording"})
    fms = d / "impacts_vs_fms.csv"      # FixMyStreet match from fms_compare.py, if run
    if fms.exists():
        f = pd.read_csv(fms)[['event_id', 'reported', 'nearest_report_m', 'nearest_report_title', 'nearest_report_state', 'nearest_report_created', 'nearest_report_url']]
        imp = imp.merge(f.rename(columns={"reported": "fms_recent_report_within_25m"}),
                        on="event_id", how="left")
    stats = json.loads((d / "impact_stats.json").read_text())
    by_road = pd.read_csv(d / "impacts_by_road.csv").assign(recording=rec)
    return imp, stats, by_road


def summary_table(imps, stats):
    rows = []
    for rec in imps["recording"].unique():
        r, s = stats[rec]["ride"], stats[rec]["summary"]
        rows.append({"recording": rec, "km_ridden": round(r["distance_km"], 2),
                     "min_moving": round(r["moving_min"], 1), "impacts": s["n_impacts"],
                     "per_km": round(s["per_km"], 1), "median_g": round(s["median_g"], 2),
                     "max_g": round(s["max_g"], 2), "ge_1_5g": s["n_ge_1_5"], "wobble": s["n_wobble"]})
    t = pd.DataFrame(rows)
    allg = imps["peak_abs_g"]
    pooled = {"recording": "pooled (all)", "km_ridden": round(t["km_ridden"].sum(), 2),
              "min_moving": round(t["min_moving"].sum(), 1), "impacts": int(t["impacts"].sum()),
              "per_km": round(t["impacts"].sum() / t["km_ridden"].sum(), 1),
              "median_g": round(float(allg.median()), 2), "max_g": round(float(allg.max()), 2),
              "ge_1_5g": int(t["ge_1_5g"].sum()), "wobble": int(t["wobble"].sum())}
    return pd.concat([t, pd.DataFrame([pooled])], ignore_index=True)


def road_table(roads):
    per = roads.pivot_table(index="road", columns="recording", values=["km_ridden", "impacts"],
                            aggfunc="sum", fill_value=0)
    out = pd.DataFrame(index=per.index)
    for rec in roads["recording"].unique():
        km, n = per[("km_ridden", rec)], per[("impacts", rec)]
        out[f"{rec} km"] = km.round(2)
        out[f"{rec} per km"] = (n / km.where(km >= MIN_KM_FOR_RATE)).round(1)
    out["pooled km"] = per["km_ridden"].sum(axis=1).round(2)
    out["pooled impacts"] = per["impacts"].sum(axis=1).astype(int)
    out["pooled per km"] = (out["pooled impacts"] / out["pooled km"].where(out["pooled km"] >= MIN_KM_FOR_RATE)).round(1)
    order = [r for r in ir.STUDY_ROADS.values() if r in out.index] + [r for r in out.index
                                                                     if r not in ir.STUDY_ROADS.values()]
    return out.loc[list(dict.fromkeys(order))]


def hotspot_table(imps):
    lat0, lon0 = imps["lat"].mean(), imps["lon"].mean()
    imps["hotspot_all"] = ir.hotspots(imps, lat0, lon0).to_numpy()
    rows = []
    for h, g in imps.groupby("hotspot_all"):
        if len(g) < 2:
            continue
        rows.append({"hotspot": int(h), "impacts": len(g), "recordings_hitting": g["recording"].nunique(),
                     "recordings": ", ".join(sorted(g["recording"].unique())),
                     "max_g": g["peak_abs_g"].max(), "median_g": g["peak_abs_g"].median(),
                     "road": g["road"].mode().iloc[0], "lat": round(g["lat"].mean(), 5),
                     "lon": round(g["lon"].mean(), 5),
                     "events": "; ".join(f"{r.recording[-5:]}#{r.event_id}" for r in g.itertuples())})
    hs = pd.DataFrame(rows).sort_values(["recordings_hitting", "impacts", "max_g"], ascending=False)
    return hs.reset_index(drop=True)


def build_map(imps, hs, recs):
    m = im.base_map([imps["lat"].mean(), imps["lon"].mean()])
    walks_all = []
    for rec in recs:
        _, _, _, _, _, loc = im.load_inputs(RAW_DIR / rec)
        fg = folium.FeatureGroup(name=f"{rec} ({(imps['recording'] == rec).sum()} impacts)")
        folium.PolyLine(loc[["latitude", "longitude"]].to_numpy(), color=ROUTE_COLOUR, weight=3,
                        opacity=0.7, tooltip=f"GPS track {rec}").add_to(fg)
        for _, r in imps[imps["recording"] == rec].sort_values("peak_abs_g").iterrows():
            _, label, colour = im.severity_band(r["peak_abs_g"])
            folium.CircleMarker(
                location=[r["lat"], r["lon"]], radius=5 + 4 * (r["peak_abs_g"] - 1.0),
                color="#ffffff", weight=2, fill=True, fill_color=colour, fill_opacity=0.95,
                tooltip=f"{r['peak_abs_g']:.2f} g at {r['speed_kmh']:.0f} km/h · {rec} #{r['event_id']}",
                popup=folium.Popup(f"<b>{html.escape(rec)}, impact {r['event_id']}</b><br>"
                                   f"{r['local_time']}<br>Peak {r['peak_abs_g']:.2f} g ({label})<br>"
                                   f"Speed {r['speed_kmh']:.1f} km/h<br>Road: {html.escape(r['road'])}",
                                   max_width=260)).add_to(fg)
        for a, b, la, lb, steps in im.walking_bouts(WALKS, rec):
            g = loc[(loc["seconds_elapsed"] >= a) & (loc["seconds_elapsed"] <= b)]
            if len(g) >= 2:
                folium.PolyLine(g[["latitude", "longitude"]].to_numpy(), color=im.WALK_COLOUR,
                                weight=5, opacity=0.95, dash_array="8 6",
                                tooltip=f"Walking (detected) {rec}: {la}-{lb}, {steps} steps").add_to(fg)
                walks_all.append(rec)
        fg.add_to(m)

    multi = hs[hs["recordings_hitting"] >= 2]
    fg = folium.FeatureGroup(name=f"Hotspots hit on 2+ recordings ({len(multi)})")
    for r in multi.itertuples():
        folium.Circle(location=[r.lat, r.lon], radius=ir.HOTSPOT_RADIUS_M, color=HOTSPOT_RING,
                      weight=2, fill=False, dash_array="4 4",
                      tooltip=f"Hotspot {r.hotspot}: {r.impacts} impacts on {r.recordings_hitting} "
                              f"recordings, max {r.max_g:.2f} g ({r.road})").add_to(fg)
    fg.add_to(m)

    rows = "".join(
        f'<div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;'
        f'background:{c};border:2px solid #fff;box-shadow:0 0 0 1px #999;margin-right:6px;'
        f'vertical-align:middle"></span>{lab}</div>' for _, lab, c in im.SEVERITY_BANDS)
    walk_row = (f'<div style="margin-top:6px"><span style="display:inline-block;width:22px;border-top:4px '
                f'dashed {im.WALK_COLOUR};margin-right:6px;vertical-align:middle"></span>Walking (detected)</div>'
                if walks_all else "")
    ring_row = (f'<div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;'
                f'border:2px dashed {HOTSPOT_RING};margin-right:6px;vertical-align:middle"></span>'
                f'Hotspot hit on 2+ recordings ({ir.HOTSPOT_RADIUS_M:g} m)</div>')
    legend = f"""
    <div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:#fff;padding:10px 12px;
         border-radius:6px;font:13px/1.5 sans-serif;color:#222;box-shadow:0 1px 4px rgba(0,0,0,.3)">
      <b>All recordings: impact events</b>{rows}{walk_row}{ring_row}
      <div style="color:#666;margin-top:4px">{len(imps)} events &ge; {im.THRESHOLD_G:g} g at
      &ge; {im.MIN_SPEED_MS * 3.6:.0f} km/h, {len(recs)} recordings<br>Switch recordings on/off top right</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[imps["lat"].min(), imps["lon"].min()], [imps["lat"].max(), imps["lon"].max()]],
                 padding=(30, 30))
    return m


def fms_section(imps, recs):
    """Impacts with a recent FixMyStreet road-surface report within 25 m, per recording."""
    if "fms_recent_report_within_25m" not in imps:
        return ""
    rows = []
    for rec in recs:
        g = imps[imps["recording"] == rec]["fms_recent_report_within_25m"]
        if g.notna().any():
            rows.append(f"<tr><td>{rec}</td><td>{int(g.sum())} of {len(g)}</td>"
                        f"<td>{100 * g.mean():.0f}%</td><td><a href=\"../recordings/{rec}/fms_comparison.html\">"
                        f"comparison and route baseline</a></td></tr>")
    return ("<h2>FixMyStreet: impacts near a recent report</h2><p class=\"sub\">Recent = road-surface report "
            "made in the 365 days before that ride, within 25 m. Each recording is compared with reports from "
            "its own route's area; the route baseline (share of all route points near a report) is on each "
            "recording's comparison page. No FixMyStreet report does not mean unreported: other channels exist."
            "</p><div class=\"wrap\"><table class=\"t\"><tr><th>Recording</th><th>Impacts</th><th>Share</th>"
            f"<th></th></tr>{''.join(rows)}</table></div>")


def write_report(path, summ, roads, hs, recs, fms_html=""):
    def tbl(df, index=False):
        return df.to_html(index=index, border=0, classes="t", na_rep="–", float_format=lambda v: f"{v:.2f}")
    multi = hs[hs["recordings_hitting"] >= 2]
    path.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All Recordings Combined</title>
<style>
body{{margin:0;background:#fafaf8;color:#222;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1150px;margin:0 auto;padding:28px 16px 48px}} h1{{font-size:24px;margin:0 0 6px}}
h2{{font-size:19px;margin:30px 0 6px}} .sub{{color:#6b6b6b}} a{{color:#1c5cab}}
.wrap{{overflow-x:auto}} table.t{{border-collapse:collapse;font-size:13.5px}}
table.t th,table.t td{{padding:5px 9px;border-bottom:1px solid #e3e2de;text-align:left;white-space:nowrap}}
ul{{padding-left:20px}}
</style></head><body><main>
<h1>All recordings combined</h1>
<p class="sub">{len(recs)} recordings · <a href="combined_map.html">combined map</a> · <a href="spot_links.html">spot links</a>
(run spot_links.py) · <a href="../index.html">overview</a>.
Impacts: |vertical acceleration| &ge; {im.THRESHOLD_G:g} g at &ge; {im.MIN_SPEED_MS * 3.6:.0f} km/h
(analyst choices, not established criteria). Distance counts riding speed only.</p>
<h2>Read with care</h2>
<ul>
<li>The recordings are <b>not independent</b>: one rider, one phone, overlapping roads. A spot hit on
several rides is several measurements of one spot. Pooled rates are descriptive, not a sample estimate.</li>
<li>All three rides were on Voi Voiager 5 scooters (confirmed by Voi customer support, personal communications, 3 October 2026 for ride 1 and 8 October 2026 for rides 2 and 3),
so pooling does not mix models. Individual scooters may still differ
(tyre wear and pressure, fork condition): each ride was on a different scooter (SZ22, UPAR, BTLZ).</li>
<li>Recording 2's impacts 25&ndash;37 form a regular series (~0.6&ndash;1.2 s apart at ~8 km/h); not checked.
They make up most of the largest pooled hotspot, which recording 3 also hit (its impacts 1&ndash;5), so a
rough surface there is plausible, but not confirmed.</li>
<li>Distance comes from GPS-reported speed, which under-read walking speed in the validity check
(<a href="../sensor_validity/report.html">report</a>).</li>
<li>Hotspots here are clustered on the pooled impacts, so their numbers differ from the per-recording reports.</li>
</ul>
<h2>Per recording and pooled</h2><div class="wrap">{tbl(summ)}</div>
{fms_html}
<h2>Impacts per km by road</h2>
<p class="sub">Rates are left blank (&ndash;) where less than {MIN_KM_FOR_RATE:g} km was ridden on that road
(an analyst choice): a few impacts over a few metres give meaningless rates.</p>
<div class="wrap">{tbl(roads, index=True)}</div>
<h2>Hotspots hit on two or more recordings ({len(multi)})</h2>
<div class="wrap">{tbl(multi.drop(columns=["events"])) if len(multi) else "<p>None.</p>"}</div>
<h2>All hotspots (2+ impacts within {ir.HOTSPOT_RADIUS_M:g} m)</h2>
<div class="wrap">{tbl(hs)}</div>
</main></body></html>""", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recs = recordings()
    loaded = {r: load(r) for r in recs}
    imps = pd.concat([v[0] for v in loaded.values()], ignore_index=True)
    stats = {r: v[1] for r, v in loaded.items()}
    roads = pd.concat([v[2] for v in loaded.values()], ignore_index=True)

    summ = summary_table(imps, stats)
    rtab = road_table(roads)
    hs = hotspot_table(imps)

    imps.to_csv(OUT / "impacts_all.csv", index=False)
    summ.to_csv(OUT / "summary.csv", index=False)
    rtab.to_csv(OUT / "by_road.csv")
    hs.to_csv(OUT / "hotspots_all.csv", index=False)
    build_map(imps, hs, recs).save(str(OUT / "combined_map.html"))
    write_report(OUT / "combined_report.html", summ, rtab, hs, recs, fms_section(imps, recs))

    pd.set_option("display.width", 220)
    print(summ.to_string(index=False))
    print("\nBy road:\n", rtab.to_string())
    print("\nHotspots hit on 2+ recordings:\n",
          hs[hs["recordings_hitting"] >= 2].drop(columns=["events"]).to_string(index=False))
    print(f"\nOutputs in {OUT.resolve()}")


if __name__ == "__main__":
    main()
