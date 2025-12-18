# PubMed Abstract Numeric Mentions (Exploratory)

This report summarizes **automatically extracted numeric mentions** from PubMed abstracts.

- These extracts are intended for **screening/triage**, not evidence synthesis.

- Percent values may refer to demographics, diagnostics, outcomes, or non-India contexts.


## Snapshot

- Articles kept after India filter: 104
- Articles excluded by filter: 161
- Articles with ≥1 percent mention: 68
- Total percent mentions (rows in `pubmed_numeric_mentions.csv`): 537

## Top Articles by Percent Mentions


| pmid | year | n_percents | min | max | mean |
|---:|:---:|---:|---:|---:|---:|
| 40669825 | 2025.0 | 34 | 0.00 | 93.60 | 44.55 |
| 33067551 | 2020.0 | 28 | 1.30 | 95.00 | 50.82 |
| 29596221 | 2018.0 | 25 | 5.60 | 87.30 | 30.81 |
| 31408508 | 2019.0 | 18 | 4.00 | 97.00 | 73.44 |
| 40844110 | 2025.0 | 16 | 86.80 | 95.00 | 94.03 |
| 31151492 | 2019.0 | 14 | 16.00 | 93.30 | 56.29 |
| 33565479 | 2020.0 | 14 | 7.40 | 94.70 | 43.65 |
| 39067941 | 2024.0 | 14 | 4.44 | 93.33 | 35.81 |
| 30319946 | 2018.0 | 13 | 2.10 | 86.91 | 37.74 |
| 29628698 | 2018.0 | 12 | 0.40 | 85.00 | 23.79 |

## Category Breakdown (Heuristic)


| category | mentions | pmids |
|---|---:|---:|
| other | 208 | 48 |
| drug_resistance_profile | 166 | 45 |
| demographics_comorbidity | 88 | 27 |
| treatment_outcomes | 36 | 15 |
| diagnostic_performance | 27 | 4 |
| epidemiology_burden | 12 | 10 |

## Files

- `reanalysis_project/reports/pubmed_search_results.csv`

- `reanalysis_project/reports/pubmed_percent_mentions.csv`

- `reanalysis_project/reports/pubmed_numeric_mentions.csv`

- `reanalysis_project/reports/pubmed_numeric_mentions_by_pmid.csv`

- `reanalysis_project/reports/pubmed_numeric_mentions_category_summary.csv`

- `reanalysis_project/reports/pubmed_excluded.csv`
