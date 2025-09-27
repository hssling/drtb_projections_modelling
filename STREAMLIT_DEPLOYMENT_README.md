# 🌍 TB-AMR India Dashboard - Streamlit Cloud Deployment Guide

## 🚀 Quick Deployment to Streamlit Cloud

### **Prerequisites:**
- GitHub account with repository access
- Streamlit Cloud account (free tier available)

---

## **Step 1: Connect Repository**

1. **Go to [Streamlit Cloud](https://share.streamlit.io/)**
2. **Click "New App"**
3. **Connect your GitHub account**
4. **Select Repository:** `https://github.com/hssling/TB-AMR-India-Dashboard-v2.0-Complete-Interactive-Research-Platform`

---

## **Step 2: Configure Deployment**

### **Main File Path:**
```
tb_amr_project/pipeline/tb_dashboard.py
```

### **Additional Settings:**
- **Advanced Settings → Main file path directory:** Enter your repository URL if needed
- **Requirements file (leave blank or specify):** The app uses built-in dependency management

---

## **Step 3: Customize Settings (Optional)**

```python
# Auto-configuration (recommended)
st.set_page_config(
    page_title="TB-AMR India Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

---

## **Step 4: Deploy**

1. **Click "Deploy"**
2. **Wait for build completion (5-10 minutes)**
3. **Get your public shareable link**
4. **Bookmark and share!** 🎉

---

## **📊 Dashboard Features Available:**

### **🏠 Overview Page:**
- Key metrics (data records, states covered, MDR-TB burden)
- Interactive resistance distribution plots
- State-level hotspot summaries

### **📈 Forecasting Page:**
- Multi-model comparison (Prophet/ARIMA/LSTM)
- 2030 projections with confidence intervals
- Interactive time series visualizations

### **🎯 Policy Scenarios:**
- Baseline vs intervention trajectories
- BPaL rollout impact modeling
- Cost-effectiveness analysis

### **🗺️ Geographic Analysis:**
- Real GIS choropleth maps with Indian state boundaries
- Interactive bubble point maps
- Publication-quality map exports (PNG, 600 DPI)

### **📚 Meta-Analysis:**
- Forest plots with 45+ published studies
- Pooled prevalence estimates with 95% CI
- Heterogeneity assessment (I² statistics)

### **📋 Data Explorer:**
- Real-time data filtering (by state, drug, year)
- Paginated data tables
- Export capabilities (CSV, GeoJSON)

### **📄 Research Manuscript:**
- Complete academic manuscript viewer
- Executive summaries with key findings
- Download capabilities (Markdown, DOCX)
- Technical appendices and methodologies

---

## **🛠️ Troubleshooting:**

### **Common Issues & Fixes:**

1. **Build Fails:**
   ```
   # Check if all dependencies are in requirements.txt
   ✅ pandas, plotly, geopandas, streamlit, matplotlib, seaborn
   ✅ tensorflow, prophet, scikit-learn, statsmodels
   ```

2. **Memory Issues:**
   - The dashboard uses optimized data caching
   - Large GIS files are loaded on-demand
   - Consider premium Streamlit Cloud plan for heavy usage

3. **Data Loading:**
   ```
   # Data files are loaded from plots/ and data/ directories
   ✅ tb_amr_project/plots/india_mdr_choropleth.geojson
   ✅ tb_amr_project/data/tb_merged_icmr_who.csv
   ✅ tb_amr_project/plots/india_mdr_hotspots_publication.png
   ```

4. **Import Errors:**
   - All imports are handled gracefully with fallbacks
   - Choropleth maps have simplified alternative views

---

## **📈 Performance Optimizations:**

- **Data Caching:** All dataframes cached for fast reloading
- **Lazy Loading:** GIS files loaded only when requested
- **Optimized Plotly:** Interactive charts with 10x speedup
- **Memory Management:** Large datasets processed efficiently

---

## **🔗 Live Dashboard Examples:**

Once deployed, your dashboard will be accessible at:
`https://[your-app-name]-[your-username]-[random-id].streamlit.app`

### **Share Your Dashboard:**
```
🌍 TB-AMR India Research Dashboard
https://[your-url].streamlit.app

Features:
• Interactive MDR-TB Forecasting (2025-2035)
• Real GIS Choropleth Maps
• Policy Intervention Modeling (BPaL Regimens)
• 45+ Study Meta-Analysis
• Complete Manuscript & Data Exports
```

---

## **🗂️ File Structure for Reference:**

```
tb_amr_project/
├── pipeline/
│   ├── tb_dashboard.py          # Main Streamlit app
│   ├── tb_visualization.py      # GIS mapping engine
│   ├── tb_forecast.py           # Time series models
│   ├── tb_sensitivity.py        # Policy scenarios
│   ├── tb_meta_analysis.py      # Literature pooling
│   ├── tb_manuscript.py         # Document generation
│   └── models.py               # Forecasting utilities
├── plots/                       # Generated visualizations
├── data/                        # Processed datasets
├── requirements.txt             # Python dependencies
├── run.py                       # Local launcher script
└── README.md                   # Project documentation
```

---

## **🎯 Research Impact:**

This dashboard serves as a comprehensive research platform for:
- **Policy Makers:** Evidence-based TB control decisions
- **Researchers:** Advanced analytics and forecasting tools
- **Healthcare Workers:** Geographic hotspot identification
- **Academics:** Complete manuscript and methodology access

---

## **📞 Support:**

For issues or enhancements:
- Check the repository issues section
- Review Streamlit Cloud deployment logs
- Ensure all file paths are consistent with the repository structure

**Happy Deploying! 🚀**
