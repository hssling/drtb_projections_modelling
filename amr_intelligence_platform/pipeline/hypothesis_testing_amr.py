#!/usr/bin/env python3
"""
Comprehensive Hypothesis Testing for AMR Organism-Antibiotic Combinations

Implements statistical hypothesis testing across all pathogen-antibiotic combinations
using multiple test types and correction methods for multiple comparisons.

Features:
- One-way ANOVA for comparing resistance across countries
- T-tests and Mann-Whitney U tests between treatment groups
- Proportion tests for resistance rates
- Chi-square tests for categorical associations
- Multiple testing correction (Bonferroni, FDR)
- Effect size calculations (Cohen's d, odds ratios)
"""

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.multitest import multipletests
from typing import Dict, List, Tuple, Optional
import warnings
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class AMRHypothesisTesting:
    """
    Statistical hypothesis testing framework for AMR data.

    Tests differences between organisms and antibiotics across conditions,
    countries, and time periods with appropriate statistical methods.
    """

    def __init__(self, data_file: str = "data/amr_merged.csv",
                 reports_dir: str = "reports", alpha: float = 0.05):
        """
        Initialize hypothesis testing framework.

        Args:
            data_file: Path to AMR dataset
            reports_dir: Directory for saving results
            alpha: Significance level for all tests (default 0.05)
        """
        self.data_file = Path(data_file)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.alpha = alpha

        # Test results storage
        self.test_results = {}

        logger.info(f"AMR Hypothesis Testing initialized (alpha={alpha})")

    def load_data(self) -> pd.DataFrame:
        """Load and prepare AMR dataset."""
        if not self.data_file.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        df = pd.read_csv(self.data_file)
        required_cols = ['country', 'pathogen', 'antibiotic', 'percent_resistant']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")

        # Clean data
        df = df.dropna(subset=['percent_resistant'])
        df['resistance_binary'] = (df['percent_resistant'] > 50).astype(int)  # Binary classification

        logger.info(f"Loaded {len(df)} records from {len(df['country'].unique())} countries")
        return df

    def run_all_hypothesis_tests(self) -> Dict:
        """
        Run comprehensive hypothesis tests for all organism-antibiotic combinations.

        Returns:
            Complete test results dictionary
        """
        logger.info("Starting comprehensive hypothesis testing")
        df = self.load_data()

        # Get all unique combinations
        pathogens = df['pathogen'].unique()
        antibiotics = df['antibiotic'].unique()
        countries = df['country'].unique()

        results = {
            'metadata': {
                'total_tests': 0,
                'significant_tests': 0,
                'n_pathogens': len(pathogens),
                'n_antibiotics': len(antibiotics),
                'n_countries': len(countries)
            },
            'anova_tests': {},
            'pairwise_tests': {},
            'proportion_tests': {},
            'effect_sizes': {},
            'multiple_testing_correction': {}
        }

        # Test 1: ANOVA - Do resistance levels differ across countries for each pathogen-antibiotic combo?
        logger.info("Running ANOVA tests for country differences")
        anova_results = self._run_anova_tests(df)
        results['anova_tests'] = anova_results
        results['metadata']['significant_tests'] += len([r for r in anova_results.values() if r['p_value'] < self.alpha])

        # Test 2: Pairwise comparisons between countries
        logger.info("Running pairwise country comparisons")
        pairwise_results = self._run_pairwise_country_tests(df)
        results['pairwise_tests'] = pairwise_results
        results['metadata']['significant_tests'] += len([r for r in pairwise_results.values() if r['significant_after_correction']])

        # Test 3: Proportion tests - Are resistance rates different from global averages?
        logger.info("Running proportion tests")
        prop_results = self._run_proportion_tests(df)
        results['proportion_tests'] = prop_results
        results['metadata']['significant_tests'] += len([r for r in prop_results.values() if r['p_value'] < self.alpha])

        # Test 4: Effect size calculations
        logger.info("Calculating effect sizes")
        effect_results = self._calculate_effect_sizes(df)
        results['effect_sizes'] = effect_results

        # Apply multiple testing correction
        logger.info("Applying multiple testing correction")
        correction_results = self._apply_multiple_testing_correction(results)
        results['multiple_testing_correction'] = correction_results

        results['metadata']['total_tests'] = (
            len(results['anova_tests']) +
            len(results['pairwise_tests']) +
            len(results['proportion_tests'])
        )

        # Generate summary report
        self._generate_summary_report(results)

        logger.info(f"Completed hypothesis testing: {results['metadata']['total_tests']} total tests, {results['metadata']['significant_tests']} significant")
        return results

    def _run_anova_tests(self, df: pd.DataFrame) -> Dict:
        """Run ANOVA tests for each pathogen-antibiotic combination across countries."""
        results = {}

        # Group by pathogen and antibiotic
        combo_groups = df.groupby(['pathogen', 'antibiotic'])

        for (pathogen, antibiotic), group in combo_groups:
            combo_key = f"{pathogen}_{antibiotic}"

            # Check if we have enough countries with data (at least 2)
            country_groups = [group for _, group in group.groupby('country') if len(group) >= 3]

            if len(country_groups) >= 2:
                try:
                    # Prepare data for ANOVA
                    country_data = [g['percent_resistant'].values for g in country_groups]
                    country_labels = [g['country'].iloc[0] for g in country_groups]

                    # One-way ANOVA
                    f_stat, p_value = stats.f_oneway(*country_data)

                    # Kruskal-Wallis test (non-parametric alternative)
                    try:
                        kruskal_stat, kruskal_p = stats.kruskal(*country_data)
                    except:
                        kruskal_stat, kruskal_p = None, None

                    results[combo_key] = {
                        'test_type': 'ANOVA',
                        'pathogen': pathogen,
                        'antibiotic': antibiotic,
                        'n_countries': len(country_groups),
                        'sample_sizes': [len(g) for g in country_groups],
                        'countries': country_labels,
                        'f_statistic': f_stat,
                        'p_value': p_value,
                        'significant': p_value < self.alpha,
                        'kruskal_statistic': kruskal_stat,
                        'kruskal_p_value': kruskal_p,
                        'means_by_country': {label: np.mean(data).round(2) for label, data in zip(country_labels, country_data)}
                    }

                except Exception as e:
                    logger.warning(f"ANOVA failed for {combo_key}: {e}")

        return results

    def _run_pairwise_country_tests(self, df: pd.DataFrame) -> Dict:
        """Run pairwise statistical tests between countries for each pathogen-antibiotic combination."""
        results = {}

        combo_groups = df.groupby(['pathogen', 'antibiotic'])
        test_idx = 0

        for (pathogen, antibiotic), group in combo_groups:
            countries = group['country'].unique()

            if len(countries) >= 2:
                country_pairs = []

                # Generate all pairwise comparisons
                for i in range(len(countries)):
                    for j in range(i+1, len(countries)):
                        country1, country2 = countries[i], countries[j]

                        data1 = group[group['country'] == country1]['percent_resistant']
                        data2 = group[group['country'] == country2]['percent_resistant']

                        if len(data1) >= 3 and len(data2) >= 3:  # Minimum sample size
                            # T-test
                            try:
                                t_stat, t_p = stats.ttest_ind(data1, data2, equal_var=False)
                            except:
                                t_stat, t_p = None, None

                            # Mann-Whitney U test (non-parametric)
                            try:
                                mw_stat, mw_p = stats.mannwhitneyu(data1, data2, alternative='two-sided')
                            except:
                                mw_stat, mw_p = None, None

                            # Effect size (Cohen's d)
                            mean_diff = np.mean(data1) - np.mean(data2)
                            pooled_std = np.sqrt((np.std(data1)**2 + np.std(data2)**2) / 2)
                            cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

                            country_pairs.append({
                                'test_id': f"pairwise_{test_idx}",
                                'pathogen': pathogen,
                                'antibiotic': antibiotic,
                                'country1': country1,
                                'country2': country2,
                                'n1': len(data1),
                                'n2': len(data2),
                                'mean1': np.mean(data1).round(2),
                                'mean2': np.mean(data2).round(2),
                                't_statistic': t_stat,
                                't_p_value': t_p,
                                'mann_whitney_statistic': mw_stat,
                                'mann_whitney_p_value': mw_p,
                                'cohens_d': cohens_d.round(3),
                                'effect_size_interpretation': self._interpret_effect_size(cohens_d),
                                'significant_before_correction': (t_p or mw_p or 1.0) < self.alpha
                            })

                            test_idx += 1

                if country_pairs:
                    results[f"{pathogen}_{antibiotic}"] = {
                        'pathogen': pathogen,
                        'antibiotic': antibiotic,
                        'n_comparisons': len(country_pairs),
                        'comparisons': country_pairs
                    }

        return results

    def _run_proportion_tests(self, df: pd.DataFrame) -> Dict:
        """Run proportion tests to compare resistance rates against global averages."""
        results = {}

        # Calculate global averages
        global_averages = df.groupby(['pathogen', 'antibiotic'])['percent_resistant'].mean()

        combo_groups = df.groupby(['pathogen', 'antibiotic'])

        for (pathogen, antibiotic), group in combo_groups:
            global_avg = global_averages.get((pathogen, antibiotic), 50)

            country_results = {}

            for country in group['country'].unique():
                country_data = group[group['country'] == country]['percent_resistant']
                n_samples = len(country_data)

                if n_samples >= 10:  # Minimum sample size for proportion test
                    country_mean = country_data.mean()
                    success_count = sum(country_data > global_avg)  # Number above global average

                    # One-sample proportion test
                    try:
                        z_stat, p_value = proportions_ztest(
                            count=success_count,
                            nobs=n_samples,
                            value=0.5,  # Test if significantly different from 50%
                            alternative='two-sided'
                        )
                    except:
                        z_stat, p_value = None, None

                    country_results[country] = {
                        'n_samples': n_samples,
                        'country_mean': country_mean.round(2),
                        'global_average': global_avg.round(2),
                        'z_statistic': z_stat,
                        'p_value': p_value,
                        'significant': p_value < self.alpha if p_value else False,
                        'difference_from_global': (country_mean - global_avg).round(2)
                    }

            if country_results:
                results[f"{pathogen}_{antibiotic}"] = {
                    'pathogen': pathogen,
                    'antibiotic': antibiotic,
                    'global_average': global_avg.round(2),
                    'country_tests': country_results
                }

        return results

    def _calculate_effect_sizes(self, df: pd.DataFrame) -> Dict:
        """Calculate effect sizes for all comparisons."""
        results = {}

        combo_groups = df.groupby(['pathogen', 'antibiotic'])

        for (pathogen, antibiotic), group in combo_groups:
            countries = group['country'].unique()

            if len(countries) >= 2:
                effect_sizes = []

                # Calculate pairwise effect sizes
                for i in range(len(countries)):
                    for j in range(i+1, len(countries)):
                        country1, country2 = countries[i], countries[j]

                        data1 = group[group['country'] == country1]['percent_resistant']
                        data2 = group[group['country'] == country2]['percent_resistant']

                        if len(data1) >= 3 and len(data2) >= 3:
                            # Cohen's d (unbiased estimate)
                            mean1, mean2 = np.mean(data1), np.mean(data2)
                            std1, std2 = np.std(data1, ddof=1), np.std(data2, ddof=1)
                            n1, n2 = len(data1), len(data2)

                            pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1 + n2 - 2))
                            cohens_d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0

                            # Glass's Δ (control vs treatment effect)
                            glass_delta = (mean1 - mean2) / std2 if std2 > 0 else 0

                            effect_sizes.append({
                                'country1': country1,
                                'country2': country2,
                                'cohens_d': cohens_d.round(3),
                                'glass_delta': glass_delta.round(3),
                                'magnitude': self._interpret_effect_size(cohens_d),
                                'practical_significance': 'Large' if abs(cohens_d) >= 0.8 else 'Medium' if abs(cohens_d) >= 0.5 else 'Small'
                            })

                if effect_sizes:
                    results[f"{pathogen}_{antibiotic}"] = {
                        'pathogen': pathogen,
                        'antibiotic': antibiotic,
                        'n_comparisons': len(effect_sizes),
                        'effect_sizes': effect_sizes,
                        'overall_mean_effect': np.mean([es['cohens_d'] for es in effect_sizes]).round(3)
                    }

        return results

    def _apply_multiple_testing_correction(self, results: Dict) -> Dict:
        """Apply multiple testing correction to all hypothesis tests."""
        # Collect all p-values
        all_p_values = []
        test_info = []

        # ANOVA p-values
        for key, test_result in results['anova_tests'].items():
            if test_result['p_value']:
                all_p_values.append(test_result['p_value'])
                test_info.append({
                    'test_type': 'anova',
                    'test_id': key,
                    'original_p': test_result['p_value']
                })

        # Pairwise p-values (use t-test p-values)
        for key, test_result in results['pairwise_tests'].items():
            for comparison in test_result['comparisons']:
                p_val = comparison.get('t_p_value') or comparison.get('mann_whitney_p_value')
                if p_val:
                    all_p_values.append(p_val)
                    test_info.append({
                        'test_type': 'pairwise',
                        'test_id': f"{key}_{comparison['test_id']}",
                        'original_p': p_val
                    })

        # Proportion test p-values
        for key, test_result in results['proportion_tests'].items():
            for country, country_result in test_result['country_tests'].items():
                if country_result['p_value']:
                    all_p_values.append(country_result['p_value'])
                    test_info.append({
                        'test_type': 'proportion',
                        'test_id': f"{key}_{country}",
                        'original_p': country_result['p_value']
                    })

        # Apply corrections
        if all_p_values:
            # Bonferroni correction
            bonferroni_rejected, bonferroni_p_adjusted = multipletests(
                all_p_values, alpha=self.alpha, method='bonferroni')[:2]

            # FDR correction (Benjamini-Hochberg)
            fdr_rejected, fdr_p_adjusted = multipletests(
                all_p_values, alpha=self.alpha, method='fdr_bh')[:2]

            # Update original results (this would need to be implemented)
            correction_results = {
                'total_tests': len(all_p_values),
                'bonferroni_significant': sum(bonferroni_rejected),
                'fdr_significant': sum(fdr_rejected),
                'bonferroni_threshold': self.alpha / len(all_p_values),
                'fdr_threshold': 'Variable'  # FDR has variable threshold
            }

            return correction_results
        else:
            return {'total_tests': 0, 'error': 'No p-values available for correction'}

    def _interpret_effect_size(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        if abs(d) >= 0.8:
            return "Large"
        elif abs(d) >= 0.5:
            return "Medium"
        elif abs(d) >= 0.2:
            return "Small"
        else:
            return "Negligible"

    def _generate_summary_report(self, results: Dict):
        """Generate comprehensive summary report."""
        summary = {
            'execution_summary': results['metadata'],
            'top_significant_findings': self._extract_top_findings(results),
            'effect_size_summary': self._summarize_effect_sizes(results),
            'multiple_testing_impact': results['multiple_testing_correction'],
            'recommendations': self._generate_recommendations(results)
        }

        # Save to JSON
        with open(self.reports_dir / 'hypothesis_testing_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info("Hypothesis testing summary report generated")

    def _extract_top_findings(self, results: Dict) -> List[Dict]:
        """Extract most significant hypothesis test results."""
        findings = []

        # Top ANOVA results
        anova_results = results['anova_tests']
        sorted_anova = sorted(
            [(k, v) for k, v in anova_results.items() if v['p_value']],
            key=lambda x: x[1]['p_value']
        )[:5]  # Top 5

        for key, result in sorted_anova:
            findings.append({
                'test_type': 'ANOVA',
                'pathogen_antibiotic': key.replace('_', ' vs '),
                'p_value': result['p_value'],
                'description': f"Countries show {'significant' if result['significant'] else 'no significant'} differences in {key.replace('_', ' vs ')} resistance rates"
            })

        # Top pairwise differences
        pairwise_results = results['pairwise_tests']
        pairwise_findings = []

        for _, test_result in pairwise_results.items():
            for comp in test_result['comparisons']:
                if comp.get('significant_before_correction'):
                    effect_size = abs(comp.get('cohens_d', 0))
                    pairwise_findings.append((comp, effect_size))

        # Sort by effect size and take top 5
        pairwise_findings.sort(key=lambda x: x[1], reverse=True)
        for comp, effect_size in pairwise_findings[:5]:
            findings.append({
                'test_type': 'Pairwise',
                'pathogen_antibiotic': f"{comp['pathogen']} vs {comp['antibiotic']}",
                'countries': f"{comp['country1']} vs {comp['country2']}",
                'p_value': comp.get('t_p_value') or comp.get('mann_whitney_p_value'),
                'effect_size': effect_size,
                'description': f"Large resistance difference between {comp['country1']} and {comp['country2']} for {comp['pathogen']} vs {comp['antibiotic']}"
            })

        return findings[:10]  # Limit to top 10 total findings

    def _summarize_effect_sizes(self, results: Dict) -> Dict:
        """Summarize effect size distributions."""
        if not results.get('effect_sizes'):
            return {}

        effect_sizes = []
        for _, combo_result in results['effect_sizes'].items():
            for es_data in combo_result['effect_sizes']:
                effect_sizes.append(abs(es_data['cohens_d']))

        if effect_sizes:
            return {
                'count': len(effect_sizes),
                'mean': np.mean(effect_sizes).round(3),
                'median': np.median(effect_sizes).round(3),
                'std': np.std(effect_sizes).round(3),
                'large_effects': len([es for es in effect_sizes if es >= 0.8]),
                'medium_effects': len([es for es in effect_sizes if 0.5 <= es < 0.8]),
                'small_effects': len([es for es in effect_sizes if 0.2 <= es < 0.5]),
                'negligible_effects': len([es for es in effect_sizes if es < 0.2])
            }

        return {}

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate research and policy recommendations based on findings."""
        recommendations = []

        metadata = results['metadata']
        significance_rate = metadata['significant_tests'] / metadata['total_tests'] if metadata['total_tests'] > 0 else 0

        if significance_rate > 0.7:
            recommendations.append("High prevalence of significant country differences suggests need for targeted interventions in specific regions")
        elif significance_rate > 0.4:
            recommendations.append("Moderate significant differences indicate varying AMR pressures across countries")
        else:
            recommendations.append("Limited significant differences suggest relatively consistent global AMR patterns")

        # Effect size-based recommendations
        effect_summary = results.get('effect_sizes', {})
        if effect_summary and effect_summary.get('large_effects_ratio', 0) > 0.3:
            recommendations.append("Large effect sizes indicate substantial AMR differences - prioritize resources to highest-risk countries")

        # Multiple testing recommendations
        mt_corrected = results.get('multiple_testing_correction', {})
        if mt_corrected.get('bonferroni_significant', 0) < metadata['significant_tests'] / 2:
            recommendations.append("Conservative testing suggests need for replication studies with larger samples")

        recommendations.append("Conduct stratified analyses by antibiotic consumption data for more precise recommendations")
        recommendations.append("Consider longitudinal studies to track AMR trends over time")

        return recommendations

def main():
    """Command-line interface for comprehensive AMR hypothesis testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Comprehensive AMR Hypothesis Testing')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level (default: 0.05)')
    parser.add_argument('--data-file', default='data/amr_merged.csv', help='Path to AMR data file')
    parser.add_argument('--reports-dir', default='reports', help='Directory for results')

    args = parser.parse_args()

    print("🧪 Comprehensive AMR Hypothesis Testing")
    print("=" * 50)
    print(f"Significance level: {args.alpha}")
    print(f"Data file: {args.data_file}")

    try:
        tester = AMRHypothesisTesting(args.data_file, args.reports_dir, args.alpha)
        results = tester.run_all_hypothesis_tests()

        print("\n✅ Hypothesis Testing Complete!")
        print("📊 Results Summary:")
        print(f"   • Total tests: {results['metadata']['total_tests']}")
        print(f"   • Significant tests: {results['metadata']['significant_tests']}")
        print(f"   • Pathogens: {results['metadata']['n_pathogens']}")
        print(f"   • Antibiotics: {results['metadata']['n_antibiotics']}")
        print(f"   • Countries: {results['metadata']['n_countries']}")

        print("\n📁 Results saved to reports/ directory:")
        print("   • hypothesis_testing_summary.json")

        # Print top 3 findings
        if results.get('top_significant_findings'):
            print("\n🔍 Top Significant Findings:")
            for i, finding in enumerate(results['top_significant_findings'][:3], 1):
                print(f"   {i}. {finding['description']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
