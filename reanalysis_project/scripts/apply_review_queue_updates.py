"""
Apply verified updates from the meta review queue back into the main extraction sheet.

Workflow:
  1) Generate queue: scripts/generate_meta_review_queue.py
  2) Fill verified_* columns in reports/lit_meta_review_queue.csv
  3) Apply updates:
       python3 reanalysis_project/scripts/apply_review_queue_updates.py

Inputs:
  - reports/lit_meta_review_queue.csv
  - reports/lit_meta_extraction.csv

Outputs:
  - reports/lit_meta_extraction_updated.csv (default)

Notes:
  - Only updates PMIDs present in the queue.
  - Only overwrites fields when verified_* is provided (non-empty).
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


def _truthy(x) -> bool:
    if _is_blank(x):
        return False
    s = str(x).strip().lower()
    return s in {"y", "yes", "true", "1", "include", "included"}


def _falsey(x) -> bool:
    if _is_blank(x):
        return False
    s = str(x).strip().lower()
    return s in {"n", "no", "false", "0", "exclude", "excluded"}


def _to_int(x):
    if _is_blank(x):
        return ""
    try:
        return int(float(str(x).strip()))
    except Exception:
        return str(x).strip()


def apply_updates(extraction_csv: Path, queue_csv: Path, out_csv: Path) -> Path:
    ex = pd.read_csv(extraction_csv)
    q = pd.read_csv(queue_csv)

    if ex.empty or q.empty:
        ex.to_csv(out_csv, index=False)
        return out_csv

    required = {"pmid"} - set(q.columns)
    if required:
        raise ValueError(f"Queue is missing required columns: {sorted(required)}")

    ex = ex.copy()
    ex["pmid"] = ex["pmid"].astype(int)
    q = q.copy()
    q["pmid"] = q["pmid"].astype(int)

    q = q.set_index("pmid")

    for pmid, row in q.iterrows():
        idx = ex.index[ex["pmid"] == pmid]
        if len(idx) == 0:
            continue
        i = idx[0]

        # included
        if "verified_included" in row.index and not _is_blank(row["verified_included"]):
            if _truthy(row["verified_included"]):
                ex.at[i, "included"] = "yes"
            elif _falsey(row["verified_included"]):
                ex.at[i, "included"] = "no"
            else:
                ex.at[i, "included"] = str(row["verified_included"]).strip()

        # counts
        if "verified_n_total" in row.index and not _is_blank(row["verified_n_total"]):
            ex.at[i, "n_total"] = _to_int(row["verified_n_total"])
        if "verified_n_resistant" in row.index and not _is_blank(row["verified_n_resistant"]):
            ex.at[i, "n_resistant"] = _to_int(row["verified_n_resistant"])

        # optional notes/url
        if "verified_notes" in row.index and not _is_blank(row["verified_notes"]):
            ex.at[i, "notes"] = str(row["verified_notes"]).strip()
        if "pdf_or_url" in row.index and not _is_blank(row["pdf_or_url"]):
            ex.at[i, "pdf_or_url"] = str(row["pdf_or_url"]).strip()

    ex.to_csv(out_csv, index=False)
    return out_csv


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    p = argparse.ArgumentParser(description="Apply verified updates from lit_meta_review_queue.csv to lit_meta_extraction.csv")
    p.add_argument("--extraction-csv", default=str(reports / "lit_meta_extraction.csv"))
    p.add_argument("--queue-csv", default=str(reports / "lit_meta_review_queue.csv"))
    p.add_argument("--out-csv", default=str(reports / "lit_meta_extraction_updated.csv"))
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    out = apply_updates(Path(args.extraction_csv), Path(args.queue_csv), Path(args.out_csv))
    print(f"Saved {out}")


if __name__ == "__main__":
    main()

