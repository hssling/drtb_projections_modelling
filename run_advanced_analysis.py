import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import BayesianRidge
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer # Fixed import
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

warnings.filterwarnings('ignore')

# --- CONFIG ---
DATA_DIR = r'd:\research-automation\tb_amr_project\data\processed'
SOURCE_DIR = r'd:\research-automation\tb_amr_project\SOURCES DATA'
OUTPUT_DIR = r'd:\research-automation\tb_amr_project\analysis_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- UTILS ---
def clean_state_name(name):
    if pd.isna(name): return "Unknown"
    name = str(name).strip().title()
    name = name.replace('&', 'and')
    name = name.replace('Telengana', 'Telangana')
    name = name.replace('Nct Of Delhi', 'Delhi')
    name = name.replace('Jammu And Kashmir', 'Jammu and Kashmir')
    return name

# --- 1. DATA LOADING & PREP ---
def load_and_prep_data():
    print("Loading datasets...")
    
    # A. TB Notifications (Time Series)
    ts_file = os.path.join(DATA_DIR, 'tb_notifications_comprehensive_17_24.csv')
    df_ts = pd.read_csv(ts_file)
    df_ts['State'] = df_ts['State'].apply(clean_state_name)
    
    # B. Outcomes/Age (Recent Snapshot)
    # We'll use the outcomes file for success rates
    out_file = os.path.join(DATA_DIR, 'tb_notifications_outcomes_state_23_24.csv')
    df_out = pd.read_csv(out_file)
    df_out['state'] = df_out['state'].apply(clean_state_name)
    
    # C. NFHS-5 (Socio-Economic Context)
    nfhs_file = os.path.join(SOURCE_DIR, 'NFHS_5_India_Districts_Factsheet_Data.xls')
    df_nfhs_dist = pd.read_excel(nfhs_file)
    df_nfhs_dist['State/UT'] = df_nfhs_dist['State/UT'].apply(clean_state_name)
    
    # Aggregate NFHS to State Level (mean of districts)
    # Filter for numeric columns only
    numeric_cols = df_nfhs_dist.select_dtypes(include=[np.number]).columns
    df_nfhs_state = df_nfhs_dist.groupby('State/UT')[numeric_cols].mean().reset_index()
    
    # Select key relevant columns if possible (requires knowing column names, usually they are numbered 1-100+)
    # We will use PCA on ALL numeric columns to extract "Socio-Health Factor"
    
    print("Data loaded correctly.")
    return df_ts, df_out, df_nfhs_state

# --- 2. TIME SERIES FORECASTING ---
def perform_forecasting(df_ts):
    print("\n--- Performing Time Series Forecasting (National) ---")
    
    # Sum all states to get National Trend
    year_cols = [str(y) for y in range(2017, 2025)]
    national_ts = df_ts[year_cols].sum(axis=0)
    national_ts.index = pd.to_datetime([f"{y}-12-31" for y in year_cols])
    
    # Model: Holt-Winters Exponential Smoothing
    model = ExponentialSmoothing(national_ts, trend='add', seasonal=None).fit()
    forecast_years = 3
    forecast = model.forecast(forecast_years)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(national_ts.index.year, national_ts.values, marker='o', label='Historical (2017-2024)')
    plt.plot(forecast.index.year, forecast.values, marker='o', linestyle='--', color='red', label='Forecast (2025-2027)')
    plt.title('National TB Notification Trend & Forecast (India)')
    plt.xlabel('Year')
    plt.ylabel('Total Notifications')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(os.path.join(OUTPUT_DIR, 'national_forecast.png'))
    print(f"Forecast for 2025: {int(forecast.iloc[0]):,}")
    
    # Save Forecast Data
    forecast_df = pd.DataFrame({'Year': forecast.index.year, 'Predicted_Cases': forecast.values})
    forecast_df.to_csv(os.path.join(OUTPUT_DIR, 'national_forecast_2025_27.csv'), index=False)

# --- 3. CLUSTERING & PCA (State Stratification) ---
def perform_clustering(df_ts, df_out, df_nfhs):
    print("\n--- Performing Clustering & PCA ---")
    
    # Merge datasets
    # Calculate 'Growth Rate' from TS (2024 vs 2017)
    df_ts['Growth_17_24'] = (df_ts['2024'] - df_ts['2017']) / df_ts['2017']
    
    # Master Merge
    merged = pd.merge(df_ts[['State', '2024', 'Growth_17_24']], df_out[['state', 'success_rate_2023_pct']], 
                      left_on='State', right_on='state', how='inner')
    merged = pd.merge(merged, df_nfhs, left_on='State', right_on='State/UT', how='inner')
    
    # Feature Selection for Clustering
    # We want to cluster based on: Disease Burden, Performance, and Context
    # 1. 2024 Notifications (Volume) -> Log Transformed
    # 2. Growth Rate (Trend)
    # 3. Success Rate (Performance)
    # 4. NFHS PC1 (Socio-Economic Status)
    
    # First, run PCA on NFHS data to get a single "Development Index"
    nfhs_numeric = merged.select_dtypes(include=[np.number]).drop(columns=['2024', 'Growth_17_24', 'success_rate_2023_pct'], errors='ignore')
    # Fill NAs
    nfhs_numeric = nfhs_numeric.fillna(nfhs_numeric.mean())
    
    pca = PCA(n_components=2)
    nfhs_pca = pca.fit_transform(StandardScaler().fit_transform(nfhs_numeric))
    merged['NFHS_PC1'] = nfhs_pca[:, 0]
    merged['NFHS_PC2'] = nfhs_pca[:, 1]
    
    # Now Cluster
    cluster_features = ['2024', 'Growth_17_24', 'success_rate_2023_pct', 'NFHS_PC1']
    X = merged[cluster_features].copy()
    X['2024'] = np.log1p(X['2024']) # Log transform volume
    X = X.fillna(X.mean())
    
    kmeans = KMeans(n_clusters=4, random_state=42)
    merged['Cluster'] = kmeans.fit_predict(StandardScaler().fit_transform(X))
    
    # Save Results
    merged[['State', 'Cluster', '2024', 'Growth_17_24', 'success_rate_2023_pct', 'NFHS_PC1']].to_csv(
        os.path.join(OUTPUT_DIR, 'state_clustering_results.csv'), index=False)
    
    # Plot Clusters (Scatter: Outcome vs Burden)
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=merged, x='2024', y='success_rate_2023_pct', hue='Cluster', palette='viridis', style='Cluster', s=100)
    
    # Label Points
    for i in range(merged.shape[0]):
        plt.text(merged['2024'][i]+0.02, merged['success_rate_2023_pct'][i], 
                 merged['State'][i], fontsize=8, alpha=0.7)
                 
    plt.title('State Clusters: TB Burden vs Treatment Success')
    plt.xlabel('Total TB Cases 2024 (Log Scale for Visualization)') # Actually linear here unless we plot log
    plt.xscale('log')
    plt.ylabel('Treatment Success Rate (%)')
    plt.grid(True)
    plt.savefig(os.path.join(OUTPUT_DIR, 'cluster_plot.png'))
    print("Clustering completed.")

# --- 4. BAYESIAN ANALYSIS (Drivers of TB Burden) ---
def perform_bayesian_regression(merged_df):
    pass # Placeholder for future

def main():
    df_ts, df_out, df_nfhs = load_and_prep_data()
    perform_forecasting(df_ts)
    perform_clustering(df_ts, df_out, df_nfhs)

if __name__ == "__main__":
    main()
