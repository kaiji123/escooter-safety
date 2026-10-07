"""
Compare measured e-scooter impacts with FixMyStreet road-surface reports.

Questions
  1. Measured AND reported: impacts with a road-surface report nearby.
  2. Measured but NEVER reported: impacts with no report nearby (original finding).
  3. Reported but not felt: reports on the ridden route where no impact was measured
     (may be repaired, in another lane, or not severe for a scooter).

FixMyStreet data
  Public report pins (location, title, status, date, category) for the ride's
  bounding box, fetched from fixmystreet.com's map endpoint one road-surface
  category at a time, with a pause between requests. This is a small number of
  requests; for anything larger, ask mySociety for bulk data instead.
  Saved once to data/fixmystreet/reports.csv (with the fetch date) and reused, so
  the analysis is reproducible. Use --refresh to download again.

Matching
  An impact is "reported" if a road-surface report made in the RECENT_DAYS before
  the ride lies within MATCH_RADIUS_M of it. Older reports are excluded from the main
  comparison: the area has reports back to 2009, so dense that ~80% of all points on
  the route lie within 25 m of one, which would make any match meaningless.
  Baseline: every match rate is shown next to the rate for all points along the
  ridden route (moving sections), i.e. what chance alone would give.
  GPS (~10 m) and reporters' pin placement are both approximate, so results are
  also given for 15, 25 and 50 m. A report is "on the route" if it lies within
  ROUTE_RADIUS_M of the ridden GPS track. Report dates are submission dates.

Usage
    python scripts/fms_compare.py --data-dir data/raw/2026-10-03_1830_rec01 --out-dir outputs
"""

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import folium
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import impact_map as im  # noqa: E402
import impact_report as ir  # noqa: E402

# Road-surface categories that can jolt a scooter (Oxfordshire FixMyStreet names).
# Pavement categories are excluded: e-scooters are not allowed on pavements.
FMS_CATEGORIES = ["Pothole", "Potholes and maintenance", "Carriageway Defect",
                  "Roads and Carriageways", "Manhole", "Damaged Gully or Catchpit Ironwork"]
# Two of those categories are catch-alls that also hold e.g. road signs, leaves and
# walls. For them only, a report counts if its title describes the road surface.
MIXED_CATEGORIES = {"Potholes and maintenance", "Roads and Carriageways"}
SURFACE_WORDS = re.compile(
    r"pot ?hole|surface|uneven|hole|asphalt|tarmac|crack|sunk|sink|subsid|collaps|"
    r"rut|bump|broken road|road condition|condition|manhole|cover|drain|gully|grate|"
    r"defect|damage|depression|dip|crumbl|patch|resurfac|ridge|raised|loose|lump|heave|"
    r"undulat", re.I)
# ...unless the title is about something beside the road surface.
NOT_SURFACE_WORDS = re.compile(
    r"\bwall\b|\bsign|fence|railing|bollard|refuge|island|light|bin\b|tree|hedge|kerb|curb",
    re.I)
FMS_URL = "https://www.fixmystreet.com/around"
USER_AGENT = "escooter-safety-research (student project)"
REQUEST_PAUSE_S = 2.0
BBOX_BUFFER_DEG = 0.001       # ~100 m around the ride

MATCH_RADIUS_M = 25.0         # main matching radius impact <-> report
SENSITIVITY_RADII_M = (15.0, 25.0, 50.0)
ROUTE_RADIUS_M = 15.0         # report counts as "on the route" within this of the track
RECENT_DAYS = 365             # "recent" report = created within this many days of the ride

C_REPORT = "#eb6834"          # orange: FixMyStreet report
C_MATCHED = "#2a78d6"         # blue: impact with a report nearby
C_UNREPORTED = "#4a3aa7"      # violet: impact with no report nearby
# (palette validated for colour-vision deficiency; shapes/labels also differ)


# --------------------------------------------------------------------------- fetch
def _get_json(params):
    url = FMS_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return json.load(urllib.request.urlopen(req, timeout=60))


def _parse_created(text, fetched):
    """Report time from list text, e.g. '10:58, Friday' or '02:03, 21 Sep 2026'."""
    m = re.search(r"(\d{1,2}:\d{2}),\s*(\d{1,2} \w{3} \d{4})", text)
    if m:
        return dt.datetime.strptime(f"{m.group(2)} {m.group(1)}", "%d %b %Y %H:%M")
    m = re.search(r"(\d{1,2}:\d{2})\s*today", text)
    if m:
        return dt.datetime.combine(fetched.date(), dt.time.fromisoformat(m.group(1).zfill(5)))
    m = re.search(r"(\d{1,2}:\d{2}),\s*(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", text)
    if m:  # within the last week: most recent such weekday before the fetch date
        target = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
                  "Sunday"].index(m.group(2))
        days_back = (fetched.weekday() - target) % 7 or 7
        day = fetched.date() - dt.timedelta(days=days_back)
        return dt.datetime.combine(day, dt.time.fromisoformat(m.group(1).zfill(5)))
    return None


def _parse_list(list_html, fetched):
    """Report id -> (address, state, created) from the HTML list returned with the pins."""
    out = {}
    for m in re.finditer(r'data-report-id="(\d+)".*?</li>', list_html, re.S):
        block = m.group(0)
        addr = re.search(r'<span class="visuallyhidden">\s*(.*?)\s*</span>', block, re.S)
        small = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
                       (re.search(r"<small>(.*?)</small>", block, re.S) or [None, ""])[1])).strip()
        if addr:
            small = small.replace(re.sub(r"\s+", " ", addr.group(1)).strip(), "").strip()
        state = next((s for s in ("Fixed", "Closed", "Duplicate", "Not responsible",
                                  "Internal referral", "No further action")
                      if small.startswith(s)), "Open")
        out[int(m.group(1))] = (addr.group(1).strip() if addr else "", state,
                                _parse_created(small, fetched))
    return out


def fetch_reports(bbox, cache_path, refresh=False):
    if cache_path.exists() and not refresh:
        return pd.read_csv(cache_path, parse_dates=["created", "fetched"])
    fetched = dt.datetime.now().replace(microsecond=0)
    w, s, e, n = bbox
    rows = []
    for cat in FMS_CATEGORIES:
        page = 1
        while True:
            d = _get_json([("ajax", "1"), ("bbox", f"{w:.4f},{s:.4f},{e:.4f},{n:.4f}"),
                           ("status", "all"), ("show_old_reports", "1"),
                           ("sort", "created-desc"), ("filter_category", cat), ("p", page)])
            meta = _parse_list(d["reports_list"], fetched)
            for lat, lon, colour, rid, title, *_ in d["pins"]:
                addr, state, created = meta.get(int(rid), ("", "", None))
                rows.append({"report_id": int(rid), "category": cat, "title": title,
                             "lat": lat, "lon": lon, "state": state, "created": created,
                             "address": addr, "pin_colour": colour, "fetched": fetched})
            time.sleep(REQUEST_PAUSE_S)
            if 'class="next"' not in d.get("pagination", ""):
                break
            page += 1
        print(f"  {cat}: {sum(r['category'] == cat for r in rows)} reports")
    df = pd.DataFrame(rows).drop_duplicates("report_id")
    df["url"] = "https://www.fixmystreet.com/report/" + df["report_id"].astype(str)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return pd.read_csv(cache_path, parse_dates=["created", "fetched"])


# --------------------------------------------------------------------------- geometry
def pairwise_m(lat1, lon1, lat2, lon2, lat0, lon0):
    x1, y1 = ir.to_metres(lat1, lon1, lat0, lon0)
    x2, y2 = ir.to_metres(lat2, lon2, lat0, lon0)
    return np.hypot(x1[:, None] - x2[None, :], y1[:, None] - y2[None, :])


def dist_to_track_m(lat, lon, track, lat0, lon0):
    """Distance from each point to the ridden track (polyline of GPS positions)."""
    tx, ty = ir.to_metres(track["lat"], track["lon"], lat0, lon0)
    A = np.column_stack([tx[:-1], ty[:-1]])[None]
    AB = np.column_stack([np.diff(tx), np.diff(ty)])[None]
    px, py = ir.to_metres(lat, lon, lat0, lon0)
    P = np.column_stack([px, py])[:, None, :]
    t = np.clip(((P - A) * AB).sum(-1) / np.maximum((AB ** 2).sum(-1), 1e-9), 0, 1)
    return np.linalg.norm(P - (A + t[..., None] * AB), axis=-1).min(1)


# --------------------------------------------------------------------------- analysis
def nearest_dist(lat, lon, sub, lat0, lon0):
    """Distance (m) from each point to the nearest report in sub, and its index."""
    if sub.empty:
        return np.full(len(lat), np.inf), np.zeros(len(lat), dtype=int)
    D = pairwise_m(np.asarray(lat), np.asarray(lon), sub["lat"].to_numpy(),
                   sub["lon"].to_numpy(), lat0, lon0)
    idx = D.argmin(1)
    return D[np.arange(len(idx)), idx], idx


def compare(impacts, reports, track, moving_track, ride_date, osm):
    lat0, lon0 = track["lat"].mean(), track["lon"].mean()
    reports = reports.copy()
    title = reports["title"].fillna("")
    surface = (~reports["category"].isin(MIXED_CATEGORIES)
               | (title.str.contains(SURFACE_WORDS) & ~title.str.contains(NOT_SURFACE_WORDS)))
    print(f"  excluded {int((~surface).sum())} non-surface reports from catch-all categories")
    reports = reports[surface].reset_index(drop=True)
    reports["age_days_at_ride"] = (pd.Timestamp(ride_date) - reports["created"]).dt.days
    reports["recent"] = reports["age_days_at_ride"].between(0, RECENT_DAYS)
    reports["dist_to_route_m"] = dist_to_track_m(reports["lat"], reports["lon"], track, lat0, lon0)
    recent = reports[reports["recent"]].reset_index(drop=True)
    on_route = recent[recent["dist_to_route_m"] <= ROUTE_RADIUS_M].copy()
    on_route["road"], _ = ir.assign_roads(on_route["lat"], on_route["lon"], osm, lat0, lon0)

    imp = impacts.copy()
    d, idx = nearest_dist(imp["lat"], imp["lon"], recent, lat0, lon0)
    imp["nearest_report_m"] = d.round(1)
    for col in ("report_id", "title", "state", "created", "url"):
        imp[f"nearest_report_{col}"] = recent[col].to_numpy()[idx] if len(recent) else None
    imp["reported"] = imp["nearest_report_m"] <= MATCH_RADIUS_M
    d_all, _ = nearest_dist(imp["lat"], imp["lon"], reports, lat0, lon0)
    imp["report_any_date_m"] = d_all.round(1)

    # Baseline: share of all (moving) route points that would count as "reported".
    base_recent, _ = nearest_dist(moving_track["lat"], moving_track["lon"], recent, lat0, lon0)
    base_all, _ = nearest_dist(moving_track["lat"], moving_track["lon"], reports, lat0, lon0)
    sens = pd.DataFrame([{
        "radius_m": r,
        "impacts_reported": int((imp["nearest_report_m"] <= r).sum()),
        "pct_impacts_reported": 100 * (imp["nearest_report_m"] <= r).mean(),
        "pct_route_baseline": 100 * (base_recent <= r).mean(),
        "pct_impacts_any_date": 100 * (imp["report_any_date_m"] <= r).mean(),
        "pct_route_any_date": 100 * (base_all <= r).mean(),
    } for r in SENSITIVITY_RADII_M])

    # Reports on the route: was an impact measured within MATCH_RADIUS_M?
    Dr = pairwise_m(on_route["lat"].to_numpy(), on_route["lon"].to_numpy(),
                    imp["lat"].to_numpy(), imp["lon"].to_numpy(), lat0, lon0)
    on_route["impact_within_radius"] = (Dr <= MATCH_RADIUS_M).any(1) if len(imp) else False

    # Hotspot level (the same clusters as the statistics report)
    hs = (imp.groupby("hotspot")
          .agg(impacts=("event_id", "size"), events=("event_id", lambda s: ", ".join(map(str, s))),
               max_g=("peak_abs_g", "max"), road=("road", "first"), lat=("lat", "mean"),
               lon=("lon", "mean"), reported=("reported", "any"),
               nearest_report_m=("nearest_report_m", "min")))
    hs = hs[hs["impacts"] >= 2].sort_values(["impacts", "max_g"], ascending=False)
    return imp, reports, on_route, hs, sens


# --------------------------------------------------------------------------- outputs
def build_map(track, imp, on_route, label):
    m = folium.Map(location=[track["lat"].mean(), track["lon"].mean()], zoom_start=15,
                   tiles=None, control_scale=True)
    esri = ("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
            "World_Light_Gray_{layer}/MapServer/tile/{{z}}/{{y}}/{{x}}")
    attr = ("Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors"
            " &middot; Reports: FixMyStreet (mySociety)")
    folium.TileLayer(esri.format(layer="Base"), attr=attr, name="Basemap",
                     max_native_zoom=16, max_zoom=19).add_to(m)
    folium.TileLayer(esri.format(layer="Reference"), attr=attr, name="Street names",
                     overlay=True, max_native_zoom=16, max_zoom=19).add_to(m)

    route = folium.FeatureGroup(name="Ridden route")
    folium.PolyLine(track[["lat", "lon"]].to_numpy(), color="#8a8984", weight=3,
                    opacity=0.8).add_to(route)
    route.add_to(m)

    rep = folium.FeatureGroup(name="Reported on FixMyStreet (orange squares)")
    for _, r in on_route.iterrows():
        created = r["created"].strftime("%d %b %Y") if pd.notna(r["created"]) else "unknown"
        popup = (f"<b>FixMyStreet report</b><br>{html.escape(str(r['title']))}<br>"
                 f"Category: {html.escape(r['category'])}<br>"
                 f"Reported {created} &middot; {r['state']}<br>"
                 f"Impact measured within {MATCH_RADIUS_M:g} m: "
                 f"{'yes' if r['impact_within_radius'] else 'no'}<br>"
                 f'<a href="{r["url"]}" target="_blank">Open report</a>')
        folium.RegularPolygonMarker(  # square: distinct from circular impact markers
            [r["lat"], r["lon"]], number_of_sides=4, rotation=45, radius=6,
            color="#ffffff", weight=1.5, fill=True, fill_color=C_REPORT, fill_opacity=0.95,
            tooltip=f"FixMyStreet report: {r['title']}", popup=folium.Popup(popup, max_width=280),
        ).add_to(rep)
    rep.add_to(m)

    hits = folium.FeatureGroup(name="Measured by my sensors (circles)")
    for _, r in imp.sort_values("peak_abs_g").iterrows():
        col = C_MATCHED if r["reported"] else C_UNREPORTED
        status = (f"Report {r['nearest_report_m']:.0f} m away: "
                  f"{html.escape(str(r['nearest_report_title']))}" if r["reported"]
                  else f"<b>No report within {MATCH_RADIUS_M:g} m</b> "
                       f"(nearest {r['nearest_report_m']:.0f} m)")
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=5 + 4 * (r["peak_abs_g"] - 1.0),
            color="#ffffff", weight=2, fill=True, fill_color=col, fill_opacity=0.95,
            tooltip=f"Impact {r['event_id']}: {r['peak_abs_g']:.2f} g"
                    f" ({'reported' if r['reported'] else 'not reported'})",
            popup=folium.Popup(f"<b>Impact {r['event_id']}</b> &middot; {r['road']}<br>"
                               f"{r['peak_abs_g']:.2f} g at {r['speed_kmh']:.0f} km/h<br>{status}",
                               max_width=280),
        ).add_to(hits)
    hits.add_to(m)

    def dot(c, square=False):
        shape = "border-radius:2px;transform:rotate(45deg)" if square else "border-radius:50%"
        return (f'<span style="display:inline-block;width:11px;height:11px;{shape};background:{c};'
                f'border:2px solid #fff;box-shadow:0 0 0 1px #999;margin:0 7px 0 2px;'
                f'vertical-align:middle"></span>')
    legend = f"""
    <div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:#fff;
         padding:10px 12px;border-radius:6px;font:13px/1.6 sans-serif;color:#222;
         box-shadow:0 1px 4px rgba(0,0,0,.3)">
      <b>Measured impacts vs FixMyStreet reports</b>
      <div style="margin-top:4px;color:#444">Reported on FixMyStreet</div>
      <div>{dot(C_REPORT, True)}Road-surface problem reported by the public</div>
      <div style="margin-top:4px;color:#444">Measured by my sensors (impact &ge; {im.THRESHOLD_G:g} g)</div>
      <div>{dot(C_MATCHED)}Impact <i>with</i> a FixMyStreet report within {MATCH_RADIUS_M:g} m</div>
      <div>{dot(C_UNREPORTED)}Impact with <i>no</i> FixMyStreet report nearby</div>
      <div style="color:#666;margin-top:4px">Reports made in the {RECENT_DAYS} days before the ride<br>
      Circle size = impact strength<br>{html.escape(label)}</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[track["lat"].min(), track["lon"].min()],
                  [track["lat"].max(), track["lon"].max()]], padding=(30, 30))
    return m


def write_html(path, ride_label, ride_date, imp, reports, on_route, hs, sens, fetched):
    n = len(imp)
    n_rep = int(imp["reported"].sum())
    n_unrep = n - n_rep
    strong = imp[imp["peak_abs_g"] >= 1.5]
    strong_unrep = int((~strong["reported"]).sum())
    n_hs = len(hs)
    hs_unrep = int((~hs["reported"]).sum())
    n_route = len(on_route)
    route_felt = int(on_route["impact_within_radius"].sum())

    main = sens.set_index("radius_m").loc[MATCH_RADIUS_M]
    tiles = [(f"{n_unrep} of {n}", f"impacts with no recent report within {MATCH_RADIUS_M:g} m"),
             (f"{strong_unrep} of {len(strong)}", "strong impacts (≥ 1.5 g) unreported"),
             (f"{hs_unrep} of {n_hs}", "hotspots with no recent report"),
             (f"{route_felt} of {n_route}", "recent reports on route where an impact was measured")]
    tiles_html = "".join(f'<div class="tile"><div class="v">{v}</div><div class="k">{k}</div></div>'
                         for v, k in tiles)

    by_road = (imp.groupby("road").agg(impacts=("event_id", "size"),
                                       reported=("reported", "sum"))
               .assign(unreported=lambda d: d["impacts"] - d["reported"]))
    route_by_road = on_route.groupby("road").agg(reports_on_route=("report_id", "size"),
                                                  impact_measured=("impact_within_radius", "sum"))
    by_road = by_road.join(route_by_road, how="outer").fillna(0).astype(int)
    by_road.index.name = "Road"
    by_road.columns = ["Impacts", "Reported", "Not reported", "Reports on route",
                       "…with impact measured"]

    route_states = on_route["state"].value_counts().rename_axis("Current status").to_frame("Reports")
    route_cats = on_route["category"].value_counts().rename_axis("Category").to_frame("Reports")

    hs_t = hs[["road", "impacts", "events", "max_g", "reported", "nearest_report_m"]].copy()
    hs_t["reported"] = hs_t["reported"].map({True: "yes", False: "NO"})
    hs_t.columns = ["Road", "Impacts", "Event IDs", "Max g", "Reported", "Nearest report (m)"]
    hs_t.index.name = "Hotspot"

    unrep = imp[~imp["reported"]].sort_values("peak_abs_g", ascending=False)
    unrep_t = unrep[["event_id", "road", "peak_abs_g", "speed_kmh", "nearest_report_m",
                     "lat", "lon"]].rename(columns={
        "event_id": "#", "road": "Road", "peak_abs_g": "Peak g", "speed_kmh": "km/h",
        "nearest_report_m": "Nearest report (m)", "lat": "Lat", "lon": "Lon"})
    rep_t = imp[imp["reported"]][["event_id", "road", "peak_abs_g", "nearest_report_m",
                                  "nearest_report_title", "nearest_report_state",
                                  "nearest_report_created"]].copy()
    rep_t["nearest_report_created"] = pd.to_datetime(rep_t["nearest_report_created"]).dt.strftime("%d %b %Y")
    rep_t.columns = ["#", "Road", "Peak g", "Distance (m)", "Report", "Status", "Reported on"]

    sens_t = sens.set_index("radius_m")
    sens_t.index.name = "Matching radius (m)"
    sens_t.columns = ["Impacts reported", "% impacts reported", "% route points (baseline)",
                      "% impacts, any date", "% route points, any date"]
    pct = "{:.0f}%"

    strong_txt = (f"<b>all {len(strong)}</b>" if strong_unrep == len(strong)
                  else f"<b>{strong_unrep} of {len(strong)}</b>")
    # Reported hotspots, described with the report they matched (e.g. marked "Fixed").
    rep_hs = []
    for _, h in hs[hs["reported"]].iterrows():
        ev = imp[(imp["hotspot"] == h.name) & imp["reported"]].iloc[0]
        when = pd.to_datetime(ev["nearest_report_created"])
        where = "a road outside the study roads" if h["road"] == ir.OTHER else h["road"]
        rep_hs.append(
            f"The only reported hotspot ({h['impacts']} impacts, up to {h['max_g']:.2f} g, on "
            f"{html.escape(where)}) sits {ev['nearest_report_m']:.0f} m from a pothole report made "
            f"{when:%B %Y} and now marked “{ev['nearest_report_state']}”; it was still producing strong "
            f"impacts at the time of the ride, so the repair may have failed or a separate defect is there.")
    overview = f"""
<h2>Overview</h2>
<p><b>What was compared.</b> The {n} impacts my handlebar-mounted phone measured on this ride
(jolts of {im.THRESHOLD_G:g} g or more while moving) were checked against FixMyStreet, the public website
where people report road problems to the council. Only road-surface reports (potholes, carriageway defects,
manholes, drain covers) made in the {RECENT_DAYS} days before the ride were used.</p>
<p><b>What was found.</b></p>
<ul>
<li><b>{n_unrep} of {n} impacts</b> had no FixMyStreet report within {MATCH_RADIUS_M:g} m, including
{strong_txt} of the strong ones (≥ 1.5 g).</li>
<li><b>{hs_unrep} of {n_hs} hotspots</b> (places hit repeatedly) had never been reported in that year.</li>
{''.join(f'<li>{t}</li>' for t in rep_hs)}
<li>Of the {n_route} recent reports along the route, only {route_felt} had an impact measured nearby;
all are now closed or fixed, so many were probably repaired before the ride.</li>
</ul>
<p><b>What it means.</b> The road hazards a scooter rider actually feels are largely missing from the
public reporting system, so FixMyStreet alone underestimates the risk on these roads. Measured impacts were
reported no more often than random points along the route ({main['pct_impacts_reported']:.0f}% vs
{main['pct_route_baseline']:.0f}%); with {n} impacts from one ride this shows the gap, not a firm rate.</p>"""

    T = ir.table
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FixMyStreet Comparison</title>
<style>
:root{{--bg:#fafaf8;--card:#fff;--ink:#222;--muted:#6b6b6b;--line:#e3e2de;--accent:{C_MATCHED}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:880px;margin:0 auto;padding:32px 16px 64px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:19px;margin:36px 0 10px}}
.sub{{color:var(--muted);margin:0 0 20px}}
.note{{background:#eef4fc;border-left:3px solid var(--accent);padding:10px 14px;border-radius:4px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}}
.tile .v{{font-size:24px;font-weight:650}} .tile .k{{color:var(--muted);font-size:13px}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--card)}}
th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid var(--line)}}
th{{color:var(--muted);font-weight:600}} td{{font-variant-numeric:tabular-nums}}
.scroll{{overflow-x:auto}} ul{{padding-left:20px}} li{{margin:4px 0}} a{{color:#1c5cab}}
</style></head><body><main>
<h1>Measured impacts vs FixMyStreet reports</h1>
<p class="sub">{html.escape(ride_label)} · FixMyStreet data fetched {fetched:%d %b %Y} ·
<a href="fms_map.html">Open the comparison map</a></p>

{overview}

<p class="note"><b>How to read the details.</b> An impact counts as <i>reported</i> when a FixMyStreet
road-surface report (pothole, carriageway defect, manhole, drain ironwork) made in the {RECENT_DAYS} days before
the ride lies within {MATCH_RADIUS_M:g} m, whatever its status now. Older reports are left out of the main
comparison because they are so dense (back to 2009) that almost any point on the route is near one.
The <i>baseline</i> is the same rate for every point along the ridden route: what chance alone would give.</p>

<h2>Headline figures</h2>
<div class="tiles">{tiles_html}</div>
<p>{main['pct_impacts_reported']:.0f}% of impacts had a recent report within {MATCH_RADIUS_M:g} m, against
{main['pct_route_baseline']:.0f}% of all points along the route. In other words, the places where the scooter
was jolted were <b>no more likely to have been reported</b> than the route in general. With only {n} impacts,
the difference between these two rates should not be read as meaningful in either direction.</p>

<h2>Sensitivity: matching radius and report age</h2>
<p>All-time columns show why old reports were excluded: with every report since 2009, impacts and random
route points match at nearly the same, very high rate.</p>
<div class="scroll">{T(sens_t, {"% impacts reported": pct, "% route points (baseline)": pct,
                                "% impacts, any date": pct, "% route points, any date": pct})}</div>

<h2>By road</h2>
<div class="scroll">{T(by_road)}</div>

<h2>Hotspots</h2>
<p>The repeated-impact locations from the statistics report.</p>
<div class="scroll">{T(hs_t, {"Max g": "{:.2f}", "Nearest report (m)": "{:.0f}"})}</div>

<h2>Measured but not reported</h2>
<p>The original finding: impacts with no road-surface report within {MATCH_RADIUS_M:g} m, strongest first.</p>
<div class="scroll">{T(unrep_t, {"Peak g": "{:.2f}", "km/h": "{:.1f}", "Nearest report (m)": "{:.0f}",
                                 "Lat": "{:.5f}", "Lon": "{:.5f}"}, index=False)}</div>

<h2>Measured and reported</h2>
<div class="scroll">{T(rep_t, {"Peak g": "{:.2f}", "Distance (m)": "{:.0f}"}, index=False)
                     if len(rep_t) else "<p>None.</p>"}</div>

<h2>Reports on the route</h2>
<p>{n_route} recent reports lie within {ROUTE_RADIUS_M:g} m of the route ({len(reports)} road-surface
reports of any date in the wider ride area). Current status (today, not at ride time):</p>
<div class="scroll">{T(route_states)}</div>
<div class="scroll">{T(route_cats)}</div>

<h2>Limitations</h2>
<ul>
<li>FixMyStreet only covers reports made through FixMyStreet and its council versions; problems
reported to the council by phone or other channels are missing.</li>
<li>Report status is as of the fetch date. A report closed or fixed before the ride may not match
the surface the rider met; one opened after the ride cannot have been known at the time.</li>
<li>“Not reported” means no report within the matching radius, not that nobody ever reported it.</li>
<li>Impacts include kerbs, drain covers and speed humps; not every unreported impact is a defect.</li>
<li>One ride, one rider; see the statistics report for the impact method and its limits.</li>
</ul>
<p class="sub">Generated by scripts/fms_compare.py. Report data: FixMyStreet by mySociety.</p>
</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Compare measured impacts with FixMyStreet reports")
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/2026-10-03_1830_rec01"))
    ap.add_argument("--out-dir", type=Path, default=Path("outputs"))
    ap.add_argument("--fms-cache", type=Path, default=Path("data/fixmystreet/reports.csv"))
    ap.add_argument("--roads-cache", type=Path, default=Path("data/osm_study_roads.json"))
    ap.add_argument("--refresh", action="store_true", help="download FixMyStreet data again")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    res = im.analyse(args.data_dir)
    osm = ir.fetch_study_roads(args.roads_cache)
    _, _, impacts, _, _, _ = ir.compute(res, osm)  # adds road and hotspot to each impact
    track = res["rough"][["lat", "lon"]].reset_index(drop=True)
    moving_track = res["rough"].loc[res["rough"]["speed"] >= im.MIN_SPEED_MS, ["lat", "lon"]]

    meta = pd.read_csv(args.data_dir / "Metadata.csv").iloc[0]
    ride_date = pd.to_datetime(int(meta["recording epoch time"]), unit="ms")

    b = BBOX_BUFFER_DEG
    bbox = (track["lon"].min() - b, track["lat"].min() - b,
            track["lon"].max() + b, track["lat"].max() + b)
    reports = fetch_reports(bbox, args.fms_cache, args.refresh)
    fetched = reports["fetched"].iloc[0]

    imp, reports, on_route, hs, sens = compare(impacts, reports, track, moving_track,
                                               ride_date, osm)

    build_map(track, imp, on_route, res["label"]).save(str(args.out_dir / "fms_map.html"))
    write_html(args.out_dir / "fms_comparison.html", res["label"], ride_date, imp, reports,
               on_route, hs, sens, fetched)
    imp.to_csv(args.out_dir / "impacts_vs_fms.csv", index=False)
    on_route.to_csv(args.out_dir / "fms_reports_on_route.csv", index=False)

    print(f"{len(reports)} road-surface reports in area; "
          f"{len(on_route)} recent (<= {RECENT_DAYS} d before ride) on route")
    print(f"Impacts with recent report <= {MATCH_RADIUS_M:g} m: "
          f"{int(imp['reported'].sum())} of {len(imp)}")
    print(sens.round(1).to_string(index=False))
    print("\nHotspots:\n", hs.drop(columns=["lat", "lon"]).to_string())
    print("\nReports on route by state:\n", on_route["state"].value_counts().to_string())


if __name__ == "__main__":
    main()
