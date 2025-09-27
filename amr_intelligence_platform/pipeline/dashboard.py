#!/usr/bin/env python3
"""
AMR Forecasting Interactive Dashboard

Streamlit-based dashboard for exploring AMR forecasts and historical trends.
Allows users to select country/pathogen/antibiotic combinations and visualize
predictions with confidence intervals.

Usage:
    streamlit run pipeline/dashboard.py

Requirements:
    - Unified AMR dataset (data/amr_merged.csv)
    - Prophet forecasting library
    - Streamlit for the web interface
"""

import streamlit as st
import pandas as pd
from prophet import Prophet
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import numpy as np

# Page configuration
st.set_page_config(
    page_title="AMR Forecasting Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .risk-high {
        color: #d32f2f;
        font-weight: bold;
        background-color: #ffebee;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    .risk-moderate {
        color: #f57c00;
        font-weight: bold;
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    .risk-low {
        color: #388e3c;
        font-weight: bold;
        background-color: #e8f5e8;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    .forecast-insight {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_amr_data():
    """Load the unified AMR dataset with caching."""
    data_path = Path("data/amr_merged.csv")

    if not data_path.exists():
        st.error("❌ Unified dataset not found. Please run data extraction first:")
        st.code("python simple_amr_extract.py")
        st.stop()

    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])  # Remove invalid dates

    return df

def get_available_options(df):
    """Get unique values for dropdowns."""
    return {
        "countries": sorted(df["country"].dropna().unique()),
        "pathogens": sorted(df["pathogen"].dropna().unique()),
        "antibiotics": sorted(df["antibiotic"].dropna().unique()),
        "sources": sorted(df["source"].dropna().unique())
    }

def filter_data(df, country, pathogen, antibiotic):
    """Filter data for specific combination."""
    subset = df[
        (df["country"].str.lower() == country.lower()) &
        (df["pathogen"].str.lower() == pathogen.lower()) &
        (df["antibiotic"].str.lower() == antibiotic.lower())
    ].copy()

    if subset.empty:
        return None

    # Sort by date and remove duplicates
    subset = subset.sort_values("date").drop_duplicates(subset="date", keep="last")
    return subset

def create_forecast(df_subset, forecast_periods=24):
    """Generate forecast using Prophet."""
    try:
        # Prepare data for Prophet
        data = df_subset[["date", "percent_resistant"]].copy()
        data.columns = ["ds", "y"]
        data = data.dropna()

        if len(data) < 3:
            return None, "Insufficient data points for forecasting"

        # Fit Prophet model
        model = Prophet(
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.95
        )

        model.fit(data)

        # Generate forecast
        future = model.make_future_dataframe(periods=forecast_periods, freq="M")
        forecast = model.predict(future)

        # Mark historical vs forecast data
        forecast["is_forecast"] = forecast["ds"] > data["ds"].max()

        return forecast, None

    except Exception as e:
        return None, f"Forecasting failed: {str(e)}"

def create_forecast_plot(data, forecast, country, pathogen, antibiotic):
    """Create interactive forecast plot using Plotly."""
    # Historical data
    hist_data = data[data["ds"] <= data["ds"].max()].copy()

    # Forecast data
    forecast_data = forecast[forecast["is_forecast"]].copy()

    # Create figure
    fig = go.Figure()

    # Historical points
    fig.add_trace(go.Scatter(
        x=hist_data["ds"],
        y=hist_data["y"],
        mode="markers",
        name="Historical Data",
        marker=dict(color="blue", size=8, symbol="circle"),
        hovertemplate="<b>Historical</b><br>Date: %{x}<br>Resistance: %{y:.1f}%<extra></extra>"
    ))

    # Forecast line
    fig.add_trace(go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat"],
        mode="lines",
        name="Forecast",
        line=dict(color="red", width=3),
        hovertemplate="<b>Forecast</b><br>Date: %{x}<br>Predicted: %{y:.1f}%<extra></extra>"
    ))

    # Confidence interval
    fig.add_trace(go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat_upper"],
        mode="lines",
        name="Upper Bound",
        line=dict(color="gray", width=1, dash="dash"),
        hovertemplate="Upper bound: %{y:.1f}%<extra></extra>",
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=forecast["ds"],
        y=forecast["yhat_lower"],
        mode="lines",
        name="Lower Bound",
        line=dict(color="gray", width=1, dash="dash"),
        fill="tonos",
        fillcolor="rgba(255,0,0,0.2)",
        hovertemplate="Lower bound: %{y:.1f}%<extra></extra>",
        showlegend=False
    ))

    # Resistance threshold lines
    fig.add_hline(y=70, line_dash="dash", line_color="orange",
                 annotation_text="Warning (70%)", annotation_position="bottom right")
    fig.add_hline(y=80, line_dash="dash", line_color="red",
                 annotation_text="Critical (80%)", annotation_position="bottom right")

    # Update layout
    fig.update_layout(
        title=f"AMR Forecast: {pathogen} vs {antibiotic} in {country}",
        xaxis_title="Date",
        yaxis_title="Resistance Percentage (%)",
        yaxis_range=[0, 100],
        hovermode="x unified",
        width=800,
        height=500
    )

    return fig

def calculate_risk_metrics(current_resistance, forecast_peak, forecast_latest):
    """Calculate risk assessment metrics."""
    metrics = {
        "current": current_resistance,
        "forecast_peak": forecast_peak,
        "forecast_2yr": forecast_latest,
        "change_2yr": forecast_latest - current_resistance,
        "change_percent": ((forecast_latest - current_resistance) / current_resistance) * 100 if current_resistance > 0 else 0
    }

    # Risk level assessment
    if forecast_latest > 80:
        metrics["risk_level"] = "🚨 CRITICAL RISK"
        metrics["risk_color"] = "risk-high"
        metrics["recommendation"] = "Immediate intervention required - antibiotic stewardship crisis"
    elif forecast_latest > 70:
        metrics["risk_level"] = "⚠️ HIGH RISK"
        metrics["risk_color"] = "risk-high"
        metrics["recommendation"] = "Urgent action needed - monitor and implement stewardship protocols"
    elif forecast_latest > 50:
        metrics["risk_level"] = "🔶 MODERATE RISK"
        metrics["risk_color"] = "risk-moderate"
        metrics["recommendation"] = "Close monitoring required - consider preventive measures"
    else:
        metrics["risk_level"] = "✅ LOW RISK"
        metrics["risk_color"] = "risk-low"
        metrics["recommendation"] = "Current levels acceptable - maintain surveillance"

    return metrics

def main():
    """Main Streamlit application."""

    # Header
    st.markdown('<h1 class="main-header">🦠 Antimicrobial Resistance Forecasting Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("*Interactive exploration of AMR trends and future predictions*")

    # Load data
    with st.spinner("Loading AMR dataset..."):
        df = load_amr_data()

    if df.empty:
        st.stop()

    # Dataset overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Countries", len(df["country"].unique()))
    with col3:
        st.metric("Pathogens", len(df["pathogen"].unique()))
    with col4:
        st.metric("Data Sources", len(df["source"].unique()))

    # Sidebar controls
    st.sidebar.header("🎛️ Forecast Controls")

    # Get available options
    options = get_available_options(df)

    # Selectors
    country = st.sidebar.selectbox(
        "Select Country",
        ["Choose..."] + options["countries"]
    )

    if country != "Choose...":
        # Filter pathogens for selected country
        country_pathogens = df[df["country"] == country]["pathogen"].unique()
        pathogen = st.sidebar.selectbox(
            "Select Pathogen",
            ["Choose..."] + sorted(country_pathogens)
        )

        if pathogen != "Choose...":
            # Filter antibiotics for selected country + pathogen
            country_pathogen_abx = df[
                (df["country"] == country) &
                (df["pathogen"] == pathogen)
            ]["antibiotic"].unique()
            antibiotic = st.sidebar.selectbox(
                "Select Antibiotic",
                ["Choose..."] + sorted(country_pathogen_abx)
            )

    # Forecast parameters
    forecast_months = st.sidebar.slider("Forecast Horizon (Months)", 6, 48, 24, 6)

    # Main content
    if country != "Choose..." and pathogen != "Choose..." and antibiotic != "Choose...":
        st.header(f"📊 Analysis: {country} | {pathogen} | {antibiotic}")

        # Filter data
        subset = filter_data(df, country, pathogen, antibiotic)

        if subset is None or subset.empty:
            st.error("No data found for this combination. Try different selections.")
            st.stop()

        # Data summary
        col1, col2, col3 = st.columns(3)
        with col1:
            data_points = len(subset)
            st.metric("Data Points", f"{data_points:,}")
        with col2:
            date_range = f"{subset['date'].min().strftime('%Y-%m')} to {subset['date'].max().strftime('%Y-%m')}"
            st.metric("Date Range", date_range)
        with col3:
            current_resistance = subset["percent_resistant"].iloc[-1]
            st.metric("Current Resistance", ".1f")

        # Historical trend tabs
        tab1, tab2, tab3 = st.tabs(["📈 Forecast", "📊 Historical Data", "💡 Insights"])

        with tab1:
            st.subheader("🔮 Resistance Forecast")

            # Generate forecast
            with st.spinner("Generating forecast..."):
                forecast, error_msg = create_forecast(subset, forecast_months)

            if error_msg:
                st.error(error_msg)
            elif forecast is not None:
                # Create and display plot
                fig = create_forecast_plot(subset[["date", "percent_resistant"]].rename(columns={"date":"ds", "percent_resistant":"y"}),
                                         forecast, country, pathogen, antibiotic)
                st.plotly_chart(fig, use_container_width=True)

                # Forecast metrics
                current_resistance = subset["percent_resistant"].iloc[-1]
                forecast_peak = forecast[forecast["is_forecast"]]["yhat"].max()
                forecast_2yr = forecast[forecast["is_forecast"]]["yhat"].iloc[-1]

                metrics = calculate_risk_metrics(current_resistance, forecast_peak, forecast_2yr)

                # Risk assessment
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Risk Assessment: <span class="{metrics['risk_color']}">{metrics['risk_level']}</span></h3>
                    <p><strong>Recommendation:</strong> {metrics['recommendation']}</p>
                </div>
                """, unsafe_allow_html=True)

                # Forecast summary table
                forecast_summary = pd.DataFrame({
                    "Metric": ["Current Resistance", "Peak Forecast", f"{forecast_months}-Month Forecast", "Change", "Change %"],
                    "Value": [".1f"".1f"".1f""+.1f""+.1f"],
                    "Risk Level": [
                        "Current", "Peak", "Future",
                        "↗️ Increasing" if metrics['change_2yr'] > 5 else "→ Stable" if metrics['change_2yr'] > -5 else "↘️ Decreasing",
                        "Significant" if abs(metrics['change_percent']) > 20 else "Moderate" if abs(metrics['change_percent']) > 10 else "Minor"
                    ]
                })

                st.dataframe(forecast_summary, hide_index=True)

                # Export button
                forecast_export = forecast.copy()
                forecast_export["country"] = country
                forecast_export["pathogen"] = pathogen
                forecast_export["antibiotic"] = antibiotic

                csv_data = forecast_export.to_csv(index=False)
                st.download_button(
                    label="📥 Download Forecast Data (CSV)",
                    data=csv_data,
                    file_name=f"forecast_{country}_{pathogen}_{antibiotic}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="forecast_download"
                )

        with tab2:
            st.subheader("📊 Historical Data")

            # Raw data table
            st.dataframe(subset[["date", "percent_resistant", "tested", "resistant", "source"]])

            # Time series plot
            fig = px.line(subset, x="date", y="percent_resistant",
                         title=f"Historical Resistance Trend",
                         labels={"percent_resistant": "Resistance (%)", "date": "Date"})
            fig.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Warning")
            fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Critical")

            st.plotly_chart(fig, use_container_width=True)

            # Statistics
            st.subheader("📈 Statistical Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean", ".1f")
            with col2:
                st.metric("Maximum", ".1f")
            with col3:
                st.metric("Minimum", ".1f")
            with col4:
                st.metric("Trend", "↗️ Rising" if subset["percent_resistant"].iloc[-1] > subset["percent_resistant"].iloc[0] + 5 else "→ Stable")

        with tab3:
            st.subheader("💡 Forecasting Insights")

            if forecast is not None:
                # Key insights with markdown formatting
                st.markdown("### 🎯 Key Forecast Insights:")

                current = subset["percent_resistant"].iloc[-1]
                forecast_2yr = forecast[forecast["is_forecast"]]["yhat"].iloc[-1]

                st.markdown(f"""
                <div class="forecast-insight">
                <h4>📈 Resistance Trajectory:</h4>
                <ul>
                <li><strong>Current Level:</strong> {current:.1f}% resistance</li>
                <li><strong>Projected Trend:</strong> {'Increases by +.1f)' if forecast_2yr > current + 5 else 'Stable (+/-5% change)' if forecast_2yr > current - 5 else f'Decreases by {current - forecast_2yr:.1f}%'}</li>
                <li><strong>Risk Assessment:</strong> {calculate_risk_metrics(current, forecast[forecast["is_forecast"]]["yhat"].max(), forecast_2yr)['risk_level']}</li>
                </ul>
                </div>
                """, unsafe_allow_html=True)

                # Intervention recommendations
                st.markdown("### 🏥 Strategic Recommendations:")

                if forecast_2yr > 80:
                    st.error("🚨 **CRITICAL INTERVENTION REQUIRED**")
                    st.markdown("""
                    - 🔴 Immediate review of antibiotic stewardship protocols
                    - 🔴 Enhanced infection prevention measures
                    - 🔴 Consideration of antibiotic reserve medications
                    - 🔴 Urgent surveillance expansion
                    """)

                elif forecast_2yr > 70:
                    st.warning("⚠️ **HIGH PRIORITY INTERVENTION**")
                    st.markdown("""
                    - 🟡 Implement antibiotic rotation protocols
                    - 🟡 Enhanced laboratory testing for resistance
                    - 🟡 Staff training in appropriate antibiotic use
                    - 🟡 Regular resistance pattern monitoring
                    """)

                elif forecast_2yr > 50:
                    st.warning("🔶 **MODERATE MONITORING REQUIRED**")
                    st.markdown("""
                    - 🟡 Continue current surveillance practices
                    - 🟡 Periodic protocol reviews
                    - 🟡 Awareness campaigns for appropriate use
                    - 🟡 Consider targeted interventions if trend continues
                    """)

                else:
                    st.success("✅ **CURRENT PROTOCOLS SUFFICIENT**")
                    st.markdown("""
                    - 🟢 Maintain existing surveillance and stewardship
                    - 🟢 Continue appropriate antibiotic use education
                    - 🟢 Monitor for any emerging resistance patterns
                    """)

    else:
        st.info("👈 Select a Country, Pathogen, and Antibiotic combination in the sidebar to begin forecasting.")

    # Footer
    st.markdown("---")
    st.caption("*AMR Forecasting Dashboard - Evidence-based antibiotic resistance monitoring and policy support*")

if __name__ == "__main__":
    main()
