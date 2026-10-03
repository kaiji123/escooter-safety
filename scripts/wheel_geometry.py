"""
Geometric model: how wheel diameter changes what a pothole does to an e-scooter.

A rigid wheel of radius R rolls at speed v across a rectangular pothole of depth d
and length w (along the direction of travel) with sharp edges (worst case).

1. Drop. While over the hole the wheel centre can sink by at most
     - the depth:                    d
     - the geometric sag limit:      R - sqrt(R^2 - (w/2)^2)  (wheel resting on both edges)
     - the ballistic limit:          0.5 * g * (w / v)^2      (time available to fall)
   The ballistic limit assumes the front end falls freely under gravity, an upper
   bound: in reality the rider and frame slow the fall. h = min of the three.

2. Far-edge impact. With the wheel bottom h below road level, the edge touches the
   tyre at angle theta from vertical, cos(theta) = (R - h) / R. For a wheel that
   must roll over the edge (point mass at the axle, plastic impact at the edge):
     - velocity component into the edge, lost in the impact:   v_n = v * sin(theta)
     - forward speed lost at the front axle:                   dv_x = v * sin(theta)^2
     - upward velocity gained:                                 v_z = v * sin(theta) * cos(theta)
   v_n is the impact severity measure; dv_x is the sudden braking of the front wheel
   that pitches the rider forward (the fall mechanism in the Imperial simulations).
   If h >= R the edge is above the axle and the wheel cannot roll over it at all.

A bigger wheel lowers theta for the same pothole, so every quantity falls.
Absolute peak accelerations need tyre stiffness and suspension, which this model
does not include; compare wheel sizes relative to each other.

Wheel sizes: nominal size taken as tyre outer diameter (10 in = 254 mm).
Baseline: Voi Voiager 5, 10 in front (Levy fleet spec, pneumatic, front spring).
Voiager 7: 12 in front tyre ("a size increase from its predecessors"); rear not
stated, assumed 10 in here. CONFIRM which model runs in Oxford.

Usage
    python scripts/wheel_geometry.py --out-dir outputs/wheel_model
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

G = 9.80665
INCH = 0.0254

# Scooter configurations compared: (label, front diameter in, rear diameter in)
CONFIGS = [
    ("Current (10/10 in, Voiager 5)", 10, 10),
    ("Larger front only (12/10 in, Voiager 7-style)", 12, 10),
    ("Larger front only (14/10 in)", 14, 10),
    ("Larger both (12/12 in)", 12, 12),
]
DIAMETERS_IN = [8, 10, 12, 14, 16]       # for the wheel-size sweep
SPEED_KMH = 20.0                         # rider's measured cruising speed (~18-22 km/h)
SPEEDS_KMH = [15.0, 20.0, 25.0]          # sensitivity (UK rental limit is 15.5 mph ~ 25 km/h)
DEPTHS_MM = np.arange(0, 121, 1.0)       # pothole depth sweep
WIDTHS_MM = [150, 300, 600, 1000]        # pothole length along travel
KEY_DEPTHS_MM = [30, 60, 90]             # depths used in the Imperial simulations
KEY_WIDTH_MM = 600

# Sequential blue ramp: darker = larger wheel (wheel size is an ordered magnitude)
RAMP = {8: "#9ec5f4", 10: "#5598e7", 12: "#2a78d6", 14: "#1c5cab", 16: "#0d366b"}
INK, MUTED = "#222222", "#6b6b6b"


def wheel_drop_m(R, d, w, v=None):
    """Depth (m) the wheel bottom sinks below road level crossing the pothole.

    v=None gives the static case (wheel at rest in the hole, no time limit).
    """
    half = np.minimum(w / 2, R)
    sag = R - np.sqrt(R ** 2 - half ** 2)
    h = np.minimum(d, sag)
    if v is not None:
        h = np.minimum(h, 0.5 * G * (w / v) ** 2)
    return h


def edge_impact(R, h, v):
    """Impact quantities at the far edge for drop h (all arrays broadcast)."""
    h = np.asarray(h, dtype=float)
    blocked = h >= R
    c = np.clip((R - h) / R, 0, 1)
    s = np.sqrt(1 - c ** 2)
    return {"theta_deg": np.degrees(np.arcsin(s)), "v_n": v * s,
            "dv_x": v * s ** 2, "v_z": v * s * c, "blocked": blocked}


def sweep(speed_kmh):
    v = speed_kmh / 3.6
    rows = []
    for D in DIAMETERS_IN:
        R = D * INCH / 2
        for w in WIDTHS_MM:
            h = wheel_drop_m(R, DEPTHS_MM / 1000, w / 1000, v)
            imp = edge_impact(R, h, v)
            for i, d in enumerate(DEPTHS_MM):
                rows.append({"diameter_in": D, "speed_kmh": speed_kmh, "width_mm": w,
                             "depth_mm": d, "drop_mm": h[i] * 1000,
                             "theta_deg": imp["theta_deg"][i], "v_n_ms": imp["v_n"][i],
                             "dv_x_ms": imp["dv_x"][i], "speed_loss_pct": 100 * imp["dv_x"][i] / v,
                             "blocked": bool(imp["blocked"][i])})
    return pd.DataFrame(rows)


def config_table(df):
    """Front and rear wheel metrics per configuration at the key depths."""
    sub = df[(df["speed_kmh"] == SPEED_KMH) & (df["width_mm"] == KEY_WIDTH_MM)
             & (df["depth_mm"].isin(KEY_DEPTHS_MM))].set_index(["diameter_in", "depth_mm"])
    rows = []
    for label, Df, Dr in CONFIGS:
        for d in KEY_DEPTHS_MM:
            f, r = sub.loc[(Df, d)], sub.loc[(Dr, d)]
            rows.append({"configuration": label, "depth_mm": d,
                         "front_v_n_ms": f["v_n_ms"], "front_speed_loss_pct": f["speed_loss_pct"],
                         "rear_v_n_ms": r["v_n_ms"], "front_drop_mm": f["drop_mm"]})
    t = pd.DataFrame(rows)
    base = t[t["configuration"] == CONFIGS[0][0]].set_index("depth_mm")
    t["front_v_n_change_pct"] = t.apply(
        lambda x: 100 * (x["front_v_n_ms"] / base.loc[x["depth_mm"], "front_v_n_ms"] - 1), axis=1)
    t["front_speed_loss_change_pct"] = t.apply(
        lambda x: 100 * (x["front_speed_loss_pct"] / base.loc[x["depth_mm"], "front_speed_loss_pct"] - 1),
        axis=1)
    return t


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#bbbbbb")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(color="#ececec", lw=0.6)
    ax.set_axisbelow(True)


def fig_by_depth(df, metric, ylabel, path, width_mm=KEY_WIDTH_MM):
    sub = df[(df["speed_kmh"] == SPEED_KMH) & (df["width_mm"] == width_mm)]
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    for D in DIAMETERS_IN:
        s = sub[sub["diameter_in"] == D]
        lw = 2.6 if D in (10, 12) else 1.6
        ax.plot(s["depth_mm"], s[metric], color=RAMP[D], lw=lw)
        tag = {10: " (Voiager 5)", 12: " (Voiager 7 front)"}.get(D, "")
        ax.annotate(f"{D} in{tag}", (s["depth_mm"].iloc[-1], s[metric].iloc[-1]),
                    xytext=(4, 0), textcoords="offset points", va="center",
                    fontsize=8.5, color=INK)
    for d in KEY_DEPTHS_MM:
        ax.axvline(d, color="#cccccc", lw=0.8, ls=":")
    ax.set_xlabel(f"Pothole depth (mm)  ·  {width_mm} mm long, sharp edges, {SPEED_KMH:g} km/h")
    ax.set_ylabel(ylabel)
    ax.set_xlim(0, DEPTHS_MM.max())
    _style(ax)
    fig.tight_layout()
    fig.subplots_adjust(right=0.78)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_by_width(df, path):
    """Normal impact velocity vs depth, small multiples by pothole length, 10 vs 12 in."""
    fig, axes = plt.subplots(1, len(WIDTHS_MM), figsize=(10, 3.2), sharey=True)
    sub = df[df["speed_kmh"] == SPEED_KMH]
    for ax, w in zip(axes, WIDTHS_MM):
        for D in (10, 12, 16):
            s = sub[(sub["width_mm"] == w) & (sub["diameter_in"] == D)]
            ax.plot(s["depth_mm"], s["v_n_ms"], color=RAMP[D], lw=2, label=f"{D} in")
        ax.set_title(f"{w} mm long", fontsize=9.5, color=INK, loc="left")
        ax.set_xlabel("Depth (mm)")
        _style(ax)
    axes[0].set_ylabel("Edge impact velocity (m/s)")
    axes[-1].legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_schematic(path, depth_mm=60, width_mm=KEY_WIDTH_MM):
    """Side view: 10 in and 12 in wheels resting in the same pothole at the far edge."""
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
    d, w = depth_mm / 1000, width_mm / 1000
    for ax, D in zip(axes, (10, 12)):
        R = D * INCH / 2
        h = wheel_drop_m(R, d, w)  # static drop, no speed limit, for illustration
        th = np.arccos((R - h) / R)
        cx, cy = w - R * np.sin(th), R - h  # wheel touching the far edge
        road = "#8a8984"
        ax.plot([-0.25, 0, 0, w, w, w + 0.25], [0, 0, -d, -d, 0, 0], color=road, lw=2)
        ax.add_patch(plt.Circle((cx, cy), R, fill=False, color=RAMP[D], lw=2.5))
        ax.plot(cx, cy, "o", color=RAMP[D], ms=4)
        ax.plot([cx, w], [cy, 0], color=INK, lw=0.8, ls="--")
        ax.annotate(f"θ = {np.degrees(th):.0f}°", (w, 0), xytext=(6, 8),
                    textcoords="offset points", fontsize=9, color=INK)
        ax.set_title(f"{D} in wheel: sinks {h * 1000:.0f} mm", fontsize=10, color=INK, loc="left")
        ax.set_aspect("equal")
        ax.set_xlim(-0.25, w + 0.25)
        ax.axis("off")
    fig.suptitle(f"Same pothole ({depth_mm} mm deep, {width_mm} mm long): the larger wheel meets the edge "
                 f"at a shallower angle", fontsize=10, color=MUTED, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Geometric wheel-pothole model")
    ap.add_argument("--out-dir", type=Path, default=Path("outputs/wheel_model"))
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.concat([sweep(s) for s in SPEEDS_KMH], ignore_index=True)
    df.round(4).to_csv(args.out_dir / "wheel_sweep.csv", index=False)
    table = config_table(df)
    table.round(2).to_csv(args.out_dir / "configurations.csv", index=False)

    fig_schematic(args.out_dir / "fig_schematic.png")
    fig_by_depth(df, "v_n_ms", "Edge impact velocity (m/s)", args.out_dir / "fig_impact_velocity.png")
    fig_by_depth(df, "speed_loss_pct", "Front-wheel speed lost at edge (%)",
                 args.out_dir / "fig_speed_loss.png")
    fig_by_width(df, args.out_dir / "fig_by_pothole_length.png")

    pd.set_option("display.width", 160)
    print(table.round(2).to_string(index=False))
    print(f"\nOutputs in {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()
