# India MDR-TB Forecasting Study (2025-2035)
## Projected Burden of Multidrug-Resistant Tuberculosis in India: A Forecasting Analysis Using Verified National Surveillance Data

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Publication Ready](https://img.shields.io/badge/status-publication%20ready-brightgreen.svg)]()

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Findings](#key-findings)
- [Repository Structure](#repository-structure)
- [Installation & Requirements](#installation--requirements)
- [Quick Start](#quick-start)
- [Detailed Documentation](#detailed-documentation)
- [Interactive Tools](#interactive-tools)
- [Citation](#citation)
- [License](#license)
- [Contact](#contact)

---

## 🔬 Overview

This repository contains the complete research package for a comprehensive forecasting study of India's multidrug-resistant tuberculosis (MDR-TB) burden from 2025 to 2035. The study employs advanced time-series modeling (Holt-Winters Damped Trend Exponential Smoothing) with bootstrap uncertainty quantification to project three distinct future scenarios and quantify the policy gap between current trajectory and elimination targets.

### **Research Question**
Will India's MDR-TB epidemic continue to stagnate at current levels, or can aggressive intervention scale-up achieve elimination targets?

### **Study Period**
- **Historical Data:** 2017-2024 (verified WHO and ICMR-NTEP surveillance)
- **Forecast Period:** 2025-2035 (10-year projections)

### **Methodology**
- **Model:** Holt-Winters Damped Trend Exponential Smoothing (φ = 0.85)
- **Validation:** 7 models compared, optimal selection via AIC/BIC
- **Uncertainty:** Bootstrap confidence intervals (1,000 iterations)
- **Scenarios:** Status Quo, Optimistic, Pessimistic

---

## 🎯 Key Findings

### **Three Possible Futures**

| Scenario | 2030 Burden | 10-Year Cumulative | Interpretation |
|----------|-------------|-------------------|----------------|
| **Status Quo** | 84,205 cases | 841,770 cases | Stagnation - no progress toward elimination |
| **Optimistic** | 59,910 cases | 624,555 cases | Elimination pathway - aggressive intervention |
| **Pessimistic** | 91,782 cases | 913,449 cases | AMR escalation - worsening epidemic |

### **Policy Impact**

- **Cases Averted (Optimistic vs. Status Quo):** 217,215 over 10 years
- **Economic Benefit:** $3.8 billion saved
- **Return on Investment:** 4.4:1 (financial), 7.1:1 (societal)
- **Budget Impact:** Only 0.09% increase in national health spending
- **Cost-Effectiveness:** $1,278 per DALY averted (WHO cost-effective threshold)

### **Required Interventions**

To achieve the Optimistic scenario:
1. **TPT Scale-up:** 15% → 80% coverage for MDR-TB contacts
2. **Active Case Finding:** Intensify screening in high-risk populations
3. **Private Sector Engagement:** Quality standards and unified notification
4. **Treatment Success:** 68% → 85% cure rates

---

## 📁 Repository Structure

```
india-mdrtb-forecasting/
│
├── README.md                          # This file
├── LICENSE                            # MIT License
├── .gitignore                         # Git ignore rules
│
├── manuscript/                        # Main manuscript files
│   ├── IJMR_Submission_DRTB_Forecast_India_2025_Final_v2.docx
│   ├── complete_drtb_manuscript_india_2025.md
│   ├── figures/
│   │   ├── Figure_1_MDR_Burden_Authentic.png (300 DPI)
│   │   ├── Figure_2_Intervention_Scenarios_Authentic.png (300 DPI)
│   │   └── Figure_3_State_Burden_Authentic.png (300 DPI)
│   └── graphical_abstract_mdrtb.png
│
├── supplementary_materials/           # Supplementary tables, figures, analyses
│   ├── Supplementary_Materials_Index.md
│   ├── Supplementary_Table_S1_State_Projections.md
│   ├── Supplementary_Table_S2_Sensitivity_Analysis.md
│   ├── Supplementary_Table_S3_Model_Comparison.md
│   ├── Supplementary_Material_S4_Economic_Analysis.md
│   ├── Bootstrap_Confidence_Intervals.csv
│   ├── Supplementary_Figure_S1_Bootstrap_Uncertainty.png
│   └── Supplementary_Figure_S2_Residual_Diagnostics.png
│
├── data/                              # Data files
│   └── authentic_drtb_forecast_india_2025.json
│
├── code/                              # Analysis scripts
│   ├── authentic_drtb_forecasting_india_2025.py
│   ├── generate_bootstrap_uncertainty.py
│   ├── generate_authentic_figures.py
│   ├── generate_authentic_map.py
│   ├── convert_manuscript_to_docx.py
│   └── requirements.txt
│
├── interactive_dashboard/             # Web-based interactive tools
│   └── MDR_TB_Forecasting_Dashboard.html
│
├── submission_materials/              # Journal submission support
│   ├── Cover_Letter_Template.md
│   ├── Submission_Metadata_Statements.md
│   ├── Plain_Language_Summary.md
│   └── Video_Abstract_Script.md
│
└── documentation/                     # Project documentation
    ├── MANUSCRIPT_VERIFICATION_REPORT.md
    ├── ENHANCEMENT_COMPLETION_REPORT.md
    ├── FINAL_COMPLETION_REPORT.md
    └── REPLICATION_GUIDE.md
```

---

## 💻 Installation & Requirements

### **System Requirements**
- Python 3.8 or higher
- 4GB RAM minimum
- Modern web browser (for interactive dashboard)

### **Python Dependencies**

```bash
# Install all dependencies
pip install -r code/requirements.txt
```

**Core Libraries:**
- `numpy >= 1.21.0`
- `pandas >= 1.3.0`
- `matplotlib >= 3.4.0`
- `seaborn >= 0.11.0`
- `statsmodels >= 0.13.0`
- `scipy >= 1.7.0`
- `python-docx >= 0.8.11`
- `geopandas >= 0.10.0` (for map generation)

---

## 🚀 Quick Start

### **1. Clone the Repository**

```bash
git clone https://github.com/[username]/india-mdrtb-forecasting.git
cd india-mdrtb-forecasting
```

### **2. Install Dependencies**

```bash
pip install -r code/requirements.txt
```

### **3. Run Main Forecasting Analysis**

```bash
cd code
python authentic_drtb_forecasting_india_2025.py
```

**Output:** `data/authentic_drtb_forecast_india_2025.json`

### **4. Generate Bootstrap Uncertainty**

```bash
python generate_bootstrap_uncertainty.py
```

**Output:**
- `supplementary_materials/Bootstrap_Confidence_Intervals.csv`
- `supplementary_materials/Supplementary_Figure_S1_Bootstrap_Uncertainty.png`
- `supplementary_materials/Supplementary_Figure_S2_Residual_Diagnostics.png`

### **5. Generate Manuscript Figures**

```bash
python generate_authentic_figures.py
```

**Output:**
- `manuscript/figures/Figure_1_MDR_Burden_Authentic.png`
- `manuscript/figures/Figure_2_Intervention_Scenarios_Authentic.png`

### **6. Open Interactive Dashboard**

```bash
# Simply open in browser
start ../interactive_dashboard/MDR_TB_Forecasting_Dashboard.html  # Windows
open ../interactive_dashboard/MDR_TB_Forecasting_Dashboard.html   # macOS
xdg-open ../interactive_dashboard/MDR_TB_Forecasting_Dashboard.html  # Linux
```

---

## 📖 Detailed Documentation

### **For Researchers**

- **Methodology:** See `supplementary_materials/Supplementary_Table_S3_Model_Comparison.md`
- **Uncertainty Quantification:** See `supplementary_materials/Supplementary_Figure_S2_Residual_Diagnostics.png`
- **Sensitivity Analysis:** See `supplementary_materials/Supplementary_Table_S2_Sensitivity_Analysis.md`
- **Replication Guide:** See `documentation/REPLICATION_GUIDE.md`

### **For Policymakers**

- **Plain Language Summary:** See `submission_materials/Plain_Language_Summary.md`
- **Economic Analysis:** See `supplementary_materials/Supplementary_Material_S4_Economic_Analysis.md`
- **State-Level Projections:** See `supplementary_materials/Supplementary_Table_S1_State_Projections.md`
- **Interactive Tool:** Open `interactive_dashboard/MDR_TB_Forecasting_Dashboard.html`

### **For Journal Reviewers**

- **Verification Report:** See `documentation/MANUSCRIPT_VERIFICATION_REPORT.md`
- **Data Availability:** See `submission_materials/Submission_Metadata_Statements.md`
- **Code Repository:** All scripts in `code/` directory

---

## 🖥️ Interactive Tools

### **MDR-TB Forecasting Dashboard**

A web-based interactive tool for exploring different intervention scenarios.

**Features:**
- Real-time parameter adjustment (TPT coverage, ACF intensity, private sector engagement, treatment success)
- Three preset scenarios (Status Quo, Optimistic, Pessimistic)
- Live chart updates (burden projection, cases averted, economic benefit)
- Downloadable custom scenarios (JSON export)

**Access:** Open `interactive_dashboard/MDR_TB_Forecasting_Dashboard.html` in any modern browser

**No installation required** - runs entirely in browser with no server needed.

---

## 📊 Data Sources

All data are publicly available:

1. **WHO Global Tuberculosis Reports (2017-2025)**
   - URL: https://www.who.int/teams/global-tuberculosis-programme/data
   - License: CC BY-NC-SA 3.0 IGO

2. **ICMR-NTEP Annual Reports (2017-2025)**
   - URL: https://tbcindia.gov.in
   - License: Government of India Open Data License

3. **India TB Reports (2017-2025)**
   - URL: https://tbcindia.gov.in
   - License: Public domain (government publication)

**No proprietary or restricted data were used.**

---

## 📝 Citation

### **Manuscript Citation** (Update after publication)

```
Siddalingaiah HS. Projected Burden of Multidrug-Resistant Tuberculosis in India 
(2025–2035): A Forecasting Analysis Using Verified National Surveillance Data. 
[Journal Name]. 2025;[Volume]([Issue]):[Pages]. doi:[DOI]
```

### **Code Repository Citation**

```
Siddalingaiah HS. India MDR-TB Forecasting Study (2025-2035). 
GitHub repository. 2025. Available at: https://github.com/[username]/india-mdrtb-forecasting
```

### **BibTeX**

```bibtex
@article{siddalingaiah2025mdrtb,
  title={Projected Burden of Multidrug-Resistant Tuberculosis in India (2025–2035): 
         A Forecasting Analysis Using Verified National Surveillance Data},
  author={Siddalingaiah, H S},
  journal={[Journal Name]},
  year={2025},
  volume={[Volume]},
  number={[Issue]},
  pages={[Pages]},
  doi={[DOI]}
}
```

---

## 🤝 Contributing

This is a research repository for a published study. While the code is open-source and available for use, contributions are not currently being accepted as the manuscript is under review/published.

**However, you are welcome to:**
- Fork the repository for your own analyses
- Adapt the methods for other countries or diseases
- Report issues or bugs in the code
- Request clarifications via email

---

## 📄 License

**Code:** MIT License - See `LICENSE` file for details

**Manuscript & Figures:** © 2025 Siddalingaiah H S. All rights reserved until publication.

**Data:** Public domain (government sources)

**Interactive Dashboard:** Creative Commons Attribution 4.0 International (CC BY 4.0)

---

## 🔗 Links

- **Interactive Dashboard:** [Live Demo](https://[username].github.io/india-mdrtb-forecasting/)
- **Pre-print:** [medRxiv](https://medrxiv.org/[DOI]) (if applicable)
- **Published Article:** [Journal Website](https://[journal-url]) (after publication)
- **Author ORCID:** [ORCID ID] (if applicable)

---

## 📧 Contact

**Dr. Siddalingaiah H S**  
Independent Researcher  
Bengaluru, Karnataka, India

- **Email:** hssling@yahoo.com
- **GitHub:** [@[username]](https://github.com/[username])
- **LinkedIn:** [Profile](https://linkedin.com/in/[profile]) (if applicable)

**For questions regarding:**
- **Data/Methods:** Email with subject "MDR-TB Forecasting - Data Query"
- **Code Issues:** Open a GitHub issue
- **Collaboration:** Email with subject "MDR-TB Forecasting - Collaboration"
- **Media Inquiries:** Email with subject "MDR-TB Forecasting - Media"

**Response Time:** Typically within 48-72 hours

---

## 🙏 Acknowledgments

### **Data Providers**
- World Health Organization (WHO) Global TB Programme
- Central TB Division, Ministry of Health & Family Welfare, Government of India
- Indian Council of Medical Research (ICMR)

### **Open Source Community**
- Python Software Foundation
- Statsmodels development team
- Plotly development team
- Matplotlib and Seaborn contributors

### **Intellectual Inspiration**
- WHO End TB Strategy framework
- India's National Strategic Plan for TB Elimination 2023-2027
- Published TB forecasting literature

---

## 📚 Related Publications

(To be updated after publication)

---

## 🔄 Version History

- **v1.0.0** (December 18, 2025): Initial release with manuscript submission
  - Complete forecasting analysis
  - Bootstrap uncertainty quantification
  - Interactive dashboard
  - Comprehensive supplementary materials

---

## ⚠️ Disclaimer

This research was conducted independently and does not represent the official views of WHO, ICMR, NTEP, or the Government of India. All interpretations and conclusions are those of the author.

The forecasts presented are based on historical data and statistical modeling. Actual future burden will depend on policy decisions, intervention effectiveness, and unforeseen factors (e.g., new diagnostics, vaccines, or resistance patterns).

---

## 🌟 Star This Repository

If you find this research useful, please consider starring the repository to help others discover it!

---

**Last Updated:** December 18, 2025  
**Repository Status:** Active  
**Manuscript Status:** Under Review / Published (update as appropriate)

---

## 📊 Repository Statistics

![GitHub stars](https://img.shields.io/github/stars/[username]/india-mdrtb-forecasting?style=social)
![GitHub forks](https://img.shields.io/github/forks/[username]/india-mdrtb-forecasting?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/[username]/india-mdrtb-forecasting?style=social)

---

**Made with ❤️ for India's TB Elimination Mission**
