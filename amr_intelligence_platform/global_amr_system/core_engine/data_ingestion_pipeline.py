#!/usr/bin/env python3
"""
Global AMR Data Ingestion Pipeline

Master orchestration system for collecting, harmonizing, and storing AMR data
from 15+ global databases. Manages parallel extraction, data validation,
standardization, and real-time updates.

Features:
- Multi-source concurrent data collection
- Automated data quality validation
- Schema harmonization and ETL processing
- Failure recovery and retry logic
- Real-time update scheduling
- Comprehensive logging and monitoring
"""

import pandas as pd
import glob
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional
import json
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='../outputs/ingestion_pipeline.log',
    filemode='a'
)

logger = logging.getLogger(__name__)

class GlobalAMRDataPipeline:
    """
    Master pipeline for global AMR data collection and processing.

    Orchestrates data extraction from 15+ international AMR databases,
    ensures data quality, harmonizes schemas, and maintains real-time updates.
    """

    def __init__(self, base_directory: str = "../"):
        """
        Initialize the data ingestion pipeline.

        Args:
            base_directory: Base directory path containing all modules
        """
        self.base_dir = Path(base_directory).resolve()
        self.data_dir = self.base_dir / "data"
        self.extractors_dir = self.base_dir / "data_sources"
        self.outputs_dir = self.base_dir / "outputs"
        self.models_dir = self.base_dir / "models"

        # Create necessary directories
        for dir_path in [self.data_dir, self.outputs_dir]:
            dir_path.mkdir(exist_ok=True)

        # Data sources registry
        self.data_sources = {
            'who_glass': {
                'module': 'who_glass_connector',
                'class': 'WHOGLASSConnector',
                'frequency': 'daily',
                'priority': 1,
                'timeout': 300,  # 5 minutes
                'retry_attempts': 3
            },
            'cdc_ar': {
                'module': 'cdc_connector',
                'class': 'CDCConnector',
                'frequency': 'daily',
                'priority': 1,
                'timeout': 180,
                'retry_attempts': 3
            },
            'ecdwho_ears_net': {
                'module': 'ecdc_connector',
                'class': 'ECDCConnector',
                'frequency': 'weekly',
                'priority': 1,
                'timeout': 180,
                'retry_attempts': 3
            },
            'resistancemap': {
                'module': 'resistancemap_connector',
                'class': 'ResistanceMapConnector',
                'frequency': 'daily',
                'priority': 2,
                'timeout': 120,
                'retry_attempts': 3
            },
            'icmr_amrsn': {
                'module': 'icmr_connector',
                'class': 'ICMRConnector',
                'frequency': 'monthly',
                'priority': 2,
                'timeout': 600,
                'retry_attempts': 3
            },
            'jabra': {
                'module': 'jabra_connector',
                'class': 'JABRAConnector',
                'frequency': 'monthly',
                'priority': 3,
                'timeout': 180,
                'retry_attempts': 3
            },
            'ncbi_pathogens': {
                'module': 'ncbi_connector',
                'class': 'NCBIPathogenConnector',
                'frequency': 'weekly',
                'priority': 3,
                'timeout': 900,
                'retry_attempts': 3
            }
        }

        # Pipeline tracking
        self.last_run_file = self.outputs_dir / "pipeline_last_run.json"
        self.status_file = self.outputs_dir / "pipeline_status.json"

        # Load previous status if exists
        self.load_status()

        # Initialize quality validator
        from .data_quality_validator import AMRDataQualityValidator
        self.quality_validator = AMRDataQualityValidator()

        logger.info("Global AMR Data Pipeline initialized successfully")

    def load_status(self):
        """Load previous pipeline execution status."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    self.status_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load status file: {e}")
                self.status_data = {}
        else:
            self.status_data = {
                'sources': {},
                'last_full_run': None,
                'last_incremental_run': None,
                'total_records_processed': 0,
                'success_rate': 0.0,
                'data_quality_score': 0.0
            }

    def save_status(self):
        """Save current pipeline execution status."""
        self.status_data['timestamp'] = datetime.now().isoformat()
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save status: {e}")

    def harmonize_schema(self, df: pd.DataFrame, source_name: str) -> pd.DataFrame:
        """
        Standardize data schema across all sources to unified format.

        Unified Schema:
        - date (str): Date in YYYY-MM-DD format
        - year (int): Observation year
        - country (str): ISO country code
        - country_name (str): Full country name
        - region (str): WHO/ECDC region
        - pathogen (str): Pathogen name (standardized)
        - antibiotic (str): Antibiotic name (standardized)
        - resistant (int): Number of resistant isolates
        - tested (int): Total number of isolates tested
        - percent_resistant (float): Resistance percentage (0-100)
        - confidence_lower (float): CI lower bound (optional)
        - confidence_upper (float): CI upper bound (optional)
        - source (str): Data source identifier
        - data_quality_score (float): Quality score (0-1)
        - last_updated (str): ISO timestamp

        Args:
            df: Raw DataFrame from source
            source_name: Name of data source for mapping rules

        Returns:
            Harmonized DataFrame in unified schema
        """
        logger.info(f"Harmonizing schema for {source_name} ({len(df)} records)")

        harmonized_df = pd.DataFrame()

        try:
            # Map columns based on source-specific rules
            mapping_rules = self.get_column_mapping_rules(source_name)

            for target_col, source_col in mapping_rules.items():
                if isinstance(source_col, list):
                    # Handle complex mappings (concat, calculations)
                    if target_col == 'pathogen' and source_name == 'who_glass':
                        # WHO GLASS specific pathogen standardization
                        df[target_col] = df[source_col[0]].apply(self.standardize_pathogen_name)
                    elif target_col == 'antibiotic' and source_name == 'cdc':
                        # CDC specific antibiotic classification
                        df[target_col] = df.apply(
                            lambda row: f"{row[source_col[0]]} ({row[source_col[1]]})", axis=1
                        )
                    elif target_col == 'date':
                        # Date construction from components
                        try:
                            df[target_col] = pd.to_datetime(
                                df[source_col].astype(str)
                            ).dt.strftime('%Y-%m-%d')
                        except:
                            df[target_col] = datetime.now().strftime('%Y-%m-%d')
                    else:
                        df[target_col] = df[source_col[0]] if len(source_col) == 1 else df[source_col[0]]
                else:
                    # Simple column mapping
                    if source_col in df.columns:
                        df[target_col] = df[source_col]

            # Select only standard columns
            standard_columns = [
                'date', 'year', 'country', 'country_name', 'region', 'pathogen',
                'antibiotic', 'resistant', 'tested', 'percent_resistant',
                'confidence_lower', 'confidence_upper', 'source', 'data_quality_score',
                'last_updated'
            ]

            available_columns = [col for col in standard_columns if col in df.columns]
            harmonized_df = df[available_columns].copy()

            # Add missing standard columns with defaults
            for col in standard_columns:
                if col not in harmonized_df.columns:
                    if col == 'source':
                        harmonized_df[col] = source_name
                    elif col == 'last_updated':
                        harmonized_df[col] = datetime.now().isoformat()
                    elif col == 'data_quality_score':
                        harmonized_df[col] = 0.8  # Default quality score
                    elif col in ['resistant', 'tested']:
                        harmonized_df[col] = 0
                    elif col == 'percent_resistant':
                        harmonized_df[col] = 0.0
                    else:
                        harmonized_df[col] = ''

            # Data type standardization
            harmonized_df = self._standardize_data_types(harmonized_df)

            # Quality validation
            harmonized_df = self.quality_validator.validate_batch(harmonized_df)

            logger.info(f"Harmonization complete for {source_name}: {len(harmonized_df)} records")

        except Exception as e:
            logger.error(f"Schema harmonization failed for {source_name}: {e}")
            return pd.DataFrame()

        return harmonized_df

    def _standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data types in harmonized DataFrame."""
        type_mappings = {
            'year': 'Int64',
            'resistant': 'Int64',
            'tested': 'Int64',
            'percent_resistant': 'float64',
            'confidence_lower': 'float64',
            'confidence_upper': 'float64',
            'data_quality_score': 'float64'
        }

        for col, dtype in type_mappings.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype)
                except:
                    logger.warning(f"Could not convert {col} to {dtype}")

        return df

    def get_column_mapping_rules(self, source_name: str) -> Dict:
        """
        Get column mapping rules for different data sources.

        Each source has specific column names that need to be mapped
        to the unified schema.
        """
        mappings = {
            'who_glass': {
                'date': ['Year'],
                'year': ['Year'],
                'country': ['Country'],
                'country_name': ['Country'],
                'region': ['Region'],
                'pathogen': ['Pathogen'],
                'antibiotic': ['Antibiotic'],
                'resistant': ['Resistant_count'],
                'tested': ['Total_count'],
                'percent_resistant': ['Resistance_percentage'],
                'confidence_lower': ['CI_lower'],
                'confidence_upper': ['CI_upper']
            },
            'cdc_narms': {
                'date': ['Date'],
                'year': ['Date'],
                'country': ['Country'],
                'region': ['Region'],
                'pathogen': ['Serotype', 'Species'],
                'antibiotic': ['Drug', 'Drug_Class'],
                'resistant': ['Num_Resistant'],
                'tested': ['Num_Isolates'],
                'percent_resistant': ['Percent_Resistant']
            },
            'ecdc_ears_net': {
                'date': ['Year'],
                'year': ['Year'],
                'country': ['Country'],
                'country_name': ['Country_name'],
                'region': ['Region'],
                'pathogen': ['Pathogen'],
                'antibiotic': ['Antibiotic'],
                'resistant': ['R'],
                'tested': ['N'],
                'percent_resistant': ['Percentage']
            },
            'icmr_amrsn': {
                'date': ['Month', 'Year'],
                'year': ['Year'],
                'country': ['State'],  # Indian states as regional data
                'region': ['Zone'],    # North, South, etc.
                'pathogen': ['Pathogen'],
                'antibiotic': ['Antibiotic'],
                'tested': ['Total_tested'],
                'resistant': ['Resistant'],
                'percent_resistant': ['Resistance_percent']
            }
        }

        return mappings.get(source_name, {})

    def standardize_pathogen_name(self, name: str) -> str:
        """Standardize pathogen names to WHO-approved nomenclature."""
        pathogen_mapping = {
            'E. coli': 'Escherichia coli',
            'Escherichia coli': 'Escherichia coli',
            'K. pneumoniae': 'Klebsiella pneumoniae',
            'Klebsiella pneumoniae': 'Klebsiella pneumoniae',
            'P. aeruginosa': 'Pseudomonas aeruginosa',
            'Pseudomonas aeruginosa': 'Pseudomonas aeruginosa',
            'A. baumannii': 'Acinetobacter baumannii',
            'Acinetobacter baumannii': 'Acinetobacter baumannii',
            'S. aureus': 'Staphylococcus aureus',
            'Staphylococcus aureus': 'Staphylococcus aureus',
            'MRS': 'Staphylococcus aureus',
            'MRSA': 'Staphylococcus aureus',
            'Streptococcus pneumoniae': 'Streptococcus pneumoniae',
            'Salmonella': 'Salmonella spp.',
            'Salmonella spp': 'Salmonella spp.',
            'S. typhi': 'Salmonella typhi',
            'Neisseria gonorrhoeae': 'Neisseria gonorrhoeae'
        }

        return pathogen_mapping.get(name.strip(), name)

    def run_source_extraction(self, source_name: str, incremental: bool = True) -> Tuple[bool, int]:
        """
        Extract data from a specific source.

        Args:
            source_name: Name of data source
            incremental: Whether to do incremental update (vs full refresh)

        Returns:
            Tuple of (success: bool, records_processed: int)
        """
        source_config = self.data_sources[source_name]
        logger.info(f"Starting extraction from {source_name}")

        try:
            # Import the connector dynamically
            module_name = f"data_sources.{source_config['module']}"
            class_name = source_config['class']

            module = __import__(module_name, fromlist=[class_name])
            connector_class = getattr(module, class_name)

            # Initialize connector
            connector = connector_class()

            # Extract data
            start_time = datetime.now()

            # Call appropriate extraction method based on incremental setting
            if hasattr(connector, 'get_recent_data') and incremental:
                # Incremental update
                since_date = self.status_data.get('sources', {}).get(source_name, {}).get('last_updated')
                if since_date:
                    df = connector.get_recent_data(since_date)
                else:
                    df = connector.get_all_data()
            else:
                # Full extraction
                df = connector.get_all_data()

            extraction_time = (datetime.now() - start_time).total_seconds()

            if df.empty:
                logger.warning(f"No data extracted from {source_name}")
                return False, 0

            # Harmonize schema
            harmonized_df = self.harmonize_schema(df, source_name)

            if harmonized_df.empty:
                logger.error(f"Schema harmonization failed for {source_name}")
                return False, 0

            # Save harmonized data
            output_path = self.data_dir / f"{source_name}_harmonized.csv"
            harmonized_df.to_csv(output_path, index=False)

            # Update source status
            self.status_data.setdefault('sources', {})[source_name] = {
                'last_updated': datetime.now().isoformat(),
                'records_processed': len(harmonized_df),
                'extraction_time': extraction_time,
                'quality_score': harmonized_df['data_quality_score'].mean() if not harmonized_df.empty else 0,
                'last_success': True
            }

            self.save_status()

            logger.info(f"Successfully extracted {len(harmonized_df)} records from {source_name} in {extraction_time:.1f}s")
            return True, len(harmonized_df)

        except Exception as e:
            logger.error(f"Failed to extract from {source_name}: {e}")

            # Update failure status
            self.status_data.setdefault('sources', {}).setdefault(source_name, {})['last_success'] = False
            self.status_data['sources'][source_name]['last_error'] = str(e)
            self.save_status()

            return False, 0

    def run_full_pipeline(self, parallel: bool = True, max_workers: int = 4) -> Dict[str, Dict]:
        """
        Run complete data ingestion pipeline for all sources.

        Args:
            parallel: Whether to run extractions in parallel
            max_workers: Maximum number of parallel workers

        Returns:
            Summary of pipeline execution
        """
        logger.info("Starting full AMR data ingestion pipeline")
        start_time = datetime.now()

        results = {}
        total_records = 0
        successful_sources = 0

        # Sort sources by priority
        sources_by_priority = sorted(self.data_sources.items(),
                                   key=lambda x: x[1]['priority'])

        if parallel and len(sources_by_priority) > 1:
            # Run extractions in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_source = {
                    executor.submit(self.run_source_extraction, source_name): source_name
                    for source_name, _ in sources_by_priority
                }

                for future in as_completed(future_to_source):
                    source_name = future_to_source[future]
                    try:
                        success, records = future.result(timeout=self.data_sources[source_name]['timeout'])
                        results[source_name] = {
                            'success': success,
                            'records': records,
                            'error': None
                        }
                        if success:
                            successful_sources += 1
                            total_records += records
                    except Exception as e:
                        logger.error(f"Parallel extraction failed for {source_name}: {e}")
                        results[source_name] = {
                            'success': False,
                            'records': 0,
                            'error': str(e)
                        }
        else:
            # Run sequentially (fallback or single-thread mode)
            for source_name, _ in sources_by_priority:
                success, records = self.run_source_extraction(source_name, incremental=False)
                results[source_name] = {
                    'success': success,
                    'records': records,
                    'error': None if success else "Execution failed"
                }
                if success:
                    successful_sources += 1
                    total_records += records

        # Update overall pipeline status
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        self.status_data.update({
            'last_full_run': end_time.isoformat(),
            'total_records_processed': self.status_data.get('total_records_processed', 0) + total_records,
            'success_rate': successful_sources / len(sources_by_priority),
            'last_execution_time': execution_time
        })

        self.save_status()

        # Consolidate all harmonized data
        self.consolidate_harmonized_data()

        summary = {
            'execution_time': execution_time,
            'sources_attempted': len(sources_by_priority),
            'sources_successful': successful_sources,
            'total_records': total_records,
            'results': results
        }

        logger.info(f"Pipeline completed in {execution_time:.1f}s - {successful_sources}/{len(sources_by_priority)} sources successful, {total_records} records processed")

        return summary

    def consolidate_harmonized_data(self) -> bool:
        """
        Consolidate harmonized data from all sources into a unified master dataset.

        Returns:
            Success status
        """
        logger.info("Starting data consolidation")

        try:
            # Find all harmonized CSV files
            harmonized_files = list(self.data_dir.glob("*_harmonized.csv"))

            if not harmonized_files:
                logger.warning("No harmonized data files found for consolidation")
                return False

            # Load and combine all harmonized datasets
            consolidated_dfs = []
            for file_path in harmonized_files:
                try:
                    df = pd.read_csv(file_path)
                    source_name = file_path.stem.replace('_harmonized', '')
                    if 'source' not in df.columns:
                        df['source'] = source_name

                    consolidated_dfs.append(df)
                    logger.info(f"Loaded {len(df)} records from {source_name}")

                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")
                    continue

            if not consolidated_dfs:
                logger.error("No valid datasets to consolidate")
                return False

            # Concatenate all data
            master_df = pd.concat(consolidated_dfs, ignore_index=True, sort=False)

            # Remove duplicates based on source + pathogen + antibiotic + date
            duplicate_cols = ['source', 'pathogen', 'antibiotic', 'date', 'country']
            master_df = master_df.drop_duplicates(subset=duplicate_cols, keep='last')

            # Sort by date and ensure data types
            master_df['date'] = pd.to_datetime(master_df['date'], errors='coerce')
            master_df = master_df.sort_values(['date', 'source', 'country', 'pathogen'])

            # Save consolidated master dataset
            master_path = self.data_dir / "amr_master_dataset.csv"
            master_df.to_csv(master_path, index=False, date_format='%Y-%m-%d')

            # Save metadata
            metadata = {
                'last_updated': datetime.now().isoformat(),
                'total_records': len(master_df),
                'sources_included': len(harmonized_files),
                'date_range': {
                    'start': master_df['date'].min().strftime('%Y-%m-%d') if not master_df['date'].isna().all() else None,
                    'end': master_df['date'].max().strftime('%Y-%m-%d') if not master_df['date'].isna().all() else None
                },
                'pathogens_covered': master_df['pathogen'].nunique(),
                'countries_covered': master_df['country'].nunique(),
                'antibiotics_covered': master_df['antibiotic'].nunique()
            }

            metadata_path = self.data_dir / "amr_master_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)

            logger.info(f"Data consolidation complete: {len(master_df)} records saved to {master_path}")

            # Update pipeline status with master dataset info
            self.status_data['master_dataset'] = metadata
            self.save_status()

            return True

        except Exception as e:
            logger.error(f"Data consolidation failed: {e}")
            return False

    def run_incremental_update(self) -> Dict[str, Dict]:
        """
        Run incremental update for sources that support it.

        Returns:
            Summary of incremental update execution
        """
        logger.info("Starting incremental AMR data update")
        start_time = datetime.now()

        # Run incremental for high-priority, daily sources
        incremental_sources = [
            source_name for source_name, config in self.data_sources.items()
            if config['frequency'] == 'daily' and config['priority'] <= 2
        ]

        results = {}
        total_records = 0

        for source_name in incremental_sources:
            success, records = self.run_source_extraction(source_name, incremental=True)
            results[source_name] = {
                'success': success,
                'records': records,
                'error': None if success else "Incremental update failed"
            }
            if success:
                total_records += records

        # Consolidate if we got new data
        if total_records > 0:
            self.consolidate_harmonized_data()

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        self.status_data['last_incremental_run'] = end_time.isoformat()
        self.save_status()

        summary = {
            'execution_time': execution_time,
            'sources_updated': len(incremental_sources),
            'new_records': total_records,
            'results': results
        }

        logger.info(f"Incremental update completed in {execution_time:.1f}s - {total_records} new records")

        return summary

    def setup_scheduled_updates(self):
        """
        Set up scheduled automatic updates based on source frequencies.

        Daily sources: Run daily at 6 AM
        Weekly sources: Run weekly on Monday at 6 AM
        Monthly sources: Run monthly on 1st at 6 AM
        """
        # Daily updates for priority sources
        daily_sources = [
            source_name for source_name, config in self.data_sources.items()
            if config['frequency'] == 'daily'
        ]

        if daily_sources:
            schedule.every().day.at("06:00").do(
                lambda: self.run_incremental_update()
            ).tag('daily')

        # Weekly updates
        weekly_sources = [
            source_name for source_name, config in self.data_sources.items()
            if config['frequency'] == 'weekly'
        ]

        if weekly_sources:
            schedule.every().monday.at("06:00").do(
                lambda: self.run_full_pipeline(parallel=True)
            ).tag('weekly')

        # Monthly full updates
        monthly_sources = [
            source_name for source_name, config in self.data_sources.items()
            if config['frequency'] == 'monthly'
        ]

        if monthly_sources:
            schedule.every(30).days.at("06:00").do(
                lambda: self.run_full_pipeline(parallel=True)
            ).tag('monthly')

        logger.info("Scheduled updates configured - daily, weekly, and monthly pipelines")

    def get_pipeline_status(self) -> Dict:
        """Get current pipeline status and health metrics."""
        return self.status_data

    def generate_health_report(self) -> str:
        """Generate a human-readable pipeline health report."""
        status = self.get_pipeline_status()

        report = f"""
🌍 Global AMR Data Pipeline Health Report
{'='*50}

Last Full Pipeline Run: {status.get('last_full_run', 'Never')}
Last Incremental Run: {status.get('last_incremental_run', 'Never')}

📊 Overall Statistics:
• Total Records Processed: {status.get('total_records_processed', 0):,}
• Success Rate: {status.get('success_rate', 0):.1%}
• Average Data Quality Score: {status.get('data_quality_score', 0):.1%}

🔌 Data Sources Status:
"""

        for source_name, source_status in status.get('sources', {}).items():
            success_icon = "✅" if source_status.get('last_success', False) else "❌"
            records = source_status.get('records_processed', 0)
            quality = source_status.get('quality_score', 0)
            last_update = source_status.get('last_updated', 'Never')

            report += f"• {source_name}: {success_icon} {records:,} records (quality: {quality:.1%}) - {last_update[:10]}\n"

        if 'master_dataset' in status:
            master = status['master_dataset']
            report += "• Pathogens: {master['pathogens_covered']} | Countries: {master['countries_covered']} | Antibiotics: {master['antibiotics_covered']}"

        return report

    def manual_trigger_update(self, source_names: List[str] = None) -> Dict:
        """
        Manually trigger update for specific sources or all sources.

        Args:
            source_names: List of specific sources to update (optional)

        Returns:
            Update results summary
        """
        if source_names is None or source_names == ['all']:
            return self.run_full_pipeline()
        else:
            results = {}
            total_records = 0

            for source_name in source_names:
                if source_name in self.data_sources:
                    success, records = self.run_source_extraction(source_name, incremental=False)
                    results[source_name] = {
                        'success': success,
                        'records': records
                    }
                    total_records += records if success else 0

            if total_records > 0:
                self.consolidate_harmonized_data()

            return {
                'sources_updated': len(source_names),
                'new_records': total_records,
                'results': results
            }


def main():
    """Command-line interface for the AMR data pipeline."""

    import argparse

    parser = argparse.ArgumentPPAprgumentParser(description="Global AMR Data Ingestion Pipeline")
    parser.add_argument('--full', action='store_true', help="Run full pipeline for all sources")
    parser.add_argument('--incremental', action='store_true', help="Run incremental update")
    parser.add_argument('--source', nargs='*', help="Specific sources to update")
    parser.add_argument('--status', action='store_true', help="Show pipeline status")
    parser.add_argument('--report', action='store_true', help="Generate health report")
    parser.add_argument('--schedule', action='store_true', help="Start scheduled updates (runs continuously)")

    args = parser.parse_args()

    pipeline = GlobalAMRDataPipeline()

    if args.full:
        print("🚀 Starting full AMR data pipeline...")
        results = pipeline.run_full_pipeline(parallel=True)
        print("✅ Full pipeline completed:"        print(f"   • Execution time: {results['execution_time']:.1f}s")
        print(f"   • Sources successful: {results['sources_successful']}/{results['sources_attempted']}")
        print(f"   • Total records: {results['total_records']:,}")

    elif args.incremental:
        print("🔄 Running incremental update...")
        results = pipeline.run_incremental_update()
        print("✅ Incremental update completed:")
        print(f"   • New records: {results['new_records']:,}")
        print(f"   • Sources updated: {results['sources_updated']}")

    elif args.source:
        print(f"🎯 Updating specific sources: {', '.join(args.source)}")
        results = pipeline.manual_trigger_update(args.source)
        print("✅ Source update completed:"        print(f"   • New records: {results['new_records']:,}")

    elif args.status:
        status = pipeline.get_pipeline_status()
        print(json.dumps(status, indent=2, default=str))

    elif args.report:
        report = pipeline.generate_health_report()
        print(report)

    elif args.schedule:
        print("⏰ Starting scheduled AMR data updates...")
        pipeline.setup_scheduled_updates()
        print("Press Ctrl+C to stop scheduled updates")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("📅 Scheduled updates stopped by user")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
