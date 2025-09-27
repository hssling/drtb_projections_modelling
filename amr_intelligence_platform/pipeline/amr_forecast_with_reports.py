#!/usr/bin/env python3
"""
AMR Forecasting Pipeline with Automated Report Generation

Produces forecasts, performance metrics, and comprehensive ready-to-share reports
(DOCX + PDF) automatically for each analysis.

Features:
- Multi-model forecasting (Prophet, ARIMA, LSTM)
- Performance metrics evaluation (RMSE, MAE, MAPE)
- Automated professional report generation
- Model comparison visualizations
- Risk assessment and recommendations
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path
from datetime import datetime

# Import custom report generator
try:
    from reports_generator import AMRForecastReportGenerator
    REPORTS_AVAILABLE = True
except ImportError:
    print("⚠️ Report generator not available. Install python-docx and reportlab for full reporting.")
    REPORTS_AVAILABLE = False

def load_amr_data():
    """Load unified AMR dataset."""
    data_path = Path("data/amr_merged.csv")
    if not data_path.exists():
        print("❌ Unified AMR dataset not found. Run: python simple_amr_extract.py")
        sys.exit(1)

    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    return df

def evaluate_performance_metrics(true_values, predicted_values, model_name):
    """Calculate comprehensive performance metrics."""
    try:
        rmse = mean_squared_error(true_values, predicted_values, squared=False)
        mae = mean_absolute_error(true_values, predicted_values)
        mape = np.mean(np.abs((true_values - predicted_values) / true_values)) * 100
        mse = mean_squared_error(true_values, predicted_values)
        bias = np.mean(predicted_values - true_values)
        accuracy_score = rmse + mae + (mape / 100)  # Composite score

        return {
            "Model": model_name,
            "RMSE": float(rmse),
            "MAE": float(mae),
            "MAPE": float(mape),
            "MSE": float(mse),
            "bias": float(bias),
            "accuracy_score": float(accuracy_score),
            "sample_size": len(true_values)
        }
    except Exception as e:
        return {
            "Model": model_name,
            "error": str(e),
            "RMSE": None, "MAE": None, "MAPE": None
        }

def run_prophet_model(data, test_size, forecast_periods=24):
    """Run Prophet forecasting model."""
    print("🤖 Running Prophet model...")
    try:
        prophet_model = Prophet(
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0
        )

        prophet_model.fit(data)
        future = prophet_model.make_future_dataframe(periods=forecast_periods, freq="M")
        forecast = prophet_model.predict(future)

        # Test predictions
        test_pred = forecast["yhat"].iloc[-test_size:].values

        return {
            "test_predictions": test_pred,
            "future_forecast": forecast,
            "model_object": prophet_model
        }
    except Exception as e:
        print(f"❌ Prophet failed: {e}")
        return None

def run_arima_model(series_train, test_size, forecast_periods=24):
    """Run ARIMA forecasting model."""
    print("📊 Running ARIMA model...")
    try:
        arima_model = ARIMA(series_train, order=(2,1,2))
        arima_fit = arima_model.fit()

        # Test predictions
        test_pred = arima_fit.forecast(steps=test_size)

        # Future forecast
        future_pred = arima_fit.forecast(steps=forecast_periods)

        future_df = pd.DataFrame({
            "ds": pd.date_range(series_train.index[-1], periods=forecast_periods+1, freq="M")[1:],
            "yhat": future_pred.values
        })

        return {
            "test_predictions": test_pred.values,
            "future_forecast": future_df,
            "model_object": arima_fit
        }
    except Exception as e:
        print(f"❌ ARIMA failed: {e}")
        try:
            # Fallback to simpler model
            arima_fallback = ARIMA(series_train, order=(1,1,1))
            arima_fallback_fit = arima_fallback.fit()
            test_pred = arima_fallback_fit.forecast(steps=test_size)
            future_pred = arima_fallback_fit.forecast(steps=forecast_periods)

            future_df = pd.DataFrame({
                "ds": pd.date_range(series_train.index[-1], periods=forecast_periods+1, freq="M")[1:],
                "yhat": future_pred.values
            })

            return {
                "test_predictions": test_pred.values,
                "future_forecast": future_df,
                "model_object": arima_fallback_fit
            }
        except:
            return None

def run_lstm_model(series_all, split_idx, test_size, forecast_periods=24):
    """Run LSTM neural network forecasting model."""
    print("🧠 Running LSTM model...")
    try:
        scaler = MinMaxScaler()
        data_scaled = scaler.fit_transform(series_all.values.reshape(-1, 1))

        look_back = min(5, split_idx // 2)
        train_scaled = data_scaled[:split_idx]

        def create_dataset(dataset, look_back):
            X, y = [], []
            for i in range(len(dataset) - look_back):
                X.append(dataset[i:i+look_back, 0])
                y.append(dataset[i+look_back, 0])
            return np.array(X), np.array(y)

        X_train, y_train = create_dataset(train_scaled, look_back)
        X_train = X_train.reshape(X_train.shape[0], look_back, 1)

        model = Sequential([
            LSTM(50, activation='relu', input_shape=(look_back, 1), return_sequences=False),
            Dense(25, activation='relu'),
            Dense(1)
        ])

        model.compile(optimizer='adam', loss='mse')
        model.fit(X_train, y_train, epochs=20, batch_size=min(8, len(X_train)), verbose=0)

        # Test predictions
        test_scaled = data_scaled[split_idx:split_idx + test_size]
        pred_test = []
        current_seq = test_scaled[:look_back].reshape(1, look_back, 1)

        for _ in range(test_size):
            pred = model.predict(current_seq, verbose=0)[0][0]
            pred_test.append(pred)
            current_seq = np.roll(current_seq, -1, axis=1)
            current_seq[0, -1, 0] = pred

        pred_test = scaler.inverse_transform(np.array(pred_test).reshape(-1, 1)).flatten()

        # Future predictions
        pred_future = []
        for _ in range(forecast_periods):
            pred = model.predict(current_seq, verbose=0)[0][0]
            pred_future.append(pred)
            current_seq = np.roll(current_seq, -1, axis=1)
            current_seq[0, -1, 0] = pred

        pred_future = scaler.inverse_transform(np.array(pred_future).reshape(-1, 1)).flatten()

        future_df = pd.DataFrame({
            "ds": pd.date_range(series_all.index[-1], periods=forecast_periods+1, freq="M")[1:],
            "yhat": pred_future
        })

        return {
            "test_predictions": pred_test,
            "future_forecast": future_df,
            "model_object": model
        }
    except Exception as e:
        print(f"❌ LSTM failed: {e}")
        return None

def run_forecast_analysis(country, pathogen, antibiotic, forecast_periods=24, test_split=0.8):
    """
    Complete AMR forecasting analysis with automated reporting.

    Returns comprehensive results including forecasts, metrics, and reports.
    """
    print(f"🦠 STARTING AMR FORECASTING ANALYSIS")
    print(f"Target: {country} | {pathogen} | {antibiotic}")
    print("=" * 60)

    # Load and filter data
    df = load_amr_data()
    subset = df[(df["country"].str.lower() == country.lower()) &
                (df["pathogen"].str.lower() == pathogen.lower()) &
                (df["antibiotic"].str.lower() == antibiotic.lower())].dropna()

    if subset.empty:
        print("❌ No data found for this combination")
        available = df.groupby(['country', 'pathogen', 'antibiotic']).size().reset_index()
        print(f"Available combinations: {len(available)}")
        print(f"Sample countries: {sorted(df['country'].unique())[:5]}")
        return None

    print(f"📊 Dataset: {len(subset)} records")
    print(f"   Time range: {subset['date'].min()} to {subset['date'].max()}")
    print(f"   Current resistance: {subset['percent_resistant'].iloc[-1]:.1f}%")

    # Prepare time series data
    data_full = subset.copy()
    data_full["ds"] = data_full["date"]
    data_full["y"] = data_full["percent_resistant"]

    series_full = data_full.set_index("ds")["y"].dropna()
    series_full = series_full.sort_index()

    if len(series_full) < 10:
        print(f"❌ Insufficient data: {len(series_full)} records (need ≥10)")
        return None

    # Train/test split
    split_idx = int(len(series_full) * test_split)
    series_train = series_full[:split_idx]
    series_test = series_full[split_idx:]
    data_train = data_full[data_full["ds"].isin(series_train.index)].copy()

    print(f"🔬 Analysis Configuration:")
    print(f"   Training data: {len(series_train)} records ({split_idx})")
    print(f"   Testing data: {len(series_test)} records")
    print(f"   Forecast horizon: {forecast_periods} months")

    # Initialize results tracking
    model_results = []
    all_forecasts = {}
    metrics_list = []

    # Run all models
    models_to_run = [
        ("Prophet", run_prophet_model),
        ("ARIMA", run_arima_model),
        ("LSTM", run_lstm_model)
    ]

    for model_name, model_function in models_to_run:
        if model_name in ["Prophet"]:
            result = model_function(data_train, len(series_test), forecast_periods)
        elif model_name in ["ARIMA"]:
            result = model_function(series_train, len(series_test), forecast_periods)
        elif model_name == "LSTM":
            result = model_function(series_full, split_idx, len(series_test), forecast_periods)

        if result is None:
            # Model failed, add placeholder results
            metrics_list.append({
                "Model": model_name,
                "error": "Model execution failed",
                "RMSE": None, "MAE": None, "MAPE": None
            })
            all_forecasts[model_name] = {
                "test_predictions": np.array([]),
                "future_forecast": None
            }
            continue

        # Evaluate model performance
        test_true = series_test.values
        test_pred = result["test_predictions"]

        if len(test_true) > 0 and len(test_pred) > 0:
            min_len = min(len(test_true), len(test_pred))
            metrics = evaluate_performance_metrics(
                test_true[:min_len], test_pred[:min_len], model_name
            )
            metrics_list.append(metrics)

        all_forecasts[model_name] = result
        print(f"   ✓ {model_name} completed")

    # Convert metrics to DataFrame
    metrics_df = pd.DataFrame(metrics_list)

    if not metrics_df.empty:
        # Rank models and provide recommendations
        valid_metrics = metrics_df.dropna(subset=['accuracy_score'])
        if not valid_metrics.empty:
            metrics_df['rank'] = valid_metrics['accuracy_score'].rank(method='dense').astype(int)

        # Display comprehensive performance summary
        print("\n📊 MODEL PERFORMANCE ANALYSIS")
        print("=" * 50)

        print("\n🏆 MODEL RANKING (Lower Accuracy Score = Better):")
        print("-" * 80)

        display_df = metrics_df.copy()
        for col in ['RMSE', 'MAE', 'MAPE']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: '.3f' if pd.notna(x) else 'N/A')

        if 'rank' in display_df.columns:
            display_df = display_df.sort_values('rank')

        print(display_df.to_string(index=False))
        print()

        # Model recommendations
        if 'accuracy_score' in metrics_df.columns and metrics_df['accuracy_score'].notna().any():
            best_model = metrics_df.loc[metrics_df['accuracy_score'].idxmin(), 'Model']
            best_score = metrics_df['accuracy_score'].min()

            print("💡 ANALYSIS INSIGHT:")
            print(f"   Recommended Model: {best_model}")
            print(".3f")
            print("   This model showed the most reliable performance for this dataset.")

    # Generate visualizations
    print("\n📈 Generating comprehensive visualizations...")

    # Model comparison plot
    plt.figure(figsize=(14, 8))

    # Historical and test data
    plt.plot(series_train.index, series_train.values, 'b-', linewidth=2, label='Training Data')
    plt.plot(series_test.index, series_test.values, 'g-', linewidth=2, marker='o', label='Test Data (Actual)')

    # Model predictions
    colors = {'Prophet': 'red', 'ARIMA': 'blue', 'LSTM': 'orange'}
    for model_name, result in all_forecasts.items():
        if 'test_predictions' in result and len(result['test_predictions']) > 0:
            plt.plot(series_test.index, result['test_predictions'][:len(series_test)],
                    color=colors.get(model_name, 'gray'), linewidth=2, linestyle='--',
                    label=f'{model_name} Prediction')

    # Add future forecast extension (showing next 6 months)
    for model_name, result in all_forecasts.items():
        if result.get('future_forecast') is not None:
            future_df = result['future_forecast']
            if hasattr(future_df, 'head'):
                future_short = future_df.head(6)  # First 6 months
                if 'ds' in future_df.columns and 'yhat' in future_df.columns:
                    plt.plot(future_short['ds'], future_short['yhat'],
                            color=colors.get(model_name, 'gray'), linewidth=1,
                            linestyle=':', alpha=0.7,
                            label=f'{model_name} Future')

    # Add resistance thresholds
    plt.axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='Warning (70%)')
    plt.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='Critical (80%)')

    plt.title(f'AMR Forecast Model Comparison: {pathogen} vs {antibiotic} in {country}')
    plt.xlabel('Date')
    plt.ylabel('Resistance Percentage (%)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save plot
    plot_filename = f"amr_forecast_{country}_{pathogen}_{antibiotic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png".replace(" ", "_")
    plt.savefig(f"reports/{plot_filename}", dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   ✓ Comparison plot saved: reports/{plot_filename}")

    # Generate performance metrics plot
    if not metrics_df.empty and len([col for col in ['RMSE', 'MAE', 'MAPE'] if col in metrics_df.columns]) >= 2:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

        models = metrics_df['Model'].dropna().tolist()
        x_pos = range(len(models))

        # RMSE
        if 'RMSE' in metrics_df.columns:
            rmse_vals = metrics_df['RMSE'].dropna().tolist()
            if rmse_vals:
                ax1.bar(x_pos, rmse_vals, color=['red', 'blue', 'orange'][:len(rmse_vals)])
                ax1.set_title('Root Mean Square Error (RMSE)')
                ax1.set_xticks(x_pos)
                ax1.set_xticklabels(models, rotation=45)

        # MAE
        if 'MAE' in metrics_df.columns:
            mae_vals = metrics_df['MAE'].dropna().tolist()
            if mae_vals:
                ax2.bar(x_pos, mae_vals, color=['red', 'blue', 'orange'][:len(mae_vals)])
                ax2.set_title('Mean Absolute Error (MAE)')
                ax2.set_xticks(x_pos)
                ax2.set_xticklabels(models, rotation=45)

        # MAPE
        if 'MAPE' in metrics_df.columns:
            mape_vals = metrics_df['MAPE'].dropna().tolist()
            if mape_vals:
                ax3.bar(x_pos, mape_vals, color=['red', 'blue', 'orange'][:len(mape_vals)])
                ax3.set_title('Mean Absolute Percentage Error (MAPE %)')
                ax3.set_xticks(x_pos)
                ax3.set_xticklabels(models, rotation=45)

        # Combined performance
        if 'accuracy_score' in metrics_df.columns:
            acc_vals = metrics_df['accuracy_score'].dropna().tolist()
            if acc_vals:
                ax4.bar(x_pos, acc_vals, color=['red', 'blue', 'orange'][:len(acc_vals)])
                ax4.set_title('Composite Accuracy Score')
                ax4.set_xticks(x_pos)
                ax4.set_xticklabels(models, rotation=45)

        plt.suptitle('Model Performance Metrics Comparison')
        plt.tight_layout()

        metrics_plot_filename = f"metrics_{country}_{pathogen}_{antibiotic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png".replace(" ", "_")
        plt.savefig(f"reports/{metrics_plot_filename}", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"   ✓ Metrics plot saved: reports/{metrics_plot_filename}")

    # Auto-generate reports if available
    generated_files = {}
    if REPORTS_AVAILABLE:
        print("\n📄 Generating comprehensive reports...")

        try:
            report_generator = AMRForecastReportGenerator("reports")
            generated_files = report_generator.generate_comprehensive_report(
                country, pathogen, antibiotic,
                all_forecasts, metrics_df, subset
            )

            print("   📑 Generated reports:")
            for report_type, file_path in generated_files.items():
                if file_path and Path(file_path).exists():
                    print(f"      ✓ {report_type}: {Path(file_path).name}")
                else:
                    print(f"      ⚠️ {report_type}: Not available")

        except Exception as e:
            print(f"   ⚠️ Report generation failed: {e}")

    # Performance insights
    print("\n🎯 ANALYSIS SUMMARY:")

    if not metrics_df.empty:
        valid_models = metrics_df.dropna(subset=['accuracy_score'])
        if not valid_models.empty:
            best_model = valid_models.loc[valid_models['accuracy_score'].idxmin(), 'Model']
            best_score = valid_models['accuracy_score'].min()

            print(f"   🏆 Best Performing Model: {best_model}")
            print(".3f")

            # Risk assessment based on best model
            current_resistance = series_full.iloc[-1]

            if best_model in all_forecasts and all_forecasts[best_model].get('future_forecast') is not None:
                future_forecast = all_forecasts[best_model]['future_forecast']
                if hasattr(future_forecast, 'iloc'):
                    future_24m = future_forecast.iloc[-1] if hasattr(future_forecast, 'iloc') else future_forecast['yhat'].iloc[-1]
                elif isinstance(future_forecast, pd.DataFrame) and 'yhat' in future_forecast.columns:
                    future_24m = future_forecast['yhat'].iloc[-1]
                else:
                    future_24m = current_resistance

                change = future_24m - current_resistance

                print("\n   📈 Resistance Trajectory:")
                print(".1f")
                print(".1f")

                if future_24m > 80:
                    risk_level = "🚨 CRITICAL RISK"
                elif future_24m > 70:
                    risk_level = "⚠️ HIGH RISK"
                else:
                    risk_level = "✅ LOW RISK"

                print(f"   🏥 Risk Assessment: {risk_level}")
            else:
                print("   ⚠️ Unable to assess long-term risk")
        else:
            print("   ⚠️ No valid model results for analysis")
    else:
        print("   ⚠️ No metrics available for analysis")

        print("
✅ ANALYSIS COMPLETE!"
    if generated_files:
        print("📁 Reports available in reports/ folder")
    else:
        print("💡 Run with report generation libraries for full reports")

    # Return comprehensive results
    return {
        "metrics": metrics_df,
        "forecasts": all_forecasts,
        "historical_data": subset,
        "generated_reports": generated_files,
        "recommendation": best_model if 'best_model' in locals() else None
    }

def main():
    """Command-line interface for AMR forecasting with reports."""
    if len(sys.argv) != 4:
        print("🦠 AMR Forecasting Pipeline with Automated Reports")
        print("Usage: python pipeline/amr_forecast_with_reports.py <country> <pathogen> <antibiotic>")
        print("\nExample:")
        print('python pipeline/amr_forecast_with_reports.py "India" "E.coli" "Ciprofloxacin"')
        print("\nOutputs:")
        print("- Model comparison plots (PNG)")
        print("- Performance metrics analysis")
        print("- DOCX comprehensive report (full methodology & interpretation)")
        print("- PDF executive summary (key findings & recommendations)")
        print("\nRequirements: pip install python-docx reportlab")
        sys.exit(1)

    country, pathogen, antibiotic = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        results = run_forecast_analysis(country, pathogen, antibiotic)

        if results:
            print(f"\n📊 Analysis completed successfully!")
            if results.get('generated_reports'):
                report_count = len([r for r in results['generated_reports'].values() if r])
                print(f"📄 {report_count} professional reports generated")
        else:
            print("\n❌ Analysis failed - check parameters and data availability")

    except KeyboardInterrupt:
        print("\n⏹️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
