#!/usr/bin/env python3
"""
AMR Data Preprocessing - Clean and validate AMR datasets

This script cleans, validates, and prepares AMR datasets for forecasting models.
Handles missing values, date formatting, outlier detection, and data quality checks.

Usage:
    python preprocess.py

Outputs:
    - Cleaned and validated CSV suitable for forecasting
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def validate_amr_data(df):
    """Validate AMR dataset structure and quality."""
    required_columns = ['date', 'pathogen', 'antibiotic', 'resistant', 'tested', 'percent_resistant']
    optional_columns = ['ddd', 'hospital_region', 'geo_coordinates', 'notes']

    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Validate data types
    if not pd.to_datetime(df['date'], errors='coerce').notna().all():
        raise ValueError("Invalid date format in 'date' column")

    if not df['resistant'].astype(str).str.match(r'^\d+$').all():
        raise ValueError("Invalid values in 'resistant' column")

    if not df['tested'].astype(str).str.match(r'^\d+$').all():
        raise ValueError("Invalid values in 'tested' column")

    print("✅ Data validation passed")

def calculate_percent_resistant(df):
    """Calculate percent resistant where missing."""
    if 'resistant' in df.columns and 'tested' in df.columns:
        df['calculated_percent'] = (df['resistant'] / df['tested'] * 100).round(1)
        if 'percent_resistant' not in df.columns:
            df['percent_resistant'] = df['calculated_percent']
        else:
            # Check for consistency
            diff = abs(df['percent_resistant'] - df['calculated_percent'])
            if diff.max() > 1.0:  # Allow for rounding differences
                print("⚠️  Warning: Some percent_resistant values don't match calculated values")

    return df

def handle_missing_values(df):
    """Handle missing values in AMR dataset."""
    # Fill missing DDD values with group means
    if 'ddd' in df.columns:
        df['ddd'] = df.groupby(['pathogen', 'antibiotic'])['ddd'].transform(lambda x: x.fillna(x.mean()))

    # Fill missing resistance values by interpolation
    df['percent_resistant'] = df.groupby(['pathogen', 'antibiotic'])['percent_resistant'].transform(
        lambda x: x.interpolate(method='linear', limit_direction='both')
    )

    print(f"✅ Missing values handled: {df.isna().sum().sum()} remaining")
    return df

def detect_outliers(df, threshold=3):
    """Detect and report outliers in resistance data."""
    outliers = {}

    for pathogen in df['pathogen'].unique():
        for antibiotic in df['antibiotic'].unique():
            subset = df[(df['pathogen'] == pathogen) & (df['antibiotic'] == antibiotic)]

            if len(subset) > 5:  # Need sufficient data for outlier detection
                resistance_values = subset['percent_resistant']

                mean_val = resistance_values.mean()
                std_val = resistance_values.std()

                outliers_for_pair = subset[
                    abs(resistance_values - mean_val) > threshold * std_val
                ]

                if len(outliers_for_pair) > 0:
                    outliers[f"{pathogen}_{antibiotic}"] = len(outliers_for_pair)
                    print(f"⚠️  Outliers detected in {pathogen}-{antibiotic}: {len(outliers_for_pair)} data points")

    if not outliers:
        print("✅ No significant outliers detected")

    return df

def calculate_data_quality_metrics(df):
    """Calculate data quality metrics for each pathogen-antibiotic pair."""
    metrics = []

    for (pathogen, antibiotic), group in df.groupby(['pathogen', 'antibiotic']):
        metrics.append({
            'pathogen': pathogen,
            'antibiotic': antibiotic,
            'data_points': len(group),
            'date_range': f"{group['date'].min()} to {group['date'].max()}",
            'avg_resistance': group['percent_resistant'].mean(),
            'resistance_trend': 'increasing' if group['percent_resistant'].is_monotonic_increasing else 'variable',
            'ddd_available': 'ddd' in group.columns and group['ddd'].notna().any()
        })

    metrics_df = pd.DataFrame(metrics)
    print("\n📊 DATA QUALITY SUMMARY:")
    print(metrics_df.to_string(index=False))
    return metrics_df

def main():
    """Main preprocessing pipeline."""

    print("🔧 Starting AMR data preprocessing...")

    # Load raw data
    data_path = "../data/amr_data.csv"
    if not os.path.exists(data_path):
        print(f"❌ Data file not found: {data_path}")
        return

    df = pd.read_csv(data_path)
    print(f"📊 Loaded {len(df):,} raw records")

    # Validate data structure
    try:
        validate_amr_data(df)
    except ValueError as e:
        print(f"❌ Data validation failed: {e}")
        return

    # Process data
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['pathogen', 'antibiotic', 'date'])

    # Calculate missing resistance percentages
    df = calculate_percent_resistant(df)

    # Handle missing values
    df = handle_missing_values(df)

    # Detect outliers
    df = detect_outliers(df)

    # Calculate data quality metrics
    metrics = calculate_data_quality_metrics(df)

    # Save processed data
    output_dir = "../data"
    os.makedirs(output_dir, exist_ok=True)

    processed_path = os.path.join(output_dir, "amr_data_processed.csv")
    df.to_csv(processed_path, index=False)
    print(f"💾 Saved processed data to: {processed_path}")

    # Save metrics
    metrics_path = os.path.join(output_dir, "data_quality_metrics.csv")
    metrics.to_csv(metrics_path, index=False)
    print(f"📋 Saved quality metrics to: {metrics_path}")

    print(f"\n✅ Preprocessing complete!")
    print(f"   - Final dataset: {len(df):,} records")
    print(f"   - Pathogen-antibiotic pairs: {len(metrics)}")
    print(f"   - Ready for forecasting models")

if __name__ == "__main__":
    main()
