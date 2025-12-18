"""
Simple PCA-like clustering for state TB metrics (no sklearn dependency).

Features:
- 2024 notifications
- Growth rate 2017–2024
- Treatment success rate 2023 (%)

Outputs:
- reports/state_clusters.csv
- figures/state_clusters.png
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
FIGS = ROOT / "figures"
REPORTS = ROOT / "reports"

FIGS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


def load_data():
    ts = pd.read_csv(ROOT / "../data/processed/tb_notifications_comprehensive_17_24.csv")
    outcomes = pd.read_csv(ROOT / "../data/processed/tb_notifications_outcomes_state_23_24.csv")
    ts["Growth_17_24"] = (ts["2024"] - ts["2017"]) / ts["2017"]
    merged = pd.merge(
        ts[["State", "2024", "Growth_17_24"]],
        outcomes[["state", "success_rate_2023_pct"]],
        left_on="State",
        right_on="state",
        how="inner",
    )
    merged = merged.rename(columns={"2024": "notif_2024", "success_rate_2023_pct": "success_rate"})
    merged = merged[["State", "notif_2024", "Growth_17_24", "success_rate"]].dropna()
    return merged


def zscore(df: pd.DataFrame) -> pd.DataFrame:
    return (df - df.mean()) / df.std(ddof=0)


def kmeans(data: np.ndarray, k: int = 4, iters: int = 25, seed: int = 42):
    rng = np.random.default_rng(seed)
    n, d = data.shape
    centers = data[rng.choice(n, k, replace=False)]
    for _ in range(iters):
        dists = ((data[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = dists.argmin(axis=1)
        new_centers = np.array([data[labels == j].mean(axis=0) if (labels == j).any() else centers[j] for j in range(k)])
        if np.allclose(new_centers, centers):
            break
        centers = new_centers
    return labels, centers


def main():
    df = load_data()
    features = df[["notif_2024", "Growth_17_24", "success_rate"]]
    X = zscore(features).values
    labels, centers = kmeans(X, k=4)
    df["cluster"] = labels
    df.to_csv(REPORTS / "state_clusters.csv", index=False)

    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(df["notif_2024"], df["success_rate"], c=labels, cmap="tab10", s=80, edgecolors="k")
    plt.xlabel("Notifications 2024")
    plt.ylabel("Success rate 2023 (%)")
    plt.title("State Clusters: Burden vs. Success Rate")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGS / "state_clusters.png", dpi=300)

    print("Cluster counts:", df["cluster"].value_counts().to_dict())
    print("Saved reports/state_clusters.csv and figures/state_clusters.png")


if __name__ == "__main__":
    main()
