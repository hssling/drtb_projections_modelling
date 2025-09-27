#!/usr/bin/env python3
"""
Simple AMR Forecasting Batch Runner

Automatically processes all unique pathogen-drug-country combinations
from the unified AMR dataset and generates reports for each.

Usage:
    python pipeline/simple_batch_runner.py [--country COUNTRY] [--limit N]
"""

import pandas as pd
import sys
import argparse
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # Import the simpler forecasting function that has metrics + reports
    from forecast_metrics import forecast_and_evaluate_all
    FORECAST_AVAILABLE = True
    logger.info("Using enhanced forecasting with metrics and reports")
except ImportError:
    try:
        logger.warning("Enhanced forecasting not available, using basic forecasting")
        from forecast_compare import forecast_all
        forecast_and_evaluate_all = lambda c, p, a, **kwargs: forecast_all(c, p, a)
        FORECAST_AVAILABLE = True
    except ImportError:
        logger.warning("No forecasting functions available")
        FORECAST_AVAILABLE = False

def get_unique_combinations(data_file="data/amr_merged.csv", country_filter=None, limit=None):
    """Get unique country-pathogen-antibiotic combinations."""
    if not Path(data_file).exists():
        logger.error(f"Data file not found: {data_file}")
        sys.exit(1)

    df = pd.read_csv(data_file)
    df = df.dropna(subset=["country", "pathogen", "antibiotic"])

    if country_filter:
        df = df[df["country"].str.lower() == country_filter.lower()]
        if df.empty:
            logger.error(f"No data found for country: {country_filter}")
            sys.exit(1)

    # Get unique combinations
    combos = df.groupby(["country", "pathogen", "antibiotic"]).size()
    combos = combos.sort_values(ascending=False)  # Process most data-rich first

    combo_list = list(combos.index)
    if limit and len(combo_list) > limit:
        combo_list = combo_list[:limit]

    return combo_list

def process_combo(combo_tuple):
    """Process a single combination."""
    country, pathogen, antibiotic = combo_tuple
    combo_str = f"{country} | {pathogen} | {antibiotic}"

    logger.info(f"Processing: {combo_str}")

    try:
        # Use the imported forecasting function
        result = forecast_and_evaluate_all(country, pathogen, antibiotic)

        # Check if successful (function returns dict with results)
        if result:
            return True, f"✅ Successfully processed {combo_str}"
        else:
            return False, f"⚠️ Processing returned no results for {combo_str}"

    except Exception as e:
        return False, f"❌ Failed {combo_str}: {str(e)}"

def run_batch(country_filter=None, limit=None):
    """Run batch processing."""
    if not FORECAST_AVAILABLE:
        logger.error("Forecasting functions not available")
        sys.exit(1)

    logger.info("🚀 STARTING AMR BATCH FORECASTING")
    logger.info("=" * 50)

    # Get combinations
    combinations = get_unique_combinations(country_filter=country_filter, limit=limit)
    logger.info(f"Found {len(combinations)} combinations to process")

    # Process each combination
    results = []
    for i, combo in enumerate(combinations, 1):
        success, message = process_combo(combo)
        results.append((combo, success, message))

        if success:
            logger.info(message)
        else:
            logger.warning(message)

        # Progress update
        if i % 5 == 0 or i == len(combinations):
            successful = sum(1 for _, success, _ in results if success)
            logger.info(f"Progress: {successful}/{len(combinations)} completed")

    # Summary
    successful = sum(1 for _, success, _ in results if success)
    failed = len(results) - successful

    logger.info("\n" + "=" * 50)
    logger.info("🏆 BATCH PROCESSING COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Total combinations: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info("Reports saved to: reports/ folder")

def main():
    parser = argparse.ArgumentParser(description='AMR Forecasting Batch Runner')
    parser.add_argument('--country', help='Filter by specific country')
    parser.add_argument('--limit', type=int, help='Limit number of combinations')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')

    args = parser.parse_args()

    if args.dry_run:
        combos = get_unique_combinations(country_filter=args.country, limit=args.limit)
        print("🧪 DRY RUN - Would process:")
        for i, combo in enumerate(combos, 1):
            print("2d")
        print(f"\nTotal: {len(combos)} combinations")
        return

    run_batch(country_filter=args.country, limit=args.limit)

if __name__ == "__main__":
    main()
