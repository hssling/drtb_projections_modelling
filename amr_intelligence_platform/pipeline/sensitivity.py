#!/usr/bin/env python3
"""
AMR Sensitivity & Scenario Analysis Module

Provides comprehensive sensitivity analysis capabilities for AMR forecasting,
including Monte Carlo simulations, one-way/multi-way sensitivity analysis,
and policy scenario modeling.

Features:
- Monte Carlo uncertainty quantification
- Antibiotic consumption sensitivity scenarios
- What-if policy simulations
- Elasticity analysis
- Multi-factor sensitivity modeling
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class AMRSensitivityAnalyzer:
    """
    Comprehensive sensitivity analysis for AMR forecasting models.

    Supports various types of sensitivity analysis:
    - One-way sensitivity (vary one parameter)
    - Multi-way sensitivity (vary multiple parameters)
    - Monte Carlo simulation (probabilistic uncertainty)
    - Elasticity analysis (impact quantification)
    - Policy scenario modeling
    """

    def __init__(self, data_file: str = "data/amr_merged.csv", reports_dir: str = "reports"):
        """
        Initialize sensitivity analyzer.

        Args:
            data_file: Path to unified AMR dataset
            reports_dir: Directory to save analysis results
        """
        self.data_file = Path(data_file)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)

        # Analysis parameters
        self.baseline_model = None
        self.forecast_horizon = 24  # months
        self.confidence_levels = [5, 95]  # Percentiles for uncertainty bands

    def load_data(self, country: str, pathogen: str, antibiotic: str) -> pd.DataFrame:
        """Load and prepare data for specified combination."""
        if not self.data_file.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        df = pd.read_csv(self.data_file)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        subset = df[(df["country"].str.lower() == country.lower()) &
                    (df["pathogen"].str.lower() == pathogen.lower()) &
                    (df["antibiotic"].str.lower() == antibiotic.lower())].dropna(subset=['percent_resistant'])

        if subset.empty:
            raise ValueError(f"No data found for {country} | {pathogen} | {antibiotic}")

        # Check for consumption data
        if 'ddd' in subset.columns and not subset['ddd'].isna().all():
            subset = subset.dropna(subset=['ddd'])
            self.has_consumption_data = True
            logger.info(f"Consumption data (DDD) available: {len(subset)} records")
        else:
            self.has_consumption_data = False
            logger.warning("No antibiotic consumption (DDD) data found - sensitivity analysis limited")

        return subset

    def fit_baseline_model(self, data: pd.DataFrame) -> Prophet:
        """Fit baseline Prophet model with consumption regressor if available."""
        prophet_data = data[['date', 'percent_resistant']].rename(
            columns={'date': 'ds', 'percent_resistant': 'y'}
        )

        model = Prophet(
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
            interval_width=0.95
        )

        # Add consumption regressor if available
        if self.has_consumption_data and 'ddd' in data.columns:
            prophet_data['consumption'] = data['ddd']
            model.add_regressor('consumption')
            logger.info("Added antibiotic consumption (DDD) as regression covariate")

        try:
            model.fit(prophet_data)
            self.baseline_model = model
            logger.info("Baseline model fitted successfully")
            return model
        except Exception as e:
            logger.error(f"Model fitting failed: {e}")
            # Fallback to simple model
            fallback_model = Prophet()
            fallback_model.fit(prophet_data[['ds', 'y']])
            self.baseline_model = fallback_model
            logger.info("Fallback to simple Prophet model")
            return fallback_model

    def run_baseline_forecast(self, model: Prophet, data: pd.DataFrame) -> pd.DataFrame:
        """Generate baseline forecast."""
        last_date = data['date'].max()
        future_dates = pd.date_range(start=last_date, periods=self.forecast_horizon + 1, freq='M')[1:]

        future_df = pd.DataFrame({'ds': future_dates})

        # Add consumption regressor if model expects it
        if model.extra_regressors and 'consumption' in model.extra_regressors:
            last_consumption = data['ddd'].iloc[-1] if 'ddd' in data.columns else 0
            future_df['consumption'] = last_consumption

        forecast = model.predict(future_df)
        return forecast

    def monte_carlo_simulation(self, country: str, pathogen: str, antibiotic: str,
                              n_simulations: int = 500, consumption_variation: float = 0.2,
                              other_variations: Optional[Dict] = None) -> Dict:
        """
        Run Monte Carlo sensitivity analysis.

        Args:
            country, pathogen, antibiotic: AMR combination
            n_simulations: Number of Monte Carlo runs
            consumption_variation: Std dev for consumption variation
            other_variations: Other parameter variations

        Returns:
            Dictionary with simulation results
        """
        logger.info(f"Starting Monte Carlo simulation: {n_simulations} runs")

        # Load and prepare data
        data = self.load_data(country, pathogen, antibiotic)
        model = self.fit_baseline_model(data)

        # Baseline forecast
        baseline_forecast = self.run_baseline_forecast(model, data)

        # Monte Carlo simulations
        simulations = []

        for i in range(n_simulations):
            if i % 100 == 0:
                logger.info(f"Monte Carlo: Run {i+1}/{n_simulations}")

            # Create perturbed future dataframe
            future_dates = pd.date_range(start=data['date'].max(),
                                       periods=self.forecast_horizon + 1, freq='M')[1:]
            future_df = pd.DataFrame({'ds': future_dates})

            # Perturb consumption if available
            if model.extra_regressors and 'consumption' in model.extra_regressors:
                base_consumption = data['ddd'].iloc[-1]

                # Apply random variation (normal distribution)
                consumption_factor = np.random.normal(1.0, consumption_variation)
                consumption_factor = np.clip(consumption_factor, 0.1, 3.0)  # Reasonable bounds
                future_df['consumption'] = base_consumption * consumption_factor

            # Apply other variations (if specified)
            if other_variations:
                for param, std_dev in other_variations.items():
                    if param in future_df.columns:
                        # Add random variation to existing parameters
                        base_values = future_df[param].values
                        variation = np.random.normal(1.0, std_dev, len(base_values))
                        future_df[param] = base_values * variation

            # Generate forecast
            forecast = model.predict(future_df)
            simulations.append(forecast[['ds', 'yhat']].set_index('ds')['yhat'].values)

        # Process results
        simulations = np.array(simulations)
        forecast_dates = future_df['ds'].values

        # Calculate statistics
        mean_forecast = np.mean(simulations, axis=0)
        median_forecast = np.median(simulations, axis=0)
        std_forecast = np.std(simulations, axis=0)

        # Confidence intervals
        lower_ci = np.percentile(simulations, self.confidence_levels[0], axis=0)
        upper_ci = np.percentile(simulations, self.confidence_levels[1], axis=0)

        # Create results dictionary
        results = {
            'baseline_forecast': baseline_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
            'monte_carlo': {
                'mean': mean_forecast,
                'median': median_forecast,
                'std': std_forecast,
                'lower_ci': lower_ci,
                'upper_ci': upper_ci,
                'all_simulations': simulations,
                'dates': forecast_dates,
                'n_simulations': n_simulations
            },
            'parameters': {
                'consumption_variation': consumption_variation,
                'other_variations': other_variations or {},
                'confidence_level': self.confidence_levels
            }
        }

        # Generate visualization
        self._plot_monte_carlo_results(results, country, pathogen, antibiotic)

        logger.info(f"Monte Carlo simulation completed: {n_simulations} runs")

        return results

    def _plot_monte_carlo_results(self, results: Dict, country: str, pathogen: str, antibiotic: str):
        """Generate comprehensive Monte Carlo results visualization."""
        mc_data = results['monte_carlo']
        baseline = results['baseline_forecast']

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        dates = pd.to_datetime(mc_data['dates'])

        # Plot 1: Mean forecast with uncertainty bands
        ax1.fill_between(dates, mc_data['lower_ci'], mc_data['upper_ci'],
                        color='lightblue', alpha=0.4, label=f'{self.confidence_levels[1]}-{self.confidence_levels[0]}% CI')
        ax1.plot(dates, mc_data['mean'], 'b-', linewidth=2, label='Mean Forecast')
        ax1.plot(baseline['ds'], baseline['yhat'], 'r--', linewidth=2, label='Baseline')
        ax1.set_title('Monte Carlo Forecast with Uncertainty Bands')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Resistance %')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        # Plot 2: Standard deviation (uncertainty)
        ax2.plot(dates, mc_data['std'], 'g-', linewidth=2)
        ax2.set_title('Forecast Uncertainty (Standard Deviation)')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Std Deviation')
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)

        # Plot 3: Sample simulation trajectories
        sample_indices = np.random.choice(mc_data['all_simulations'].shape[0], size=min(50, mc_data['n_simulations']), replace=False)
        for idx in sample_indices:
            ax3.plot(dates, mc_data['all_simulations'][idx], 'gray', alpha=0.1, linewidth=0.5)

        # Add mean trajectory on top
        ax3.plot(dates, mc_data['mean'], 'r-', linewidth=2, label='Mean')
        ax3.set_title('Sample Simulation Trajectories')
        ax3.set_xlabel('Date')
        ax3.set_ylabel('Resistance %')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)

        # Plot 4: Forecast distribution at end point
        end_forecasts = mc_data['all_simulations'][:, -1]  # Last forecast point
        ax4.hist(end_forecasts, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax4.axvline(mc_data['mean'][-1], color='red', linestyle='--', linewidth=2, label='Mean')
        ax4.axvline(mc_data['median'][-1], color='orange', linestyle='--', linewidth=2, label='Median')
        ax4.set_title(f'Forecast Distribution at {dates[-1].strftime("%Y-%m")}')
        ax4.set_xlabel('Resistance %')
        ax4.set_ylabel('Frequency')
        ax4.legend()

        # Overall title
        fig.suptitle(f'Monte Carlo Sensitivity Analysis: {pathogen} vs {antibiotic} in {country}',
                    fontsize=16, fontweight='bold')
        plt.tight_layout()

        # Save plot
        output_file = self.reports_dir / f"monte_carlo_{country}_{pathogen}_{antibiotic}.png".replace(" ", "_")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Monte Carlo visualization saved to {output_file}")

    def consumption_sensitivity_scenarios(self, country: str, pathogen: str, antibiotic: str,
                                        scenarios: Optional[Dict[str, float]] = None) -> Dict:
        """
        Run sensitivity scenarios for antibiotic consumption changes.

        Args:
            country, pathogen, antibiotic: AMR combination
            scenarios: Dict of scenario names to consumption multipliers (e.g., {'+20%': 1.2})

        Returns:
            Dictionary with scenario results
        """
        if scenarios is None:
            scenarios = {
                '+50%': 1.5, '+20%': 1.2, '+10%': 1.1,
                'Baseline': 1.0,
                '-10%': 0.9, '-20%': 0.8, '-50%': 0.5
            }

        logger.info(f"Running consumption sensitivity scenarios: {list(scenarios.keys())}")

        # Load and prepare data
        data = self.load_data(country, pathogen, antibiotic)

        if not self.has_consumption_data:
            logger.warning("No consumption data available - using simple scenarios")
            # Generate synthetic consumption scenarios
            return self._synthetic_sensitivity_scenarios(data, country, pathogen, antibiotic, scenarios)

        model = self.fit_baseline_model(data)
        baseline_forecast = self.run_baseline_forecast(model, data)

        scenario_results = {}

        for scenario_name, multiplier in scenarios.items():
            logger.info(f"Running scenario: {scenario_name} (multiplier: {multiplier})")

            # Generate future dataframe with modified consumption
            future_dates = pd.date_range(start=data['date'].max(),
                                       periods=self.forecast_horizon + 1, freq='M')[1:]
            future_df = pd.DataFrame({'ds': future_dates})

            base_consumption = data['ddd'].iloc[-1]
            future_df['consumption'] = base_consumption * multiplier

            # Generate forecast
            forecast = model.predict(future_df)

            scenario_results[scenario_name] = {
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
                'multiplier': multiplier,
                'consumption_level': base_consumption * multiplier
            }

        # Generate comparative visualization
        self._plot_sensitivity_scenarios(scenario_results, baseline_forecast,
                                       country, pathogen, antibiotic)

        logger.info(f"Consumption sensitivity analysis completed: {len(scenarios)} scenarios")
        return scenario_results

    def _synthetic_sensitivity_scenarios(self, data: pd.DataFrame, country: str,
                                       pathogen: str, antibiotic: str,
                                       scenarios: Dict[str, float]) -> Dict:
        """Generate synthetic sensitivity scenarios when no consumption data is available."""
        logger.info("Using synthetic scenarios (no real consumption data)")

        # Simple approach: apply multipliers directly to resistance trend
        last_resistance = data['percent_resistant'].iloc[-1]

        # Generate synthetic forecasts assuming increasing/decreasing resistance
        base_trend = [last_resistance + i * (0.5 if last_resistance < 50 else -0.3)
                     for i in range(self.forecast_horizon)]

        scenario_results = {}

        for scenario_name, multiplier in scenarios.items():
            # Modify trend based on scenario
            trend_modifier = (multiplier - 1.0) * 10  # Convert to percentage change
            modified_trend = [base + trend_modifier * (i/self.forecast_horizon)
                            for i, base in enumerate(base_trend)]

            # Keep within reasonable bounds
            modified_trend = [max(0, min(100, x)) for x in modified_trend]

            # Create synthetic forecast dataframe
            future_dates = pd.date_range(start=data['date'].max(),
                                       periods=self.forecast_horizon + 1, freq='M')[1:]

            forecast_df = pd.DataFrame({
                'ds': future_dates,
                'yhat': modified_trend,
                'yhat_lower': [x * 0.8 for x in modified_trend],
                'yhat_upper': [x * 1.2 for x in modified_trend]
            })

            scenario_results[scenario_name] = {
                'forecast': forecast_df,
                'multiplier': multiplier,
                'consumption_level': None,
                'synthetic': True
            }

        # Create baseline forecast
        baseline_forecast = pd.DataFrame({
            'ds': future_dates,
            'yhat': base_trend,
            'yhat_lower': [x * 0.9 for x in base_trend],
            'yhat_upper': [x * 1.1 for x in base_trend]
        })

        # Generate visualization
        self._plot_sensitivity_scenarios(scenario_results, baseline_forecast,
                                       country, pathogen, antibiotic, synthetic=True)

        return scenario_results

    def _plot_sensitivity_scenarios(self, scenarios: Dict, baseline_forecast: pd.DataFrame,
                                  country: str, pathogen: str, antibiotic: str, synthetic: bool = False):
        """Generate comparative visualization of sensitivity scenarios."""
        plt.figure(figsize=(14, 8))

        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'gray']

        for i, (scenario_name, scenario_data) in enumerate(scenarios.items()):
            forecast_df = scenario_data['forecast']
            color = colors[i % len(colors)]

            plt.plot(forecast_df['ds'], forecast_df['yhat'],
                    color=color, linewidth=2, label=scenario_name)

            # Add confidence interval (shaded)
            plt.fill_between(forecast_df['ds'], forecast_df['yhat_lower'], forecast_df['yhat_upper'],
                           color=color, alpha=0.1)

        # Add baseline reference if different from scenarios
        if 'Baseline' not in scenarios:
            plt.plot(baseline_forecast['ds'], baseline_forecast['yhat'],
                    'k-', linewidth=3, label='Baseline', linestyle='--')

        # Add resistance threshold lines
        plt.axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='Warning (70%)')
        plt.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Critical (80%)')

        title_suffix = " (Synthetic Scenarios)" if synthetic else ""
        plt.title(f'Sensitivity Analysis: {pathogen} vs {antibiotic} in {country}{title_suffix}',
                 fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Resistance Percentage (%)', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot
        output_file = self.reports_dir / f"sensitivity_scenarios_{country}_{pathogen}_{antibiotic}.png".replace(" ", "_")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Sensitivity scenarios visualization saved to {output_file}")

    def elasticity_analysis(self, country: str, pathogen: str, antibiotic: str) -> Dict:
        """
        Calculate elasticity of resistance with respect to consumption.

        Elasticity = % change in resistance / % change in consumption
        """
        logger.info(f"Calculating resistance elasticity for {country} | {pathogen} | {antibiotic}")

        data = self.load_data(country, pathogen, antibiotic)

        if not self.has_consumption_data:
            logger.warning("No consumption data available for elasticity analysis")
            return {'elasticity': None, 'error': 'No consumption data available'}

        # Calculate percentage changes
        resistance_pct_change = data['percent_resistant'].pct_change()
        consumption_pct_change = data['ddd'].pct_change()

        # Remove NaN values
        valid_data = pd.DataFrame({
            'resistance_change': resistance_pct_change,
            'consumption_change': consumption_pct_change
        }).dropna()

        if len(valid_data) < 5:
            logger.warning("Insufficient data for elasticity calculation")
            return {'elasticity': None, 'error': 'Insufficient data'}

        try:
            # Calculate elasticity (simple correlation-based approach)
            correlation = valid_data['resistance_change'].corr(valid_data['consumption_change'])
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                valid_data['consumption_change'], valid_data['resistance_change']
            )

            elasticity = slope  # dy/dx in percentage terms

            results = {
                'elasticity': elasticity,
                'correlation': correlation,
                'r_squared': r_value ** 2,
                'p_value': p_value,
                'significance': 'Significant' if p_value < 0.05 else 'Not significant',
                'slope': slope,
                'intercept': intercept,
                'n_points': len(valid_data),
                'interpretation': self._interpret_elasticity(elasticity, p_value)
            }

            logger.info(".4f"f"   Interpretation: {results['interpretation']}")

            return results

        except Exception as e:
            logger.error(f"Elasticity calculation failed: {e}")
            return {'elasticity': None, 'error': str(e)}

    def _interpret_elasticity(self, elasticity: float, p_value: float) -> str:
        """Provide interpretation of elasticity results."""
        if p_value >= 0.05:
            return "No significant relationship between antibiotic consumption and resistance"

        if elasticity > 1.0:
            elasticity_strength = "highly elastic"
        elif elasticity > 0.5:
            elasticity_strength = "moderately elastic"
        elif elasticity > 0:
            elasticity_strength = "inelastic"
        elif elasticity == 0:
            return "No relationship between consumption and resistance changes"
        else:
            elasticity_strength = "negative relationship"

        return f"Resistance is {elasticity_strength} to antibiotic consumption (elasticity = {elasticity:.2f}, p = {p_value:.2f})"
def main():
    """Command-line interface for sensitivity analysis."""

    # Example usage - can be expanded with argparse
    analyzer = AMRSensitivityAnalyzer()

    # Example: Monte Carlo simulation
    try:
        print("🧪 Running sample Monte Carlo sensitivity analysis...")
        mc_results = analyzer.monte_carlo_simulation(
            country="India",
            pathogen="E. coli",
            antibiotic="Ciprofloxacin",
            n_simulations=100,  # Reduced for demo
            consumption_variation=0.2
        )
        print("✅ Monte Carlo simulation completed")
    except Exception as e:
        print(f"⚠️ Monte Carlo failed: {e}")

    # Example: Consumption sensitivity scenarios
    try:
        print("📊 Running consumption sensitivity scenarios...")
        scenario_results = analyzer.consumption_sensitivity_scenarios(
            country="India",
            pathogen="E. coli",
            antibiotic="Ciprofloxacin",
            scenarios={
                '+50%': 1.5, '+20%': 1.2, 'Baseline': 1.0,
                '-20%': 0.8, '-50%': 0.5
            }
        )
        print("✅ Sensitivity scenarios completed")
    except Exception as e:
        print(f"⚠️ Sensitivity scenarios failed: {e}")

    # Example: Elasticity analysis
    try:
        print("📈 Calculating resistance elasticity...")
        elasticity_results = analyzer.elasticity_analysis(
            country="India",
            pathogen="E. coli",
            antibiotic="Ciprofloxacin"
        )
        if elasticity_results.get('elasticity') is not None:
            print(f"   Elasticity: {elasticity_results['elasticity']:.4f}")
        else:
            print(f"⚠️ Elasticity analysis: {elasticity_results.get('error', 'Failed')}")
    except Exception as e:
        print(f"⚠️ Elasticity analysis failed: {e}")

    print("\n📁 Analysis results saved to reports/ directory")

if __name__ == "__main__":
    main()
