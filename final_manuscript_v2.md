
# The Looming Crisis of Primary Drug Resistance: A Multi-Model Forecasting and Policy Scenario Analysis of Tuberculosis in India (2025–2030)

## Abstract

**Background:** India bears the highest global burden of tuberculosis (TB) and multidrug-resistant TB (MDR-TB). Recent systematic reviews indicate a persistent prevalence of drug resistance (~3.5–3.9% in new cases), yet future trajectories remain uncertain. As the 2025 elimination deadline approaches, this study estimates the burden of total and drug-resistant TB (DR-TB) in India through 2030, contrasting these with meta-analytical trends to advocate for targeted policy interventions.

**Methods:** We analyzed national annual TB notification data (2017–2024) and state-level demographic datasets. A multi-model ensemble approach combining Holt-Winters Exponential Smoothing, ARIMA, and Machine Learning algorithms (XGBoost, Bayesian Ridge) was employed to forecast total notifications. A risk-stratified model projected DR-TB burden separately for new and retreatment cases. We also performed a synthesis of recent meta-analyses (2020–2024) to validate our epidemiological assumptions. Finally, we conducted a policy sensitivity analysis comparing three scenarios: Status Quo, Treatment Optimization, and a Combination Strategy.

**Results:** Under the Status Quo, India’s total TB notifications are projected to rise from 2.59 million in 2025 (95% CI: 2.19–2.99M) to approximately 3.00 million by 2030 (Figure 1A). Concurrently, the DR-TB burden is forecasted to reach ∼158,914 annual cases by 2030. Our projections align with meta-analytical trends (Figure 4) showing a creeping rise in primary resistance from 3.5% (2020) to a projected 4.2% (2030). Crucially, 67% (∼106,000) of these future DR-TB cases will occur in *new* patients. State-level forecasting identifies extreme heterogeneity (Figure 2), with Uttar Pradesh, Bihar, Maharashtra, Madhya Pradesh, and Rajasthan accounting for >55% of the resistant burden. Scenario analysis reveals that a Combination Strategy (Prevention + Treatment) could avert ∼1.2 million cases (47% reduction) by 2030.

**Conclusion:** India faces a "new case paradox" validated by both forecasting and meta-analysis: the majority of drug resistance arises from primary transmission. Current treatment-centric policies are insufficient to bend the curve. A radical pivot towards universal upfront molecular testing, active case finding, and mass preventive treatment is mathematically essential to avert a catastrophic rise in drug-resistant tuberculosis.

---

## 1. Introduction

Tuberculosis (TB) remains a formidable public health challenge in India, accounting for over a quarter of the global burden. Despite ambitious goals to eliminate TB by 2025, the epidemic's trajectory is complex. The emergence of Rifampicin-Resistant and Multidrug-Resistant Tuberculosis (MDR/RR-TB) poses a severe threat. While traditionally linked to treatment failure, recent evidence suggests a shift towards primary transmission.

Effective policy requires robust estimates. This study aims to: (1) Forecast India’s total and DR-TB burden to 2030 using a multi-model ensemble; (2) Validate these trends against a meta-analysis of recent literature; (3) Identify geographic hotspots; and (4) Quantify the impact of strategic policy shifts.

## 2. Methodology

### 2.1 Data Sources & Meta-Analysis Synthesis
We utilized national notification data (2017–2024) and state-level demographic datasets. Additionally, we conducted a targeted review of recent systematic reviews and meta-analyses (2020–2024) on DR-TB prevalence in India to contextualize our model inputs.
*   **Key Meta-Analysis Inputs:** Studies by Goyal et al. (2020) and Kumar et al. (2023) established a baseline primary resistance rate of 3.5%–3.9% in new cases, validating our model's starting parameters (Figure 4).

### 2.2 Forecasting Models
We employed an **Ensemble Forecasting Approach** (Holt-Winters, ARIMA, XGBoost, Bayesian Ridge) to ensure robustness against post-pandemic data volatility. The consensus forecast was used to project the 2025–2030 trajectory.

### 2.3 Policy Scenario Analysis
We modeled three hypothetical intervention scenarios:
*   **Scenario A:** Universal BPaL/M Treatment (Treatment Optimization).
*   **Scenario B:** Active Case Finding + TPT (Prevention First).
*   **Scenario C:** Combination Strategy.

## 3. Results

### 3.1 National Notification Trajectory (2025–2030)
Under the status quo, total TB notifications are projected to rise from **2.59 million** in 2025 to **~3.00 million** by 2030. This upward trend suggests that without disruptive intervention, the incidence will not naturally decline to elimination levels.

### 3.2 Meta-Analysis vs. Forecast: The Resistance Trend
Our meta-analytical comparison (Figure 4) reveals a concerning consistency.
*   **Historical Context:** Systematic reviews (2006–2018 data) placed primary resistance at ~3.5%.
*   **Recent Trends:** More recent studies (2016–2022) indicate a creeping rise to ~3.9%.
*   **Future Projection:** Our model extends this trend, forecasting a primary resistance rate of **4.2% by 2030**. This seemingly small percentage increase translates to a massive absolute burden due to the high volume of new cases.
*   **Source Attribution:** Consequently, **67% (~106,000)** of the projected 158,914 DR-TB cases in 2030 will originate from *new* patients (Figure 1C).

### 3.3 State-Level Heterogeneity
The national burden is unevenly distributed (Figure 2).
*   **Hotspots:** Uttar Pradesh, Bihar, Maharashtra, Madhya Pradesh, and Rajasthan are projected to shoulder **>55%** of the DR-TB caseload.
*   **Intensity:** While UP has the highest volume, the "intensity" of resistance (as a % of notifications) varies, necessitating tailored state micro-plans.

### 3.4 Impact of Policy Interventions
*   **Treatment Only:** Reduces 2030 burden by 11%.
*   **Prevention First:** Reduces 2030 burden by 34%.
*   **Combination Strategy:** Averts **~1.2 million cases (47% reduction)**, offering the only viable path to modifying the epidemic trajectory effectively (Figure 1B).

## 4. Discussion

### 4.1 Convergence of Evidence
The alignment between our machine learning forecasts and independent meta-analyses strengthens the conclusion that primary transmission is the dominant driver of the future DR-TB epidemic. The "New Case Paradox"—where the majority of resistance is found in patients with no treatment history—is now a validated epidemiological reality.

### 4.2 Strategic Imperatives
1.  **Universal NAAT:** With ~106,000 new resistant cases projected annually, upfront molecular testing for *all* is non-negotiable.
2.  **Prevent to End:** The 34% reduction from prevention strategies proves that blocking transmission via TPT and ACF is far more effective than treating active cases alone.
3.  **Surge Capacity in Hotspots:** Resources must be disproportionately allocated to the identified high-burden states.

## 5. Conclusion
India stands at a fork in the road. Status quo policies will lead to a plateauing high burden. However, a radical combination strategy, grounded in the evidence of primary transmission, can avert millions of cases.

## 6. Future Work
*   **District-Level Granularity:** Extending forecasts to the district level to guide local administrative action.
*   **Cost-Effectiveness Analysis:** Modeling the economic ROI of the Combination Strategy.
*   **Genomic Surveillance:** Integrating genomic data to track transmission clusters.

## References
1. Goyal S, et al. *BMC Public Health*. 2020.
2. Kumar A, et al. *Cureus*. 2023.
3. World Health Organization. *Global TB Report 2024*.
4. Central TB Division. *India TB Report 2024*.
5. Churchyard G, et al. *Lancet Infect Dis*. 2024.
(Full references provided in final document)
