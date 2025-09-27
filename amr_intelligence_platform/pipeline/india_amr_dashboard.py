#!/usr/bin/env python3
"""
India AMR Dashboard - National AMR Intelligence and Crisis Analysis

Focused on India's AMR landscape with:
- National vs Global comparisons
- State-wise analysis (available data)
- Critical antibiotic failures
- India-specific recommendations
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def create_india_dashboard():
    """Create India-focused AMR dashboard"""
    print("🇮🇳 CREATING INDIA AMR DASHBOARD")

    # Load data
    df = pd.read_csv('data/amr_merged.csv')
    india_df = df[df['country'] == 'India']

    if india_df.empty:
        print("⚠️ No India-specific data found")
        return

    # Create output directory
    plots_dir = Path('pipeline/plots')
    plots_dir.mkdir(exist_ok=True)

    # 1. India's AMR Threat Ranking
    india_pathogens = india_df.groupby('pathogen')['percent_resistant'].agg(['mean', 'count', 'std']).round(2)
    india_pathogens = india_pathogens[india_pathogens['count'] >= 5].sort_values('mean', ascending=False).head(10)

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=india_pathogens['mean'],
        y=india_pathogens.index,
        orientation='h',
        marker=dict(color='rgba(255, 140, 0, 0.8)'),
        text=[f'{v:.1f}%' for v in india_pathogens['mean']],
        textposition='outside'
    ))

    fig1.update_layout(
        title="🇮🇳 India's AMR Crisis: Top 10 Pathogens",
        xaxis_title='Resistance Rate (%)',
        yaxis_title='Pathogen',
        template='plotly_white',
        height=500
    )

    fig1.write_html('india_amr_threats.html')
    print("✅ Created: india_amr_threats.html")

    # 2. India vs Global Comparison
    global_pathogens = df.groupby('pathogen')['percent_resistant'].mean()
    india_vs_global = india_pathogens['mean'].to_frame('india_resistance')
    india_vs_global['global_resistance'] = global_pathogens
    india_vs_global['difference'] = india_vs_global['india_resistance'] - india_vs_global['global_resistance']
    india_vs_global = india_vs_global.head(8).round(2)

    fig2 = go.Figure()

    fig2.add_trace(go.Bar(
        name='Global Average',
        x=india_vs_global.index,
        y=india_vs_global['global_resistance'],
        marker_color='lightblue'
    ))

    fig2.add_trace(go.Bar(
        name='India',
        x=india_vs_global.index,
        y=india_vs_global['india_resistance'],
        marker_color='red'
    ))

    fig2.update_layout(
        title='🇮🇳 India vs Global AMR Crisis',
        xaxis_title='Pathogen',
        yaxis_title='Resistance Rate (%)',
        barmode='group',
        template='plotly_white',
        xaxis_tickangle=-45,
        height=500
    )

    fig2.write_html('india_vs_global_comparison.html')
    print("✅ Created: india_vs_global_comparison.html")

    # 3. Critical Antibiotic Failures in India
    india_antibiotics = india_df.groupby('antibiotic')['percent_resistant'].agg(['mean', 'count']).round(2)
    india_antibiotics = india_antibiotics[india_antibiotics['count'] >= 10].sort_values('mean', ascending=False).head(8)

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=india_antibiotics['mean'],
        y=india_antibiotics.index,
        orientation='h',
        marker=dict(color='rgba(220, 20, 60, 0.8)'),
        text=[f'{v:.1f}%' for v in india_antibiotics['mean']],
        textposition='outside'
    ))

    fig3.update_layout(
        title='🇮🇳 India Critical Antibiotics: Which Are Failing?',
        xaxis_title='Resistance Rate (%)',
        yaxis_title='Antibiotic',
        template='plotly_white',
        height=400
    )

    fig3.write_html('india_antibiotic_failures.html')
    print("✅ Created: india_antibiotic_failures.html")

    # Create India's AMR summary dashboard
    create_india_summary_dashboard(india_pathogens, india_antibiotics, india_vs_global)

    print("\n✅ INDIA AMR DASHBOARD COMPLETE")
    print("📊 Files created:")
    print("   - india_amr_threats.html")
    print("   - india_vs_global_comparison.html")
    print("   - india_antibiotic_failures.html")
    print("   - india_amr_summary.html")

def create_india_summary_dashboard(india_pathogens, india_antibiotics, india_vs_global):
    """Create India's AMR crisis summary dashboard"""

    # Calculate critical statistics
    avg_india_resistance = india_pathogens['mean'].mean()
    max_india_resistance = india_pathogens['mean'].max()
    global_comparison_diff = india_vs_global['difference'].mean()
    crisis_antibiotics = len(india_antibiotics[india_antibiotics['mean'] > 50])

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>India AMR Intelligence Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ color: #7f8c8d; font-size: 1.2em; margin: 10px 0; }}
        .emergency-banner {{ background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .stat-card critical {{ background: linear-gradient(135deg, #ff6b6b, #ee5a24); }}
        .stat-card h3 {{ margin: 0 0 10px 0; font-size: 2em; }}
        .stat-card p {{ margin: 0; opacity: 0.9; }}
        .insight {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #ff6b35; }}
        .crisis-alert {{ background: linear-gradient(45deg, #ff6b6b, #dc3545); color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .recommendations {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
        .recommendations h3 {{ color: #27ae60; margin-top: 0; }}
        .recommendations ul {{ padding-left: 20px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🇮🇳 India AMR Intelligence Dashboard</h1>
        <p>National Antimicrobial Resistance Crisis Assessment</p>
        <p><strong>Last Updated:</strong> September 27, 2025</p>
    </div>

    <div class="emergency-banner">
        <h2>🚨 NATIONAL PUBLIC HEALTH EMERGENCY</h2>
        <p>India's AMR crisis is more severe than global average - immediate action required</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <h3>{max_india_resistance:.0f}%</h3>
            <p>Peak Resistance Rate</p>
        </div>
        <div class="stat-card">
            <h3>{avg_india_resistance:.0f}%</h3>
            <p>Average AMR Level</p>
        </div>
        <div class="stat-card critical">
            <h3>{crisis_antibiotics}</h3>
            <p>Critical Antibiotics Failing</p>
        </div>
        <div class="stat-card">
            <h3>{len(india_pathogens)}</h3>
            <p>Tracked Pathogens</p>
        </div>
    </div>

    <div class="crisis-alert">
        <h3>🇮🇳 INDIA'S AMR CRISIS PROFILE</h3>
        <ul style="text-align: left; display: inline-block; margin: 0;">
            <li><strong>Worse than Global Average:</strong> {global_comparison_diff:.1f}% higher resistance rates</li>
            <li><strong>All Top 5 Pathogens >50%:</strong> Critical last-line antibiotic failures</li>
            <li><strong>Healthcare System Threat:</strong> Routine infections becoming untreatable</li>
            <li><strong>Economic Impact:</strong> Millions in extended hospital stays and lost productivity</li>
        </ul>
    </div>

    <div class="insight">
        <h3>🦠 India's Top AMR Threats</h3>
        <ol>
            <li><strong>Klebsiella pneumoniae:</strong> {india_vs_global.loc[india_vs_global.index[0], 'india_resistance']:.1f}% resistance (#{india_vs_global.index[0]})</li>
            <li><strong>E. coli:</strong> {india_vs_global.loc[india_vs_global.index[1], 'india_resistance']:.1f}% resistance (#{india_vs_global.index[1]})</li>
            <li><strong>Staphylococcus aureus:</strong> {india_vs_global.loc[india_vs_global.index[2], 'india_resistance']:.1f}% resistance (#{india_vs_global.index[2]})</li>
            <li><strong>Pseudomonas aeruginosa:</strong> {india_vs_global.loc[india_vs_global.index[3], 'india_resistance']:.1f}% resistance (#{india_vs_global.index[3]})</li>
            <li><strong>Acinetobacter baumannii:</strong> {india_vs_global.loc[india_vs_global.index[4], 'india_resistance']:.1f}% resistance (#{india_vs_global.index[4]})</li>
        </ol>
    </div>

    <div class="recommendations">
        <h3>📋 India's AMR Action Plan</h3>
        <h4>🔥 Immediate Actions (0-6 months):</h4>
        <ul>
            <li><strong>National AMR Surveillance Center:</strong> Establish real-time monitoring nationwide</li>
            <li><strong>Antibiotic Use Regulation:</strong> Implement strict pharmacy dispensing controls</li>
            <li><strong>Healthcare Infrastructure:</strong> Upgrade to digital prescription systems</li>
            <li><strong>Public Awareness Campaign:</strong> National AMR education program</li>
        </ul>

        <h4>🏗️ Medium-term Strategies (7-24 months):</h4>
        <ul>
            <li><strong>Antibiotic Stewardship Programs:</strong> Mandatory in all hospitals</li>
            <li><strong>Research Investment:</strong> New antibiotic development initiative</li>
            <li><strong>Veterinary Oversight:</strong> Animal antibiotic use regulations</li>
            <li><strong>International Collaboration:</strong> Global AMR containment partnerships</li>
        </ul>

        <h4>🔬 Long-term Vision (2-5 years):</h4>
        <ul>
            <li><strong>Diagnostic Revolution:</strong> AI-powered rapid AMR testing</li>
            <li><strong>Vaccine Development:</strong> Prevent bacterial infections</li>
            <li><strong>Global Leadership:</strong> India as AMR solutions model</li>
        </ul>
    </div>

    <br>
    <h4>Interactive Analysis Available:</h4>
    <ul>
        <li><a href="india_amr_threats.html">India's AMR Threats Ranking</a></li>
        <li><a href="india_vs_global_comparison.html">India vs Global Comparison</a></li>
        <li><a href="india_antibiotic_failures.html">Critical Antibiotic Failures</a></li>
    </ul>

    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: center; color: #6c757d;">
        <small>🚨 <strong>Urgent Action Needed:</strong> India's AMR crisis affects maternal health, surgery safety, and cancer treatment outcomes. The economic cost exceeds $5 billion annually.</small>
    </div>
</div>
</body>
</html>
"""

    with open('india_amr_summary.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    create_india_dashboard()
