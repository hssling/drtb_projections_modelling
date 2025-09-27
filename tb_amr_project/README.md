# TB-AMR Research Pipeline for India

A comprehensive analytical framework for forecasting multidrug-resistant tuberculosis (MDR-TB) burden in India and evaluating policy interventions.

## 🎯 Research Question
*"What will be the projected burden of MDR-TB and XDR-TB in India over the next decade, and how will scaling up new treatment regimens and stewardship interventions change this trajectory?"*

## 📊 Pipeline Components

### 1. Data Extraction (`extract_tb_data.py` + `icmr_connector.py`)
- **WHO Global TB Report**: Downloads international drug resistance surveillance data
- **ICMR-NTEP Integration**: State/district-level patterns from India's national TB program
- Calculates MDR-TB percentages from case numbers and DST testing volumes
- **Expanded Drugs**: Rifampicin, Isoniazid, Fluoroquinolones, Injectable agents, XDR-TB
- Unifies schema: date, country, state, district, drug, percent_resistant, n_tested, type, source

### 2. Time Series Forecasting (`tb_forecast.py`)
- Multi-model comparison: Prophet, ARIMA, LSTM
- 5-year MDR-TB trend projections with uncertainty bands
- Model metrics: RMSE, MAE, MAPE
- Risk assessment categorizations

### 3. Policy Sensitivity Analysis (`tb_sensitivity.py`)
- Baseline scenario (status quo)
- BPaL/BPaLM regimen rollout (-20% resistance)
- Improved adherence (-15% resistance)
- Comprehensive interventions (-35% resistance)
- Poor stewardship (+10% resistance)

### 4. GIS Hotspot Mapping (`tb_gis_mapping.py`)
- **Auto-Download**: Automatically downloads India state boundaries from GADM.org
- Current MDR-TB state-level prevalence maps
- Forecasted hotspots (5-year projections per state)
- **Publication-Ready**: Choropleth maps with legends and statistical summaries
- **Error Handling**: Multiple fallback URLs and manual download instructions

### 5. Meta-Analysis Module (`tb_meta_analysis.py`)
- PubMed API searches for TB-AMR studies in India
- Automated prevalence data extraction from abstracts
- Pooled estimates with 95% confidence intervals
- Heterogeneity assessment (I² statistic)
- Forest plot generation and export

### 6. Automated Manuscript Generator (`tb_manuscript.py`)
- Complete IMRAD structure manuscripts (Introduction, Methods, Results, Discussion)
- Auto-populated tables, figures, and policy recommendations
- Bibliography with scientific citations
- Export to Markdown or DOCX formats
- Ready for submission to journals like PLOS, Lancet, etc.

### 7. Interactive Streamlit Dashboard (`tb_dashboard.py`)
- **6 Interactive Pages**: Overview, Forecasting, Policy Scenarios, Geographic, Meta-Analysis, Data Explorer
- Real-time data exploration with filters and controls
- Interactive plotly visualizations and exports
- Model comparison and parameter tuning
- Download capabilities for results and figures

**Interactive Web App Command:**
```bash
streamlit run tb_amr_project/pipeline/tb_dashboard.py
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run data extraction
python pipeline/extract_tb_data.py

# Generate MDR-TB forecasts
python pipeline/tb_forecast.py "India" "Rifampicin (proxy MDR)" "new"

# Run sensitivity analysis
python pipeline/tb_sensitivity.py

# View results in data/ and reports/ folders
```

## 📁 Project Structure
```
tb_amr_project/
├── data/                    # Dataset outputs
│   ├── tb_raw/             # Raw WHO downloads
│   ├── tb_merged.csv       # Unified time series
│   ├── forecast_tb_India_*.csv
│   └── sensitivity_tb_India_*.csv
├── pipeline/               # Analysis scripts
│   ├── extract_tb_data.py  # Data extraction
│   ├── tb_forecast.py      # Time series forecasting
│   ├── tb_sensitivity.py   # Policy scenarios
│   └── models.py          # Forecasting models
├── reports/               # Plots and metrics
│   ├── tb_forecast*.png   # Forecast comparisons
│   ├── tb_metrics*.csv    # Model performance
│   └── tb_sensitivity*.png # Scenario analysis
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 📈 Data Highlights
- Historical MDR-TB trends (2017-2023)
- **New Cases**: 1-5% MDR-TB (avg ~3%)
- **Retreated Cases**: 5-20% MDR-TB (avg ~13.5%)
- 5-year forecasts with confidence intervals
- WHO threshold: 5% (moderate burden), 10% (high burden)

## 🔬 Analysis Capabilities

### Forecasting Models
- **Prophet**: Handles seasonality, trends, and uncertainty
- **ARIMA**: Statistical time series with autocorrelation
- **LSTM**: Deep learning for complex pattern recognition

### Policy Scenarios
- Measure impact of BPaL/BPaLM regimens on resistance trends
- Simulate adherence improvement effects
- Quantify consequences of delayed interventions
- Combined strategy evaluations

## 📊 Output Formats
- **CSV**: Forecast data with historical + future projections
- **PNG**: Publication-ready comparison plots
- **Markdown**: Executive summaries and metadata
- **Interactive**: Expandable to web dashboards

## 🏥 Public Health Impact
Addresses India's END-TB Strategy 2035 targets by:
- Quantifying MDR-TB burden trajectories
- Evaluating intervention effectiveness
- Identifying optimal policy combinations
- Supporting evidence-based allocation decisions

## 📚 Dependencies
- pandas, numpy
- matplotlib, seaborn
- prophet (Facebook forecasting)
- statsmodels (ARIMA)
- tensorflow (LSTM)
- scikit-learn (ML utilities)

## 🔄 Future Extensions
- ICMR data integration
- State-level GIS mapping
- Meta-analysis of TB literature
- Automated research manuscript generation
- Web-based interactive dashboard

---

**Developed for India's TB-AMR research and policy evaluation.**
