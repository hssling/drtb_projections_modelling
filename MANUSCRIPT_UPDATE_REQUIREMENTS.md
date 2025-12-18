# 📝 MANUSCRIPT UPDATE REQUIREMENTS
## Missing Analyses to be Integrated

**Date:** December 18, 2025, 22:30 IST  
**Status:** Manuscript needs updating with latest analyses

---

## ❌ **What's Currently Missing from the Manuscript**

### **1. Bootstrap Uncertainty Quantification** (CRITICAL)

**What was done:**
- 1,000 bootstrap iterations performed
- 95% confidence intervals calculated for all projections (2025-2034)
- Residual diagnostics completed (6-panel analysis)
- All model assumptions validated

**What needs to be added to manuscript:**

#### **In Methods Section (2.4):**
```markdown
### 2.4 Uncertainty Quantification via Parametric Bootstrap

To rigorously quantify forecast uncertainty, we implemented a parametric bootstrap procedure with 1,000 iterations. For each iteration, residuals from the fitted Holt-Winters model were resampled with replacement, synthetic time series were generated, and the model was refit to produce alternative forecast trajectories. Percentile-based 95% confidence intervals were calculated from the distribution of bootstrap forecasts.

Model assumptions were validated through comprehensive residual diagnostics including: (1) normality assessment via Shapiro-Wilk test and Q-Q plots, (2) homoscedasticity evaluation through residuals vs. fitted values plots, (3) autocorrelation testing using ACF and PACF plots, and (4) temporal independence verification. All diagnostic tests confirmed that model assumptions were satisfied (Supplementary Figure S2).
```

#### **In Results Section (3.2):**
```markdown
The bootstrap analysis revealed moderate forecast uncertainty that increases with projection horizon. For 2030, the Status Quo projection of 84,205 cases has a 95% confidence interval of [71,338, 97,072], representing ±15.3% relative uncertainty. By 2034, the CI widens to [69,373, 100,171], with ±18.2% relative uncertainty (Supplementary Table S4, Supplementary Figure S1). This widening reflects the inherent limitations of long-term forecasting but remains within acceptable bounds for policy planning.
```

---

### **2. Economic Analysis & Cost-Effectiveness** (CRITICAL)

**What was done:**
- Comprehensive cost-effectiveness analysis
- ROI calculations (4.4:1 financial, 7.1:1 societal)
- Budget impact analysis
- Economic burden quantification ($3.8B savings)

**What needs to be added to manuscript:**

#### **In Methods Section (2.5):**
```markdown
### 2.5 Economic Analysis

We conducted a comprehensive cost-effectiveness analysis from a societal perspective with a 10-year time horizon (2025-2035). Direct medical costs per MDR-TB case were estimated at $4,980 (weighted average of public and private sector costs), including diagnosis ($146), treatment drugs ($1,680), monitoring ($840), hospitalization ($1,530), and adverse event management ($520). Indirect costs, including productivity loss ($2,400), caregiver time ($800), catastrophic health expenditure ($1,200), and premature mortality ($8,000), totaled $12,400 per case.

The incremental cost-effectiveness ratio (ICER) was calculated as the difference in costs divided by the difference in health outcomes (cases averted, DALYs averted) between the Optimistic and Status Quo scenarios. Cost-effectiveness was assessed against WHO-CHOICE thresholds for India (highly cost-effective: <$710/DALY; cost-effective: <$2,130/DALY). Return on investment (ROI) was calculated as net economic benefit divided by total intervention investment.
```

#### **In Results Section (3.5):**
```markdown
### 3.5 Economic Impact and Cost-Effectiveness

The economic analysis demonstrates compelling financial justification for the Optimistic intervention strategy. Over the 10-year period, the Status Quo scenario would incur a total economic burden of $14.6 billion ($4.2B direct medical costs + $10.4B indirect costs). The Optimistic scenario, despite requiring $694 million in intervention investments (TPT scale-up: $384M, ACF intensification: $165M, private sector engagement: $145M), would reduce the total burden to $10.9 billion, yielding net savings of $3.8 billion.

The incremental cost-effectiveness ratio is $1,278 per DALY averted, well below the WHO cost-effectiveness threshold of $2,130/DALY for India. The financial return on investment is 4.4:1, meaning every dollar invested returns $4.40 in economic benefits. When including intangible benefits (reduced transmission, improved quality of life, reduced stigma), the societal ROI increases to 7.1:1.

Critically, the Optimistic strategy would protect 65,164 households from catastrophic health expenditure, disproportionately benefiting the lowest two income quintiles. The required budget increase represents only 0.09% of national health spending—a modest investment relative to the substantial returns (Supplementary Material S4).
```

---

### **3. State-Level Projections** (MODERATE PRIORITY)

**What was done:**
- Projections for all 36 states/UTs
- Trajectory classifications (Optimistic, Status Quo, Pessimistic-leaning)
- Policy prioritization tiers

**What needs to be added:**

#### **In Discussion Section (4.3 - Expand existing):**
```markdown
State-level projections reveal profound heterogeneity (Supplementary Table S1). High-burden states (Uttar Pradesh, Maharashtra, Gujarat, Madhya Pradesh, Bihar) account for 62% of the national burden and exhibit Status Quo or Pessimistic trajectories, requiring immediate intensive intervention (Tier 1 priority). Medium-burden states show mixed trajectories, while Kerala and Himachal Pradesh demonstrate Optimistic-leaning patterns, approaching elimination thresholds.

This 10-fold variation in per-capita burden across states demands differentiated, precision public health strategies rather than uniform national approaches.
```

---

### **4. Model Comparison & Validation** (MODERATE PRIORITY)

**What was done:**
- 7 models evaluated (SES, Holt's Linear, Holt-Winters Damped, ARIMA variants, Polynomial)
- Comprehensive comparison (AIC, BIC, out-of-sample validation)
- Decision matrix justifying Holt-Winters selection

**What needs to be added:**

#### **In Methods Section (2.2 - Expand existing):**
```markdown
Model selection was based on rigorous comparison of seven candidate models: Simple Exponential Smoothing, Holt's Linear Trend, Holt-Winters Damped Trend, ARIMA(1,1,1), ARIMA(2,1,2), and Polynomial Regression (degrees 2 and 3). The Holt-Winters Damped Trend model achieved the optimal balance of in-sample fit (AIC: 161.7, BIC: 162.1), out-of-sample validation performance (leave-one-out RMSE: 2,847), and epidemiological plausibility. Alternative models either overfit the limited data (high-order ARIMA) or failed to capture saturation dynamics (linear models) (Supplementary Table S3).
```

---

### **5. Sensitivity Analysis** (MODERATE PRIORITY)

**What was done:**
- Damping parameter variations (φ = 0.70 to 0.95)
- Robustness assessment across parameter range
- Cases averted range: 195,000-244,000

**What needs to be added:**

#### **In Results Section (3.4 - Expand existing):**
```markdown
Sensitivity analysis across damping parameter values (φ = 0.70 to 0.95) confirmed the robustness of policy conclusions. While the absolute magnitude of projections varied, the relative ranking of scenarios and the qualitative finding of Status Quo stagnation persisted across all parameter values. Cases averted under the Optimistic strategy ranged from 195,000 (conservative, φ=0.70) to 244,000 (optimistic, φ=0.95), bracketing our base case estimate of 217,215 (Supplementary Table S2).
```

---

## 🔧 **Reference Superscript Issue**

**Problem:** References appear as `<sup>1</sup>` instead of superscript numbers in DOCX

**Solution:** Update the DOCX conversion script to properly handle superscripts

### **Fix Required in `convert_manuscript_to_docx.py`:**

Add this function:
```python
def add_paragraph_with_superscripts(doc, text, style='CustomNormal'):
    """Add paragraph with proper superscript formatting for references"""
    para = doc.add_paragraph(style=style)
    
    # Split by superscript tags
    parts = re.split(r'<sup>(.*?)</sup>', text)
    
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Regular text
            para.add_run(part)
        else:
            # Superscript text
            run = para.add_run(part)
            run.font.superscript = True
    
    return para
```

Then replace all `doc.add_paragraph()` calls in main sections with this function.

---

## 📋 **Priority Action Items**

### **CRITICAL (Must Add):**
1. ✅ Bootstrap uncertainty quantification (Methods 2.4, Results 3.2)
2. ✅ Economic analysis (Methods 2.5, Results 3.5)
3. ✅ Fix reference superscripts in DOCX script

### **IMPORTANT (Should Add):**
4. ✅ Model comparison justification (Methods 2.2)
5. ✅ Sensitivity analysis results (Results 3.4)
6. ✅ State-level heterogeneity expansion (Discussion 4.3)

### **OPTIONAL (Nice to Have):**
7. ⭐ Reference to interactive dashboard in Discussion
8. ⭐ Mention of supplementary materials throughout

---

## 📊 **Updated Word Count Target**

**Current:** ~3,850 words  
**After additions:** ~4,500-4,800 words  
**IJMR Limit:** 5,000 words (excluding references)  
**Status:** ✅ Within acceptable range

---

## 🎯 **Recommended Approach**

Given the extent of updates needed, I recommend:

**Option 1: Systematic Section-by-Section Update** (Recommended)
- Update Methods section first (add 2.4, 2.5, expand 2.2)
- Update Results section (add 3.5, expand 3.2, 3.4)
- Update Discussion (expand 4.3)
- Fix DOCX script for superscripts
- Regenerate manuscript

**Option 2: Create New Version**
- Create `complete_drtb_manuscript_india_2025_v2.md`
- Incorporate all analyses
- Keep original as backup

---

## ✅ **Next Steps**

1. **Fix DOCX script** for reference superscripts (quick fix)
2. **Update Methods** section with bootstrap and economic methods
3. **Update Results** section with new findings
4. **Expand Discussion** with state-level insights
5. **Regenerate DOCX** with all updates
6. **Commit and push** to GitHub

---

**Estimated Time:** 30-45 minutes for complete update  
**Complexity:** Moderate (systematic additions, not rewrites)  
**Impact:** HIGH - transforms manuscript from good to exceptional

---

**Status:** 📝 **READY TO UPDATE**  
**Priority:** 🔴 **HIGH - CRITICAL FOR SUBMISSION**
