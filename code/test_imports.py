#!/usr/bin/env python3
"""
TB-AMR Dashboard Import Test

Tests if all critical modules can be imported successfully.
This is essential for Streamlit Cloud deployment.
"""

import sys
import os

def test_imports():
    print("Testing TB-AMR Dashboard imports...")
    print("=" * 50)

    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    try:
        # Test core dashboard
        from tb_amr_project.pipeline.tb_dashboard import main
        print("✅ tb_dashboard import SUCCESS")
    except ImportError as e:
        print(f"❌ tb_dashboard import FAILED: {e}")
        return False

    try:
        # Test visualization engine
        from tb_amr_project.pipeline.tb_visualization import TBAMRVisualizationGenerator
        print("✅ tb_visualization import SUCCESS")
    except ImportError as e:
        print(f"❌ tb_visualization import FAILED: {e}")
        return False

    try:
        # Test forecasting
        from tb_amr_project.pipeline import tb_forecast
        print("✅ tb_forecast import SUCCESS")
    except ImportError as e:
        print(f"❌ tb_forecast import FAILED: {e}")
        return False

    try:
        # Test sensitivity analysis
        from tb_amr_project.pipeline import tb_sensitivity
        print("✅ tb_sensitivity import SUCCESS")
    except ImportError as e:
        print(f"❌ tb_sensitivity import FAILED: {e}")
        return False

    print("=" * 50)
    print("🎯 All imports working - READY FOR DEPLOYMENT!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
