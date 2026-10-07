"""
Sensor Logger (iPhone) data quality checks and walking-vs-scooting segmentation.

Two parts, run on every recording in data/raw/:

A. Data quality (internal consistency; no external reference)
   - sampling: rate, interval jitter, gaps, non-monotonic or duplicate timestamps
   - clock: absolute `time` (ns since epoch) vs `seconds_elapsed`
   - accelerometer: raw (AccelerometerUncalibrated, in g) vs fused user acceleration +
     gravity (m/s^2); magnitude of the raw signal at rest (should be 1 g)
   - noise floor at rest (stationary windows): user-acceleration SD, gyroscope SD and
     calibrated-vs-uncalibrated gyroscope offset
   - GPS: fix interval, gaps, reported horizontal accuracy, reported speed vs speed
     derived from consecutive positions, position scatter while stationary
   NOTE: Gravity.csv has a fixed magnitude (9.80665 m/s^2) by construction of the
   iOS sensor fusion, so its magnitude is reported but is not an accuracy test.

B. Activity segmentation (walking / scooting / stationary / unclear)
   Overlapping 4 s windows, 1 s apart. Features:
     sd_v       SD of vertical user acceleration (projection on the gravity vector), m/s^2
     step_frac  share of vertical-acceleration power in the step band 1.2-2.8 Hz
                (of 0.5-20 Hz); walking cadence is ~1.6-2.2 steps/s
     step_ac    highest normalised autocorrelation at lags of one step (0.36-0.83 s);
                regular steps give a high value, road vibration does not
     cadence    step frequency at that autocorrelation peak, steps/s
     speed_kmh  median GPS speed of fixes inside the window (NaN if none valid)
   Rules (set from physical reasoning before the ground truth is known; see
   ANALYST CHOICES below), applied in this order:
     stationary  sd_v < 0.5 and (speed < 2 km/h or no speed)
     walking     step_ac >= 0.5 and step_frac >= 0.5 and (speed < 8 km/h or no speed)
     scooting    speed >= 8 km/h and step_frac < 0.3
     unclear     anything else (e.g. slow riding, handling the phone, mixed)
   Labels are smoothed with a centred 5-window majority filter. A walking bout is >= 10 s
   of consecutive walking windows. The bout's start is then refined to the first step:
   steps are peaks of band-passed (0.8-4 Hz) vertical acceleration; going back from the
   first step inside the bout, earlier peaks are kept while successive intervals stay
   within one step period (0.35-0.85 s).

   Optional ground truth: data/ground_truth.csv (recording, event, local_time, precision,
   source, notes). Events evaluated:
     walking_start  difference between the nearest detected first step and the time
     no_walking     the recording contains no walking: every walking label is a false
                    positive (seconds labelled, bouts >= MIN_WALK_BOUT_S, labels while
                    GPS showed riding speed)
     rental_end     end of the Voi rental, given to the minute (true time within
                    [t, t+60 s)): compared with the end of the last scooting segment
                    and the first step of the next walking bout
   The comparison is only as good as the reference: a remembered "after about 10
   minutes" checks agreement to within about a minute, not seconds.

Prior methods this builds on (full references in references.bib / REFERENCES.md):
   phone-accelerometer activity recognition (Kwapisz et al. 2011) and GPS + accelerometer
   transport-mode detection (Reddy et al. 2010); vertical component by projection onto
   gravity (Mizell 2003); step regularity and cadence from autocorrelation
   (Moe-Nilssen & Helbostad 2004); walking step frequency ~1.8-2.0 Hz (Pachi & Ji 2005);
   Welch (1967) spectrum; Butterworth (1930) filter; SciPy (Virtanen et al. 2020).

Usage
    python scripts/sensor_validity.py                      # all recordings in data/raw
    python scripts/sensor_validity.py --recordings 2026-10-07_1037_rec02
Outputs in outputs/sensor_validity/ (per recording: windows.csv, segments.csv,
steps_*.csv, fig_timeline.png, fig_walk_onset_*.png; overall: quality_summary.csv,
segments_all.csv, walking_onsets.csv, report.html).
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import warnings

import numpy as np
import pandas as pd
from scipy.signal import butter, find_peaks, sosfiltfilt, welch

G = 9.80665
TZ = "Europe/London"
FS = 100.0                       # Sensor Logger sample rate (sampleRateMs = 10)
STREAMS = ["Accelerometer", "AccelerometerUncalibrated", "Gravity", "Gyroscope",
           "GyroscopeUncalibrated"]

# ---- ANALYST CHOICES (not established criteria; state them in the paper) ----
WIN_S, HOP_S = 4.0, 1.0          # window length and spacing
STEP_BAND = (1.2, 2.8)           # Hz, plausible walking cadence
TOTAL_BAND = (0.5, 20.0)         # Hz
STATIONARY_SD = 0.5              # m/s^2, vertical user-acceleration SD
STATIONARY_MAX_KMH = 2.0
WALK_AC, WALK_STEPFRAC, WALK_MAX_KMH = 0.5, 0.5, 8.0
SCOOT_MIN_KMH, SCOOT_MAX_STEPFRAC = 8.0, 0.3
SMOOTH_WINDOWS = 5
MIN_WALK_BOUT_S = 10.0
STEP_PROMINENCE = 1.0            # m/s^2, band-passed vertical acceleration
STEP_INTERVAL = (0.35, 0.85)     # s, one step period
GAP_FACTOR = 1.5                 # an interval > 1.5x nominal counts as a gap
GPS_MOVING_KMH, GPS_MOVING_FIXES = 1.5, 3   # GPS "moving": > 1.5 km/h on 3 fixes in a row
MIN_SPEED_SEG_S = 30.0           # segments used for the GPS speed comparison
SPEED_SEG_TRIM_S = 15.0          # trimmed at both ends (transitions, GPS lag)

COLORS = {"scooting": "#2a78d6", "walking": "#eb6834",   # categorical slots 1-2
          "stationary": "#8a8984", "unclear": "#d6d5cf"}  # neutrals (not series)
INK, MUTED = "#222222", "#6b6b6b"


# --------------------------------------------------------------------------- loading
def load(rec):
    d = {s: pd.read_csv(rec / f"{s}.csv") for s in STREAMS}
    d["Location"] = pd.read_csv(rec / "Location.csv")
    d["meta"] = pd.read_csv(rec / "Metadata.csv").iloc[0]
    return d


def local_time(t_ns):
    return pd.to_datetime(np.asarray(t_ns, dtype="int64"), utc=True).tz_convert(TZ)


# ------------------------------------------------------------------- A: data quality
def sampling_stats(df, nominal_s):
    t = df["time"].to_numpy(dtype="int64")
    dt = np.diff(t) / 1e9
    se = df["seconds_elapsed"].to_numpy()
    drift = ((t - t[0]) / 1e9) - (se - se[0])
    return {
        "rows": len(df),
        "duration_s": round(float(se[-1] - se[0]), 1),
        "rate_hz": round(float(len(df) / (se[-1] - se[0])), 2),
        "dt_median_ms": round(float(np.median(dt) * 1000), 3),
        "dt_p1_ms": round(float(np.percentile(dt, 1) * 1000), 3),
        "dt_p99_ms": round(float(np.percentile(dt, 99) * 1000), 3),
        "gaps": int((dt > GAP_FACTOR * nominal_s).sum()),
        "max_gap_s": round(float(dt.max()), 3),
        "non_monotonic": int((dt < 0).sum()),
        "duplicates": int((dt == 0).sum()),
        "clock_vs_elapsed_max_ms": round(float(np.abs(drift).max() * 1000), 3),
    }


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def quality(d, win):
    q = {}
    for s in STREAMS:
        q[s] = sampling_stats(d[s], 1 / FS)
    loc = d["Location"]
    q["Location"] = sampling_stats(loc, 1.0)

    # Raw accelerometer (g) vs fused user acceleration + gravity (m/s^2). The two are
    # sampled at different instants, so the fused signal is interpolated to the raw
    # timestamps (time in ns, relative to the first fused sample).
    acc, grav, raw = d["Accelerometer"], d["Gravity"], d["AccelerometerUncalibrated"]
    tf = (acc["time"].to_numpy(dtype="int64") - int(acc["time"].iloc[0])) / 1e9
    tr = (raw["time"].to_numpy(dtype="int64") - int(acc["time"].iloc[0])) / 1e9
    inside = (tr >= tf[0]) & (tr <= tf[-1])
    res2 = np.zeros(inside.sum())
    for c in "xyz":
        fused_c = np.interp(tr[inside], tf, (acc[c].to_numpy() + grav[c].to_numpy()) / G)
        res2 += (raw[c].to_numpy()[inside] - fused_c) ** 2
    res = np.sqrt(res2)
    q["accel_raw_vs_fused"] = {"pairs": int(inside.sum()), "residual_median_g": round(float(np.median(res)), 4),
                               "residual_p95_g": round(float(np.percentile(res, 95)), 4)}
    gn = np.sqrt(grav.x ** 2 + grav.y ** 2 + grav.z ** 2)
    q["gravity_norm"] = {"mean": round(float(gn.mean()), 5), "sd": round(float(gn.std()), 6),
                         "note": "fixed by sensor fusion; not an accuracy test"}

    # Noise floor and bias in the quietest windows: non-overlapping 4 s windows ranked by
    # user-acceleration SD (largest axis); the quietest 5% are used. No threshold is
    # needed, but if the phone was never truly still these values are upper bounds.
    gyr, gyu = d["Gyroscope"], d["GyroscopeUncalibrated"]
    n = int(WIN_S * FS)
    k = len(acc) // n
    A = np.stack([acc[c].to_numpy()[: k * n].reshape(k, n) for c in "xyz"])      # 3 x k x n
    sd_max = A.std(axis=2).max(axis=0)
    quiet = np.argsort(sd_max)[: max(1, int(0.05 * k))]
    def win_vals(df, cols):
        se = df["seconds_elapsed"].to_numpy()
        t0s = acc["seconds_elapsed"].to_numpy()[quiet * n]
        m = np.zeros(len(df), bool)
        for t0 in t0s:
            m |= (se >= t0) & (se < t0 + WIN_S)
        return m
    mr, mg, mu = win_vals(raw, "xyz"), win_vals(gyr, "xyz"), win_vals(gyu, "xyz")
    rawn = np.sqrt(raw.x ** 2 + raw.y ** 2 + raw.z ** 2)
    G3 = np.stack([gyr[c].to_numpy()[: k * n].reshape(k, n) for c in "xyz"])
    rest = {
        "method": "quietest 5% of 4 s windows",
        "windows": int(len(quiet)),
        "user_acc_sd_ms2_median": round(float(np.median(sd_max[quiet])), 4),
        "gyro_sd_rads_median": round(float(np.median(G3.std(axis=2).max(axis=0)[quiet])), 4),
        "raw_acc_norm_mean_g": round(float(rawn[mr].mean()), 4),
        "raw_acc_norm_sd_g": round(float(rawn[mr].std()), 4),
        "gyro_cal_minus_uncal_mean_rads": [round(float(gyr[c][mg].mean() - gyu[c][mu].mean()), 4)
                                           for c in "xyz"],
    }
    q["at_rest"] = rest

    # GPS.
    v = loc[loc["speed"] >= 0]
    dist = haversine_m(loc.latitude.values[:-1], loc.longitude.values[:-1],
                       loc.latitude.values[1:], loc.longitude.values[1:])
    dts = np.diff(loc["seconds_elapsed"].to_numpy())
    ok = (dts > 0.5) & (dts < 2.0)
    v_pos = dist[ok] / dts[ok]
    v_rep = ((loc["speed"].values[:-1] + loc["speed"].values[1:]) / 2)[ok]
    both = (loc["speed"].values[:-1][ok] >= 0) & (loc["speed"].values[1:][ok] >= 0)
    moving = both & (v_rep > 1.0)
    q["gps"] = {
        "fixes": len(loc),
        "invalid_speed_share": round(float((loc["speed"] < 0).mean()), 3),
        "hacc_median_m": round(float(loc["horizontalAccuracy"].median()), 1),
        "hacc_p90_m": round(float(loc["horizontalAccuracy"].quantile(0.9)), 1),
        "speed_reported_vs_position_median_abs_ms": round(float(np.median(np.abs(v_pos[moving] - v_rep[moving]))), 2)
        if moving.any() else None,
        "speed_pairs_compared": int(moving.sum()),
        "gps_valid_speed_rows": int(len(v)),
    }
    # Position scatter while the phone is labelled stationary (GPS jitter).
    still = win[win["label"] == "stationary"]
    if len(still):
        se_l = loc["seconds_elapsed"].to_numpy()
        ml = np.zeros(len(loc), bool)
        for t0 in still["t_start"]:
            ml |= (se_l >= t0) & (se_l < t0 + WIN_S)
        if ml.sum() >= 5:
            # group consecutive still fixes; scatter = distance from each group's median
            seg = np.cumsum(np.r_[True, np.diff(np.flatnonzero(ml)) > 2])
            idx = np.flatnonzero(ml)
            errs = []
            for g in np.unique(seg):
                ii = idx[seg == g]
                if len(ii) < 5:
                    continue
                la, lo = loc.latitude.values[ii], loc.longitude.values[ii]
                errs.extend(haversine_m(la, lo, np.median(la), np.median(lo)))
            if errs:
                q["gps"]["stationary_scatter_median_m"] = round(float(np.median(errs)), 1)
                q["gps"]["stationary_scatter_p90_m"] = round(float(np.percentile(errs, 90)), 1)
    return q


# --------------------------------------------------------------- B: segmentation
def vertical_acc(d):
    acc, grav = d["Accelerometer"], d["Gravity"]
    gx, gy, gz = grav.x.to_numpy(), grav.y.to_numpy(), grav.z.to_numpy()
    gn = np.sqrt(gx ** 2 + gy ** 2 + gz ** 2)
    # User acceleration along gravity, sign flipped so + = upwards (gravity points down).
    av = -(acc.x.to_numpy() * gx + acc.y.to_numpy() * gy + acc.z.to_numpy() * gz) / gn
    return acc["seconds_elapsed"].to_numpy(), av, acc["time"].to_numpy(dtype="int64")


def window_features(d):
    t, av, _ = vertical_acc(d)
    loc = d["Location"]
    ls, lv = loc["seconds_elapsed"].to_numpy(), loc["speed"].to_numpy()
    grav = d["Gravity"]
    rows = []
    lags = np.arange(int(FS * STEP_INTERVAL[0]), int(FS * STEP_INTERVAL[1]) + 1)
    n_win = int(WIN_S * FS)
    starts = np.arange(t[0], t[-1] - WIN_S, HOP_S)
    i0s = np.searchsorted(t, starts)
    for w0, i0 in zip(starts, i0s):
        x = av[i0:i0 + n_win]
        if len(x) < 0.9 * n_win:
            continue
        xc = x - x.mean()
        f, P = welch(xc, fs=FS, nperseg=256)
        band = (f >= STEP_BAND[0]) & (f <= STEP_BAND[1])
        tot = (f >= TOTAL_BAND[0]) & (f <= TOTAL_BAND[1])
        ac = np.correlate(xc, xc, "full")[len(xc) - 1:]
        ac = ac / ac[0] if ac[0] > 0 else ac
        k = lags[np.argmax(ac[lags])]
        sp = lv[(ls >= w0) & (ls < w0 + WIN_S)]
        sp = sp[sp >= 0]
        gw = grav.iloc[i0:i0 + n_win]
        rows.append({"t_start": round(float(w0), 2), "t_mid": float(w0 + WIN_S / 2),
                     "sd_v": float(x.std()),
                     "step_frac": float(P[band].sum() / P[tot].sum()) if P[tot].sum() > 0 else 0.0,
                     "step_ac": float(ac[k]), "cadence": float(FS / k),
                     "speed_kmh": float(np.median(sp) * 3.6) if len(sp) else np.nan,
                     "grav_x": float(gw.x.mean()), "grav_y": float(gw.y.mean()),
                     "grav_z": float(gw.z.mean())})
    w = pd.DataFrame(rows)
    w["label_raw"] = [classify(r) for r in w.itertuples()]
    w["label"] = smooth(w["label_raw"].tolist())
    return w


def classify(r):
    spd = r.speed_kmh
    no_spd = np.isnan(spd)
    if r.sd_v < STATIONARY_SD and (no_spd or spd < STATIONARY_MAX_KMH):
        return "stationary"
    if r.step_ac >= WALK_AC and r.step_frac >= WALK_STEPFRAC and (no_spd or spd < WALK_MAX_KMH):
        return "walking"
    if not no_spd and spd >= SCOOT_MIN_KMH and r.step_frac < SCOOT_MAX_STEPFRAC:
        return "scooting"
    return "unclear"


def smooth(labels, k=SMOOTH_WINDOWS):
    h = k // 2
    out = []
    for i in range(len(labels)):
        seg = labels[max(0, i - h): i + h + 1]
        vals, counts = np.unique(seg, return_counts=True)
        best = vals[counts == counts.max()]
        out.append(labels[i] if labels[i] in best else best[0])
    return out


def segments(w):
    lab = w["label"].to_numpy()
    cut = np.flatnonzero(lab[1:] != lab[:-1]) + 1
    rows = []
    for a, b in zip(np.r_[0, cut], np.r_[cut, len(lab)]):
        rows.append({"label": lab[a], "t_start": w["t_start"].iloc[a],
                     "t_end": w["t_start"].iloc[b - 1] + HOP_S,
                     "median_speed_kmh": round(float(w["speed_kmh"].iloc[a:b].median()), 1),
                     "median_cadence": round(float(w["cadence"].iloc[a:b].median()), 2)})
    s = pd.DataFrame(rows)
    s["duration_s"] = s["t_end"] - s["t_start"]
    return s


def step_peaks(d):
    t, av, tns = vertical_acc(d)
    sos = butter(2, [0.8, 4.0], btype="band", fs=FS, output="sos")
    y = sosfiltfilt(sos, av)
    pk, _ = find_peaks(y, prominence=STEP_PROMINENCE, distance=int(STEP_INTERVAL[0] * FS))
    return t, y, pk, tns


def walk_onsets(d, segs):
    """For each walking bout >= MIN_WALK_BOUT_S: bout start (window rule) and the
    refined onset (first step of the regular step sequence leading into the bout)."""
    t, y, pk, tns = step_peaks(d)
    tp = t[pk]
    loc = d["Location"]
    lv = loc[loc["speed"] >= 0]
    out = []
    for s in segs[(segs["label"] == "walking") & (segs["duration_s"] >= MIN_WALK_BOUT_S)].itertuples():
        inside = np.flatnonzero((tp >= s.t_start) & (tp < s.t_end))
        if not len(inside):
            continue
        j = inside[0]
        while j > 0 and STEP_INTERVAL[0] <= tp[j] - tp[j - 1] <= STEP_INTERVAL[1]:
            j -= 1
        onset_t = tp[j]
        n_steps = len(inside)
        # GPS lag: first fix after the first step from which GPS speed exceeds
        # GPS_MOVING_KMH on GPS_MOVING_FIXES consecutive fixes.
        after = lv[lv["seconds_elapsed"] >= onset_t]
        mv = (after["speed"].to_numpy() * 3.6 > GPS_MOVING_KMH).astype(int)
        run = np.convolve(mv, np.ones(GPS_MOVING_FIXES, int), "valid")
        k = np.flatnonzero(run == GPS_MOVING_FIXES)
        gps_lag = round(float(after["seconds_elapsed"].iloc[k[0]] - onset_t), 1) if len(k) else np.nan
        out.append({"bout_start_s": s.t_start, "bout_end_s": s.t_end,
                    "bout_duration_s": s.duration_s, "first_step_s": round(float(onset_t), 2),
                    "first_step_local": local_time([tns[pk[j]]])[0].strftime("%Y-%m-%d %H:%M:%S.%f")[:-4],
                    "steps_in_bout": int(n_steps), "gps_moving_lag_s": gps_lag,
                    "median_cadence": s.median_cadence, "median_speed_kmh": s.median_speed_kmh})
    return pd.DataFrame(out), (t, y, pk)


def gps_speed_by_activity(d, segs):
    """For each walking or scooting segment >= MIN_SPEED_SEG_S (trimmed by
    SPEED_SEG_TRIM_S at both ends): median GPS-reported speed vs speed from positions
    (summed fix-to-fix distance, which GPS jitter inflates; and straight-line distance
    between first and last fix, a lower bound on distance travelled)."""
    loc = d["Location"]
    rows = []
    for s in segs[segs["label"].isin(["walking", "scooting"])
                  & (segs["duration_s"] >= MIN_SPEED_SEG_S)].itertuples():
        a, b = s.t_start + SPEED_SEG_TRIM_S, s.t_end - SPEED_SEG_TRIM_S
        g = loc[(loc["seconds_elapsed"] >= a) & (loc["seconds_elapsed"] <= b)]
        if len(g) < 10:
            continue
        T = g["seconds_elapsed"].iloc[-1] - g["seconds_elapsed"].iloc[0]
        path = haversine_m(g.latitude.values[:-1], g.longitude.values[:-1],
                           g.latitude.values[1:], g.longitude.values[1:]).sum()
        line = haversine_m(g.latitude.values[0], g.longitude.values[0],
                           g.latitude.values[-1], g.longitude.values[-1])
        rep = g.loc[g["speed"] >= 0, "speed"]
        rows.append({"label": s.label, "t_start_local": s.t_start_local, "t_end_local": s.t_end_local,
                     "seconds_used": round(float(T), 1), "fixes": len(g),
                     "reported_median_kmh": round(float(rep.median() * 3.6), 2),
                     "path_kmh": round(float(path / T * 3.6), 2),
                     "straight_line_kmh": round(float(line / T * 3.6), 2),
                     "hacc_median_m": round(float(g["horizontalAccuracy"].median()), 1),
                     "median_cadence": s.median_cadence})
    return pd.DataFrame(rows)


def evaluate_ground_truth(gt, segs_all, ons, wins):
    rows = []
    for r in gt.itertuples():
        segs = segs_all[segs_all["recording"] == r.recording]
        on = ons[ons["recording"] == r.recording] if len(ons) else ons
        w = wins.get(r.recording)
        out = {"recording": r.recording, "event": r.event, "reference": r.local_time if isinstance(r.local_time, str) else "",
               "precision": r.precision, "source": r.source}
        if w is None:
            out["result"] = "recording not analysed"
        elif r.event == "walking_start":
            truth = pd.Timestamp(r.local_time)
            cand = pd.to_datetime(on["first_step_local"])
            if len(cand):
                k = int(np.argmin(np.abs((cand - truth).dt.total_seconds()).to_numpy()))
                out["detected"] = on["first_step_local"].iloc[k]
                out["difference_s"] = round((cand.iloc[k] - truth).total_seconds(), 1)
                out["result"] = "difference within the reference's precision" \
                    if "minute" in str(r.precision) and abs(out["difference_s"]) < 60 else "see difference"
            else:
                out["result"] = "no walking bout detected"
        elif r.event == "no_walking":
            n_raw = int((w["label_raw"] == "walking").sum())
            n_s = int((w["label"] == "walking").sum())
            ride_fp = int(((w["label_raw"] == "walking") & (w["speed_kmh"] >= SCOOT_MIN_KMH)).sum())
            bouts = int(len(on))
            out["detected"] = (f"{n_s} s labelled walking after smoothing ({100 * n_s / len(w):.1f}% of "
                               f"{len(w)} windows; {n_raw} before smoothing); {bouts} walking bouts >= "
                               f"{MIN_WALK_BOUT_S:g} s; {ride_fp} walking windows at GPS >= {SCOOT_MIN_KMH:g} km/h")
            out["result"] = "false-positive windows only, no false bout" if bouts == 0 else "false-positive bout(s)"
        elif r.event == "rental_end":
            t0 = pd.Timestamp(r.local_time)
            lo, hi = t0, t0 + pd.Timedelta(seconds=60)
            day = t0.strftime("%Y-%m-%d ")
            sc = segs[(segs["label"] == "scooting")]
            sc_end = [pd.Timestamp(day + x) for x in sc["t_end_local"]]
            last_sc = max([x for x in sc_end if x <= hi], default=None)
            walk = [pd.Timestamp(x) for x in on["first_step_local"]] if len(on) else []
            next_walk = min([x for x in walk if last_sc is not None and x >= last_sc], default=None)
            out["detected"] = (f"last scooting segment ends {last_sc.strftime('%H:%M:%S') if last_sc is not None else '-'}; "
                               f"next walking bout first step {next_walk.strftime('%H:%M:%S.%f')[:-4] if next_walk is not None else '-'}")
            ok = last_sc is not None and last_sc < hi and (next_walk is None or next_walk >= lo)
            out["result"] = (f"order consistent: riding ends before the rental-end minute closes and walking starts "
                             f"after it opens ({lo.strftime('%H:%M:%S')}-{hi.strftime('%H:%M:%S')})" if ok
                             else "order NOT consistent with the reference")
        else:
            out["result"] = "event type not evaluated"
        rows.append(out)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------ figures
def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("#bbbbbb")
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.grid(color="#ececec", lw=0.6)
    ax.set_axisbelow(True)


def fig_timeline(name, d, w, segs, onsets, path):
    t0_ns = int(d["Accelerometer"]["time"].iloc[0])
    t0_s = float(d["Accelerometer"]["seconds_elapsed"].iloc[0])
    to_dt = lambda s: local_time([t0_ns + int((np.asarray(s) - t0_s) * 1e9)])[0] \
        if np.isscalar(s) else local_time(t0_ns + ((np.asarray(s) - t0_s) * 1e9).astype("int64"))
    x = to_dt(w["t_mid"].to_numpy()).tz_localize(None)
    fig, axes = plt.subplots(4, 1, figsize=(11, 7.2), sharex=True,
                             gridspec_kw={"height_ratios": [1, 1, 1, 0.45]})
    loc = d["Location"]
    lv = loc[loc["speed"] >= 0]
    lx = to_dt(lv["seconds_elapsed"].to_numpy()).tz_localize(None)
    axes[0].plot(lx, lv["speed"] * 3.6, color=INK, lw=1)
    axes[0].axhline(SCOOT_MIN_KMH, color=MUTED, lw=0.8, ls=":")
    axes[0].set_ylabel("GPS speed\n(km/h)", fontsize=9)
    axes[1].plot(x, w["sd_v"], color=INK, lw=1)
    axes[1].axhline(STATIONARY_SD, color=MUTED, lw=0.8, ls=":")
    axes[1].set_ylabel("Vertical accel.\nSD (m/s²)", fontsize=9)
    axes[2].plot(x, w["step_ac"], color=INK, lw=1)
    axes[2].axhline(WALK_AC, color=MUTED, lw=0.8, ls=":")
    axes[2].set_ylim(-0.3, 1)
    axes[2].set_ylabel("Step regularity\n(autocorr.)", fontsize=9)
    ax = axes[3]
    for s in segs.itertuples():
        a, b = to_dt(s.t_start).tz_localize(None), to_dt(s.t_end).tz_localize(None)
        ax.axvspan(a, b, color=COLORS[s.label], lw=0)
        for a_ in axes[:3]:
            if s.label == "walking":
                a_.axvspan(a, b, color=COLORS["walking"], alpha=0.12, lw=0)
    for i, o in enumerate(onsets.itertuples()):
        ox = to_dt(o.first_step_s).tz_localize(None)
        for a_ in axes:
            a_.axvline(ox, color=COLORS["walking"], lw=1.2)
        axes[0].annotate(f"walking bout from {o.first_step_local[11:19]}", (ox, axes[0].get_ylim()[1]),
                         xytext=(4, -10 - 13 * i), textcoords="offset points", fontsize=8.5, color=INK)
    ax.set_yticks([])
    ax.set_ylabel("Activity", fontsize=9)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[k]) for k in COLORS]
    ax.legend(handles, list(COLORS), ncol=4, frameon=False, fontsize=8.5,
              loc="upper center", bbox_to_anchor=(0.5, -0.9))
    for a_ in axes:
        _style(a_)
    ax.grid(False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_xlabel(f"Local time ({TZ})", fontsize=9)
    fig.suptitle(f"{name}: dotted lines = classification thresholds (analyst choices)",
                 fontsize=9, color=MUTED, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_onset(name, d, w, segs, steps, onset, path, before=20.0, after=20.0):
    """Transition into a walking bout: from the end of the last scooting segment before
    it (minus `before` s) to `after` s past the first step. Top: GPS speed; middle:
    band-passed vertical acceleration with detected steps; bottom: window labels."""
    t, y, pk = steps
    a = onset.first_step_s
    prev = segs[(segs["label"] == "scooting") & (segs["t_end"] <= a)]
    lo = (prev["t_end"].iloc[-1] if len(prev) else a) - before
    lo = min(lo, a - before)
    hi = a + after
    loc = d["Location"]
    lv = loc[(loc["speed"] >= 0) & (loc["seconds_elapsed"] >= lo) & (loc["seconds_elapsed"] <= hi)]
    m = (t >= lo) & (t <= hi)
    p = pk[(t[pk] >= lo) & (t[pk] <= hi)]
    fig, axes = plt.subplots(3, 1, figsize=(10, 5.2), sharex=True,
                             gridspec_kw={"height_ratios": [0.8, 1.2, 0.3]})
    axes[0].plot(lv["seconds_elapsed"] - a, lv["speed"] * 3.6, color=INK, lw=1.2, marker="o", ms=2.5)
    axes[0].axhline(SCOOT_MIN_KMH, color=MUTED, lw=0.8, ls=":")
    axes[0].set_ylabel("GPS speed\n(km/h)", fontsize=9)
    axes[1].plot(t[m] - a, y[m], color=INK, lw=0.7)
    axes[1].plot(t[p] - a, y[p], ls="none", marker="o", ms=3.5, color=COLORS["walking"],
                 label="step-like peaks")
    axes[1].set_ylabel("Vertical accel.,\n0.8-4 Hz (m/s²)", fontsize=9)
    axes[1].legend(frameon=False, fontsize=8, loc="upper left")
    for sg in segs[(segs["t_end"] > lo) & (segs["t_start"] < hi)].itertuples():
        axes[2].axvspan(max(sg.t_start, lo) - a, min(sg.t_end, hi) - a, color=COLORS[sg.label], lw=0)
    axes[2].set_yticks([])
    axes[2].set_ylabel("Label", fontsize=9)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[k]) for k in COLORS]
    axes[2].legend(handles, list(COLORS), ncol=4, frameon=False, fontsize=8,
                   loc="upper center", bbox_to_anchor=(0.5, -1.6))
    for ax in axes:
        ax.axvline(0, color=COLORS["walking"], lw=1.2)
        _style(ax)
    axes[2].grid(False)
    axes[2].set_xlabel(f"Seconds from the first step of the walking bout ({onset.first_step_local[11:22]} local)",
                       fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------------- report
def write_report(path, summary, all_segs, onsets, gt):
    import html as _h
    def table(df):
        return df.to_html(index=False, border=0, classes="t", na_rep="–")
    body = []
    for name, q in summary.items():
        rec_on = onsets[onsets["recording"] == name]
        segs = all_segs[all_segs["recording"] == name]
        tot = segs.groupby("label")["duration_s"].sum().reindex(list(COLORS)).fillna(0).astype(int)
        body.append(f"<h2>{_h.escape(name)}</h2>"
                    f"<p class='sub'>Start {q['start_local']} · {q['duration_min']} min · "
                    f"time per class (s): " + ", ".join(f"{k} {v}" for k, v in tot.items()) + "</p>"
                    f"<img src='{name}/fig_timeline.png' alt='Activity timeline {name}'>")
        for i, o in enumerate(rec_on.itertuples()):
            body.append(f"<img src='{name}/fig_walk_onset_{i + 1}.png' alt='Walking onset {i + 1}'>")
        if len(rec_on):
            body.append(table(rec_on.drop(columns=["recording"])))
    gt_html = table(gt) if gt is not None and len(gt) else "<p>No ground truth entered yet (data/ground_truth.csv).</p>"
    path.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sensor Logger Validity</title>
<style>
body{{margin:0;background:#fafaf8;color:#222;font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:28px 16px 48px}} h1{{font-size:24px;margin:0 0 6px}}
h2{{font-size:19px;margin:34px 0 4px}} .sub{{color:#6b6b6b;margin:0 0 12px}}
img{{width:100%;height:auto;display:block;margin:10px 0;background:#fff;border:1px solid #e3e2de;border-radius:6px}}
table.t{{border-collapse:collapse;font-size:13px;margin:8px 0;display:block;overflow-x:auto}}
table.t th,table.t td{{padding:4px 8px;border-bottom:1px solid #e3e2de;text-align:left;white-space:nowrap}}
</style></head><body><main>
<h1>Sensor Logger validity: data quality and walking vs scooting</h1>
<p class="sub">Generated by scripts/sensor_validity.py. Thresholds are analyst choices.
Detected times are model estimates; accuracy can only be judged against the ground truth below.</p>
<h2>Ground truth comparison</h2>{gt_html}
<h2>Data quality summary</h2>{table(pd.read_csv(path.parent / 'quality_summary.csv'))}
{''.join(body)}
</main></body></html>""", encoding="utf-8")


def flatten_quality(name, q):
    r = {"recording": name}
    for s in STREAMS + ["Location"]:
        for k in ("rate_hz", "dt_median_ms", "dt_p99_ms", "gaps", "max_gap_s", "non_monotonic",
                  "duplicates", "clock_vs_elapsed_max_ms"):
            r[f"{s}.{k}"] = q[s][k]
    r.update({f"accel_raw_vs_fused.{k}": v for k, v in q["accel_raw_vs_fused"].items()})
    r.update({f"at_rest.{k}": v for k, v in q["at_rest"].items()})
    r.update({f"gps.{k}": v for k, v in q["gps"].items()})
    return r


# --------------------------------------------------------------------------- main
def main():
    warnings.filterwarnings("ignore", message="Mean of empty slice")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    ap.add_argument("--recordings", nargs="*", help="folder names (default: all)")
    ap.add_argument("--out-dir", type=Path, default=Path("outputs/sensor_validity"))
    ap.add_argument("--ground-truth", type=Path, default=Path("data/ground_truth.csv"))
    args = ap.parse_args()
    recs = args.recordings or sorted(p.name for p in args.raw_dir.iterdir()
                                     if p.is_dir() and (p / "Metadata.csv").exists())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary, flat, all_segs, all_on, all_spd, wins = {}, [], [], [], [], {}
    for name in recs:
        print(f"== {name}")
        d = load(args.raw_dir / name)
        od = args.out_dir / name
        od.mkdir(exist_ok=True)
        w = window_features(d)
        segs = segments(w)
        q = quality(d, w)
        q["start_local"] = local_time([int(d["Accelerometer"]["time"].iloc[0])])[0].strftime("%Y-%m-%d %H:%M:%S")
        q["duration_min"] = round(q["Accelerometer"]["duration_s"] / 60, 1)
        on, steps = walk_onsets(d, segs)
        # local clock times for segments
        t0_ns, t0_s = int(d["Accelerometer"]["time"].iloc[0]), float(d["Accelerometer"]["seconds_elapsed"].iloc[0])
        for c in ("t_start", "t_end"):
            segs[c + "_local"] = local_time(t0_ns + ((segs[c] - t0_s) * 1e9).astype("int64")).strftime("%H:%M:%S")
        spd = gps_speed_by_activity(d, segs)
        spd.to_csv(od / "gps_speed_by_activity.csv", index=False)
        all_spd.append(spd.assign(recording=name))
        w.round(4).to_csv(od / "windows.csv", index=False)
        wins[name] = w
        segs.to_csv(od / "segments.csv", index=False)
        (od / "quality.json").write_text(json.dumps(q, indent=2, default=str))
        fig_timeline(name, d, w, segs, on, od / "fig_timeline.png")
        for i, o in enumerate(on.itertuples()):
            fig_onset(name, d, w, segs, steps, o, od / f"fig_walk_onset_{i + 1}.png")
        summary[name] = q
        flat.append(flatten_quality(name, q))
        all_segs.append(segs.assign(recording=name))
        all_on.append(on.assign(recording=name))
        tot = segs.groupby("label")["duration_s"].sum()
        print("  time per class (s):", tot.to_dict())
        if len(on):
            print(on[["first_step_local", "bout_duration_s", "steps_in_bout", "median_cadence",
                      "median_speed_kmh"]].to_string(index=False))
    pd.DataFrame(flat).to_csv(args.out_dir / "quality_summary.csv", index=False)
    segs_all = pd.concat(all_segs)
    segs_all.to_csv(args.out_dir / "segments_all.csv", index=False)
    ons = pd.concat(all_on)
    if len(ons):
        ons = ons[["recording"] + [c for c in ons.columns if c != "recording"]]
    ons.to_csv(args.out_dir / "walking_onsets.csv", index=False)
    spd_all = pd.concat(all_spd)
    spd_all = spd_all[["recording"] + [c for c in spd_all.columns if c != "recording"]]
    spd_all.to_csv(args.out_dir / "gps_speed_by_activity.csv", index=False)
    print("\nGPS speed by activity (segments >= 30 s, trimmed):\n", spd_all.to_string(index=False))

    gt = None
    if args.ground_truth.exists():
        gt = evaluate_ground_truth(pd.read_csv(args.ground_truth, dtype=str), segs_all, ons, wins)
        gt.to_csv(args.out_dir / "ground_truth_comparison.csv", index=False)
        print("\nGround truth comparison:\n", gt.to_string(index=False))
    write_report(args.out_dir / "report.html", summary, segs_all, ons, gt)
    print(f"\nOutputs in {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()
