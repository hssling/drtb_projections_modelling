#!/usr/bin/env python3
"""
AMR Meta-Analysis Module

Integrates systematic literature review with forecasting models to provide
comprehensive evidence synthesis for AMR surveillance and policy decisions.

Features:
- Automated literature search via EuropePMC API
- Systematic review of published AMR studies
- Meta-analysis of resistance proportions
- Forest plots and funnel plots for publication bias detection
- Integration with forecasting models for evidence validation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import json
import re
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import time

# Statistical packages for meta-analysis
try:
    from statsmodels.stats.meta_analysis import combine_effects, effectsize_proportions
    import statsmodels.api as sm
    STATS_MODELS_AVAILABLE = True
except ImportError:
    STATS_MODELS_AVAILABLE = False
    warnings.warn("statsmodels not available - meta-analysis functionality limited")

logger = logging.getLogger(__name__)

class AMRMetaAnalysis:
    """
    Comprehensive meta-analysis framework for AMR research.

    Combines automated literature review with statistical synthesis
    to provide evidence-based validation of forecasting models.
    """

    def __init__(self, literature_file: str = "data/amr_meta_literature.csv",
                 reports_dir: str = "reports"):
        """
        Initialize meta-analysis system.

        Args:
            literature_file: CSV file containing extracted literature data
            reports_dir: Directory for saving analysis results
        """
        self.literature_file = Path(literature_file)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True, parents=True)

        # EuropePMC API settings
        self.europe_pmc_base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        self.search_cache = {}
        self.rate_limit_delay = 1.0  # seconds between API calls

        logger.info("AMR Meta-Analysis module initialized")

    def search_literature(self, pathogen: str, antibiotic: str,
                         country: str = None, max_results: int = 100) -> pd.DataFrame:
        """
        Search EuropePMC for AMR studies and extract metadata.

        Args:
            pathogen: Pathogen name (e.g., "E. coli")
            antibiotic: Antibiotic name (e.g., "Ciprofloxacin")
            country: Country filter (optional)
            max_results: Maximum number of results to retrieve

        Returns:
            DataFrame with study metadata and extracted information
        """
        logger.info(f"Searching literature for {pathogen} + {antibiotic}")

        # Build search query
        query_parts = [
            f'"{pathogen}"',
            f'"{antibiotic}"',
            "resistance",
            "antimicrobial"
        ]

        if country and country.lower() not in ['global', 'all']:
            query_parts.append(f'"{country}"')

        query = " AND ".join(query_parts)

        try:
            results = self._query_european_pmc(query, max_results)
            studies = self._parse_search_results(results, pathogen, antibiotic, country)

            if studies:
                df = pd.DataFrame(studies)
                logger.info(f"Found {len(df)} relevant studies")

                # Save to literature file
                self._append_to_literature_database(df)
                return df
            else:
                logger.warning(f"No studies found for {pathogen} + {antibiotic}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Literature search failed: {e}")
            return pd.DataFrame()

    def _query_european_pmc(self, query: str, max_results: int = 100) -> List[Dict]:
        """Query EuropePMC API for studies."""
        results = []
        page_size = min(25, max_results)  # API limits page size

        for page in range(0, max_results, page_size):
            if len(results) >= max_results:
                break

            params = {
                'query': query,
                'format': 'json',
                'pageSize': str(page_size),
                'page': str(page // page_size + 1)
            }

            try:
                response = requests.get(self.europe_pmc_base_url, params=params)
                response.raise_for_status()

                data = response.json()
                page_results = data.get('resultList', {}).get('result', [])

                if not page_results:
                    break

                results.extend(page_results)

                # Rate limiting
                time.sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"API query failed: {e}")
                break

        return results[:max_results]

    def _parse_search_results(self, results: List[Dict], pathogen: str,
                           antibiotic: str, country: str = None) -> List[Dict]:
        """Parse EuropePMC results into structured study data."""
        studies = []

        for result in results:
            try:
                title = result.get('title', '')
                abstract = result.get('abstractText', '')
                year = result.get('pubYear', '')

                # Extract study information from title/abstract
                extracted_data = self._extract_study_data(title + " " + abstract)

                if extracted_data:
                    study = {
                        'study_id': result.get('id', ''),
                        'title': title,
                        'abstract': abstract[:500],  # Truncate for storage
                        'year': year,
                        'journal': result.get('journalTitle', ''),
                        'authors': result.get('authorString', ''),
                        'pmcid': result.get('pmcid', ''),
                        'pmid': result.get('pmid', ''),
                        'doi': result.get('doi', ''),
                        'pathogen': pathogen,
                        'antibiotic': antibiotic,
                        'country': country or self._extract_country(title + " " + abstract),
                        **extracted_data
                    }
                    studies.append(study)

            except Exception as e:
                logger.debug(f"Parsing failed for result: {e}")
                continue

        return studies

    def _extract_study_data(self, text: str) -> Optional[Dict]:
        """Extract sample sizes and resistance counts from text using regex."""
        text_lower = text.lower()

        # Look for resistance patterns
        patterns = {
            'sample_size': [
                r'n\s*[\=\:]\s*(\d+)',
                r'tested\s*[\:\=]\s*(\d+)',
                r'sample\s*size\s*[\:\=]\s*(\d+)',
                r'n\s*=\s*(\d+)'
            ],
            'resistant': [
                r'resistant\s*[\:\=]\s*(\d+)',
                r'resistance\s*rate\s*[\:\=]\s*(\d+)',
                r'resistant\s*\(\s*(\d+)',
                r'(\d+)\s*resistant'
            ]
        }

        extracted = {}

        # Try to extract numbers
        for field, regexes in patterns.items():
            for regex in regexes:
                matches = re.findall(regex, text_lower)
                if matches:
                    # Take the first reasonable number (not years, etc.)
                    for match in matches:
                        try:
                            num = int(match)
                            if 1 <= num <= 10000:  # Reasonable range
                                extracted[field] = num
                                break
                        except ValueError:
                            continue
                    if field in extracted:
                        break

        return extracted if 'resistant' in extracted and 'sample_size' in extracted else None

    def _extract_country(self, text: str) -> str:
        """Extract country names from text."""
        countries = [
            'India', 'China', 'United States', 'USA', 'UK', 'United Kingdom',
            'Germany', 'France', 'Italy', 'Spain', 'Japan', 'Brazil',
            'Russia', 'Canada', 'Australia', 'South Korea'
        ]

        for country in countries:
            if country.lower() in text.lower():
                return country

        return 'Unknown'

    def _append_to_literature_database(self, new_studies: pd.DataFrame):
        """Append new studies to the literature database."""
        try:
            if self.literature_file.exists():
                existing = pd.read_csv(self.literature_file)
                combined = pd.concat([existing, new_studies], ignore_index=True)
                combined.drop_duplicates(subset=['study_id'], keep='first', inplace=True)
            else:
                combined = new_studies

            combined.to_csv(self.literature_file, index=False)
            logger.info(f"Added {len(new_studies)} studies to literature database")

        except Exception as e:
            logger.error(f"Failed to update literature database: {e}")

    def run_meta_analysis(self, pathogen: str, antibiotic: str,
                         country: str = None, method: str = 'random') -> Dict:
        """
        Perform meta-analysis on extracted literature data.

        Args:
            pathogen: Pathogen filter
            antibiotic: Antibiotic filter
            country: Country filter (optional)
            method: Meta-analysis method ('fixed' or 'random')

        Returns:
            Meta-analysis results dictionary
        """
        logger.info(f"Running meta-analysis for {pathogen} + {antibiotic}")

        try:
            # Load literature data
            if not self.literature_file.exists():
                logger.error("Literature database not found. Run search_literature() first.")
                return {}

            df = pd.read_csv(self.literature_file)

            # Apply filters
            filters = {'pathogen': pathogen, 'antibiotic': antibiotic}
            if country:
                filters['country'] = country

            for col, value in filters.items():
                if col in df.columns:
                    df = df[df[col].str.lower() == value.lower()]

            if df.empty:
                logger.warning("No studies match the specified criteria")
                return {}

            # Filter out unreasonable values
            df = df[
                (df['sample_size'] > 0) &
                (df['sample_size'] <= 10000) &
                (df['resistant'] >= 0) &
                (df['resistant'] <= df['sample_size'])
            ]

            if len(df) < 2:
                logger.warning("Need at least 2 studies for meta-analysis")
                return {}

            # Calculate proportions
            df['proportion'] = df['resistant'] / df['sample_size']
            df['variance'] = (df['proportion'] * (1 - df['proportion'])) / df['sample_size']
            df['se'] = np.sqrt(df['variance'])
            df['ci_lower'] = df['proportion'] - 1.96 * df['se']
            df['ci_upper'] = df['proportion'] + 1.96 * df['se']

            if not STATS_MODELS_AVAILABLE:
                logger.warning("statsmodels not available - using basic pooling")
                # Basic fixed effects pooling
                weights = 1 / df['variance']
                pooled_prop = np.sum(df['proportion'] * weights) / np.sum(weights)
                pooled_se = 1 / np.sqrt(np.sum(weights))
                pooled_var = pooled_se ** 2
            else:
                # Advanced meta-analysis with statsmodels
                try:
                    # Use method_re="dl" for DerSimonian-Laird random effects
                    method_re = 'dl' if method == 'random' else None
                    effect = combine_effects(df['proportion'], df['variance'],
                                           method_re=method_re)

                    pooled_effect, pooled_var = effect

                    if hasattr(pooled_effect, 'summary_frame'):
                        pooled_df = pooled_effect.summary_frame()
                        pooled_prop = pooled_df['coef'].iloc[0] if 'coef' in pooled_df.columns else pooled_effect
                        pooled_var = pooled_df['std err'].iloc[0]**2 if 'std err' in pooled_df.columns else pooled_var
                    else:
                        pooled_prop = float(pooled_effect)
                        pooled_var = float(pooled_var)

                except Exception as e:
                    logger.warning(f"Advanced meta-analysis failed, using basic pooling: {e}")
                    weights = 1 / df['variance']
                    pooled_prop = np.sum(df['proportion'] * weights) / np.sum(weights)
                    pooled_var = 1 / np.sum(weights)

            # Calculate confidence intervals
            pooled_se = np.sqrt(pooled_var)
            ci_lower = pooled_prop - 1.96 * pooled_se
            ci_upper = pooled_prop + 1.96 * pooled_se

            # Heterogeneity statistics (simplified)
            q_stat = np.sum(weights * (df['proportion'] - pooled_prop)**2) if 'weights' in locals() else 0
            df_resid = len(df) - 1
            i_squared = max(0, (q_stat - df_resid) / q_stat * 100) if q_stat > df_resid else 0

            results = {
                'pooled_proportion': pooled_prop,
                'pooled_percent': pooled_prop * 100,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'ci_lower_percent': ci_lower * 100,
                'ci_upper_percent': ci_upper * 100,
                'heterogeneity_i2': i_squared,
                'n_studies': len(df),
                'method': method,
                'studies': df[['study_id', 'year', 'country', 'sample_size',
                             'resistant', 'proportion']].to_dict('records')
            }

            # Generate visualizations
            self._create_forest_plot(df, results, pathogen, antibiotic, country)
            self._create_funnel_plot(df, results, pathogen, antibiotic, country)

            # Save results
            self._save_meta_results(results, pathogen, antibiotic, country)

            logger.info(f"Meta-analysis complete: {pooled_prop:.1%} "
                       f"(95% CI: {ci_lower:.1%} - {ci_upper:.1%})")

            return results

        except Exception as e:
            logger.error(f"Meta-analysis failed: {e}")
            return {}

    def _create_forest_plot(self, df: pd.DataFrame, results: Dict,
                           pathogen: str, antibiotic: str, country: str = None):
        """Create forest plot for meta-analysis results."""
        fig, ax = plt.subplots(figsize=(12, max(6, len(df) * 0.5)))

        # Study-level estimates
        for i, (_, study) in enumerate(df.iterrows()):
            ax.errorbar(study['proportion'], i,
                       xerr=1.96 * study['se'],
                       fmt='o', color='blue', markersize=4, capsize=3)
            ax.axhline(i, color='gray', alpha=0.3, linestyle='--')

        # Pooled estimate
        pooled_y = len(df) + 1
        ax.errorbar(results['pooled_proportion'], pooled_y,
                   xerr=1.96 * np.sqrt(results.get('pooled_var', 0.001)),
                   fmt='D', color='red', markersize=8, capsize=5,
                   label='Pooled Estimate')

        # Confidence interval shading
        ax.axvspan(results['ci_lower'], results['ci_upper'],
                  alpha=0.2, color='red', label='95% Confidence Interval')

        # Formatting
        ax.set_yticks(range(len(df) + 2))
        ax.set_yticklabels([f"{row['study_id'][:15]}..." if len(row['study_id']) > 15
                           else row['study_id'] for _, row in df.iterrows()] +
                          [''] + ['Pooled'])
        ax.set_xlabel('Proportion Resistant')
        ax.set_title(f'Forest Plot: {pathogen} vs {antibiotic}' +
                    (f' in {country}' if country else ''))

        ax.axvline(results['pooled_proportion'], color='red', linestyle='--', alpha=0.7)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save
        country_suffix = f"_{country}" if country else ""
        filename = f"meta_forest_{pathogen}_{antibiotic}{country_suffix}.png".replace(" ", "_")
        plt.savefig(self.reports_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Forest plot saved: {filename}")

    def _create_funnel_plot(self, df: pd.DataFrame, results: Dict,
                           pathogen: str, antibiotic: str, country: str = None):
        """Create funnel plot for publication bias assessment."""
        fig, ax = plt.subplots(figsize=(8, 8))

        # Calculate precision (1/SE)
        df_plot = df.copy()
        df_plot['precision'] = 1 / df_plot['se']
        df_plot['std_error'] = df_plot['se']

        # Plot studies
        ax.scatter(df_plot['std_error'], df_plot['proportion'],
                  alpha=0.7, color='blue', s=50)

        # Add reference lines for funnel shape
        se_range = np.linspace(df_plot['std_error'].min(), df_plot['std_error'].max(), 100)
        ax.plot(se_range, results['pooled_proportion'] + 1.96 * se_range,
               'r--', alpha=0.7, label='95% CI Upper')
        ax.plot(se_range, results['pooled_proportion'] - 1.96 * se_range,
               'r--', alpha=0.7, label='95% CI Lower')

        ax.axhline(results['pooled_proportion'], color='red', linestyle='-',
                  alpha=0.8, label='Pooled Estimate')

        ax.set_xlabel('Standard Error (1/Precision)')
        ax.set_ylabel('Proportion Resistant')
        ax.set_title(f'Funnel Plot: {pathogen} vs {antibiotic}' +
                    (f' in {country}' if country else ''))
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save
        country_suffix = f"_{country}" if country else ""
        filename = f"meta_funnel_{pathogen}_{antibiotic}{country_suffix}.png".replace(" ", "_")
        plt.savefig(self.reports_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Funnel plot saved: {filename}")

    def _save_meta_results(self, results: Dict, pathogen: str,
                          antibiotic: str, country: str = None):
        """Save meta-analysis results to CSV."""
        country_suffix = f"_{country}" if country else ""
        filename = f"meta_results_{pathogen}_{antibiotic}{country_suffix}.csv".replace(" ", "_")

        results_df = pd.DataFrame([{
            'pathogen': pathogen,
            'antibiotic': antibiotic,
            'country': country or 'All',
            'method': results.get('method', 'random'),
            'pooled_proportion': results.get('pooled_proportion'),
            'pooled_percent': results.get('pooled_percent'),
            'ci_lower': results.get('ci_lower'),
            'ci_upper': results.get('ci_upper'),
            'ci_lower_percent': results.get('ci_lower_percent'),
            'ci_upper_percent': results.get('ci_upper_percent'),
            'heterogeneity_i2': results.get('heterogeneity_i2'),
            'n_studies': results.get('n_studies'),
            'date': pd.Timestamp.now().strftime('%Y-%m-%d')
        }])

        results_df.to_csv(self.reports_dir / filename, index=False)
        logger.info(f"Meta-analysis results saved: {filename}")

    def compare_with_forecast(self, meta_results: Dict, forecast_data: Dict) -> Dict:
        """
        Compare meta-analysis pooled estimate with forecasting model predictions.

        Args:
            meta_results: Results from run_meta_analysis()
            forecast_data: Forecast results from forecasting models

        Returns:
            Comparison analysis
        """
        try:
            meta_pooled = meta_results.get('pooled_proportion', 0)
            meta_ci_lower = meta_results.get('ci_lower', 0)
            meta_ci_upper = meta_results.get('ci_upper', 0)

            # Extract forecast values (assuming forecast_data format)
            if 'yhat' in forecast_data:
                # Single forecast scenario
                forecast_values = [forecast_data['yhat']]
            elif isinstance(forecast_data, list) and len(forecast_data) > 0:
                # Multiple scenarios
                forecast_values = [f.get('yhat', 0) if isinstance(f, dict) else f for f in forecast_data]
            else:
                logger.error("Invalid forecast data format")
                return {}

            # Find best matching forecast period (assume next 2-3 years)
            current_time = pd.Timestamp.now()
            forecast_horizon = len(forecast_values) // 4  # First quarter as example

            if forecast_horizon < len(forecast_values):
                end_forecast = np.mean(forecast_values[-forecast_horizon:])
                end_forecast = end_forecast / 100 if end_forecast > 1 else end_forecast  # Normalize if %
            else:
                end_forecast = np.mean(forecast_values)
                end_forecast = end_forecast / 100 if end_forecast > 1 else end_forecast

            # Statistical comparison
            difference = end_forecast - meta_pooled
            z_score = abs(difference) / ((meta_ci_upper - meta_ci_lower) / (2 * 1.96))
            agreement = "Strong agreement" if z_score < 1 else ("Moderate agreement" if z_score < 2 else "Significant difference")

            comparison = {
                'meta_estimate': meta_pooled * 100,  # Convert to %
                'meta_ci': (meta_ci_lower * 100, meta_ci_upper * 100),
                'forecast_estimate': end_forecast * 100,
                'difference_percent': difference * 100,
                'z_score': z_score,
                'agreement_level': agreement,
                'forecast_period': f"Next {forecast_horizon//12} year(s)" if forecast_horizon > 12 else f"Next {forecast_horizon} months"
            }

            logger.info(f"Meta-forecast comparison: {agreement} "
                       f"(Z={z_score:.2f}, Difference={difference*100:.1f}%)")

            return comparison

        except Exception as e:
            logger.error(f"Forecast comparison failed: {e}")
            return {}

def main():
    """Command-line interface for meta-analysis."""

    analyzer = AMRMetaAnalysis()

    # Example workflow
    pathogen = "E. coli"
    antibiotic = "Ciprofloxacin"
    country = "India"

    print("🧪 AMR Meta-Analysis System")
    print("=" * 50)

    # Step 1: Search literature (if needed)
    print("\n📚 Step 1: Literature Search")
    try:
        studies = analyzer.search_literature(pathogen, antibiotic, country)
        if not studies.empty:
            print(f"✅ Found {len(studies)} relevant studies")
        else:
            print("⚠️ No new studies found, using existing database")
    except Exception as e:
        print(f"⚠️ Literature search failed: {e}")

    # Step 2: Run meta-analysis
    print("\n📊 Step 2: Meta-Analysis")
    try:
        meta_results = analyzer.run_meta_analysis(pathogen, antibiotic, country)

        if meta_results:
            pooled = meta_results.get('pooled_proportion', 0) * 100
            ci_lower = meta_results.get('ci_lower', 0) * 100
            ci_upper = meta_results.get('ci_upper', 0) * 100
            n_studies = meta_results.get('n_studies', 0)

            print(f"   Pooled Resistance: {pooled:.1f}% (95% CI: {ci_lower:.1f}% - {ci_upper:.1f}%) from {n_studies} studies")
            print("📈 Results saved to reports/ directory")
        else:
            print("❌ Meta-analysis failed - insufficient data")
    except Exception as e:
        print(f"❌ Meta-analysis execution failed: {e}")

    print("\n✅ Meta-analysis complete!")

if __name__ == "__main__":
    main()
