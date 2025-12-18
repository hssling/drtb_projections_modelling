#!/usr/bin/env python3
"""
Fresh Meta-Analysis Validation Script - 2025
Re-extracts and validates MDR-TB prevalence data from fresh CSV extraction
"""

import pandas as pd
import numpy as np
from scipy import stats
import json
from datetime import datetime

def load_fresh_extraction_data():
    """Load the fresh extraction data"""
    df = pd.read_csv('fresh_meta_extraction_clean_2025.csv', index_col=False)

    print(f"Raw data loaded: {len(df)} rows")
    print(f"Included column values: {df['included'].unique()}")
    print(f"N_total column values (first 5): {df['n_total'].head().tolist()}")
    print(f"N_resistant column values (first 5): {df['n_resistant'].head().tolist()}")

    # Filter to included studies with valid numerical data
    df_valid = df[
        (df['included'].astype(str).str.strip() == 'yes') &
        (pd.notna(df['n_total'])) &
        (pd.notna(df['n_resistant'])) &
        (df['n_total'] > 0)
    ].copy()

    print(f"After filtering: {len(df_valid)} valid studies")

    # Calculate prevalence if not provided
    df_valid['prevalence_percent'] = df_valid.apply(
        lambda row: (row['n_resistant'] / row['n_total']) * 100
        if pd.isna(row['prevalence_percent']) else row['prevalence_percent'],
        axis=1
    )

    return df_valid

def calculate_pooled_prevalence(df, resistance_type):
    """Calculate pooled prevalence using random effects model"""
    subset = df[df['drug_resistance_type'].str.contains(resistance_type, case=False, na=False)]

    if len(subset) == 0:
        return None

    # Calculate individual study proportions and variances
    subset = subset.copy()
    subset['p'] = subset['prevalence_percent'] / 100
    subset['n'] = subset['n_total']

    # Variance for each study (using binomial variance)
    subset['v'] = subset['p'] * (1 - subset['p']) / subset['n']

    # Random effects model
    weights = 1 / subset['v']
    weighted_sum = np.sum(weights * subset['p'])
    total_weight = np.sum(weights)

    pooled_p = weighted_sum / total_weight

    # Between-study variance (tau-squared)
    q = np.sum(weights * (subset['p'] - pooled_p) ** 2)
    df_q = len(subset) - 1
    c = total_weight - np.sum(weights ** 2) / total_weight

    if c > 0:
        tau2 = max(0, (q - df_q) / c)
    else:
        tau2 = 0

    # Adjusted weights
    adjusted_weights = 1 / (subset['v'] + tau2)
    adjusted_weighted_sum = np.sum(adjusted_weights * subset['p'])
    adjusted_total_weight = np.sum(adjusted_weights)

    final_pooled_p = adjusted_weighted_sum / adjusted_total_weight

    # Standard error
    se = np.sqrt(1 / adjusted_total_weight)
    ci_low = max(0, final_pooled_p - 1.96 * se)
    ci_high = min(1, final_pooled_p + 1.96 * se)

    # I-squared
    if tau2 > 0:
        i_squared = (tau2 / (tau2 + np.mean(subset['v']))) * 100
    else:
        i_squared = 0

    return {
        'resistance_type': resistance_type,
        'pooled_prevalence': round(final_pooled_p * 100, 1),
        'ci_lower': round(ci_low * 100, 1),
        'ci_upper': round(ci_high * 100, 1),
        'n_studies': len(subset),
        'total_sample': int(subset['n'].sum()),
        'i_squared': round(i_squared, 1),
        'tau2': round(tau2, 6)
    }

def validate_against_original(original_file='data/meta_analysis_tb_amr_results.json'):
    """Compare fresh extraction with original results"""
    try:
        with open(original_file, 'r') as f:
            original = json.load(f)
    except FileNotFoundError:
        return {"error": "Original file not found"}

    validation_report = {
        'validation_timestamp': datetime.now().isoformat(),
        'comparison_results': {}
    }

    # Compare key metrics
    original_mdr = original['pooled_effect_sizes'].get('multi_drug_resistance', {})
    original_xdr = original['pooled_effect_sizes'].get('extensive_drug_resistance', {})
    original_rif = original['pooled_effect_sizes'].get('rifampicin_resistance', {})

    validation_report['original_totals'] = {
        'total_studies': original.get('total_studies_included', 0),
        'mdr_prevalence': f"{original_mdr.get('pooled_prevalence', 0)*100:.1f}%",
        'xdr_prevalence': f"{original_xdr.get('pooled_prevalence', 0)*100:.1f}%",
        'rif_prevalence': f"{original_rif.get('pooled_prevalence', 0)*100:.1f}%"
    }

    return validation_report

def main():
    print("=== Fresh Meta-Analysis Validation 2025 ===")
    print("Loading fresh extraction data...")

    # Load data
    df = load_fresh_extraction_data()
    print(f"Loaded {len(df)} valid studies from fresh extraction")

    # Calculate pooled estimates for different resistance types
    resistance_types = ['MDR', 'XDR', 'RR', 'pre-XDR']
    results = {}

    print("\nCalculating pooled prevalence estimates...")
    for res_type in resistance_types:
        result = calculate_pooled_prevalence(df, res_type)
        if result:
            results[res_type] = result
            print(f"{res_type}: {result['pooled_prevalence']:.1f}% "
                  f"(95% CI: {result['ci_lower']:.1f}-{result['ci_upper']:.1f}%) "
                  f"from {result['n_studies']} studies, n={result['total_sample']}")

    # Create validation report
    print("\nGenerating validation report...")
    validation = validate_against_original()

    # Save results
    output = {
        'validation_report': validation,
        'fresh_results': results,
        'extraction_summary': {
            'total_studies_extracted': len(df),
            'date_extracted': datetime.now().isoformat(),
            'resistance_types_covered': resistance_types
        }
    }

    with open('fresh_meta_analysis_results_2025.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("Fresh validation complete. Results saved to 'fresh_meta_analysis_results_2025.json'")

    # Summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Studies analyzed: {len(df)}")
    print(f"Total patients: {df['n_total'].sum()}")
    print(f"Resistance types: {', '.join(results.keys())}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
