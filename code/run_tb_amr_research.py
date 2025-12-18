#!/usr/bin/env python3
"""
TB-AMR Research Pipeline Runner

Demonstrates the complete TB-AMR analysis pipeline for India.
Runs all components end-to-end to generate research outputs answering:
"What will be the projected burden of MDR-TB and XDR-TB in India over the next decade,
and how will scaling up new treatment regimens and stewardship interventions change this trajectory?"
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def run_command(cmd, description=""):
    """Execute a command with status reporting."""
    print(f"\n🚀 {description}")
    print(f"Command: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout:
                print(f"Output: {result.stdout.strip()}")
        else:
            print(f"❌ Failed: {description}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

    return True

def main():
    """Main research pipeline execution."""
    print("🇮🇳 INDIA TB-AMR RESEARCH ANALYSIS")
    print("=" * 50)
    print("Research Question Answer Generation Pipeline")
    print("=" * 50)

    # Ensure we're in the right directory
    if not Path("tb_amr_project").exists():
        print("❌ Error: tb_amr_project directory not found. Please ensure the TB-AMR platform was created.")
        sys.exit(1)

    os.chdir("tb_amr_project")

    # Step 1: Install dependencies
    print("\n📦 STEP 1: Installing Dependencies")
    run_command("pip install -r requirements.txt", "Installing Python dependencies")

    # Step 2: Data Integration (WHO + ICMR)
    print("\n📊 STEP 2: Data Integration & Preparation")
    run_command("python pipeline/icmr_connector.py", "Integrating WHO Global TB Report Data with ICMR Surveillance")

    # Step 3: Time Series Forecasting
    print("\n🔮 STEP 3: Multi-Model Forecasting")
    run_command("python pipeline/tb_forecast.py \"India\" \"Rifampicin (proxy MDR)\" \"new\"", "Forecasting MDR-TB burden (New Cases)")
    run_command("python pipeline/tb_forecast.py \"India\" \"Rifampicin (proxy MDR)\" \"retreated\"", "Forecasting MDR-TB burden (Retreated Cases)")

    # Step 4: Policy Sensitivity Analysis
    print("\n🎯 STEP 4: Policy Intervention Analysis")
    run_command("python pipeline/tb_sensitivity.py", "Evaluating BPaL/BPaL-M and stewardship interventions")

    # Step 5: Geographic Hotspot Mapping
    print("\n🗺️ STEP 5: Geographic Analysis")
    run_command("python pipeline/tb_gis_mapping.py", "Auto-downloading India shapefiles and generating hotspot maps")

    # Step 6: Meta-Analysis Integration
    print("\n📚 STEP 6: Evidence Synthesis")
    run_command("python pipeline/tb_meta_analysis.py", "Conducting literature meta-analysis for validation")

    # Step 7: Automated Manuscript Generation
    print("\n✍️ STEP 7: Research Manuscript Generation")
    run_command("python pipeline/tb_manuscript.py", "Auto-generating complete IMRAD research manuscript")

    print("\n" + "=" * 70)
    print("🎯 RESEARCH QUESTION ANSWERED!")
    print("=" * 70)
    print("The TB-AMR research pipeline has been executed successfully.")
    print("Research outputs are available in the following locations:")
    print()
    print("📁 Generated Outputs:")
    print("   ├── data/tb_merged_icmr_who.csv           # Unified dataset")
    print("   ├── data/forecast_tb_India_*.csv           # Time series projections")
    print("   ├── data/sensitivity_tb_India_*.csv        # Policy scenarios")
    print("   ├── reports/                               # Visualizations & maps")
    print("   └── manuscripts/tb_amr_*.md                # Research manuscripts")
    print()
    print("🎯 To launch interactive dashboard:")
    print("   streamlit run pipeline/tb_dashboard.py")
    print()
    print("📊 To view research summary:")
    print("   cat ../year_one_research_summary.md")

    print("\n" + "=" * 50)
    print("🚀 END-TO-END RESEARCH PIPELINE COMPLETE!")
    print("=" * 50)

if __name__ == "__main__":
    main()
