"""
Generate a compact verification queue for abstract-autofilled meta-extraction rows.

Input:
  - reports/lit_meta_extraction_autofill_applied.csv

Output:
  - reports/lit_meta_review_queue.csv
  - reports/lit_meta_review_queue.md
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd


def pubmed_url(pmid) -> str:
    return f"https://pubmed.ncbi.nlm.nih.gov/{int(pmid)}/"


def generate_queue(in_csv: Path, out_csv: Path, out_md: Path) -> tuple[Path, Path]:
    df = pd.read_csv(in_csv)
    if df.empty:
        pd.DataFrame().to_csv(out_csv, index=False)
        out_md.write_text("# Meta-Extraction Review Queue\n\n(no rows)\n", encoding="utf-8")
        return out_csv, out_md

    inc = df["included"].astype(str).str.strip().str.lower() if "included" in df.columns else pd.Series([""] * len(df))
    q = df[inc == "auto"].copy()
    if q.empty:
        pd.DataFrame().to_csv(out_csv, index=False)
        out_md.write_text("# Meta-Extraction Review Queue\n\n(no `included=auto` rows)\n", encoding="utf-8")
        return out_csv, out_md

    q["pubmed_url"] = q["pmid"].map(pubmed_url)

    keep_cols = [
        "pmid",
        "year",
        "title",
        "journal",
        "pubmed_url",
        "drug_resistance_type",
        "new_or_retreatment",
        "n_resistant",
        "n_total",
        "prevalence_percent",
        "auto_confidence",
        "auto_evidence",
        "notes",
        "pdf_or_url",
    ]
    for c in keep_cols:
        if c not in q.columns:
            q[c] = ""
    q = q[keep_cols]

    # Add blank verification columns for manual work.
    q.insert(len(q.columns), "verified_included", "")
    q.insert(len(q.columns), "verified_n_total", "")
    q.insert(len(q.columns), "verified_n_resistant", "")
    q.insert(len(q.columns), "verified_notes", "")

    q.to_csv(out_csv, index=False)

    # Markdown checklist for quick review.
    lines: list[str] = []
    lines.append("# Meta-Extraction Review Queue\n")
    lines.append("These rows were auto-filled from abstracts and must be verified against full text.\n")
    lines.append("")
    for _, r in q.sort_values(["auto_confidence", "year"], ascending=[True, False]).iterrows():
        lines.append(f"## PMID {int(r['pmid'])} ({r.get('year','')})\n")
        lines.append(f"- Title: {r.get('title','')}\n")
        lines.append(f"- Journal: {r.get('journal','')}\n")
        lines.append(f"- Link: {r.get('pubmed_url','')}\n")
        lines.append(
            f"- Suggested: {r.get('drug_resistance_type','')} {r.get('new_or_retreatment','')} "
            f"n_resistant={r.get('n_resistant','')} n_total={r.get('n_total','')} "
            f"prev%={r.get('prevalence_percent','')}\n"
        )
        lines.append(f"- Auto confidence: {r.get('auto_confidence','')}\n")
        ev = str(r.get("auto_evidence", "") or "").strip()
        if ev:
            lines.append(f"- Evidence: {ev}\n")
        lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_csv, out_md


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    p = argparse.ArgumentParser(description="Generate a review queue for `included=auto` rows.")
    p.add_argument("--in-csv", default=str(reports / "lit_meta_extraction_autofill_applied.csv"))
    p.add_argument("--out-csv", default=str(reports / "lit_meta_review_queue.csv"))
    p.add_argument("--out-md", default=str(reports / "lit_meta_review_queue.md"))
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    out_csv, out_md = generate_queue(Path(args.in_csv), Path(args.out_csv), Path(args.out_md))
    print(f"Saved {out_csv}")
    print(f"Saved {out_md}")


if __name__ == "__main__":
    main()

