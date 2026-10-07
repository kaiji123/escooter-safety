"""
Statistics report on e-scooter impact events for one recording.

Builds on impact_map.py (same detection, same parameters) and adds:
  - ride summary (moving time, distance, speed)
  - impact counts, rates (per km, per moving minute) and severity distribution
  - impacts followed by marked handlebar wobble (instability ratio >= WOBBLE_RATIO)
  - breakdown by study road, using OpenStreetMap road geometry
  - hotspots: impacts within HOTSPOT_RADIUS_M of each other
  - speed vs severity (Spearman rank correlation)

What the numbers mean: the sensors measure vertical jolts at the handlebar.
They do NOT measure whether the rider felt at risk; impact counts are used as
an objective proxy for that experience.

Road geometry is fetched once from the Overpass API (a bounding-box query for
the study roads in Headington, containing no ride data) and cached in
data/osm_study_roads.json so reruns are reproducible and offline.

Usage
    python scripts/impact_report.py --data-dir data/raw/2026-10-03_1830_rec01 --out-dir outputs
"""

import argparse
import base64
import html
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import impact_map as im  # noqa: E402

# ---- Report parameters ----
WOBBLE_RATIO = 1.5       # post/pre gyro RMS at or above this = "marked wobble"
ROAD_MATCH_M = 20.0      # max distance from a road centreline to count as on that road
HOTSPOT_RADIUS_M = 30.0  # impacts closer than this (single linkage) form one hotspot

# Study area bounding box (south, west, north, east). Its eastern edge excludes
# the other "Old Road" at Forest Hill / Shotover.
STUDY_BBOX = (51.740, -1.250, 51.770, -1.190)
# OSM name -> study road. Headington Hill is the steep section of Headington Road.
STUDY_ROADS = {"Marston Road": "Marston Road", "Headington Road": "Headington Road",
               "Headington Hill": "Headington Road", "Old Road": "Old Road",
               "Morrell Avenue": "Morrell Avenue"}
OVERPASS_URLS = ["https://overpass-api.de/api/interpreter",
                 "https://overpass.kumi.systems/api/interpreter"]
OTHER = "Other roads"

BLUE = "#2a78d6"
BLUE_DARK = "#0d366b"
INK = "#222222"
MUTED = "#6b6b6b"


# --------------------------------------------------------------------------- roads
def fetch_study_roads(cache_path):
    """Return OSM ways for the study roads, using a local cache when present.

    The cache stores the query it came from; changing STUDY_ROADS or STUDY_BBOX
    invalidates it and triggers a fresh download.
    """
    names = "|".join(STUDY_ROADS)
    s, w, n, e = STUDY_BBOX
    query = (f'[out:json][timeout:60];way["highway"]["name"~"^({names})$"]'
             f'({s},{w},{n},{e});out geom tags;')
    if cache_path.exists():
        cached = json.loads(cache_path.read_text())
        if cached.get("_query") == query:
            return cached

    last_err = None
    for url in OVERPASS_URLS:  # public servers are often busy; try a mirror
        try:
            req = urllib.request.Request(
                url, data=urllib.parse.urlencode({"data": query}).encode(),
                headers={"User-Agent": "escooter-safety-research (student project)"})
            data = json.load(urllib.request.urlopen(req, timeout=90))
            break
        except Exception as err:
            last_err = err
    else:
        raise RuntimeError(f"Could not download road geometry: {last_err}")
    data["_query"] = query
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data))
    return data


def to_metres(lat, lon, lat0, lon0):
    """Local equirectangular projection; accurate to <0.1% over a few km."""
    x = (np.asarray(lon) - lon0) * np.cos(np.radians(lat0)) * 111_320.0
    y = (np.asarray(lat) - lat0) * 110_540.0
    return x, y


def assign_roads(lat, lon, osm, lat0, lon0):
    """Nearest study road for each point, or OTHER if none within ROAD_MATCH_M."""
    seg_a, seg_b, seg_road = [], [], []
    for el in osm["elements"]:
        g = el["geometry"]
        x, y = to_metres([p["lat"] for p in g], [p["lon"] for p in g], lat0, lon0)
        pts = np.column_stack([x, y])
        seg_a.append(pts[:-1]); seg_b.append(pts[1:])
        seg_road += [STUDY_ROADS[el["tags"]["name"]]] * (len(pts) - 1)
    A, B = np.vstack(seg_a), np.vstack(seg_b)
    seg_road = np.array(seg_road)

    px, py = to_metres(lat, lon, lat0, lon0)
    P = np.column_stack([px, py])[:, None, :]           # (points, 1, 2)
    AB = (B - A)[None, :, :]                             # (1, segments, 2)
    tproj = np.clip(((P - A) * AB).sum(-1) / np.maximum((AB ** 2).sum(-1), 1e-9), 0, 1)
    d = np.linalg.norm(P - (A + tproj[..., None] * AB), axis=-1)
    nearest = d.argmin(1)
    dmin = d[np.arange(len(P)), nearest]
    return np.where(dmin <= ROAD_MATCH_M, seg_road[nearest], OTHER), dmin


# --------------------------------------------------------------------------- stats
def hotspots(impacts, lat0, lon0):
    if len(impacts) < 2:
        return pd.Series(np.arange(len(impacts)) + 1, index=impacts.index)
    x, y = to_metres(impacts["lat"], impacts["lon"], lat0, lon0)
    Z = linkage(np.column_stack([x, y]), method="single")
    return pd.Series(fcluster(Z, t=HOTSPOT_RADIUS_M, criterion="distance"), index=impacts.index)


def band_label(g):
    return im.severity_band(g)[1]


def compute(res, osm):
    impacts, rough = res["impacts"].copy(), res["rough"].copy()
    lat0, lon0 = rough["lat"].mean(), rough["lon"].mean()

    # Ride summary from the 1 s roughness windows (each window = 1 s of riding).
    rough["moving"] = rough["speed"] >= im.MIN_SPEED_MS
    rough["dist_m"] = np.where(rough["moving"], rough["speed"] * im.ROUGH_WIN_S, 0.0)
    rough["road"], _ = assign_roads(rough["lat"], rough["lon"], osm, lat0, lon0)
    moving_s = rough["moving"].sum() * im.ROUGH_WIN_S
    dist_km = rough["dist_m"].sum() / 1000
    ride = {
        "recording": res["label"],
        "duration_min": (res["t"][-1] - res["t"][0]) / 60,
        "moving_min": moving_s / 60,
        "distance_km": dist_km,
        "mean_moving_speed_kmh": rough.loc[rough["moving"], "speed"].mean() * 3.6,
    }

    n = len(impacts)
    impacts["severity_band"] = impacts["peak_abs_g"].map(band_label)
    impacts["marked_wobble"] = impacts["instability_ratio"] >= WOBBLE_RATIO
    impacts["road"], impacts["road_dist_m"] = assign_roads(
        impacts["lat"], impacts["lon"], osm, lat0, lon0)
    impacts["hotspot"] = hotspots(impacts, lat0, lon0)

    g = impacts["peak_abs_g"]
    summary = {
        "n_impacts": n,
        "per_km": n / dist_km if dist_km else np.nan,
        "per_moving_min": n / (moving_s / 60) if moving_s else np.nan,
        "metres_between": dist_km * 1000 / n if n else np.nan,
        "median_g": g.median(), "q1_g": g.quantile(.25), "q3_g": g.quantile(.75),
        "max_g": g.max(),
        "n_ge_1_5": int((g >= 1.5).sum()), "n_ge_2": int((g >= 2.0).sum()),
        "n_wobble": int(impacts["marked_wobble"].sum()),
        "n_ge_1_5_and_wobble": int(((g >= 1.5) & impacts["marked_wobble"]).sum()),
    }
    rho, p = spearmanr(impacts["speed_kmh"], g) if n >= 3 else (np.nan, np.nan)
    summary.update({"spearman_rho": rho, "spearman_p": p})

    bands = [b[1] for b in im.SEVERITY_BANDS]
    by_band = (impacts.groupby("severity_band")
               .agg(impacts=("event_id", "size"), with_wobble=("marked_wobble", "sum"))
               .reindex(bands, fill_value=0))
    by_band["pct"] = 100 * by_band["impacts"] / max(n, 1)

    road_order = list(dict.fromkeys(STUDY_ROADS.values())) + [OTHER]
    km = rough.groupby("road")["dist_m"].sum() / 1000
    by_road = (impacts.groupby("road")
               .agg(impacts=("event_id", "size"),
                    ge_1_5g=("peak_abs_g", lambda s: int((s >= 1.5).sum())),
                    with_wobble=("marked_wobble", "sum"),
                    max_g=("peak_abs_g", "max"))
               .reindex(road_order))
    by_road.insert(0, "km_ridden", km.reindex(road_order))
    by_road[["impacts", "ge_1_5g", "with_wobble"]] = (
        by_road[["impacts", "ge_1_5g", "with_wobble"]].fillna(0).astype(int))
    by_road["per_km"] = by_road["impacts"] / by_road["km_ridden"]
    by_road = by_road[by_road["km_ridden"].fillna(0) > 0]  # roads not ridden are omitted

    hs = (impacts.groupby("hotspot")
          .agg(impacts=("event_id", "size"), events=("event_id", lambda s: ", ".join(map(str, s))),
               max_g=("peak_abs_g", "max"), road=("road", "first"),
               lat=("lat", "mean"), lon=("lon", "mean")))
    hs = hs[hs["impacts"] >= 2].sort_values(["impacts", "max_g"], ascending=False)

    return ride, summary, impacts, by_band, by_road, hs


# --------------------------------------------------------------------------- figures
def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#bbbbbb")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(INK); ax.yaxis.label.set_color(INK)


def fig_severity(impacts, path):
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    bins = np.arange(1.0, max(3.0, impacts["peak_abs_g"].max() + 0.1) + 1e-9, 0.1)
    ax.hist(impacts["peak_abs_g"], bins=bins, color=BLUE, edgecolor="white", linewidth=2)
    ax.set_xlabel("Peak vertical acceleration (g)")
    ax.set_ylabel("Impacts")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.grid(axis="y", color="#e8e8e8", lw=0.6); ax.set_axisbelow(True)
    _style(ax); fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fig_roads(by_road, path):
    d = by_road.iloc[::-1]
    fig, ax = plt.subplots(figsize=(6.4, 0.55 * len(d) + 1.0))
    ax.barh(d.index, d["per_km"], color=BLUE, height=0.6)
    for y, (rate, n_, km_) in enumerate(zip(d["per_km"], d["impacts"], d["km_ridden"])):
        ax.text(rate, y, f"  {rate:.1f}/km  (n={n_}, {km_:.2f} km)", va="center",
                fontsize=9, color=INK)
    ax.set_xlabel("Impacts per km ridden")
    ax.set_xlim(0, d["per_km"].max() * 1.6)
    _style(ax); fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fig_speed(impacts, summary, path):
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.scatter(impacts["speed_kmh"], impacts["peak_abs_g"], s=60, color=BLUE,
               edgecolor="white", linewidth=1.5, zorder=3)
    ax.set_xlabel("Speed at impact (km/h)")
    ax.set_ylabel("Peak vertical acceleration (g)")
    ax.set_title(f"Spearman ρ = {summary['spearman_rho']:.2f}, p = {summary['spearman_p']:.2f}, "
                 f"n = {summary['n_impacts']}", fontsize=9, color=MUTED, loc="left")
    ax.grid(color="#e8e8e8", lw=0.6); ax.set_axisbelow(True)
    _style(ax); fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def img_tag(path, alt):
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b64}" alt="{html.escape(alt)}">'


# --------------------------------------------------------------------------- report
def table(df, fmt=None, index=True):
    fmt = fmt or {}
    cols = ([df.index.name or ""] if index else []) + list(df.columns)
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
    rows = []
    for idx, r in df.iterrows():
        cells = [f"<td>{html.escape(str(idx))}</td>"] if index else []
        for c in df.columns:
            v = r[c]
            s = "–" if pd.isna(v) else (fmt[c].format(v) if c in fmt else str(v))
            cells.append(f"<td>{html.escape(s)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def write_html(path, ride, s, impacts, by_band, by_road, hs, figs, threshold_g):
    tiles = [
        (f"{s['n_impacts']}", f"impacts ≥ {threshold_g:g} g"),
        (f"{s['per_km']:.1f}", "impacts per km"),
        (f"1 every {s['metres_between']:.0f} m", "average spacing"),
        (f"{s['n_ge_1_5']}", "impacts ≥ 1.5 g"),
        (f"{s['n_wobble']}", f"followed by marked wobble (≥ {WOBBLE_RATIO:g}×)"),
        (f"{s['max_g']:.2f} g", "strongest impact"),
    ]
    tiles_html = "".join(f'<div class="tile"><div class="v">{v}</div><div class="k">{k}</div></div>'
                         for v, k in tiles)

    band_t = by_band.rename(columns={"impacts": "Impacts", "with_wobble": "With marked wobble",
                                     "pct": "% of impacts"})
    band_t.index.name = "Severity band"
    road_t = by_road.rename(columns={"km_ridden": "km ridden", "impacts": "Impacts",
                                     "per_km": "Per km", "ge_1_5g": "≥ 1.5 g",
                                     "with_wobble": "With wobble", "max_g": "Max g"})
    road_t = road_t[["km ridden", "Impacts", "Per km", "≥ 1.5 g", "With wobble", "Max g"]]
    road_t.index.name = "Road"
    hs_t = hs[["road", "impacts", "events", "max_g", "lat", "lon"]].rename(columns={
        "road": "Road", "impacts": "Impacts", "events": "Event IDs", "max_g": "Max g",
        "lat": "Lat", "lon": "Lon"})
    hs_t.index.name = "Hotspot"
    ev_t = impacts[["event_id", "seconds_elapsed", "road", "peak_abs_g", "severity_band",
                    "speed_kmh", "instability_ratio", "marked_wobble"]].rename(columns={
        "event_id": "#", "seconds_elapsed": "t (s)", "road": "Road", "peak_abs_g": "Peak g",
        "severity_band": "Band", "speed_kmh": "km/h", "instability_ratio": "Wobble ratio",
        "marked_wobble": "Marked wobble"})

    rho_txt = (f"Spearman ρ = {s['spearman_rho']:.2f} (p = {s['spearman_p']:.2f}, n = {s['n_impacts']})")
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Impact Statistics Report</title>
<style>
:root{{--bg:#fafaf8;--card:#fff;--ink:#222;--muted:#6b6b6b;--line:#e3e2de;--accent:{BLUE}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:880px;margin:0 auto;padding:32px 16px 64px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:19px;margin:36px 0 10px}}
.sub{{color:var(--muted);margin:0 0 20px}}
.note{{background:#eef4fc;border-left:3px solid var(--accent);padding:10px 14px;border-radius:4px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}}
.tile .v{{font-size:24px;font-weight:650}} .tile .k{{color:var(--muted);font-size:13px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--card)}}
th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid var(--line)}}
th{{color:var(--muted);font-weight:600}} td{{font-variant-numeric:tabular-nums}}
.scroll{{overflow-x:auto}} img{{max-width:100%;height:auto;display:block;margin:8px 0}}
ul{{padding-left:20px}} li{{margin:4px 0}}
</style></head><body><main>
<h1>E-scooter impact statistics</h1>
<p class="sub">{html.escape(ride['recording'])} · {ride['distance_km']:.2f} km ridden in
{ride['moving_min']:.1f} min moving ({ride['duration_min']:.1f} min recorded) ·
mean moving speed {ride['mean_moving_speed_kmh']:.1f} km/h</p>

<p class="note"><b>How to read this.</b> An <i>impact</i> is a vertical jolt at the handlebar of at least
{threshold_g:g} g while riding at {im.MIN_SPEED_MS*3.6:.0f} km/h or faster. The sensors cannot record whether
the rider felt at risk; impact counts are an objective proxy for that experience. <i>Marked wobble</i> means
handlebar rotation in the 1.5 s after the impact was at least {WOBBLE_RATIO:g}× the rotation before it.</p>

<h2>Headline figures</h2>
<div class="tiles">{tiles_html}</div>
<p>{s['n_ge_1_5_and_wobble']} impacts were both strong (≥ 1.5 g) <i>and</i> followed by marked wobble —
the clearest candidates for moments of lost stability.</p>

<h2>Severity</h2>
<p>Median peak {s['median_g']:.2f} g (interquartile range {s['q1_g']:.2f}–{s['q3_g']:.2f} g).
{s['n_ge_2']} impact(s) reached 2 g or more.</p>
{img_tag(figs['severity'], 'Histogram of peak vertical acceleration per impact')}
<div class="scroll">{table(band_t, {"pct": "{:.0f}%"})}</div>

<h2>By road</h2>
<p>Points are assigned to a study road when within {ROAD_MATCH_M:g} m of its OpenStreetMap
centreline; everything else is “{OTHER}”. Rates on short stretches rest on few impacts.</p>
{img_tag(figs['roads'], 'Impacts per km ridden by road')}
<div class="scroll">{table(road_t, {"km ridden": "{:.2f}", "Per km": "{:.1f}", "Max g": "{:.2f}"})}</div>

<h2>Hotspots</h2>
<p>Places where two or more impacts fell within {HOTSPOT_RADIUS_M:g} m of each other.
Worth checking on foot and against FixMyStreet reports.</p>
<div class="scroll">{table(hs_t, {"Max g": "{:.2f}", "Lat": "{:.5f}", "Lon": "{:.5f}"})
                     if len(hs_t) else "<p>None found.</p>"}</div>

<h2>Speed and severity</h2>
<p>{rho_txt}. A single ride at a narrow range of speeds cannot separate the effect of speed from the
effect of the road surface; treat this as descriptive.</p>
{img_tag(figs['speed'], 'Scatter of speed at impact against peak vertical acceleration')}

<h2>All impact events</h2>
<div class="scroll">{table(ev_t, {"Peak g": "{:.2f}", "km/h": "{:.1f}", "Wobble ratio": "{:.2f}"},
                           index=False)}</div>

<h2>Limitations</h2>
<ul>
<li>One ride, one rider, one phone mount. Counts will vary with route, speed, tyre pressure and mount stiffness.</li>
<li>The 1.0 g threshold, severity bands and {WOBBLE_RATIO:g}× wobble cut-off are analyst choices for this
study, not established injury or comfort criteria.</li>
<li>Impacts are positioned from 1 Hz GPS (typical accuracy ~10 m); road assignment near junctions can be wrong.</li>
<li>Kerbs, drop-kerbs, speed humps and manhole covers register as impacts too; not every impact is a pothole.</li>
</ul>
<p class="sub">Generated by scripts/impact_report.py. Road data © OpenStreetMap contributors (ODbL).</p>
</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Impact statistics report")
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/2026-10-03_1830_rec01"))
    ap.add_argument("--out-dir", type=Path, default=Path("outputs"))
    ap.add_argument("--threshold-g", type=float, default=im.THRESHOLD_G)
    ap.add_argument("--roads-cache", type=Path, default=Path("data/osm_study_roads.json"))
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    res = im.analyse(args.data_dir, args.threshold_g)
    if res["impacts"].empty:
        sys.exit("No impacts detected; nothing to report.")
    osm = fetch_study_roads(args.roads_cache)
    ride, s, impacts, by_band, by_road, hs = compute(res, osm)

    figs = {"severity": args.out_dir / "fig_severity_hist.png",
            "roads": args.out_dir / "fig_impacts_per_km_by_road.png",
            "speed": args.out_dir / "fig_speed_vs_severity.png"}
    fig_severity(impacts, figs["severity"])
    fig_roads(by_road, figs["roads"])
    fig_speed(impacts, s, figs["speed"])

    impacts.to_csv(args.out_dir / "impacts_with_roads.csv", index=False)
    by_road.to_csv(args.out_dir / "impacts_by_road.csv")
    stats = {"ride": ride, "summary": s, "wobble_ratio": WOBBLE_RATIO,
             "road_match_m": ROAD_MATCH_M, "hotspot_radius_m": HOTSPOT_RADIUS_M,
             "threshold_g": args.threshold_g}
    (args.out_dir / "impact_stats.json").write_text(
        json.dumps(stats, indent=2, default=lambda o: None if pd.isna(o) else float(o)))
    write_html(args.out_dir / "impact_report.html", ride, s, impacts, by_band, by_road, hs,
               figs, args.threshold_g)

    print(json.dumps({**ride, **{k: (round(v, 3) if isinstance(v, float) else v)
                                 for k, v in s.items()}}, indent=1, default=float))
    print("\nBy severity band:\n", by_band.to_string())
    print("\nBy road:\n", by_road.round(2).to_string())
    print("\nHotspots:\n", hs.round(5).to_string())


if __name__ == "__main__":
    main()
