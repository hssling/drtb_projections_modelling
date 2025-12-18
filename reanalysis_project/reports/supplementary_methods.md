# Supplementary Methods: India TB & DR-TB Reanalysis

## Data provenance
- GTB 2025 snapshot (`annual_notifs.csv`, `sub_annual_notifs.csv`) for national notifications.
- GTB routine drug-resistance counts (`drroutine.rda` → `drroutine.csv`).
- State notifications (2017–2024) from `tb_notifications_comprehensive_17_24.csv`.
- WHO MDR/RR estimates (`mdr_tb_india_burden.csv`), World Bank TB incidence (`SH.TBS.INCD`).

## Processing
- National series: prefer GTB annual; replace latest year with sub-annual monthly sum when available; fallback to summed state totals.
- RR percentages: convert GTB rr.new/rr.ret to prevalence using notification denominators (assume new/retreated split 87/13); blend with WHO RR%; project linearly to 2030.
- State DR burden: forecast state notifications (linear trend) and allocate national DR burden proportional to volume (no state RR data available).

## Time-series modeling
- Models compared: poly_deg1, poly_deg2, manual Holt linear trend, Bayesian linear (OLS posterior). Holdout = last 2 years.
- Metrics saved to `reports/timeseries_model_metrics.csv`; forecasts to `reports/timeseries_model_forecasts.csv`; plot `figures/timeseries_model_comparison.png`.

## Meta-analysis of RR prevalence
- Source: GTB routine counts (India). Denominator: notifications * 0.87 (new), *0.13 (retreated).
- Method: fixed-effect inverse-variance pooling; outputs `reports/meta_rr_summary.csv`, per-year tables, and forest plots `figures/meta_rr_p_new.png`, `figures/meta_rr_p_ret.png`.

## Reproducibility
- Scripts: `scripts/run_reanalysis.py`, `scripts/run_timeseries_compare.py`, `scripts/run_rr_meta.py`.
- Generated tables: `data/processed/*`, `reports/*`.
- Generated figures: `figures/*`.
