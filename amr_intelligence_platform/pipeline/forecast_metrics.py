#!/usr/bin/env python3
"""
AMR Forecasting with Performance Metrics - Prophet vs ARIMA vs LSTM

Enhanced forecasting script that compares all three models side-by-side
and computes performance metrics (RMSE, MAE, MAPE) for model reliability analysis.
"""

import pandas as pd
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import numpy as np
import matplotlib.pyplot as plt
import sys
import json
from datetime import datetime

def evaluate_metrics(true_values, predicted_values, model_name):
    """Calculate comprehensive performance metrics for forecast evaluation."""
    try:
        # Basic metrics
        rmse = mean_squared_error(true_values, predicted_values, squared=False)
        mae = mean_absolute_error(true_values, predicted_values)
        mape = np.mean(np.abs((true_values - predicted_values) / true_values)) * 100

        # Additional metrics
        mse = mean_squared_error(true_values, predicted_values)

        # Bias metrics
        bias = np.mean(predicted_values - true_values)
        mean_error = np.mean(predicted_values - true_values)

        # Accuracy score (lower is better)
        accuracy_score = rmse + mae + (mape / 100)  # Composite metric

        metrics = {
            "model": model_name,
            "RMSE": float(rmse),  # Root Mean Square Error
            "MSE": float(mse),    # Mean Square Error
            "MAE": float(mae),    # Mean Absolute Error
            "MAPE": float(mape),  # Mean Absolute Percentage Error
            "bias": float(bias),   # Prediction bias
            "mean_error": float(mean_error),
            "accuracy_score": float(accuracy_score),  # Composite score
            "sample_size": len(true_values)
        }

        # Rank (will be added later for comparison)
        metrics["rank"] = None

        return metrics

    except Exception as e:
        return {
            "model": model_name,
            "error": f"Metrics calculation failed: {e}",
            "RMSE": None, "MSE": None, "MAE": None, "MAPE": None,
            "bias": None, "mean_error": None, "accuracy_score": None
        }

def run_prophet_forecast(train_data, test_size, forecast_periods=24):
    """Run Prophet forecast with performance evaluation."""
    prophet = Prophet(
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0
    )
    prophet.fit(train_data)

    # Forecast for test period (backtesting)
    future_test = prophet.make_future_dataframe(periods=test_size, freq="M")
    forecast_test = prophet.predict(future_test)
    pred_test = forecast_test["yhat"].iloc[-test_size:].values

    # Full forecast for future periods
    future_full = prophet.make_future_dataframe(periods=forecast_periods, freq="M")
    forecast_full = prophet.predict(future_full)

    return forecast_test, forecast_full

def run_arima_forecast(series_train, test_size, forecast_periods=24, order=(2,1,2)):
    """Run ARIMA forecast with performance evaluation."""
    arima_model = ARIMA(series_train, order=order)

    try:
        arima_fit = arima_model.fit()

        # Forecast for test period
        forecast_test = arima_fit.forecast(steps=test_size)

        # Full forecast for future periods
        forecast_full = arima_fit.forecast(steps=forecast_periods)

        return forecast_test, forecast_full

    except Exception as e:
        # Fallback to simpler model
        try:
            arima_model_fallback = ARIMA(series_train, order=(1,1,1))
            arima_fit_fallback = arima_model_fallback.fit()
            forecast_test = arima_fit_fallback.forecast(steps=test_size)
            forecast_full = arima_fit_fallback.forecast(steps=forecast_periods)
            return forecast_test, forecast_full
        except:
            raise e

def run_lstm_forecast(series_all, split_idx, test_size, forecast_periods=24):
    """Run LSTM forecast with performance evaluation."""
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(series_all.values.reshape(-1, 1))

    look_back = min(5, split_idx // 2)  # Adaptive look-back

    # Training data for LSTM
    train_scaled = data_scaled[:split_idx]

    def create_dataset(dataset, look_back):
        X, y = [], []
        for i in range(len(dataset) - look_back):
            X.append(dataset[i:i+look_back, 0])
            y.append(dataset[i+look_back, 0])
        return np.array(X), np.array(y)

    X_train, y_train = create_dataset(train_scaled, look_back)
    X_train = X_train.reshape(X_train.shape[0], look_back, 1)

    # Build LSTM model
    model = Sequential([
        LSTM(50, activation='relu', input_shape=(look_back, 1), return_sequences=False),
        Dense(25, activation='relu'),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mse')
    model.fit(X_train, y_train, epochs=20, batch_size=min(8, len(X_train)), verbose=0)

    # Forecast test period
    test_scaled = data_scaled[split_idx:split_idx + test_size]

    if len(test_scaled) < look_back:
        raise ValueError("Insufficient test data for LSTM forecasting")

    pred_test = []
    current_seq = test_scaled[:look_back].reshape(1, look_back, 1)

    for _ in range(test_size):
        pred = model.predict(current_seq, verbose=0)[0][0]
        pred_test.append(pred)
        current_seq = np.roll(current_seq, -1, axis=1)
        current_seq[0, -1, 0] = pred

    pred_test = scaler.inverse_transform(np.array(pred_test).reshape(-1, 1)).flatten()

    # Forecast future periods
    pred_future = []
    for _ in range(forecast_periods):
        pred = model.predict(current_seq, verbose=0)[0][0]
        pred_future.append(pred)
        current_seq = np.roll(current_seq, -1, axis=1)
        current_seq[0, -1, 0] = pred

    pred_future = scaler.inverse_transform(np.array(pred_future).reshape(-1, 1)).flatten()

    return pred_test, pred_future

def forecast_and_evaluate_all(country, pathogen, antibiotic, forecast_periods=24, test_split=0.8):
    """Run all models and evaluate performance metrics."""
    print(f"🚀 Starting enhanced AMR forecasting for {country} | {pathogen} | {antibiotic}")
    print("=" * 80)

    # Load and filter data
    df = pd.read_csv("data/amr_merged.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    subset = df[(df["country"].str.lower() == country.lower()) &
                (df["pathogen"].str.lower() == pathogen.lower()) &
                (df["antibiotic"].str.lower() == antibiotic.lower())].dropna()

    if subset.empty:
        print("❌ No data found for this combination")
        print("\nAvailable combinations:")
        available = df.groupby(['country', 'pathogen', 'antibiotic']).size().reset_index()
        print(f"Total combinations: {len(available)}")
        print("Sample countries:", sorted(df['country'].unique())[:5])
        return None

    print(f"📊 Historical data: {len(subset)} records")
    print(f"   Date range: {subset['date'].min()} to {subset['date'].max()}")
    print(f"   Current resistance: {subset['percent_resistant'].iloc[-1]:.1f}%")

    # Prepare time series data
    data = subset[["date", "percent_resistant"]].copy()
    data.columns = ["ds", "y"]
    data = data.sort_values("ds").dropna()
    series = data.set_index("ds")["y"]

    if len(series) < 10:
        print(f"❌ Insufficient data: {len(series)} records (need ≥10)")
        return None

    # Train/test split
    split_idx = int(len(series) * test_split)
    train_series = series[:split_idx]
    test_series = series[split_idx:]
    train_data = data[:split_idx].copy()

    print(f"\n🔬 Model Training Configuration:")
    print(f"   Training data: {len(train_series)} records ({split_idx})")
    print(f"   Testing data: {len(test_series)} records ({len(series) - split_idx})")
    print(f"   Forecast horizon: {forecast_periods} months")

    # Initialize results storage
    model_results = {}
    metrics_results = []
    forecast_results = {}

    # 1. PROPHET FORECAST
    print("\n🤖 Running Prophet forecast...")
    try:
        prophet_test_forecast, prophet_full_forecast = run_prophet_forecast(
            train_data, len(test_series), forecast_periods
        )

        prophet_metrics = evaluate_metrics(
            test_series.values,
            prophet_test_forecast["yhat"].values,
            "Prophet"
        )
        metrics_results.append(prophet_metrics)

        forecast_results["Prophet"] = {
            "test_forecast": prophet_test_forecast,
            "future_forecast": prophet_full_forecast,
            "test_predictions": prophet_test_forecast["yhat"].values
        }

        print(".2f"        print(".2f"        print(".2f"
    except Exception as e:
        print(f"❌ Prophet failed: {e}")
        metrics_results.append({
            "model": "Prophet", "error": str(e),
            "RMSE": None, "MSE": None, "MAE": None, "MAPE": None
        })

    # 2. ARIMA FORECAST
    print("\n📊 Running ARIMA forecast...")
    try:
        arima_test_forecast, arima_future_forecast = run_arima_forecast(
            train_series, len(test_series), forecast_periods
        )

        arima_metrics = evaluate_metrics(
            test_series.values,
            arima_test_forecast.values,
            "ARIMA"
        )
        metrics_results.append(arima_metrics)

        forecast_results["ARIMA"] = {
            "test_forecast": arima_test_forecast,
            "future_forecast": arima_future_forecast,
            "test_predictions": arima_test_forecast.values
        }

        print(".2f"        print(".2f"        print(".2f"
    except Exception as e:
        print(f"❌ ARIMA failed: {e}")
        metrics_results.append({
            "model": "ARIMA", "error": str(e),
            "RMSE": None, "MSE": None, "MAE": None, "MAPE": None
        })

    # 3. LSTM FORECAST
    print("\n🧠 Running LSTM forecast...")
    try:
        lstm_test_pred, lstm_future_pred = run_lstm_forecast(
            series, split_idx, len(test_series), forecast_periods
        )

        lstm_metrics = evaluate_metrics(
            test_series.values,
            lstm_test_pred,
            "LSTM"
        )
        metrics_results.append(lstm_metrics)

        # Create DataFrames for consistency
        lstm_future_df = pd.DataFrame({
            "ds": pd.date_range(series.index[-1], periods=forecast_periods+1, freq="M")[1:],
            "yhat": lstm_future_pred
        })

        forecast_results["LSTM"] = {
            "test_forecast": pd.Series(lstm_test_pred, index=test_series.index),
            "future_forecast": lstm_future_df,
            "test_predictions": lstm_test_pred
        }

        print(".2f"        print(".2f"        print(".2f"
    except Exception as e:
        print(f"❌ LSTM failed: {e}")
        metrics_results.append({
            "model": "LSTM", "error": str(e),
            "RMSE": None, "MSE": None, "MAE": None, "MAPE": None
        })

    # MODEL PERFORMANCE ANALYSIS
    print("\n📊 MODEL PERFORMANCE ANALYSIS")
    print("=" * 50)

    # Rank models by accuracy score (lower is better)
    valid_metrics = [m for m in metrics_results if m.get("accuracy_score") is not None]
    valid_metrics.sort(key=lambda x: x.get("accuracy_score", float('inf')))

    for rank, metric in enumerate(valid_metrics, 1):
        metric["rank"] = rank

    # Display performance table
    print("\n🏆 MODEL RANKING (Lower Accuracy Score = Better):")
    print("-" * 80)

    metrics_df = pd.DataFrame(metrics_results)
    if not metrics_df.empty:
        # Calculate rankings if we have valid metrics
        valid_rows = metrics_df.dropna(subset=['accuracy_score'])
        if not valid_rows.empty:
            metrics_df['rank'] = valid_rows['accuracy_score'].rank(method='dense').astype(int)
        else:
            metrics_df['rank'] = None

        print(metrics_df.to_string(index=False, float_format='%.3f'))

        # Best model recommendation
        best_model = None
        min_score = float('inf')

        for metric in metrics_results:
            score = metric.get("accuracy_score")
            if score is not None and score < min_score:
                min_score = score
                best_model = metric.get("model")

        if best_model:
            print(".3f"            print(f"💡 Recommended for deployment: {best_model}")

            # Model-specific insights
            print("\n🎯 MODEL INSIGHTS:")
            best_metrics = next(m for m in metrics_results if m.get("model") == best_model)
            if best_metrics.get("MAPE") is not None:
                print(".1f")
    else:
        print("No valid metrics available for analysis")

    # SAVE RESULTS
    output_prefix = f"enhanced_forecast_{country}_{pathogen}_{antibiotic}".replace(" ", "_")

    # Save metrics
    metrics_df.to_csv(f"data/{output_prefix}_metrics.csv", index=False)

    # Save forecasts
    forecast_combined = []
    for model_name, result in forecast_results.items():
        future_forecast = result.get("future_forecast")
        if future_forecast is not None:
            if isinstance(future_forecast, pd.DataFrame) and "ds" in future_forecast.columns:
                df_temp = future_forecast[["ds", "yhat"]].copy()
            else:
                # For ARIMA/Series results, create DataFrame
                future_dates = pd.date_range(series.index[-1], periods=forecast_periods+1, freq="M")[1:]
                if hasattr(future_forecast, 'values'):
                    values = future_forecast.values
                else:
                    values = future_forecast
                df_temp = pd.DataFrame({"ds": future_dates, "yhat": values})

            df_temp["model"] = model_name
            forecast_combined.append(df_temp)

    if forecast_combined:
        forecast_master = pd.concat(forecast_combined, ignore_index=True)
        forecast_master.to_csv(f"data/{output_prefix}_forecasts.csv", index=False)

        # Generate comparison plot
        generate_comparison_plot(series, test_series, forecast_results, forecast_periods,
                               country, pathogen, antibiotic, output_prefix)

    print(".2f")

    return {
        "metrics": metrics_df,
        "forecasts": forecast_results,
        "recommendation": best_model
    }

def generate_comparison_plot(series, test_series, forecast_results, forecast_periods,
                           country, pathogen, antibiotic, output_prefix):
    """Generate comprehensive comparison plot showing all models."""
    plt.figure(figsize=(14, 10))

    # Plot 1: Training data
    plt.subplot(2, 2, 1)
    plt.plot(series.index, series.values, 'b-', linewidth=2, label='Training Data')
    plt.title('Training Data')
    plt.xlabel('Date')
    plt.ylabel('Resistance (%)')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    # Plot 2: Forecast accuracy on test set
    plt.subplot(2, 2, 2)
    plt.plot(test_series.index, test_series.values, 'k-', linewidth=2, label='Actual Test', marker='o')

    colors = {'Prophet': 'red', 'ARIMA': 'blue', 'LSTM': 'green'}
    for model_name, result in forecast_results.items():
        if "test_predictions" in result:
            plt.plot(test_series.index, result["test_predictions"],
                    color=colors.get(model_name, 'gray'),
                    label=f'{model_name} Forecast')

    plt.title('Forecast Accuracy (Test Data)')
    plt.xlabel('Date')
    plt.ylabel('Resistance (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    # Plot 3: Future forecasts
    plt.subplot(2, 2, 3)
    future_dates = pd.date_range(series.index[-1], periods=forecast_periods+1, freq="M")[1:]

    plt.plot(series.index[-12:], series.values[-12:], 'k-', linewidth=2, label='Recent History', marker='o')

    for model_name, result in forecast_results.items():
        future_forecast = result.get("future_forecast")
        if future_forecast is not None:
            if isinstance(future_forecast, pd.DataFrame) and "yhat" in future_forecast.columns:
                plt.plot(future_dates[:min(len(future_dates), len(future_forecast))],
                        future_forecast["yhat"].values[:len(future_dates)],
                        color=colors.get(model_name, 'gray'), linewidth=2,
                        label=f'{model_name} Future', linestyle='--')

    plt.axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='Warning (70%)')
    plt.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Critical (80%)')

    plt.title('Future Forecast Projections')
    plt.xlabel('Date')
    plt.ylabel('Resistance (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    # Plot 4: Error analysis
    plt.subplot(2, 2, 4)

    error_data = []
    for i, model_name in enumerate(['Prophet', 'ARIMA', 'LSTM']):
        if model_name in forecast_results and "test_predictions" in forecast_results[model_name]:
            errors = test_series.values - forecast_results[model_name]["test_predictions"]
            error_data.append(errors)

    if error_data:
        plt.boxplot(error_data, labels=['Prophet', 'ARIMA', 'LSTM'])
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.title('Forecast Error Distribution')

    plt.suptitle(f'AMR Forecast Model Comparison: {pathogen} vs {antibiotic} in {country}',
                 fontsize=16, fontweight='bold')
    plt.tight_layout()

    # Save plot
    plt.savefig(f"data/{output_prefix}_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()

    print(f"📈 Comprehensive analysis plot saved: {output_prefix}_analysis.png")

def main():
    """Command-line interface."""
    if len(sys.argv) != 4:
        print("Usage: python pipeline/forecast_metrics.py <country> <pathogen> <antibiotic>")
        print("\nExample: python pipeline/forecast_metrics.py \"India\" \"E.coli\" \"Ciprofloxacin\"")
        print("\nOutputs:")
        print("- Performance metrics CSV (RMSE, MAE, MAPE)")
        print("- Forecast comparisons CSV")
        print("- Analysis visualization PNG")
        sys.exit(1)

    country, pathogen, antibiotic = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        results = forecast_and_evaluate_all(country, pathogen, antibiotic)

        if results:
            print("\n✅ Enhanced forecasting analysis complete!")
            print("📁 Check data/ folder for metrics, forecasts, and analysis plots")
        else:
            print("❌ Analysis failed")

    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {e}")

if __name__ == "__main__":
    main()
