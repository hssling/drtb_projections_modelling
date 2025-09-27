#!/usr/bin/env python3
"""
AMR Forecasting Dashboard - Interactive Streamlit Application

Interactive exploration of antimicrobial resistance forecasting with real-time model selection,
pathogen-antibiotic filtering, and visualization of resistance trends.

Usage:
    streamlit run dashboard.py

Requirements:
    pip install streamlit plotly pandas numpy
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="AMR Forecasting Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .warning-text {
        color: #ff6b35;
        font-weight: bold;
    }
    .alert-text {
        color: #d32f2f;
        font-weight: bold;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

def load_amr_data():
    """Load AMR dataset for dashboard."""
    data_paths = [
        "../data/amr_data_processed.csv",
        "../data/amr_data.csv"
    ]

    for path in data_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df['date'] = pd.to_datetime(df['date'])
            return df

    # Fallback to default sample data structure
    st.error("No AMR data files found. Please ensure you have amr_data.csv in the data/ folder.")
    return pd.DataFrame()

def filter_data(df, pathogen_filter=None, antibiotic_filter=None, date_range=None):
    """Filter AMR data based on user selections."""
    filtered_df = df.copy()

    if pathogen_filter and pathogen_filter != "All":
        filtered_df = filtered_df[filtered_df['pathogen'] == pathogen_filter]

    if antibiotic_filter and antibiotic_filter != "All":
        filtered_df = filtered_df[filtered_df['antibiotic'] == antibiotic_filter]

    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]

    return filtered_df

def create_resistance_trend_plot(df, pathogen, antibiotic):
    """Create interactive resistance trend plot."""
    subset = df[(df['pathogen'] == pathogen) & (df['antibiotic'] == antibiotic)].copy()

    if len(subset) == 0:
        st.warning(f"No data available for {pathogen} vs {antibiotic}")
        return None

    subset = subset.sort_values('date')

    # Create figure with secondary y-axis
    fig = go.Figure()

    # Resistance percentage line
    fig.add_trace(go.Scatter(
        x=subset['date'],
        y=subset['percent_resistant'],
        mode='lines+markers',
        name='Resistance %',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        hovertemplate='<b>Date:</b> %{x}<br><b>Resistance:</b> %{y:.1f}%<extra></extra>'
    ))

    # DDD consumption if available
    if 'ddd' in subset.columns and subset['ddd'].notna().any():
        fig.add_trace(go.Scatter(
            x=subset['date'],
            y=subset['ddd'],
            mode='lines+markers',
            name='DDD Consumption',
            line=dict(color='#ff7f0e', width=2, dash='dot'),
            marker=dict(symbol='diamond', size=6),
            yaxis='y2',
            hovertemplate='<b>Date:</b> %{x}<br><b>DDD:</b> %{y:.1f}<extra></extra>'
        ))

    # Add resistance thresholds
    current_resistance = subset['percent_resistant'].iloc[-1] if len(subset) > 0 else 0
    colors = {'low': 'green', 'medium': 'orange', 'high': 'red', 'critical': 'darkred'}

    risk_level = 'low'
    if current_resistance > 80:
        risk_level = 'critical'
    elif current_resistance > 70:
        risk_level = 'high'
    elif current_resistance > 50:
        risk_level = 'medium'

    # Update layout
    fig.update_layout(
        title=f"AMR Trend: {pathogen} vs {antibiotic}",
        xaxis_title="Date",
        yaxis_title="Resistance Percentage (%)",
        yaxis2=dict(title="DDD Consumption", overlaying='y', side='right'),
        hovermode='x unified',
        width=800,
        height=500
    )

    # Add threshold lines
    fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Critical (80%)")
    fig.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="High Risk (70%)")

    return fig

def create_summary_metrics(df, pathogen, antibiotic):
    """Create summary metrics cards."""
    subset = df[(df['pathogen'] == pathogen) & (df['antibiotic'] == antibiotic)]

    if len(subset) == 0:
        return None, None, None, None, "No data"

    current_resistance = subset['percent_resistant'].iloc[-1]
    avg_resistance = subset['percent_resistant'].mean()
    max_resistance = subset['percent_resistant'].max()
    trend_change = subset['percent_resistant'].iloc[-1] - subset['percent_resistant'].iloc[0] if len(subset) > 1 else 0

    # Determine risk level
    if current_resistance > 80:
        risk_level = "🚨 CRITICAL"
    elif current_resistance > 70:
        risk_level = "⚠️ HIGH"
    elif current_resistance > 50:
        risk_level = "🔶 MEDIUM"
    else:
        risk_level = "✅ LOW"

    return current_resistance, avg_resistance, max_resistance, trend_change, risk_level

def create_forecast_placeholder(pathogen, antibiotic):
    """Create placeholder forecast visualization."""
    # This would be replaced with actual forecast loading
    fig = go.Figure()

    # Dummy forecast data (24 months ahead)
    dates = pd.date_range(start=datetime.now(), periods=25, freq='M')[1:]
    current_resistance = st.session_state.get('current_resistance', 50)
    forecast = [current_resistance + i*0.5 for i in range(24)]

    # Historical + forecast
    fig.add_trace(go.Scatter(
        x=dates[:12], y=[current_resistance - i*0.2 for i in range(12)],  # Dummy historical
        mode='lines+markers', name='Historical',
        line=dict(color='blue', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=dates[-12:], y=forecast[-12:],  # Near-term forecast
        mode='lines+markers', name='Forecast',
        line=dict(color='orange', width=2, dash='dash')
    ))

    fig.update_layout(
        title=f"Forecast Preview: {pathogen} vs {antibiotic}",
        xaxis_title="Date",
        yaxis_title="Resistance %"
    )

    return fig

# Main application
def main():
    # Header
    st.markdown('<h1 class="main-header">💊 AMR Forecasting Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("*Interactive analysis of antimicrobial resistance trends and forecasting*")

    # Load data
    df = load_amr_data()

    if df.empty:
        st.stop()

    # Sidebar controls
    st.sidebar.header("🎛️ Dashboard Controls")

    # Data overview
    st.sidebar.subheader("📊 Data Overview")
    st.sidebar.metric("Total Records", f"{len(df):,}")
    st.sidebar.metric("Pathogen Types", len(df['pathogen'].unique()))
    st.sidebar.metric("Antibiotic Types", len(df['antibiotic'].unique()))
    st.sidebar.metric("Date Range", f"{df['date'].min().strftime('%Y-%m')} - {df['date'].max().strftime('%Y-%m')}")

    # Filters
    col1, col2 = st.sidebar.columns(2)

    with col1:
        pathogen_options = ["All"] + sorted(df['pathogen'].unique().tolist())
        selected_pathogen = st.selectbox("Select Pathogen", pathogen_options)

    with col2:
        antibiotic_options = ["All"] + sorted(df['antibiotic'].unique().tolist())
        selected_antibiotic = st.selectbox("Select Antibiotic", antibiotic_options)

    # Date range filter
    date_min = df['date'].min().date()
    date_max = df['date'].max().date()
    date_range = st.sidebar.slider(
        "Date Range",
        min_value=date_min,
        max_value=date_max,
        value=(date_min, date_max)
    )

    # Apply filters
    filtered_df = filter_data(df, selected_pathogen, selected_antibiotic, date_range)

    # Main content area
    if len(filtered_df) > 0:
        st.header("📈 Resistance Trend Analysis")

        # Sample pathogen-antibiotic pairs for demo
        demo_pairs = [
            ("E.coli", "Ciprofloxacin"),
            ("Klebsiella pneumoniae", "Meropenem"),
            ("Acinetobacter baumannii", "Imipenem"),
            ("Pseudomonas aeruginosa", "Ciprofloxacin")
        ]

        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Current Trends", "🔮 Model Forecasts", "📋 Data Summary"])

        with tab1:
            st.subheader("Current Resistance Trends")

            # Quick selection
            quick_select = st.selectbox(
                "Quick Select Pathogen-Antibiotic Pair:",
                ["🔍 Custom Selection"] + [f"{p} vs {a}" for p, a in demo_pairs]
            )

            if quick_select == "🔍 Custom Selection":
                selected_p, selected_a = selected_pathogen, selected_antibiotic
            else:
                selected_p, selected_a = quick_select.replace(" vs ", "|").split("|")

            # Metrics cards
            if selected_p != "All" and selected_a != "All":
                current_res, avg_res, max_res, trend_change, risk_level = create_summary_metrics(df, selected_p, selected_a)

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Current Resistance", f"{current_res:.1f}%", f"{trend_change:+.1f}%")
                with col2:
                    st.metric("Average Resistance", f"{avg_res:.1f}%")
                with col3:
                    st.metric("Peak Resistance", f"{max_res:.1f}%")
                with col4:
                    st.markdown(f"**Risk Level:** {risk_level}")

                # Main trend plot
                fig = create_resistance_trend_plot(df, selected_p, selected_a)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Model Forecasts")
            st.info("🔮 Forecasting models available in pipeline scripts. To run predictions:")

            code_example = '''
# Prophet forecast
python pipeline/forecast_prophet.py

# ARIMA forecast
python pipeline/forecast_arima.py

# Results saved to reports/ folder
            '''
            st.code(code_example, language='bash')

            # Placeholder forecast visualization
            if selected_pathogen != "All" and selected_antibiotic != "All":
                st.subheader(f"📈 Forecast Preview: {selected_pathogen} vs {selected_antibiotic}")
                placeholder_fig = create_forecast_placeholder(selected_pathogen, selected_antibiotic)
                st.plotly_chart(placeholder_fig, use_container_width=True)

                st.markdown("""
                **Note**: This is a placeholder. Run the actual forecasting scripts to generate real predictions.

                **Available Models:**
                - 🤖 **Prophet**: Includes antibiotic consumption regressor
                - 🔬 **ARIMA**: Statistical time series modeling
                - 🧠 **LSTM**: Deep learning neural networks (optional)
                """)

        with tab3:
            st.subheader("Data Summary & Export")

            st.markdown(f"**Filtered Dataset:** {len(filtered_df):,} records")

            # Data preview
            st.subheader("Data Preview")
            st.dataframe(filtered_df.head(20))

            # Summary statistics
            st.subheader("Summary Statistics")
            numeric_cols = ['percent_resistant', 'resistant', 'tested']
            available_cols = [col for col in numeric_cols if col in filtered_df.columns]

            if available_cols:
                st.dataframe(filtered_df[available_cols].describe())

            # Export functionality
            st.subheader("Export Data")

            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=csv,
                file_name=f"amr_filtered_{selected_pathogen}_{selected_antibiotic}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    else:
        st.warning("No data matches your current filter selections. Try adjusting the filters.")

    # Footer
    st.markdown("---")
    st.markdown("*AMR Forecasting Dashboard - Independent Research Initiative*")

if __name__ == "__main__":
    main()
