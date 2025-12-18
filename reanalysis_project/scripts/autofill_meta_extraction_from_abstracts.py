"""
Autofill *suggestions* for the meta-analysis extraction sheet using PubMed abstracts.

Important:
  - This is NOT sufficient for a real meta-analysis by itself.
  - It is a screening/triage helper to reduce manual work.

Inputs:
  - reports/pubmed_search_results.csv
  - reports/lit_meta_extraction.csv

Outputs:
  - reports/lit_meta_extraction_autofill.csv (adds auto_* columns; does not overwrite manual fields)
  - reports/lit_meta_autofill_summary.csv
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


FRACTION_RE = re.compile(r"(?P<num>\d{1,7})\s*/\s*(?P<den>\d{1,7})")
PERCENT_RE = re.compile(r"(?<!\d)(?P<pct>\d{1,3}(?:\.\d+)?)\s*%")
PCT_FRACTION_RE = re.compile(
    r"(?P<pct>\d{1,3}(?:\.\d+)?)\s*%\s*\(\s*(?P<num>\d{1,7})\s*/\s*(?P<den>\d{1,7})\s*\)"
)

RESIST_KW_RE = re.compile(
    r"\b(rr[-\s]?tb|rifampicin|rifampin|isoniazid|mdr|xdr|pre[-\s]?xdr|drug[-\s]?resistan)\b",
    re.IGNORECASE,
)
PREV_KW_RE = re.compile(r"\b(prevalen|proportion|rate|found in|detected|isolates|cases|patients)\b", re.IGNORECASE)
NEG_CONTEXT_RE = re.compile(r"\b(sensitivity|specificity|ppv|npv|auc|accuracy)\b", re.IGNORECASE)
DEMOG_CONTEXT_RE = re.compile(r"\b(male|female|median|interquartile|age)\b", re.IGNORECASE)


def _to_int(s: str) -> int | None:
    try:
        return int(s)
    except Exception:
        return None


def _to_float(s: str) -> float | None:
    try:
        return float(s)
    except Exception:
        return None


def guess_drug_resistance_type(title: str, abstract: str) -> str:
    t = f"{title} {abstract}".lower()
    if "pre-xdr" in t or "pre xdr" in t:
        return "pre-XDR"
    if "xdr" in t:
        return "XDR"
    if "rr-tb" in t or "rifampicin-resistant" in t or "rifampin-resistant" in t or "rifamycin resistance" in t:
        return "RR"
    if "mdr-tb" in t or "multidrug-resistant" in t or "multidrug resistant" in t:
        return "MDR"
    if "drug-resistant" in t or "drug resistant" in t or "dr-tb" in t:
        return "DR-TB"
    return ""


def guess_new_or_retreatment(title: str, abstract: str) -> str:
    t = f"{title} {abstract}".lower()
    new = bool(re.search(r"\bnew(ly)?\b", t)) or "new case" in t
    ret = bool(re.search(r"\b(retreat|retreated|previously treated|re-treatment)\b", t))
    if new and not ret:
        return "new"
    if ret and not new:
        return "retreated"
    return ""


@dataclass(frozen=True)
class Candidate:
    num: int
    den: int
    pct: float
    start: int
    end: int
    evidence: str
    score: float


def _score_window(window: str) -> float:
    score = 0.0
    if RESIST_KW_RE.search(window):
        score += 2.0
    if PREV_KW_RE.search(window):
        score += 1.0
    if NEG_CONTEXT_RE.search(window):
        score -= 2.0
    if DEMOG_CONTEXT_RE.search(window):
        score -= 1.0
    return score


def _find_nearby_percent_values(window: str) -> list[float]:
    vals: list[float] = []
    for m in PERCENT_RE.finditer(window):
        v = _to_float(m.group("pct"))
        if v is None:
            continue
        if 0.0 <= v <= 100.0:
            vals.append(v)
    return vals


def pick_best_fraction(abstract: str, *, context_chars: int = 160, tol_pct: float = 1.0) -> Candidate | None:
    if not isinstance(abstract, str) or not abstract.strip():
        return None

    candidates: list[Candidate] = []

    # Prefer explicit "p% (x/y)" patterns when present.
    for m in PCT_FRACTION_RE.finditer(abstract):
        pct = _to_float(m.group("pct"))
        num = _to_int(m.group("num"))
        den = _to_int(m.group("den"))
        if pct is None or num is None or den is None or den <= 0 or num < 0 or num > den:
            continue
        start = m.start()
        end = m.end()
        win_start = max(0, start - context_chars)
        win_end = min(len(abstract), end + context_chars)
        window = abstract[win_start:win_end]
        computed = num / den * 100.0
        pct_ok = abs(pct - computed) <= tol_pct
        score = _score_window(window) + (2.0 if pct_ok else 0.0)
        evidence = re.sub(r"\s+", " ", abstract[max(0, start - 60) : min(len(abstract), end + 60)]).strip()
        candidates.append(Candidate(num=num, den=den, pct=float(pct), start=start, end=end, evidence=evidence, score=score + 3.0))

    # Otherwise, consider standalone fractions.
    for m in FRACTION_RE.finditer(abstract):
        num = _to_int(m.group("num"))
        den = _to_int(m.group("den"))
        if num is None or den is None or den <= 0 or num < 0 or num > den:
            continue
        start = m.start()
        end = m.end()
        win_start = max(0, start - context_chars)
        win_end = min(len(abstract), end + context_chars)
        window = abstract[win_start:win_end]
        pct = num / den * 100.0
        nearby_pcts = _find_nearby_percent_values(window)
        pct_ok = any(abs(p - pct) <= tol_pct for p in nearby_pcts)
        score = _score_window(window) + (1.5 if pct_ok else 0.0)
        evidence = re.sub(r"\s+", " ", abstract[max(0, start - 60) : min(len(abstract), end + 60)]).strip()
        candidates.append(Candidate(num=num, den=den, pct=float(pct), start=start, end=end, evidence=evidence, score=score))

    if not candidates:
        return None
    # Prefer higher score; tie-breaker: larger denominator (more study-like).
    candidates.sort(key=lambda c: (c.score, c.den), reverse=True)
    return candidates[0]


def confidence_from_candidate(c: Candidate | None) -> str:
    if c is None:
        return "none"
    if c.score >= 4.0:
        return "high"
    if c.score >= 2.0:
        return "medium"
    return "low"


def autofill(extraction_csv: Path, pubmed_csv: Path, out_csv: Path, summary_csv: Path) -> tuple[Path, Path]:
    ex = pd.read_csv(extraction_csv)
    pub = pd.read_csv(pubmed_csv)
    pub = pub[["pmid", "abstract", "title", "year", "journal"]].copy()
    merged = ex.merge(pub, on="pmid", how="left", suffixes=("", "_pub"))

    auto_rows: list[dict] = []
    for _, r in merged.iterrows():
        title = str(r.get("title") or r.get("title_pub") or "")
        abstract = str(r.get("abstract") or "")
        cand = pick_best_fraction(abstract)
        conf = confidence_from_candidate(cand)
        auto_rows.append(
            {
                "pmid": r.get("pmid"),
                "auto_n_total": cand.den if cand else "",
                "auto_n_resistant": cand.num if cand else "",
                "auto_prevalence_percent": round(cand.pct, 4) if cand else "",
                "auto_drug_resistance_type": guess_drug_resistance_type(title, abstract),
                "auto_new_or_retreatment": guess_new_or_retreatment(title, abstract),
                "auto_confidence": conf,
                "auto_evidence": cand.evidence if cand else "",
                "auto_suggest_include": "yes" if conf in {"high", "medium"} and cand is not None else "",
            }
        )

    auto = pd.DataFrame(auto_rows)
    out = merged.drop(columns=["abstract"], errors="ignore").merge(auto, on="pmid", how="left")
    out.to_csv(out_csv, index=False)

    # Summary
    if not auto.empty:
        summ = (
            auto.groupby(["auto_confidence", "auto_drug_resistance_type"], as_index=False)
            .agg(pmids=("pmid", "nunique"))
            .sort_values(["auto_confidence", "pmids"], ascending=[True, False])
        )
    else:
        summ = pd.DataFrame(columns=["auto_confidence", "auto_drug_resistance_type", "pmids"])
    summ.to_csv(summary_csv, index=False)
    return out_csv, summary_csv


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    p = argparse.ArgumentParser(description="Autofill meta-extraction suggestions from PubMed abstracts.")
    p.add_argument("--extraction-csv", default=str(reports / "lit_meta_extraction.csv"))
    p.add_argument("--pubmed-csv", default=str(reports / "pubmed_search_results.csv"))
    p.add_argument("--out-csv", default=str(reports / "lit_meta_extraction_autofill.csv"))
    p.add_argument("--summary-csv", default=str(reports / "lit_meta_autofill_summary.csv"))
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    out_csv, summary_csv = autofill(
        Path(args.extraction_csv),
        Path(args.pubmed_csv),
        Path(args.out_csv),
        Path(args.summary_csv),
    )
    print(f"Saved {out_csv}")
    print(f"Saved {summary_csv}")


if __name__ == "__main__":
    main()

