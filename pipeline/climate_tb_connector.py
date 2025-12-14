"""
Climate Change & TB Transmission Analysis for India

This module extracts climate data and integrates it with TB epidemiological data
to analyze climate change impacts on MDR-TB transmission dynamics.

Dr. Siddalingaiah H S - Independent Researcher
"""

import pandas as pd
import numpy as np
import requests
import json
import pickle
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings('ignore')

class ClimateTBConnector:
    """Climate change and TB transmission correlation analysis."""

    def __init__(self):
        self.data_dir = Path('../data')
        self.plots_dir = Path('../plots')
        self.researcher_name = "Dr. Siddalingaiah H S"

        # Climate data sources
        self.climate_sources = {
            'NASA_MERRA2': {
                'url': 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2_MONTHLY',
                'temperature_collection': 'M2TMNXFLX.5.12.4',
                'humidity_collection': 'M2TMNXFLX.5.12.4'
            },
            'ERA5_CDS': {
                'url': 'https://cds.climate.copernicus.eu/api/v2',
                'temperature_dataset': 'reanalysis-era5-single-levels-monthly-means',
                'humidity_dataset': 'reanalysis-era5-single-levels-monthly-means'
            },
            'NOAA_GHCN': {
                'stations_url': 'https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt',
                'daily_url': 'https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_year/{year}.csv.gz'
            }
        }

        # Indian states coordinates (latitude, longitude centers)
        self.india_states = {
            'Maharashtra': (19.6948, 75.0800),
            'Uttar Pradesh': (26.5195, 80.8740),
            'Bihar': (25.0961, 85.3131),
            'West Bengal': (22.9786, 87.7478),
            'Andhra Pradesh': (15.9129, 79.6799),
            'Madhya Pradesh': (22.9734, 78.6569),
            'Tamil Nadu': (11.0142, 78.4000),
            'Rajasthan': (27.0238, 74.2179),
            'Karnataka': (15.3173, 75.7139),
            'Gujarat': (22.3094, 72.2398),
            'Odisha': (20.9517, 85.0985),
            'Telangana': (18.1124, 79.0193),
            'Kerala': (10.8505, 76.2711),
            'Jharkhand': (23.6102, 85.2799),
            'Assam': (26.2006, 92.9376),
            'Punjab': (31.1471, 75.3412),
            'Chhattisgarh': (21.2787, 81.8661),
            'Haryana': (29.0588, 76.0856),
            'Uttarakhand': (30.0668, 79.0193),
            'Himachal Pradesh': (31.1048, 77.1734),
            'Tripura': (23.9408, 91.9882),
            'Meghalaya': (25.4670, 91.3662),
            'Manipur': (24.6637, 93.9063),
            'Nagaland': (26.1584, 94.5624),
            'Goa': (15.2993, 74.1240),
            'Arunachal Pradesh': (28.2180, 94.7278),
            'Mizoram': (23.1645, 92.9376),
            'Sikkim': (27.5330, 88.5122),
            'Delhi': (28.7041, 77.1025),
            'Jammu and Kashmir': (33.7782, 76.5762),
            'Puducherry': (11.9416, 79.8083),
            'Chandigarh': (30.7333, 76.7794),
            'Dadra and Nagar Haveli': (20.1809, 73.0169),
            'Daman and Diu': (20.4283, 72.8397),
            'Lakshadweep': (10.5667, 72.6167)
        }

    def fetch_nasa_power_data(self, lat, lon, start_date='2017-01-01', end_date='2023-12-31'):
        """Fetch climate data from NASA POWER API."""
        print(f"Fetching NASA POWER climate data for coordinates: {lat}, {lon}")

        # Correct NASA POWER API endpoint - use the REST API for point data
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"

        params = {
            "start": start_date.replace('-', ''),
            "end": end_date.replace('-', ''),
            "latitude": lat,
            "longitude": lon,
            "community": "RE",  # Research community
            "parameters": "T2M,PRECTOTCORR,QV2M,RH2M",  # Temperature, Precipitation, Humidity
            "format": "JSON",
            "header": "true"
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Extract daily climate data from NASA POWER format
            climate_data = []
            if 'properties' in data and 'parameter' in data['properties']:
                parameters = data['properties']['parameter']

                # Get all dates
                if 'T2M' in parameters:
                    dates = list(parameters['T2M'].keys())

                    for date in dates:
                        try:
                            record = {
                                'date': date,
                                'temperature_2m': float(parameters['T2M'].get(date, np.nan)),  # °C
                                'total_precipitation': float(parameters.get('PRECTOTCORR', {}).get(date, np.nan)),  # mm/day
                                'specific_humidity_2m': float(parameters.get('QV2M', {}).get(date, np.nan)),  # g/kg
                                'relative_humidity_2m': float(parameters.get('RH2M', {}).get(date, np.nan)),  # %
                                'latitude': lat,
                                'longitude': lon
                            }
                            climate_data.append(record)
                        except (ValueError, KeyError) as e:
                            print(f"Error parsing data for date {date}: {e}")
                            continue

            if climate_data:
                return pd.DataFrame(climate_data)
            else:
                print("No climate data found in NASA POWER response")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error fetching NASA POWER data: {str(e)}")
            return pd.DataFrame()

    def generate_monthly_aggregates(self, daily_data):
        """Convert daily climate data to monthly aggregates."""
        if daily_data.empty:
            return pd.DataFrame()

        # Convert date column to datetime
        daily_data = daily_data.copy()
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        daily_data.set_index('date', inplace=True)

        # Aggregate to monthly
        monthly_data = daily_data.resample('M').agg({
            'temperature_2m': ['mean', 'std', 'min', 'max', lambda x: (x > 25).sum()],  # Hot days count
            'total_precipitation': ['sum', 'std', 'max'],  # Total, variability, max daily
            'specific_humidity_2m': 'mean',
            'relative_humidity_2m': 'mean'
        }).round(2)

        # Flatten column names
        monthly_data.columns = [
            'temp_mean', 'temp_std', 'temp_min', 'temp_max', 'hot_days',
            'precip_total', 'precip_std', 'precip_max',
            'humidity_specific_mean', 'humidity_relative_mean'
        ]

        # Add derived variables
        monthly_data['year'] = monthly_data.index.year
        monthly_data['month'] = monthly_data.index.month
        monthly_data['temp_range'] = monthly_data['temp_max'] - monthly_data['temp_min']
        monthly_data['precip_dry_days'] = (daily_data['total_precipitation'] < 1).groupby(pd.Grouper(freq='M')).sum()
        monthly_data['humidity_critical_days'] = (daily_data['relative_humidity_2m'] > 80).groupby(pd.Grouper(freq='M')).sum()

        return monthly_data.reset_index()

    def extract_state_climate_data(self, state_name):
        """Extract and save climate data for a specific Indian state."""
        print(f"\n=== Extracting Climate Data for {state_name} ===")

        try:
            lat, lon = self.india_states[state_name]
            print(f"Coordinates: {lat}°, {lon}°")

            # Fetch raw daily data
            daily_data = self.fetch_nasa_power_data(lat, lon, '2017-01-01', '2023-12-31')

            if daily_data.empty:
                print(f"No climate data available for {state_name}")
                return pd.DataFrame()

            # Generate monthly aggregates
            monthly_data = self.generate_monthly_aggregates(daily_data)

            if monthly_data.empty:
                print(f"Failed to aggregate data for {state_name}")
                return pd.DataFrame()

            # Add state identifier
            monthly_data['state'] = state_name
            monthly_data['latitude'] = lat
            monthly_data['longitude'] = lon

            # Reorganize columns
            cols_order = ['date', 'state', 'latitude', 'longitude', 'year', 'month',
                         'temp_mean', 'temp_std', 'temp_min', 'temp_max', 'temp_range', 'hot_days',
                         'precip_total', 'precip_std', 'precip_max', 'precip_dry_days',
                         'humidity_specific_mean', 'humidity_relative_mean', 'humidity_critical_days']

            monthly_data = monthly_data[cols_order]

            print(f"Extracted {len(monthly_data)} monthly records for {state_name}")
            print("Sample data:")
            print(monthly_data.head())

            return monthly_data

        except Exception as e:
            print(f"Error processing climate data for {state_name}: {str(e)}")
            return pd.DataFrame()

    def create_india_climate_database(self):
        """Generate climate database for all Indian states."""
        print("\n🌡️ BUILDING INDIA CLIMATE DATABASE FOR TB-CLIMATE CORRELATION")
        print(f"Researcher: {self.researcher_name}")

        all_states_climate_data = []

        # Process states by priority (high TB burden first)
        high_priority_states = [
            'Maharashtra', 'Uttar Pradesh', 'Bihar', 'West Bengal',
            'Andhra Pradesh', 'Madhya Pradesh', 'Tamil Nadu', 'Rajasthan',
            'Karnataka', 'Gujarat', 'Odisha', 'Telangana', 'Kerala'
        ]

        remaining_states = [s for s in self.india_states.keys() if s not in high_priority_states]

        target_states = high_priority_states + remaining_states[:5]  # Add 5 more

        print(f"Processing {len(target_states)} states with highest TB burden priority...")

        for i, state in enumerate(target_states, 1):
            print(f"\n📍 Processing {i}/{len(target_states)}: {state}")
            state_data = self.extract_state_climate_data(state)

            if not state_data.empty:
                all_states_climate_data.append(state_data)
                print(f"✅ {state}: {len(state_data)} records collected")
            else:
                print(f"❌ {state}: Data extraction failed")

            # Save intermediate progress every 5 states
            if i % 5 == 0 or i == len(target_states):
                temp_all = pd.concat(all_states_climate_data, ignore_index=True) if all_states_climate_data else pd.DataFrame()
                if not temp_all.empty:
                    climate_file = self.data_dir / 'india_climate_tb_study.csv'
                    temp_all.to_csv(climate_file, index=False)
                    print(f"\n💾 Interim save: {len(temp_all)} records from {i} states")

        # Final consolidation
        if all_states_climate_data:
            final_climate_data = pd.concat(all_states_climate_data, ignore_index=True)
            climate_file = self.data_dir / 'india_climate_tb_study_complete.csv'
            final_climate_data.to_csv(climate_file, index=False)

            print("\n🎉 INDIA CLIMATE DATABASE COMPLETED!")
            print(f"📊 Total Records: {len(final_climate_data)}")
            print(f"📅 Date Range: {final_climate_data['date'].min()} to {final_climate_data['date'].max()}")
            print(f"🏛️ States Covered: {final_climate_data['state'].nunique()}")
            print(f"💾 Saved to: {climate_file}")

            # Summary statistics
            summary_stats = final_climate_data.groupby('state').agg({
                'temp_mean': ['mean', 'std', 'min', 'max'],
                'precip_total': 'mean',
                'humidity_relative_mean': 'mean',
                'date': 'count'
            }).round(2)

            summary_file = self.data_dir / 'climate_tb_summary_stats.csv'
            summary_stats.columns = ['temp_avg', 'temp_variability', 'temp_min_hist', 'temp_max_hist',
                                   'avg_precip', 'avg_humidity', 'records_count']
            summary_stats.reset_index().to_csv(summary_file, index=False)

            print(f"📈 Summary statistics saved to {summary_file}")

            return final_climate_data, summary_stats
        else:
            print("❌ No climate data collected successfully")
            return pd.DataFrame(), pd.DataFrame()

    def validate_climate_data_quality(self, climate_data):
        """Validate climate data completeness and quality."""
        if climate_data.empty:
            return {"overall_quality": 0}

        total_records = len(climate_data)
        complete_records = climate_data.dropna().shape[0]
        completeness = round((complete_records / total_records * 100), 1)

        # State-wise coverage
        state_coverage = climate_data.groupby('state').size()
        temporal_coverage = climate_data.groupby(['year', 'month']).size()

        # Climatological plausibility checks
        temp_plausible = ((climate_data['temp_mean'] > -40) &
                         (climate_data['temp_mean'] < 60)).sum() / total_records * 100
        precip_plausible = ((climate_data['precip_total'] >= 0) &
                           (climate_data['precip_total'] < 500)).sum() / total_records * 100
        humidity_plausible = ((climate_data['humidity_relative_mean'] >= 0) &
                             (climate_data['humidity_relative_mean'] <= 100)).sum() / total_records * 100

        quality_report = {
            "overall_quality": completeness,
            "states_covered": climate_data['state'].nunique(),
            "total_records": total_records,
            "complete_records": complete_records,
            "temporal_coverage": {
                "years": len(climate_data['year'].unique()),
                "months_per_year_avg": temporal_coverage.mean()
            },
            "climatological_plausibility": {
                "temperature_plausible_percent": temp_plausible,
                "precipitation_plausible_percent": precip_plausible,
                "humidity_plausible_percent": humidity_plausible
            },
            "data_ranges": {
                "temperature_range": climate_data['temp_mean'].agg(['min', 'max', 'mean', 'std']).round(2).to_dict(),
                "precipitation_range": climate_data['precip_total'].agg(['min', 'max', 'mean', 'std']).round(2).to_dict(),
                "humidity_range": climate_data['humidity_relative_mean'].agg(['min', 'max', 'mean', 'std']).round(2).to_dict()
            }
        }

        print("\n🔍 CLIMATE DATA QUALITY VALIDATION:")
        print(f"📈 Completeness: {quality_report['overall_quality']}%")
        print(f"🏛️ States: {quality_report['states_covered']}")
        print(f"📊 Records: {quality_report['total_records']}")
        print(f"🌡️ Temp Range: {quality_report['data_ranges']['temperature_range']['min']:.1f}-{quality_report['data_ranges']['temperature_range']['max']:.1f}°C")

        return quality_report

def main():
    """Main execution function."""
    climate_connector = ClimateTBConnector()

    print("🌡️🥵 CLIMATE CHANGE & TB TRANSMISSION STUDY")
    print(f"Researcher: {climate_connector.researcher_name}")
    print("=" * 60)

    # Build complete climate database
    climate_data, summary_stats = climate_connector.create_india_climate_database()

    if not climate_data.empty:
        # Validate data quality
        quality_report = climate_connector.validate_climate_data_quality(climate_data)

        # Save validation report
        validation_file = climate_connector.data_dir / 'climate_tb_data_validation.json'
        with open(validation_file, 'w') as f:
            json.dump(quality_report, f, indent=2)

        print(f"\n✅ CLIMATE DATA EXTRACTION COMPLETE")
        print(f"📁 Files generated:")
        print(f"   • india_climate_tb_study_complete.csv")
        print(f"   • climate_tb_summary_stats.csv")
        print(f"   • climate_tb_data_validation.json")
        print(f"\n🎯 Ready for TB transmission correlation analysis!")

    else:
        print("❌ Climate data extraction failed. Check internet connection and try again.")

if __name__ == "__main__":
    main()
