# Supplementary Materials Index
## Projected Burden of Multidrug-Resistant Tuberculosis in India (2025–2035)

**Main Manuscript**: IJMR_Submission_DRTB_Forecast_India_2025_Final_v2.docx  
**Authors**: Siddalingaiah H S  
**Date**: December 18, 2025

---

## Overview

This supplementary materials package provides comprehensive technical details, extended analyses, and additional data supporting the main manuscript. The materials are organized into tables, figures, and detailed methodological documentation.

---

## Supplementary Tables

### **Table S1: State-Level MDR-TB Burden Projections (2025-2030)**
📄 **File**: `Supplementary_Table_S1_State_Projections.md`

**Content**:
- Detailed state-by-state projections for all 28 states + 8 Union Territories
- Three scenario projections (Status Quo, Optimistic, Pessimistic) for each state
- Trajectory group classifications (Optimistic, Status Quo, Pessimistic-leaning)
- Geographic burden concentration analysis
- Policy prioritization framework (Tier 1/2/3 states)

**Key Insights**:
- Top 5 states account for 62% of national burden
- 10-fold variation in per-capita burden across states
- Kerala and Himachal Pradesh on elimination trajectory
- Uttar Pradesh and Jharkhand require immediate intensive intervention

---

### **Table S2: Sensitivity Analysis - Damping Parameter Variations**
📄 **File**: `Supplementary_Table_S2_Sensitivity_Analysis.md`

**Content**:
- Systematic sensitivity analysis across damping parameter values (φ = 0.70 to 0.95)
- Model fit statistics (AIC, BIC, RMSE, MAE, R²) for each parameter value
- Projected burden trajectories under different dampening assumptions
- Cumulative impact analysis (cases averted) across parameter range
- Robustness assessment of policy conclusions

**Key Findings**:
- Base case (φ = 0.85) is AIC/BIC-optimized
- Cases averted range: 195,000-244,000 (conservative to optimistic)
- Policy conclusions robust across all plausible parameter values
- Status Quo burden consistently plateaus at 82,000-88,000 cases/year

---

### **Table S3: Model Comparison and Selection Justification**
📄 **File**: `Supplementary_Table_S3_Model_Comparison.md`

**Content**:
- Comprehensive comparison of 7 forecasting models
- In-sample fit statistics (AIC, BIC, RMSE, MAE, MAPE, R²)
- Out-of-sample validation (leave-one-out cross-validation)
- Residual diagnostics (autocorrelation, normality, heteroscedasticity tests)
- Epidemiological plausibility assessment
- Decision matrix with weighted scoring

**Models Evaluated**:
1. Simple Exponential Smoothing
2. Holt's Linear Trend
3. **Holt-Winters Damped Trend** (selected)
4. ARIMA(1,1,1)
5. ARIMA(2,1,2)
6. Polynomial Regression (Degree 2)
7. Polynomial Regression (Degree 3)

**Justification**: Holt-Winters Damped Trend achieved highest weighted score (9.8/10) based on statistical fit, out-of-sample accuracy, epidemiological plausibility, and interpretability.

---

### **Table S4: Bootstrap Confidence Intervals**
📊 **File**: `Bootstrap_Confidence_Intervals.csv`

**Content**:
- Year-by-year forecast uncertainty quantification (2025-2034)
- Bootstrap median, 95% confidence intervals (lower/upper bounds)
- Confidence interval width and relative uncertainty percentages
- Comparison of point estimates vs. bootstrap medians

**Methodology**:
- Parametric bootstrap with 1,000 iterations
- Residual resampling approach
- Percentile-based confidence intervals (95% level)

**Key Results**:
- 2030 CI: 84,205 ± 12,867 cases (15.3% relative uncertainty)
- 2034 CI: 84,772 ± 15,399 cases (18.2% relative uncertainty)
- Uncertainty increases with forecast horizon (expected)

---

## Supplementary Figures

### **Figure S1: Forecast with Bootstrap Uncertainty Quantification**
🖼️ **File**: `Supplementary_Figure_S1_Bootstrap_Uncertainty.png`

**Description**:
- Historical data (2017-2024): Estimated true burden
- Point forecast (2025-2034): Holt-Winters projection
- Bootstrap median forecast
- 95% confidence interval (shaded blue region)
- Vertical line marking forecast start (2025)

**Resolution**: 300 DPI (publication-quality)

**Interpretation**: The widening confidence interval over time reflects increasing uncertainty in long-term projections, consistent with standard forecasting practice. Even the upper bound of the CI remains below 100,000 cases under Status Quo, confirming the stagnation hypothesis.

---

### **Figure S2: Model Residual Diagnostics**
🖼️ **File**: `Supplementary_Figure_S2_Residual_Diagnostics.png`

**Description**: Six-panel diagnostic plot assessing model assumptions:

**(A) Residuals vs. Fitted Values**: Tests for heteroscedasticity
- **Result**: Random scatter around zero (✓ homoscedastic)

**(B) Normal Q-Q Plot**: Tests for normality of residuals
- **Result**: Points closely follow theoretical line (✓ normal)

**(C) Histogram of Residuals**: Visual normality check
- **Result**: Approximately symmetric, centered at zero (✓ normal)

**(D) Autocorrelation Function (ACF)**: Tests for serial correlation
- **Result**: All lags within confidence bounds (✓ no autocorrelation)

**(E) Partial Autocorrelation Function (PACF)**: Tests for higher-order correlation
- **Result**: All lags within confidence bounds (✓ no autocorrelation)

**(F) Residuals Over Time**: Tests for temporal patterns
- **Result**: No systematic trend (✓ time-independent)

**Resolution**: 300 DPI

**Conclusion**: All diagnostic tests confirm model assumptions are satisfied. Residuals are well-behaved (normal, homoscedastic, uncorrelated), validating the Holt-Winters model specification.

---

## Supplementary Materials (Narrative Documents)

### **Material S4: Economic Analysis and Cost-Effectiveness**
📄 **File**: `Supplementary_Material_S4_Economic_Analysis.md`

**Content**:
1. **Cost Parameters**: Direct medical costs, indirect costs, total economic burden per case
2. **Scenario-Based Projections**: 10-year cumulative costs under each scenario
3. **Intervention Costs**: Detailed costing of TPT scale-up, ACF, private sector engagement
4. **Cost-Effectiveness Analysis**: ICER calculations (per case averted, per DALY averted)
5. **Return on Investment**: Financial ROI (4.4:1) and societal ROI (7.1:1)
6. **Budget Impact Analysis**: Annual financing requirements, comparison to current NTEP budget
7. **Sensitivity Analysis**: One-way sensitivity on key economic parameters
8. **Distributional Impact**: Catastrophic expenditure averted, geographic equity
9. **Benchmarking**: Comparison to other health interventions in India
10. **Policy Recommendations**: Financing strategies and economic arguments

**Key Findings**:
- **Total economic burden per MDR-TB case**: $17,380 (direct + indirect costs)
- **Economic burden averted (Optimistic vs. Status Quo)**: $3.8 billion over 10 years
- **Total intervention investment required**: $694 million over 10 years
- **ICER**: $1,278 per DALY averted (cost-effective by WHO standards)
- **ROI**: $4.40 returned for every $1 invested
- **Budget requirement**: 0.09% increase in national health spending

**Policy Implication**: The Optimistic elimination strategy is not only epidemiologically necessary but economically superior to Status Quo.

---

## Supporting Code & Data

### **Bootstrap Analysis Script**
💻 **File**: `generate_bootstrap_uncertainty.py`

**Description**: Python script implementing parametric bootstrap for uncertainty quantification

**Key Functions**:
- `parametric_bootstrap()`: Runs 1,000 bootstrap iterations
- `calculate_confidence_intervals()`: Computes percentile-based CIs
- `generate_uncertainty_table()`: Exports results to CSV
- `plot_forecast_with_uncertainty()`: Creates Figure S1
- `generate_residual_diagnostics()`: Creates Figure S2

**Dependencies**: numpy, pandas, matplotlib, seaborn, statsmodels, scipy

**Execution**: `python generate_bootstrap_uncertainty.py`

**Output**:
- `Bootstrap_Confidence_Intervals.csv`
- `Supplementary_Figure_S1_Bootstrap_Uncertainty.png`
- `Supplementary_Figure_S2_Residual_Diagnostics.png`

---

### **Primary Forecasting Script**
💻 **File**: `authentic_drtb_forecasting_india_2025.py` (in parent directory)

**Description**: Main forecasting model implementation

**Key Components**:
- Historical data loading and validation
- Holt-Winters Damped Trend model fitting
- Scenario generation (Status Quo, Optimistic, Pessimistic)
- Cumulative impact calculations
- JSON output generation

**Output**: `authentic_drtb_forecast_india_2025.json`

---

### **Figure Generation Scripts**
💻 **Files**:
- `generate_authentic_figures.py`: Creates Figures 1 & 2 for main manuscript
- `generate_authentic_map.py`: Creates Figure 3 (state-wise burden map)

---

## File Organization

```
supplementary_materials/
├── Supplementary_Table_S1_State_Projections.md
├── Supplementary_Table_S2_Sensitivity_Analysis.md
├── Supplementary_Table_S3_Model_Comparison.md
├── Supplementary_Material_S4_Economic_Analysis.md
├── Bootstrap_Confidence_Intervals.csv
├── Supplementary_Figure_S1_Bootstrap_Uncertainty.png
├── Supplementary_Figure_S2_Residual_Diagnostics.png
└── Supplementary_Materials_Index.md (this file)
```

---

## Usage Guidelines

### For Reviewers
- **Table S3** provides full justification for model selection
- **Figure S2** demonstrates model assumptions are satisfied
- **Table S2** shows robustness of findings to parameter variations
- **Material S4** addresses economic feasibility questions

### For Policymakers
- **Table S1** enables state-specific planning
- **Material S4** provides budget impact and ROI analysis
- **Figure S1** visualizes forecast uncertainty for risk assessment

### For Researchers
- All code is provided for reproducibility
- Bootstrap methodology is fully documented
- Economic parameters are transparently reported with sources

---

## Citation

When citing supplementary materials, please use:

> Siddalingaiah HS. Supplementary Materials for "Projected Burden of Multidrug-Resistant Tuberculosis in India (2025–2035): A Forecasting Analysis Using Verified National Surveillance Data." 2025.

Individual supplementary items can be cited as:

> Siddalingaiah HS. Supplementary Table S1: State-Level MDR-TB Burden Projections. In: Supplementary Materials for "Projected Burden of MDR-TB in India." 2025.

---

## Contact

For questions regarding supplementary materials:

**Dr. Siddalingaiah H S**  
Independent Researcher  
Email: hssling@yahoo.com

---

## Version History

- **Version 1.0** (December 18, 2025): Initial release with manuscript submission
  - 4 supplementary tables
  - 2 supplementary figures
  - 1 economic analysis document
  - Bootstrap uncertainty quantification
  - Complete code repository

---

**Total Supplementary Package Size**:
- Documents: ~50 pages
- Figures: 2 high-resolution images (300 DPI)
- Data: 1 CSV file
- Code: 3 Python scripts

**Estimated Review Time**: 2-3 hours for comprehensive review

---

## Acknowledgements

Supplementary analyses were conducted using open-source software (Python 3.11, statsmodels, matplotlib). Economic parameters were derived from publicly available sources (WHO, ICMR-NTEP, National Health Accounts).

---

**End of Supplementary Materials Index**
