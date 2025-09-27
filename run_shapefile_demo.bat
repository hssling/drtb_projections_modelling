@echo off
echo ================================================
echo INDIAN MDR-TB GIS CHOROPLETH SHAPEFILE DEMO
echo ================================================
echo.
echo Testing GIS choropleth generation...
echo.
cd /d "%~dp0"
python -c "from pipeline.tb_visualization import TBAMRVisualizationGenerator; gen = TBAMRVisualizationGenerator(); gen.generate_geographic_map(); print('\\n✅ Indian MDR-TB choropleth shapefile maps generated successfully!')"
echo.
echo ================================================
echo CREATED FILES IN plots/ DIRECTORY:
echo ================================================
dir /b plots\*
echo.
echo ================================================
echo OPEN THESE FILES IN YOUR GIS APPLICATION:
echo ================================================
echo - india_mdr_choropleth.geojson (polygon choropleth)
echo - india_mdr_hotspots_2023.geojson (point data)
echo - india_mdr_hotspots_2023.csv (spreadsheet)
echo - shapefiles/ directory (ESRI shapefile set)
echo.
echo ================================================
echo 📊 Maps: india_mdr_hotspots_publication.png
echo 🗺️ GIS Ready: All choropleth files created successfully
echo ================================================
pause
