#!/usr/bin/env python3
"""
AMR Temporal-Spatial Animation Module

Creates dynamic visualizations showing AMR resistance spread over time and space.
Generates animated GIF/MP4 time-lapse sequences that combine temporal forecasting
with geographic epidemiology for powerful spatio-temporal intelligence.

Features:
- Time-lapse animations of resistance evolution
- Historical to forecasted resistance mapping
- Frame-by-frame geographic visualization
- Policy scenario animation comparisons
- Presentation-ready animated formats

Capabilities:
- GIF animations (.gif)
- Video format (.mp4)
- Configurable time steps and horizons
- Multiple countries/regions supported
- Sensitivity scenario animations
"""

import pandas as pd
import geopandas as gpd
from prophet import Prophet
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import imageio.v2 as imageio  # Updated import for v2
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import warnings

logger = logging.getLogger(__name__)

class AMRAnimationMapper:
    """
    Spatio-temporal AMR visualization engine.

    Creates time-lapse animations showing resistance patterns evolving
    through historical data and forecasted trends across geographic regions.
    """

    def __init__(self, data_file: str = "data/amr_merged.csv",
                 shapefile_dir: str = "data/shapefiles",
                 reports_dir: str = "reports"):
        """
        Initialize animation mapper.

        Args:
            data_file: Path to unified AMR dataset
            shapefile_dir: Directory containing geographic shapefiles
            reports_dir: Output directory for animations
        """
        self.data_file = Path(data_file)
        self.shapefile_dir = Path(shapefile_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True, parents=True)

        # Animation parameters
        self.default_fps = 2  # frames per second
        self.default_step = 12  # months between frames
        self.quality_settings = {
            'fast': {'fps': 3, 'step': 24, 'format': 'gif'},
            'standard': {'fps': 2, 'step': 12, 'format': 'gif'},
            'high_quality': {'fps': 1, 'step': 6, 'format': 'mp4'}
        }

        logger.info("AMR Animation Mapper initialized")

    def create_temporal_animation(self, country: str, pathogen: str, antibiotic: str,
                                horizon: int = 60, step: int = 12,
                                quality: str = 'standard') -> Dict[str, str]:
        """
        Create full temporal animation from historical through forecasted resistance.

        Args:
            country: Country name
            pathogen, antibiotic: AMR combination
            horizon: Months to forecast into future
            step: Months between animation frames
            quality: Animation quality ('fast', 'standard', 'high_quality')

        Returns:
            Dictionary with paths to generated animations
        """
        logger.info(f"Creating temporal animation for {country} | {pathogen} | {antibiotic}")
        logger.info(f"Horizon: {horizon} months, Step: {step} months, Quality: {quality}")

        # Load and process data
        amr_data = self._load_amr_data(country, pathogen, antibiotic)
        if amr_data.empty:
            return {}

        # Get shapefile for mapping
        shapefile = self._get_shapefile(country)
        if shapefile is None:
            return {}

        # Generate forecasts for each region
        region_forecasts = self._generate_region_forecasts(amr_data, horizon)

        # Create animation frames
        quality_settings = self.quality_settings[quality]
        fps = quality_settings['fps']
        animation_step = quality_settings.get('step', step)

        frame_files = self._create_animation_frames(
            country, pathogen, antibiotic, region_forecasts,
            shapefile, horizon, animation_step
        )

        if not frame_files:
            return {}

        # Create animations
        outputs = {}

        # GIF format (always created)
        gif_path = f"amr_animation_{country}_{pathogen}_{antibiotic}.gif"
        logger.info(f"Creating GIF animation with {len(frame_files)} frames...")
        imageio.mimsave(self.reports_dir / gif_path, frame_files, fps=fps, loop=0)
        outputs['gif'] = str(self.reports_dir / gif_path)

        # MP4 format (only for high quality)
        if quality == 'high_quality':
            mp4_path = gif_path.replace('.gif', '.mp4')
            logger.info("Creating MP4 animation...")
            imageio.mimsave(self.reports_dir / mp4_path, frame_files, fps=fps)
            outputs['mp4'] = str(self.reports_dir / mp4_path)

        # Clean up temporary frames
        self._cleanup_frames(frame_files)
        logger.info(f"Animation complete! Files: {list(outputs.values())}")

        return outputs

    def create_scenario_animation(self, country: str, pathogen: str, antibiotic: str,
                               scenarios: Dict[str, float], horizon: int = 60,
                               step: int = 12) -> Dict[str, str]:
        """
        Create comparative animations for different policy scenarios.

        Args:
            scenarios: Dict of scenario names to consumption multipliers

        Returns:
            Dictionary with paths to scenario animations
        """
        scenario_outputs = {}

        for scenario_name, multiplier in scenarios.items():
            logger.info(f"Creating animation for scenario: {scenario_name}")

            # Apply consumption multiplier to forecasts
            scenario_data = self._load_amr_data(country, pathogen, antibiotic)
            if scenario_data.empty:
                continue

            # Modify consumption data (if available) or resistance trend
            if 'ddd' in scenario_data.columns:
                scenario_data['ddd'] = scenario_data['ddd'] * multiplier

            scenario_outputs[scenario_name] = self.create_temporal_animation(
                country, pathogen, antibiotic, horizon, step,
                quality='fast'  # Faster for scenario comparisons
            ).get('gif', '')

        logger.info(f"Scenario animations created: {list(scenario_outputs.keys())}")
        return scenario_outputs

    def _load_amr_data(self, country: str, pathogen: str, antibiotic: str) -> pd.DataFrame:
        """Load and validate AMR data for specified combination."""
        if not self.data_file.exists():
            raise FileNotFoundError(f"AMR data file not found: {self.data_file}")

        df = pd.read_csv(self.data_file)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        subset = df[(df["country"].str.lower() == country.lower()) &
                    (df["pathogen"].str.lower() == pathogen.lower()) &
                    (df["antibiotic"].str.lower() == antibiotic.lower())].dropna(subset=['percent_resistant'])

        if subset.empty:
            logger.warning(f"No data found for {country} | {pathogen} | {antibiotic}")
            return pd.DataFrame()

        if "region" not in subset.columns:
            logger.warning("⚠️ No region information in dataset. Using country-level aggregation.")
            subset['region'] = country

        logger.info(f"Loaded data: {len(subset)} records, {len(subset['region'].unique())} regions")
        return subset

    def _get_shapefile(self, country: str) -> Optional[gpd.GeoDataFrame]:
        """Load appropriate shapefile for country."""
        # Shapefile mapping
        shapefile_configs = {
            'India': 'india_districts.shp',
            'United States': 'us_states.shp',
            'Brazil': 'brazil_states.shp',
            'global': 'world_countries.shp'
        }

        shapefile_name = shapefile_configs.get(country, shapefile_configs['global'])
        shapefile_path = self.shapefile_dir / shapefile_name

        if shapefile_path.exists():
            try:
                gdf = gpd.read_file(shapefile_path)
                logger.info(f"Loaded shapefile: {shapefile_path} ({len(gdf)} regions)")
                return gdf
            except Exception as e:
                logger.error(f"Could not load shapefile: {e}")

        logger.warning(f"No shapefile found for {country} ({shapefile_path})")
        return None

    def _generate_region_forecasts(self, data: pd.DataFrame,
                                 horizon: int = 60) -> Dict[str, pd.Series]:
        """
        Generate time series forecasts for each region.
        """
        forecasts = {}

        for region, group in data.groupby("region"):
            region_data = group[["date", "percent_resistant"]].rename(
                columns={"date": "ds", "percent_resistant": "y"}
            ).dropna()

            if len(region_data) < 6:  # Reasonable minimum for forecasting
                logger.debug(f"Skipping region {region}: insufficient data ({len(region_data)} points)")
                continue

            try:
                # Apply consumption regressor if available
                model = Prophet(
                    yearly_seasonality=True,
                    changepoint_prior_scale=0.05,
                    interval_width=0.95
                )

                # Add consumption data if available
                if 'ddd' in group.columns:
                    consumption_data = group.dropna(subset=['ddd'])
                    if len(consumption_data) > 0:
                        region_data['consumption'] = group.set_index('date')['ddd'].reindex(
                            region_data['ds']
                        ).fillna(method='ffill').fillna(method='bfill')
                        model.add_regressor('consumption')

                model.fit(region_data)

                # Create future dataframe
                future = model.make_future_dataframe(periods=horizon, freq="M")

                # Add future consumption (use last available value)
                if model.extra_regressors and 'consumption' in region_data.columns:
                    last_consumption = region_data['consumption'].fillna(method='ffill').iloc[-1]
                    future['consumption'] = last_consumption

                forecast = model.predict(future)

                # Store forecasted values
                forecasts[region] = forecast.set_index('ds')['yhat']

                logger.debug(f"Generated forecast for {region}: {len(forecast)} months")

            except Exception as e:
                logger.warning(f"Forecast failed for region {region}: {e}")
                continue

        logger.info(f"Generated forecasts for {len(forecasts)} regions")
        return forecasts

    def _create_animation_frames(self, country: str, pathogen: str, antibiotic: str,
                               forecasts: Dict[str, pd.Series], shapefile: gpd.GeoDataFrame,
                               horizon: int, step: int) -> List[str]:
        """
        Create individual animation frames for each time step.
        """
        frame_files = []

        # Get time range
        if forecasts:
            first_forecast = next(iter(forecasts.values()))
            time_index = first_forecast.index

            # Create monthly time steps (historical + forecasted)
            start_date = time_index[0] - pd.DateOffset(months=24)  # Show historical context
            end_date = time_index[-1]
            frame_dates = pd.date_range(start=start_date, end=end_date, freq=f'{step}M')

            logger.info(f"Creating {len(frame_dates)} animation frames")

            for i, current_date in enumerate(frame_dates):
                frame_data = []

                for region, forecast_series in forecasts.items():
                    try:
                        # Get resistance value for current date
                        if current_date in forecast_series.index:
                            value = forecast_series.loc[current_date]
                        elif current_date < forecast_series.index[0]:
                            # Historical: use actual data if available
                            historical_value = self._get_historical_value(
                                self._load_amr_data(country, pathogen, antibiotic),
                                region, current_date
                            )
                            value = historical_value if historical_value is not None else forecast_series.iloc[0]
                        else:
                            # Future: extrapolate from last available
                            value = forecast_series.iloc[-1] if len(forecast_series) > 0 else 50

                        frame_data.append({'region': region, 'resistance': value})

                    except Exception as e:
                        logger.debug(f"Frame data error for {region} at {current_date}: {e}")
                        continue

                if not frame_data:
                    continue

                # Create frame visualization
                frame_df = pd.DataFrame(frame_data)
                frame_file = self._create_single_frame(
                    country, pathogen, antibiotic, frame_df, shapefile,
                    current_date, i, len(frame_dates)
                )

                if frame_file:
                    frame_files.append(frame_file)

        return frame_files

    def _get_historical_value(self, data: pd.DataFrame, region: str,
                           target_date: pd.Timestamp) -> Optional[float]:
        """Get historical resistance value for a specific region and date."""
        try:
            region_data = data[data['region'] == region]
            if region_data.empty:
                return None

            # Find closest available date
            region_data['date_diff'] = abs(region_data['date'] - target_date)
            closest_idx = region_data['date_diff'].idxmin()
            return region_data.loc[closest_idx, 'percent_resistant']

        except Exception as e:
            logger.debug(f"Historical value lookup failed: {e}")
            return None

    def _create_single_frame(self, country: str, pathogen: str, antibiotic: str,
                           frame_data: pd.DataFrame, shapefile: gpd.GeoDataFrame,
                           current_date: pd.Timestamp, frame_idx: int,
                           total_frames: int) -> Optional[str]:
        """
        Create a single animation frame showing resistance at a specific point in time.
        """
        try:
            # Get shapefile merge key
            merge_key = self._get_shapefile_key(country)

            # Merge frame data with geography
            merged_gdf = shapefile.merge(
                frame_data,
                left_on=merge_key,
                right_on='region',
                how='left'
            )

            # Create visualization
            fig, ax = plt.subplots(1, 1, figsize=(12, 9))

            if not merged_gdf['resistance'].isna().all():
                merged_gdf.plot(
                    column='resistance',
                    ax=ax,
                    legend=True,
                    cmap='RdYlGn_r',
                    missing_kwds={'color': 'lightgrey'},
                    edgecolor='black',
                    linewidth=0.3,
                    vmax=100,
                    vmin=0
                )

            # Styling
            date_str = current_date.strftime('%Y-%m')
            is_forecast = "(Predicted)" if current_date > pd.Timestamp.now() else "(Historical)"

            title = f'AMR Evolution: {pathogen} vs {antibiotic} in {country}\n'
            title += f'Period: {date_str} {is_forecast}\n'
            title += f'Frame {frame_idx+1:3d}/{total_frames}'

            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.axis('off')

            # Add resistance scale explanation
            ax.text(0.02, 0.02,
                   f'Resistance Scale:\n• Green: Low (0-20%)\n• Yellow: Moderate (20-50%)\n• Orange: High (50-80%)\n• Red: Critical (80-100%)',
                   transform=ax.transAxes, fontsize=9,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))

            plt.tight_layout()

            # Save frame
            frame_filename = f"frame_{frame_idx:04d}_{current_date.strftime('%Y%m')}.png"
            frame_path = self.reports_dir / frame_filename
            plt.savefig(frame_path, dpi=150, bbox_inches='tight')
            plt.close()

            return str(frame_path)

        except Exception as e:
            logger.error(f"Frame creation failed at {current_date}: {e}")
            plt.close()
            return None

    def _get_shapefile_key(self, country: str) -> str:
        """Get appropriate shapefile merge key for country."""
        key_mappings = {
            'India': 'district',
            'United States': 'state',
            'Brazil': 'state',
            'global': 'country'
        }
        return key_mappings.get(country, 'name')

    def _cleanup_frames(self, frame_files: List[str]):
        """Remove temporary frame files after animation creation."""
        try:
            for frame_file in frame_files:
                Path(frame_file).unlink(missing_ok=True)
            logger.info(f"Cleaned up {len(frame_files)} temporary frame files")
        except Exception as e:
            logger.debug(f"Frame cleanup failed: {e}")

def create_amr_animation(country="India", pathogen="E. coli", antibiotic="Ciprofloxacin",
                       horizon=60, step=12, quality='standard') -> Dict[str, str]:
    """
    Convenience function to create AMR temporal animation.
    """
    mapper = AMRAnimationMapper()
    return mapper.create_temporal_animation(country, pathogen, antibiotic, horizon, step, quality)

if __name__ == "__main__":
    """Command-line interface for animation generation."""

    # Example: Create animation for Indian AME resistance
    outputs = create_amr_animation(
        country="India",
        pathogen="E. coli",
        antibiotic="Ciprofloxacin",
        horizon=60,  # 5 years forecast
        step=12,     # Monthly frames
        quality="standard"
    )

    if outputs:
        print("🎥 AMR Animation Generated!")
        print("=" * 50)
        for format_name, file_path in outputs.items():
            print(f"{format_name.upper()}: {file_path}")
        print("=" * 50)

        # Example scenario comparison
        print("\n🔄 Creating scenario comparison animations...")
        scenarios = {
            'Baseline': 1.0,
            'Reduced_Consumption': 0.8,
            'Increased_Consumption': 1.2
        }

        mapper = AMRAnimationMapper()
        scenario_outs = mapper.create_scenario_animation(
            "India", "E. coli", "Ciprofloxacin", scenarios, 36, 12
        )

        print("🔔 Scenario Animations:")
        for scenario, path in scenario_outs.items():
            print(f"  • {scenario}: {path}")
    else:
        print("❌ Animation creation failed - check data and shapefiles")
