@echo off
echo Testing TB-AMR Dashboard imports...
cd /d "tb_amr_project"
python -c "
import sys
print('Testing imports from tb_amr_project...')
try:
    from pipeline.tb_dashboard import main
    print('✅ tb_dashboard import SUCCESS')
    from pipeline.tb_visualization import TBAMRVisualizationGenerator
    print('✅ tb_visualization import SUCCESS') 
    from pipeline.tb_forecast import TBForecastGenerator
    print('✅ tb_forecast import SUCCESS')
    from pipeline.tb_sensitivity import TBSensitivityAnalyzer
    print('✅ tb_sensitivity import SUCCESS')
    print('🎯 All imports working - READY FOR DEPLOYMENT!')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    exit(1)
"
pause
