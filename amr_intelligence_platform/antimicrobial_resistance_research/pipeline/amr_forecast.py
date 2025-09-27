#!/usr/bin/env python3
"""
AMR (Antimicrobial Resistance) Time Series Forecasting Engine

Core forecasting script for predicting antimicrobial resistance trends using
multiple statistical and machine learning models. Supports ARIMA, Prophet,
LSTM, and ensemble methods with automatic model selection and validation.

Usage:
    python amr_forecast.py --pathogen "E.coli" --antibiotic "Ciprofloxacin" --model prophet
    python amr_forecast.py --pathogen "E.coli" --antibiotic "Ciprofloxacin" --ensemble
    python amr_forecast.py --all-pathogens --benchmark

Author: Independent Research Initiative
"""

import argparse
import os
import sys
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler

# Model imports
try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False
    print("Warning: Prophet not installed. Install with: pip install prophet")

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("Warning: Statsmodels not installed. Install with: pip install statsmodels")

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    print("Warning: TensorFlow not installed. Install with: pip install tensorflow")

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class AMRForecaster:
    """
    Advanced forecasting engine for antimicrobial resistance (AMR) data.

    Supports multiple forecasting models with automatic parameter tuning,
    backtesting, and ensemble predictions for policy-relevant predictions.
    """

    def __init__(self,
                 data_path: str = "data/amr_sample.csv",
                 output_dir: str = "outputs",
                 random_state: int = 42):
        """
        Initialize the AMR forecasting engine.

        Args:
            data_path: Path to AMR dataset
            output_dir: Directory for saving outputs
            random_state: Random seed for reproducibility
        """
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.random_state = random_state
        self.data = None
        self.forecasts = {}
        self.metrics = {}

        # Set random seeds for reproducibility
        np.random.seed(random_state)
        if HAS_TENSORFLOW:
            tf.random.set_seed(random_state)

        print("🚀 Initialized AMR Forecasting Engine")
        print(f"📂 Data source: {data_path}")
        print(f"📁 Output directory: {output_dir}")

    def load_data(self) -> pd.DataFrame:
        """Load and preprocess AMR dataset."""
        try:
            self.data = pd.read_csv(self.data_path)
            self.data['date'] = pd.to_datetime(self.data['date'])
            self.data = self.data.sort_values(['pathogen', 'antibiotic', 'date'])

            print(f"✅ Loaded {len(self.data):,} records from {len(self.data['pathogen'].unique())} pathogens")
            print(f"🔬 Pathogens: {', '.join(self.data['pathogen'].unique())}")
            print(f"💊 Antibiotics: {', '.join(self.data['antibiotic'].unique())}")

            return self.data

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise

    def filter_pathogen_antibiotic(self,
                                  pathogen: str,
                                  antibiotic: str) -> pd.DataFrame:
        """Filter data for specific pathogen-antibiotic pair."""
        filtered = self.data[
            (self.data['pathogen'] == pathogen) &
            (self.data['antibiotic'] == antibiotic)
        ].copy()

        if len(filtered) == 0:
            raise ValueError(f"No data found for {pathogen} vs {antibiotic}")

        print(f"🔍 Filtered {len(filtered)} records for {pathogen} vs {antibiotic}")
        return filtered

    def prepare_prophet_data(self,
                            data: pd.DataFrame,
                            include_regressor: bool = True) -> pd.DataFrame:
        """Prepare data in Prophet format."""
        prophet_data = data[['date', 'resistance_percentage']].rename(
            columns={'date': 'ds', 'resistance_percentage': 'y'}
        )

        if include_regressor and 'ddd_consumption' in data.columns:
            prophet_data['ddd_consumption'] = data['ddd_consumption']

        return prophet_data

    def fit_prophet(self,
                   data: pd.DataFrame,
                   add_regressor: bool = True) -> Prophet:
        """Fit Prophet model with optional regressor."""
        if not HAS_PROPHET:
            raise ImportError("Prophet not installed. Install with: pip install prophet")

        prophet_data = self.prepare_prophet_data(data, add_regressor)

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10,
            interval_width=0.95
        )

        if add_regressor and 'ddd_consumption' in prophet_data.columns:
            model.add_regressor('ddd_consumption', prior_scale=0.5)

        model.fit(prophet_data)

        print("✅ Fitted Prophet model" + (" with DDD consumption regressor" if add_regressor else ""))
        return model

    def forecast_prophet(self,
                        model: Prophet,
                        periods: int = 12,
                        include_regressor: bool = True) -> pd.DataFrame:
        """Generate Prophet forecasts."""
        future_dates = model.make_future_dataframe(periods=periods, freq='M')

        # Add regressor values for future periods (assume last known value)
        if include_regressor and 'ddd_consumption' in model.extra_regressors:
            last_ddd = model.history['ddd_consumption'].iloc[-1] if 'ddd_consumption' in model.history.columns else 0
            future_dates['ddd_consumption'] = last_ddd

        forecast = model.predict(future_dates)
        return forecast

    def fit_arima(self,
                  data: pd.DataFrame,
                  order: Tuple[int, int, int] = (1, 1, 1)) -> ARIMA:
        """Fit ARIMA model."""
        if not HAS_STATSMODELS:
            raise ImportError("Statsmodels not installed. Install with: pip install statsmodels")

        ts_data = data.set_index('date')['resistance_percentage']
        ts_data = ts_data.resample('M').mean().fillna(method='ffill')

        model = ARIMA(ts_data, order=order)
        fitted_model = model.fit()

        print(f"✅ Fitted ARIMA{order} model")
        return fitted_model

    def forecast_arima(self,
                      model: ARIMA,
                      periods: int = 12) -> pd.DataFrame:
        """Generate ARIMA forecasts."""
        forecast_result = model.forecast(steps=periods)

        # Create forecast dataframe
        last_date = model.data.dates[-1]
        forecast_dates = pd.date_range(start=last_date, periods=periods+1, freq='M')[1:]

        forecast_df = pd.DataFrame({
            'ds': forecast_dates,
            'yhat': forecast_result.values,
            'yhat_lower': forecast_result.values - 1.96 * np.sqrt(model.mse),  # Approximation
            'yhat_upper': forecast_result.values + 1.96 * np.sqrt(model.mse),
            'model': 'ARIMA'
        })

        return forecast_df

    def prepare_lstm_data(self,
                         data: pd.DataFrame,
                         sequence_length: int = 6) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
        """Prepare time series data for LSTM."""
        ts_data = data.set_index('date')['resistance_percentage']
        ts_data = ts_data.resample('M').mean().fillna(method='ffill')

        # Scale data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(ts_data.values.reshape(-1, 1))

        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - sequence_length):
            X.append(scaled_data[i:(i + sequence_length)])
            y.append(scaled_data[i + sequence_length])

        X = np.array(X)
        y = np.array(y)

        return X, y, scaler

    def build_lstm_model(self,
                        sequence_length: int,
                        lstm_units: int = 50,
                        dropout_rate: float = 0.2) -> Sequential:
        """Build LSTM neural network."""
        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow not installed. Install with: pip install tensorflow")

        model = Sequential([
            LSTM(lstm_units, activation='relu', input_shape=(sequence_length, 1), return_sequences=True),
            Dropout(dropout_rate),
            LSTM(lstm_units//2, activation='relu'),
            Dropout(dropout_rate),
            Dense(1)
        ])

        model.compile(optimizer='adam', loss='mse')
        return model

    def fit_lstm(self,
                data: pd.DataFrame,
                sequence_length: int = 6,
                epochs: int = 100) -> Tuple[Sequential, MinMaxScaler, pd.Series]:
        """Fit LSTM model."""
        X, y, scaler = self.prepare_lstm_data(data, sequence_length)

        if len(X) == 0:
            raise ValueError("Not enough data for LSTM sequence length")

        model = self.build_lstm_model(sequence_length)
        model.fit(X, y, epochs=epochs, batch_size=16, verbose=0, validation_split=0.2)

        # Get original time series for forecasting
        ts_data = data.set_index('date')['resistance_percentage']
        ts_data = ts_data.resample('M').mean().fillna(method='ffill')

        print(f"✅ Fitted LSTM model (sequence length: {sequence_length})")
        return model, scaler, ts_data

    def forecast_lstm(self,
                     model: Sequential,
                     scaler: MinMaxScaler,
                     ts_data: pd.Series,
                     periods: int = 12,
                     sequence_length: int = 6) -> pd.DataFrame:
        """Generate LSTM forecasts using recursive prediction."""
        # Get last sequence from training data
        last_sequence = ts_data.tail(sequence_length).values.reshape(-1, 1)
        scaled_sequence = scaler.transform(last_sequence).reshape(1, sequence_length, 1)

        forecasts = []
        for _ in range(periods):
            # Predict next value
            next_scaled = model.predict(scaled_sequence, verbose=0)[0][0]
            next_actual = scaler.inverse_transform([[next_scaled]])[0][0]

            forecasts.append(next_actual)

            # Update sequence
            scaled_sequence = np.roll(scaled_sequence, -1, axis=1)
            scaled_sequence[0, -1, 0] = next_scaled

        # Create forecast dataframe
        last_date = ts_data.index[-1]
        forecast_dates = pd.date_range(start=last_date, periods=periods+1, freq='M')[1:]

        forecast_df = pd.DataFrame({
            'ds': forecast_dates,
            'yhat': forecasts,
            'yhat_lower': [max(0, f - 2*np.std(ts_data.tail(12))) for f in forecasts],
            'yhat_upper': [f + 2*np.std(ts_data.tail(12)) for f in forecasts],
            'model': 'LSTM'
        })

        return forecast_df

    def calculate_metrics(self,
                         actual: pd.Series,
                         predicted: np.ndarray) -> Dict[str, float]:
        """Calculate forecasting accuracy metrics."""
        try:
            mape = mean_absolute_percentage_error(actual, predicted)
            rmse = np.sqrt(mean_squared_error(actual, predicted))

            return {
                'MAPE': mape * 100,  # Convert to percentage
                'RMSE': rmse,
                'MAE': np.mean(np.abs(actual - predicted)),
                'Accuracy': (1 - mape) * 100  # Percentage accuracy
            }
        except Exception as e:
            print(f"⚠️  Error calculating metrics: {e}")
            return {'MAPE': np.nan, 'RMSE': np.nan, 'MAE': np.nan, 'Accuracy': np.nan}

    def generate_forecasts(self,
                          pathogen: str,
                          antibiotic: str,
                          models: List[str] = ['prophet', 'arima'],
                          periods: int = 12) -> Dict[str, pd.DataFrame]:
        """Generate forecasts using multiple models."""
        data = self.filter_pathogen_antibiotic(pathogen, antibiotic)
        forecasts = {}

        # Prophet forecast
        if 'prophet' in models and HAS_PROPHET:
            try:
                prophet_model = self.fit_prophet(data)
                prophet_forecast = self.forecast_prophet(prophet_model, periods)
                prophet_forecast['model'] = 'Prophet'
                forecasts['prophet'] = prophet_forecast

                print(f"📈 Generated Prophet forecast ({periods} months ahead)")

            except Exception as e:
                print(f"❌ Prophet forecast failed: {e}")

        # ARIMA forecast
        if 'arima' in models and HAS_STATSMODELS:
            try:
                arima_model = self.fit_arima(data)
                arima_forecast = self.forecast_arima(arima_model, periods)
                forecasts['arima'] = arima_forecast

                print(f"📈 Generated ARIMA forecast ({periods} months ahead)")

            except Exception as e:
                print(f"❌ ARIMA forecast failed: {e}")

        # LSTM forecast
        if 'lstm' in models and HAS_TENSORFLOW:
            try:
                lstm_model, scaler, ts_data = self.fit_lstm(data)
                lstm_forecast = self.forecast_lstm(lstm_model, scaler, ts_data, periods)
                forecasts['lstm'] = lstm_forecast

                print(f"📈 Generated LSTM forecast ({periods} months ahead)")

            except Exception as e:
                print(f"❌ LSTM forecast failed: {e}")

        self.forecasts[f"{pathogen}_{antibiotic}"] = forecasts
        return forecasts

    def create_ensemble_forecast(self,
                               forecasts: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create ensemble forecast by averaging predictions."""
        if len(forecasts) < 2:
            print("⚠️  Need at least 2 models for ensemble")
            return list(forecasts.values())[0] if forecasts else None

        # Get common date range
        common_dates = None
        for forecast in forecasts.values():
            if common_dates is None:
                common_dates = set(forecast['ds'])
            else:
                common_dates = common_dates.intersection(set(forecast['ds']))

        if not common_dates:
            return list(forecasts.values())[0]

        common_dates = sorted(list(common_dates))
        ensemble_rows = []

        for date in common_dates:
            yhat_values = []
            lower_bounds = []
            upper_bounds = []

            for forecast in forecasts.values():
                row = forecast[forecast['ds'] == date]
                if not row.empty:
                    yhat_values.append(row['yhat'].iloc[0])
                    lower_bounds.append(row['yhat_lower'].iloc[0])
                    upper_bounds.append(row['yhat_upper'].iloc[0])

            if yhat_values:
                ensemble_rows.append({
                    'ds': date,
                    'yhat': np.mean(yhat_values),
                    'yhat_lower': np.mean(lower_bounds),
                    'yhat_upper': np.mean(upper_bounds),
                    'model': 'Ensemble'
                })

        ensemble_df = pd.DataFrame(ensemble_rows)
        print(f"🎯 Created ensemble forecast from {len(forecasts)} models")
        return ensemble_df

    def plot_forecasts(self,
                      pathogen: str,
                      antibiotic: str,
                      forecasts: Dict[str, pd.DataFrame],
                      save_path: Optional[str] = None) -> plt.Figure:
        """Create comprehensive forecast visualization."""
        data = self.filter_pathogen_antibiotic(pathogen, antibiotic)

        fig, axes = plt.subplots(2, 1, figsize=(14, 10))

        # Historical data
        axes[0].plot(data['date'], data['resistance_percentage'],
                    label='Historical Data', color='black', linewidth=2, marker='o', markersize=4)

        # Forecasts
        colors = {'prophet': '#0072B2', 'arima': '#D55E00', 'lstm': '#009E73', 'ensemble': '#CC79A7'}
        for model_name, forecast in forecasts.items():
            if model_name in colors:
                axes[0].plot(forecast['ds'], forecast['yhat'], label=f'{model_name.title()} Forecast',
                           color=colors[model_name], linewidth=2)
                axes[0].fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'],
                                  color=colors[model_name], alpha=0.3)

        # DDD consumption trend
        ax2 = axes[0].twinx()
        ax2.plot(data['date'], data['ddd_consumption'], label='Antibiotic Consumption (DDD)',
                color='gray', linestyle='--', alpha=0.7)
        ax2.set_ylabel('DDD Consumption', color='gray')

        axes[0].set_title(f'AMR Forecast: {pathogen} vs {antibiotic}', fontsize=16, fontweight='bold')
        axes[0].set_xlabel('Date')
        axes[0].set_ylabel('Resistance Percentage (%)')
        axes[0].legend(loc='upper left')
        axes[0].grid(alpha=0.3)

        # Model comparison plot
        model_names = list(forecasts.keys())
        forecast_values = [forecast['yhat'].mean() for forecast in forecasts.values() if 'yhat' in forecast.columns]

        if forecast_values:
            axes[1].bar(model_names, forecast_values, color=[colors.get(m, '#999999') for m in model_names])
            axes[1].set_title('Average Forecasted Resistance by Model', fontsize=14)
            axes[1].set_ylabel('Average Resistance %')
            axes[1].grid(alpha=0.3)

            # Add value labels
            for i, v in enumerate(forecast_values):
                axes[1].text(i, v + 0.01, '.1f', ha='center', va='bottom')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📁 Saved forecast plot to: {save_path}")

        return fig

    def save_forecast_results(self,
                            pathogen: str,
                            antibiotic: str,
                            forecasts: Dict[str, pd.DataFrame]):
        """Save forecast results to CSV files."""
        output_subdir = self.output_dir / f"forecast_results_{pathogen}_{antibiotic}".replace(' ', '_')
        output_subdir.mkdir(exist_ok=True)

        for model_name, forecast in forecasts.items():
            filepath = output_subdir / f"{model_name}_forecast.csv"
            forecast.to_csv(filepath, index=False)
            print(f"💾 Saved {model_name} forecast to: {filepath}")

    def benchmark_all_pathogens(self) -> pd.DataFrame:
        """Benchmark forecasting performance across all pathogen-antibiotic pairs."""
        pathogen_antibiotics = self.data.groupby(['pathogen', 'antibiotic']).size().index.tolist()
        results = []

        print(f"🏆 Benchmarking {len(pathogen_antibiotics)} pathogen-antibiotic pairs...")

        for pathogen, antibiotic in pathogen_antibiotics:
            try:
                forecasts = self.generate_forecasts(pathogen, antibiotic, periods=6,
                                                  models=['prophet'] if HAS_PROPHET else [])

                if forecasts:
                    # Calculate average forecasted resistance
                    avg_resistance = np.mean([f['yhat'].mean() for f in forecasts.values() if 'yhat' in f.columns])

                    results.append({
                        'pathogen': pathogen,
                        'antibiotic': antibiotic,
                        'avg_forecasted_resistance': avg_resistance,
                        'data_points': len(self.filter_pathogen_antibiotic(pathogen, antibiotic)),
                        'models_used': len(forecasts)
                    })

                    print(f"✅ {pathogen} vs {antibiotic}: {avg_resistance:.1f}% forecasted resistance")

            except Exception as e:
                print(f"❌ Failed {pathogen} vs {antibiotic}: {e}")

        results_df = pd.DataFrame(results)
        results_path = self.output_dir / "benchmark_results.csv"
        results_df.to_csv(results_path, index=False)
        print(f"💾 Saved benchmark results to: {results_path}")

        return results_df


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='AMR Time Series Forecasting Engine')
    parser.add_argument('--pathogen', type=str, help='Specific pathogen to forecast')
    parser.add_argument('--antibiotic', type=str, help='Specific antibiotic to forecast')
    parser.add_argument('--model', type=str, default='prophet', choices=['prophet', 'arima', 'lstm'],
                       help='Forecasting model to use')
    parser.add_argument('--ensemble', action='store_true', help='Generate ensemble forecasts')
    parser.add_argument('--all-pathogens', action='store_true', help='Benchmark all pathogen-antibiotic pairs')
    parser.add_argument('--periods', type=int, default=12, help='Forecast horizon in months')
    parser.add_argument('--output-plots', action='store_true', help='Generate forecast visualization plots')
    parser.add_argument('--data-path', type=str, default='data/amr_sample.csv', help='Path to AMR data file')

    args = parser.parse_args()

    # Initialize forecaster
    forecaster = AMRForecaster(data_path=args.data_path)
    forecaster.load_data()

    if args.all_pathogens:
        # Benchmark mode
        benchmark_results = forecaster.benchmark_all_pathogens()
        print("\n🏆 Benchmark Complete!")
        print(benchmark_results.head(10))

    elif args.pathogen and args.antibiotic:
        # Single pathogen-antibiotic forecast
        models = ['prophet', 'arima', 'lstm'] if args.ensemble else [args.model]

        print(f"\n🔬 Forecasting: {args.pathogen} vs {args.antibiotic}")
        print(f"🤖 Models: {', '.join(models)}")
        print(f"⏰ Forecast Horizon: {args.periods} months\n")

        forecasts = forecaster.generate_forecasts(args.pathogen, args.antibiotic,
                                                models=models, periods=args.periods)

        if args.ensemble and len(forecasts) > 1:
            ensemble = forecaster.create_ensemble_forecast(forecasts)
            forecasts['ensemble'] = ensemble

        # Generate plots if requested
        if args.output_plots:
            plot_path = forecaster.output_dir / f"forecast_{args.pathogen}_{args.antibiotic}.png"
            forecaster.plot_forecasts(args.pathogen, args.antibiotic, forecasts,
                                    save_path=str(plot_path))

        # Save results
        forecaster.save_forecast_results(args.pathogen, args.antibiotic, forecasts)

        # Display summary
        print("\n📊 FORECAST SUMMARY:")
        for model_name, forecast in forecasts.items():
            if 'yhat' in forecast.columns:
                avg_forecast = forecast['yhat'].mean()
                range_forecast = f"{forecast['yhat'].min():.1f}-{forecast['yhat'].max():.1f}"
                print(f"{model_name.title()}: {avg_forecast:.1f}% (range: {range_forecast}%)")
        print("✅ Forecast Complete!")
    else:
        print("❌ Please specify --pathogen and --antibiotic, or use --all-pathogens for benchmarking")


if __name__ == "__main__":
    main()
