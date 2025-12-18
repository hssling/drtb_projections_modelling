"""
Compute a simple meta-analysis of RR prevalence using GTB routine counts (India).
- Uses rr.new / notifications (new proxy: notifications * 0.87) and rr.ret / (notifications * 0.13)
- Fixed-effect pooling via inverse-variance weighting.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
FIGS = ROOT / "figures"
REPORTS = ROOT / "reports"

FIGS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


def load_counts():
    rr = pd.read_csv(PROC / "india_rr_routine.csv")
    notif_path = PROC / "national_notifications_gtb_adjusted.csv"
    if notif_path.exists():
        notif = pd.read_csv(notif_path)
    else:
        notif = pd.read_csv(PROC / "national_notifications_gtb.csv")
    notif_series = notif.set_index("year")["notifications"]
    rr = rr.merge(notif_series.rename("notifications"), on="year", how="left")
    rr["new_den"] = rr["notifications"] * 0.87
    rr["ret_den"] = rr["notifications"] * 0.13
    rr["p_new"] = rr["rr.new"] / rr["new_den"]
    rr["p_ret"] = rr["rr.ret"] / rr["ret_den"]
    return rr.dropna(subset=["p_new", "p_ret"])


def fixed_effect(p, n):
    # variance of proportion ~ p(1-p)/n
    var = p * (1 - p) / n
    weight = 1 / var
    pooled = np.sum(weight * p) / np.sum(weight)
    se = np.sqrt(1 / np.sum(weight))
    ci = (pooled - 1.96 * se, pooled + 1.96 * se)
    return pooled, ci


def forest_plot(df, col, out_png):
    plt.figure(figsize=(8, 6))
    y = range(len(df))
    plt.errorbar(df[col] * 100, y, xerr=df["se"] * 100, fmt="o", color="black", ecolor="gray", capsize=4)
    plt.yticks(y, df["year"])
    plt.axvline(df["pooled"].iloc[0] * 100, color="red", linestyle="--", label="Pooled")
    plt.xlabel("RR prevalence (%)")
    plt.title(f"India RR prevalence ({col})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)


def main():
    df = load_counts()
    meta_records = []
    outputs = {}
    for col, den in [("p_new", "new_den"), ("p_ret", "ret_den")]:
        p = df[col]
        n = df[den]
        pooled, ci = fixed_effect(p, n)
        df_meta = df.copy()
        df_meta["pooled"] = pooled
        df_meta["se"] = np.sqrt(p * (1 - p) / n)
        out_csv = REPORTS / f"meta_rr_{col}.csv"
        df_meta.to_csv(out_csv, index=False)
        outputs[col] = {"pooled": pooled, "ci": ci}
        forest_plot(df_meta, col, FIGS / f"meta_rr_{col}.png")
    # save summary
    pd.DataFrame(outputs).to_csv(REPORTS / "meta_rr_summary.csv")
    print("Meta-analysis complete.", outputs)


if __name__ == "__main__":
    main()
