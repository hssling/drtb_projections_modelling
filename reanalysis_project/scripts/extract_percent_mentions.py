"""
Extract percentage mentions from PubMed abstracts.

Input:
    - reports/pubmed_search_results.csv (pmid, title, abstract, ...)

Output:
    - reports/pubmed_percent_mentions.csv (pmid, title, percents, n_percents, min, max, mean, context_snippets)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

PERCENT_RE = re.compile(r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*%")


def stable_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def extract_percent_mentions(text: str, *, context_chars: int = 40) -> list[dict]:
    if not isinstance(text, str) or not text.strip():
        return []

    mentions: list[dict] = []
    for m in PERCENT_RE.finditer(text):
        s = m.group(1).strip()
        try:
            val = float(s)
        except ValueError:
            continue
        if 0.0 <= val <= 100.0:
            start = max(0, m.start() - context_chars)
            end = min(len(text), m.end() + context_chars)
            snippet = re.sub(r"\s+", " ", text[start:end]).strip()
            mentions.append({"value_str": s, "value": val, "start": int(m.start()), "end": int(m.end()), "snippet": snippet})
    return mentions


def extract_percent_strings(text: str) -> list[str]:
    return [m["value_str"] for m in extract_percent_mentions(text)]


def _summary_stats(values: list[float]) -> tuple[int, float | None, float | None, float | None]:
    if not values:
        return 0, None, None, None
    n = len(values)
    mn = min(values)
    mx = max(values)
    mean = sum(values) / n
    return n, mn, mx, mean


def build_percent_mentions(
    df: pd.DataFrame,
    *,
    include_empty: bool = False,
    dedupe: bool = False,
    context_chars: int = 40,
) -> pd.DataFrame:
    missing = {"pmid", "title", "abstract"} - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {sorted(missing)}")

    out_rows: list[dict] = []
    for _, row in df.iterrows():
        mentions = extract_percent_mentions(row["abstract"], context_chars=context_chars)
        percents = [m["value_str"] for m in mentions]
        if dedupe:
            percents = stable_unique(percents)
        values: list[float] = []
        if percents:
            for p in percents:
                try:
                    values.append(float(p))
                except ValueError:
                    continue
        n, mn, mx, mean = _summary_stats(values)
        context_snippets = " | ".join([m["snippet"] for m in mentions]) if mentions else ""

        if percents or include_empty:
            out_rows.append(
                {
                    "pmid": row["pmid"],
                    "title": row["title"],
                    "percents": "; ".join(percents),
                    "n_percents": n,
                    "min": mn,
                    "max": mx,
                    "mean": mean,
                    "context_snippets": context_snippets,
                }
            )
    return pd.DataFrame(
        out_rows,
        columns=["pmid", "title", "percents", "n_percents", "min", "max", "mean", "context_snippets"],
    )


def write_percent_mentions_report(
    in_csv: str | Path,
    out_csv: str | Path,
    *,
    include_empty: bool = False,
    dedupe: bool = False,
    context_chars: int = 40,
) -> Path:
    in_csv = Path(in_csv)
    out_csv = Path(out_csv)
    df = pd.read_csv(in_csv)
    out = build_percent_mentions(df, include_empty=include_empty, dedupe=dedupe, context_chars=context_chars)
    out.to_csv(out_csv, index=False)
    return out_csv


def write_percent_mentions_summary(in_csv: str | Path, out_csv: str | Path) -> Path:
    in_csv = Path(in_csv)
    out_csv = Path(out_csv)
    df = pd.read_csv(in_csv)
    if df.empty:
        pd.DataFrame(columns=["pmid", "count", "min", "max", "mean"]).to_csv(out_csv, index=False)
        return out_csv

    def parse_list(s: str) -> list[float]:
        if not isinstance(s, str) or not s.strip():
            return []
        out: list[float] = []
        for part in s.split(";"):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(float(part))
            except ValueError:
                continue
        return out

    rows: list[dict] = []
    for _, r in df.iterrows():
        vals = parse_list(r.get("percents", ""))
        if not vals:
            continue
        rows.append(
            {
                "pmid": r["pmid"],
                "count": len(vals),
                "min": min(vals),
                "max": max(vals),
                "mean": sum(vals) / len(vals),
            }
        )
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    return out_csv


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract percentage mentions from PubMed abstracts.")
    p.add_argument(
        "--in",
        dest="in_csv",
        default=str(Path(__file__).resolve().parents[1] / "reports" / "pubmed_search_results.csv"),
        help="Input CSV path (default: reanalysis_project/reports/pubmed_search_results.csv)",
    )
    p.add_argument(
        "--out",
        dest="out_csv",
        default=str(Path(__file__).resolve().parents[1] / "reports" / "pubmed_percent_mentions.csv"),
        help="Output CSV path (default: reanalysis_project/reports/pubmed_percent_mentions.csv)",
    )
    p.add_argument(
        "--include-empty",
        action="store_true",
        help="Include articles with no percent mentions (empty `percents`).",
    )
    p.add_argument(
        "--dedupe",
        action="store_true",
        help="De-duplicate repeated percent strings per abstract (keeps first occurrence order).",
    )
    p.add_argument(
        "--context-chars",
        type=int,
        default=40,
        help="Number of characters to capture before/after each % mention for quick review.",
    )
    p.add_argument(
        "--summary-out",
        dest="summary_out",
        default="",
        help="Optional path to write a per-PMID summary CSV (count/min/max/mean).",
    )
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    out = write_percent_mentions_report(
        args.in_csv,
        args.out_csv,
        include_empty=args.include_empty,
        dedupe=args.dedupe,
        context_chars=args.context_chars,
    )
    if args.summary_out:
        write_percent_mentions_summary(out, args.summary_out)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
