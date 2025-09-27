#!/usr/bin/env python3
"""
CDC Antimicrobial Resistance (AR) Data Connector

Connects to US Centers for Disease Control and Prevention databases for AMR surveillance:
- National Antimicrobial Resistance Monitoring System (NARMS)
- Antibiotic Resistance (AR) Lab Network data
- CDC environmental isolate collections

Data: Foodborne, clinical, and environmental pathogen resistance testing.
Format: API access via Socrata, CSV, and XML endpoints.
Access: Public APIs and data.cdc.gov platforms.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import logging
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

# Try importing Socrata API client
try:
    from sodapy import Socrata
    SODA_AVAILABLE = True
except ImportError:
    SODA_AVAILABLE = False
    logging.warning("Socrata API client not available. Install with: pip install sodapy")

logger = logging.getLogger(__name__)

class CDCConnector:
    """
    Comprehensive connector to CDC antimicrobial resistance databases.

    Features:
    - NARMS foodborne pathogen surveillance
    - CDC AR Isolate Bank data
    - National AR Lab Network data
    - Automated data quality validation
    - Real-time threshold alerts
    """

    def __init__(self, config_path: str = "../config/data_sources.yml"):
        """
        Initialize CDC connector with API credentials.

        Args:
            config_path: Path to API credentials configuration
        """
        # CDC API endpoints (no authentication required for public data)
        self.base_url = "https://data.cdc.gov/resource"
        self.narms_endpoint = f"{self.base_url}/eci2-5tkr.json"  # NARMS retail meat data
        self.ar_lab_endpoint = f"{self.base_url}/eci2-5tkr.json"  # AR Lab Network
        self.isolate_bank_endpoint = f"{self.base_url}"  # Isolate Bank (when available)

        # Public domain identifiers for CDC datasets
        self.dataset_ids = {
            'narms_retail': '4jje-kehk',  # Retail meat NARMS data
            'narms_integrated': '4nfx-sxau',  # Integrated NARMS data
            'ar_lab_network': 'mff5-ku3e',  # Antibiotic Resistance Lab Network
        }

        self.rate_limit_delay = 1.0  # Respect CDC API limits
        self.max_records_per_request = 50000  # CDC API limit

        logger.info("CDC AMR connector initialized")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=60))
    def _make_request(self, url: str, params: Dict = None) -> List[Dict]:
        """
        Make request to CDC API with retry logic and rate limiting.

        Args:
            url: API endpoint URL
            params: Query parameters including $limit, $offset for pagination

        Returns:
            List of JSON records
        """
        import time
        time.sleep(self.rate_limit_delay)  # Rate limiting

        headers = {
            'User-Agent': 'Global-AMR-System/1.0 (Public Health Research)',
            'Accept': 'application/json',
            'X-App-Token': None  # Public data, no token needed
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                logger.info(f"Retrieved {len(data) if isinstance(data, list) else 1} records from CDC")
                return data if isinstance(data, list) else [data]
            else:
                logger.warning(f"Non-JSON response from CDC API: {response.text[:200]}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"CDC API request failed: {e}")
            raise

    def get_narms_data(self, pathogen: str = None, antibiotic: str = None,
                      start_year: int = None, end_year: int = None) -> pd.DataFrame:
        """
        Retrieve NARMS (National Antimicrobial Resistance Monitoring System) data.

        Args:
            pathogen: Specific pathogen (e.g., 'E. coli', 'Salmonella')
            antibiotic: Specific antibiotic class
            start_year: Start year for data range
            end_year: End year for data range

        Returns:
            DataFrame with NARMS resistance data
        """

        # Build SoQL query for CDC API
        where_clause = []
        select_fields = [
            'year',
            'serotype',
            'isolate_type',
            'antibiotic',
            'ddda',
            'percent_resistant',
            'number_resistant',
            'number_tested'
        ]

        if pathogen and pathogen.lower() != 'all':
            if 'coli' in pathogen.lower():
                where_clause.append("lower(serotype) like '%coli%'")
            elif 'salmonella' in pathogen.lower():
                where_clause.append("lower(serotype) like '%salmonella%'")
            else:
                where_clause.append(f"lower(serotype) like '%{pathogen.lower()}%'")

        if antibiotic and antibiotic.lower() != 'all':
            where_clause.append(f"lower(antibiotic) like '%{antibiotic.lower()}%'")

        if start_year:
            where_clause.append(f"year >= {start_year}")
        if end_year:
            where_clause.append(f"year <= {end_year}")

        # Pagination handling for large datasets
        all_records = []
        offset = 0

        while True:
            params = {
                '$select': ','.join(select_fields),
                '$order': 'year DESC, serotype',
                '$limit': self.max_records_per_request,
                '$offset': offset
            }

            if where_clause:
                params['$where'] = ' AND '.join(where_clause)

            url = f"{self.base_url}/{self.dataset_ids['narms_retail']}.json"
            batch_data = self._make_request(url, params)

            if not batch_data:
                break

            all_records.extend(batch_data)
            offset += len(batch_data)

            # Safety limit to prevent infinite loops
            if offset > 500000:  # Max 500k records
                logger.warning("Reached maximum record limit (500k)")
                break

            # CDC API pagination safety
            if len(batch_data) < self.max_records_per_request:
                break

        logger.info(f"Retrieved {len(all_records)} NARMS records")

        if not all_records:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Data harmonization
        df['date'] = pd.to_datetime(df['year'].astype(str) + '-01-01')
        df['year'] = df['year'].astype(int)
        df['country'] = 'USA'
        df['country_name'] = 'United States'
        df['region'] = 'North America'
        df['source'] = 'CDC_NARMS'

        # Standardize pathogen names
        df['pathogen'] = df['serotype'].apply(self._standardize_narms_pathogen)
        df['antibiotic'] = df['antibiotic'].str.strip()

        # Calculate resistance metrics
        df['tested'] = pd.to_numeric(df['number_tested'], errors='coerce').fillna(0).astype(int)
        df['resistant'] = pd.to_numeric(df['number_resistant'], errors='coerce').fillna(0).astype(int)

        # Use provided percentage or calculate it
        if 'percent_resistant' in df.columns:
            df['percent_resistant'] = pd.to_numeric(df['percent_resistant'], errors='coerce').fillna(0.0)
        else:
            df['percent_resistant'] = (df['resistant'] / df['tested'] * 100).round(1).fillna(0.0)

        # Quality scoring
        df['data_quality_score'] = df.apply(self._calculate_cdc_quality_score, axis=1)

        # Select standardized columns
        standardized_df = df[[
            'date', 'year', 'country', 'country_name', 'region', 'pathogen',
            'antibiotic', 'resistant', 'tested', 'percent_resistant',
            'source', 'data_quality_score'
        ]].copy()

        standardized_df['last_updated'] = datetime.now().isoformat()

        return standardized_df

    def get_ar_lab_network_data(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Retrieve data from CDC Antibiotic Resistance Lab Network.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with AR Lab Network surveillance data
        """

        params = {
            '$select': 'test_date,organism,antibiotic,interpretation,sample_type,facility_location',
            '$order': 'test_date DESC',
            '$limit': self.max_records_per_request
        }

        where_clause = []
        if start_date:
            where_clause.append(f"test_date >= '{start_date}'")
        if end_date:
            where_clause.append(f"test_date <= '{end_date}'")

        if where_clause:
            params['$where'] = ' AND '.join(where_clause)

        url = f"{self.base_url}/mff5-ku3e.json"  # AR Lab Network dataset

        try:
            data = self._make_request(url, params)

            if not data:
                logger.warning("No AR Lab Network data retrieved")
                return pd.DataFrame()

            df = pd.DataFrame(data)

            # Data harmonization for AR Lab Network
            df['date'] = pd.to_datetime(df['test_date'], errors='coerce')
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            df['year'] = pd.to_datetime(df['test_date'], errors='coerce').dt.year
            df['country'] = 'USA'
            df['country_name'] = 'United States'
            df['region'] = 'North America'
            df['pathogen'] = df['organism'].apply(self._standardize_ar_lab_pathogen)
            df['antibiotic'] = df['antibiotic'].str.strip()
            df['source'] = 'CDC_AR_LAB'

            # Convert interpretation to resistance metrics
            df['is_resistant'] = df['interpretation'].str.lower().isin(['resistant', 'intermediate'])
            df_grouped = df.groupby(['date', 'pathogen', 'antibiotic']).agg({
                'is_resistant': ['count', 'sum']
            }).reset_index()

            # Flatten multi-level columns
            df_grouped.columns = ['date', 'pathogen', 'antibiotic', 'tested', 'resistant']
            df_grouped['percent_resistant'] = (df_grouped['resistant'] / df_grouped['tested'] * 100).round(1)

            # Re-add metadata columns
            df_grouped['country'] = 'USA'
            df_grouped['country_name'] = 'United States'
            df_grouped['region'] = 'North America'
            df_grouped['source'] = 'CDC_AR_LAB'
            df_grouped['data_quality_score'] = 0.9  # High quality lab data
            df_grouped['last_updated'] = datetime.now().isoformat()

            logger.info(f"Processed {len(df_grouped)} AR Lab Network resistance summaries")
            return df_grouped

        except Exception as e:
            logger.error(f"Failed to retrieve AR Lab Network data: {e}")
            return pd.DataFrame()

    def _standardize_narms_pathogen(self, pathogen: str) -> str:
        """Standardize NARMS pathogen nomenclature."""
        pathogen_maps = {
            'Escherichia coli': 'Escherichia coli',
            'E. coli': 'Escherichia coli',
            'Salmonella': 'Salmonella spp.',
            'Salmonella enterica': 'Salmonella spp.',
            'Salmonella Heidelberg': 'Salmonella Heidelberg',
            'Salmonella Typhimurium': 'Salmonella Typhimurium',
            'Salmonella Enteritidis': 'Salmonella Enteritidis',
            'Campylobacter': 'Campylobacter spp.',
            'Campylobacter jejuni': 'Campylobacter jejuni',
            'Campylobacter coli': 'Campylobacter coli'
        }

        pathogen_clean = pathogen.strip() if pathogen else ''
        return pathogen_maps.get(pathogen_clean, pathogen_clean)

    def _standardize_ar_lab_pathogen(self, pathogen: str) -> str:
        """Standardize AR Lab Network pathogen nomenclature."""
        pathogen_maps = {
            'ESCHERICHIA COLI': 'Escherichia coli',
            'KLEBSIELLA PNEUMONIAE': 'Klebsiella pneumoniae',
            'PSEUDOMONAS AERUGINOSA': 'Pseudomonas aeruginosa',
            'ACINETOBACTER BAUMANNII': 'Acinetobacter baumannii',
            'STAPHYLOCOCCUS AUREUS': 'Staphylococcus aureus',
            'ENTEROCOCCUS FAECALIS': 'Enterococcus faecalis',
            'ENTEROCOCCUS FAECIUM': 'Enterococcus faecium'
        }

        pathogen_upper = pathogen.upper().strip() if pathogen else ''
        return pathogen_maps.get(pathogen_upper, pathogen.title())

    def _calculate_cdc_quality_score(self, row) -> float:
        """Calculate data quality score for CDC NARMS data."""
        score = 0.5  # Base score

        # Higher score for recent data
        if hasattr(row, 'year') and row['year'] >= 2020:
            score += 0.2

        # Higher score if DDD data available
        if hasattr(row, 'ddda') and pd.notna(row['ddda']):
            score += 0.1

        # Higher score if explicit resistance percentage provided
        if hasattr(row, 'percent_resistant') and pd.notna(row['percent_resistant']):
            score += 0.1

        # Lower score if no isolates tested
        if hasattr(row, 'tested') and row['tested'] <= 10:
            score -= 0.2

        return min(1.0, max(0.0, score))

    def get_all_data(self) -> pd.DataFrame:
        """
        Retrieve comprehensive AMR data from all CDC sources.

        This is the main method called by the ingestion pipeline.

        Returns:
            Unified DataFrame with all CDC AMR data
        """
        all_dataframes = []

        # Get NARMS Retail Meat Data
        logger.info("Retrieving CDC NARMS data...")
        narms_df = self.get_narms_data(start_year=2010)
        if not narms_df.empty:
            all_dataframes.append(narms_df)

        # Get AR Lab Network Data
        logger.info("Retrieving CDC AR Lab Network data...")
        ar_lab_df = self.get_ar_lab_network_data()
        if not ar_lab_df.empty:
            all_dataframes.append(ar_lab_df)

        if not all_dataframes:
            logger.warning("No data retrieved from any CDC sources")
            return pd.DataFrame()

        # Combine all CDC data
        combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)

        # Remove duplicates (same pathogen + antibiotic + date + location)
        duplicate_cols = ['pathogen', 'antibiotic', 'date', 'country']
        combined_df = combined_df.drop_duplicates(subset=duplicate_cols, keep='first')

        # Sort by date descending (most recent first)
        combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce')
        combined_df = combined_df.sort_values(['date', 'pathogen', 'antibiotic'], ascending=[False, True, True])

        logger.info(f"CDC data collection complete: {len(combined_df)} total records")
        return combined_df

    def get_recent_data(self, since_date: str) -> pd.DataFrame:
        """
        Retrieve only recent CDC data since specified date.

        Args:
            since_date: Date string in ISO format

        Returns:
            DataFrame with recent AMR data
        """
        try:
            since_datetime = datetime.fromisoformat(since_date.replace('Z', '+00:00'))
            start_date_str = since_datetime.strftime('%Y-%m-%d')

            # Get NARMS data from the specified date onward
            narms_df = self.get_narms_data(start_year=since_datetime.year)

            # Filter to only data after since_date
            if not narms_df.empty:
                narms_df['date_dt'] = pd.to_datetime(narms_df['date'])
                narms_df = narms_df[narms_df['date_dt'] > since_datetime]
                narms_df = narms_df.drop('date_dt', axis=1)

            # Get recent AR Lab network data
            ar_lab_df = self.get_ar_lab_network_data(start_date=start_date_str)

            # Combine results
            recent_dfs = [df for df in [narms_df, ar_lab_df] if not df.empty]

            if not recent_dfs:
                return pd.DataFrame()

            combined_df = pd.concat(recent_dfs, ignore_index=True, sort=False)
            combined_df = combined_df.drop_duplicates(
                subset=['pathogen', 'antibiotic', 'date'], keep='first'
            )

            logger.info(f"Retrieved {len(combined_df)} recent CDC records since {since_date}")
            return combined_df

        except Exception as e:
            logger.error(f"Failed to retrieve recent CDC data: {e}")
            return pd.DataFrame()


def main():
    """Example usage and testing of CDC connector."""

    # Initialize connector
    connector = CDCConnector()

    print("🔬 Testing CDC AMR Data Connection...")

    # Test comprehensive data retrieval
    print("\n🏥 Retrieving comprehensive CDC AMR data...")
    all_data = connector.get_all_data()
    print(f"Retrieved {len(all_data)} total CDC AMR records")

    if not all_data.empty:
        # Show sample data
        print("\n📈 Sample CDC AMR Data:")
        sample = all_data.head(5)
        for _, row in sample.iterrows():
            pathogen = row.get('pathogen', 'Unknown')
            antibiotic = row.get('antibiotic', 'Unknown')
            resistance = row.get('percent_resistant', 0)
            year = row.get('year', 'Unknown')
            print(f"• {pathogen} vs {antibiotic}: {resistance}% resistant ({year})")

        # Show data summary
        print(f"\n📊 Data Summary:")
        print(f"• Date range: {all_data['date'].min()} to {all_data['date'].max()}")
        print(f"• Pathogens covered: {all_data['pathogen'].nunique()}")
        print(f"• Antibiotics tested: {all_data['antibiotic'].nunique()}")
        print(f"• Sources included: {', '.join(all_data['source'].unique())}")

        # Export sample for verification
        sample_file = "../outputs/cdc_amr_sample.csv"
        sample.to_csv(sample_file, index=False)
        print(f"\n💾 Saved sample data to: {sample_file}")

    # Test recent data retrieval
    print("\n📅 Testing recent data retrieval (last 3 months)...")
    three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()
    recent_data = connector.get_recent_data(three_months_ago)
    print(f"Retrieved {len(recent_data)} recent records")

    print("\n✅ CDC AMR connector test completed!")


if __name__ == "__main__":
    main()
