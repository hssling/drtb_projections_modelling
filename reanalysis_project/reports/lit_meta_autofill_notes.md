# Abstract-Based Meta Extraction (Autofill) — Caveats

Files produced by the autofill workflow are **screening aids** built from PubMed abstracts and regex heuristics.
They are **not a substitute** for full-text/table extraction and can be wrong about which numerator/denominator
corresponds to RR/MDR prevalence in the target population.

## What was generated
- `reanalysis_project/reports/lit_meta_extraction_autofill.csv`: adds `auto_*` suggestion columns (does not overwrite your manual sheet).
- `reanalysis_project/reports/lit_meta_extraction_autofill_applied.csv`: copies `auto_*` into the main fields and sets `included=auto` for suggested rows.
- `reanalysis_project/reports/lit_meta_summary_autofill.csv`: pooled estimates **only when running** `run_meta_from_extraction.py --include-auto`.

## How to use safely
1. Open `reanalysis_project/reports/lit_meta_extraction_autofill_applied.csv`.
2. For each `included=auto` row, verify the `auto_evidence` snippet against the full abstract and (ideally) the PDF.
3. Replace `included=auto` with `included=yes` only after full-text verification, and correct `n_total/n_resistant` if needed.
4. Run `python3 reanalysis_project/scripts/run_meta_from_extraction.py` (without `--include-auto`) to produce a real analysis output.

