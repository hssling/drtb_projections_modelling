#!/usr/bin/env python3
"""
TB-AMR GIS Hotspot Mapping Pipeline

Creates geographic visualizations of MDR-TB resistance in India,
showing current prevalence and forecasted hotspots by state/district.
"""

import geopandas as gpd
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from pathlib import Path
import requests
import zipfile
import io

def tb_hotspot_map(country="India", drug="Rifampicin (proxy MDR)", case_type="new", horizon=60):
    """
    Creates GIS maps of MDR-TB resistance in India (current + forecast).
    horizon: forecast period in months (default 5 years = 60 months)
    """

    # Load unified TB dataset
    df = pd.read_csv("data/tb_merged.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    subset = df[(df["country"] == country) &
                (df["drug"] == drug) &
                (df["type"] == case_type)]

    if subset.empty:
        print(f"❌ No TB-AMR data found for {country}, {drug}, {case_type} cases.")
        return

    if "state" not in subset.columns or subset["state"].nunique() <= 1:
        print("⚠️ No state-level data available. Cannot generate hotspot maps.")
        print("   Currently data aggregated at national level.")
        return

    # ---------------- Aggregate Latest Data ----------------
    latest = subset.groupby("state").tail(1)  # last available per state
    latest = latest[["state","percent_resistant"]]

    # ---------------- Forecast per State ----------------
    forecast_results = []
    for state, group in subset.groupby("state"):
        data = group[["date","percent_resistant"]].dropna()
        if len(data) < 3:  # Need minimum data points for forecasting
            print(f"⏭️ Skipping {state} - insufficient data ({len(data)} points)")
            continue

        try:
            data = data.rename(columns={"date":"ds","percent_resistant":"y"})
            model = Prophet()
            model.fit(data)
            future = model.make_future_dataframe(periods=horizon, freq="M")
            forecast = model.predict(future)
            forecast_results.append({
                "state": state,
                "forecast_resistant": forecast.iloc[-1]["yhat"]
            })
        except Exception as e:
            print(f"⚠️ Forecast failed for {state}: {e}")

    if not forecast_results:
        print("❌ Insufficient data for any state forecasts.")
        return

    forecast_df = pd.DataFrame(forecast_results)

    # ---------------- Load India Shapefile ----------------
    shp = load_india_shapefile(auto_download=True)

    if shp is None:
        return

    # Determine common state name column
    possible_keys = ["NAME_1", "STATE", "state", "STATE_NAME", "ADM1_NAME"]
    merge_key = None
    for key in possible_keys:
        if key in shp.columns:
            merge_key = key
            break

    if merge_key is None:
        print(f"❌ State name column not found. Available columns: {shp.columns.tolist()}")
        return

    # Check if state names match
    print(f"Available states in shapefile: {shp[merge_key].unique()[:5]}...")
    print(f"States in TB data: {latest['state'].unique()}")

    # Standardize state names (case insensitive merge)
    shp[merge_key] = shp[merge_key].str.lower().str.strip()
    latest['state'] = latest['state'].str.lower().str.strip()
    forecast_df['state'] = forecast_df['state'].str.lower().str.strip()

    # ---------------- Merge Data ----------------
    shp_current = shp.merge(latest, left_on=merge_key, right_on="state", how="left")
    shp_forecast = shp.merge(forecast_df, left_on=merge_key, right_on="state", how="left")

    # ---------------- Plot Current Map ----------------
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    shp_current.plot(column="percent_resistant", ax=ax, legend=True,
                     cmap="Reds", missing_kwds={"color": "lightgrey"},
                     legend_kwds={"label": "MDR-TB %", "orientation": "horizontal"})
    plt.title(f'Current MDR-TB Hotspots: {drug} ({case_type} cases) in {country}',
              fontsize=14, fontweight='bold')
    plt.axis('off')

    out_file_current = f"reports/tb_hotspots_current_{country}_{case_type}.png".replace(" ","_")
    plt.savefig(out_file_current, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"🗺️ Current hotspot map saved → {out_file_current}")

    # ---------------- Plot Forecast Map ----------------
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    shp_forecast.plot(column="forecast_resistant", ax=ax, legend=True,
                      cmap="Reds", missing_kwds={"color": "lightgrey"},
                      legend_kwds={"label": f"MDR-TB % ({horizon//12} year forecast)", "orientation": "horizontal"})
    plt.title(f'Forecasted MDR-TB Hotspots ({horizon//12} years): {country}',
              fontsize=14, fontweight='bold')
    plt.axis('off')

    out_file_forecast = f"reports/tb_hotspots_forecast_{country}_{case_type}.png".replace(" ","_")
    plt.savefig(out_file_forecast, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"🔮 Forecast hotspot map saved → {out_file_forecast}")

    # ---------------- Summary Statistics ----------------
    print("\n📊 TB Hotspot Mapping Summary:")
    print(f"   States with data: {len(latest)}")
    print(f"   States with forecasts: {len(forecast_df)}")

    current_avg = latest["percent_resistant"].mean()
    forecast_avg = forecast_df["forecast_resistant"].mean()
    change_pct = ((forecast_avg - current_avg) / current_avg) * 100

    print(".1f")
    print(".1f")
    print(".1f")

def download_india_shapefile(gadm_version="4.1", country_code="IND", admin_level=1):
    """
    Downloads India administrative boundaries from GADM.org.
    gadm_version: GADM dataset version (default 4.1)
    admin_level: Administrative level (1=states, 2=districts)
    """
    shapefiles_dir = Path("../data/shapefiles")
    shapefiles_dir.mkdir(parents=True, exist_ok=True)

    # GADM download URL format
    base_url = "https://geodata.ucdavis.edu"
    file_name = f"gadm{gadm_version}_{country_code}_{admin_level}.tar.gz"
    download_url = f"{base_url}/gadm/gadm{gadm_version}/shp/{file_name}"

    # Try alternative URL formats if needed
    alt_urls = [
        download_url,
        f"{base_url}/gadm{gadm_version}/shp/{file_name}",
        f"https://data.biogeo.ucdavis.edu/data/gadm{gadm_version}/shp/gadm{gadm_version}_{country_code}_shp.zip"
    ]

    for url in alt_urls:
        try:
            print(f"📥 Downloading India shapefile from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Handle different file extensions
            if url.endswith('.zip'):
                # Extract ZIP file
                zip_content = zipfile.ZipFile(io.BytesIO(response.content))
                zip_content.extractall(shapefiles_dir)
                print(f"✅ Shapefile extracted to: {shapefiles_dir}")

                # Find the shapefile name
                shp_files = list(shapefiles_dir.glob("**/gadm*.shp"))
                if shp_files:
                    return shp_files[0].name.replace('.shp', '')

            elif url.endswith('.tar.gz'):
                # Extract tar.gz file
                import tarfile
                tar_content = tarfile.open(fileobj=io.BytesIO(response.content), mode='r:gz')
                tar_content.extractall(shapefiles_dir)
                print(f"✅ Shapefile extracted to: {shapefiles_dir}")

                # Find the shapefile name
                shp_files = list(shapefiles_dir.glob("**/gadm*.shp"))
                if shp_files:
                    return shp_files[0].name.replace('.shp', '')

            print("✅ India shapefile downloaded successfully!")
            return f"gadm{gadm_version}_{country_code}_{admin_level}"

        except Exception as e:
            print(f"⚠️ Download failed from {url}: {e}")
            continue

    print("❌ All download attempts failed.")
    print("📥 Manual download instructions:")
    print("   Go to: https://gadm.org/download_country.html")
    print("   Select: India → Administrative Level 1 (States)")
    print("   Place downloaded files in: data/shapefiles/")
    return None

def load_india_shapefile(auto_download=True):
    """
    Loads India administrative boundaries, downloading if needed.
    Returns GeoDataFrame with state boundaries.
    """
    shapefiles_dir = Path("../data/shapefiles")

    # Check for existing shapefile
    existing_files = list(shapefiles_dir.glob("**/gadm*IND*.shp"))
    if existing_files:
        try:
            shp = gpd.read_file(existing_files[0])
            print(f"✅ Loaded existing India shapefile: {existing_files[0]}")
            return shp
        except Exception as e:
            print(f"⚠️ Error loading existing shapefile: {e}")

    # Download if not found
    if auto_download:
        print("🔍 India shapefile not found locally. Downloading from GADM...")
        shapefile_name = download_india_shapefile()

        if shapefile_name:
            try:
                shp_path = shapefiles_dir / f"{shapefile_name}.shp"
                shp = gpd.read_file(shp_path)
                print(f"✅ Successfully loaded downloaded shapefile!")
                return shp
            except Exception as e:
                print(f"❌ Error loading downloaded shapefile: {e}")

    # Fallback to manual instructions
    create_sample_india_shapefile()
    return None

def create_sample_india_shapefile():
    """Creates a simple sample India shapefile with major states for testing."""
    # This is a placeholder - real shapefiles need to be downloaded
    print("📥 Note: Download India state shapefile manually from:")
    print("   https://gadm.org/download_country.html")
    print("   Select: India → Level 1 (States)")
    print("   Place extracted files in: data/shapefiles/india_states.*")

if __name__ == "__main__":
    print("TB-AMR GIS Mapping Pipeline")
    print("=" * 40)

    try:
        tb_hotspot_map("India", "Rifampicin (proxy MDR)", "new", horizon=60)
    except Exception as e:
        print(f"❌ Error: {e}")
        create_sample_india_shapefile()
