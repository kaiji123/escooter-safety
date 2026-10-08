"""
Figures and numbers for Part A of the paper (measured impacts, all recordings).

Main paper (combined data):
    paper/figures/fig_a4_map.png          routes of all rides, impacts by severity, spots hit
                                          on 2+ rides (start and end of each route trimmed)
    paper/figures/fig_a2_severity.png     distribution of impact peaks, all rides
    paper/figures/fig_a3_roads.png        impacts per km by road, pooled and per ride
    paper/figures/fig_a1_walk_onset.png   copy of the ride-to-walk transition (sensor check)
    paper/figures/part_a_numbers.json     every number quoted in the Part A text
Appendix (individual recordings):
    paper/figures/appendix/<recording>_*.png   copies of each recording's trace, severity,
                                          roads and activity-timeline figures

Inputs: outputs/combined/ (combined_outputs.py, spot_links.py), outputs/recordings/<rec>/
(impact_map.py, impact_report.py, fms_compare.py), outputs/sensor_validity/.

Basemap: streets, paths, parks and water drawn from OpenStreetMap data (ODbL,
"(c) OpenStreetMap contributors"), downloaded once through the Overpass API and cached in
data/osm_paper_basemap.json (the cache stores its query; a changed area downloads again).
Vector data rather than web map tiles: clear licence for publication and sharp at any size.

Privacy: the published map trims TRIM_M metres from the start and end of every route, so
the figures do not show where rides began or ended. Impacts inside the trimmed parts are
still counted in all statistics but are not drawn.

Usage
    python scripts/paper_part_a.py
"""

import json
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import matplotlib
import matplotlib.text
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import impact_map as im                      # noqa: E402
import impact_report as ir                   # noqa: E402

OUT = Path("paper/figures")
APP = OUT / "appendix"
COMB = Path("outputs/combined")
RECS = Path("outputs/recordings")
RAW = Path("data/raw")
TRIM_M = 200.0                     # privacy: metres hidden at each end of each route
BASEMAP_CACHE = Path("data/osm_paper_basemap.json")
BASEMAP_PAD = 0.004                # degrees around the impacts downloaded for the basemap
MAJOR = {"trunk", "primary", "secondary", "tertiary", "trunk_link", "primary_link",
         "secondary_link", "tertiary_link"}
MINOR = {"residential", "unclassified", "living_street", "service", "pedestrian"}
PATHS = {"cycleway", "footway", "path", "bridleway", "track", "steps"}
LABEL_ROADS = {"Marston Road", "Headington Road", "Old Road", "Morrell Avenue",
               "London Road", "Cheney Lane", "Headley Way", "Marston Ferry Road",
               "Cowley Road", "Iffley Road", "St Clement's Street"}
INK, MUTED, GRID = "#222222", "#6b6b6b", "#ececec"
ROUTE = "#b5b4ae"
RIDE_MARKERS = {0: "o", 1: "s", 2: "^"}      # identity of rides in per-ride dots


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#bbbbbb")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def short(rec):
    return {"rec01": "Ride 1", "rec02": "Ride 2", "rec03": "Ride 3"}[rec[-5:]]


def trimmed_track(rec):
    _, _, _, _, _, loc = im.load_inputs(RAW / rec)
    lat, lon = loc["latitude"].to_numpy(), loc["longitude"].to_numpy()
    x, y = ir.to_metres(lat, lon, lat.mean(), lon.mean())
    d = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]
    keep = (d >= TRIM_M) & (d <= d[-1] - TRIM_M)
    return lat[keep], lon[keep], (lat[~keep], lon[~keep])


def fetch_basemap(s_, w, n, e):
    """OSM roads, paths, parks and water in the box (cached; see module docstring)."""
    q = (f"[out:json][timeout:90];("
         f'way["highway"]({s_:.4f},{w:.4f},{n:.4f},{e:.4f});'
         f'way["leisure"~"^(park|garden|recreation_ground|pitch)$"]({s_:.4f},{w:.4f},{n:.4f},{e:.4f});'
         f'way["landuse"~"^(grass|meadow|recreation_ground|cemetery)$"]({s_:.4f},{w:.4f},{n:.4f},{e:.4f});'
         f'way["natural"="water"]({s_:.4f},{w:.4f},{n:.4f},{e:.4f});'
         f'way["waterway"~"^(river|stream|canal)$"]({s_:.4f},{w:.4f},{n:.4f},{e:.4f});'
         f");out geom tags;")
    if BASEMAP_CACHE.exists():
        cached = json.loads(BASEMAP_CACHE.read_text())
        if cached.get("_query") == q:
            return cached
    last = None
    for url in ir.OVERPASS_URLS:
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                                         headers={"User-Agent": "escooter-safety-research (student project)"})
            data = json.load(urllib.request.urlopen(req, timeout=120))
            break
        except Exception as err:
            last = err
    else:
        raise RuntimeError(f"Could not download the basemap: {last}")
    data["_query"] = q
    BASEMAP_CACHE.write_text(json.dumps(data))
    return data


def draw_basemap(ax, data):
    """Parks and water as fills, roads and paths as lines, a few road names."""
    labels = {}
    for el in data["elements"]:
        g = el.get("geometry")
        if not g:
            continue
        lon = np.array([p["lon"] for p in g]); lat = np.array([p["lat"] for p in g])
        t = el.get("tags", {})
        if t.get("natural") == "water" or t.get("waterway"):
            if t.get("waterway"):
                ax.plot(lon, lat, color="#bcd3ea", lw=2.2, zorder=0.2, solid_capstyle="round")
            else:
                ax.fill(lon, lat, color="#d6e5f3", lw=0, zorder=0.1)
        elif "leisure" in t or "landuse" in t:
            ax.fill(lon, lat, color="#e7efe1", lw=0, zorder=0.1)
        elif "highway" in t:
            h = t["highway"]
            if h in MAJOR:
                ax.plot(lon, lat, color="#cfcdc6", lw=1.8, zorder=0.4, solid_capstyle="round")
            elif h in MINOR:
                ax.plot(lon, lat, color="#e0dfda", lw=0.9, zorder=0.3, solid_capstyle="round")
            elif h in PATHS:
                ax.plot(lon, lat, color="#e6e5e1", lw=0.5, zorder=0.25, ls=(0, (2, 1.5)))
            name = t.get("name")
            if name in LABEL_ROADS and len(lon) >= 2:
                length = np.hypot(np.diff(lon), np.diff(lat)).sum()
                if length > labels.get(name, (0,))[0]:
                    labels[name] = (length, lon, lat)
    return labels


def label_roads(ax, fig, labels, offset_pt=8.0):
    """One label per road name, on its longest visible way, rotated along the road and
    shifted offset_pt sideways so it sits beside the road (and the ridden route), not on it."""
    from matplotlib.transforms import offset_copy
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    for name, (_, lon, lat) in labels.items():
        inside = (lon > x0) & (lon < x1) & (lat > y0) & (lat < y1)
        if inside.sum() < 2:
            continue
        lo, la = lon[inside], lat[inside]
        k = len(lo) // 2
        k2 = min(k + 1, len(lo) - 1); k1 = max(k2 - 2, 0)
        p1, p2 = ax.transData.transform([(lo[k1], la[k1]), (lo[k2], la[k2])])
        ang = np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        a = np.radians(ang)
        shift = offset_copy(ax.transData, fig=fig, x=-np.sin(a) * offset_pt, y=np.cos(a) * offset_pt,
                            units="points")
        ax.text(lo[k], la[k], name, fontsize=6.5, color="#6b6b6b", style="italic", rotation=ang,
                rotation_mode="anchor", ha="center", va="center", zorder=0.6, transform=shift,
                path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])


def place_labels(ax, fig, spots):
    """Spot labels with leader lines. Each label goes to the first candidate offset whose
    box overlaps neither an earlier label nor any spot circle (greedy)."""
    from matplotlib.transforms import Bbox
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    # spot circles (drawn with s=420 points^2, i.e. ~11.6 pt radius) as obstacles
    rad = np.sqrt(420) / 2 * fig.dpi / 72
    centres = ax.transData.transform(np.column_stack([spots["lon"], spots["lat"]]))
    placed = [Bbox.from_extents(x - rad, y - rad, x + rad, y + rad) for x, y in centres]
    cands = [(d * np.cos(a), d * np.sin(a)) for d in (26, 38, 52)
             for a in np.radians([30, -30, 150, -150, 0, 180, 90, -90, 60, -60, 120, -120])]
    for sp in spots.sort_values("lat").itertuples():
        for dx, dy in cands:
            t = ax.annotate(sp.spot, (sp.lon, sp.lat), xytext=(dx, dy), textcoords="offset points",
                            fontsize=8, color=INK, zorder=5, ha="center", va="center",
                            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7, shrinkA=1, shrinkB=12))
            # text box only (an Annotation's own extent includes its leader line);
            # update_positions applies the offset, which otherwise happens only at draw time
            t.update_positions(r)
            bb = matplotlib.text.Text.get_window_extent(t, r).expanded(1.2, 1.3)
            if not any(bb.overlaps(o) for o in placed):
                placed.append(bb)
                break
            t.remove()


def trimmed_points(imps):
    """GPS points in the trimmed (hidden) start and end of every route."""
    hid = [np.column_stack(trimmed_track(rec)[2]) for rec in sorted(imps["recording"].unique())]
    hid = [h for h in hid if len(h)]
    return np.concatenate(hid) if hid else np.empty((0, 2))


def hidden_impacts(imps, hid, radius_m=15):
    """True for impacts within radius_m of a trimmed route end (privacy: not drawn/listed)."""
    if not len(hid):
        return pd.Series(False, index=imps.index)
    def near(r):
        x, y = ir.to_metres(hid[:, 0], hid[:, 1], r["lat"], r["lon"])
        return np.hypot(x, y).min() < radius_m
    return imps.apply(near, axis=1)


def hidden_spots(spots, imps, hidden):
    """Spot names (P..) containing at least one hidden impact. Spots are matched to the
    pooled clusters (hotspot_all) by their centre, which is the cluster mean."""
    cent = imps.groupby("hotspot_all")[["lat", "lon"]].mean()
    hid_cl = set(imps.loc[hidden, "hotspot_all"])
    out = set()
    for r in spots.itertuples():
        d = np.hypot((cent["lat"] - r.lat) * 111320,
                     (cent["lon"] - r.lon) * 111320 * np.cos(np.radians(r.lat)))
        if d.idxmin() in hid_cl:
            out.add(r.spot)
    return out


def tex_url(u):
    """URL safe inside \\href in a LaTeX table."""
    return u.replace("\\", "/").replace("%", "\\%").replace("#", "\\#").replace("&", "\\&")


TIER_HEAD = {1: "Hit on 2+ separate rides", 2: "2+ impacts on one ride", 3: "Single impact"}


def _tex(text):
    """Escape plain text for LaTeX."""
    for a, b in (("\\", "/"), ("&", "\\&"), ("%", "\\%"), ("#", "\\#"), ("_", "\\_")):
        text = text.replace(a, b)
    return text


def _fms_tex(r):
    """FixMyStreet cell, worded as on spot_links.html."""
    d = r.fms_nearest_recent_m
    if d is None or (isinstance(d, float) and np.isnan(d)) or d == "":
        return "\\textcolor{gray}{not compared}"
    d = float(d)
    if d == float("inf"):
        return "\\textcolor{gray}{none in area}"
    link = f"\\href{{{tex_url(str(r.fms_url))}}}{{{d:.0f} m}}"
    state = _tex(str(r.fms_state)).lower()
    if d <= 25:
        return f"report {link} ({state})"
    return f"\\textcolor{{gray}}{{none $\\leq$ 25 m (nearest {link})}}"


def spot_table_tex(spots, hide, path):
    """Appendix table of spots in the style of outputs/combined/spot_links.html: one block
    per tier (heading + its own table with header row), clickable Street View / Map /
    Mapillary links, FixMyStreet status, location and events. Landscape pages. A tier
    heading only starts where there is room for it and a few rows (needspace); fixed
    column widths keep the tiers aligned. Spots in the trimmed route ends are not listed."""
    # QR column (print): Street View link, 13 mm, error-correction level L (largest modules)
    spec = ("@{}p{9mm} >{\\raggedleft\\arraybackslash}p{11mm} >{\\raggedleft\\arraybackslash}p{8mm} "
            ">{\\raggedleft\\arraybackslash}p{9mm} p{20mm} p{38mm} p{36mm} >{\\raggedright\\arraybackslash}p{31mm} "
            ">{\\raggedright\\arraybackslash}p{33mm} >{\\centering\\arraybackslash}p{14mm}@{}")
    cols = ("Spot & Impacts & Rides & Max g & Road & Open & FixMyStreet (recent) & "
            "Location & Events (recording\\#impact) & Scan \\\\")
    hidden_list = ", ".join(sorted(hide, key=lambda x: int(x[1:])))
    caption = ("Impact spots for the visual check, most important first, as in the project's "
               "spot list. Links open Google Street View at the spot facing the direction of travel "
               "(tilted towards the road), a Google Maps pin, and Mapillary imagery. On paper, scan the "
               "QR code to open the same Street View, or enter the coordinates in any map. FixMyStreet: nearest "
               "road-surface report made in the 365 days before the ride (within 25 m, or the nearest). "
               f"Spots {hidden_list} lie in the hidden first or last 200 m of a route and are not listed, "
               "for privacy; they are included in all counts and in the tier totals.")
    out = ["% Generated by scripts/paper_part_a.py (spot_table_tex) from outputs/combined/spot_links.csv;",
           "% do not edit by hand. Styled after outputs/combined/spot_links.html.",
           "\\begin{landscape}",
           "\\footnotesize\\arrayrulecolor{rulegray}",
           "\\setlength{\\LTpre}{3pt}\\setlength{\\LTpost}{8pt}",
           f"\\captionof{{table}}{{{caption}}}\\label{{tab:C1}}",
           "\\vspace{6pt}",
           ""]
    for tier, g in spots.groupby("tier"):
        n_all = int((spots["tier"] == tier).sum())
        g = g[~g["spot"].isin(hide)]
        out += ([] if tier == spots["tier"].min() else [f"\\needspace{{9\\baselineskip}}"]) + [
                f"\\noindent{{\\normalsize\\bfseries Tier {tier}: {TIER_HEAD[tier]} ({n_all})}}\\par\\nopagebreak",
                f"\\begin{{longtable}}{{{spec}}}",
                "\\toprule", cols, "\\midrule", "\\endfirsthead",
                "\\toprule", cols, "\\midrule", "\\endhead"]
        for r in g.itertuples():
            links = (f"\\href{{{tex_url(r.google_streetview_url)}}}{{Street View}}\\,\\textperiodcentered\\, "
                     f"\\href{{{tex_url(r.google_maps_url)}}}{{Map}}\\,\\textperiodcentered\\, "
                     f"\\href{{{tex_url(r.mapillary_url)}}}{{Mapillary}}")
            lat_s, lon_s = (f"{v:.5f}".replace("-", "−") for v in (r.lat, r.lon))
            loc = f"\\textcolor{{gray}}{{{lat_s}, {lon_s} \\textperiodcentered{{}} \\mbox{{facing {r.heading_deg:.0f}°}}}}"
            ev = f"\\textcolor{{gray}}{{{_tex(r.events)}}}"
            qr = (f"\\raisebox{{-0.92\\height}}{{\\qrcode[height=13mm,level=L,nolink]"
                  f"{{{tex_url(r.google_streetview_url)}}}}}")
            out.append(f"\\textbf{{{r.spot}}} & {r.impacts} & {r.rides_hitting} & {r.max_g:.2f} & "
                       f"{_tex(r.road)} & {links} & {_fms_tex(r)} & {loc} & {ev} & {qr} \\\\ "
                       f"\\specialrule{{0.2pt}}{{1pt}}{{1pt}}")
        out += ["\\end{longtable}", ""]
    out += ["\\arrayrulecolor{black}", "\\end{landscape}", ""]
    path.write_text("\n".join(out), encoding="utf-8")
    return int((~spots["spot"].isin(hide)).sum())


def fig_map(imps, spots, path):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    osm = fetch_basemap(imps["lat"].min() - BASEMAP_PAD, imps["lon"].min() - BASEMAP_PAD,
                        imps["lat"].max() + BASEMAP_PAD, imps["lon"].max() + BASEMAP_PAD)
    road_labels = draw_basemap(ax, osm)
    hidden = []
    for rec in sorted(imps["recording"].unique()):
        la, lo, h = trimmed_track(rec)
        ax.plot(lo, la, color="#6b6b6b", lw=1.5, solid_capstyle="round", zorder=1)
        hidden.append(h)
    # drop impacts that lie within the trimmed ends (privacy)
    hid = np.concatenate([np.column_stack(h) for h in hidden if len(h[0])]) if hidden else np.empty((0, 2))
    def is_hidden(r):
        if not len(hid):
            return False
        x, y = ir.to_metres(hid[:, 0], hid[:, 1], r["lat"], r["lon"])
        return np.hypot(x, y).min() < 15
    shown = imps[~imps.apply(is_hidden, axis=1)].sort_values("peak_abs_g")
    for lo_g, label, colour in im.SEVERITY_BANDS:
        hi_g = next((b[0] for b in im.SEVERITY_BANDS if b[0] > lo_g), 99)
        s = shown[(shown["peak_abs_g"] >= lo_g) & (shown["peak_abs_g"] < hi_g)]
        ax.scatter(s["lon"], s["lat"], s=18 + 22 * (s["peak_abs_g"] - 1), color=colour,
                   edgecolor="white", linewidth=0.8, zorder=3, label=f"{label} ({len(s)})")
    t1 = spots[(spots["tier"] == 1) & ~spots["spot"].isin(hidden_spots(spots, imps, hidden_impacts(imps, hid)))]
    ax.scatter(t1["lon"], t1["lat"], s=420, facecolor="none", edgecolor=INK, linewidth=1.1,
               linestyle=(0, (3, 2)), zorder=4, label="Spot hit on 2+ rides")
    lat0 = imps["lat"].mean()
    ax.set_aspect(1 / np.cos(np.radians(lat0)))
    pad = 0.0012
    ax.set_xlim(imps["lon"].min() - pad, imps["lon"].max() + pad)
    ax.set_ylim(imps["lat"].min() - pad, imps["lat"].max() + pad)
    ax.set_xticks([]), ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    # scale bar: 200 m
    x0, y0 = ax.get_xlim()[0] + 0.0004, ax.get_ylim()[0] + 0.0002
    dlon = 200 / (111320 * np.cos(np.radians(lat0)))
    ax.plot([x0 + 0.0005, x0 + 0.0005 + dlon], [y0 + 0.0004] * 2, color=INK, lw=2)
    ax.text(x0 + 0.0005 + dlon / 2, y0 + 0.0006, "200 m", ha="center", fontsize=8, color=INK)
    ax.plot([], [], color="#6b6b6b", lw=1.5, label="Ridden route")
    leg = ax.legend(frameon=True, fontsize=8, loc="upper left", title="Impact peak (number shown)",
                    title_fontsize=8, framealpha=0.9, edgecolor="none")
    leg.set_zorder(6)
    ax.text(0.995, 0.005, "Map data \u00a9 OpenStreetMap contributors", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=6, color=MUTED, zorder=6)
    fig.tight_layout()
    label_roads(ax, fig, road_labels)
    place_labels(ax, fig, t1)      # after the layout is final, so measured positions hold
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return int(len(imps) - len(shown))


def fig_severity(imps, path):
    g = imps["peak_abs_g"]
    bins = np.r_[np.arange(1.0, 3.01, 0.1), 7.0]
    counts, _ = np.histogram(np.clip(g, None, 3.05), bins=np.r_[np.arange(1.0, 3.01, 0.1), 3.1])
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    centres = np.r_[np.arange(1.05, 3.0, 0.1), 3.05]
    ax.bar(centres, counts, width=0.085, color="#2a78d6")
    ax.set_xticks([1.0, 1.5, 2.0, 2.5, 3.05], ["1.0", "1.5", "2.0", "2.5", "> 3"])
    ax.axvline(g.median(), color=INK, lw=1, ls=":")
    ax.text(g.median() + 0.03, counts.max() * 0.95, f"median {g.median():.2f} g", fontsize=8.5, color=INK)
    ax.set_xlabel("Peak vertical acceleration of impact (g)")
    ax.set_ylabel("Impacts")
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_roads(by_road, path):
    roads = [r for r in by_road.index if not np.isnan(by_road.loc[r, "pooled per km"])]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    y = np.arange(len(roads))[::-1]
    ax.barh(y, by_road.loc[roads, "pooled per km"], height=0.55, color="#2a78d6", label="All rides")
    rec_cols = [c for c in by_road.columns if c.endswith(" per km") and not c.startswith("pooled")]
    for i, c in enumerate(rec_cols):
        ax.scatter(by_road.loc[roads, c], y, marker=RIDE_MARKERS[i], s=34, color=INK,
                   facecolor="white", linewidth=1.1, zorder=3, label=short(c.split(" ")[0]))
    ax.set_yticks(y, [f"{r} ({by_road.loc[r, 'pooled km']:.2f} km)" for r in roads], fontsize=9)
    ax.set_xlabel("Impacts per km ridden")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_speed(imps, path, cluster_min=10, ylim=(0.95, 3.25)):
    """Speed at impact vs peak g, all rides; impacts in spots of >= cluster_min impacts
    highlighted (they drive the pooled correlation); values above ylim[1] drawn at the
    top edge with their value."""
    big = imps["hotspot_all"].map(imps["hotspot_all"].value_counts()) >= cluster_min
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for i, rec in enumerate(sorted(imps["recording"].unique())):
        for in_cl, colour, lab in ((False, "#2a78d6", short(rec)),
                                   (True, "#eb6834", None)):
            d = imps[(imps["recording"] == rec) & (big == in_cl)]
            y = d["peak_abs_g"].clip(upper=ylim[1] - 0.05)
            ax.scatter(d["speed_kmh"], y, marker=RIDE_MARKERS[i], s=30, color=colour,
                       edgecolor="white", linewidth=0.6, zorder=3, label=lab)
    for r in imps[imps["peak_abs_g"] > ylim[1]].itertuples():
        ax.annotate(f"{r.peak_abs_g:.2f} g", (r.speed_kmh, ylim[1] - 0.05), xytext=(6, -2),
                    textcoords="offset points", fontsize=8, color=INK, va="center")
    ax.scatter([], [], marker="o", s=30, color="#eb6834", edgecolor="white",
               label=f"in spots of {cluster_min}+ impacts (P3, P4)")
    ax.set_ylim(*ylim)
    gate = im.MIN_SPEED_MS * 3.6
    ax.axvline(gate, color=MUTED, lw=0.9, ls=":")
    ax.text(gate - 0.12, ylim[0] + 0.04, "speed rule: none counted below", fontsize=7.5, color=MUTED,
            va="bottom", ha="right", rotation=90)
    ax.set_xlim(left=gate - 1.2)
    ax.set_xlabel("GPS speed at impact (km/h)")
    ax.set_ylabel("Peak vertical acceleration (g)")
    ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return int(big.sum())


def _near_hidden(lat, lon, hid, radius_m=15):
    """Boolean array: points within radius_m of a trimmed (hidden) route end."""
    lat, lon = np.asarray(lat), np.asarray(lon)
    if not len(hid) or not len(lat):
        return np.zeros(len(lat), bool)
    out = np.zeros(len(lat), bool)
    for i, (a, b) in enumerate(zip(lat, lon)):
        x, y = ir.to_metres(hid[:, 0], hid[:, 1], a, b)
        out[i] = np.hypot(x, y).min() < radius_m
    return out


def _map_frame(ax, lats, lons, pad=0.0010):
    lat0 = float(np.mean(lats))
    ax.set_aspect(1 / np.cos(np.radians(lat0)))
    ax.set_xlim(min(lons) - pad, max(lons) + pad)
    ax.set_ylim(min(lats) - pad, max(lats) + pad)
    ax.set_xticks([]), ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    x0, y0 = ax.get_xlim()[0] + 0.0004, ax.get_ylim()[0] + 0.0002
    dlon = 200 / (111320 * np.cos(np.radians(lat0)))
    ax.plot([x0 + 0.0003, x0 + 0.0003 + dlon], [y0 + 0.0004] * 2, color=INK, lw=2, zorder=6)
    ax.text(x0 + 0.0003 + dlon / 2, y0 + 0.0006, "200 m", ha="center", fontsize=8, color=INK, zorder=6)
    ax.text(0.995, 0.005, "Map data © OpenStreetMap contributors", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=6, color=MUTED, zorder=6)


def ride_maps(imps, osm, hid, out_dir):
    """Per-recording static maps for Appendix A: (1) impacts by severity on the ridden
    route, with detected walking (dashed orange); (2) the same route with that ride's
    recent FixMyStreet road-surface reports. Same privacy trimming as the main map:
    route ends, and impacts or reports near them, are not drawn."""
    written = []
    for rec in sorted(imps["recording"].unique()):
        la, lo, _ = trimmed_track(rec)
        d = imps[imps["recording"] == rec]
        d = d[~_near_hidden(d["lat"], d["lon"], hid)]
        # walking bouts (ride 2): GPS points of each bout, minus hidden parts
        _, _, _, _, _, loc = im.load_inputs(RAW / rec)
        walk_pts = []
        for a, b, *_ in im.walking_bouts(Path("outputs/sensor_validity/walking_onsets.csv"), rec):
            g = loc[(loc["seconds_elapsed"] >= a) & (loc["seconds_elapsed"] <= b)]
            keep = ~_near_hidden(g["latitude"], g["longitude"], hid, radius_m=30)
            walk_pts.append(g[keep])
        # ---- (1) impacts map
        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        labels = draw_basemap(ax, osm)
        ax.plot(lo, la, color="#6b6b6b", lw=1.5, solid_capstyle="round", zorder=1, label="Ridden route")
        for w in walk_pts:
            if len(w) > 1:
                ax.plot(w["longitude"], w["latitude"], color=im.WALK_COLOUR, lw=2, ls=(0, (4, 3)), zorder=2,
                        label="Walking (detected)" if w is walk_pts[0] else None)
        d = d.sort_values("peak_abs_g")
        for lo_g, lab, colour in im.SEVERITY_BANDS:
            hi_g = next((b[0] for b in im.SEVERITY_BANDS if b[0] > lo_g), 99)
            s_ = d[(d["peak_abs_g"] >= lo_g) & (d["peak_abs_g"] < hi_g)]
            ax.scatter(s_["lon"], s_["lat"], s=18 + 22 * (s_["peak_abs_g"] - 1), color=colour,
                       edgecolor="white", linewidth=0.8, zorder=3, label=f"{lab} ({len(s_)})")
        lats = list(la) + list(d["lat"]) + [p for w in walk_pts for p in w["latitude"]]
        lons = list(lo) + list(d["lon"]) + [p for w in walk_pts for p in w["longitude"]]
        _map_frame(ax, lats, lons)
        leg = ax.legend(frameon=True, fontsize=8, loc="best", framealpha=0.9, edgecolor="none",
                        title="Impact peak (number shown)", title_fontsize=8)
        leg.set_zorder(7)
        fig.tight_layout()
        label_roads(ax, fig, labels)
        p1 = out_dir / f"{rec}_impact_map.png"
        fig.savefig(p1, dpi=200, bbox_inches="tight")
        plt.close(fig)
        # ---- (2) FixMyStreet map
        rep = pd.read_csv(RECS / rec / "fms_reports_on_route.csv")
        rep = rep[rep["recent"].astype(bool)]
        rep = rep[~_near_hidden(rep["lat"], rep["lon"], hid, radius_m=30)]
        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        labels = draw_basemap(ax, osm)
        ax.plot(lo, la, color="#6b6b6b", lw=1.5, solid_capstyle="round", zorder=1, label="Ridden route")
        ax.scatter(d["lon"], d["lat"], s=16, color="#2a78d6", edgecolor="white", linewidth=0.6, zorder=3,
                   label=f"Impact ({len(d)})")
        for state, face in (("Closed", "white"), ("Fixed", INK)):
            r_ = rep[rep["state"] == state]
            ax.scatter(r_["lon"], r_["lat"], marker="s", s=34, facecolor=face, edgecolor=INK, linewidth=1.0,
                       zorder=4, label=f"FixMyStreet report, {state.lower()} ({len(r_)})")
        _map_frame(ax, lats, lons)
        leg = ax.legend(frameon=True, fontsize=8, loc="best", framealpha=0.9, edgecolor="none")
        leg.set_zorder(7)
        fig.tight_layout()
        label_roads(ax, fig, labels)
        p2 = out_dir / f"{rec}_fms_map.png"
        fig.savefig(p2, dpi=200, bbox_inches="tight")
        plt.close(fig)
        written += [p1, p2]
    return written


def numbers(imps, summ, by_road, spots, hidden_n):
    recs = sorted(imps["recording"].unique())
    rho, p = spearmanr(imps["speed_kmh"], imps["peak_abs_g"])
    g = imps["peak_abs_g"]
    fms = {}
    for rec in recs:
        f = RECS / rec / "fms_match_rates.csv"
        if f.exists():
            r = pd.read_csv(f).set_index("radius_m").loc[25.0]
            fms[short(rec)] = {"impacts_reported": int(r["impacts_reported"]),
                               "pct_impacts_reported": round(r["pct_impacts_reported"], 1),
                               "pct_route_baseline": round(r["pct_route_baseline"], 1)}
    t1 = spots[spots["tier"] == 1]
    return {
        "per_ride_and_pooled": summ.to_dict(orient="records"),
        "pooled": {
            "impacts": int(len(g)), "median_g": round(float(g.median()), 2),
            "iqr_g": [round(float(g.quantile(.25)), 2), round(float(g.quantile(.75)), 2)],
            "p95_g": round(float(g.quantile(.95)), 2), "max_g": round(float(g.max()), 2),
            "n_le_2_97": int((g <= 2.97).sum()), "n_gt_3": int((g > 3).sum()),
            "n_ge_1_5": int((g >= 1.5).sum()), "n_ge_2": int((g >= 2).sum()),
            "n_wobble": int(imps["marked_wobble"].sum()),
            "n_ge_1_5_and_wobble": int(((g >= 1.5) & imps["marked_wobble"]).sum()),
            "spearman_speed_vs_g": {"rho": round(float(rho), 3), "p": round(float(p), 3)},
            "severity_bands": {lab: int(((g >= lo) & (g < next((b[0] for b in im.SEVERITY_BANDS if b[0] > lo), 99))).sum())
                               for lo, lab, _ in im.SEVERITY_BANDS},
        },
        "spots": {"total": int(len(spots)), "tier_counts": spots["tier"].value_counts().sort_index().to_dict(),
                  "tier1": t1[["spot", "rides_hitting", "impacts", "max_g", "road", "fms_recent_within_25m",
                               "fms_nearest_recent_m", "fms_state"]].to_dict(orient="records"),
                  "tier1_without_recent_fms_25m": int((~t1["fms_recent_within_25m"].astype(bool)).sum())},
        "fms_25m": fms,
        "fms_pooled_reported_25m": int(imps.get("fms_recent_report_within_25m", pd.Series(dtype=bool)).fillna(False).sum()),
        "by_road": by_road.reset_index().to_dict(orient="records"),
        "map_impacts_hidden_by_trim": hidden_n, "map_trim_m": TRIM_M,
    }


def copy_appendix():
    APP.mkdir(parents=True, exist_ok=True)
    for rec_dir in sorted(RECS.iterdir()):
        # per-ride road charts are not copied: they show rates for very short distances
        for f in ("impact_trace.png", "fig_severity_hist.png", "fig_speed_vs_severity.png"):
            if (rec_dir / f).exists():
                shutil.copy2(rec_dir / f, APP / f"{rec_dir.name}_{f}")
        tl = Path("outputs/sensor_validity") / rec_dir.name / "fig_timeline.png"
        if tl.exists():
            shutil.copy2(tl, APP / f"{rec_dir.name}_activity_timeline.png")
        on2 = Path("outputs/sensor_validity") / rec_dir.name / "fig_walk_onset_2.png"
        if on2.exists():   # second walking bout (Appendix B)
            shutil.copy2(on2, APP / f"{rec_dir.name}_walk_onset_2.png")


# Part B key-frame figures (made by scooter_sim.py --keyframes), copied into the paper.
PART_B_FIGURES = {"keyframes_susp_80x600_15kmh.png": "fig_b5_keyframes_sharp.png",
                  "keyframes_susp_edge50_80x600_15kmh.png": "fig_b6_keyframes_edge50.png",
                  # Appendix D (road bumps, exploratory)
                  "keyframes_bump_box_90x600_20kmh.png": "fig_d1_bump_keyframes.png",
                  "keyframes_bump_box_susp_90x300_15kmh.png": "fig_d2_bump_rear_strike.png"}


# Other model figures (Part B main text, Appendices D and E), copied unchanged.
SIM_FIGURES = {
    "wheel_model/fig_schematic.png": "geom_schematic.png",
    "wheel_model/fig_speed_loss.png": "geom_speed_loss.png",
    "wheel_model/fig_impact_velocity.png": "geom_impact_velocity.png",
    "wheel_model/fig_by_pothole_length.png": "geom_by_length.png",
    "scooter_sim/fig_consistency.png": "consistency.png",
    "scooter_sim/fig_rider_lean.png": "sweep_lean_nofork.png",
    "scooter_sim/fig_speed_loss.png": "sweep_speedloss_nofork.png",
    "scooter_sim/fig_handlebar_g.png": "sweep_handlebar_nofork.png",
    "scooter_sim/suspension/fig_rider_lean.png": "sweep_lean_fork.png",
    "scooter_sim/suspension/fig_speed_loss.png": "sweep_speedloss_fork.png",
    "scooter_sim/suspension/fig_handlebar_g.png": "sweep_handlebar_fork.png",
    "scooter_sim/ratio/fig_ratio_first_fall.png": "ratio_first_fall_nofork.png",
    "scooter_sim/ratio/fig_ratio_rear_wheel.png": "ratio_rear_wheel_nofork.png",
    "scooter_sim/suspension/ratio/fig_ratio_first_fall.png": "ratio_first_fall_fork.png",
    "scooter_sim/suspension/ratio/fig_ratio_rear_wheel.png": "ratio_rear_wheel_fork.png",
    "scooter_sim/suspension/soft_edges/fig_edges.png": "soft_edges_fork.png",
    "scooter_sim/bumps/fig_bump_falls.png": "bump_falls_nofork.png",
    "scooter_sim/bumps/fig_bump_vs_pothole.png": "bump_vs_pothole_nofork.png",
    "scooter_sim/bumps/fig_bump_speed_loss.png": "bump_speedloss_nofork.png",
    "scooter_sim/bumps/fig_bump_handlebar_g.png": "bump_handlebar_nofork.png",
    "scooter_sim/suspension/bumps/fig_bump_falls.png": "bump_falls_fork.png",
    "scooter_sim/suspension/bumps/fig_bump_vs_pothole.png": "bump_vs_pothole_fork.png",
    "scooter_sim/suspension/bumps/fig_bump_speed_loss.png": "bump_speedloss_fork.png",
    "scooter_sim/suspension/bumps/fig_bump_handlebar_g.png": "bump_handlebar_fork.png",
}


def copy_part_b():
    src = Path("outputs/scooter_sim/keyframes")
    for a, b in PART_B_FIGURES.items():
        if (src / a).exists():
            shutil.copy2(src / a, OUT / b)
    (OUT / "sim").mkdir(exist_ok=True)
    for a, b in SIM_FIGURES.items():
        if (Path("outputs") / a).exists():
            shutil.copy2(Path("outputs") / a, OUT / "sim" / b)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    copy_part_b()
    imps = pd.read_csv(COMB / "impacts_all.csv")
    summ = pd.read_csv(COMB / "summary.csv")
    by_road = pd.read_csv(COMB / "by_road.csv", index_col=0)
    spots = pd.read_csv(COMB / "spot_links.csv")
    hidden_n = fig_map(imps, spots, OUT / "fig_a4_map.png")
    fig_severity(imps, OUT / "fig_a2_severity.png")
    fig_roads(by_road, OUT / "fig_a3_roads.png")
    n_cl = fig_speed(imps, OUT / "fig_a5_speed.png")
    hid = trimmed_points(imps)
    hide = hidden_spots(spots, imps, hidden_impacts(imps, hid))
    n_listed = spot_table_tex(spots, hide, Path("paper/sections/appendix_spot_links.tex"))
    # per-recording maps for Appendix A (same basemap download as the main map)
    osm = fetch_basemap(imps["lat"].min() - BASEMAP_PAD, imps["lon"].min() - BASEMAP_PAD,
                        imps["lat"].max() + BASEMAP_PAD, imps["lon"].max() + BASEMAP_PAD)
    APP.mkdir(parents=True, exist_ok=True)
    ride_maps(imps, osm, hid, APP)
    shutil.copy2("outputs/sensor_validity/2026-10-07_1037_rec02/fig_walk_onset_1.png",
                 OUT / "fig_a1_walk_onset.png")
    copy_appendix()
    nums = numbers(imps, summ, by_road, spots, hidden_n)
    nums["speed_fig_impacts_in_big_spots"] = n_cl
    nums["spots_hidden_for_privacy"] = sorted(hide, key=lambda x: int(x[1:]))
    nums["spots_listed_in_appendix"] = n_listed
    (OUT / "part_a_numbers.json").write_text(json.dumps(nums, indent=2, default=str))
    print(json.dumps(nums["pooled"], indent=1))
    print("spots:", nums["spots"]["tier_counts"], "tier1 without recent FMS <=25 m:",
          nums["spots"]["tier1_without_recent_fms_25m"])
    print("FMS 25 m:", nums["fms_25m"], "pooled reported:", nums["fms_pooled_reported_25m"])
    print("impacts hidden on map by trimming:", hidden_n)


if __name__ == "__main__":
    main()
