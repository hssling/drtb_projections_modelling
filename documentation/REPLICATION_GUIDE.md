# Replication Guide
## How to Fully Reproduce the India MDR-TB Forecasting Study

**Estimated Time:** 2-3 hours (including data download)  
**Difficulty:** Intermediate (requires Python knowledge)  
**Last Updated:** December 18, 2025

---

## Prerequisites

### System Requirements
- **Operating System:** Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 500MB for code and data
- **Internet:** Required for data download

### Software Requirements
- **Python:** 3.8 or higher ([Download](https://www.python.org/downloads/))
- **Git:** For cloning repository ([Download](https://git-scm.com/downloads))
- **Text Editor:** VS Code, PyCharm, or similar (optional but recommended)

---

## Step 1: Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/[username]/india-mdrtb-forecasting.git
cd india-mdrtb-forecasting
```

**Alternative:** Download ZIP from GitHub and extract

---

## Step 2: Set Up Python Environment

### Option A: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt
```

### Option B: Using Conda

```bash
# Create conda environment
conda create -n mdrtb python=3.9
conda activate mdrtb

# Install dependencies
pip install -r code/requirements.txt
```

---

## Step 3: Verify Installation

```bash
# Test Python installation
python --version  # Should show 3.8 or higher

# Test package imports
python -c "import numpy, pandas, statsmodels, matplotlib; print('All packages installed successfully!')"
```

**Expected Output:** "All packages installed successfully!"

---

## Step 4: Download Source Data (Optional)

The repository includes processed data (`data/authentic_drtb_forecast_india_2025.json`), but you can verify against original sources:

### WHO Global TB Reports

1. Visit: https://www.who.int/teams/global-tuberculosis-programme/data
2. Download reports for years 2017-2025
3. Extract MDR/RR-TB notification data for India

### India TB Reports

1. Visit: https://tbcindia.gov.in
2. Navigate to "Publications" → "India TB Reports"
3. Download reports for years 2017-2025
4. Extract state-wise MDR-TB detection data

**Note:** This step is optional as verified data is already included in the repository.

---

## Step 5: Run Main Forecasting Analysis

```bash
cd code
python authentic_drtb_forecasting_india_2025.py
```

**Expected Runtime:** 10-30 seconds

**Output Files:**
- `../data/authentic_drtb_forecast_india_2025.json`

**Verification:**
- Check that JSON file contains 159 lines
- Verify 2030 Status Quo projection = 84,205 cases
- Confirm metadata version = "3.0 (World Class)"

---

## Step 6: Generate Bootstrap Uncertainty

```bash
python generate_bootstrap_uncertainty.py
```

**Expected Runtime:** 2-5 minutes (1,000 bootstrap iterations)

**Output Files:**
- `../supplementary_materials/Bootstrap_Confidence_Intervals.csv`
- `../supplementary_materials/Supplementary_Figure_S1_Bootstrap_Uncertainty.png`
- `../supplementary_materials/Supplementary_Figure_S2_Residual_Diagnostics.png`

**Verification:**
- CSV should have 10 rows (2025-2034)
- 2030 CI should be approximately 84,205 ± 12,867
- Figures should be 300 DPI PNG files

---

## Step 7: Generate Manuscript Figures

```bash
python generate_authentic_figures.py
```

**Expected Runtime:** 5-10 seconds

**Output Files:**
- `../manuscript/figures/Figure_1_MDR_Burden_Authentic.png`
- `../manuscript/figures/Figure_2_Intervention_Scenarios_Authentic.png`

**Verification:**
- Both figures should be 300 DPI
- Figure 1 should show vertical "Forecast Start (2025)" line
- Figure 2 should show three scenario lines (Optimistic, Status Quo, Pessimistic)

---

## Step 8: Generate State-Level Map (Optional)

```bash
python generate_authentic_map.py
```

**Note:** Requires India shapefile (included in repository or download from GADM)

**Output:**
- `../manuscript/figures/Figure_3_State_Burden_Authentic.png`

---

## Step 9: Generate DOCX Manuscript

```bash
python convert_manuscript_to_docx.py
```

**Expected Runtime:** 5-10 seconds

**Output:**
- `../manuscript/IJMR_Submission_DRTB_Forecast_India_2025_Final_v2.docx`

**Verification:**
- Document should be ~25 pages
- Double-spaced, Times New Roman 12pt
- Contains 3 figures and 2 tables
- References in Vancouver style

---

## Step 10: Open Interactive Dashboard

```bash
# Navigate to dashboard directory
cd ../interactive_dashboard

# Open in default browser
# Windows:
start MDR_TB_Forecasting_Dashboard.html
# macOS:
open MDR_TB_Forecasting_Dashboard.html
# Linux:
xdg-open MDR_TB_Forecasting_Dashboard.html
```

**Verification:**
- Dashboard should load in browser
- Sliders should be interactive
- Charts should update in real-time
- Download button should export JSON

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'statsmodels'"

**Solution:**
```bash
pip install statsmodels
```

### Issue: "FileNotFoundError: [Errno 2] No such file or directory"

**Solution:** Ensure you're running scripts from the `code/` directory:
```bash
cd code
python [script_name].py
```

### Issue: Bootstrap script runs very slowly

**Solution:** Reduce bootstrap iterations (edit line 11 in `generate_bootstrap_uncertainty.py`):
```python
N_BOOTSTRAP = 100  # Instead of 1000 for faster testing
```

### Issue: Figures don't match published versions exactly

**Possible Causes:**
- Different matplotlib version (minor visual differences acceptable)
- Different random seed in bootstrap (use `np.random.seed(42)` for reproducibility)
- Updated source data (if WHO/NTEP releases new reports)

### Issue: DOCX generation fails

**Solution:** Ensure python-docx is installed:
```bash
pip install python-docx
```

---

## Expected Results

### Numerical Verification

| Metric | Expected Value | Tolerance |
|--------|---------------|-----------|
| 2024 Detected Cases | 65,200 | Exact |
| 2030 Status Quo | 84,205 | ±100 |
| 2030 Optimistic | 59,910 | ±100 |
| 2030 Pessimistic | 91,782 | ±100 |
| Cases Averted (Optimistic) | 217,215 | ±500 |
| Model AIC | 161.7 | ±0.5 |
| Model BIC | 162.1 | ±0.5 |

### File Verification Checksums

```bash
# Verify JSON output (should match)
md5sum data/authentic_drtb_forecast_india_2025.json
# Expected: [MD5 hash to be added]
```

---

## Advanced Replication

### Modify Parameters

To test different scenarios, edit `authentic_drtb_forecasting_india_2025.py`:

```python
# Line 85-95: Modify scenario assumptions
optimistic_reduction = 0.05  # Change to 0.03 for less aggressive
pessimistic_increase = 0.02  # Change to 0.03 for worse scenario
```

### Run Sensitivity Analysis

```python
# Test different damping parameters
for phi in [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
    # Modify line 65 in forecasting script
    # Re-run and compare outputs
```

### Generate Custom State Projections

Edit `Supplementary_Table_S1_State_Projections.md` with your own state-level data.

---

## Validation Against Published Results

After running all scripts, compare your outputs to published values in:
- `documentation/MANUSCRIPT_VERIFICATION_REPORT.md`

**All values should match within stated tolerance (typically ±1%).**

---

## Time Estimates

| Step | Time Required |
|------|---------------|
| Environment setup | 10-15 minutes |
| Main forecasting | 30 seconds |
| Bootstrap analysis | 2-5 minutes |
| Figure generation | 10 seconds |
| DOCX generation | 10 seconds |
| **Total** | **15-25 minutes** |

*(Excluding initial data download and software installation)*

---

## Getting Help

### Common Questions

**Q: Do I need to download WHO/NTEP data manually?**  
A: No, processed data is included. Manual download only needed for independent verification.

**Q: Can I run this on Windows?**  
A: Yes, all scripts are cross-platform compatible.

**Q: What if my results differ slightly?**  
A: Minor differences (<1%) are acceptable due to floating-point precision and library versions.

**Q: Can I modify the code for my own country?**  
A: Yes! The code is open-source (MIT License). Adapt as needed.

### Support Channels

1. **GitHub Issues:** For code bugs or technical problems
2. **Email:** hssling@yahoo.com for methodology questions
3. **Documentation:** Check `documentation/` folder for detailed guides

---

## Citation for Replication

If you replicate this study or use the code, please cite:

```
Siddalingaiah HS. India MDR-TB Forecasting Study (2025-2035): 
Replication Package. GitHub. 2025. 
Available at: https://github.com/[username]/india-mdrtb-forecasting
```

---

## Certification

**I certify that following this guide will produce results that match the published manuscript within stated tolerances.**

**Signed:** Dr. Siddalingaiah H S  
**Date:** December 18, 2025

---

**Last Updated:** December 18, 2025  
**Guide Version:** 1.0  
**Tested On:** Windows 11, macOS 13, Ubuntu 22.04
