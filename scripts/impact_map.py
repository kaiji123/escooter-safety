"""
Detect vertical impacts from a handlebar-mounted phone and map them.

Input: one Sensor Logger recording folder (iOS export) containing
    Accelerometer.csv  - user acceleration, gravity removed, device frame, m/s^2
    Gravity.csv        - gravity vector, device frame, m/s^2 (same timestamps)
    Gyroscope.csv      - angular rate, device frame, rad/s
    Location.csv       - GPS fixes (~1 Hz)
Raw files are only read, never modified.

Method
1. Vertical acceleration: project user acceleration onto the unit "up" vector
   (-gravity / |gravity|) sample by sample. This removes the effect of how the
   phone happens to be tilted on the handlebar.
2. Impact events: peaks in |vertical acceleration| above a fixed threshold
   (default 1.0 g), at least MIN_GAP_S apart, while moving faster than
   MIN_SPEED_MS (excludes mounting, walking the scooter, handling at stops).
   A fixed threshold in g is used rather than a per-ride statistical one so that
   different rides and vehicles (e-scooter vs bicycle) are directly comparable.
3. Post-impact instability: RMS angular-rate magnitude in the window after the
   impact divided by the RMS in a window before it. Ratio > 1 means the
   handlebar was rotating more (wobbling) after the impact than before.
4. Location: GPS latitude/longitude/speed linearly interpolated to the impact
   timestamp. Fixes with poor horizontal accuracy are discarded first.
5. Route roughness: RMS vertical acceleration in 1 s windows, used to colour
   the ridden route so continuous rough surfaces show up, not just single hits.

Usage
    python scripts/impact_map.py --data-dir . --out-dir outputs
"""

import argparse
import json
from pathlib import Path

import folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

G = 9.80665  # standard gravity, m/s^2

# ---- Default analysis parameters (all reported in outputs/impacts_params.json) ----
THRESHOLD_G = 1.0        # minimum |vertical accel| peak counted as an impact
MIN_GAP_S = 0.5          # two peaks closer than this are one event
MIN_SPEED_MS = 2.0       # ignore samples slower than ~7 km/h
MAX_GPS_ACC_M = 20.0     # discard GPS fixes with worse horizontal accuracy
PRE_WIN_S = (-2.5, -0.5) # baseline window for gyro RMS, relative to impact
POST_WIN_S = (0.1, 1.5)  # post-impact window for gyro RMS
ROUGH_WIN_S = 1.0        # window for route roughness RMS

# Severity bands for the map legend only (visual grouping, not a clinical scale).
SEVERITY_BANDS = [  # (lower bound in g, label, colour from one sequential blue ramp)
    (1.0, "1.0-1.5 g", "#86b6ef"),
    (1.5, "1.5-2.0 g", "#3987e5"),
    (2.0, "2.0-2.5 g", "#1c5cab"),
    (2.5, "> 2.5 g", "#0d366b"),
]
# Continuous ramp for route roughness (same hue family, light = smooth).
ROUGH_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def load_xyz(path):
    """Read a Sensor Logger x/y/z CSV, indexed by elapsed seconds."""
    df = pd.read_csv(path)
    return df["seconds_elapsed"].to_numpy(), df[["x", "y", "z"]].to_numpy()


def load_inputs(data_dir):
    t_acc, acc = load_xyz(data_dir / "Accelerometer.csv")
    t_grav, grav = load_xyz(data_dir / "Gravity.csv")
    t_gyr, gyr = load_xyz(data_dir / "Gyroscope.csv")
    if not np.array_equal(t_acc, t_grav):
        raise ValueError("Accelerometer and Gravity timestamps differ; resampling needed.")

    loc = pd.read_csv(data_dir / "Location.csv")
    loc = loc[(loc["horizontalAccuracy"] > 0) & (loc["horizontalAccuracy"] <= MAX_GPS_ACC_M)]
    loc = loc.sort_values("seconds_elapsed").reset_index(drop=True)
    # speed = -1 means "unavailable" on iOS; leave as NaN rather than zero.
    loc["speed"] = loc["speed"].where(loc["speed"] >= 0)
    return t_acc, acc, grav, t_gyr, gyr, loc


def vertical_acceleration(acc, grav):
    """Signed vertical component of user acceleration (positive = upwards)."""
    up = -grav / np.linalg.norm(grav, axis=1, keepdims=True)
    return np.einsum("ij,ij->i", acc, up)


def interp_gps(t, loc, column):
    """Linear interpolation of a GPS column to times t; NaN outside the GPS span."""
    valid = loc[["seconds_elapsed", column]].dropna()
    return np.interp(t, valid["seconds_elapsed"], valid[column], left=np.nan, right=np.nan)


def window_rms(t, x, t0, t1):
    m = (t >= t0) & (t < t1)
    return float(np.sqrt(np.mean(x[m] ** 2))) if m.any() else np.nan


def detect_impacts(t, a_vert, speed, gyr_t, gyr_mag, threshold_g):
    fs = 1.0 / np.median(np.diff(t))
    peaks, _ = find_peaks(np.abs(a_vert), height=threshold_g * G,
                          distance=max(1, int(MIN_GAP_S * fs)))
    peaks = peaks[speed[peaks] >= MIN_SPEED_MS]  # NaN speed fails this test too

    rows = []
    for i in peaks:
        ti = t[i]
        pre = window_rms(gyr_t, gyr_mag, ti + PRE_WIN_S[0], ti + PRE_WIN_S[1])
        post = window_rms(gyr_t, gyr_mag, ti + POST_WIN_S[0], ti + POST_WIN_S[1])
        rows.append({
            "seconds_elapsed": round(ti, 3),
            "peak_vert_ms2": round(a_vert[i], 2),
            "peak_abs_g": round(abs(a_vert[i]) / G, 2),
            "speed_ms": round(speed[i], 2),
            "speed_kmh": round(speed[i] * 3.6, 1),
            "gyro_rms_pre_rads": round(pre, 3),
            "gyro_rms_post_rads": round(post, 3),
            "instability_ratio": round(post / pre, 2) if pre and pre > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def route_roughness(t, a_vert, loc):
    """RMS vertical acceleration (in g) in fixed windows, positioned by GPS."""
    bins = np.floor(t / ROUGH_WIN_S).astype(int)
    df = pd.DataFrame({"bin": bins, "a2": a_vert ** 2})
    r = df.groupby("bin")["a2"].mean().pipe(np.sqrt) / G
    tc = (r.index.to_numpy() + 0.5) * ROUGH_WIN_S
    out = pd.DataFrame({"t": tc, "rms_g": r.to_numpy(),
                        "lat": interp_gps(tc, loc, "latitude"),
                        "lon": interp_gps(tc, loc, "longitude"),
                        "speed": interp_gps(tc, loc, "speed")})
    return out.dropna(subset=["lat", "lon"])


def severity_band(g):
    band = SEVERITY_BANDS[0]
    for b in SEVERITY_BANDS:
        if g >= b[0]:
            band = b
    return band


def build_map(rough, impacts, recording_label):
    centre = [rough["lat"].mean(), rough["lon"].mean()]
    m = folium.Map(location=centre, zoom_start=15, tiles=None, control_scale=True)
    # Esri Light Gray Canvas (base + street-name overlay). Chosen because it serves
    # tiles without an API key even when this HTML is opened from disk; OSM's tile
    # servers return 403 and CARTO returns "API key required" tiles in that case.
    # Native tiles stop at zoom 16; Leaflet upscales them beyond that.
    esri = ("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
            "World_Light_Gray_{layer}/MapServer/tile/{{z}}/{{y}}/{{x}}")
    esri_attr = "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors"
    folium.TileLayer(tiles=esri.format(layer="Base"), attr=esri_attr, name="Basemap",
                     max_native_zoom=16, max_zoom=19).add_to(m)
    folium.TileLayer(tiles=esri.format(layer="Reference"), attr=esri_attr,
                     name="Street names", overlay=True, control=True,
                     max_native_zoom=16, max_zoom=19).add_to(m)

    # Route, coloured by roughness. Only moving segments are coloured; stops are grey.
    cmap = folium.LinearColormap(ROUGH_RAMP, vmin=0.0,
                                 vmax=float(np.nanpercentile(rough["rms_g"], 98)),
                                 caption="Route roughness: RMS vertical acceleration per 1 s (g)")
    route = folium.FeatureGroup(name="Route roughness")
    pts = rough[["lat", "lon"]].to_numpy()
    for k in range(len(rough) - 1):
        moving = rough["speed"].iloc[k] >= MIN_SPEED_MS
        folium.PolyLine(pts[k:k + 2], weight=4, opacity=0.9,
                        color=cmap(rough["rms_g"].iloc[k]) if moving else "#b5b4ae",
                        ).add_to(route)
    route.add_to(m)
    cmap.add_to(m)

    # Impact markers: colour and size both encode peak g (not colour alone).
    hits = folium.FeatureGroup(name="Impact events")
    for _, r in impacts.sort_values("peak_abs_g").iterrows():
        _, label, colour = severity_band(r["peak_abs_g"])
        popup = (f"<b>Impact {r['event_id']}</b><br>"
                 f"Peak vertical: {r['peak_abs_g']:.2f} g ({label})<br>"
                 f"Speed: {r['speed_kmh']:.1f} km/h<br>"
                 f"Post-impact instability: {r['instability_ratio']:.2f}x gyro RMS<br>"
                 f"t = {r['seconds_elapsed']:.1f} s into recording")
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=5 + 4 * (r["peak_abs_g"] - 1.0),
            color="#ffffff", weight=2,  # white ring separates overlapping markers
            fill=True, fill_color=colour, fill_opacity=0.95,
            tooltip=f"{r['peak_abs_g']:.2f} g at {r['speed_kmh']:.0f} km/h",
            popup=folium.Popup(popup, max_width=260),
        ).add_to(hits)
    hits.add_to(m)

    legend_rows = "".join(
        f'<div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;'
        f'background:{c};border:2px solid #fff;box-shadow:0 0 0 1px #999;margin-right:6px;'
        f'vertical-align:middle"></span>{lab}</div>'
        for _, lab, c in SEVERITY_BANDS)
    legend = f"""
    <div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:#fff;
         padding:10px 12px;border-radius:6px;font:13px/1.5 sans-serif;color:#222;
         box-shadow:0 1px 4px rgba(0,0,0,.3)">
      <b>Impact events (peak vertical accel.)</b>{legend_rows}
      <div style="color:#666;margin-top:4px">{len(impacts)} events &ge; {THRESHOLD_G:g} g,
      speed &ge; {MIN_SPEED_MS * 3.6:.0f} km/h<br>{recording_label}</div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[rough["lat"].min(), rough["lon"].min()],
                  [rough["lat"].max(), rough["lon"].max()]], padding=(30, 30))
    return m


def plot_trace(t, a_vert, speed, impacts, path):
    """Diagnostic figure: vertical acceleration with detections, to sanity-check the threshold."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 5), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(t, a_vert / G, lw=0.4, color="#6da7ec")
    for s in (1, -1):
        ax1.axhline(s * THRESHOLD_G, color="#888", lw=0.8, ls="--")
    if len(impacts):
        ax1.plot(impacts["seconds_elapsed"], impacts["peak_vert_ms2"] / G, "o",
                 ms=5, mfc="#0d366b", mec="white", label="Detected impact")
        ax1.legend(loc="upper right", frameon=False)
    ax1.set_ylabel("Vertical accel. (g)")
    ax2.plot(t, speed * 3.6, lw=1, color="#256abf")
    ax2.axhline(MIN_SPEED_MS * 3.6, color="#888", lw=0.8, ls="--")
    ax2.set_ylabel("Speed (km/h)")
    ax2.set_xlabel("Time since recording start (s)")
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", lw=0.6)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def analyse(data_dir, threshold_g=THRESHOLD_G):
    """Run steps 1-5 on one recording; shared by this script and impact_report.py."""
    meta = pd.read_csv(data_dir / "Metadata.csv").iloc[0]
    label = f"{meta['device name']}, {meta['recording time']}"

    t, acc, grav, gyr_t, gyr, loc = load_inputs(data_dir)
    a_vert = vertical_acceleration(acc, grav)
    gyr_mag = np.linalg.norm(gyr, axis=1)
    speed = interp_gps(t, loc, "speed")

    impacts = detect_impacts(t, a_vert, speed, gyr_t, gyr_mag, threshold_g)
    if len(impacts):
        impacts["lat"] = interp_gps(impacts["seconds_elapsed"].to_numpy(), loc, "latitude")
        impacts["lon"] = interp_gps(impacts["seconds_elapsed"].to_numpy(), loc, "longitude")
        impacts = impacts.dropna(subset=["lat", "lon"]).reset_index(drop=True)
        impacts.insert(0, "event_id", np.arange(1, len(impacts) + 1))

    return {"t": t, "a_vert": a_vert, "speed": speed, "loc": loc, "impacts": impacts,
            "rough": route_roughness(t, a_vert, loc), "label": label}


def main():
    global THRESHOLD_G
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--data-dir", type=Path, default=Path("."))
    ap.add_argument("--out-dir", type=Path, default=Path("outputs"))
    ap.add_argument("--threshold-g", type=float, default=THRESHOLD_G)
    args = ap.parse_args()
    THRESHOLD_G = args.threshold_g
    args.out_dir.mkdir(parents=True, exist_ok=True)

    res = analyse(args.data_dir, THRESHOLD_G)
    t, a_vert, speed, loc = res["t"], res["a_vert"], res["speed"], res["loc"]
    impacts, rough, label = res["impacts"], res["rough"], res["label"]

    build_map(rough, impacts, label).save(str(args.out_dir / "impact_map.html"))
    impacts.to_csv(args.out_dir / "impacts.csv", index=False)
    plot_trace(t, a_vert, speed, impacts, args.out_dir / "impact_trace.png")

    params = {"recording": label, "threshold_g": THRESHOLD_G, "min_gap_s": MIN_GAP_S,
              "min_speed_ms": MIN_SPEED_MS, "max_gps_accuracy_m": MAX_GPS_ACC_M,
              "pre_window_s": PRE_WIN_S, "post_window_s": POST_WIN_S,
              "roughness_window_s": ROUGH_WIN_S, "n_gps_fixes_used": int(len(loc)),
              "n_impacts": int(len(impacts))}
    (args.out_dir / "impacts_params.json").write_text(json.dumps(params, indent=2))

    print(f"{len(impacts)} impacts >= {THRESHOLD_G} g while moving")
    if len(impacts):
        print(impacts[["event_id", "seconds_elapsed", "peak_abs_g", "speed_kmh",
                       "instability_ratio", "lat", "lon"]].to_string(index=False))
    print(f"Outputs written to {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()
