#!/usr/bin/env python3
"""
AMR Forecasting Batch Runner - Multi-Pathogen Analysis

Automatically runs forecasting analysis for all pathogen-drug-country combinations
in the unified AMR dataset, generating comprehensive reports for each combination.

Features:
- Processes all unique country-pathogen-antibiotic combinations
- Generates metrics, plots, and professional reports for each
- Progress tracking and error handling
- Parallel processing support
- Incremental updates (skips already processed combinations)
- Configurable filtering by country/region

Usage:
    python pipeline/batch_runner.py [--country COUNTRY] [--limit N] [--parallel]

Example:
    python pipeline/batch_runner.py --country "India" --limit 5
    python pipeline/batch_runner.py --parallel --limit 20
"""

import pandas as pd
import sys
import argparse
from pathlib import Path
import logging
from datetime import datetime
import time
import concurrent.futures
import multiprocessing
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline/batch_run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    # Import the forecasting functions
    from amr_forecast_with_reports import run_forecast_analysis
    FORECAST_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Could not import forecast functions. Please ensure amr_forecast_with_reports.py is available")
    FORECAST_AVAILABLE = False

class AMRBatchRunner:
    """
    Batch processing engine for AMR forecasting analysis.

    Handles multi-pathogen analysis across all country-pathogen-antibiotic combinations.
    """

    def __init__(self, data_file: str = "data/amr_merged.csv", reports_dir: str = "reports"):
        """
        Initialize batch runner.

        Args:
            data_file: Path to unified AMR dataset
            reports_dir: Directory to save generated reports
        """
        self.data_file = Path(data_file)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)

    def load_data(self) -> pd.DataFrame:
        """Load and validate the AMR dataset."""
        if not self.data_file.exists():
            raise FileNotFoundError(f"AMR dataset not found: {self.data_file}")

        logger.info(f"Loading AMR dataset from {self.data_file}")
        df = pd.read_csv(self.data_file)

        # Validate required columns
        required_cols = ['country', 'pathogen', 'antibiotic', 'percent_resistant', 'date']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        logger.info(f"Dataset loaded: {len(df)} records")
        return df

    def get_combinations(self, df: pd.DataFrame,
                        country_filter: Optional[str] = None,
                        limit: Optional[int] = None) -> List[Tuple[str, str, str]]:
        """
        Get unique country-pathogen-antibiotic combinations.

        Args:
            df: AMR dataset
            country_filter: Filter by specific country (optional)
            limit: Limit number of combinations to process (optional)

        Returns:
            List of (country, pathogen, antibiotic) tuples
        """
        # Filter by country if specified
        if country_filter:
            df = df[df['country'].str.lower() == country_filter.lower()]
            if df.empty:
                logger.warning(f"No data found for country: {country_filter}")
                return []

        # Ensure we have valid data
        df_filtered = df.dropna(subset=['country', 'pathogen', 'antibiotic'])
        df_filtered = df_filtered[~df_filtered[['country', 'pathogen', 'antibiotic']].isin(['']).any(axis=1)]

        # Get unique combinations
        combinations = df_filtered.groupby(['country', 'pathogen', 'antibiotic']).size().reset_index()
        combinations = combinations[['country', 'pathogen', 'antibiotic']]

        # Sort by data volume (process most data-rich combinations first)
        combinations['data_volume'] = df_filtered.groupby(['country', 'pathogen', 'antibiotic']).size().values
        combinations = combinations.sort_values('data_volume', ascending=False).drop('data_volume', axis=1)

        # Convert to list of tuples
        combo_list = list(combinations.itertuples(index=False, name=None))

        # Apply limit if specified
        if limit and len(combo_list) > limit:
            logger.info(f"Limiting to top {limit} combinations by data volume")
            combo_list = combo_list[:limit]

        logger.info(f"Selected {len(combo_list)} combinations to process")
        return combo_list

    def process_single_combination(self, combo: Tuple[str, str, str]) -> Tuple[bool, str]:
        """
        Process a single country-pathogen-antibiotic combination.

        Args:
            combo: Tuple of (country, pathogen, antibiotic)

        Returns:
            Tuple of (success: bool, message: str)
        """
        country, pathogen, antibiotic = combo

        # Safely format filename
        safe_combo = (country.replace(' ', '_').replace('/', '_'),
                     pathogen.replace(' ', '_').replace('/', '_').replace('.', ''),
                     antibiotic.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', ''))

        combo_str = f"{country} | {pathogen} | {antibiotic}"
        logger.info(f"Processing: {combo_str}")

        try:
            start_time = time.time()

            # Run forecast analysis with reports
            result = run_forecast_analysis(country, pathogen, antibiotic)

            if result and result.get('generated_reports'):
                report_count = len([r for r in result['generated_reports'].values() if r])

                elapsed_time = time.time() - start_time
                message = ".1f"                logger.info(message)
                return True, message
            else:
                message = f"⚠️ Analysis completed but no reports generated: {combo_str}"
                logger.warning(message)
                return False, message

        except Exception as e:
            error_msg = f"❌ Failed to process {combo_str}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def run_batch(self, country_filter: Optional[str] = None,
                  limit: Optional[int] = None, parallel: bool = False,
                  max_workers: Optional[int] = None) -> dict:
        """
        Run batch analysis for all combinations.

        Args:
            country_filter: Filter by specific country
            limit: Limit number of combinations
            parallel: Use parallel processing
            max_workers: Maximum parallel workers (default: CPU count)

        Returns:
            Summary statistics of batch run
        """
        if not FORECAST_AVAILABLE:
            raise RuntimeError("Forecast functions not available. Please ensure amr_forecast_with_reports.py is properly configured")

        logger.info("=" * 80)
        logger.info("🦠 STARTING AMR FORECASTING BATCH RUN")
        logger.info("=" * 80)

        # Load data
        df = self.load_data()

        # Get combinations to process
        combinations = self.get_combinations(df, country_filter, limit)

        if not combinations:
            logger.warning("No combinations to process")
            return {"success": 0, "failed": 0, "total": 0}

        total_combinations = len(combinations)
        logger.info(f"Beginning batch processing of {total_combinations} combinations")

        # Choose processing method
        if parallel and total_combinations > 3:
            return self._run_parallel(combinations, max_workers)
        else:
            return self._run_sequential(combinations)

    def _run_sequential(self, combinations: List[Tuple[str, str, str]]) -> dict:
        """Run combinations sequentially."""
        results = []
        start_time = time.time()

        for i, combo in enumerate(combinations, 1):
            logger.info(f"[{i}/{len(combinations)}] Processing combination...")

            # Check if already processed (optional)
            country, pathogen, antibiotic = combo
            combo_prefix = f"{country}_{pathogen}_{antibiotic}".replace(' ', '_')

            # Skip existing (uncomment to enable incremental updates)
            # existing_files = list(self.reports_dir.glob(f"*{combo_prefix}*.docx"))
            # if existing_files:
            #     logger.info(f"⏭️ Skipping already processed: {combo_prefix}")
            #     continue

            success, message = self.process_single_combination(combo)
            results.append((combo, success, message))

            # Progress update every 5 combinations
            if i % 5 == 0:
                completed = sum(1 for _, success, _ in results if success)
                logger.info(f"Progress: {completed}/{len(combinations)} completed")

        # Summarize results
        return self._summarize_results(results, start_time)

    def _run_parallel(self, combinations: List[Tuple[str, str, str]],
                     max_workers: Optional[int] = None) -> dict:
        """Run combinations in parallel."""
        if max_workers is None:
            max_workers = max(1, multiprocessing.cpu_count() - 1)  # Leave one CPU free

        logger.info(f"Using parallel processing with {max_workers} workers")

        start_time = time.time()

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_combo = {
                executor.submit(self.process_single_combination, combo): combo
                for combo in combinations
            }

            # Collect results as they complete
            results = []
            completed_count = 0

            for future in concurrent.futures.as_completed(future_to_combo):
                combo = future_to_combo[future]
                try:
                    success, message = future.result(timeout=300)  # 5 minute timeout per combination
                    results.append((combo, success, message))

                    completed_count += 1
                    if completed_count % 5 == 0:
                        logger.info(f"Progress: {completed_count}/{len(combinations)} completed")

                except concurrent.futures.TimeoutError:
                    logger.error(f"❌ Timeout processing {combo}")
                    results.append((combo, False, "Timeout"))

                except Exception as e:
                    logger.error(f"❌ Execution error for {combo}: {e}")
                    results.append((combo, False, str(e)))

        return self._summarize_results(results, start_time)

    def _summarize_results(self, results: List[Tuple], start_time: float) -> dict:
        """Generate summary of batch run results."""
        total_time = time.time() - start_time
        total_combinations = len(results)
        successful = sum(1 for _, success, _ in results if success)
        failed = total_combinations - successful

        # Log individual failures
        failures = [(combo, message) for combo, success, message in results if not success]
        if failures:
            logger.warning(f"Failed combinations ({len(failures)}):")
            for combo, message in failures[:5]:  # Show first 5
                logger.warning(f"  • {combo[0]}|{combo[1]}|{combo[2]}: {message}")
            if len(failures) > 5:
                logger.warning(f"  ... and {len(failures) - 5} more")

        # Summary report
        logger.info("=" * 80)
        logger.info("🏆 BATCH RUN COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total combinations processed: {total_combinations}")
        logger.info(f"Successful analyses: {successful}")
        logger.info(f"Failed analyses: {failed}")
        logger.info(".2f")
        logger.info(".1f")
        logger.info(f"Average time per combination: {total_time / total_combinations:.1f} seconds")

        # Generate summary CSV
        summary_file = self.reports_dir / f"batch_run_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        summary_data = []
        for combo, success, message in results:
            summary_data.append({
                'country': combo[0],
                'pathogen': combo[1],
                'antibiotic': combo[2],
                'success': success,
                'message': message
            })

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(summary_file, index=False)

        logger.info(f"📊 Detailed summary saved: {summary_file}")
        logger.info(f"📁 All reports saved to: {self.reports_dir}/")

        return {
            'total': total_combinations,
            'successful': successful,
            'failed': failed,
            'total_time': total_time,
            'summary_file': str(summary_file)
        }

def main():
    """Command-line interface for batch AMR forecasting."""
    parser = argparse.ArgumentParser(
        description='AMR Forecasting Batch Runner - Multi-Pathogen Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all combinations
  python pipeline/batch_runner.py

  # Process only India combinations
  python pipeline/batch_runner.py --country "India"

  # Process top 5 combinations in parallel
  python pipeline/batch_runner.py --limit 5 --parallel

  # Process US combinations with custom workers
  python pipeline/batch_runner.py --country "United States" --parallel --max-workers 4
        """
    )

    parser.add_argument(
        '--country',
        type=str,
        help='Filter by specific country (e.g., "India", "United States")'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of combinations to process (for testing)'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Use parallel processing for multiple combinations'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        default=None,
        help='Maximum parallel workers (default: CPU count - 1)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without running analysis'
    )

    args = parser.parse_args()

    try:
        runner = AMRBatchRunner()

        if args.dry_run:
            # Just show what would be processed
            df = runner.load_data()
            combinations = runner.get_combinations(df, args.country, args.limit)

            print("🧪 DRY RUN - Would process the following combinations:")
            print("=" * 60)
            for i, combo in enumerate(combinations, 1):
                print("2d")
            print(f"\nTotal: {len(combinations)} combinations")
            return

        # Run batch analysis
        summary = runner.run_batch(
            country_filter=args.country,
            limit=args.limit,
            parallel=args.parallel,
            max_workers=args.max_workers
        )

        # Print final summary
        print("\n📈 FINAL SUMMARY:")
        print("=" * 30)
        print(f"✅ Successful: {summary['successful']}")
        print(f"❌ Failed: {summary['failed']}")
        print(".1f"        print(".2f")

        if summary['failed'] > 0:
            print(f"📄 Check {summary.get('summary_file', 'logs')} for detailed error information")

    except KeyboardInterrupt:
        print("\n⏹️ Batch run interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Batch run failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
