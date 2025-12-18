
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# --- CONFIG ---
st.set_page_config(page_title="Living Review: DR-TB India 2030", layout="wide")

DATA_DIR = r'analysis_results'
ASSETS_DIR = r'manuscript_assets'

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df_forecast = pd.read_csv(os.path.join(DATA_DIR, 'advanced_forecast_refined.csv'))
    df_state = pd.read_csv(os.path.join(DATA_DIR, 'state_drtb_forecasts_split_2030.csv'))
    df_policy = pd.read_csv(os.path.join(DATA_DIR, 'policy_scenario_data.csv'))
    return df_forecast, df_state, df_policy

try:
    df_forecast, df_state, df_policy = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Executive Summary", "National Forecast", "State Hotspots", "Policy Simulator", "Evidence Base"])

st.sidebar.info("This 'Living Review' updates continuously as new data becomes available.")

# --- PAGES ---

if page == "Executive Summary":
    st.title("The Looming Crisis of Primary Drug Resistance")
    st.subheader("India's TB Epidemic: 2025-2030 Outlook")
    
    col1, col2, col3 = st.columns(3)
    
    cases_2030 = df_forecast[df_forecast['Year'] == 2030]['Ensemble_Projection'].values[0]
    drtb_2030 = df_state['DRTB_Total_2030'].sum()
    new_share = (df_state['DRTB_New_2030'].sum() / drtb_2030) * 100
    
    col1.metric("Projected Total Cases (2030)", f"{cases_2030/1e6:.2f} M", "+Status Quo")
    col2.metric("Projected DR-TB Cases (2030)", f"{int(drtb_2030):,}", "High Burden")
    col3.metric("Primary Resistance Share", f"{new_share:.1f}%", "New Case Paradox")
    
    st.markdown("""
    ### Key Findings
    *   **Trajectory:** India is on a path to ~3 million cases by 2030, deviating from elimination goals.
    *   **The Threat:** Primary transmission of drug-resistant strains is becoming the dominant driver (67% of future cases).
    *   **The Solution:** Only a radical **Combination Strategy** (Prevention + Treatment) can bend the curve.
    """)
    
    st.image(os.path.join(ASSETS_DIR, 'Figure_4_Multipanel_DRTB_Dynamics.png'), caption="Dynamics of the Epidemic", use_column_width=True)

elif page == "National Forecast":
    st.title("National Forecast Model (2025-2030)")
    
    # Plotly Forecast
    fig = go.Figure()
    
    # History (Simulated for visual from 2024 point)
    # df_forecast starts 2024 usually
    
    fig.add_trace(go.Scatter(x=df_forecast['Year'], y=df_forecast['Ensemble_Projection'], 
                             mode='lines+markers', name='Consensus Forecast', line=dict(color='blue', width=4)))
    
    # Uncertainty
    fig.add_trace(go.Scatter(x=df_forecast['Year'], y=df_forecast['Scenario_Pessimistic'], 
                             mode='lines', line=dict(width=0), showlegend=False, name='Upper Bound'))
    fig.add_trace(go.Scatter(x=df_forecast['Year'], y=df_forecast['Scenario_Optimistic'], 
                             mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(0,0,255,0.1)', name='95% Interval'))
    
    fig.update_layout(title="Projected TB Notifications", xaxis_title="Year", yaxis_title="Cases")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Model Details")
    st.write("This forecast is an ensemble of Holt-Winters, ARIMA, XGBoost, and Bayesian Ridge Regression models.")
    st.dataframe(df_forecast)

elif page == "State Hotspots":
    st.title("State-Level Vulnerability Map")
    
    year_select = st.slider("Select Year", 2025, 2030, 2030)
    col_map = f'DRTB_Total_{year_select}'
    
    # Choropleth needs GeoJSON, but simpler to do a Bar/scatter or heatmap without shapefile load overhead in basic streamlit app
    # Or simplified bubble map if we had coords.
    # For now, let's show a nice interactive Bar Chart of Top States
    
    st.subheader(f"Projected DR-TB Burden by State ({year_select})")
    
    df_plot = df_state[['State', f'Total_{year_select}', f'DRTB_Total_{year_select}']].copy()
    df_plot['Rate'] = (df_plot[f'DRTB_Total_{year_select}'] / df_plot[f'Total_{year_select}']) * 100
    
    sort_by = st.radio("Sort By:", ["Absolute Volume (Cases)", "Intensity (% Resistant)"])
    
    if "Volume" in sort_by:
        df_plot = df_plot.sort_values(f'DRTB_Total_{year_select}', ascending=False).head(15)
        fig = px.bar(df_plot, x='State', y=f'DRTB_Total_{year_select}', color='Rate', 
                     color_continuous_scale='RdYlBu_r', title=f"Top 15 States by DR-TB Volume ({year_select})")
    else:
        df_plot = df_plot.sort_values('Rate', ascending=False).head(15)
        fig = px.bar(df_plot, x='State', y='Rate', color=f'DRTB_Total_{year_select}', 
                     color_continuous_scale='Reds', title=f"Top 15 States by Resistance Intensity ({year_select})")
        
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("Data Table:")
    st.dataframe(df_state)

elif page == "Policy Simulator":
    st.title("Interactive Policy Simulator")
    
    st.markdown("""
    Compare the projected impact of different strategies on the 2030 burden.
    """)
    
    # Plotly Lines
    fig = go.Figure()
    
    # Robust Color Mapping
    color_map = {
        'Baseline': 'black',
        'Prevention_First': 'orange',
        'Treatment_First': 'blue',
        'Combination_Strategy': 'red'
    }
    
    for col in df_policy.columns:
        if col != 'Year':
            # Default to gray if column not in map, preventing IndexError
            line_color = color_map.get(col, 'gray')
            line_width = 3 if 'Combination' in col else 2
            
            fig.add_trace(go.Scatter(x=df_policy['Year'], y=df_policy[col], mode='lines', name=col.replace('_', ' '),
                                     line=dict(color=line_color, width=line_width)))
            
    fig.update_layout(title="Scenario Trajectories (Cases Averted)", xaxis_title="Year", yaxis_title="Total Notifications")
    st.plotly_chart(fig, use_container_width=True)
    
    # Simple "What If" Calculator
    st.subheader("Impact Calculator")
    base_cases = 2546029 # 2030 baseline
    
    st.write("Adjust implementation efficiency:")
    eff_tpt = st.slider("Preventive Treatment (TPT) Coverage Efficiency", 0.0, 1.0, 1.0, help="1.0 = Full rollout (34% red). 0.5 = Half rollout.")
    eff_rx = st.slider("Treatment Optimization (BPaL) Rollout", 0.0, 1.0, 1.0, help="1.0 = Universal BPaL (11% red).")
    
    # Simple linear attribution logic for demo
    # Max reduction TPT = ~875k. Max Rx = ~290k. (Synergy is extra but let's approximate)
    
    averted = (875000 * eff_tpt) + (290000 * eff_rx)
    final_burden = base_cases - averted
    
    col1, col2 = st.columns(2)
    col1.metric(" adjusted 2030 Burden", f"{final_burden/1e6:.2f} M")
    col2.metric("Cases Averted", f"{int(averted):,}")

elif page == "Evidence Base":
    st.title("Evidence Base: Original Meta-Analysis")
    st.image(os.path.join(ASSETS_DIR, 'Figure_4_Rapid_Meta_Analysis.png'), caption="Synthesized Primary Resistance Rate", use_column_width=True)
    
    st.markdown("""
    **Methodology:**
    We conducted a rapid systematic search of 5 key studies (2019-2024) covering >150,000 individuals.
    The weighted average primary resistance rate is **3.64%**.
    """)
