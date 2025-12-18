"""
Extract structured numeric mentions (percents, denominators, confidence intervals) from PubMed abstracts.

Input:
    - reports/pubmed_search_results.csv (pmid, title, abstract, ...)

Output:
    - reports/pubmed_numeric_mentions.csv (one row per detected percent mention)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

PERCENT_RE = re.compile(r"(?<!\d)(?P<pct>\d{1,3}(?:\.\d+)?)\s*%")
FRACTION_RE = re.compile(r"(?P<num>\d{1,7})\s*/\s*(?P<den>\d{1,7})")
N_EQUALS_RE = re.compile(r"\b[nN]\s*=\s*(?P<n>\d{1,9})\b")
CI_95_RE = re.compile(
    r"\b(?:(?P<level>\d{2})\s*%\s*CI|CI\s*(?P<level2>\d{2})\s*%)[:\s]*"
    r"\(?(?P<low>\d{1,3}(?:\.\d+)?)\s*[-–]\s*(?P<high>\d{1,3}(?:\.\d+)?)\s*%?\)?",
    re.IGNORECASE,
)


def _to_float(s: str) -> float | None:
    try:
        return float(s)
    except Exception:
        return None


def _to_int(s: str) -> int | None:
    try:
        return int(s)
    except Exception:
        return None


def extract_numeric_mentions(text: str, *, window_chars: int = 120, context_chars: int = 50) -> list[dict]:
    if not isinstance(text, str) or not text.strip():
        return []

    rows: list[dict] = []
    for idx, m in enumerate(PERCENT_RE.finditer(text)):
        pct_str = m.group("pct")
        pct = _to_float(pct_str)
        if pct is None or not (0.0 <= pct <= 100.0):
            continue

        win_start = max(0, m.start() - window_chars)
        win_end = min(len(text), m.end() + window_chars)
        window = text[win_start:win_end]

        ctx_start = max(0, m.start() - context_chars)
        ctx_end = min(len(text), m.end() + context_chars)
        context = re.sub(r"\s+", " ", text[ctx_start:ctx_end]).strip()

        # Pick the closest fraction and closest n= within the window.
        closest_fraction = None
        closest_fraction_dist = None
        for fm in FRACTION_RE.finditer(window):
            frac_mid = win_start + (fm.start() + fm.end()) // 2
            dist = abs(frac_mid - (m.start() + m.end()) // 2)
            if closest_fraction_dist is None or dist < closest_fraction_dist:
                closest_fraction_dist = dist
                closest_fraction = fm

        closest_n = None
        closest_n_dist = None
        for nm in N_EQUALS_RE.finditer(window):
            n_mid = win_start + (nm.start() + nm.end()) // 2
            dist = abs(n_mid - (m.start() + m.end()) // 2)
            if closest_n_dist is None or dist < closest_n_dist:
                closest_n_dist = dist
                closest_n = nm

        ci = None
        for cim in CI_95_RE.finditer(window):
            ci = cim
            break

        row = {
            "mention_index": idx,
            "percent": pct,
            "percent_str": pct_str,
            "context_snippet": context,
            "n": _to_int(closest_n.group("n")) if closest_n else None,
            "fraction_num": _to_int(closest_fraction.group("num")) if closest_fraction else None,
            "fraction_den": _to_int(closest_fraction.group("den")) if closest_fraction else None,
            "ci_level": None,
            "ci_low": None,
            "ci_high": None,
        }
        if ci:
            level = ci.group("level") or ci.group("level2")
            row["ci_level"] = _to_int(level) if level else None
            row["ci_low"] = _to_float(ci.group("low"))
            row["ci_high"] = _to_float(ci.group("high"))

        rows.append(row)
    return rows


def build_numeric_mentions(
    df: pd.DataFrame,
    *,
    window_chars: int = 120,
    context_chars: int = 50,
) -> pd.DataFrame:
    missing = {"pmid", "title", "abstract"} - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {sorted(missing)}")

    out_rows: list[dict] = []
    for _, row in df.iterrows():
        mentions = extract_numeric_mentions(row["abstract"], window_chars=window_chars, context_chars=context_chars)
        for m in mentions:
            out_rows.append(
                {
                    "pmid": row["pmid"],
                    "title": row["title"],
                    **m,
                }
            )
    return pd.DataFrame(
        out_rows,
        columns=[
            "pmid",
            "title",
            "mention_index",
            "percent",
            "percent_str",
            "n",
            "fraction_num",
            "fraction_den",
            "ci_level",
            "ci_low",
            "ci_high",
            "context_snippet",
        ],
    )


def write_numeric_mentions_report(
    in_csv: str | Path,
    out_csv: str | Path,
    *,
    window_chars: int = 120,
    context_chars: int = 50,
) -> Path:
    in_csv = Path(in_csv)
    out_csv = Path(out_csv)
    df = pd.read_csv(in_csv)
    out = build_numeric_mentions(df, window_chars=window_chars, context_chars=context_chars)
    out.to_csv(out_csv, index=False)
    return out_csv


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="Extract structured numeric mentions from PubMed abstracts.")
    p.add_argument(
        "--in",
        dest="in_csv",
        default=str(root / "reports" / "pubmed_search_results.csv"),
        help="Input CSV path (default: reanalysis_project/reports/pubmed_search_results.csv)",
    )
    p.add_argument(
        "--out",
        dest="out_csv",
        default=str(root / "reports" / "pubmed_numeric_mentions.csv"),
        help="Output CSV path (default: reanalysis_project/reports/pubmed_numeric_mentions.csv)",
    )
    p.add_argument("--window-chars", type=int, default=120, help="Search window around each percent mention.")
    p.add_argument("--context-chars", type=int, default=50, help="Context snippet size around each percent mention.")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    out = write_numeric_mentions_report(args.in_csv, args.out_csv, window_chars=args.window_chars, context_chars=args.context_chars)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()

