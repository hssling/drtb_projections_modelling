#!/usr/bin/env python3
"""
AMR Time Series Analysis Module

Comprehensive time series analysis for AMR surveillance data including:
- Time series decomposition and trend analysis
- Seasonal patterns detection
- Forecasting with multiple models (Prophet, ARIMA, Exponential Smoothing)
- Model comparison and validation
- Interactive visualizations for dashboard integration
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
import logging
from typing import Dict, List, Tuple, Optional, Union

# Forecasting libraries
from prophet import Prophet
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle

logger = logging.getLogger(__name__)

class AMRTimeSeriesAnalyzer:
    """
    Comprehensive AMR time series analysis and forecasting system.

    Provides multiple forecasting models, validation metrics, and
    dashboard-ready visualizations for AMR surveillance.
    """

    def __init__(self, data_file: str = "data/amr_merged.csv",
                 reports_dir: str = "reports"):
        """
        Initialize time series analyzer.

        Args:
            data_file: Path to AMR dataset
            reports_dir: Directory for saving results
        """
        self.data_file = Path(data_file)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)

        # Forecasting parameters
        self.forecast_horizon = 24  # months ahead
        self.validation_split = 0.2  # validation data proportion
        self.seasonal_periods = 12  # monthly seasonality

        # Store fitted models
        self.fitted_models = {}

        logger.info("AMR Time Series Analyzer initialized")

    def load_and_prepare_data(self, country: str, pathogen: str, antibiotic: str,
                            min_samples: int = 5) -> pd.DataFrame:
        """
        Load and prepare time series data for analysis.

        Args:
            country, pathogen, antibiotic: AMR combination
            min_samples: Minimum required data points

        Returns:
            Prepared time series DataFrame
        """
        if not self.data_file.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        df = pd.read_csv(self.data_file)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Filter for specific combination
        subset = df[
            (df["country"].str.lower() == country.lower()) &
            (df["pathogen"].str.lower() == pathogen.lower()) &
            (df["antibiotic"].str.lower() == antibiotic.lower())
        ].dropna(subset=['percent_resistant', 'date'])

        if subset.empty:
            raise ValueError(f"No data found for {country} | {pathogen} | {antibiotic}")

        if len(subset) < min_samples:
            raise ValueError(f"Insufficient data points ({len(subset)}) for time series analysis")

        # Sort by date and remove duplicates
        subset = subset.sort_values('date').drop_duplicates('date')

        # Create complete time series with missing date handling
        date_range = pd.date_range(start=subset['date'].min(),
                                 end=subset['date'].max(),
                                 freq='ME')

        # Reindex to fill missing dates
        ts_data = subset.set_index('date').reindex(date_range)

        # Interpolate missing values
        ts_data['percent_resistant'] = ts_data['percent_resistant'].interpolate(method='linear')

        # Reset index
        ts_data = ts_data.reset_index().rename(columns={'index': 'date'})

        logger.info(f"Prepared time series: {len(ts_data)} points from {ts_data['date'].min()} to {ts_data['date'].max()}")

        return ts_data[['date', 'percent_resistant']]

    def analyze_time_series(self, data: pd.DataFrame) -> Dict:
        """
        Perform comprehensive time series analysis.

        Args:
            data: Time series data

        Returns:
            Analysis results dictionary
        """
        logger.info("Performing comprehensive time series analysis")

        # Stationarity tests
        stationarity_results = self._test_stationarity(data['percent_resistant'])

        # Decomposition
        decomposition_results = self._decompose_series(data)

        # Trend analysis
        trend_analysis = self._analyze_trend(data)

        # Seasonality analysis
        seasonality_analysis = self._analyze_seasonality(data)

        # Volatility analysis
        volatility_analysis = self._analyze_volatility(data)

        results = {
            'stationarity': stationarity_results,
            'decomposition': decomposition_results,
            'trend': trend_analysis,
            'seasonality': seasonality_analysis,
            'volatility': volatility_analysis,
            'summary_stats': {
                'mean': data['percent_resistant'].mean(),
                'std': data['percent_resistant'].std(),
                'min': data['percent_resistant'].min(),
                'max': data['percent_resistant'].max(),
                'n_points': len(data),
                'time_range': {
                    'start': data['date'].min().strftime('%Y-%m-%d'),
                    'end': data['date'].max().strftime('%Y-%m-%d'),
                    'duration_months': (data['date'].max() - data['date'].min()).days // 30
                }
            }
        }

        logger.info("Time series analysis completed")
        return results

    def _test_stationarity(self, series: pd.Series) -> Dict:
        """Test for stationarity using ADF and KPSS tests."""
        # Augmented Dickey-Fuller test
        adf_result = adfuller(series.dropna())
        adf_stat = adf_result[0]
        adf_pvalue = adf_result[1]
        adf_critical = adf_result[4]

        # KPSS test
        try:
            kpss_result = kpss(series.dropna(), regression='c')
            kpss_stat = kpss_result[0]
            kpss_pvalue = kpss_result[1]
            kpss_critical = kpss_result[3]
        except:
            kpss_stat = kpss_pvalue = None
            kpss_critical = {}

        return {
            'adf': {
                'test_statistic': adf_stat,
                'p_value': adf_pvalue,
                'critical_values': adf_critical,
                'stationary': adf_pvalue < 0.05
            },
            'kpss': {
                'test_statistic': kpss_stat,
                'p_value': kpss_pvalue,
                'critical_values': kpss_critical,
                'stationary': kpss_pvalue >= 0.05 if kpss_pvalue else None
            },
            'conclusion': self._interpret_stationarity_tests(adf_pvalue, kpss_pvalue)
        }

    def _interpret_stationarity_tests(self, adf_p, kpss_p) -> str:
        """Interpret stationarity test results."""
        if adf_p < 0.05 and (kpss_p is None or kpss_p >= 0.05):
            return "Series is stationary"
        elif adf_p >= 0.05 and kpss_p is not None and kpss_p < 0.05:
            return "Series is non-stationary"
        else:
            return "Mixed results - further investigation needed"

    def _decompose_series(self, data: pd.DataFrame) -> Dict:
        """Decompose time series into trend, seasonal, and residual components."""
        try:
            # Ensure we have enough data for decomposition
            if len(data) >= 2 * self.seasonal_periods:
                decomposition = seasonal_decompose(
                    data.set_index('date')['percent_resistant'],
                    model='additive',
                    period=self.seasonal_periods
                )

                return {
                    'trend': decomposition.trend.dropna().tolist(),
                    'seasonal': decomposition.seasonal.dropna().tolist(),
                    'residual': decomposition.resid.dropna().tolist(),
                    'dates': [d.strftime('%Y-%m-%d') for d in decomposition.trend.dropna().index],
                    'seasonal_strength': self._calculate_seasonal_strength(decomposition),
                    'trend_strength': self._calculate_trend_strength(decomposition)
                }
            else:
                return {'error': 'Insufficient data for decomposition'}
        except Exception as e:
            return {'error': str(e)}

    def _calculate_seasonal_strength(self, decomposition) -> float:
        """Calculate seasonal component strength."""
        seasonal_var = np.var(decomposition.seasonal.dropna())
        residual_var = np.var(decomposition.resid.dropna())
        return seasonal_var / (seasonal_var + residual_var) if residual_var != 0 else 0

    def _calculate_trend_strength(self, decomposition) -> float:
        """Calculate trend component strength."""
        trend_var = np.var(decomposition.trend.dropna())
        residual_var = np.var(decomposition.resid.dropna())
        return trend_var / (trend_var + residual_var) if residual_var != 0 else 0

    def _analyze_trend(self, data: pd.DataFrame) -> Dict:
        """Analyze trend in the time series."""
        series = data['percent_resistant']

        # Linear regression for trend
        x = np.arange(len(series))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, series)

        # Trend direction and strength
        annual_change = slope * 12  # Convert to annual change

        if abs(annual_change) < 0.01:
            trend_direction = "Stable"
        elif annual_change > 0:
            trend_direction = "Increasing"
        else:
            trend_direction = "Decreasing"

        return {
            'slope': slope,
            'annual_change_pct': annual_change,
            'r_squared': r_value**2,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'direction': trend_direction,
            'strength': abs(r_value),  # Correlation coefficient
            'intercept': intercept
        }

    def _analyze_seasonality(self, data: pd.DataFrame) -> Dict:
        """Analyze seasonal patterns."""
        try:
            from statsmodels.tsa.stattools import acf

            # ACF to detect seasonality
            autocorr = acf(data['percent_resistant'].dropna(), nlags=min(len(data)-1, 24), fft=True)

            # Find peaks in ACF (potential seasonal lags)
            seasonal_peaks = []
            for i in range(self.seasonal_periods, len(autocorr)):
                if autocorr[i] > 0.3:  # Threshold for significant autocorrelation
                    seasonal_peaks.append((i, autocorr[i]))

            return {
                'autocorr_values': autocorr[:25].tolist(),
                'seasonal_peaks': seasonal_peaks,
                'has_seasonality': len([p for p, v in seasonal_peaks if p == self.seasonal_periods]) > 0,
                'seasonal_strength': autocorr[self.seasonal_periods] if self.seasonal_periods < len(autocorr) else 0
            }
        except Exception as e:
            return {'error': str(e)}

    def _analyze_volatility(self, data: pd.DataFrame) -> Dict:
        """Analyze volatility patterns."""
        series = data['percent_resistant']

        # Rolling volatility
        rolling_std_3m = series.rolling(window=3).std()
        rolling_std_6m = series.rolling(window=6).std()
        rolling_std_12m = series.rolling(window=12).std()

        # Overall volatility measures
        overall_std = series.std()
        cv = overall_std / abs(series.mean())  # Coefficient of variation

        # Volatility clusters detection
        from scipy.signal import find_peaks
        diff_series = series.diff().abs()

        return {
            'overall_std': overall_std,
            'coefficient_of_variation': cv,
            'rolling_volatility': {
                '3month': rolling_std_3m.tolist(),
                '6month': rolling_std_6m.tolist(),
                '12month': rolling_std_12m.tolist()
            },
            'volatility_trend': self._analyze_volatility_trend(rolling_std_12m),
            'change_points': self._detect_change_points(series)
        }

    def _analyze_volatility_trend(self, rolling_volatility: pd.Series) -> str:
        """Analyze if volatility is increasing or decreasing."""
        if len(rolling_volatility.dropna()) < 6:
            return "Insufficient data"

        recent = rolling_volatility.dropna()[-6:]
        x = np.arange(len(recent))
        slope, _, _, p, _ = stats.linregress(x, recent)

        if p > 0.05:
            return "Stable"
        elif slope > 0.001:
            return "Increasing"
        else:
            return "Decreasing"

    def _detect_change_points(self, series: pd.Series) -> List[int]:
        """Detect change points in the time series."""
        try:
            from ruptures import Pelt
            import ruptures as rpt

            # Convert to numpy array
            signal = series.dropna().values.reshape(-1, 1)

            # PELT algorithm for change points
            algo = rpt.Pelt(model="rbf").fit(signal)
            change_points = algo.predict(pen=10)

            return change_points[:-1]  # Remove last element (end of series)
        except ImportError:
            # Fallback: simple threshold-based detection
            diff = series.diff().abs()
            threshold = diff.mean() + 2 * diff.std()
            return (diff > threshold).astype(int).tolist()

    def fit_forecasting_models(self, data: pd.DataFrame) -> Dict:
        """
        Fit multiple forecasting models.

        Args:
            data: Time series data

        Returns:
            Dictionary of fitted models and their results
        """
        logger.info("Fitting forecasting models")

        models = {}

        # Split data for validation
        split_point = int(len(data) * (1 - self.validation_split))
        train_data = data[:split_point]
        validation_data = data[split_point:]

        # Model 1: Prophet
        try:
            models['prophet'] = self._fit_prophet_model(train_data, validation_data)
            logger.info("Prophet model fitted successfully")
        except Exception as e:
            logger.error(f"Prophet model failed: {e}")

        # Model 2: SARIMA
        try:
            models['sarima'] = self._fit_sarima_model(train_data, validation_data)
            logger.info("SARIMA model fitted successfully")
        except Exception as e:
            logger.error(f"SARIMA model failed: {e}")

        # Model 3: Exponential Smoothing
        try:
            models['exp_smoothing'] = self._fit_exp_smoothing_model(train_data, validation_data)
            logger.info("Exponential Smoothing model fitted successfully")
        except Exception as e:
            logger.error(f"Exponential Smoothing model failed: {e}")

        # Model comparison
        if models:
            models['comparison'] = self._compare_models(models, validation_data)

        return models

    def _fit_prophet_model(self, train_data: pd.DataFrame, validation_data: pd.DataFrame) -> Dict:
        """Fit Prophet forecasting model."""
        # Prepare data for Prophet
        prophet_data = train_data[['date', 'percent_resistant']].rename(
            columns={'date': 'ds', 'percent_resistant': 'y'}
        )

        # Fit model
        model = Prophet(
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.95
        )

        model.fit(prophet_data)

        # Generate forecast
        future_dates = pd.date_range(
            start=train_data['date'].max(),
            periods=len(validation_data) + self.forecast_horizon + 1,
            freq='ME'
        )[1:]

        future_df = pd.DataFrame({'ds': future_dates})
        forecast = model.predict(future_df)

        # Validation metrics
        if not validation_data.empty:
            validation_forecast = forecast[:len(validation_data)]
            metrics = self._calculate_validation_metrics(
                validation_data['percent_resistant'].values,
                validation_forecast['yhat'].values
            )
        else:
            metrics = {}

        return {
            'model': model,
            'forecast': forecast,
            'validation_metrics': metrics,
            'forecast_dates': future_dates,
            'forecasted_values': forecast['yhat'].values,
            'confidence_intervals': (forecast['yhat_lower'].values, forecast['yhat_upper'].values)
        }

    def _fit_sarima_model(self, train_data: pd.DataFrame, validation_data: pd.DataFrame) -> Dict:
        """Fit SARIMA model."""
        # SARIMA parameters (can be auto-selected)
        order = (1, 1, 1)  # (p, d, q)
        seasonal_order = (1, 0, 1, self.seasonal_periods)  # (P, D, Q, s)

        # Fit model
        model = SARIMAX(
            train_data['percent_resistant'],
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )

        fitted_model = model.fit(disp=False)

        # Forecast
        forecast_steps = len(validation_data) + self.forecast_horizon
        forecast = fitted_model.forecast(steps=forecast_steps)

        # Confidence intervals
        forecast_ci = fitted_model.get_forecast(steps=forecast_steps).conf_int()

        # Validation metrics
        if not validation_data.empty:
            validation_forecast = forecast[:len(validation_data)]
            metrics = self._calculate_validation_metrics(
                validation_data['percent_resistant'].values,
                validation_forecast
            )
        else:
            metrics = {}

        forecast_dates = pd.date_range(
            start=train_data['date'].max(),
            periods=forecast_steps + 1,
            freq='ME'
        )[1:]

        return {
            'model': fitted_model,
            'forecast': forecast,
            'forecast_dates': forecast_dates,
            'forecasted_values': forecast.values,
            'confidence_intervals': (forecast_ci.iloc[:, 0].values, forecast_ci.iloc[:, 1].values),
            'validation_metrics': metrics
        }

    def _fit_exp_smoothing_model(self, train_data: pd.DataFrame, validation_data: pd.DataFrame) -> Dict:
        """Fit Exponential Smoothing model."""
        # Holt-Winters Exponential Smoothing
        model = ExponentialSmoothing(
            train_data['percent_resistant'],
            seasonal_periods=self.seasonal_periods,
            trend='add',
            seasonal='add'
        )

        fitted_model = model.fit()

        # Forecast
        forecast_steps = len(validation_data) + self.forecast_horizon
        forecast = fitted_model.forecast(steps=forecast_steps)

        # Confidence intervals (approximated)
        forecast_std = np.std(fitted_model.resid)
        upper_ci = forecast + 1.96 * forecast_std
        lower_ci = forecast - 1.96 * forecast_std

        # Validation metrics
        if not validation_data.empty:
            validation_forecast = forecast[:len(validation_data)]
            metrics = self._calculate_validation_metrics(
                validation_data['percent_resistant'].values,
                validation_forecast
            )
        else:
            metrics = {}

        forecast_dates = pd.date_range(
            start=train_data['date'].max(),
            periods=forecast_steps + 1,
            freq='ME'
        )[1:]

        return {
            'model': fitted_model,
            'forecast': forecast,
            'forecast_dates': forecast_dates,
            'forecasted_values': forecast.values,
            'confidence_intervals': (lower_ci.values, upper_ci.values),
            'validation_metrics': metrics
        }

    def _calculate_validation_metrics(self, actual: np.ndarray, predicted: np.ndarray) -> Dict:
        """Calculate validation metrics."""
        return {
            'mae': mean_absolute_error(actual, predicted),
            'rmse': np.sqrt(mean_squared_error(actual, predicted)),
            'mape': np.mean(np.abs((actual - predicted) / actual)) * 100,
            'r2': r2_score(actual, predicted)
        }

    def _compare_models(self, models: Dict, validation_data: pd.DataFrame) -> Dict:
        """Compare forecasting model performance."""
        if validation_data.empty:
            return {}

        performance = {}
        for name, model_result in models.items():
            if name == 'comparison':
                continue

            metrics = model_result.get('validation_metrics', {})
            if metrics:
                performance[name] = metrics

        # Rank models by RMSE
        if performance:
            ranked = sorted(performance.items(), key=lambda x: x[1]['rmse'])
            return {
                'ranking': [model for model, _ in ranked],
                'best_model': ranked[0][0],
                'performance_scores': performance
            }
        else:
            return {}

    def generate_interactive_forecast(self, model_results: Dict,
                                    historical_data: pd.DataFrame,
                                    title: str = "AMR Forecasting Results") -> go.Figure:
        """
        Create interactive Plotly forecast visualization.

        Args:
            model_results: Forecasting results from fit_forecasting_models
            historical_data: Historical time series data
            title: Plot title

        Returns:
            Plotly figure object
        """
        fig = go.Figure()

        # Historical data
        fig.add_trace(go.Scatter(
            x=historical_data['date'],
            y=historical_data['percent_resistant'],
            mode='lines+markers',
            name='Historical Data',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))

        # Forecasted data from different models
        colors = ['red', 'green', 'orange', 'purple']
        color_idx = 0

        for model_name, results in model_results.items():
            if model_name == 'comparison':
                continue

            forecast_dates = results.get('forecast_dates', [])
            forecast_values = results.get('forecasted_values', [])
            ci_lower, ci_upper = results.get('confidence_intervals', ([], []))

            if not forecast_dates or not forecast_values:
                continue

            # Confidence interval
            fig.add_trace(go.Scatter(
                x=list(forecast_dates) + list(forecast_dates[::-1]),
                y=list(ci_upper) + list(ci_lower[::-1]),
                fill='toself',
                fillcolor=f'rgba({50 + color_idx*50}, {100 + color_idx*30}, {150 + color_idx*20}, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name=f'{model_name.title()} CI'
            ))

            # Forecast line
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_values,
                mode='lines',
                name=f'{model_name.title()} Forecast',
                line=dict(
                    color=colors[color_idx % len(colors)],
                    width=3,
                    dash='dash'
                )
            ))

            color_idx += 1

        # Add resistance threshold lines
        fig.add_hline(y=70, line_dash="dash", line_color="orange",
                     annotation_text="Warning (70%)")
        fig.add_hline(y=80, line_dash="dash", line_color="red",
                     annotation_text="Critical (80%)")

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Resistance Rate (%)",
            template="plotly_white",
            height=600,
            hovermode="x unified"
        )

        return fig

    def create_analysis_dashboard(self, analysis_results: Dict,
                               forecast_results: Dict,
                               country: str, pathogen: str, antibiotic: str):
        """
        Create comprehensive dashboard visualizations.

        Args:
            analysis_results: From analyze_time_series
            forecast_results: From fit_forecasting_models
            country, pathogen, antibiotic: identifiers
        """
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Time Series with Trend',
                'Seasonal Decomposition',
                'Forecast Model Comparison',
                'Stationarity Analysis',
                'Volatility Analysis',
                'Forecast Confidence Bands'
            ),
            specs=[[{'type': 'scatter'}, {'type': 'scatter'}],
                   [{'type': 'scatter'}, {'type': 'indicator'}],
                   [{'type': 'scatter'}, {'type': 'scatter'}]]
        )

        # Add analysis plots (implementation simplified for brevity)
        # This would be a comprehensive dashboard

        # Save interactive plot
        fig.write_html(self.reports_dir / f"ts_analysis_{country}_{pathogen}_{antibiotic}.html")

        logger.info(f"Dashboard created: ts_analysis_{country}_{pathogen}_{antibiotic}.html")

        return fig

    def run_complete_analysis(self, country: str, pathogen: str, antibiotic: str) -> Dict:
        """
        Run complete time series analysis pipeline.

        Args:
            country, pathogen, antibiotic: AMR combination

        Returns:
            Complete analysis results
        """
        logger.info(f"Running complete time series analysis for {country} | {pathogen} | {antibiotic}")

        try:
            # Load and prepare data
            data = self.load_and_prepare_data(country, pathogen, antibiotic)

            # Time series analysis
            analysis = self.analyze_time_series(data)

            # Forecasting models
            forecasts = self.fit_forecasting_models(data)

            # Generate visualizations
            interactive_plot = self.generate_interactive_forecast(
                forecasts, data,
                f"AMR Forecasting: {pathogen} vs {antibiotic} in {country}"
            )

            # Create analysis summary
            summary = {
                'country': country,
                'pathogen': pathogen,
                'antibiotic': antibiotic,
                'data_summary': analysis['summary_stats'],
                'stationarity': analysis['stationarity']['conclusion'],
                'trend': analysis['trend']['direction'],
                'forecast_performance': forecasts.get('comparison', {}),
                'key_findings': self._generate_key_findings(analysis, forecasts)
            }

            results = {
                'data': data,
                'analysis': analysis,
                'forecasts': forecasts,
                'visualization': interactive_plot,
                'summary': summary
            }

            # Save results
            self._save_analysis_results(results)

            logger.info("Complete analysis finished successfully")
            return results

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {'error': str(e)}

    def _generate_key_findings(self, analysis: Dict, forecasts: Dict) -> List[str]:
        """Generate key findings from analysis."""
        findings = []

        # Stationarity findings
        stationarity = analysis['stationarity']['conclusion']
        findings.append(f"📊 Stationarity: {stationarity}")

        # Trend findings
        trend = analysis['trend']
        if trend['p_value'] < 0.05:
            direction = trend['direction'].lower()
            annual_change = abs(trend['annual_change_pct'])
            findings.append(f"📈 Significant {direction} trend ({annual_change:.1f}% annually)")

        # Decomposition findings
        decomp = analysis.get('decomposition', {})
        if 'trend_strength' in decomp:
            trend_strength = decomp['trend_strength']
            if trend_strength > 0.6:
                findings.append(f"🎯 Strong trend component ({trend_strength:.1f})")
            elif trend_strength > 0.3:
                findings.append(f"🌊 Moderate trend component ({trend_strength:.1f})")

        # Forecast performance
        comparison = forecasts.get('comparison', {})
        if 'best_model' in comparison:
            best_model = comparison['best_model']
            findings.append(f"🎢 Best forecasting model: {best_model.title()}")

        # Volatility findings
        volatility = analysis.get('volatility', {})
        if 'volatility_trend' in volatility:
            vol_trend = volatility['volatility_trend']
            findings.append(f"⚡ Volatility: {vol_trend}")

        return findings

    def _save_analysis_results(self, results: Dict):
        """Save analysis results to files."""
        summary = results['summary']

        # Save summary JSON
        import json
        with open(self.reports_dir / f"ts_analysis_{summary['country']}_{summary['pathogen']}_{summary['antibiotic']}.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        # Save interactive plot
        results['visualization'].write_html(
            self.reports_dir / f"ts_analysis_{summary['country']}_{summary['pathogen']}_{summary['antibiotic']}.html"
        )

        logger.info("Analysis results saved to reports directory")

def main():
    """Command-line interface for time series analysis."""

    analyzer = AMRTimeSeriesAnalyzer()

    # Example analysis
    print("🧪 AMR Time Series Analysis System")
    print("=" * 50)

    # Example parameters
    params = [
        ('India', 'E. coli', 'Ciprofloxacin'),
        # Add more combinations as needed
    ]

    for country, pathogen, antibiotic in params:
        print(f"\n🔬 Analyzing: {country} | {pathogen} | {antibiotic}")

        try:
            results = analyzer.run_complete_analysis(country, pathogen, antibiotic)

            if 'error' not in results:
                summary = results['summary']
                print("   ✅ Analysis completed")
                print(f"   📊 Data points: {summary['data_summary']['n_points']}")
                print(f"   📈 Trend: {summary['trend']}")
                print(f"   🎯 Stationarity: {summary['stationarity']}")
                print("   📁 Results saved to reports/")

                # Print key findings
                print("   🔑 Key Findings:")
                for finding in summary['key_findings'][:3]:  # Limit to top 3
                    print(f"      • {finding}")
            else:
                print(f"   ❌ Analysis failed: {results['error']}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n✅ Time series analysis complete!")

if __name__ == "__main__":
    main()
