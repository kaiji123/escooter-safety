"""Summary tables for the paper appendices, generated from the model outputs.

Writes, into the paper:
  paper/sections/appendix_impact_list.tex   (Appendix A: all impacts, no coordinates)
  paper/sections/appendix_model_tables.tex  (Appendix E: fall thresholds without the fork,
      sensitivity analysis)
  paper/sections/appendix_bump_tables.tex   (Appendix D: bump fall thresholds)
  paper/sections/ratio_fall_counts.tex      (main text Table 9: ratio-study fall counts)
and, NOT in the paper (they repeat figures, captions or public data), into
paper/supplement/ for a supplement or the data deposit: recent FixMyStreet reports,
full geometry table, consistency values, key-frame runs, ratio and soft-edge thresholds.

Every number comes from a CSV in outputs/; the source file is named in a comment above
each table. Run after scooter_sim.py; rebuild the paper with `python paper/build.py`.
"""
import html
from pathlib import Path

import pandas as pd

SIM = Path("outputs/scooter_sim")
SECTIONS = Path("paper/sections")
SUPP = Path("paper/supplement")      # generated, not included in main.tex
CONFIGS = ["10/10", "11/10", "12/10", "12/12", "14/10"]
# Column headings: 11/10 is the Voiager 5 that was ridden (tyre sidewalls 60/55-8.5 front,
# 60/55-7.5 rear, photographed 2026-10-09); 10/10 is a smaller reference, not the ridden scooter.
HEAD = {"10/10": "10/10 (ref.)", "11/10": "11/10 (V5)"}
CFG_NOTE = ("11/10 (V5) = the Voi Voiager 5 that was ridden; 10/10 (ref.) = smaller "
            "reference wheels.")


def heads(cfgs):
    return [HEAD.get(c, c) for c in cfgs]
NONE = "--"


def mm(x):
    return NONE if pd.isna(x) else f"{x:.0f}"


def table(caption, label, header, rows, colspec, source, note=None):
    """A booktabs table; `rows` are lists of already-formatted cells."""
    out = [f"% {source}", "\\begin{table}[htbp]", "\\centering\\small",
           f"\\caption{{{caption}}}\\label{{{label}}}", f"\\begin{{tabular}}{{@{{}}{colspec}@{{}}}}",
           "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    for r in rows:
        out.append("\\midrule" if r == "midrule" else " & ".join(r) + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    if note:
        out.append(f"\\par\\smallskip\\parbox{{0.92\\linewidth}}{{\\footnotesize {note}}}")
    out.append("\\end{table}\n")
    return "\n".join(out)


def threshold_rows(df, cols, keys=("length_mm", "speed_kmh"), prefix=None):
    """Rows of first-fall depths; rows with no fall in any column are left out."""
    rows = []
    for _, r in df.iterrows():
        if r[cols].isna().all():
            continue
        lead = f"{r[keys[0]]:.0f} mm, {r[keys[1]]:.0f} km/h"
        rows.append(([prefix(r)] if prefix else []) + [lead] + [mm(r[c]) for c in cols])
    return rows


def fall_counts(results_csv):
    d = pd.read_csv(results_csv)
    d["config"] = d["front_in"].astype(int).astype(str) + "/" + d["rear_in"].astype(int).astype(str)
    return d.groupby("config")["fall"].sum().astype(int)


def model_tables():
    parts = ["\\FloatBarrier\n\\subsection{Summary tables}\n",
             "The tables below give the fall thresholds without suspension and the sensitivity "
             "analysis behind the statements in the model sections. Depths are on a 10 mm grid: ``80'' means a first "
             "fall between 70 and 80 mm. -- = no fall up to the deepest case simulated (100 mm). "
             "Rows in which no configuration fell are left out. All values come from the planar "
             "model with assumed parameters (Table~\\ref{tab:4}) and compare configurations; "
             "they are not real-world thresholds.\n"]

    # --- no fork: fall thresholds (counterpart of Table 7)
    ft = pd.read_csv(SIM / "fall_thresholds.csv")
    cols = [f"{c} in" for c in CONFIGS]
    n = fall_counts(SIM / "sim_results.csv")
    rows = threshold_rows(ft, cols)
    rows.append(["\\textbf{Falls (of 81 runs)}"] + [f"\\textbf{{{n[c]}}}" for c in CONFIGS])
    parts.append(table(
        "Shallowest pothole depth (mm) causing a fall, model without suspension "
        "(counterpart of Table~\\ref{tab:7}). " + CFG_NOTE, "tab:Enofork",
        ["Length, speed"] + heads(CONFIGS), rows, "l" + "r" * len(CONFIGS),
        "outputs/scooter_sim/fall_thresholds.csv, sim_results.csv"))

    # --- sensitivity, both models
    for sub, tag, label in (("suspension/", "with front suspension (main model)", "tab:Esensfork"),
                            ("", "without suspension", "tab:Esensnofork")):
        s = pd.read_csv(SIM / sub / "sensitivity.csv")
        s["config"] = s["config"].str.replace(" in", "", regex=False)
        rows = []
        for setting, g in s.groupby("setting", sort=False):
            g = g.set_index("config")
            rows.append([setting.replace("tau", "$\\tau$")] +
                        [f"{mm(g.loc[c, 'first_fall_mm_1000mm_20kmh'])} / {g.loc[c, 'speed_loss_pct_60x600_20kmh']:.1f}\\%"
                         for c in CONFIGS])
        parts.append(table(
            f"Sensitivity analysis, {tag}: first fall depth (mm) on a 1000 mm pothole at "
            f"20 km/h / forward speed lost on a 60 mm deep, 600 mm pothole at 20 km/h. "
            f"One parameter changed at a time from the baseline. " + CFG_NOTE, label,
            ["Setting"] + heads(CONFIGS), rows, "p{40mm}" + "r" * len(CONFIGS),
            f"outputs/scooter_sim/{sub}sensitivity.csv"))

    return "\n".join(parts)


def ratio_count_table():
    """Main-text Table 9: falls per configuration in the ratio study, both models. The
    Appendix E figures show first-fall depths, not counts, so this repeats no figure."""
    nofork = fall_counts(SIM / "ratio" / "ratio_results.csv")
    fork = fall_counts(SIM / "suspension" / "ratio" / "ratio_results.csv")
    runs = pd.read_csv(SIM / "ratio" / "ratio_results.csv").groupby(["front_in", "rear_in"]).size()
    assert runs.nunique() == 1, "unequal runs per configuration"
    # same order as the figures: rear 10 in by front size, then rear 8 in
    order = sorted(nofork.index, key=lambda c: (-int(c.split("/")[1]), int(c.split("/")[0])))
    rows = [[c, f"{int(c.split('/')[0]) / int(c.split('/')[1]):.1f}", str(nofork[c]), str(fork[c])]
            for c in order]
    return table(
        f"Front/rear ratio study: runs meeting the fall criteria (of {runs.iloc[0]} per "
        "configuration). Planar model with assumed parameters (Table~\\ref{tab:4}); relative "
        "comparison of wheel configurations only.", "tab:9",
        ["Front/rear (in)", "Ratio", "Without suspension", "With suspension"], rows, "lrrr",
        "outputs/scooter_sim/ratio/ratio_results.csv, "
        "outputs/scooter_sim/suspension/ratio/ratio_results.csv")


def ratio_edge_tables():
    """Ratio-study and soft-edge thresholds (same data as the Appendix E figures);
    kept out of the paper, written to paper/supplement/ for a supplement or deposit."""
    parts = []
    # --- ratio study, both models
    for sub, tag, label in (("suspension/", "with front suspension", "tab:Eratiofork"),
                            ("", "without suspension", "tab:Eration")):
        r = pd.read_csv(SIM / sub / "ratio" / "ratio_fall_thresholds.csv")
        # same order as the figures: rear 10 in by front size, then rear 8 in
        order = sorted(set(r["config"]), key=lambda c: (-int(c.split("/")[1]), int(c.split("/")[0])))
        w = r.pivot_table(index=["length_mm", "speed_kmh"], columns="config",
                          values="first_fall_mm", aggfunc="first", dropna=False)
        w = w.reindex(columns=order).reset_index()
        phases = set(r["fall_phase"].dropna())
        note = ("All falls began with the front-wheel impact." if phases <= {"front"} else
                "Fall cause by wheel: " + ", ".join(sorted(phases)) + ".")
        parts.append(table(
            f"Front/rear ratio study, {tag}: shallowest pothole depth (mm) causing a fall. "
            f"{note}", label, ["Length, speed"] + order,
            threshold_rows(w, order), "l" + "r" * len(order),
            f"outputs/scooter_sim/{sub}ratio/ratio_fall_thresholds.csv"))

    # --- soft edges
    e = pd.read_csv(SIM / "suspension/soft_edges/edge_fall_thresholds.csv")
    rows = []
    for wdt, g in e.groupby("edge_width_mm"):
        rr = threshold_rows(g, CONFIGS, prefix=lambda r: "sharp" if r["edge_width_mm"] == 0
                            else f"{r['edge_width_mm']:.0f} mm")
        if rows and rr:
            rows.append("midrule")
        rows += rr
    parts.append(table(
        "Soft pothole edges (profile contact, with front suspension): shallowest depth (mm) "
        "causing a fall, by edge width. Fall counts are in Table~\\ref{tab:8}. " + CFG_NOTE,
        "tab:Eedges", ["Edge", "Length, speed"] + heads(CONFIGS), rows, "ll" + "r" * len(CONFIGS),
        "outputs/scooter_sim/suspension/soft_edges/edge_fall_thresholds.csv"))
    return "\n".join(parts)


def bump_tables():
    parts = []
    for sub, tag, label in (("", "without front suspension", "tab:D3"),
                            ("suspension/", "with the front spring", "tab:D4")):
        b = pd.read_csv(SIM / sub / "bumps" / "bump_fall_thresholds.csv")
        rows = threshold_rows(b, CONFIGS, prefix=lambda r: r["case"])
        if not rows:
            rows = [[f"\\multicolumn{{{2 + len(CONFIGS)}}}{{l}}{{No falls in any case.}}"]]
        parts.append(table(
            f"Bumps, model {tag}: lowest bump height (mm) causing a fall. Exploratory; not "
            f"validated against measurements. " + CFG_NOTE, label,
            ["Obstacle", "Length, speed"] + heads(CONFIGS), rows, "ll" + "r" * len(CONFIGS), f"outputs/scooter_sim/{sub}bumps/bump_fall_thresholds.csv"))
    return "\n".join(parts)


def extra_model_tables():
    """Geometry configurations, consistency check values and the key-frame runs."""
    parts = []
    g = pd.read_csv("outputs/wheel_model/configurations.csv")
    short = {"Small-wheel reference (10/10 in)": "10/10 (reference)",
             "Current (11/10 in, Voiager 5)": "11/10 (Voiager 5)",
             "Larger front only (12/10 in)": "12/10 (larger front)",
             "Larger front only (14/10 in)": "14/10 (larger front)",
             "Larger both (12/12 in)": "12/12 (larger both)"}
    rows = [[short.get(r.configuration, r.configuration), f"{r.depth_mm:.0f}", f"{r.front_drop_mm:.0f}", f"{r.front_v_n_ms:.2f}",
             f"{r.front_speed_loss_pct:.1f}\\%", f"{r.rear_v_n_ms:.2f}",
             "--" if r.front_v_n_change_pct == 0 else f"{r.front_v_n_change_pct:+.1f}\\% / {r.front_speed_loss_change_pct:+.1f}\\%"]
            for r in g.itertuples()]
    parts.append(table(
        "Geometry model, all configurations: 600 mm long sharp-edged pothole at 20 km/h. Drop = "
        "how far the front wheel falls before reaching the far edge; impact velocity = component "
        "into the edge; change = front impact velocity / speed loss relative to the 10/10 "
        "reference. Rigid wheels, no tyre or suspension.", "tab:Egeom",
        ["Configuration", "Depth (mm)", "Drop (mm)", "Front (m/s)", "Front loss", "Rear (m/s)", "Change"],
        rows, "lrrrrrr", "outputs/wheel_model/configurations.csv"))
    c = pd.read_csv(SIM / "consistency.csv")
    rows = [[r.model, f"{r.length_mm:.0f}", f"{r.depth_mm:.0f}", f"{r.handlebar_peak_g:.2f}",
             "yes" if r.within_1_to_3_g else "no"] for r in c.itertuples()]
    parts.append(table(
        "Consistency check values (Figure~\\ref{fig:consistency}): simulated handlebar peak for "
        "the current 11/10 (Voiager 5) at 20 km/h on assumed common potholes. Criterion fixed before running: 1--3 g.",
        "tab:Econs", ["Model", "Length (mm)", "Depth (mm)", "Peak (g)", "Within 1--3 g"],
        rows, "lrrrl", "outputs/scooter_sim/consistency.csv"))
    k = pd.read_csv(SIM / "keyframes/keyframes_runs.csv")
    names = {"keyframes_susp_80x600_15kmh": "Fig.~\\ref{fig:5}",
             "keyframes_susp_edge50_80x600_15kmh": "Fig.~\\ref{fig:6}",
             "keyframes_bump_box_90x600_20kmh": "Fig.~\\ref{fig:D1}",
             "keyframes_bump_box_susp_90x300_15kmh": "Fig.~\\ref{fig:D2}"}
    rows = [[names.get(r.figure, r.figure), f"{r.front_in}/{r.rear_in}", "yes" if r.fall else "no",
             "" if pd.isna(r.fall_criterion_time_s) else f"{r.fall_criterion_time_s:.2f}",
             f"{r.speed_loss_pct:.1f}\\%", f"{r.chassis_pitch_max_deg:.1f}", f"{r.rider_lean_max_deg:.1f}"]
            for r in k.itertuples()]
    parts.append(table(
        "The runs drawn as key frames: outcome and measures of each row. Fall time = when the "
        "fall criteria were met, after the front wheel reaches the obstacle.", "tab:Ekey",
        ["Figure", "Config.", "Fall", "Fall time (s)", "Speed lost", "Max pitch (deg)", "Max lean (deg)"],
        rows, "llllrrr", "outputs/scooter_sim/keyframes/keyframes_runs.csv"))
    return "\n".join(parts)


def fms_report_list():
    """Recent FixMyStreet road-surface reports near each ridden route. Reports near the
    trimmed route ends are left out (privacy); addresses and coordinates are not listed."""
    import sys
    sys.path.insert(0, "scripts")
    import paper_part_a as pa
    imps = pd.read_csv("outputs/combined/impacts_all.csv")
    hid = pa.trimmed_points(imps)
    head = "Ride & Created & State & Category: title & Road & To route & Impact $\\leq$25 m \\\\"
    out = ["% outputs/recordings/<rec>/fms_reports_on_route.csv (recent = 365 days before the ride)",
           "\\begingroup\\small",
           "\\begin{longtable}{@{}lll>{\\raggedright\\arraybackslash}p{46mm}lrl@{}}",
           "\\caption{FixMyStreet road-surface reports made in the 365 days before each ride near "
           "its route, as used in Tables~\\ref{tab:A3} and~\\ref{tab:3} (state when downloaded). "
           "Reports near the trimmed route ends are not listed (privacy); addresses are omitted. "
           "A report near an impact does not show that it describes the same defect.}"
           "\\label{tab:Areports}\\\\",
           "\\toprule", head, "\\midrule", "\\endfirsthead", "\\toprule", head, "\\midrule",
           "\\endhead", "\\bottomrule", "\\endlastfoot"]
    n_hidden = 0
    first = True
    for rec in sorted(imps["recording"].unique()):
        rep = pd.read_csv(Path("outputs/recordings") / rec / "fms_reports_on_route.csv")
        rep = rep[rep["recent"].astype(bool)].sort_values("created")
        near = pa._near_hidden(rep["lat"], rep["lon"], hid, radius_m=30)
        n_hidden += int(near.sum())
        if not first:
            out.append("\\midrule")
        first = False
        for r in rep[~near].itertuples():
            title = html.unescape(str(r.title))
            for a, b in (("\\", ""), ("&", "\\&"), ("%", "\\%"), ("#", "\\#"), ("_", "\\_"),
                         ("$", "\\$"), ("{", ""), ("}", ""), ("~", "-"), ("^", "")):
                title = title.replace(a, b)
            out.append(" & ".join([rec[-1], str(r.created)[:10], str(r.state),
                                   f"{r.category}: {title}", str(r.road),
                                   f"{r.dist_to_route_m:.0f} m", "yes" if r.impact_within_radius else ""]) + " \\\\")
    out += ["\\end{longtable}",
            f"\\noindent{{\\footnotesize {n_hidden} further reports lie near the trimmed route ends.}}",
            "\\endgroup\n"]
    return "\n".join(out)


def impact_list():
    """Every detected impact, without coordinates (privacy): locations are given only
    through the spot IDs of Table C1, which hides spots in the trimmed route ends."""
    imps = pd.read_csv("outputs/combined/impacts_all.csv")
    spots = pd.read_csv("outputs/combined/spot_links.csv")
    spot_of = {}
    for r in spots.itertuples():
        for ev in str(r.events).split(";"):
            spot_of[ev.strip()] = r.spot
    imps["rec"] = imps["recording"].str[-5:]
    imps["ride"] = imps["rec"].str[-1].astype(int)
    imps["key"] = imps["rec"] + "#" + imps["event_id"].astype(str)
    yes = lambda b: "yes" if bool(b) else ""
    head = ("Ride & \\# & Time & Peak (g) & Speed (km/h) & Wobble & Road & Report $\\leq$25 m & Spot \\\\")
    out = ["% outputs/combined/impacts_all.csv, outputs/combined/spot_links.csv",
           "\\begingroup\\small",
           "\\begin{longtable}{@{}rrlrrllll@{}}",
           "\\caption{All 100 detected impacts. Time is local (Europe/London); speed is GPS speed "
           "at the impact; wobble = gyroscope ratio $\\geq$ 1.5 after vs before (an analyst "
           "choice); report = a FixMyStreet road-surface report made in the 365 days before the "
           "ride within 25 m; spot = location in Table~\\ref{tab:C1} (spots P9, P16, P30 and P31 lie in the "
           "trimmed route ends and have no location there). "
           "Coordinates are not listed, for privacy; the anonymised dataset is described under "
           "Data availability.}\\label{tab:Aimpacts}\\\\",
           "\\toprule", head, "\\midrule", "\\endfirsthead",
           "\\toprule", head, "\\midrule", "\\endhead",
           "\\bottomrule", "\\endlastfoot"]
    prev = None
    for r in imps.sort_values(["ride", "event_id"]).itertuples():
        if prev is not None and r.ride != prev:
            out.append("\\midrule")
        prev = r.ride
        out.append(" & ".join([str(r.ride), str(r.event_id), str(r.local_time)[11:19],
                               f"{r.peak_abs_g:.2f}", f"{r.speed_kmh:.1f}", yes(r.marked_wobble),
                               str(r.road), yes(r.fms_recent_report_within_25m),
                               spot_of.get(r.key, "")]) + " \\\\")
    out += ["\\end{longtable}", "\\endgroup\n"]
    return "\n".join(out)


if __name__ == "__main__":
    # in the paper
    (SECTIONS / "appendix_impact_list.tex").write_text(impact_list(), encoding="utf-8")
    (SECTIONS / "appendix_model_tables.tex").write_text(model_tables(), encoding="utf-8")
    (SECTIONS / "appendix_bump_tables.tex").write_text(bump_tables(), encoding="utf-8")
    (SECTIONS / "ratio_fall_counts.tex").write_text(ratio_count_table(), encoding="utf-8")
    # not in the paper (they repeat figures, captions or public data): for a supplement/deposit
    SUPP.mkdir(exist_ok=True)
    (SUPP / "fms_reports.tex").write_text(fms_report_list(), encoding="utf-8")
    (SUPP / "model_extra_tables.tex").write_text(extra_model_tables(), encoding="utf-8")
    (SUPP / "ratio_edge_tables.tex").write_text(ratio_edge_tables(), encoding="utf-8")
    print("tables written")
