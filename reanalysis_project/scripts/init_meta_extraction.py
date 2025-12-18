"""
Initialize (or update) a structured literature-extraction sheet for real meta-analysis.

This converts the PubMed screening list into a CSV you can fill with full-text extracted
numerators/denominators and definitions.

Input:
  - reports/pubmed_search_results.csv

Output:
  - reports/lit_meta_extraction.csv

Behavior:
  - If the output already exists, preserves any existing manual columns/edits by merging on PMID.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd


EXTRACTION_COLUMNS: list[str] = [
    "pmid",
    "year",
    "title",
    "journal",
    "included",
    "reason_excluded",
    "country",
    "region_state",
    "study_design",
    "setting",
    "population",
    "case_definition",
    "drug_resistance_type",
    "new_or_retreatment",
    "specimen",
    "diagnostic_method",
    "start_year",
    "end_year",
    "n_total",
    "n_resistant",
    "prevalence_percent",
    "ci_low_percent",
    "ci_high_percent",
    "notes",
    "data_source",
    "pdf_or_url",
]


def _empty_extraction_frame() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in EXTRACTION_COLUMNS})


def init_extraction_sheet(pubmed_csv: Path, out_csv: Path) -> Path:
    src = pd.read_csv(pubmed_csv)
    required = {"pmid", "title", "journal", "year"} - set(src.columns)
    if required:
        raise ValueError(f"Missing required columns in {pubmed_csv}: {sorted(required)}")

    base = src[["pmid", "year", "title", "journal"]].copy()
    base["included"] = ""
    base["reason_excluded"] = ""
    for c in EXTRACTION_COLUMNS:
        if c not in base.columns:
            base[c] = ""
    base = base[EXTRACTION_COLUMNS]

    if out_csv.exists():
        existing = pd.read_csv(out_csv)
        # Ensure all expected columns exist in existing
        for c in EXTRACTION_COLUMNS:
            if c not in existing.columns:
                existing[c] = ""
        existing = existing[EXTRACTION_COLUMNS]
        merged = base.merge(existing, on="pmid", how="left", suffixes=("", "_old"))

        # Prefer old/manual values where present, but keep refreshed bibliographic fields.
        for c in EXTRACTION_COLUMNS:
            if c in {"pmid", "year", "title", "journal"}:
                continue
            old = f"{c}_old"
            if old in merged.columns:
                merged[c] = merged[old].where(merged[old].notna() & (merged[old].astype(str).str.len() > 0), merged[c])

        # Clean up suffix columns
        merged = merged[EXTRACTION_COLUMNS]
        out = merged
    else:
        out = base

    out.to_csv(out_csv, index=False)
    return out_csv


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    p = argparse.ArgumentParser(description="Initialize a literature extraction sheet for meta-analysis.")
    p.add_argument("--pubmed-csv", default=str(reports / "pubmed_search_results.csv"))
    p.add_argument("--out-csv", default=str(reports / "lit_meta_extraction.csv"))
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    out = init_extraction_sheet(Path(args.pubmed_csv), Path(args.out_csv))
    print(f"Saved {out}")


if __name__ == "__main__":
    main()

