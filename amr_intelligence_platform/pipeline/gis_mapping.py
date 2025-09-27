#!/usr/bin/env python3
"""
AMR Geographic Hotspot Mapping Module

Provides spatial epidemiology capabilities for AMR surveillance:
- Geographic hotspot visualization
- Choropleth maps of resistance distribution
- Regional resistance patterns
- Integration with existing AMR forecasting pipeline

Features:
- Static choropleth maps
- Interactive maps for dashboards
- Multiple geographic scales (district, state, country, global)
- Hotspot identification algorithms
- Color-coded resistance severity levels
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from pathlib import Path
import numpy as np
from typing import Dict, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class AMRGeographicMapper:
    """
    Geographic visualization and hotspot analysis for AMR data.

    Supports multiple mapping levels:
    - District/State level (India, USA, etc.)
    - Country level (global surveillance)
    - Custom geographic aggregations
    """

    def __init__(self, data_file: str = "data/amr_merged.csv",
                 shapefile_dir: str = "data/shapefiles",
                 reports_dir: str = "reports"):
        """
        Initialize geographic mapper.

        Args:
            data_file: Path to unified AMR dataset
            shapefile_dir: Directory containing geographic shapefiles
            reports_dir: Output directory for maps
        """
        self.data_file = Path(data_file)
        self.shapefile_dir = Path(shapefile_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.shapefile_dir.mkdir(exist_ok=True, parents=True)

        # Resistance severity thresholds
        self.resistance_thresholds = {
            'low': {'range': (0, 20), 'color': 'lightgreen', 'label': 'Low Risk (0-20%)'},
            'moderate': {'range': (20, 50), 'color': 'yellow', 'label': 'Moderate Risk (20-50%)'},
            'high': {'range': (50, 80), 'color': 'orange', 'label': 'High Risk (50-80%)'},
            'critical': {'range': (80, 100), 'color': 'red', 'label': 'Critical Risk (80-100%)'}
        }

        logger.info(f"AMR Geographic Mapper initialized with data: {data_file}")

    def load_amr_data(self, country: str = None, pathogen: str = None,
                     antibiotic: str = None, region_col: str = 'region') -> pd.DataFrame:
        """
        Load and process AMR data for mapping.

        Args:
            country: Filter by country
            pathogen: Filter by pathogen
            antibiotic: Filter by antibiotic
            region_col: Column name for geographic regions

        Returns:
            Processed DataFrame ready for mapping
        """
        if not self.data_file.exists():
            raise FileNotFoundError(f"AMR data file not found: {self.data_file}")

        df = pd.read_csv(self.data_file)

        # Apply filters
        if country:
            df = df[df['country'].str.lower() == country.lower()]
        if pathogen:
            df = df[df['pathogen'].str.lower() == pathogen.lower()]
        if antibiotic:
            df = df[df['antibiotic'].str.lower() == antibiotic.lower()]

        # Check for region/geo information
        if region_col not in df.columns:
            logger.warning(f"Region column '{region_col}' not found. Using broader geographic aggregation.")
            # Try common alternatives
            for alt_col in ['district', 'state', 'city', 'province', 'county']:
                if alt_col in df.columns:
                    region_col = alt_col
                    logger.info(f"Using alternative region column: {region_col}")
                    break

        if region_col not in df.columns:
            # Create synthetic regions based on available data
            if 'country' in df.columns:
                region_col = 'country'
                logger.info("Using country as region for global mapping")
            else:
                logger.error("No geographic information available for mapping")
                return pd.DataFrame()

        # Aggregate by region (use latest available data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date', ascending=False)

        # Group by region and take most recent value or mean
        aggregated = df.groupby(region_col).agg({
            'percent_resistant': ['mean', 'count', lambda x: x.iloc[0]],  # count for sample size
            'country': 'first'
        }).reset_index()

        # Flatten column names
        aggregated.columns = ['region', 'resistance_mean', 'data_points', 'latest_resistance']
        aggregated['country'] = aggregated['country'].fillna(country)

        logger.info(f"Loaded {len(aggregated)} regions with AMR data")
        return aggregated

    def get_shapefile(self, country: str, level: str = 'admin1') -> Optional[gpd.GeoDataFrame]:
        """
        Load appropriate shapefile for the country/region.

        Args:
            country: Country name
            level: Geographic level (admin1=states, admin2=districts, country=country borders)

        Returns:
            GeoDataFrame with geographic boundaries or None if not found
        """
        # Common shapefile mappings
        shapefile_configs = {
            'India': {
                'admin2': 'india_districts.shp',  # Districts
                'admin1': 'india_states.shp',     # States
                'country': 'india_country.shp'    # Country boundary
            },
            'United States': {
                'admin2': 'us_counties.shp',      # Counties
                'admin1': 'us_states.shp',       # States
                'country': 'us_country.shp'      # USA boundary
            },
            'global': {
                'country': 'world_countries.shp'
            }
        }

        # Try country-specific shapefiles first
        config = shapefile_configs.get(country, shapefile_configs.get('global', {}))

        shapefile_name = config.get(level, f"{country.lower().replace(' ', '_')}_{level}.shp")
        shapefile_path = self.shapefile_dir / shapefile_name

        if shapefile_path.exists():
            try:
                gdf = gpd.read_file(shapefile_path)
                logger.info(f"Loaded shapefile: {shapefile_path}")
                return gdf
            except Exception as e:
                logger.error(f"Could not load shapefile {shapefile_path}: {e}")

        # Fallback to generic world countries
        world_shp = self.shapefile_dir / 'world_countries.shp'
        if world_shp.exists():
            try:
                gdf = gpd.read_file(world_shp)
                logger.info(f"Using world countries shapefile as fallback")
                return gdf
            except Exception as e:
                logger.error(f"Could not load world shapefile: {e}")

        logger.warning(f"No shapefile found for {country} at level {level}. Please add to {self.shapefile_dir}")
        return None

    def create_choropleth_map(self, amr_data: pd.DataFrame, country: str,
                             pathogen: str, antibiotic: str,
                             level: str = 'admin1',
                             metric: str = 'resistance_mean') -> Optional[str]:
        """
        Create static choropleth map of AMR distribution.

        Args:
            amr_data: Processed AMR data
            country: Country name
            pathogen, antibiotic: AMR combination
            level: Geographic level
            metric: Data column to visualize

        Returns:
            Path to saved map file or None if failed
        """
        # Load shapefile
        shapefile = self.get_shapefile(country, level)
        if shapefile is None:
            return None

        # Merge AMR data with geographic boundaries
        # Try different join keys
        merge_keys = ['region', 'district', 'state', 'province', 'county', 'name', 'county_name']

        merged_gdf = None
        for key in merge_keys:
            if key in shapefile.columns and len(amr_data) > 0:
                try:
                    merged_gdf = shapefile.merge(
                        amr_data,
                        left_on=key,
                        right_on='region',
                        how='left'
                    )
                    if not merged_gdf.empty and not merged_gdf[metric].isna().all():
                        logger.info(f"Successfully merged using key: {key}")
                        break
                except Exception as e:
                    logger.debug(f"Merge failed with key {key}: {e}")
                    continue

        if merged_gdf is None or merged_gdf.empty:
            logger.error("Could not merge AMR data with geographic boundaries")
            return None

        # Create the map
        fig, ax = plt.subplots(1, 1, figsize=(15, 10))

        # Filter out regions without data
        has_data = merged_gdf[~merged_gdf[metric].isna()]
        no_data = merged_gdf[merged_gdf[metric].isna()]

        # Plot regions with data
        if not has_data.empty:
            has_data.plot(
                column=metric,
                ax=ax,
                legend=True,
                cmap='RdYlGn_r',  # Red for high resistance, green for low
                missing_kwds={'color': 'lightgrey', 'alpha': 0.5},
                edgecolor='black',
                linewidth=0.5,
                vmax=100,  # Max resistance is 100%
                vmin=0     # Min resistance is 0%
            )

        # Plot regions without data
        if not no_data.empty:
            no_data.plot(
                ax=ax,
                color='lightgrey',
                edgecolor='black',
                linewidth=0.5,
                alpha=0.5
            )

        # Styling
        title = f"{pathogen} resistance to {antibiotic}"
        if metric == 'resistance_mean':
            avg_resistance = merged_gdf[metric].mean()
            title += ".1f"        else:
            title += f"{metric} in {country}"

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.axis('off')

        # Add resistance threshold explanations
        threshold_text = "\n".join([
            ".1f"            for level, info in self.resistance_thresholds.items()
        ])
        ax.text(0.02, 0.02, threshold_text,
               transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

        plt.tight_layout()

        # Save the map
        safe_filename = f"amr_map_{country}_{pathogen}_{antibiotic}_{level}.png".replace(" ", "_")
        output_path = self.reports_dir / safe_filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Choropleth map saved: {output_path}")
        return str(output_path)

    def create_interactive_map(self, amr_data: pd.DataFrame, country: str,
                              pathogen: str, antibiotic: str,
                              level: str = 'admin1',
                              metric: str = 'resistance_mean') -> Optional[folium.Map]:
        """
        Create interactive Folium map for web dashboards.

        Args:
            amr_data: Processed AMR data
            country: Country name
            pathogen, antibiotic: AMR combination
            level: Geographic level
            metric: Data column to visualize

        Returns:
            Folium Map object or None if failed
        """
        # Load shapefile
        shapefile = self.get_shapefile(country, level)
        if shapefile is None:
            return None

        # Merge data (simplified for interactive maps - assumes country-level)
        try:
            merged_gdf = shapefile.merge(
                amr_data,
                left_on='country',
                right_on='region',
                how='left'
            )
        except Exception as e:
            logger.error(f"Could not merge data for interactive map: {e}")
            return None

        # Set default center based on country
        center_coords = {
            'India': [20.5937, 78.9629],
            'United States': [39.50, -98.35],
            'global': [20, 0]
        }
        center = center_coords.get(country, center_coords['global'])

        # Create the map
        m = folium.Map(
            location=center,
            zoom_start=4 if country != 'global' else 2,
            tiles='OpenStreetMap'
        )

        # Add choropleth layer
        if not merged_gdf[metric].isna().all():
            folium.Choropleth(
                geo_data=merged_gdf,
                data=merged_gdf,
                columns=['region', metric],
                key_on='feature.properties.name',  # Adjust based on shapefile properties
                fill_color='RdYlGn_r',
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name='Resistance %',
                nan_fill_color='lightgrey'
            ).add_to(m)

            # Add tooltips with detailed information
            folium.GeoJson(
                merged_gdf,
                tooltip=folium.GeoJsonTooltip(
                    fields=['region', metric, 'data_points'],
                    aliases=[f'Region: {country}', 'Resistance %', 'Data Points'],
                    localize=True
                )
            ).add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        logger.info(f"Interactive map created for {country} {pathogen} vs {antibiotic}")
        return m

    def identify_hotspots(self, amr_data: pd.DataFrame,
                         threshold_percentile: float = 75) -> pd.DataFrame:
        """
        Identify AMR hotspots based on resistance percentiles.

        Args:
            amr_data: Processed AMR data
            threshold_percentile: Percentile above which regions are considered hotspots

        Returns:
            DataFrame with hotspot identification
        """
        if amr_data.empty:
            return pd.DataFrame()

        # Calculate threshold
        resistance_values = amr_data['resistance_mean'].dropna()
        if resistance_values.empty:
            return amr_data

        threshold = np.percentile(resistance_values, threshold_percentile)

        # Classify regions
        amr_data = amr_data.copy()
        amr_data['is_hotspot'] = amr_data['resistance_mean'] >= threshold
        amr_data['resistance_category'] = pd.cut(
            amr_data['resistance_mean'],
            bins=[0, 20, 50, 80, 100],
            labels=['Low', 'Moderate', 'High', 'Critical']
        )

        hotspot_count = amr_data['is_hotspot'].sum()
        logger.info(f"Identified {hotspot_count} hotspot regions (above {threshold_percentile}th percentile)")
        return amr_data

        return amr_data

    def export_hotspot_summary(self, hotspot_data: pd.DataFrame,
                              country: str, pathogen: str, antibiotic: str) -> str:
        """
        Export hotspot analysis summary.

        Args:
            hotspot_data: Data with hotspot identification
            country, pathogen, antibiotic: AMR combination

        Returns:
            Path to summary file
        """
        hotspots = hotspot_data[hotspot_data['is_hotspot'] == True]
        summary = ".1f"f"""
AMR Hotspot Analysis Summary
===========================
Country: {country}
Pathogen: {pathogen}
Antibiotic: {antibiotic}
Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}

OVERALL STATISTICS:
- Total regions analyzed: {len(hotspot_data)}
- Regions with data: {len(hotspot_data[~hotspot_data['resistance_mean'].isna()])}
- Hotspot regions: {len(hotspots)}
- Average resistance: {hotspot_data['resistance_mean'].mean():.1f}%

TOP HOTSPOTS:
{hotspots.nlargest(5, 'resistance_mean')[['region', 'resistance_mean', 'data_points']].to_string(index=False)}

RESISTANCE CATEGORIES:
{hotspot_data.groupby('resistance_category').size().to_string()}
        """

        filename = f"hotspot_summary_{country}_{pathogen}_{antibiotic}.txt".replace(" ", "_")
        output_path = self.reports_dir / filename

        with open(output_path, 'w') as f:
            f.write(summary)

        logger.info(f"Hotspot summary saved: {output_path}")
        return str(output_path)

    def create_forecast_hotspot_map(self, forecast_data: pd.DataFrame,
                                   shapefile: gpd.GeoDataFrame,
                                   country: str, pathogen: str, antibiotic: str,
                                   time_horizon: str = "2030") -> Optional[str]:
        """
        Create forecasted resistance hotspot map.

        Args:
            forecast_data: Future resistance predictions by region
            shapefile: Geographic boundaries
            time_horizon: Forecast period label

        Returns:
            Path to saved forecast map
        """
        try:
            # Merge forecast data with geography
            merged_gdf = shapefile.merge(
                forecast_data,
                left_on='name',  # Adjust based on shapefile
                right_on='region',
                how='left'
            )

            fig, ax = plt.subplots(1, 1, figsize=(15, 10))

            if not merged_gdf['predicted_resistance'].isna().all():
                merged_gdf.plot(
                    column='predicted_resistance',
                    ax=ax,
                    legend=True,
                    cmap='RdYlGn_r',
                    missing_kwds={'color': 'lightgrey'},
                    edgecolor='black',
                    linewidth=0.5,
                    vmax=100,
                    vmin=0
                )

            ax.set_title(f'Predicted AMR Hotspots: {pathogen} vs {antibiotic} in {country} ({time_horizon})',
                        fontsize=16, fontweight='bold', pad=20)
            ax.axis('off')

            # Save
            safe_filename = f"forecast_hotspots_{country}_{pathogen}_{antibiotic}_{time_horizon}.png".replace(" ", "_")
            output_path = self.reports_dir / safe_filename
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            logger.info(f"Forecast hotspot map saved: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Could not create forecast hotspot map: {e}")
            return None

def main():
    """Command-line interface for geographic mapping."""

    mapper = AMRGeographicMapper()

    # Example usage - adjust parameters as needed
    combinations = [
        ("India", "E. coli", "Ciprofloxacin"),
        ("United States", "Klebsiella pneumoniae", "Meropenem"),
        ("Brazil", "E. coli", "Trimethoprim-sulfamethoxazole")
    ]

    for country, pathogen, antibiotic in combinations:
        logger.info(f"Creating geographic maps for {country} | {pathogen} | {antibiotic}")

        try:
            # Load and process data
            amr_data = mapper.load_amr_data(country=country, pathogen=pathogen,
                                          antibiotic=antibiotic)

            if amr_data.empty:
                logger.warning(f"No data found for {country} | {pathogen} | {antibiotic}")
                continue

            # Create choropleth map
            map_path = mapper.create_choropleth_map(amr_data, country, pathogen,
                                                   antibiotic, level='admin1')
            if map_path:
                logger.info(f"✓ Static map created: {map_path}")

            # Identify and export hotspots
            hotspot_data = mapper.identify_hotspots(amr_data)
            if not hotspot_data.empty:
                summary_path = mapper.export_hotspot_summary(hotspot_data, country,
                                                           pathogen, antibiotic)
                logger.info(f"✓ Hotspot summary: {summary_path}")

        except Exception as e:
            logger.error(f"Failed to create maps for {country} | {pathogen} | {antibiotic}: {e}")

    # Create global overview if multiple countries available
    try:
        global_data = mapper.load_amr_data()
        if not global_data.empty:
            global_map = mapper.create_choropleth_map(
                global_data, "global", "All Pathogens", "All Antibiotics",
                level='country', metric='resistance_mean'
            )
            if global_map:
                logger.info(f"✓ Global overview map: {global_map}")
    except Exception as e:
        logger.error(f"Global overview failed: {e}")

    logger.info("Geographic mapping complete!")

if __name__ == "__main__":
    main()
