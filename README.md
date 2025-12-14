
# Living Review: Future of Drug-Resistant TB in India

**A Continuously Updated Forecasting & Policy Intelligence Platform**

This repository hosts a "Living Review" of the drug-resistant tuberculosis (DR-TB) epidemic in India. Unlike static manuscripts, this project includes an interactive dashboard that updates as new data (from Ni-kshay, WHO) becomes available.

## 🔗 [Launch Interactive Dashboard](https://github.com/hssling/drtb_projections_modelling) (Requires Streamlit)

---

## 📊 Key Features
1.  **Ensemble Forecasting:** Projects national notification trends using Multi-Model AI (XGBoost, ARIMA, Holt-Winters).
2.  **Primary Resistance Tracker:** Monitors the "New Case Paradox" — the rising share of drug resistance in treatment-naïve patients.
3.  **State Hotspot Map:** Granular risk assessment for all Indian states.
4.  **Policy Simulator:** Interactive tool to model the impact of TPT and BPaL implementation.

## 🚀 How to Run Locally

1.  Clone the repository:
    ```bash
    git clone https://github.com/hssling/drtb_projections_modelling.git
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements_dashboard.txt
    ```
3.  Launch the dashboard:
    ```bash
    streamlit run dashboard_app.py
    ```

## 📂 Project Structure
*   `dashboard_app.py`: The main Streamlit application.
*   `analysis_results/`: Contains the CSV datasets powering the forecast.
*   `manuscript_assets/`: High-resolution static figures.
*   `final_comprehensive_manuscript_v6.docx`: The latest academic output (December 2025).

## ✍️ Authors
*   **Dr. Siddalingaiah H. S.** (Professor, Community Medicine, Shridevi Institute, Tumkur)

---
*Last Updated: December 14, 2025*
