"""
Run a simple prevalence meta-analysis from a completed extraction sheet.

Input:
  - reports/lit_meta_extraction.csv

Required fields (per included row):
  - included: truthy (e.g., 'y', 'yes', '1', 'true')
  - n_total, n_resistant (integers)

Optional grouping fields:
  - drug_resistance_type, new_or_retreatment

Outputs:
  - reports/lit_meta_summary.csv (overall + by-group pooled prevalence)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def _is_truthy(x, *, include_auto: bool = False) -> bool:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return False
    s = str(x).strip().lower()
    truthy = {"y", "yes", "true", "1", "include", "included"}
    if include_auto:
        truthy.add("auto")
    return s in truthy


def _to_int(x) -> int | None:
    try:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return None
        return int(float(str(x).strip()))
    except Exception:
        return None


def _logit(p: np.ndarray) -> np.ndarray:
    return np.log(p / (1.0 - p))


def _inv_logit(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


@dataclass(frozen=True)
class MetaResult:
    k: int
    pooled: float
    ci_low: float
    ci_high: float
    tau2: float


def dersimonian_laird_logit(events: np.ndarray, totals: np.ndarray, *, cc: float = 0.5) -> MetaResult:
    """
    Random-effects meta-analysis of proportions using logit transform with continuity correction.
    Returns pooled proportion (0-1) and Wald CI on logit scale.
    """
    if len(events) != len(totals):
        raise ValueError("events and totals length mismatch")
    k = len(events)
    if k == 0:
        return MetaResult(k=0, pooled=np.nan, ci_low=np.nan, ci_high=np.nan, tau2=np.nan)

    e = events.astype(float)
    n = totals.astype(float)
    # continuity correction for 0 or n events
    e_adj = np.where((e == 0) | (e == n), e + cc, e)
    n_adj = np.where((e == 0) | (e == n), n + 2 * cc, n)
    p = np.clip(e_adj / n_adj, 1e-9, 1.0 - 1e-9)

    yi = _logit(p)
    vi = 1.0 / e_adj + 1.0 / (n_adj - e_adj)
    wi = 1.0 / vi

    y_fixed = np.sum(wi * yi) / np.sum(wi)
    q = float(np.sum(wi * (yi - y_fixed) ** 2))
    c = float(np.sum(wi) - (np.sum(wi**2) / np.sum(wi)))
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0

    wi_star = 1.0 / (vi + tau2)
    y_re = float(np.sum(wi_star * yi) / np.sum(wi_star))
    se_re = float(np.sqrt(1.0 / np.sum(wi_star)))
    z = 1.96
    lo = y_re - z * se_re
    hi = y_re + z * se_re

    pooled = float(_inv_logit(np.array([y_re]))[0])
    ci = _inv_logit(np.array([lo, hi]))
    return MetaResult(k=k, pooled=pooled, ci_low=float(ci[0]), ci_high=float(ci[1]), tau2=float(tau2))


def run_meta(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    out_rows: list[dict] = []

    def add_group(grp_name: str, sub: pd.DataFrame):
        ev = sub["n_resistant"].to_numpy(dtype=float)
        tot = sub["n_total"].to_numpy(dtype=float)
        res = dersimonian_laird_logit(ev, tot)
        out_rows.append(
            {
                "group": grp_name,
                "k": res.k,
                "pooled_percent": res.pooled * 100.0,
                "ci_low_percent": res.ci_low * 100.0,
                "ci_high_percent": res.ci_high * 100.0,
                "tau2": res.tau2,
                "n_total_sum": float(np.sum(tot)),
                "n_resistant_sum": float(np.sum(ev)),
            }
        )

    add_group("overall", df)

    if group_cols:
        grouped = df.groupby(group_cols, dropna=False)
        for keys, sub in grouped:
            if not isinstance(keys, tuple):
                keys = (keys,)
            parts = []
            for c, k in zip(group_cols, keys):
                parts.append(f"{c}={k if str(k).strip() else 'NA'}")
            add_group(" | ".join(parts), sub)

    return pd.DataFrame(out_rows).sort_values(["group"])


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    p = argparse.ArgumentParser(description="Run meta-analysis from literature extraction sheet.")
    p.add_argument("--in-csv", default=str(reports / "lit_meta_extraction.csv"))
    p.add_argument("--out-csv", default=str(reports / "lit_meta_summary.csv"))
    p.add_argument(
        "--group-by",
        default="drug_resistance_type,new_or_retreatment",
        help="Comma-separated columns to stratify summary (empty to disable).",
    )
    p.add_argument(
        "--include-auto",
        action="store_true",
        help='Treat `included=auto` as included (for provisional, abstract-based runs).',
    )
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.in_csv)
    df = df.copy()
    df["included_bool"] = df["included"].map(lambda x: _is_truthy(x, include_auto=args.include_auto))
    df = df[df["included_bool"]].copy()

    df["n_total"] = df["n_total"].map(_to_int)
    df["n_resistant"] = df["n_resistant"].map(_to_int)
    df = df.dropna(subset=["n_total", "n_resistant"])
    df = df[(df["n_total"] > 0) & (df["n_resistant"] >= 0) & (df["n_resistant"] <= df["n_total"])].copy()

    group_cols = [c.strip() for c in (args.group_by or "").split(",") if c.strip()]
    for c in group_cols:
        if c not in df.columns:
            raise ValueError(f"--group-by column not found in input: {c}")

    out = run_meta(df, group_cols)
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False)
    print(f"Saved {args.out_csv}")


if __name__ == "__main__":
    main()
