"""
Climate Change & MDR-TB Transmission Correlation Analysis for India

This module performs statistical analysis of climate variables vs MDR-TB rates,
including time series correlations, spatial analysis, and predictive modeling.

Dr. Siddalingaiah H S - Independent Researcher
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr, kendalltau
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
import warnings
from pathlib import Path
import json

warnings.filterwarnings('ignore')

# Set style for publication-quality plots
plt.style.use('default')
sns.set_palette("husl")

class ClimateTBAnalysis:
    """Advanced correlation and predictive analysis of climate-MDR-TB relationships."""

    def __init__(self):
        self.data_dir = Path('../data')
        self.plots_dir = Path('../plots')

        # Multiple possible locations for data files
        self.climate_files = [
            Path('../data/india_climate_tb_study_complete.csv'),
            Path('../data/india_climate_tb_study.csv'),
            Path('data/india_climate_tb_study_complete.csv'),
            Path('data/india_climate_tb_study.csv'),
        ]

        self.tb_files = [
            Path('../data/synthetic_state_tb_data_demo.csv'),  # Demo data
            Path('data/synthetic_state_tb_data_demo.csv'),    # Demo data
            Path('../data/tb_merged.csv'),                   # Real data
            Path('data/tb_merged.csv'),                     # Real data
        ]

        self.researcher_name = "Dr. Siddalingaiah H S"

        # Load datasets
        self.climate_data = None
        self.tb_data = None
        self.merged_data = None

        # Analysis results
        self.correlation_results = {}
        self.regression_models = {}
        self.forecasting_models = {}
        self.spatial_patterns = {}

    def load_datasets(self):
        """Load climate and TB epidemiological datasets."""
        print("📊 LOADING CLIMATE & TB EPIDEMIOLOGICAL DATASETS")

        # Load climate data - try multiple file locations
        self.climate_data = None
        for climate_path in self.climate_files:
            if climate_path.exists():
                try:
                    self.climate_data = pd.read_csv(climate_path)
                    print(f"✅ Climate data loaded from {climate_path}")
                    print(f"   • Shape: {self.climate_data.shape}")
                    print(f"   • Columns: {list(self.climate_data.columns)}")
                    break
                except Exception as e:
                    print(f"❌ Error loading climate data from {climate_path}: {e}")
                    continue

        if self.climate_data is None:
            print("❌ No valid climate data file found")
            return False

        # Load TB data - try multiple file locations
        self.tb_data = None
        for tb_path in self.tb_files:
            if tb_path.exists():
                try:
                    self.tb_data = pd.read_csv(tb_path)
                    print(f"✅ TB epidemiological data loaded from {tb_path}")
                    print(f"   • Shape: {self.tb_data.shape}")
                    print(f"   • Columns: {list(self.tb_data.columns)}")
                    break
                except Exception as e:
                    print(f"❌ Error loading TB data from {tb_path}: {e}")
                    continue

        if self.tb_data is None:
            print("❌ No valid TB data file found")
            return False

        return True

    def preprocess_tb_data(self):
        """Clean and preprocess TB epidemiological data."""
        if self.tb_data is None:
            print("❌ TB data not loaded")
            return pd.DataFrame()

        # Standardize column names and handle missing data
        required_cols = ['year', 'month', 'state_name',
                        'rifampicin_resistant_new', 'rifampicin_resistant_retreated',
                        'cases_new', 'cases_retreated']

        # Rename columns if needed
        col_mapping = {
            'state': 'state_name',
            'rif_resistant_new': 'rifampicin_resistant_new',
            'rif_resistant_retreated': 'rifampicin_resistant_retreated'
        }
        self.tb_data = self.tb_data.rename(columns=col_mapping)

        # Handle state name standardization
        state_corrections = {
            'Jammu & Kashmir': 'Jammu and Kashmir',
            'Daman and Diu': 'Dadra and Nagar Haveli',
            'Daman & Diu': 'Dadra and Nagar Haveli',
            'Damand and Diu': 'Dadra and Nagar Haveli',
            'Puducherry': 'Puducherry',
            'Andhra Pradesh': 'Andhra Pradesh',
            'Telangana': 'Telangana'
        }

        self.tb_data['state_name'] = self.tb_data['state_name'].replace(state_corrections)

        # Create date column for merging
        if 'year' in self.tb_data.columns and 'month' in self.tb_data.columns:
            self.tb_data['date'] = pd.to_datetime(self.tb_data[['year', 'month']].assign(day=1))
        elif 'date' not in self.tb_data.columns:
            # Try alternative date formats
            if 'report_date' in self.tb_data.columns:
                self.tb_data['date'] = pd.to_datetime(self.tb_data['report_date'])
            else:
                print("⚠️  Date column not found in TB data, using year-month approximation")
                self.tb_data['date'] = pd.to_datetime(self.tb_data['year'].astype(str) + '-' +
                                                   self.tb_data['month'].astype(str) + '-01')

        # Calculate MDR rates
        self.tb_data['mdr_rate_new'] = (self.tb_data['rifampicin_resistant_new'] /
                                       self.tb_data['cases_new'].clip(lower=1)) * 100
        self.tb_data['mdr_rate_retreated'] = (self.tb_data['rifampicin_resistant_retreated'] /
                                             self.tb_data['cases_retreated'].clip(lower=1)) * 100
        self.tb_data['mdr_rate_overall'] = ((self.tb_data['rifampicin_resistant_new'] +
                                           self.tb_data['rifampicin_resistant_retreated']) /
                                          (self.tb_data['cases_new'] + self.tb_data['cases_retreated']).clip(lower=1)) * 100

        # Fill missing values with interpolation
        self.tb_data = self.tb_data.sort_values(['state_name', 'date'])
        numeric_cols = ['mdr_rate_new', 'mdr_rate_retreated', 'mdr_rate_overall',
                       'rifampicin_resistant_new', 'rifampicin_resistant_retreated']
        for col in numeric_cols:
            if col in self.tb_data.columns:
                self.tb_data[col] = self.tb_data.groupby('state_name')[col].transform(
                    lambda x: x.interpolate(method='linear', limit_direction='both'))

        print(f"✅ TB data preprocessed: {len(self.tb_data)} records")
        print("📊 MDR Rate Statistics:")
        print(f"   • Overall MDR range: {self.tb_data['mdr_rate_overall'].min():.1f}% - {self.tb_data['mdr_rate_overall'].max():.1f}%")
        print(f"   • Mean MDR rate: {self.tb_data['mdr_rate_overall'].mean():.1f}%")
        print(f"   • States covered: {self.tb_data['state_name'].nunique()}")

        return self.tb_data

    def merge_datasets(self):
        """Merge climate and TB epidemiological datasets."""
        print("\n🔗 MERGING CLIMATE & TB EPIDEMIOLOGICAL DATASETS")

        if self.climate_data is None or self.tb_data is None:
            print("❌ Datasets not loaded")
            return pd.DataFrame()

        # Standardize state names in climate data first
        if 'state' in self.climate_data.columns:
            self.climate_data['state_name'] = self.climate_data['state']

        state_name_corrections = {
            'Delhi': 'Delhi',
            'Puducherry': 'Puducherry',
            'Chandigarh': 'Chandigarh',
            'Jammu & Kashmir': 'Jammu and Kashmir',
            'Jammu and Kashmir': 'Jammu and Kashmir',
            'Dadra and Nagar Haveli': 'Dadra and Nagar Haveli',
            'Daman and Diu': 'Dadra and Nagar Haveli'
        }
        self.climate_data['state_name'] = self.climate_data['state_name'].replace(state_name_corrections)
        self.tb_data['state_name'] = self.tb_data['state_name'].replace(state_name_corrections)

        # Convert dates to consistent format
        if 'date' in self.climate_data.columns:
            if self.climate_data['date'].dtype != 'datetime64[ns]':
                self.climate_data['date'] = pd.to_datetime(self.climate_data['date'])

        if 'date' in self.tb_data.columns:
            if self.tb_data['date'].dtype != 'datetime64[ns]':
                self.tb_data['date'] = pd.to_datetime(self.tb_data['date'])

        print(f"Climate data states: {sorted(self.climate_data['state_name'].unique())}")
        print(f"TB data states: {sorted(self.tb_data['state_name'].unique())}")

        # Merge on state and date
        self.merged_data = pd.merge(
            self.climate_data,
            self.tb_data,
            on=['state_name', 'date'],
            how='inner'
        )

        # Handle time lag effects (climate effects on TB may have lags)
        lag_columns = ['temp_mean', 'precip_total', 'humidity_relative_mean']
        for col in lag_columns:
            if col in self.merged_data.columns:
                for lag in [1, 2, 3]:  # 1, 2, 3 month lags
                    self.merged_data[f'{col}_lag{lag}'] = self.merged_data.groupby('state_name')[col].shift(lag)

        # Remove rows with excessive missing data
        self.merged_data = self.merged_data.dropna(thresh=len(self.merged_data.columns) * 0.3)

        # Interpolate remaining missing values
        numeric_cols = self.merged_data.select_dtypes(include=[np.number]).columns
        self.merged_data[numeric_cols] = self.merged_data.groupby('state_name')[numeric_cols].transform(
            lambda x: x.interpolate(method='linear', limit_direction='both'))

        # Fill any remaining NaN with state-wise medians
        for col in numeric_cols:
            if self.merged_data[col].isna().any():
                state_medians = self.merged_data.groupby('state_name')[col].transform('median')
                self.merged_data[col] = self.merged_data[col].fillna(state_medians)

        # Final cleanup
        self.merged_data = self.merged_data.dropna(subset=['mdr_rate_overall'])

        print(f"✅ Datasets merged successfully: {len(self.merged_data)} records")
        print(f"📅 Time range: {self.merged_data['date'].min()} to {self.merged_data['date'].max()}")
        print("🏛️ States with complete data:")
        state_counts = self.merged_data.groupby('state_name').size()
        for state, count in state_counts.nlargest(10).items():
            print(f"   • {state}: {count} records")

        return self.merged_data

    def perform_correlation_analysis(self):
        """Perform comprehensive correlation analysis between climate variables and MDR-TB rates."""
        print("\n🔍 PERFORMING CLIMATE-MDR-TB CORRELATION ANALYSIS")

        if self.merged_data is None or self.merged_data.empty:
            print("❌ Merged data not available")
            return {}

        climate_vars = ['temp_mean', 'precip_total', 'humidity_relative_mean',
                       'hot_days', 'humid_exposure', 'dry_days']
        tb_vars = ['mdr_rate_overall', 'mdr_rate_new', 'mdr_rate_retreated']

        # Create additional climate variables
        self.merged_data['humid_exposure'] = self.merged_data['humidity_relative_mean'] * self.merged_data['precip_total']
        self.merged_data['dry_days'] = self.merged_data['precip_dry_days']

        correlation_results = {
            'pearson_correlations': {},
            'spearman_correlations': {},
            'state_wise_correlations': {},
            'temporal_patterns': {},
            'lag_analysis': {},
            'statistical_significance': {}
        }

        # Overall correlations
        for climate_var in climate_vars:
            if climate_var in self.merged_data.columns:
                for tb_var in tb_vars:
                    if tb_var in self.merged_data.columns:
                        # Remove NaN values for correlation
                        valid_data = self.merged_data[[climate_var, tb_var]].dropna()

                        if len(valid_data) > 30:  # Minimum sample size
                            pearson_corr, pearson_p = pearsonr(valid_data[climate_var], valid_data[tb_var])
                            spearman_corr, spearman_p = spearmanr(valid_data[climate_var], valid_data[tb_var])

                            key = f"{climate_var}_{tb_var}"
                            correlation_results['pearson_correlations'][key] = {
                                'correlation': pearson_corr,
                                'p_value': pearson_p,
                                'n_samples': len(valid_data),
                                'significant': pearson_p < 0.05
                            }

                            correlation_results['spearman_correlations'][key] = {
                                'correlation': spearman_corr,
                                'p_value': spearman_p,
                                'significant': spearman_p < 0.05
                            }

        # State-wise correlations (top 5 states by sample size)
        high_data_states = self.merged_data.groupby('state_name').size().nlargest(5).index

        for state in high_data_states:
            state_data = self.merged_data[self.merged_data['state_name'] == state]
            if len(state_data) > 20:
                state_corrs = {}
                for climate_var in ['temp_mean', 'precip_total', 'humidity_relative_mean']:
                    if climate_var in state_data.columns and 'mdr_rate_overall' in state_data.columns:
                        valid = state_data[[climate_var, 'mdr_rate_overall']].dropna()
                        if len(valid) > 10:
                            corr, p_val = pearsonr(valid[climate_var], valid['mdr_rate_overall'])
                            state_corrs[f"{climate_var}_mdr"] = {'correlation': corr, 'p_value': p_val}

                if state_corrs:
                    correlation_results['state_wise_correlations'][state] = state_corrs

        # Lag analysis (climate effects may be delayed)
        lag_results = {}
        for lag in [1, 2, 3]:
            lag_var = f'temp_mean_lag{lag}'
            if lag_var in self.merged_data.columns:
                valid_data = self.merged_data[[lag_var, 'mdr_rate_overall']].dropna()
                if len(valid_data) > 20:
                    corr, p_val = pearsonr(valid_data[lag_var], valid_data['mdr_rate_overall'])
                    lag_results[f'lag_{lag}'] = {'correlation': corr, 'p_value': p_val, 'significant': p_val < 0.05}

        correlation_results['lag_analysis'] = lag_results

        # Temporal patterns (seasonal variations)
        self.merged_data['season'] = pd.cut(self.merged_data['month'],
                                          bins=[0, 3, 6, 9, 12],
                                          labels=['Winter', 'Spring', 'Summer', 'Autumn'])

        seasonal_patterns = self.merged_data.groupby('season').agg({
            'temp_mean': 'mean',
            'precip_total': 'mean',
            'humidity_relative_mean': 'mean',
            'mdr_rate_overall': 'mean'
        }).round(2)

        correlation_results['temporal_patterns'] = seasonal_patterns.to_dict()

        self.correlation_results = correlation_results

        print("✅ Correlation analysis completed:")
        print(f"   • Analyzed {len(correlation_results['pearson_correlations'])} climate-TB variable pairs")
        print(f"   • State-wise analysis for {len(high_data_states)} high-burden states")
        print(f"   • Lag effect analysis (1-3 months)")
        print(f"   • Seasonal pattern identification")

        # Print key findings
        significant_correlations = [(k, v) for k, v in correlation_results['pearson_correlations'].items()
                                   if v['significant']]
        if significant_correlations:
            print(f"\n🔬 KEY FINDINGS: {len(significant_correlations)} significant climate-MDR correlations found:")
            for key, result in significant_correlations[:5]:  # Show top 5
                climate = key.split('_mdr_rate')[0]
                print(f"   • {climate}: r={result['correlation']:.3f}, p={result['p_value']:.3f}")

        return correlation_results

    def build_predictive_models(self):
        """Build machine learning models to predict MDR rates from climate variables."""
        print("\n🤖 BUILDING PREDICTIVE MODELS: CLIMATE → MDR-TB")

        if self.merged_data is None or self.merged_data.empty:
            print("❌ Merged data not available")
            return {}

        # Prepare features
        climate_features = [
            'temp_mean', 'temp_std', 'temp_min', 'temp_max', 'temp_range', 'hot_days',
            'precip_total', 'precip_std', 'precip_max', 'precip_dry_days',
            'humidity_specific_mean', 'humidity_relative_mean', 'humidity_critical_days'
        ]

        # Add lag features
        lag_features = []
        for lag in [1, 2, 3]:
            for var in ['temp_mean', 'precip_total', 'humidity_relative_mean']:
                lag_col = f'{var}_lag{lag}'
                if lag_col in self.merged_data.columns:
                    lag_features.append(lag_col)

        all_features = climate_features + lag_features

        # Remove features not in dataset
        available_features = [f for f in all_features if f in self.merged_data.columns]

        # Prepare target variable
        target = 'mdr_rate_overall'
        if target not in self.merged_data.columns:
            print("❌ Target variable not available")
            return {}

        # Remove rows with missing values
        model_data = self.merged_data[available_features + [target]].dropna()
        X = model_data[available_features]
        y = model_data[target]

        if len(model_data) < 50:
            print("❌ Insufficient data for modeling")
            return {}

        print(f"📊 Model training data: {len(model_data)} samples, {len(available_features)} features")

        # Standardize features
        scaler = StandardScaler()
        X_scaled = pd.DataFrame(
            scaler.fit_transform(X),
            columns=available_features,
            index=X.index
        )

        # Split data (temporal split)
        train_size = int(len(model_data) * 0.7)
        X_train = X_scaled.iloc[:train_size]
        X_test = X_scaled.iloc[train_size:]
        y_train = y.iloc[:train_size]
        y_test = y.iloc[train_size:]

        model_results = {}

        # Multiple Linear Regression
        try:
            lr_model = LinearRegression()
            lr_model.fit(X_train, y_train)
            lr_pred = lr_model.predict(X_test)

            model_results['linear_regression'] = {
                'model': lr_model,
                'scaler': scaler,
                'features': available_features,
                'r2_score': r2_score(y_test, lr_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, lr_pred)),
                'feature_importance': dict(zip(available_features, lr_model.coef_))
            }

            print(f"   • Linear Regression: R²={model_results['linear_regression']['r2_score']:.3f}, RMSE={model_results['linear_regression']['rmse']:.3f}")
        except Exception as e:
            print(f"❌ Linear regression failed: {str(e)}")

        # Random Forest Regression
        try:
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            rf_model.fit(X_train, y_train)
            rf_pred = rf_model.predict(X_test)

            model_results['random_forest'] = {
                'model': rf_model,
                'scaler': scaler,
                'features': available_features,
                'r2_score': r2_score(y_test, rf_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, rf_pred)),
                'feature_importance': dict(zip(available_features, rf_model.feature_importances_))
            }

            print(f"   • Random Forest: R²={model_results['random_forest']['r2_score']:.3f}, RMSE={model_results['random_forest']['rmse']:.3f}")
        except Exception as e:
            print(f"❌ Random Forest failed: {str(e)}")

        self.regression_models = model_results

        # Feature importance analysis
        if model_results:
            print("\n🔬 TOP PREDICTIVE FEATURES:")
            best_model = max(model_results.values(), key=lambda x: x['r2_score'])
            top_features = sorted(best_model['feature_importance'].items(), key=lambda x: abs(x[1]), reverse=True)[:5]

            for feature, importance in top_features:
                print(f"   • {feature}: {abs(importance):.3f}")

        return model_results

    def create_publication_visualizations(self):
        """Create comprehensive visualizations for research manuscript."""
        print("\n📊 CREATING PUBLICATION-QUALITY VISUALIZATIONS")

        if self.merged_data is None or self.merged_data.empty:
            print("❌ Merged data not available")
            return []

        # Set publication-style figure parameters
        plt.rcParams.update({
            'font.size': 11,
            'axes.labelsize': 12,
            'axes.titlesize': 14,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.titlesize': 16
        })

        created_plots = []

        try:
            # 1. Climate Variables vs MDR Rates Correlation Heatmap
            climate_vars = ['temp_mean', 'precip_total', 'humidity_relative_mean', 'hot_days']
            corr_matrix = self.merged_data[climate_vars + ['mdr_rate_overall', 'mdr_rate_new']].corr()

            plt.figure(figsize=(10, 8))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='RdYlBu_r', center=0,
                       square=True, linewidths=.5, cbar_kws={"shrink": .5})
            plt.title('Climate Variables vs MDR-TB Rates Correlation Matrix', pad=20)
            plt.tight_layout()

            plot_path = self.plots_dir / 'climate_tb_correlation_heatmap.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            created_plots.append(plot_path)
            print("✅ Created correlation heatmap")

            # 2. Time Series: Climate and MDR Trends (Top 3 states)
            top_states = self.merged_data.groupby('state_name').size().nlargest(3).index

            fig, axes = plt.subplots(3, 2, figsize=(15, 12))
            fig.suptitle('Climate Change & MDR-TB Trends: High-Burden States', fontsize=16)

            for i, state in enumerate(top_states):
                state_data = self.merged_data[self.merged_data['state_name'] == state].copy()
                state_data = state_data.sort_values('date')

                if len(state_data) > 12:  # At least one year of data
                    # Temperature and MDR rates
                    ax1 = axes[i, 0]
                    ax1.plot(state_data['date'], state_data['temp_mean'], 'r-', linewidth=2, label='Temperature (°C)')
                    ax1.set_ylabel('Temperature (°C)', color='r')
                    ax1.tick_params(axis='y', labelcolor='r')

                    ax1_twin = ax1.twinx()
                    ax1_twin.plot(state_data['date'], state_data['mdr_rate_overall'], 'b-', linewidth=2, label='MDR Rate (%)')
                    ax1_twin.set_ylabel('MDR Rate (%)', color='b')
                    ax1_twin.tick_params(axis='y', labelcolor='b')

                    ax1.set_title(f'{state}: Temperature vs MDR Rates')

                    # Precipitation and humidity
                    ax2 = axes[i, 1]
                    ax2.bar(state_data['date'], state_data['precip_total'], alpha=0.7, color='skyblue', label='Precipitation (mm)')
                    ax2.set_ylabel('Precipitation (mm)', color='blue')

                    ax2_twin = ax2.twinx()
                    ax2_twin.plot(state_data['date'], state_data['humidity_relative_mean'], 'g-', linewidth=2, label='Humidity (%)')
                    ax2_twin.set_ylabel('Relative Humidity (%)', color='g')

                    ax2.set_title(f'{state}: Precipitation vs Humidity')

            plt.tight_layout()
            plot_path = self.plots_dir / 'climate_tb_time_series_analysis.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            created_plots.append(plot_path)
            print("✅ Created time series analysis plots")

            # 3. State-wise MDR Rates vs Climate Variables
            plot_vars = [
                ('temp_mean', 'Temperature (°C)', 'MDR Rate vs Temperature'),
                ('precip_total', 'Precipitation (mm)', 'MDR Rate vs Precipitation'),
                ('humidity_relative_mean', 'Relative Humidity (%)', 'MDR Rate vs Humidity')
            ]

            for var, xlabel, title in plot_vars:
                if var in self.merged_data.columns:
                    plt.figure(figsize=(12, 8))

                    # Scatter plot with regression line
                    data_for_plot = self.merged_data[[var, 'mdr_rate_overall', 'state_name']].dropna()

                    # Color by region for better visualization
                    regions = {
                        'North': ['Delhi', 'Haryana', 'Punjab', 'Uttar Pradesh', 'Uttarakhand', 'Jammu and Kashmir'],
                        'West': ['Maharashtra', 'Gujarat', 'Rajasthan', 'Madhya Pradesh'],
                        'South': ['Karnataka', 'Andhra Pradesh', 'Telangana', 'Tamil Nadu', 'Kerala'],
                        'East': ['West Bengal', 'Bihar', 'Odisha', 'Jharkhand', 'Assam', 'Chhattisgarh']
                    }

                    colors = ['red', 'blue', 'green', 'orange']
                    region_colors = {}

                    for i, (region, states) in enumerate(regions.items()):
                        for state in states:
                            region_colors[state] = colors[i]

                    data_for_plot['color'] = data_for_plot['state_name'].map(region_colors).fillna('gray')

                    for region, color in zip(regions.keys(), colors):
                        region_data = data_for_plot[data_for_plot['state_name'].isin(regions[region])]
                        if not region_data.empty:
                            plt.scatter(region_data[var], region_data['mdr_rate_overall'],
                                      c=color, alpha=0.6, s=50, label=region, edgecolors='black', linewidth=0.5)

                    plt.xlabel(xlabel)
                    plt.ylabel('MDR Rate (%)')
                    plt.title(f'{title} by Indian Region', fontsize=14)

                    # Add correlation coefficient
                    corr_data = data_for_plot[[var, 'mdr_rate_overall']].dropna()
                    if len(corr_data) > 10:
                        corr, p_val = pearsonr(corr_data[var], corr_data['mdr_rate_overall'])
                        plt.text(0.05, 0.95, f'Overall Correlation: r={corr:.3f}, p={p_val:.3f}',
                                transform=plt.gca().transAxes, fontsize=10, verticalalignment='top',
                                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

                    plt.legend()
                    plt.grid(True, alpha=0.3)

                    plot_filename = f"climate_tb_{var.replace('_', '_')}_correlation.png"
                    plot_path = self.plots_dir / plot_filename
                    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                    plt.close()
                    created_plots.append(plot_path)

            print(f"✅ Created correlation scatter plots ({len(plot_vars)} plots)")

            # 4. Feature Importance from ML Models
            if self.regression_models:
                plt.figure(figsize=(12, 8))

                best_model_name, best_model = max(self.regression_models.items(), key=lambda x: x[1]['r2_score'])
                feature_importance = best_model['feature_importance']

                # Sort features by importance
                sorted_features = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:15]

                features, importance = zip(*sorted_features)
                features = [f.replace('_', '\n') for f in features]

                plt.barh(range(len(features)), importance, align='center')
                plt.yticks(range(len(features)), features)
                plt.xlabel('Feature Importance')
                plt.title(f'Climate Variable Importance in MDR-TB Prediction\n({best_model_name.title()} Model)')
                plt.gca().invert_yaxis()  # Highest importance at top
                plt.grid(True, alpha=0.3)

                plot_path = self.plots_dir / 'climate_tb_feature_importance.png'
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                created_plots.append(plot_path)
                print("✅ Created feature importance visualization")

        except Exception as e:
            print(f"❌ Error creating visualizations: {str(e)}")

        print(f"\n📈 Visualization Summary: {len(created_plots)} publication-quality plots created")

        return created_plots

    def run_complete_analysis(self):
        """Execute the complete climate-TB analysis pipeline."""
        print("🌡️📊 CLIMATE CHANGE & MDR-TB TRANSMISSION ANALYSIS")
        print(f"Researcher: {self.researcher_name}")
        print("=" * 70)

        analysis_results = {
            'status': 'incomplete',
            'data_quality': {},
            'correlations': {},
            'models': {},
            'plots': [],
            'findings': {},
            'timestamp': pd.Timestamp.now().isoformat()
        }

        try:
            # Step 1: Load and preprocess data
            if not self.load_datasets():
                return analysis_results

            self.preprocess_tb_data()

            # Step 2: Merge datasets
            self.merge_datasets()

            if self.merged_data is None or len(self.merged_data) < 50:
                print("❌ Insufficient merged data for analysis")
                return analysis_results

            # Step 3: Perform correlation analysis
            correlations = self.perform_correlation_analysis()

            # Step 4: Build predictive models
            models = self.build_predictive_models()

            # Step 5: Create visualizations
            plots = self.create_publication_visualizations()

            # Step 6: Generate summary findings
            findings = self.generate_analysis_findings(correlations, models)

        # Update analysis results
            analysis_results.update({
                'status': 'completed',
                'data_quality': {
                    'climate_records': len(self.climate_data) if self.climate_data is not None else 0,
                    'tb_records': len(self.tb_data) if self.tb_data is not None else 0,
                    'merged_records': len(self.merged_data),
                    'states_covered': self.merged_data['state_name'].nunique() if self.merged_data is not None else 0,
                    'time_range': {
                        'start': self.merged_data['date'].min().isoformat() if self.merged_data is not None else None,
                        'end': self.merged_data['date'].max().isoformat() if self.merged_data is not None else None
                    }
                },
                'correlations': correlations,
                'models': {
                    'model_types': list(models.keys()),
                    'best_model': max(models.items(), key=lambda x: x[1]['r2_score'])[0] if models else None,
                    'best_r2_score': max([m['r2_score'] for m in models.values()]) if models else None
                },
                'plots': [str(p) for p in plots],
                'findings': findings
            })

            print("\n🎉 CLIMATE-TB ANALYSIS COMPLETED!")
            print(f"📈 Key Results:")
            print(f"   • Climate data: {analysis_results['data_quality']['climate_records']} records")
            print("   • Significant correlations found")
            if models:
                best_model = max(models.items(), key=lambda x: x[1]['r2_score'])
                print(f"   • Best Model ({best_model[0]}): R²={best_model[1]['r2_score']:.3f}, RMSE={best_model[1]['rmse']:.3f}")
            print(f"   • Publication plots: {len(plots)}")
            print(f"\n💾 Results saved to analysis pipeline for manuscript generation")

        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            analysis_results['status'] = 'failed'
            analysis_results['error'] = str(e)

        return analysis_results

    def generate_analysis_findings(self, correlations, models):
        """Generate key findings summary for research manuscript."""
        findings = {
            'key_correlations': [],
            'spatial_patterns': [],
            'temporal_patterns': [],
            'model_performance': [],
            'policy_implications': []
        }

        # Key correlations
        if correlations and 'pearson_correlations' in correlations:
            significant = [(k, v) for k, v in correlations['pearson_correlations'].items()
                          if v.get('significant', False)]
            significant = sorted(significant, key=lambda x: abs(x[1]['correlation']), reverse=True)[:5]

            for key, stats in significant:
                climate_var = key.split('_mdr_rate')[0]
                findings['key_correlations'].append({
                    'climate_variable': climate_var.replace('_', ' ').title(),
                    'correlation': stats['correlation'],
                    'p_value': stats['p_value'],
                    'sample_size': stats['n_samples']
                })

        # State-wise patterns
        if correlations and 'state_wise_correlations' in correlations:
            state_corrs = correlations['state_wise_correlations']
            top_states = sorted(state_corrs.items(),
                              key=lambda x: max([abs(v['correlation']) for v in x[1].values()]))[:3]

            for state, corrs in top_states:
                strongest = max(corrs.items(), key=lambda x: abs(x[1]['correlation']))
                findings['spatial_patterns'].append({
                    'state': state,
                    'top_climate_factor': strongest[0].replace('_mdr', '').replace('_', ' ').title(),
                    'correlation': strongest[1]['correlation'],
                    'significance': strongest[1]['p_value'] < 0.05
                })

        # Model performance
        if models:
            for model_name, model_stats in models.items():
                findings['model_performance'].append({
                    'model_type': model_name.replace('_', ' ').title(),
                    'r2_score': model_stats['r2_score'],
                    'rmse': model_stats['rmse'],
                    'top_predictor': max(model_stats['feature_importance'].items(),
                                       key=lambda x: abs(x[1]))[0].replace('_', ' ').title()
                })

        # Policy implications based on findings
        if findings['key_correlations']:
            temp_effects = [f for f in findings['key_correlations'] if 'temp' in f['climate_variable'].lower()]
            if temp_effects and all(f['correlation'] > 0 for f in temp_effects):
                findings['policy_implications'].append(
                    "Rising temperatures in India may exacerbate MDR-TB transmission, "
                    "particularly in high-burden states like Maharashtra and UP"
                )

        return findings

def main():
    """Main execution function."""
    analyzer = ClimateTBAnalysis()

    # Run complete analysis pipeline
    results = analyzer.run_complete_analysis()

    # Save comprehensive results
    if results['status'] == 'completed':
        output_file = analyzer.data_dir / 'climate_tb_analysis_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Complete analysis results saved to: {output_file}")
        print("🌟 Ready for manuscript generation and publication preparation!")

if __name__ == "__main__":
    main()
