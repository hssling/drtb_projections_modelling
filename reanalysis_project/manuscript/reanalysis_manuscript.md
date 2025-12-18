# India TB & DR-TB Reanalysis (Reproducible Draft)

## Data & Provenance
- World Bank/WHO TB incidence (indicator SH.TBS.INCD)¹
- National notifications & deaths (2021–2024)²
- State notifications (2017–2024)³
- GTB 2025 snapshot notifications (`annual_notifs.csv`, `sub_annual_notifs.csv`)⁴
- GTB routine RR/MDR counts (`drroutine.rda` → `drroutine.csv`)⁴
- WHO MDR/RR-TB burden estimates (2015–2024)⁵

## Methods (Transparent)
- Prefer GTB annual notifications; replace latest year with sub-annual monthly sum when available; fallback to summed state notifications; cross-check with national file for 2021–2024.
- Time-series comparisons: linear (deg1), quadratic (deg2), Holt-style smoothing, Bayesian linear (OLS posterior); holdout = 2023–2024; metrics in `timeseries_model_metrics.csv`.
- RR% trends built from GTB routine RR counts (rr.new, rr.ret) converted to percentages using notification denominators (assumes new/retreated split 87/13) and blended with WHO MDR/RR estimates; projected linearly to 2030 with residual-based CIs.
- Meta-analysis: fixed-effect pooling of annual RR prevalence (new, retreated) from GTB routine counts; outputs in `meta_rr_summary.csv` and forest plots.
- DR burden = notification volume * RR% (new/retreated split of 87/13).
- State DR burden allocated proportional to notification volume (no state RR data available; modeled estimates only).

## Model Performance
- Best model (RMSE): poly_deg1 (RMSE 1.12M; MAE 0.99M)⁶
- Other models: Bayesian linear (RMSE 1.12M), Holt smoothing (RMSE 1.24M), poly_deg2 (RMSE 1.25M).

## Results
- Projected total notifications in 2030 (poly_deg1): ~2,136,812 (95% CI: ~1.46–2.81M).
- Meta-analysis (GTB routine counts): RR prevalence pooled new = 1.03% (95% CI 1.03–1.04); retreated = 8.76% (95% CI 8.72–8.80) (fixed-effect).
- Projected DR/RR-TB burden in 2030: ~189,619 cases (national, modeled from pooled RR%).
- Top 5 states by modeled 2030 DR/RR-TB burden (allocation by volume):
  - Uttar Pradesh: ~57,948
  - Bihar: ~18,054
  - Maharashtra: ~14,426
  - Rajasthan: ~13,681
  - Madhya Pradesh: ~13,496

## Limitations
- No state-specific RR data; state DR burdens are proportional allocations, not observations.
- RR% from GTB counts uses assumed new/retreated split (87/13); retreated denominator is approximate.
- RR trend projection assumes linear change; sudden program shifts are not captured.
- Notification data are used as incidence proxy; under/over-reporting will influence forecasts.

## Exploratory Literature Snapshot (PubMed Abstracts)
To support rapid screening (not evidence synthesis), we also ran an automated PubMed abstract pull and extracted numeric mentions (percents, plus best-effort denominators/CI parsing).

- Query: `("drug resistant tuberculosis"[MeSH Terms] OR MDR-TB OR RR-TB) AND India AND (prevalence OR survey OR primary resistance OR new cases)`; date range `2018/01/01`–`2025/12/31`; India filter `strict` with exclusions logged.
- Snapshot counts: 104 articles kept; 161 excluded by filter; 68 articles contained ≥1 `%` mention; 537 total `%` mentions extracted (screening aid only).
- Heuristic context categories for extracted `%` mentions (mentions; unique PMIDs): other (208; 48), drug_resistance_profile (166; 45), demographics_comorbidity (88; 27), treatment_outcomes (36; 15), diagnostic_performance (27; 4), epidemiology_burden (12; 10).
- Outputs: `reports/pubmed_search_results.csv`, `reports/pubmed_percent_mentions.csv`, `reports/pubmed_numeric_mentions.csv`, `reports/pubmed_numeric_analysis.md`.

## Assets
- Figures: national forecast, national DR burden, state DR hotspots, RR meta-analysis forest plots, model comparison plot.
- Tables: processed notifications, RR trend projections, DR burden (national & state), time-series model metrics, meta-analysis tables.
