#!/usr/bin/env python3
"""
ResistanceMap Data Connector

Connects to CDDEP's ResistanceMap database for global antibiotic consumption
and resistance trends. Extracts country-level data for consumption patterns
and resistance correlations.

Data: Country-level antibiotic consumption, usage metrics, resistance trends.
Format: Interactive dashboard with downloadable CSVs and API endpoints.
Access: CDDEP ResistanceMap portal (public data with possible API).
"""

import pandas as pd
import requests
from pathlib import Path
import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class ResistanceMapConnector:
    """
    Connector for CDDEP ResistanceMap global antibiotic data.

    Features:
    - Country-level antibiotic consumption data
    - Resistance trends vs usage correlations
    - Geographic coverage of 41+ countries
    - Historical data from 2000-present
    """

    def __init__(self, config_path: str = "../config/data_sources.yml"):
        """
        Initialize ResistanceMap connector.

        Args:
            config_path: Path to API credentials (if available)
        """
        # ResistanceMap API endpoints (if available)
        self.base_url = "https://resistancemap.cddep.org"
        self.data_api_url = f"{self.base_url}/api"

        # Public export links (may require manual update with current URLs)
        self.consumption_export_url = "https://resistancemap.cddep.org/ConsumptionData/Export"
        self.resistance_export_url = "https://resistancemap.cddep.org/ResistnanceData/Export"

        self.rate_limit_delay = 2.0  # Respect website rate limits
        self.timeout = 30

        logger.info("ResistanceMap connector initialized")

    def fetch_resistancemap_manual_download(self) -> Optional[pd.DataFrame]:
        """
        Handle manual download workflow for ResistanceMap data.

        This method expects user to manually download CSV files from ResistanceMap
        and place them in the data directory.

        Returns:
            DataFrame if manual CSV is available
        """
        data_dir = Path("../../data")
        data_dir.mkdir(exist_ok=True)

        # Look for manually downloaded files
        consumption_file = data_dir / "resistancemap_raw.csv"
        alternative_files = [
            data_dir / "resistancemap_consumption.csv",
            data_dir / "resistancemap.csv",
            data_dir / "cddep_amr_data.csv"
        ]

        for file_path in [consumption_file] + alternative_files:
            if file_path.exists():
                logger.info(f"Found manual ResistanceMap download: {file_path}")
                return self._process_manual_download(file_path)

        logger.warning("No ResistanceMap data file found. Please manually download from: https://resistancemap.cddep.org/ConsumptionData")
        return None

    def _process_manual_download(self, file_path: Path) -> pd.DataFrame:
        """
        Process manually downloaded ResistanceMap CSV file.

        Args:
            file_path: Path to downloaded CSV file

        Returns:
            Processed DataFrame in standardized format
        """
        try:
            # Read and process CSV
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            logger.info(f"Loaded {len(df)} rows from ResistanceMap CSV")

            # Get column mapping for this source
            column_mapping = self._get_resistancemap_column_mapping(df)

            # Apply standard schema
            standardized_df = self._apply_standard_schema(df, column_mapping)
            standardized_df['source'] = 'ResistanceMap'
            standardized_df['last_updated'] = datetime.now().isoformat()

            logger.info(f"Processed ResistanceMap data: {len(standardized_df)} standardized records")
            return standardized_df

        except Exception as e:
            logger.error(f"Failed to process ResistanceMap CSV: {e}")
            return pd.DataFrame()

    def _get_resistancemap_column_mapping(self, df: pd.DataFrame) -> Dict:
        """
        Determine column mapping based on ResistanceMap CSV structure.

        Args:
            df: Raw DataFrame from ResistanceMap

        Returns:
            Dictionary mapping standard columns to source columns
        """
        # Try to auto-detect common column patterns
        mapping = {}

        # Look for country column
        country_cols = [col for col in df.columns if 'country' in col.lower()]
        if country_cols:
            mapping['country'] = country_cols[0]

        # Look for date/year column
        date_cols = [col for col in df.columns if any(x in col.lower() for x in ['year', 'date', 'time'])]
        if date_cols:
            mapping['year'] = date_cols[0]

        # Look for antibiotic consumption columns
        consumption_cols = [col for col in df.columns if any(x in col.lower() for x in ['ddd', 'consumption', 'use', 'usage'])]
        if consumption_cols:
            mapping['ddd'] = consumption_cols[0]

        # Look for pathogen columns
        pathogen_cols = [col for col in df.columns if any(x in col.lower() for x in ['pathogen', 'organism', 'bacteria'])]
        if pathogen_cols:
            mapping['pathogen'] = pathogen_cols[0]

        # Look for antibiotic columns
        antibiotic_cols = [col for col in df.columns if any(x in col.lower() for x in ['antibiotic', 'drug', 'agent'])]
        if antibiotic_cols:
            mapping['antibiotic'] = antibiotic_cols[0]

        # Look for resistance columns
        resistance_cols = [col for col in df.columns if any(x in col.lower() for x in ['resistant', 'resistance', 'percent'])]
        if resistance_cols:
            mapping['percent_resistant'] = resistance_cols[0]

        # Look for tested count columns
        tested_cols = [col for col in df.columns if any(x in col.lower() for x in ['test', 'isolat', 'n=']) and not any(x in col.lower() for x in ['resist'])]
        if tested_cols:
            mapping['tested'] = tested_cols[0]

        logger.debug(f"ResistanceMap column mapping: {mapping}")
        return mapping

    def _apply_standard_schema(self, df: pd.DataFrame, mapping: Dict) -> pd.DataFrame:
        """
        Apply standardized schema to ResistanceMap data.

        Args:
            df: Raw DataFrame
            mapping: Column mapping dictionary

        Returns:
            DataFrame in unified AMR schema
        """
        standardized_data = []

        for _, row in df.iterrows():
            try:
                record = {
                    'date': pd.to_datetime(str(row.get(mapping.get('year', '2023'), '2023')), format='%Y', errors='coerce'),
                    'country': row.get(mapping.get('country', ''), ''),
                    'country_name': row.get(mapping.get('country', ''), ''),
                    'region': self._get_country_region(row.get(mapping.get('country', ''), '')),
                    'pathogen': self._standardize_pathogen(row.get(mapping.get('pathogen', ''), 'E. coli')),
                    'antibiotic': row.get(mapping.get('antibiotic', ''), ''),
                    'resistant': row.get(mapping.get('resistant', 0), 0),
                    'tested': row.get(mapping.get('tested', 0), 0),
                    'percent_resistant': row.get(mapping.get('percent_resistant', 0.0), 0.0),
                    'ddd': row.get(mapping.get('ddd', 0), 0),
                    'source': 'ResistanceMap',
                    'data_quality_score': 0.8,  # Generally high quality CDDEP data
                    'last_updated': datetime.now().isoformat()
                }

                # Calculate resistance percentage if missing
                if record['percent_resistant'] == 0.0 and record['resistant'] > 0 and record['tested'] > 0:
                    record['percent_resistant'] = (record['resistant'] / record['tested']) * 100

                standardized_data.append(record)

            except Exception as e:
                logger.warning(f"Failed to process ResistanceMap row: {e}")
                continue

        return pd.DataFrame(standardized_data)

    def _standardize_pathogen(self, pathogen: str) -> str:
        """Standardize pathogen names from ResistanceMap."""
        if not pathogen or str(pathogen).lower() == 'nan':
            return 'E. coli'  # Most common in ResistanceMap

        pathogen_mapping = {
            'E. coli': 'Escherichia coli',
            'Escherichia coli': 'Escherichia coli',
            'K. pneumoniae': 'Klebsiella pneumoniae',
            'Klebsiella pneumoniae': 'Klebsiella pneumoniae',
            'Salmonella': 'Salmonella spp.',
            'Salmonella spp': 'Salmonella spp.',
            'S. aureus': 'Staphylococcus aureus',
            'Staphylococcus aureus': 'Staphylococcus aureus'
        }

        return pathogen_mapping.get(str(pathogen).strip(), str(pathogen).strip())

    def _get_country_region(self, country: str) -> str:
        """Get WHO region for country."""
        region_mapping = {
            'USA': 'Americas', 'Canada': 'Americas', 'Mexico': 'Americas',
            'Brazil': 'Americas', 'Argentina': 'Americas', 'Chile': 'Americas',
            'UK': 'Europe', 'Germany': 'Europe', 'France': 'Europe',
            'Italy': 'Europe', 'Spain': 'Europe', 'Netherlands': 'Europe',
            'Japan': 'Western Pacific', 'China': 'Western Pacific',
            'Australia': 'Western Pacific', 'South Korea': 'Western Pacific',
            'India': 'South East Asia', 'Thailand': 'South East Asia',
            'Indonesia': 'South East Asia', 'Philippines': 'South East Asia',
            'Nigeria': 'Africa', 'South Africa': 'Africa', 'Kenya': 'Africa',
            'Egypt': 'Eastern Mediterranean', 'Turkey': 'Europe',
            'Saudi Arabia': 'Eastern Mediterranean', 'Iran': 'Eastern Mediterranean'
        }

        return region_mapping.get(str(country).strip(), 'Unknown')

    def get_resistancemap_data(self) -> pd.DataFrame:
        """
        Main method to retrieve ResistanceMap data.

        Returns:
            DataFrame with standardized ResistanceMap AMR data
        """
        logger.info("Retrieving ResistanceMap AMR data")

        # Try to find manually downloaded data first
        df = self.fetch_resistancemap_manual_download()

        if df is not None and not df.empty:
            logger.info(f"Successfully loaded {len(df)} records from ResistanceMap")
            return df

        # Fallback: show download instructions
        self._show_download_instructions()
        return pd.DataFrame()

    def _show_download_instructions(self):
        """Display instructions for manual ResistanceMap download."""
        print("""
🔍 RESISTANCEMAP MANUAL DOWNLOAD REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ResistanceMap (CDDEP) doesn't currently provide a direct API.
Please manually download the data:

🖥️ STEPS:
1. Go to: https://resistancemap.cddep.org/ConsumptionData
2. Select filters: All countries, all antibiotics, all years
3. Click "Export" button (CSV format)
4. Save file as: data/resistancemap_raw.csv
5. Re-run the extraction script

📋 ALTERNATIVE:
• Visit: https://resistancemap.cddep.org/AntibioticResistance
• Export resistance data using same process
• Save as: data/resistancemap_resistance.csv

⚡ ONCE DOWNLOADED:
The script will automatically detect and process the file,
then merge it with WHO GLASS and CDC data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)

    # Compatibility methods for the extraction pipeline
    def get_all_data(self) -> pd.DataFrame:
        """Get all available ResistanceMap data (for pipeline compatibility)."""
        return self.get_resistancemap_data()

    def get_recent_data(self, since_date: str) -> pd.DataFrame:
        """Get recent data since specified date (ResistanceMap is annual, so return all)."""
        df = self.get_resistancemap_data()
        if not df.empty and since_date:
            try:
                since_datetime = pd.to_datetime(since_date)
                df = df[df['date'] >= since_datetime]
            except:
                pass
        return df


def main():
    """Example usage and testing of ResistanceMap connector."""

    # Initialize connector
    connector = ResistanceMapConnector()

    print("🔬 Testing ResistanceMap Data Connection...")

    # Try to retrieve data
    print("\n📊 Fetching ResistanceMap AMR data...")
    data = connector.get_resistancemap_data()

    if not data.empty:
        print(f"✅ Retrieved {len(data)} ResistanceMap records")

        # Show sample data
        print("\n📈 Sample ResistanceMap Data:")
        sample = data.head(3)
        for _, row in sample.iterrows():
            country = row.get('country', 'Unknown')
            pathogen = row.get('pathogen', 'Unknown')
            antibiotic = row.get('antibiotic', 'Unknown')
            resistance = row.get('percent_resistant', 0)
            ddd = row.get('ddd', 0)
            print(f"• {country}: {pathogen} vs {antibiotic}: {resistance:.1f}% resistant, {ddd} DDD/1000 inhabitants/day")

        # Show summary
        print("
📊 Data Summary:"        print(f"• Countries covered: {data['country'].nunique()}")
        print(f"• Antibiotics tracked: {data['antibiotic'].nunique()}")

        # Save sample
        sample_file = "../../outputs/resistancemap_sample.csv"
        data.head(100).to_csv(sample_file, index=False)
        print(f"\n💾 Saved sample to: {sample_file}")

    else:
        print("📥 No ResistanceMap data found locally.")
        connector._show_download_instructions()

    print("\n✅ ResistanceMap connector test completed!")


if __name__ == "__main__":
    main()
