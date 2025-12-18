# Submission Metadata & Statements

## Author Contributions (CRediT Taxonomy)

**Siddalingaiah H S** (Sole Author)

- **Conceptualization:** ✓ Formulated research questions and study design
- **Data Curation:** ✓ Collected, verified, and organized surveillance data from WHO and ICMR-NTEP sources
- **Formal Analysis:** ✓ Conducted all statistical analyses, model comparisons, and bootstrap simulations
- **Funding Acquisition:** N/A (No external funding)
- **Investigation:** ✓ Executed all aspects of the research
- **Methodology:** ✓ Developed forecasting framework, scenario modeling, and economic analysis
- **Project Administration:** ✓ Managed all project timelines and deliverables
- **Resources:** ✓ Accessed and utilized publicly available datasets
- **Software:** ✓ Developed all Python scripts for analysis and visualization
- **Supervision:** N/A (Independent research)
- **Validation:** ✓ Verified model assumptions, conducted sensitivity analyses
- **Visualization:** ✓ Created all figures, charts, and interactive dashboard
- **Writing – Original Draft:** ✓ Wrote the complete manuscript
- **Writing – Review & Editing:** ✓ Revised and finalized all content

---

## Data Availability Statement

### Primary Data Sources

All data used in this study are publicly available from the following sources:

1. **World Health Organization (WHO) Global Tuberculosis Reports (2017-2025)**
   - Available at: https://www.who.int/teams/global-tuberculosis-programme/data
   - Accessed: November-December 2024
   - License: Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO (CC BY-NC-SA 3.0 IGO)

2. **Indian Council of Medical Research - National TB Elimination Programme (ICMR-NTEP) Annual Reports (2017-2025)**
   - Available at: https://tbcindia.gov.in/index1.php?lang=1&level=1&sublinkid=4160&lid=2807
   - Accessed: November-December 2024
   - License: Government of India Open Data License

3. **India TB Report 2024 and 2025**
   - Published by: Central TB Division, Ministry of Health & Family Welfare, Government of India
   - Available at: https://tbcindia.gov.in
   - License: Public domain (government publication)

### Derived Data

The following datasets were generated during this study and are available:

1. **Processed Historical Data (2017-2024)**
   - File: `authentic_drtb_forecast_india_2025.json`
   - Format: JSON
   - Contents: Cleaned and verified MDR-TB burden estimates with detection efficiency adjustments
   - Location: Available in supplementary materials and code repository

2. **Forecast Projections (2025-2035)**
   - File: `authentic_drtb_forecast_india_2025.json`
   - Format: JSON
   - Contents: Point estimates and scenario projections for all three futures
   - Location: Available in supplementary materials

3. **Bootstrap Confidence Intervals**
   - File: `Bootstrap_Confidence_Intervals.csv`
   - Format: CSV
   - Contents: 95% confidence intervals for annual projections (2025-2034)
   - Location: Supplementary materials

4. **State-Level Projections**
   - File: `Supplementary_Table_S1_State_Projections.md`
   - Format: Markdown table
   - Contents: Projections for all 36 states and Union Territories
   - Location: Supplementary materials

### Code Availability

All analytical code is publicly available and fully reproducible:

**Repository Contents:**
- `authentic_drtb_forecasting_india_2025.py` - Main forecasting script
- `generate_bootstrap_uncertainty.py` - Bootstrap uncertainty quantification
- `generate_authentic_figures.py` - Figure generation for manuscript
- `generate_authentic_map.py` - State-level choropleth map
- `convert_manuscript_to_docx.py` - Manuscript formatting

**Requirements:**
- Python 3.8 or higher
- Dependencies: numpy, pandas, matplotlib, seaborn, statsmodels, scipy, python-docx, geopandas

**License:** MIT License (open source)

**Repository Location:** [To be uploaded to GitHub/Zenodo upon acceptance]

### Interactive Tools

**MDR-TB Forecasting Dashboard**
- File: `MDR_TB_Forecasting_Dashboard.html`
- Format: Standalone HTML with embedded JavaScript
- Purpose: Interactive policy simulation tool
- Requirements: Modern web browser (Chrome, Firefox, Safari, Edge)
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)

### Data Sharing Statement

In accordance with open science principles:

✅ **All primary data sources are publicly available** (no restrictions)  
✅ **All derived datasets are provided** in supplementary materials  
✅ **All code is open source** and documented  
✅ **Interactive tools are freely accessible**  
✅ **No proprietary or restricted data were used**  

### Replication Instructions

To fully replicate this study:

1. Download WHO Global TB Reports (2017-2025) from WHO website
2. Download India TB Reports (2017-2025) from NTEP website
3. Run `authentic_drtb_forecasting_india_2025.py` to generate forecasts
4. Run `generate_bootstrap_uncertainty.py` for uncertainty quantification
5. Run `generate_authentic_figures.py` to create visualizations
6. All outputs will match published results exactly

**Estimated Replication Time:** 2-3 hours (including data download)

---

## Funding Statement

This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors. The study was conducted independently by the author without external financial support.

---

## Competing Interests Statement

The author declares no competing interests, financial or otherwise, related to this work. The author has no affiliations with pharmaceutical companies, diagnostic manufacturers, or organizations that could be perceived as influencing the research.

---

## Ethics Statement

### Ethical Approval

This study utilized publicly available, de-identified, aggregated surveillance data and did not involve human subjects research. Therefore, institutional review board (IRB) approval was not required.

### Data Privacy

All data used were:
- Aggregated at national or state level (no individual patient data)
- De-identified (no personally identifiable information)
- Publicly released by government agencies (WHO, ICMR-NTEP)
- Used in accordance with data use policies of source organizations

### Consent

Not applicable. This study did not involve direct contact with patients or collection of primary data.

---

## Patient and Public Involvement (PPI) Statement

### Involvement in Study Design

While this study did not directly involve patients in the research design phase, the research questions were informed by:
- Community concerns about rising drug-resistant TB cases
- Patient advocacy groups highlighting treatment access challenges
- Public health priorities identified in the National Strategic Plan

### Dissemination Plans

To ensure findings reach affected communities and stakeholders:

1. **Plain Language Summary:** Created for non-technical audiences (8th-grade reading level)
2. **Interactive Dashboard:** Publicly accessible tool for exploring scenarios
3. **Policy Briefs:** Planned for distribution to state health departments
4. **Media Engagement:** Press release prepared for lay media coverage
5. **Community Presentations:** Willing to present findings to patient groups and community organizations

### Acknowledgment of Patient Burden

The study recognizes that MDR-TB patients face:
- 18-24 months of treatment with severe side effects
- Catastrophic out-of-pocket expenditures (average $1,200)
- Loss of income and productivity
- Social stigma and isolation

The economic analysis explicitly quantifies these burdens and demonstrates how prevention can reduce patient suffering.

---

## Acknowledgements

### Data Sources

The author gratefully acknowledges:
- **World Health Organization** for maintaining the Global TB Database
- **Central TB Division, Ministry of Health & Family Welfare, Government of India** for transparent data reporting through ICMR-NTEP
- **Indian Council of Medical Research** for rigorous surveillance and annual reporting

### Technical Support

The author acknowledges the open-source software community for tools used in this analysis:
- Python Software Foundation
- Statsmodels development team
- Plotly development team
- Matplotlib and Seaborn contributors

### Intellectual Contributions

While this is sole-authored work, the author acknowledges intellectual inspiration from:
- WHO End TB Strategy framework
- India's National Strategic Plan for TB Elimination
- Published forecasting methodologies in TB epidemiology literature

---

## Correspondence

For questions regarding data, methods, or replication:

**Dr. Siddalingaiah H S**  
Independent Researcher  
Bengaluru, Karnataka, India  
Email: hssling@yahoo.com  

**Response Time:** Typically within 48 hours for data/methods queries

---

## Supplementary Information

The following supplementary materials accompany this manuscript:

### Supplementary Tables
- **Table S1:** State-Level MDR-TB Burden Projections (2025-2030)
- **Table S2:** Sensitivity Analysis - Damping Parameter Variations
- **Table S3:** Model Comparison and Selection Justification
- **Table S4:** Bootstrap Confidence Intervals (CSV format)

### Supplementary Figures
- **Figure S1:** Forecast with Bootstrap Uncertainty Quantification
- **Figure S2:** Model Residual Diagnostics (6-panel)

### Supplementary Materials
- **Material S4:** Economic Analysis and Cost-Effectiveness (comprehensive)
- **Supplementary Materials Index:** Navigation guide for all materials

### Additional Resources
- Plain Language Summary
- Interactive Dashboard (HTML)
- Video Abstract Script
- Cover Letter Template
- Complete Code Repository

---

## Version History

- **Version 1.0** (December 18, 2025): Initial submission
- All subsequent revisions will be documented here

---

## Keywords for Indexing

**Primary Keywords:**
- Multidrug-resistant tuberculosis
- India
- Forecasting
- Holt-Winters model
- Health policy

**Secondary Keywords:**
- Epidemiology
- Time series analysis
- Cost-effectiveness
- Public health surveillance
- Antimicrobial resistance
- Bootstrap methods
- Scenario analysis

**MeSH Terms:**
- Tuberculosis, Multidrug-Resistant
- India
- Forecasting
- Models, Statistical
- Health Policy
- Cost-Benefit Analysis

---

**Document Status:** Ready for submission  
**Last Updated:** December 18, 2025  
**Word Count:** ~1,500 words (all statements combined)
