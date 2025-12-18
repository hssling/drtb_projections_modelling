"""
Create Synthetic State-Level TB Epidemiological Data for Framework Demonstration

This script generates realistic synthetic TB case data to demonstrate the climate-TB
correlation analysis framework capabilities. The data follows realistic patterns
based on known Indian TB epidemiology but is clearly marked as synthetic.

WARNING: This is DEMONSTRATION data only - not for research or policy use.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def create_synthetic_tb_data():
    """
    Create synthetic state-level TB epidemiological data for 18 Indian states.
    """

    # Define the 18 analyzed states
    states = [
        'Maharashtra', 'Gujarat', 'Karnataka', 'Rajasthan', 'Tamil Nadu',
        'Uttar Pradesh', 'Madhya Pradesh', 'West Bengal', 'Andhra Pradesh',
        'Telangana', 'Delhi', 'Punjab', 'Haryana', 'Bihar', 'Odisha',
        'Jharkhand', 'Kerala', 'Assam'
    ]

    # Time period (2017-2023)
    start_date = pd.Timestamp('2017-01-01')
    end_date = pd.Timestamp('2023-12-01')
    date_range = pd.date_range(start_date, end_date, freq='MS')

    # State population estimates (approximate, in millions)
    state_populations = {
        'Maharashtra': 125.0, 'Gujarat': 70.0, 'Karnataka': 68.0, 'Rajasthan': 81.0,
        'Tamil Nadu': 78.0, 'Uttar Pradesh': 240.0, 'Madhya Pradesh': 85.0,
        'West Bengal': 100.0, 'Andhra Pradesh': 53.0, 'Telangana': 39.0,
        'Delhi': 18.0, 'Punjab': 30.0, 'Haryana': 30.0, 'Bihar': 125.0,
        'Odisha': 46.0, 'Jharkhand': 40.0, 'Kerala': 36.0, 'Assam': 35.0
    }

    # TB incidence rates per 100,000 population (approximate ranges)
    # These are based on Indian national patterns but with state variations
    state_tb_rates = {
        'Maharashtra': 180, 'Gujarat': 165, 'Karnataka': 175, 'Rajasthan': 195,
        'Tamil Nadu': 170, 'Uttar Pradesh': 220, 'Madhya Pradesh': 210,
        'West Bengal': 190, 'Andhra Pradesh': 185, 'Telangana': 180,
        'Delhi': 150, 'Punjab': 160, 'Haryana': 155, 'Bihar': 230,
        'Odisha': 200, 'Jharkhand': 225, 'Kerala': 120, 'Assam': 205
    }

    # MDR rates as percentage of TB cases (higher in certain states)
    state_mdr_rates = {
        'Maharashtra': 8.5, 'Gujarat': 7.2, 'Karnataka': 9.1, 'Rajasthan': 10.5,
        'Tamil Nadu': 6.8, 'Uttar Pradesh': 12.2, 'Madhya Pradesh': 11.8,
        'West Bengal': 9.8, 'Andhra Pradesh': 8.9, 'Telangana': 8.6,
        'Delhi': 5.5, 'Punjab': 6.2, 'Haryana': 5.8, 'Bihar': 13.5,
        'Odisha': 11.2, 'Jharkhand': 12.8, 'Kerala': 4.2, 'Assam': 11.6
    }

    # Seasonal variation (TB cases higher in winter, lower in summer)
    monthly_multipliers = {
        1: 1.05, 2: 0.95, 3: 0.85, 4: 0.75, 5: 0.70, 6: 0.75,
        7: 0.85, 8: 0.95, 9: 1.10, 10: 1.15, 11: 1.20, 12: 1.15
    }

    synthetic_data = []

    for date in date_range:
        year = date.year
        month = date.month

        for state in states:
            # Base population for state
            population = state_populations[state] * 1e6  # Convert to actual population

            # Base TB cases per month
            tb_incidence_rate = state_tb_rates[state] / 12000  # Convert to monthly rate
            base_new_cases = int(population * tb_incidence_rate * monthly_multipliers[month])

            # Retreated cases (typically 10-15% of notified cases)
            retreated_cases = int(base_new_cases * np.random.uniform(0.10, 0.15))

            # MDR cases (rifampicin-resistant cases)
            mdr_rate = state_mdr_rates[state] / 100
            rif_resistant_new = int(base_new_cases * mdr_rate * np.random.uniform(0.9, 1.1))
            rif_resistant_retreated = int(retreated_cases * mdr_rate * np.random.uniform(0.9, 1.1))

            # Add some random variation
            base_new_cases = int(base_new_cases * np.random.uniform(0.9, 1.1))
            retreated_cases = int(retreated_cases * np.random.uniform(0.9, 1.1))

            record = {
                'year': year,
                'month': month,
                'date': date.strftime('%Y-%m-%d'),
                'state_name': state,
                'cases_new': base_new_cases,
                'cases_retreated': retreated_cases,
                'rifampicin_resistant_new': rif_resistant_new,
                'rifampicin_resistant_retreated': rif_resistant_retreated,
                'data_type': 'synthetic_demo',
                'note': 'Synthetic data for framework demonstration only'
            }

            synthetic_data.append(record)

    # Create DataFrame
    df = pd.DataFrame(synthetic_data)

    # Sort by state and date
    df = df.sort_values(['state_name', 'date']).reset_index(drop=True)

    return df

def main():
    """Create and save synthetic TB epidemiological data."""
    print("🧪 CREATING SYNTHETIC TB EPIDEMIOLOGICAL DATA FOR FRAMEWORK DEMONSTRATION")

    # Create synthetic data
    synthetic_tb_data = create_synthetic_tb_data()

    # Save to CSV
    output_file = Path('data') / 'synthetic_state_tb_data_demo.csv'
    synthetic_tb_data.to_csv(output_file, index=False)

    # Summary statistics
    print("✅ Synthetic TB data created:")
    print(f"   • Total records: {len(synthetic_tb_data)}")
    print(f"   • States covered: {synthetic_tb_data['state_name'].nunique()}")
    print(f"   • Time period: {synthetic_tb_data['year'].min()} - {synthetic_tb_data['year'].max()}")
    print(f"   • Saved to: {output_file}")

    print("\n📊 Synthetic Data Summary:")

    # State-wise totals
    state_summary = synthetic_tb_data.groupby('state_name').agg({
        'cases_new': 'sum',
        'cases_retreated': 'sum',
        'rifampicin_resistant_new': 'sum',
        'rifampicin_resistant_retreated': 'sum'
    }).round(0)

    state_summary['total_tb_cases'] = state_summary['cases_new'] + state_summary['cases_retreated']
    state_summary['total_mdr_cases'] = state_summary['rifampicin_resistant_new'] + state_summary['rifampicin_resistant_retreated']
    state_summary['mdr_rate_pct'] = (state_summary['total_mdr_cases'] / state_summary['total_tb_cases'] * 100).round(1)

    print("\nState-wise Summary (2017-2023):")
    print(state_summary[['total_tb_cases', 'total_mdr_cases', 'mdr_rate_pct']].head(10))

    print("\n⚠️  IMPORTANT: This is SYNTHETIC demonstration data only.")
    print("   - NOT suitable for research or policy decisions")
    print("   - Used only to demonstrate the analytical framework")
    print("   - Real epidemiological data required for actual analysis")

if __name__ == "__main__":
    main()
