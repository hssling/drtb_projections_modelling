"""
Apply abstract-based autofill suggestions into meta-extraction fields (creates a new CSV).

This is intended to quickly identify which rows *might* be meta-analyzable, but it does
not replace full-text extraction/verification.

Input:
  - reports/lit_meta_extraction_autofill.csv

Output:
  - reports/lit_meta_extraction_autofill_applied.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def _is_blank(x) -> bool:
    if x is None:
        return True
    if isinstance(x, float) and np.isnan(x):
        return True
    return str(x).strip() == ""


def _prefer(existing, suggestion):
    return suggestion if _is_blank(existing) and not _is_blank(suggestion) else existing


def apply_autofill(in_csv: Path, out_csv: Path) -> Path:
    df = pd.read_csv(in_csv)

    for col, auto_col in [
        ("n_total", "auto_n_total"),
        ("n_resistant", "auto_n_resistant"),
        ("prevalence_percent", "auto_prevalence_percent"),
        ("drug_resistance_type", "auto_drug_resistance_type"),
        ("new_or_retreatment", "auto_new_or_retreatment"),
    ]:
        if col not in df.columns or auto_col not in df.columns:
            continue
        df[col] = [_prefer(a, b) for a, b in zip(df[col].tolist(), df[auto_col].tolist())]

    if "included" in df.columns and "auto_suggest_include" in df.columns:
        new_included = []
        for inc, auto_inc, conf in zip(
            df["included"].tolist(),
            df["auto_suggest_include"].tolist(),
            df.get("auto_confidence", pd.Series([""] * len(df))).tolist(),
        ):
            if _is_blank(inc) and str(auto_inc).strip().lower() == "yes":
                new_included.append("auto")
            else:
                new_included.append(inc)
        df["included"] = new_included

    if "notes" in df.columns:
        notes = []
        for n, inc in zip(df["notes"].tolist(), df.get("included", pd.Series([""] * len(df))).tolist()):
            if str(inc).strip().lower() == "auto":
                base = "" if _is_blank(n) else str(n).strip()
                tag = "AUTO_FROM_ABSTRACT_NEEDS_VERIFICATION"
                notes.append(f"{base} | {tag}".strip(" |") if base else tag)
            else:
                notes.append(n)
        df["notes"] = notes

    df.to_csv(out_csv, index=False)
    return out_csv


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    p = argparse.ArgumentParser(description="Apply abstract-based autofill suggestions to extraction sheet.")
    p.add_argument("--in-csv", default=str(reports / "lit_meta_extraction_autofill.csv"))
    p.add_argument("--out-csv", default=str(reports / "lit_meta_extraction_autofill_applied.csv"))
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    out = apply_autofill(Path(args.in_csv), Path(args.out_csv))
    print(f"Saved {out}")


if __name__ == "__main__":
    main()

