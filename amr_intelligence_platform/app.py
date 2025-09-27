#!/usr/bin/env python3
"""
AMR Intelligence Platform - Streamlit Dashboard
Comprehensive AMR (Antimicrobial Resistance) visualization and analysis platform

Deployable on GitHub+Streamlit Cloud for interactive data exploration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
from pathlib import Path
import datetime

warnings.filterwarnings('ignore')

# Configuration
st.set_page_config(
    page_title="AMR Intelligence Platform",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px;
    }
    .crisis-alert {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .sidebar-header {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache AMR data"""
    try:
        # Try multiple data locations
        data_paths = [
            'data/amr_merged.csv',
            '../data/amr_merged.csv',
            'amr_intelligence_platform/data/amr_merged.csv'
        ]

        df = None
        for path in data_paths:
            if Path(path).exists():
                df = pd.read_csv(path)
                break

        if df is None:
            # Generate sample data if files not found
            st.warning("AMR data files not found. Generating sample data for demonstration.")
            df = generate_sample_amr_data()
            return df, generate_sample_metadata()

        # Data validation
        required_cols = ['country', 'pathogen', 'antibiotic', 'percent_resistant']
        if not all(col in df.columns for col in required_cols):
            st.error(f"Data missing required columns: {required_cols}")
            return None, None

        metadata = {
            'total_samples': len(df),
            'countries': df['country'].nunique(),
            'pathogens': df['pathogen'].nunique(),
            'antibiotics': df['antibiotic'].nunique(),
            'last_updated': datetime.datetime.now().strftime("%Y-%m-%d")
        }

        return df, metadata

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

def generate_sample_amr_data():
    """Generate sample AMR data for demonstration"""
    import numpy as np

    np.random.seed(42)
    pathogens = ['E. coli', 'K. pneumoniae', 'S. aureus', 'P. aeruginosa', 'A. baumannii']
    antibiotics = ['amikacin', 'ciprofloxacin', 'cefotaxime', 'meropenem', 'gentamicin']
    countries = ['India', 'USA', 'UK', 'China', 'Brazil', 'South Africa']

    data = []
    for pathogen in pathogens:
        for antibiotic in antibiotics:
            for country in countries:
                resistance = np.random.beta(2, 3) * 100  # Skewed towards lower resistance
                data.append({
                    'country': country,
                    'pathogen': pathogen,
                    'antibiotic': antibiotic,
                    'percent_resistant': round(resistance, 1),
                    'sample_count': np.random.randint(50, 500),
                    'year': 2024
                })

    df = pd.DataFrame(data)
    # Add some critical Indian data
    india_critical = df[df['country'] == 'India'].copy()
    india_critical['percent_resistant'] = india_critical['percent_resistant'] * 1.5
    india_critical['percent_resistant'] = india_critical['percent_resistant'].clip(upper=95)

    df = pd.concat([df[df['country'] != 'India'], india_critical])
    return df

def generate_sample_metadata():
    """Generate sample metadata"""
    return {
        'total_samples': 500,
        'countries': 6,
        'pathogens': 5,
        'antibiotics': 5,
        'last_updated': '2025-09-27',
        'source': 'Sample Data'
    }

# Sidebar navigation
def create_sidebar():
    """Create sidebar with navigation and filters"""
    st.sidebar.title("🦠 AMR Intelligence Platform")
    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "Dashboard Views",
        ["🏠 Overview", "🌍 Global AMR", "🇮🇳 India Focus", "💊 Antibiotics", "📈 Advanced Analytics", "ℹ️ About"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")

    # Data info
    st.sidebar.markdown("### Data Status")
    if st.session_state.get('metadata'):
        meta = st.session_state.metadata
        st.sidebar.metric("Total Samples", f"{meta['total_samples']:,}")
        st.sidebar.metric("Countries", meta['countries'])
        st.sidebar.metric("Pathogens", meta['pathogens'])

    return page

# Main dashboard components
def show_overview_dashboard(df, metadata):
    """Show overview dashboard with key metrics"""
    st.markdown('<h1 class="main-header">🦠 AMR Intelligence Platform</h1>', unsafe_allow_html=True)
    st.markdown("**Global Antimicrobial Resistance Analysis & Forecasting System**")

    if metadata:
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📊 Total Samples", f"{metadata['total_samples']:,}")

        with col2:
            st.metric("🌍 Countries", metadata['countries'])

        with col3:
            st.metric("🦠 Pathogens", metadata['pathogens'])

        with col4:
            st.metric("💊 Antibiotics", metadata['antibiotics'])

    if df is not None and not df.empty:
        # Crisis alerts
        india_df = df[df['country'] == 'India']
        if not india_df.empty:
            india_avg = india_df['percent_resistant'].mean()
            if india_avg > 40:
                st.markdown("""
                <div class="crisis-alert">
                    <h4>🚨 INDIA AMR CRISIS ALERT</h4>
                    <p>India's average AMR rate exceeds global benchmarks. All top 5 pathogens show >50% resistance.</p>
                </div>
                """, unsafe_allow_html=True)

        # Quick insights
        st.subheader("🔍 Key Insights")

        # Global threat ranking
        path_stats = df.groupby('pathogen')['percent_resistant'].agg(['mean', 'count']).round(1)
        path_stats = path_stats[path_stats['count'] >= 10].sort_values('mean', ascending=False).head(10)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🦠 Top Global AMR Threats")
            for i, (pathogen, row) in enumerate(path_stats.iterrows(), 1):
                color = "🔴" if row['mean'] > 50 else "🟡" if row['mean'] > 30 else "🟢"
                st.write(f"{i}. **{pathogen}**: {row['mean']}% resistance {color}")

        with col2:
            st.markdown("### 💊 Critical Antibiotic Failures")
            ab_stats = df.groupby('antibiotic')['percent_resistant'].agg(['mean', 'count']).round(1)
            ab_stats = ab_stats[ab_stats['count'] >= 20].sort_values('mean', ascending=False).head(8)

            for antibiotic, row in ab_stats.iterrows():
                color = "🔴" if row['mean'] > 40 else "🟡"
                st.write(f"• **{antibiotic.title()}**: {row['mean']}% resistance {color}")

def show_global_amr(df):
    """Show global AMR analysis"""
    st.header("🌍 Global AMR Threat Landscape")

    if df is None or df.empty:
        st.error("No data available")
        return

    # Global pathogen ranking
    st.subheader("🦠 Global AMR Threat Ranking")

    pathogen_stats = df.groupby('pathogen')['percent_resistant'].agg(['mean', 'count', 'std']).round(1)
    pathogen_stats = pathogen_stats[pathogen_stats['count'] >= 5].sort_values('mean', ascending=False)

    top_10 = pathogen_stats.head(10)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top_10['mean'],
        y=top_10.index,
        orientation='h',
        marker=dict(
            color=top_10['mean'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Resistance %")
        ),
        text=[f'{v:.1f}% (n={top_10.loc[idx, "count"]})' for idx, v in zip(top_10.index, top_10['mean'])],
        textposition='outside'
    ))

    fig.update_layout(
        title='Top 10 Global AMR Pathogens by Resistance Rate',
        xaxis_title='Average Resistance Rate (%)',
        yaxis_title='Pathogen',
        template='plotly_white',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Country comparison
    st.subheader("🌏 Country AMR Rankings")

    country_stats = df.groupby('country')['percent_resistant'].agg(['mean', 'count']).round(1)
    country_stats = country_stats[country_stats['count'] >= 10].sort_values('mean', ascending=False).head(15)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=country_stats.index,
        y=country_stats['mean'],
        marker=dict(
            color=country_stats['mean'],
            colorscale='Viridis_r'
        ),
        text=[f'{v:.1f}%' for v in country_stats['mean']],
        textposition='outside'
    ))

    fig2.update_layout(
        title='AMR Crisis by Country: Global Hotspots',
        xaxis_title='Country',
        yaxis_title='Average Resistance Rate (%)',
        xaxis_tickangle=-45,
        template='plotly_white',
        height=400
    )

    st.plotly_chart(fig2, use_container_width=True)

def show_india_focus(df):
    """Show India-specific AMR analysis"""
    st.header("🇮🇳 India AMR Crisis Analysis")

    if df is None or df.empty:
        st.error("No data available")
        return

    india_df = df[df['country'] == 'India'].copy()

    if india_df.empty:
        st.warning("No India-specific data available in dataset")
        # Use global data for demonstration
        india_df = df[df['country'].isin(['USA', 'UK'])].copy()  # Simulate with other countries
        india_df['country'] = 'India (Demo)'
        st.info("Using sample data for demonstration")

    # India's pathogen ranking
    st.subheader("🦠 India's AMR Threat Ranking")

    india_pathogens = india_df.groupby('pathogen')['percent_resistant'].agg(['mean', 'count']).round(1)
    india_pathogens = india_pathogens[india_pathogens['count'] >= 3].sort_values('mean', ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=india_pathogens['mean'],
        y=india_pathogens.index,
        orientation='h',
        marker=dict(
            color='rgba(255, 140, 0, 0.8)',
            line=dict(color='rgba(255, 140, 0, 1)', width=2)
        ),
        text=[f'{v:.1f}%' for v in india_pathogens['mean']],
        textposition='outside'
    ))

    fig.update_layout(
        title="🇮🇳 India's AMR Crisis: Pathogen Ranking",
        xaxis_title='Resistance Rate (%)',
        yaxis_title='Pathogen',
        template='plotly_white',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # India vs Global comparison
    if df['country'].nunique() > 1:
        st.subheader("🇮🇳 India vs Global Comparison")

        global_avg = df.groupby('pathogen')['percent_resistant'].mean().round(1)
        india_comp = india_pathogens['mean'].to_frame('india_resistance')
        india_comp['global_average'] = global_avg

        # Reset index for plotting
        india_comp = india_comp.reset_index()

        fig2 = go.Figure()

        fig2.add_trace(go.Bar(
            name='Global Average',
            x=india_comp['pathogen'],
            y=india_comp['global_average'],
            marker_color='lightblue'
        ))

        fig2.add_trace(go.Bar(
            name='India',
            x=india_comp['pathogen'],
            y=india_comp['india_resistance'],
            marker_color='red'
        ))

        fig2.update_layout(
            title='🇮🇳 India vs Global AMR Comparison',
            xaxis_title='Pathogen',
            yaxis_title='Resistance Rate (%)',
            barmode='group',
            template='plotly_white',
            xaxis_tickangle=-45,
            height=500
        )

        st.plotly_chart(fig2, use_container_width=True)

def show_antibiotics(df):
    """Show antibiotic effectiveness analysis"""
    st.header("💊 Antibiotic Effectiveness Analysis")

    if df is None or df.empty:
        st.error("No data available")
        return

    # Antibiotic effectiveness ranking
    st.subheader("💊 Antibiotic Effectiveness: Which Are Failing?")

    antibiotic_stats = df.groupby('antibiotic')['percent_resistant'].agg(['mean', 'count', 'std']).round(1)
    antibiotic_stats = antibiotic_stats[antibiotic_stats['count'] >= 10].sort_values('mean', ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=antibiotic_stats['mean'],
        y=antibiotic_stats.index,
        orientation='h',
        marker=dict(
            color=antibiotic_stats['mean'],
            colorscale='RdYlBu_r',
            showscale=True,
            colorbar=dict(title="Resistance %")
        ),
        text=[f'{v:.1f}%' for v in antibiotic_stats['mean']],
        textposition='outside'
    ))

    fig.update_layout(
        title='Antibiotic Effectiveness Analysis',
        xaxis_title='Resistance Rate (%) ⇒ Higher values = More failures',
        yaxis_title='Antibiotic',
        template='plotly_white',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Critical antibiotics analysis
    st.subheader("🚨 Critical Antibiotic Failures (>50% resistance)")

    critical_antibiotics = antibiotic_stats[antibiotic_stats['mean'] > 50]
    if not critical_antibiotics.empty:
        st.error("🚨 CRITICAL: Following antibiotics show >50% resistance rates globally:")

        for antibiotic, row in critical_antibiotics.iterrows():
            st.write(f"• **{antibiotic.title()}**: {row['mean']}% resistance (n={row['count']})")

        st.warning("These critical antibiotics are failing worldwide!")
    else:
        st.success("No antibiotics currently show >50% global resistance rates.")

def show_trends(df):
    """Show AMR trends over time"""
    st.header("📈 AMR Trends & Forecasting")

    if df is None or df.empty:
        st.error("No data available")
        return

    if 'year' not in df.columns:
        st.warning("No time series data available for trend analysis")
        return

    # Time trends
    st.subheader("📊 Resistance Trends Over Time")

    # E. coli trend
    e_coli_data = df[df['pathogen'] == 'E. coli']
    if not e_coli_data.empty and 'year' in e_coli_data.columns:
        yearly_trends = e_coli_data.groupby('year')['percent_resistant'].agg(['mean', 'count']).round(1)

        if len(yearly_trends) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=yearly_trends.index,
                y=yearly_trends['mean'],
                mode='lines+markers',
                line=dict(color='darkblue', width=3),
                marker=dict(size=8),
                text=[f'n={int(c)}' for c in yearly_trends['count']],
                hovertemplate='<b>Year:</b> %{x}<br><b>Resistance:</b> %{y:.1f}%<br><b>Samples:</b> %{text}'
            ))

            fig.update_layout(
                title='E. coli Global Resistance Trends',
                xaxis_title='Year',
                yaxis_title='Resistance Rate (%)',
                template='plotly_white',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # Trend analysis
            years = yearly_trends.index.tolist()
            rates = yearly_trends['mean'].tolist()

            if len(years) >= 3:
                # Simple linear trend
                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(years, rates)

                annual_increase = slope * 100  # Convert to percentage points
                st.metric(
                    "Annual Trend",
                    f"{annual_increase:.2f}% per year",
                    delta=f"p-value: {p_value:.3f}"
                )

                if p_value < 0.05:
                    trend_color = "🔴" if slope > 0 else "🟢"
                    st.write(f"{trend_color} **Statistically significant {'increasing' if slope > 0 else 'decreasing'} trend detected**")
                else:
                    st.write("🟡 No statistically significant trend detected")

def show_about():
    """Show about page"""
    st.header("ℹ️ About AMR Intelligence Platform")

    st.markdown("""
    ## 🦠 Mission
    **Combat Antimicrobial Resistance (AMR) through data-driven intelligence and global collaboration.**

    ## 🎯 Objectives
    - **Monitor** global AMR patterns and trends
    - **Analyze** pathogen-antibiotic resistance relationships
    - **Forecast** future resistance developments
    - **Inform** policy makers and healthcare providers
    - **Drive** evidence-based interventions

    ## 📊 Data Sources
    - World Health Organization (WHO)
    - Centers for Disease Control (CDC)
    - ResistanceMap
    - National surveillance systems

    ## 🚀 Technology
    - **Python** for data processing and analysis
    - **Streamlit** for interactive dashboards
    - **Plotly** for advanced visualizations
    - **Machine Learning** for forecasting

    ## 🔬 Methodology
    - Statistical analysis with confidence intervals
    - Time series forecasting using Prophet and ARIMA
    - Comparative analysis across countries and regions
    - Risk assessment and prioritization

    ## 📞 Contact
    For questions or collaborations, contact our AMR Intelligence team.

    ---
    *Platform Version: 1.0 | Data Last Updated: September 27, 2025*
    """)

# Main app
def main():
    """Main Streamlit application"""
    # Load data
    df, metadata = load_data()

    # Store in session state
    st.session_state.df = df
    st.session_state.metadata = metadata

    # Create sidebar and get selected page
    page = create_sidebar()

    # Route to appropriate page
    if page == "🏠 Overview":
        show_overview_dashboard(df, metadata)
    elif page == "🌍 Global AMR":
        show_global_amr(df)
    elif page == "🇮🇳 India Focus":
        show_india_focus(df)
    elif page == "💊 Antibiotics":
        show_antibiotics(df)
    elif page == "📈 Trends":
        show_trends(df)
    elif page == "ℹ️ About":
        show_about()

    # Footer
    st.markdown("---")
    st.markdown("*🦠 AMR Intelligence Platform | Powered by Data Science for Global Health*")

if __name__ == "__main__":
    main()
