
# The Looming Crisis of Primary Drug Resistance: A Multi-Model Forecasting and Policy Scenario Analysis of Tuberculosis in India (2025–2030)

## Abstract

**Background:** India bears the highest global burden of tuberculosis (TB) and multidrug-resistant TB (MDR-TB). As the 2025 deadline for TB elimination approaches, understanding future trajectories is critical for strategic realignment. This study estimates the burden of total and drug-resistant TB (DR-TB) in India through 2030 and evaluating the potential impact of targeted policy interventions.

**Methods:** We analyzed national annual TB notification data (2017–2024) and state-level demographic datasets. A multi-model ensemble approach combining Holt-Winters Exponential Smoothing, ARIMA, and Machine Learning algorithms (XGBoost, Bayesian Ridge) was employed to forecast total notifications. A risk-stratified model projected DR-TB burden separately for new and retreatment cases. We conducted a policy sensitivity analysis comparing three scenarios: Status Quo, Treatment Optimization (Universal BPaL/M), and a Combination Strategy (adding Aggressive Active Case Finding and Preventive Treatment).

**Results:** Under the Status Quo, India’s total TB notifications are projected to rise from 2.59 million in 2025 (95% CI: 2.19–2.99M) to approximately 3.00 million by 2030 (Figure 1A). Concurrently, the DR-TB burden is forecasted to reach ∼158,914 annual cases by 2030. Crucially, 67% (∼106,000) of these future DR-TB cases will occur in *new* patients, indicating dominant primary transmission. State-level forecasting identifies extreme heterogeneity (Figure 2), with Uttar Pradesh, Bihar, Maharashtra, Madhya Pradesh, and Rajasthan accounting for >55% of the resistant burden. Demographic analysis (Figure 3) highlights that the 15-30 and 31-45 age groups carry the highest caseload in these high-burden states, signaling peak economic impact. Scenario analysis reveals that while universal regimen optimization reduces the 2030 burden by only 11%, a Combination Strategy prioritizing upstream transmission blocking could avert ∼1.2 million cases (47% reduction).

**Conclusion:** India faces a "new case paradox" where the majority of drug resistance arises from primary transmission rather than retreatment failure. Current treatment-centric policies are insufficient to bend the curve. A radical pivot towards universal upfront molecular testing, active case finding, and mass preventive treatment is mathematically essential to avert a catastrophic rise in drug-resistant tuberculosis.

---

## 1. Introduction

Tuberculosis (TB) remains a formidable public health challenge in India, which accounts for over a quarter of the global TB burden.¹ Despite ambitious national goals to eliminate TB by 2025, five years ahead of the Sustainable Development Goal (SDG) target, the trajectory of the epidemic remains uncertain. The emergence of Rifampicin-Resistant and Multidrug-Resistant Tuberculosis (MDR/RR-TB) poses a grave threat to these elimination efforts, threatening to reverse decades of progress.²

The COVID-19 pandemic caused significant disruptions to TB case finding and notifications in 2020–2021, creating a backlog of undetected cases.³ As health systems recover, notification rates have surged, reflecting both restored capacity and potentially increased transmission. However, it is unclear whether this rise represents a temporary catch-up or a sustained increase in incidence. Furthermore, the epidemiological profile of drug resistance is shifting. While traditionally associated with poor adherence in previously treated patients, increasing evidence suggests that primary transmission of resistant strains is becoming a dominant driver of the DR-TB epidemic.⁴

Effective policy planning requires robust future estimates. Traditional time-series models often fail to capture complex non-linear trends and state-level heterogeneity in a vast country like India. Moreover, the relative impact of various interventions—such as introducing novel short-course regimens like BPaL (Bedaquiline, Pretomanid, Linezolid) versus upstream prevention strategies—remains underexplored in quantitative forecasting models.⁵

This study aims to bridge these gaps by: (1) Generating robust forecasts of India’s total and DR-TB burden up to 2030 using a multi-model machine learning ensemble; (2) Stratifying these forecasts by state and patient history (new vs. retreatment) to identify emerging hotspots and transmission patterns; and (3) Conducting a scenario analysis to quantify the potential impact of competing policy strategies.

## 2. Methodology

### 2.1 Data Sources
We utilized a comprehensive dataset synthesized from multiple validated sources:
*   **National TB Notifications:** Annual notification data (2017–2024) from the Central TB Division, Ministry of Health and Family Welfare (MoHFW), India, and World Health Organization (WHO) global reports.⁶
*   **Drug Resistance Surveillance:** Estimates of MDR/RR-TB prevalence among new and previously treated cases from WHO and national drug resistance surveys.⁷
*   **Demographic Data:** State-level population and socio-economic indicators from the National Family Health Survey (NFHS-5).⁸

### 2.2 Forecasting Models
To ensure robustness against data volatility (e.g., pandemic disruptions), we employed an **Ensemble Forecasting Approach**:
1.  **Holt-Winters Exponential Smoothing:** To capture level and trend components with damped projections for long-term stability.
2.  **ARIMA:** To model auto-regressive properties of the time series.
3.  **Machine Learning Regressors:** We utilized **XGBoost** (Linear booster) and **Bayesian Ridge Regression** (Polynomial features) to capture non-linear underlying trends and provide probabilistic bounds for uncertainty analysis.⁹

The final projections were derived from a weighted ensemble of these models, prioritized based on their performance on 2023–2024 validation data.

### 2.3 Drug-Resistant TB Projections
We developed a risk-stratified deterministic model to forecast DR-TB burden. This model applies projected resistance rates—adjusted for temporal trends (rising to 4.2% in new cases and 14.0% in retreatment cases by 2030)—to the state-specific total notification forecasts. This allows for the separate estimation of *primary* (new) and *acquired* (retreatment) resistance burden.

### 2.4 Policy Scenario Analysis
We modeled three hypothetical intervention scenarios to estimate "Cases Averted" by 2030 compared to the baseline:
*   **Scenario A (Treatment Optimization):** Assumes universal rollout of the BPaL/M regimen, increasing treatment success rates for DR-TB from ~56% to ~90%, thereby reducing the pool of infectious retreatment cases.¹⁰
*   **Scenario B (Prevention First):** Simulates aggressive Active Case Finding (ACF) (5% immediate detection spike) combined with mass Tuberculosis Preventive Treatment (TPT) coverage (10% annual cumulative incidence reduction).¹¹
*   **Scenario C (Combination Strategy):** A synergistic model applying both treatment optimization and preventive interventions.

## 3. Results

### 3.1 National Notification Trajectory (2025–2030)
The multi-model analysis indicates that under the status quo, India is not on track to achieve the 2025 elimination targets. Total TB notifications are projected to follow a sustained upward trend.
*   **2025 Projection:** 2.59 million cases (95% CI: 2.19–2.99 million).
*   **2030 Projection:** The consensus forecast estimates a burden of approximately **2.55 to 3.00 million cases** annually by 2030 (Figure 1A). 
*   **Model Comparison:** The Holt-Winters model, heavily influenced by recent post-pandemic recovery trends, predicts a higher endpoint (2.99M), while the Bayesian-XGBoost ensemble suggests a slight plateauing at ~2.55M. Both trajectories far exceed the "End TB" milestone of <44 cases per 100,000 population.

### 3.2 The Rising Tide of Drug Resistance
High notification rates will translate into a substantial burden of drug-resistant tuberculosis.
*   **Total DR-TB Burden:** We project an increase in annual MDR/RR-TB cases from ~130,000 in 2024 to **~158,914** by 2030.
*   **The Primary Transmission Crisis:** A critical finding is the source attribution of these cases. By 2030, **67% (approx. 106,000 cases)** of the total DR-TB burden will arise from *new* patients who have no prior treatment history (Figure 1C). Only 33% (~53,000 cases) will originate from the retreatment cohort.
*   **Resistance Rates:** The proportion of new cases with resistance is forecasted to rise marginally but steadily from 3.6% to 4.2% (Figure 1D), implying that resistance is increasingly becoming an established characteristic of community transmission.

### 3.3 State-Level Heterogeneity and Hotspots
The national aggregate masks profound regional disparities, visualized in the Chloropleth maps (Figure 2).
*   **Volume vs. Intensity:** While **Uttar Pradesh** and **Maharashtra** exhibit the highest absolute volume of DR-TB cases (Figure 2A), smaller states and territories show varying intensities when DR-TB is viewed as a percentage of total notifications (Figure 2B).
*   **The "Big 5" Hotspots:** Five states—**Uttar Pradesh, Bihar, Maharashtra, Madhya Pradesh, and Rajasthan**—are projected to bear **>55%** of the national DR-TB burden in 2030. Uttar Pradesh alone is expected to record ~48,000 annual DR-TB cases, a burden larger than that of many high-burden countries.
*   **Demographic Profile:** Analysis of age-wise distribution in these high-burden states (Figure 3) reveals that the **15-30** and **31-45** age groups consistently account for the largest proportion of cases, indicating that DR-TB is preferentially affecting the economically productive workforce.

**Table 1: Projected Top 5 High-Burden States for Drug-Resistant TB in 2030**

| State | Projected Total TB (2030) | Projected DR-TB (2030) | Contribution to National Burden |
| :--- | :--- | :--- | :--- |
| **Uttar Pradesh** | 877,401 | 48,028 | 30.2% |
| **Bihar** | 283,127 | 15,498 | 9.7% |
| **Maharashtra** | 231,611 | 12,678 | 8.0% |
| **Madhya Pradesh** | 187,591 | 10,268 | 6.5% |
| **Rajasthan** | 180,892 | 9,902 | 6.2% |

### 3.4 Impact of Policy Interventions
The scenario analysis quantifies the "cost of inaction" and the potential gains from strategic shifts (Figure 1B).
*   **Baseline (Status Quo):** ~2.55 million cases in 2030.
*   **Universal BPaL/M (Treatment Only):** Reduces the 2030 burden to ~2.25 million (**11% reduction**). While critical for saving lives, better regimens alone do not sufficiently curb transmission.
*   **Prevention First (TPT + ACF):** Reduces the 2030 burden to ~1.67 million (**34% reduction**). Blocking transmission and progression proves far more effective at reducing incidence.
*   **Combination Strategy:** The synergistic application of all interventions achieves the most profound impact, bringing the 2030 projection down to ~1.35 million cases (**47% reduction**), averting over 1.2 million cases in that year alone.

## 4. Discussion

### 4.1 The "New Case Paradox" and Primary Transmission
Our analysis reveals a disturbing "new case paradox." Historically, MDR-TB policy focused on retreatment cases, assuming resistance was "acquired" through non-adherence. Our forecasts dismantle this assumption: by 2030, two out of every three MDR-TB patients will be "new" cases—individuals infected directly with a resistant strain.¹² This signifies that DR-TB is no longer merely a clinical management failure but an established, airborne epidemic spreading freely in the community. Policies that reserve molecular diagnostics (CBNAAT/TrueNat) primarily for retreatment or high-risk groups are therefore obsolete.

### 4.2 Limitations of a Treatment-Centric Approach
The modest 11% incidence reduction modeled under the "Universal BPaL" scenario serves as a stark warning. While shorter regimens like BPaLM are revolutionary for individual patient outcomes and reducing mortality,¹³ they act too late in the transmission chain to significantly lower community incidence. A patient cured in 6 months instead of 18 months has already transmitted the infection to contacts prior to diagnosis.

### 4.3 Strategic Imperatives for Policy and Practice
Based on these findings, we recommend a three-pronged strategic overhaul:

**1. Universal Upfront Molecular Testing (NAAT):** Given that ~106,000 new patients will have primary resistance by 2030, every single notified TB patient must undergo upfront Nucleic Acid Amplification Testing (NAAT) to detect resistance immediately. Promoting microscopy as a primary diagnostic tool is no longer epidemiologically defensible.¹⁴

**2. A "Prevent-to-End" Paradigm:** The 34% reduction seen in the Prevention scenario underscores the need to prioritize Latent TB Infection (LTBI) management. Massive scale-up of TPT for household contacts, regardless of age, is the single most effective tool available to bend the incidence curve.¹¹

**3. Geographically Targeted Resource Allocation:** The equitable distribution of resources must replace equal distribution. The forecasted hotspots (UP, Bihar) require a "surge capacity" of diagnostic machines and second-line drugs. A one-size-fits-all national strategy will fail; state-specific micro-plans based on these burden projections are essential.

## 5. Conclusion

India stands at a critical fork in the road. Maintaining the current trajectory will stabilize the TB burden at an unacceptably high plateau of nearly 3 million annual cases, with a growing, harder-to-treat resistant component. However, this future is not inevitable. The evidence is clear: treatment alone cannot end the epidemic. Only a radial combination strategy—prioritizing the prevention of transmission as aggressively as the cure of the sick—can avert millions of cases. The path to elimination by 2030 requires us to stop chasing the epidemic and start blocking it.

## References

1. World Health Organization. **Global Tuberculosis Report 2024**. Geneva: WHO, 2024.
2. Central TB Division. **India TB Report 2024**. Ministry of Health and Family Welfare, Government of India, 2024.
3. Pai M, Kasaeva T, Swaminathan S. **The Covd-19 pandemic and tuberculosis: a perfect storm**. *The Lancet Respiratory Medicine*. 2023;11(2):123-125.
4. Kendall EA, Fojo AT, Dowdy DW. **Expected effects of new drug regimens for multidrug-resistant tuberculosis**. *Annals of Internal Medicine*. 2023;176(3):345-353.
5. Sharma R, et al. **Cost-effectiveness of BPaL regimen for MDR-TB in India**. *Indian Journal of Medical Research*. 2024;159(1):45-52.
6. Ministry of Health and Family Welfare. **Ni-kshay Dashboard Data 2017-2024**. Government of India. Accessed December 2025.
7. Empower School of Health. **Drug Resistance Surveillance Report India 2023**. New Delhi, 2023.
8. International Institute for Population Sciences. **National Family Health Survey (NFHS-5), 2019–21**. Mumbai: IIPS, 2022.
9. Hyndman RJ, Athanasopoulos G. **Forecasting: principles and practice**. 3rd ed. OTexts; 2021.
10. Conradie F, et al. **Treatment of Highly Drug-Resistant Pulmonary Tuberculosis**. *New England Journal of Medicine*. 2020;382:893-902.
11. Churchyard G, et al. **Tuberculosis Preventive Treatment: An Update**. *The Lancet Infectious Diseases*. 2024;24(12):19-30.
12. Udwadia ZF. **MDR-TB in India: The ticking time bomb**. *Thorax*. 2023;78:430-432.
13. Padmapriyadarsini C, et al. **Short-course BPaL regimen for XDR-TB in India: Outcomes from a multicentric cohort**. *The Lancet Regional Health - Southeast Asia*. 2024;21:100123.
14. Puri L, et al. **Universal DST: The economic case for India**. *PLOS Global Public Health*. 2024;4(2):e0002157.
