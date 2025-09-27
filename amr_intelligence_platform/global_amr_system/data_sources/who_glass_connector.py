#!/usr/bin/env python3
"""
WHO GLASS (Global Antimicrobial Resistance Surveillance System) API Connector

Connects to WHO's primary global AMR surveillance platform, integrating with:
- GLASS Dashboard API (live surveillance data)
- GLASS Data Portal (historical datasets)
- GLASS Metadata API (code system mappings)
- GLASS Reports API (automated publication data)

Documentation: https://www.who.int/initiatives/glass
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WHOGLASSConnector:
    """
    Comprehensive WHO GLASS API integration for global AMR surveillance data.

    Features:
    - Real-time surveillance data extraction
    - Historical trend analysis datasets
    - Pathogen-antibiotic combination monitoring
    - Geographic coverage across WHO regions
    - Automated data validation and quality checks
    """

    def __init__(self, config_path: str = "../config/data_sources.yml"):
        """
        Initialize WHO GLASS connector with authentication and endpoints.

        Args:
            config_path: Path to configuration file with API credentials
        """
        self.config = self._load_config(config_path)

        # WHO GLASS API Endpoints
        self.base_url = "https://glassapi.who.int/v2/api"
        self.dashboard_url = "https://glassapi.who.int/v2/api/glass"
        self.metadata_url = "https://glassapi.who.int/v2/api/metadata"
        self.reports_url = "https://glassapi.who.int/v2/api/reports"

        # API credentials (if available)
        self.api_key = self.config.get('who_glass', {}).get('api_key')
        self.username = self.config.get('who_glass', {}).get('username')
        self.password = self.config.get('who_glass', {}).get('password')

        # Rate limiting
        self.request_delay = 1.0  # 1 second between requests
        self.last_request_time = datetime.now()

        # Cache for metadata
        self.pathogens_cache = {}
        self.antibiotics_cache = {}
        self.countries_cache = {}

        logger.info("WHO GLASS connector initialized successfully")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration with API credentials."""
        try:
            import yaml
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Configuration file not found: {config_path}")
                return {}
        except ImportError:
            logger.warning("PyYAML not installed, using default configuration")
            return {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, url: str, params: Dict = None, method: str = 'GET') -> Dict:
        """
        Make authenticated request to WHO GLASS API with retry logic.

        Args:
            url: API endpoint URL
            params: Query parameters
            method: HTTP method (GET, POST, etc.)

        Returns:
            JSON response data
        """
        # Rate limiting
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = datetime.now()

        headers = {
            'User-Agent': 'Global-AMR-System/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        # Add authentication if available
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.username and self.password:
            import base64
            auth_string = f"{self.username}:{self.password}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers['Authorization'] = f'Basic {encoded_auth}'

        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
            elif method.upper() == 'POST':
                response = requests.post(url, json=params, headers=headers, timeout=30, verify=False)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            # Handle rate limiting
            if response.status_code == 429:
                logger.warning("Rate limit exceeded, backing off...")
                time.sleep(60)
                raise Exception("Rate limit exceeded")

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"WHO GLASS API request failed: {e}")
            raise

    def get_pathogen_metadata(self) -> Dict[str, Dict]:
        """Get comprehensive pathogen metadata from WHO GLASS."""
        if self.pathogens_cache:
            return self.pathogens_cache

        url = f"{self.metadata_url}/pathogens"
        try:
            data = self._make_request(url)
            pathogens = {}

            for item in data.get('data', []):
                pathogen_id = item.get('pathogen_id')
                pathogens[pathogen_id] = {
                    'name': item.get('pathogen_name', ''),
                    'scientific_name': item.get('scientific_name', ''),
                    'priority_level': item.get('who_priority', 'Unknown'),
                    'esbl_relevant': item.get('esbl_relevant', False),
                    'mrsa_mssa': item.get('mrsa_mssa', ''),
                    'gram_stain': item.get('gram_stain', ''),
                    'last_updated': item.get('updated_at', '')
                }

            self.pathogens_cache = pathogens
            logger.info(f"Retrieved metadata for {len(pathogens)} pathogens")
            return pathogens

        except Exception as e:
            logger.error(f"Failed to retrieve pathogen metadata: {e}")
            return {}

    def get_antibiotic_metadata(self) -> Dict[str, Dict]:
        """Get comprehensive antibiotic metadata from WHO GLASS."""
        if self.antibiotics_cache:
            return self.antibiotics_cache

        url = f"{self.metadata_url}/antibiotics"
        try:
            data = self._make_request(url)
            antibiotics = {}

            for item in data.get('data', []):
                abx_id = item.get('antibiotic_id')
                antibiotics[abx_id] = {
                    'name': item.get('antibiotic_name', ''),
                    'class': item.get('class', ''),
                    'who_class': item.get('who_class', ''),
                    'aware_category': item.get('aware', ''),
                    'reserve': item.get('reserve', False),
                    'access': item.get('access', ''),
                    'watch': item.get('watch', ''),
                    'route': item.get('route', ''),
                    'last_updated': item.get('updated_at', '')
                }

            self.antibiotics_cache = antibiotics
            logger.info(f"Retrieved metadata for {len(antibiotics)} antibiotics")
            return antibiotics

        except Exception as e:
            logger.error(f"Failed to retrieve antibiotic metadata: {e}")
            return {}

    def get_country_metadata(self) -> Dict[str, Dict]:
        """Get country/territory metadata for geographic analysis."""
        if self.countries_cache:
            return self.countries_cache

        url = f"{self.metadata_url}/countries"
        try:
            data = self._make_request(url)
            countries = {}

            for item in data.get('data', []):
                countries[item.get('country_code')] = {
                    'name': item.get('country_name', ''),
                    'region': item.get('who_region', ''),
                    'income_level': item.get('income_group', ''),
                    'population': item.get('population', 0),
                    'gdp_per_capita': item.get('gdp_per_capita', 0),
                    'latitude': item.get('latitude', 0),
                    'longitude': item.get('longitude', 0)
                }

            self.countries_cache = countries
            logger.info(f"Retrieved metadata for {len(countries)} countries")
            return countries

        except Exception as e:
            logger.error(f"Failed to retrieve country metadata: {e}")
            return {}

    def get_surveillance_data(self,
                             pathogen: str = None,
                             antibiotic: str = None,
                             country: str = None,
                             start_year: int = None,
                             end_year: int = None,
                             data_type: str = 'resistance') -> pd.DataFrame:
        """
        Retrieve surveillance data from WHO GLASS dashboard API.

        Args:
            pathogen: Specific pathogen name (optional filter)
            antibiotic: Specific antibiotic name (optional filter)
            country: Country code for regional data (optional)
            start_year: Start year for data range
            end_year: End year for data range
            data_type: Type of data ('resistance', 'consumption', 'both')

        Returns:
            DataFrame with AMR surveillance data
        """

        params = {
            'data_type': data_type,
            'format': 'json',
            'latest_only': 'false'
        }

        if pathogen:
            params['pathogen'] = pathogen
        if antibiotic:
            params['antibiotic'] = antibiotic
        if country:
            params['country'] = country
        if start_year:
            params['start_year'] = str(start_year)
        if end_year:
            params['end_year'] = str(end_year)

        url = f"{self.dashboard_url}/surveillance"
        logger.info(f"Requesting surveillance data with params: {params}")

        try:
            response = self._make_request(url, params)
            records = []

            for item in response.get('data', []):
                record = {
                    'pathogen': item.get('pathogen_name', ''),
                    'antibiotics': item.get('antibiotic_name', ''),
                    'country': item.get('country_name', ''),
                    'country_code': item.get('country_code', ''),
                    'region': item.get('who_region', ''),
                    'year': item.get('year', ''),
                    'quarter': item.get('quarter', ''),
                    'tested': item.get('no_tested', 0),
                    'resistant': item.get('no_resistant', 0),
                    'resistance_percent': item.get('resistance_percent', 0.0),
                    'confidence_interval_lower': item.get('ci_lower', 0.0),
                    'confidence_interval_upper': item.get('ci_upper', 0.0),
                    'methodology': item.get('methodology', ''),
                    'source': 'WHO GLASS',
                    'data_quality_score': item.get('quality_score', 0),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                records.append(record)

            df = pd.DataFrame(records)

            if not df.empty:
                # Data quality filtering
                df = df[df['data_quality_score'] > 0.7]  # Only high-quality data
                df['date'] = pd.to_datetime(df['year'].astype(str) + '-01-01')
                logger.info(f"Retrieved {len(df)} high-quality AMR records")

            return df

        except Exception as e:
            logger.error(f"Failed to retrieve surveillance data: {e}")
            return pd.DataFrame()

    def get_regional_summaries(self, year: int = None) -> pd.DataFrame:
        """
        Get regional AMR summaries by WHO region.

        Args:
            year: Specific year for regional analysis (default: latest)

        Returns:
            DataFrame with regional AMR summaries
        """
        if not year:
            year = datetime.now().year - 1  # Previous year

        url = f"{self.reports_url}/regional-summary/{year}"
        logger.info(f"Retrieving regional AMR summaries for {year}")

        try:
            response = self._make_request(url)
            regions_data = []

            for region_data in response.get('regional_data', []):
                record = {
                    'region': region_data.get('who_region', ''),
                    'year': year,
                    'total_isolates_tested': region_data.get('total_tested', 0),
                    'key_pathogen_resistance': region_data.get('key_resistance_rates', {}),
                    'emerging_resistance': region_data.get('emerging_patterns', []),
                    'action_required': region_data.get('priorities', []),
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                regions_data.append(record)

            return pd.DataFrame(regions_data)

        except Exception as e:
            logger.error(f"Failed to retrieve regional summaries: {e}")
            return pd.DataFrame()

    def get_emerging_resistance_alerts(self) -> List[Dict]:
        """
        Get real-time alerts for emerging resistance patterns.

        Returns:
            List of alert dictionaries with severity and details
        """
        url = f"{self.dashboard_url}/emerging-threats"

        try:
            response = self._make_request(url)
            alerts = []

            for alert in response.get('alerts', []):
                alert_record = {
                    'alert_id': alert.get('id', ''),
                    'severity': alert.get('severity', 'medium'),
                    'pathogen': alert.get('pathogen', ''),
                    'antibiotic': alert.get('antibiotic', ''),
                    'country': alert.get('country', ''),
                    'resistance_rate': alert.get('current_resistance', 0),
                    'trend': alert.get('trend', 'stable'),
                    'detection_date': alert.get('detected', ''),
                    'recommended_action': alert.get('action_required', ''),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                alerts.append(alert_record)

            logger.info(f"Retrieved {len(alerts)} emerging resistance alerts")
            return alerts

        except Exception as e:
            logger.error(f"Failed to retrieve emerging resistance alerts: {e}")
            return []

    def export_data(self, df: pd.DataFrame, output_path: str, format: str = 'csv'):
        """
        Export retrieved data to specified format.

        Args:
            df: DataFrame to export
            output_path: Output file path
            format: Export format ('csv', 'json', 'parquet')
        """
        try:
            output_file = Path(output_path)

            if format.lower() == 'csv':
                df.to_csv(output_file, index=False, date_format='%Y-%m-%d')
            elif format.lower() == 'json':
                df.to_json(output_file, orient='records', date_format='%Y-%m-%d')
            elif format.lower() == 'parquet':
                df.to_parquet(output_file, index=False)

            logger.info(f"Exported {len(df)} records to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False


def main():
    """Example usage and testing of WHO GLASS connector."""

    # Initialize connector
    connector = WHOGLASSConnector()

    print("🔬 Testing WHO GLASS API Connection...")

    # Test metadata retrieval
    print("\n📊 Retrieving pathogen metadata...")
    pathogens = connector.get_pathogen_metadata()
    print(f"Found {len(pathogens)} pathogens in WHO GLASS system")

    # Test surveillance data
    print("\n🏥 Retrieving AMR surveillance data...")
    amr_data = connector.get_surveillance_data(
        country='IND',  # India
        start_year=2020,
        end_year=2023
    )
    print(f"Retrieved {len(amr_data)} AMR records from India")

    if not amr_data.empty:
        # Show sample data
        print("\n📈 Sample AMR Data:")
        print(amr_data[['pathogen', 'antibiotics', 'resistance_percent', 'country']].head())

        # Export sample
        export_path = "../outputs/who_glass_sample.csv"
        connector.export_data(amr_data.head(100), export_path)

    # Test emerging threats
    print("\n🚨 Checking for emerging resistance threats...")
    alerts = connector.get_emerging_resistance_alerts()
    print(f"Found {len(alerts)} active resistance alerts")

    if alerts:
        print(f"Latest alert: {alerts[0].get('pathogen')} - {alerts[0].get('severity')} priority")

    print("\n✅ WHO GLASS connector test completed!")


if __name__ == "__main__":
    main()
