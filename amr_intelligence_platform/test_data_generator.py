#!/usr/bin/env python3
"""
Test Data Generator for AMR Batch Runner

Creates sample AMR data for testing the batch runner functionality.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_test_data():
    """Generate synthetic AMR test data."""
    print("Generating test AMR data...")

    np.random.seed(42)
    random.seed(42)

    countries = ["India", "United States", "Brazil", "South Africa", "Vietnam", "Cambodia"]
    pathogens = ["E. coli", "Klebsiella pneumoniae", "Salmonella", "Staphylococcus aureus", "Pseudomonas aeruginosa"]
    antibiotics = ["Ciprofloxacin", "Meropenem", "Gentamicin", "Tetracycline", "Amoxicillin"]

    data = []

    # Generate data from 2018 to 2024
    start_date = datetime(2018, 1, 1)
    end_date = datetime(2024, 12, 31)

    for country in countries:
        for pathogen in pathogens:
            for antibiotic in antibiotics:
                # Skip some combinations randomly
                if random.random() < 0.3:  # 30% chance to skip
                    continue

                # Generate 15-30 data points for each combination
                num_points = random.randint(15, 30)

                # Create time series
                dates = []
                base_date = start_date
                for i in range(num_points):
                    # Add 1-3 months between measurements
                    months_add = random.randint(1, 3)
                    base_date = base_date + timedelta(days=months_add * 30)
                    if base_date > end_date:
                        break
                    dates.append(base_date)

                # Generate resistance trends with some noise
                base_resistance = random.uniform(20, 60)  # Start between 20-60%
                trend_direction = random.choice([-1, 0, 1])  # Decrease, stable, or increase

                for i, measurement_date in enumerate(dates):
                    # Add trend + random noise
                    trend_effect = i * trend_direction * random.uniform(0.5, 2.0)
                    noise = random.uniform(-15, 15)
                    resistance_pct = base_resistance + trend_effect + noise

                    # Keep in realistic bounds
                    resistance_pct = max(5, min(95, resistance_pct))

                    # Calculate tested and resistant (assume 50-200 tests per sample)
                    tested = random.randint(50, 200)
                    resistant = int((resistance_pct / 100) * tested)

                    # Add record
                    data.append({
                        'date': measurement_date.strftime('%Y-%m-%d'),
                        'country': country,
                        'pathogen': pathogen,
                        'antibiotic': antibiotic,
                        'percent_resistant': round(resistance_pct, 1),
                        'resistant': resistant,
                        'tested': tested,
                        'source': 'Synthesized_Test_Data'
                    })

    # Create DataFrame and sort
    df = pd.DataFrame(data)
    df = df.sort_values(['country', 'pathogen', 'antibiotic', 'date'])

    # Save to CSV
    output_file = "data/amr_test_data.csv"
    df.to_csv(output_file, index=False)

    print(f"✅ Generated {len(df)} test records across {len(countries)} countries")
    print(f"   Unique combinations: {len(df.groupby(['country', 'pathogen', 'antibiotic']).size())}")
    print(f"   Saved to: {output_file}")

    return df

if __name__ == "__main__":
    generate_test_data()
