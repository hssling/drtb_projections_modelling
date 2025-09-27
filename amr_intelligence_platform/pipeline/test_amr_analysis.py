#!/usr/bin/env python3
"""
Test AMR Analysis Script - Simple Working Version
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def main():
    print("🧬 TESTING AMR ANALYSIS PIPELINE")

    try:
        # Load data
        data_path = "data/amr_merged.csv"
        if Path(data_path).exists():
            df = pd.read_csv(data_path)
            print(f"✅ Loaded {len(df)} AMR records")

            # Basic analysis
            pathogen_stats = df.groupby('pathogen')['percent_resistant'].agg(['mean', 'count']).round(2)
            pathogen_stats = pathogen_stats.sort_values('mean', ascending=False)
            print("\n🦠 TOP AMR THREATS:")
            print(pathogen_stats.head())

            # India analysis
            india_df = df[df['country'] == 'India']
            if not india_df.empty:
                india_stats = india_df.groupby('pathogen')['percent_resistant'].mean().round(2).sort_values(ascending=False)
                print("\n🇮🇳 INDIA AMR TOP THREATS:")
                print(india_stats.head())

            # Create simple visualization
            fig, ax = plt.subplots(figsize=(10, 6))
            pathogen_stats.head(5)['mean'].plot(kind='bar', ax=ax)
            ax.set_title('Top 5 Global AMR Threats', fontsize=16, fontweight='bold')
            ax.set_ylabel('Average Resistance Rate (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('pipeline/plots/test_global_amr.png', dpi=150)
            plt.close()

            print("✅ Plot saved: pipeline/plots/test_global_amr.png")
            return True
        else:
            print("❌ Data file not found")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_forecasts():
    """Test basic forecasting functionality"""
    print("\n🔮 TESTING FORECASTING")

    try:
        df = pd.read_csv("data/amr_merged.csv")

        # Simple forecast for E. coli
        e_coli_data = df[df['pathogen'] == 'E. coli']
        if not e_coli_data.empty:
            # Convert date and create year column
            e_coli_data['date'] = pd.to_datetime(e_coli_data['date'])
            e_coli_data['year'] = e_coli_data['date'].dt.year
            yearly_avg = e_coli_data.groupby('year')['percent_resistant'].mean()

            if len(yearly_avg) > 2:
                # Linear trend
                years = yearly_avg.index.values
                values = yearly_avg.values

                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)

                print(f"E. coli trend: {slope:.2f}% per year (p={p_value:.3f})")
                print(".0f")
                return True

        return False
    except Exception as e:
        print(f"❌ Forecast error: {e}")
        return False

if __name__ == "__main__":
    success1 = main()
    success2 = test_forecasts()

    if success1:
        print("\n🎉 AMR Analysis Pipeline BASIC VERSION WORKING!")
        print("📊 Now build World + India dashboards using these results")
    else:
        print("\n❌ Issues with basic analysis")
