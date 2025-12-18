"""
Automated PubMed literature retrieval for DR-TB/RR-TB in India.

Default query:
    ("drug resistant tuberculosis"[MeSH Terms] OR MDR-TB OR RR-TB)
    AND India
    AND (prevalence OR survey OR primary resistance OR new cases)
Default years: 2018-2025 (adjustable).

Outputs:
    - reports/pubmed_search_results.csv with PMID, title, journal, year, authors, abstract
    - reports/pubmed_percent_mentions.csv with PMID, title, percents, summary stats, and context snippets
    - reports/pubmed_percent_mentions_summary.csv with count/min/max/mean per PMID
    - reports/pubmed_numeric_mentions.csv with one row per percent mention (best-effort denominators/CI parsing)
    - reports/pubmed_excluded.csv with excluded rows + reason (optional)

Note:
    This does not extract event counts (N and MDR/RR positives); those require manual or
    semi-automated extraction from full texts/tables.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import time
from typing import Iterable, Iterator

import pandas as pd
import requests

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from extract_percent_mentions import write_percent_mentions_report, write_percent_mentions_summary  # noqa: E402
from extract_numeric_mentions import write_numeric_mentions_report  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def chunked(items: list[str], size: int) -> Iterator[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def stable_unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def search_pubmed(
    session: requests.Session,
    query: str,
    *,
    mindate: str = "2018/01/01",
    maxdate: str = "2025/12/31",
    batch_size: int = 200,
    max_total: int = 1000,
    tool: str = "tb_amr_reanalysis",
    email: str = "",
    api_key: str = "",
    sleep_s: float = 0.35,
):
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "mindate": mindate,
        "maxdate": maxdate,
        "datetype": "pdat",
        "tool": tool,
    }
    if email:
        params["email"] = email
    if api_key:
        params["api_key"] = api_key

    pmids: list[str] = []
    retstart = 0
    count = None
    while True:
        params["retstart"] = retstart
        params["retmax"] = batch_size
        resp = session.get(f"{BASE}/esearch.fcgi", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json().get("esearchresult", {})
        if count is None:
            try:
                count = int(data.get("count", 0))
            except Exception:
                count = 0
        batch = data.get("idlist", []) or []
        if not batch:
            break
        pmids.extend(batch)
        retstart += len(batch)
        if retstart >= count:
            break
        if max_total and len(pmids) >= max_total:
            pmids = pmids[:max_total]
            break
        time.sleep(sleep_s)
    return stable_unique(pmids)


def fetch_summaries(
    session: requests.Session,
    pmids: list[str],
    *,
    tool: str = "tb_amr_reanalysis",
    email: str = "",
    api_key: str = "",
):
    if not pmids:
        return []

    results: list[dict] = []
    for batch in chunked(pmids, 200):
        ids = ",".join(batch)
        params = {"db": "pubmed", "id": ids, "retmode": "json", "tool": tool}
        if email:
            params["email"] = email
        if api_key:
            params["api_key"] = api_key
        resp = session.get(f"{BASE}/esummary.fcgi", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json().get("result", {})
        for pmid in batch:
            rec = data.get(pmid, {})
            if not rec:
                continue
            results.append(
                {
                    "pmid": pmid,
                    "title": rec.get("title"),
                    "journal": rec.get("fulljournalname"),
                    "year": rec.get("pubdate", "")[:4],
                    "authors": "; ".join([a.get("name") for a in rec.get("authors", []) if a.get("name")]),
                }
            )
    return results


def fetch_abstracts(
    session: requests.Session,
    pmids: list[str],
    *,
    tool: str = "tb_amr_reanalysis",
    email: str = "",
    api_key: str = "",
):
    if not pmids:
        return {}
    from xml.etree import ElementTree as ET

    abstracts: dict[str, str] = {}
    for batch in chunked(pmids, 200):
        ids = ",".join(batch)
        params = {"db": "pubmed", "id": ids, "retmode": "xml", "tool": tool}
        if email:
            params["email"] = email
        if api_key:
            params["api_key"] = api_key
        resp = session.get(f"{BASE}/efetch.fcgi", params=params, timeout=30)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else None
            abst = []
            for ab in article.findall(".//Abstract/AbstractText"):
                if ab.text:
                    abst.append(ab.text.strip())
            if pmid:
                abstracts[pmid] = " ".join(abst)
    return abstracts


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    default_query = (
        '(\"drug resistant tuberculosis\"[MeSH Terms] OR MDR-TB OR RR-TB) '
        "AND India "
        'AND (prevalence OR survey OR primary resistance OR new cases)'
    )
    p = argparse.ArgumentParser(description="Retrieve PubMed records for DR-TB/RR-TB query and export CSV reports.")
    p.add_argument("--query", default=default_query, help="PubMed query string.")
    p.add_argument("--mindate", default="2018/01/01", help='Min publication date, e.g. "2018/01/01".')
    p.add_argument("--maxdate", default="2025/12/31", help='Max publication date, e.g. "2025/12/31".')
    p.add_argument("--batch-size", type=int, default=200, help="Esearch batch size.")
    p.add_argument("--max-total", type=int, default=1000, help="Max PMIDs to retrieve (0 = unlimited).")
    p.add_argument(
        "--india-filter",
        choices=["strict", "loose", "none"],
        default="strict",
        help='Post-filter to reduce affiliation-only matches ("strict" keeps title India or abstract "in India").',
    )
    p.add_argument(
        "--write-excluded",
        action="store_true",
        help="Write excluded records to reports/pubmed_excluded.csv (or --out-excluded-csv).",
    )
    p.add_argument(
        "--out-excluded-csv",
        default=str(REPORTS / "pubmed_excluded.csv"),
        help="Output CSV path for excluded records (pmid/title/year/reason).",
    )
    p.add_argument(
        "--out-search-csv",
        default=str(REPORTS / "pubmed_search_results.csv"),
        help="Output CSV path for search results.",
    )
    p.add_argument(
        "--out-percent-csv",
        default=str(REPORTS / "pubmed_percent_mentions.csv"),
        help="Output CSV path for percent mentions.",
    )
    p.add_argument(
        "--out-percent-summary-csv",
        default=str(REPORTS / "pubmed_percent_mentions_summary.csv"),
        help="Output CSV path for percent mentions summary.",
    )
    p.add_argument(
        "--out-numeric-csv",
        default=str(REPORTS / "pubmed_numeric_mentions.csv"),
        help="Output CSV path for structured numeric mentions (percents/denominators/CI).",
    )
    p.add_argument("--email", default="", help="Optional contact email for NCBI E-utilities.")
    p.add_argument("--api-key", default="", help="Optional NCBI API key for higher rate limits.")
    return p.parse_args(argv)


def main():
    args = parse_args()
    session = requests.Session()

    pmids = search_pubmed(
        session,
        args.query,
        mindate=args.mindate,
        maxdate=args.maxdate,
        batch_size=args.batch_size,
        max_total=args.max_total,
        email=args.email,
        api_key=args.api_key,
    )
    summaries = fetch_summaries(session, pmids, email=args.email, api_key=args.api_key)
    abstracts = fetch_abstracts(session, pmids, email=args.email, api_key=args.api_key)
    for rec in summaries:
        rec["abstract"] = abstracts.get(rec["pmid"], "")
    df = pd.DataFrame(summaries)

    excluded_rows: list[dict] = []

    if args.india_filter != "none":
        tb_kw_re = re.compile(r"\b(tuberculosis|tb|mdr|xdr|rr[-\s]?tb|rifampicin|rifampin|isoniazid)\b", re.IGNORECASE)

        def india_reason(r: pd.Series) -> str | None:
            title = str(r.get("title") or "")
            abstract = str(r.get("abstract") or "")
            if args.india_filter == "loose":
                if re.search(r"\b(india|indian)\b", title, flags=re.IGNORECASE):
                    return None
                if re.search(r"\b(india|indian)\b", abstract, flags=re.IGNORECASE):
                    return None
                return "no_india_mention"

            # strict: require India/Indian in title, or a strong India-in-study-context cue in abstract.
            if re.search(r"\b(india|indian)\b", title, flags=re.IGNORECASE):
                return None
            if re.search(r"\b(in|from|within|across)\s+india\b", abstract, flags=re.IGNORECASE):
                return None
            if re.search(r"\bindian\b", abstract, flags=re.IGNORECASE):
                return None
            if re.search(r"\bindia\b", abstract, flags=re.IGNORECASE):
                return "india_mention_weak_context"
            return "no_india_mention"

        keep_mask = []
        for _, r in df.iterrows():
            reason = india_reason(r)
            keep = reason is None
            keep_mask.append(keep)
            if not keep:
                excluded_rows.append(
                    {
                        "pmid": r.get("pmid"),
                        "year": r.get("year"),
                        "title": r.get("title"),
                        "reason": reason,
                    }
                )
        df = df[pd.Series(keep_mask, index=df.index)].copy()

    if args.write_excluded and excluded_rows:
        pd.DataFrame(excluded_rows).to_csv(Path(args.out_excluded_csv), index=False)

    out_csv = Path(args.out_search_csv)
    df.to_csv(out_csv, index=False)
    percent_csv = Path(args.out_percent_csv)
    write_percent_mentions_report(out_csv, percent_csv, include_empty=False)
    write_percent_mentions_summary(percent_csv, Path(args.out_percent_summary_csv))
    write_numeric_mentions_report(out_csv, Path(args.out_numeric_csv))
    print(f"Found {len(df)} articles. Saved to {out_csv}")


if __name__ == "__main__":
    main()
