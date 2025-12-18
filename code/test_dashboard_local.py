#!/usr/bin/env python3
"""
Quick local test of TB-AMR Dashboard functionality
"""

import pandas as pd

# Test data loading and display issues
def test_dashboard():
    print("🔍 TB-AMR Dashboard Local Testing Script")
    print("=" * 50)

    try:
        # Import dashboard module
        from pipeline.tb_dashboard import load_tb_data, show_overview_page
        print("✅ Dashboard module imported successfully")
    except Exception as e:
        print(f"❌ Dashboard import failed: {e}")
        return

    # Test data loading
    try:
        data = load_tb_data()
        print("✅ Data loading function executed")

        if 'tb_data' in data:
            tb_data = data['tb_data']
            if not tb_data.empty:
                print(f"✅ TB-AMR data loaded: {len(tb_data)} records")
                print(f"Columns: {list(tb_data.columns)}")

                # Check for required columns
                if 'year' not in tb_data.columns:
                    print("⚠️  Missing 'year' column, adding it...")
                    tb_data['year'] = pd.to_datetime(tb_data['date']).dt.year

                if 'case_type' not in tb_data.columns:
                    print("⚠️  Missing 'case_type' column, mapping from 'type'...")
                    tb_data['case_type'] = tb_data['type']

                print("Data statistics:")
                print(f"- Years: {sorted(tb_data['year'].unique())}")
                print(f"- Case types: {sorted(tb_data['case_type'].unique())}")
                print(f"- States: {sorted(tb_data['state'].unique())}")
                print(f"- Drugs: {sorted(tb_data['drug'].unique())}")
                print(f"- Resistance range: {tb_data['percent_resistant'].min():.1f}% - {tb_data['percent_resistant'].max():.1f}%")

                print("\nFirst few records:")
                print(tb_data.head(3).to_string())
            else:
                print("❌ TB data loaded but empty")
        else:
            print("❌ No 'tb_data' key in loaded data")
            print(f"Available keys: {list(data.keys())}")

    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard()
