#!/usr/bin/env python3
"""
TB-AMR Meta-Analysis Pipeline

Systematic literature synthesis for TB-AMR research in India.
Searches PubMed/MEDLINE for prevalence studies, extracts effect sizes,
and computes pooled estimates with forest plots and heterogeneity analysis.
"""

import pandas as pd
import numpy as np
import requests
import json
import re
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TBAMRMetaAnalysis:
    """Meta-analysis of TB-AMR literature for India."""

    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = None  # Add API key for higher rate limits
        self.data_dir = Path("../data/meta_analysis")

        # PICO framework for TB-AMR
        self.search_terms = [
            # Drug resistance terms
            "tuberculosis[MeSH] AND drug resistance[MeSH]",
            "tuberculosis[MeSH] AND multidrug resistant",
            "MDR tuberculosis India",
            "tuberculosis rifampicin resistant India",
            "tuberculosis XDR India",

            # Specific drugs
            "tuberculosis fluoroquinolone resistance India",
            "tuberculosis isoniazid resistance India",

            # Treatment failure
            "tuberculosis treatment failure India",
        ]

    def pubmed_search(self, query, max_results=500):
        """
        Search PubMed for TB-AMR studies in India.
        Returns list of PMIDs and basic metadata.
        """
        print(f"🔍 Searching PubMed: {query}")

        # API parameters
        params = {
            'db': 'pubmed',
            'term': query + " AND India[MeSH]",
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'relevance'
        }

        if self.api_key:
            params['api_key'] = self.api_key

        # Search for PMIDs
        search_url = f"{self.base_url}esearch.fcgi"
        response = requests.get(search_url, params=params)

        if response.status_code != 200:
            print(f"❌ PubMed search failed: {response.status_code}")
            return []

        data = response.json()
        pmids = data.get('esearchresult', {}).get('idlist', [])

        print(f"✅ Found {len(pmids)} potentially relevant studies")
        return pmids

    def fetch_abstracts(self, pmids):
        """
        Fetch detailed metadata and abstracts for given PMIDs.
        Returns structured data for data extraction.
        """
        print(f"📄 Fetching abstracts for {len(pmids)} studies...")

        # Process in batches to avoid API limits
        batch_size = 50
        all_data = []

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i+batch_size]

            # Fetch summaries
            summary_params = {
                'db': 'pubmed',
                'id': ','.join(batch),
                'retmode': 'json'
            }

            summary_url = f"{self.base_url}esummary.fcgi"
            summary_resp = requests.get(summary_url, params=summary_params)

            if summary_resp.status_code != 200:
                print(f"⚠️ Failed to fetch batch {i//batch_size + 1}")
                continue

            summary_data = summary_resp.json()

            # Extract study information
            for pmid in batch:
                article = summary_data.get('result', {}).get(pmid, {})

                study_data = {
                    'pmid': pmid,
                    'title': article.get('title', ''),
                    'authors': ', '.join([a.get('name', '') for a in article.get('authors', [])]),
                    'journal': article.get('fulljournalname', ''),
                    'year': article.get('pubdate', '').split()[0] if article.get('pubdate') else '',
                    'doi': article.get('elocationid', ''),
                }

                all_data.append(study_data)

        print(f"✅ Processed {len(all_data)} studies with metadata")
        return all_data

    def extract_prevalence_data(self, study_data):
        """
        Extract prevalence estimates from study abstracts/titles.
        Uses regex patterns to identify resistance percentages.
        """
        print("📊 Extracting prevalence estimates...")

        extracted_data = []

        # Regex patterns for prevalence extraction
        prevalence_patterns = [
            r'MDR.*?(\d+(?:\.\d+)?)%',  # MDR X%
            r'rifampicin.*?resistant.*?(\d+(?:\.\d+)?)%',  # rifampicin resistant X%
            r'fluoroquinolone.*?resistance.*?(\d+(?:\.\d+)?)%',  # fluoroquinolone resistance X%
            r'drug.resistant.*?(\d+(?:\.\d+)?)%',  # drug resistant X%
        ]

        for study in study_data:
            text = f"{study['title']} {getattr(study, 'abstract', '')}"

            extractions = []
            for pattern in prevalence_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        percent = float(match)
                        if 0 <= percent <= 100:  # Valid percentage
                            extractions.append({
                                'pmid': study['pmid'],
                                'title': study['title'][:100] + '...' if len(study['title']) > 100 else study['title'],
                                'year': study['year'],
                                'prevalence_percent': percent,
                                'resistance_type': self._classify_resistance_type(text),
                                'sample_size': self._extract_sample_size(text),
                                'confidence_interval': self._extract_ci(text)
                            })
                    except ValueError:
                        continue

            if extractions:
                extracted_data.extend(extractions)

        print(f"✅ Extracted prevalence data from {len(extracted_data)} data points")
        return pd.DataFrame(extracted_data)

    def _classify_resistance_type(self, text):
        """Classify type of resistance based on text content."""
        text_lower = text.lower()

        if 'mdr' in text_lower or 'multidrug' in text_lower:
            return 'MDR'
        elif 'xdr' in text_lower or 'extensively' in text_lower:
            return 'XDR'
        elif 'rifampicin' in text_lower or 'rifampin' in text_lower:
            return 'RR'
        elif 'fluoroquinolone' in text_lower or 'ofloxacin' in text_lower or 'levofloxacin' in text_lower:
            return 'FQ'
        elif 'isoniazid' in text_lower:
            return 'INH'
        else:
            return 'Other'

    def _extract_sample_size(self, text):
        """Extract sample size from text (n=X patterns)."""
        patterns = [
            r'n\s*=\s*(\d+)',
            r'sample.*?(\d+)',
            r'(\d+).*?patients',
            r'(\d+).*?cases'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        size = int(match)
                        if size > 0 and size < 100000:  # Reasonable range
                            return size
                    except ValueError:
                        continue
        return np.nan

    def _extract_ci(self, text):
        """Extract confidence intervals where available."""
        # Look for CI patterns like "95% CI: 10.2-15.8" or "(10.2-15.8)"
        ci_patterns = [
            r'95%.*?CI.*?:?\s*([\d.-]+)-([\d.-]+)',
            r'confidence.*?interval.*?:?\s*([\d.-]+)-([\d.-]+)',
            r'\(([\d.-]+)-([\d.-]+)\)'
        ]

        for pattern in ci_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    lower, upper = float(match.group(1)), float(match.group(2))
                    return f"{lower:.1f}-{upper:.1f}"
                except (ValueError, IndexError):
                    continue
        return None

    def compute_meta_analysis(self, extracted_data):
        """
        Perform meta-analysis on extracted prevalence data.
        Returns pooled estimates with heterogeneity statistics.
        """
        print("🔬 Computing meta-analysis...")

        results = {}

        # Group by resistance type
        for resistance_type in extracted_data['resistance_type'].unique():
            subset = extracted_data[extracted_data['resistance_type'] == resistance_type]

            if len(subset) < 3:  # Need minimum studies for meta-analysis
                continue

            # Simple random effects meta-analysis (simplified)
            studies = []
            variances = []

            for _, study in subset.iterrows():
                prevalence = study['prevalence_percent'] / 100  # Convert to proportion
                n = study['sample_size']

                if pd.isna(n) or n <= 0:
                    n = 100  # Default sample size

                # Standard error for proportion
                se = np.sqrt(prevalence * (1 - prevalence) / n)
                studies.append(prevalence)
                variances.append(se ** 2)

            # Fixed effect meta-analysis
            weights = [1/var for var in variances]
            total_weight = sum(weights)

            pooled_effect = sum([study * weight for study, weight in zip(studies, weights)]) / total_weight
            pooled_se = np.sqrt(1 / total_weight)

            # Confidence interval (95%)
            ci_lower = pooled_effect - 1.96 * pooled_se
            ci_upper = pooled_effect + 1.96 * pooled_se

            # Heterogeneity (I² statistic - simplified)
            q_stat = sum(weights * [(study - pooled_effect)**2 for study in studies])
            df = len(studies) - 1
            i_squared = max(0, (q_stat - df) / q_stat) * 100 if q_stat > df else 0

            results[resistance_type] = {
                'pooled_prevalence': pooled_effect * 100,  # Back to percentage
                'ci_lower': max(0, ci_lower * 100),
                'ci_upper': min(100, ci_upper * 100),
                'n_studies': len(studies),
                'total_n': subset['sample_size'].sum(),
                'i_squared': i_squared,
                'studies': subset.to_dict('records')
            }

        print("✅ Meta-analysis completed")
        return results

    def create_forest_plot(self, meta_results, output_file):
        """Create forest plot for meta-analysis results."""
        print("📊 Creating forest plot...")

        fig, ax = plt.subplots(figsize=(12, 8))

        y_pos = 0
        labels = []

        for resistance_type, results in meta_results.items():
            # Plot individual studies
            y_study = y_pos
            for study in results['studies']:
                ax.plot([study['prevalence_percent'], study['prevalence_percent']],
                       [y_study - 0.3, y_study + 0.3], 'ko-', markersize=4, linewidth=1)
                ax.text(study['prevalence_percent'] + 0.5, y_study,
                       f"{study['title'][:50]}...",
                       fontsize=8, verticalalignment='center')
                y_study += 1

            # Plot pooled estimate
            pooled = results['pooled_prevalence']
            ci_lower = results['ci_lower']
            ci_upper = results['ci_upper']

            ax.plot([ci_lower, ci_upper], [y_pos - 0.5, y_pos - 0.5], 'k-', linewidth=2)
            ax.plot([pooled, pooled], [y_pos - 0.8, y_pos - 0.2], 'ks', markersize=8)

            labels.append(f"{resistance_type}\n(n={results['n_studies']} studies)")
            y_pos += len(results['studies']) + 2

        ax.set_xlabel('Resistance Prevalence (%)')
        ax.set_title('Forest Plot: TB-AMR Prevalence in India')
        ax.set_yticks([])
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close ()
        print(f"📊 Forest plot saved → {output_file}")

    def run_meta_analysis(self, search_terms=None, max_studies=200):
        """
        Complete meta-analysis pipeline from search to forest plots.
        """
        print("TB-AMR Meta-Analysis Pipeline")
        print("=" * 40)

        self.data_dir.mkdir(parents=True, exist_ok=True)

        if search_terms is None:
            search_terms = self.search_terms[:3]  # Use first 3 terms for demo

        all_studies = []

        # Search and collect studies
        for term in search_terms:
            pmids = self.pubmed_search(term, max_studies // len(search_terms))
            if pmids:
                studies = self.fetch_abstracts(pmids)
                all_studies.extend(studies)

        # Remove duplicates
        unique_studies = []
        seen_pmids = set()
        for study in all_studies:
            if study['pmid'] not in seen_pmids:
                unique_studies.append(study)
                seen_pmids.add(study['pmid'])

        print(f"📚 Found {len(unique_studies)} unique TB-AMR studies in India")

        # Extract prevalence data
        prevalence_data = self.extract_prevalence_data(unique_studies)

        if prevalence_data.empty:
            print("❌ No prevalence data extracted from studies")
            return None

        # Save raw extractions
        extraction_file = self.data_dir / "tb_amr_extractions.csv"
        prevalence_data.to_csv(extraction_file, index=False)

        # Compute meta-analysis
        meta_results = self.compute_meta_analysis(prevalence_data)

        # Save meta-analysis results
        results_file = self.data_dir / "tb_amr_meta_results.json"
        with open(results_file, 'w') as f:
            json.dump(meta_results, f, indent=2, default=str)

        # Create forest plot
        forest_plot_file = self.data_dir / "tb_amr_forest_plot.png"
        self.create_forest_plot(meta_results, forest_plot_file)

        # Print summary
        print("\n📈 Meta-Analysis Summary:")
        print("-" * 30)
        for resistance_type, results in meta_results.items():
            print(f"\n{resistance_type}:")
            print(".1f")
            print(f"  95% CI: {results['ci_lower']:.1f}% - {results['ci_upper']:.1f}%")
            print(f"  Studies: {results['n_studies']}")
            print(f"  Heterogeneity (I²): {results['i_squared']:.1f}%")

        print(f"\n📁 Results saved to: {self.data_dir}")
        return meta_results

if __name__ == "__main__":
    meta = TBAMRMetaAnalysis()
    results = meta.run_meta_analysis()

    if results:
        print("\n✅ TB-AMR meta-analysis complete!")
        print("Available outputs:")
        print("  - tb_amr_extractions.csv (raw data extractions)")
        print("  - tb_amr_meta_results.json (pooled estimates)")
        print("  - tb_amr_forest_plot.png (forest plot)")
    else:
        print("\n❌ Meta-analysis failed - check API connectivity and search terms")
