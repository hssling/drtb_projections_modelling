#!/usr/bin/env python3
"""
DIAGNOSTIC SCRIPT: Indian MDR-TB Choropleth Shapefile Generation Issues

This script systematically diagnoses and fixes issues with the choropleth
shapefile generation system for India's MDR-TB geographic data.
"""

import os
import sys
import pandas as pd
import json
from pathlib import Path
import traceback

def diagnose_environment():
    """Check the execution environment and dependencies."""
    print("=" * 60)
    print("🔍 DIAGNOSTIC: ENVIRONMENT CHECK")
    print("=" * 60)

    # Current directory
    cwd = os.getcwd()
    print(f"✅ Current working directory: {cwd}")

    # Check if we're in the right directory
    tb_project_dir = Path("tb_amr_project")
    if tb_project_dir.exists():
        print("✅ tb_amr_project directory found")
    else:
        print("❌ tb_amr_project directory not found")
        return False

    # Check Python version
    print(f"✅ Python version: {sys.version}")

    # Check if required packages are available
    try:
        import geopandas as gpd
        print(f"✅ GeoPandas version: {gpd.__version__}")
    except ImportError as e:
        print(f"❌ GeoPandas not available: {e}")
        return False

    try:
        import matplotlib.pyplot as plt
        print(f"✅ Matplotlib version: {plt.__version__}")
    except ImportError as e:
        print(f"❌ Matplotlib not available: {e}")
        return False

    try:
        import seaborn as sns
        print("✅ Seaborn available")
    except ImportError as e:
        print("❌ Seaborn not available")

    return True

def diagnose_file_system():
    """Check the status of generated files."""
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSTIC: FILE SYSTEM CHECK")
    print("=" * 60)

    project_dir = Path("tb_amr_project")
    plots_dir = project_dir / "plots"

    # Check if plots directory exists
    if not plots_dir.exists():
        print("❌ plots directory does not exist")
        return False
    else:
        print("✅ plots directory exists")

    # List all files in plots directory
    file_list = list(plots_dir.glob("*"))
    if not file_list:
        print("❌ No files in plots directory")
        return False

    print(f"✅ Found {len(file_list)} files in plots directory:")
    for file_path in sorted(file_list):
        file_size = file_path.stat().st_size
        print(f"   - {file_path.name} ({file_size} bytes)")

    # Check for expected files
    expected_files = [
        'india_mdr_choropleth.geojson',
        'india_mdr_hotspots_2023.geojson',
        'india_mdr_hotspots_2023.csv',
        'india_mdr_hotspots_publication.png',
        'india_mdr_hotspots_scientific.png',
        'shapefiles'
    ]

    missing_files = []
    working_files = []

    for expected in expected_files:
        path = plots_dir / expected
        if path.exists():
            working_files.append(expected)
        else:
            missing_files.append(expected)

    print(f"\n✅ Working files ({len(working_files)}): {working_files}")
    if missing_files:
        print(f"❌ Missing files ({len(missing_files)}): {missing_files}")

    # Check shapefiles subdirectory
    shapefiles_dir = plots_dir / "shapefiles"
    if shapefiles_dir.exists():
        shapefile_count = len(list(shapefiles_dir.glob("*")))
        print(f"✅ shapefiles directory contains {shapefile_count} files")
        for sf in shapefiles_dir.glob("*"):
            print(f"   - {sf.name}")
    else:
        print("❌ shapefiles subdirectory not found")

    return len(missing_files) == 0

def diagnose_import():
    """Test importing the visualization module."""
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSTIC: MODULE IMPORT CHECK")
    print("=" * 60)

    try:
        # Change to project directory
        original_cwd = os.getcwd()
        project_dir = Path("tb_amr_project")
        os.chdir(project_dir)

        print("✅ Changed to tb_amr_project directory")

        # Try importing
        from pipeline.tb_visualization import TBAMRVisualizationGenerator
        print("✅ Successfully imported TBAMRVisualizationGenerator")

        # Try instantiating
        gen = TBAMRVisualizationGenerator()
        print("✅ Successfully created TBAMRVisualizationGenerator instance")

        # Change back
        os.chdir(original_cwd)
        print("✅ Changed back to original directory")

        return True

    except Exception as e:
        print(f"❌ Import/Instantiation failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def diagnose_json_files():
    """Check if the generated GeoJSON files are valid."""
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSTIC: GEOJSON FILE VALIDATION")
    print("=" * 60)

    project_dir = Path("tb_amr_project")
    plots_dir = project_dir / "plots"

    geojson_files = [
        'india_mdr_choropleth.geojson',
        'india_mdr_hotspots_2023.geojson'
    ]

    all_valid = True

    for gj_file in geojson_files:
        file_path = plots_dir / gj_file
        if not file_path.exists():
            print(f"❌ {gj_file} does not exist")
            all_valid = False
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Basic structure check
            if 'type' not in data:
                print(f"❌ {gj_file}: Missing 'type' field")
                all_valid = False
                continue

            if data['type'] == 'FeatureCollection':
                features = data.get('features', [])
                print(f"✅ {gj_file}: Valid GeoJSON with {len(features)} features")
            else:
                print(f"⚠️ {gj_file}: Not a FeatureCollection (type: {data['type']})")

        except json.JSONDecodeError as e:
            print(f"❌ {gj_file}: Invalid JSON: {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {gj_file}: Error reading: {e}")
            all_valid = False

    return all_valid

def diagnose_csv_files():
    """Check if the generated CSV files are valid."""
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSTIC: CSV FILE VALIDATION")
    print("=" * 60)

    project_dir = Path("tb_amr_project")
    plots_dir = project_dir / "plots"

    csv_files = ['india_mdr_hotspots_2023.csv']

    all_valid = True

    for csv_file in csv_files:
        file_path = plots_dir / csv_file
        if not file_path.exists():
            print(f"❌ {csv_file} does not exist")
            all_valid = False
            continue

        try:
            df = pd.read_csv(file_path)
            print(f"✅ {csv_file}: Valid CSV with {len(df)} rows and {len(df.columns)} columns")
            print(f"   Columns: {list(df.columns)}")
            print(f"   Sample data (first 3 rows):")
            print(df.head(3).to_string())

        except Exception as e:
            print(f"❌ {csv_file}: Error reading: {e}")
            all_valid = False

    return all_valid

def diagnose_image_files():
    """Check if the generated image files are valid."""
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSTIC: IMAGE FILE VALIDATION")
    print("=" * 60)

    project_dir = Path("tb_amr_project")
    plots_dir = project_dir / "plots"

    image_files = [
        'india_mdr_hotspots_publication.png',
        'india_mdr_hotspots_scientific.png'
    ]

    all_valid = True

    for img_file in image_files:
        file_path = plots_dir / img_file
        if not file_path.exists():
            print(f"❌ {img_file} does not exist")
            all_valid = False
            continue

        file_size = file_path.stat().st_size
        if file_size < 1000:  # Suspiciously small file
            print(f"⚠️ {img_file}: Very small file ({file_size} bytes)")
        else:
            print(f"✅ {img_file}: Exists ({file_size} bytes)")

    return all_valid

def run_full_generation_test():
    """Run the actual generation function to identify where it fails."""
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSTIC: FULL GENERATION TEST")
    print("=" * 60)

    try:
        # Import and test
        from pipeline.tb_visualization import TBAMRVisualizationGenerator

        print("✅ Successfully imported TBAMRVisualizationGenerator")

        # Create instance
        gen = TBAMRVisualizationGenerator()
        print("✅ Successfully created instance")

        # Test each method individually
        print("\n--- Testing generate_forecast_plots() ---")
        try:
            gen.generate_forecast_plots()
            print("✅ generate_forecast_plots() completed")
        except Exception as e:
            print(f"❌ generate_forecast_plots() failed: {e}")
            return False

        print("\n--- Testing generate_geographic_map() ---")
        try:
            gen.generate_geographic_map()
            print("✅ generate_geographic_map() completed")
        except Exception as e:
            print(f"❌ generate_geographic_map() failed: {e}")
            traceback.print_exc()
            return False

        print("\n--- Testing generate_intervention_comparison() ---")
        try:
            gen.generate_intervention_comparison()
            print("✅ generate_intervention_comparison() completed")
        except Exception as e:
            print(f"❌ generate_intervention_comparison() failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Full generation test failed: {e}")
        traceback.print_exc()
        return False

def provide_solution():
    """Provide diagnostic summary and solutions."""
    print("\n" + "=" * 80)
    print("🎯 DIAGNOSTIC SUMMARY & FIXES")
    print("=" * 80)

    print("If you have reached this point, the diagnostic has identified issues.")
    print("Below are the most common fixes:")
    print()

    print("1. DEPENDENCY ISSUES:")
    print("   - Ensure you have geopandas, matplotlib, seaborn installed")
    print("   - Check Python virtual environment activation")
    print()

    print("2. PATH ISSUES:")
    print("   - Make sure you're running from the tb_amr_project directory")
    print("   - Or set PYTHONPATH correctly")
    print()

    print("3. PERMISSION ISSUES:")
    print("   - Ensure write permissions to plots/ directory")
    print("   - Check if files are locked or in use")
    print()

    print("4. WINDOWS POWERSHELL ISSUES:")
    print("   - Use single commands instead of && syntax")
    print("   - Try running in Command Prompt instead")
    print()

    print("RUN THIS TO TEST INDIVIDUALLY:")
    print("cd tb_amr_project")
    print("python -c \"from pipeline.tb_visualization import TBAMRVisualizationGenerator; gen = TBAMRVisualizationGenerator(); gen.generate_geographic_map()\"")

def main():
    """Run all diagnostic tests."""
    print("🏥 INDIAN MDR-TB CHOROPLETH SHAPEFILE DIAGNOSTIC SYSTEM")
    print("Diagnosing issues with geographic choropleth GIS generation...")
    print()

    # Run all diagnostics
    env_ok = diagnose_environment()
    files_ok = diagnose_file_system()
    import_ok = diagnose_import()
    json_ok = diagnose_json_files()
    csv_ok = diagnose_csv_files()
    images_ok = diagnose_image_files()

    print("\n" + "=" * 80)
    print("📊 DIAGNOSTIC RESULTS SUMMARY")
    print("=" * 80)

    tests = [
        ("Environment", env_ok),
        ("File System", files_ok),
        ("Module Import", import_ok),
        ("GeoJSON Files", json_ok),
        ("CSV Files", csv_ok),
        ("Image Files", images_ok)
    ]

    all_passed = True
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<15}: {status}")
        if not passed:
            all_passed = False

    if not all_passed:
        print("
🚨 SOME TESTS FAILED - RUNNING FULL GENERATION TEST...
"        full_gen_ok = run_full_generation_test()

        if full_gen_ok:
            print("✅ FULL GENERATION TEST PASSED")
        else:
            print("❌ FULL GENERATION TEST FAILED")
            provide_solution()
    else:
        print("
🎉 ALL TESTS PASSED - SYSTEM HEALTHY
"        print("The choropleth shapefile system is working correctly!")
        print("Run: python pipeline/tb_visualization.py to generate choropleth maps")

if __name__ == "__main__":
    main()
