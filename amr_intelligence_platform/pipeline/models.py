#!/usr/bin/env python3
"""
AMR Forecasting Models - Comprehensive Multi-Model Implementation

Provides Prophet, ARIMA, and LSTM forecasting capabilities with standardized interfaces
for AMR (Antimicrobial Resistance) prediction. Supports both individual model runs
and comparative analysis across all three approaches.

Models:
- Prophet: Facebook's additive model with seasonality and trend detection
- ARIMA: Statistical time series analysis with autocorrelation
- LSTM: Deep learning neural network for complex pattern recognition

Usage:
    from pipeline.models import get_forecast
    forecast_df = get_forecast(data, model="prophet", periods=24)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Lazy imports to avoid loading all libraries if not needed
prophet_available = False
statsmodels_available = False
tensorflow_available = False

try:
    from prophet import Prophet
    prophet_available = True
except ImportError:
    logger.warning("Prophet not available. Install with: pip install prophet")

try:
    from statsmodels.tsa.arima.model import ARIMA
    statsmodels_available = True
except ImportError:
    logger.warning("Statsmodels not available. Install with: pip install statsmodels")

try:
    import tensorflow as tf
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    from sklearn.preprocessing import MinMaxScaler
    tensorflow_available = True
except ImportError:
    logger.warning("TensorFlow/SciKit-Learn not available. Install with: pip install tensorflow scikit-learn")

def run_prophet(data: pd.DataFrame,
                periods: int = 24,
                include_confidence: bool = True) -> pd.DataFrame:
    """
    Run Prophet forecasting on AMR data.

    Args:
        data: DataFrame with 'date' and 'percent_resistant' columns
        periods: Number of months to forecast ahead
        include_confidence: Include confidence intervals

    Returns:
        DataFrame with forecast results
    """
    if not prophet_available:
        raise ImportError("Prophet not available. Install with: pip install prophet")

    logger.info("Running Prophet forecast...")

    # Prepare data for Prophet
    prophet_data = data.copy()
    prophet_data.columns = ['ds', 'y'] if len(prophet_data.columns) >= 2 else prophet_data.columns

    # Fit Prophet model with AMR-specific parameters
    model = Prophet(
        yearly_seasonality=True,      # AMR often has yearly patterns
        changepoint_prior_scale=0.05, # Flexibility in detecting trend changes
        seasonality_prior_scale=10.0  # Strength of seasonality
    )

    model.fit(prophet_data)
    logger.info("Prophet model fitted successfully")

    # Create future dataframe
    future = model.make_future_dataframe(periods=periods, freq="M")
    forecast = model.predict(future)

    # Select relevant columns
    columns = ["ds", "yhat"]
    if include_confidence:
        columns.extend(["yhat_lower", "yhat_upper"])

    result = forecast[columns].copy()
    result["model"] = "Prophet"

    # Add trend and seasonality components
    if "trend" in forecast.columns:
        result["trend"] = forecast["trend"]

    logger.info(f"Prophet forecast completed: {len(result)} predictions")
    return result

def run_arima(data: pd.DataFrame,
               periods: int = 24,
               order: Tuple[int, int, int] = (2, 1, 2)) -> pd.DataFrame:
    """
    Run ARIMA forecasting on AMR data.

    Args:
        data: DataFrame with 'date' and 'percent_resistant' columns
        periods: Number of months to forecast ahead
        order: ARIMA order (p, d, q) - default (2,1,2) for AMR data

    Returns:
        DataFrame with forecast results
    """
    if not statsmodels_available:
        raise ImportError("Statsmodels not available. Install with: pip install statsmodels")

    logger.info("Running ARIMA forecast...")

    # Prepare time series data
    ts_data = data.set_index('date')['percent_resistant'].dropna()
    ts_data = ts_data.resample('M').mean().fillna(method='ffill')

    logger.info(f"ARIMA training on {len(ts_data)} data points")

    # Fit ARIMA model
    model = ARIMA(ts_data, order=order)
    try:
        model_fit = model.fit()
        logger.info("ARIMA model fitted successfully")
    except Exception as e:
        logger.warning(f"ARIMA fit failed with order {order}, trying simpler model: {e}")
        # Fallback to simpler model
        model = ARIMA(ts_data, order=(1, 1, 1))
        model_fit = model.fit()

    # Generate forecast
    forecast = model_fit.forecast(steps=periods)

    # Create result DataFrame
    last_date = ts_data.index[-1]
    future_dates = pd.date_range(start=last_date, periods=periods+1, freq='M')[1:]

    result = pd.DataFrame({
        "ds": future_dates,
        "yhat": forecast.values
    })

    result["model"] = "ARIMA"

    # Add model diagnostics if available
    try:
        aic = model_fit.aic
        result["aic"] = aic
    except:
        pass

    logger.info(f"ARIMA forecast completed: {len(result)} predictions")
    return result

def run_lstm(data: pd.DataFrame,
              periods: int = 24,
              look_back: int = 5,
              epochs: int = 50,
              batch_size: int = 8) -> pd.DataFrame:
    """
    Run LSTM forecasting on AMR data.

    Args:
        data: DataFrame with 'date' and 'percent_resistant' columns
        periods: Number of months to forecast ahead
        look_back: Number of previous time steps to use for prediction
        epochs: Number of training epochs
        batch_size: Training batch size

    Returns:
        DataFrame with forecast results
    """
    if not tensorflow_available:
        raise ImportError("TensorFlow not available. Install with: pip install tensorflow scikit-learn")

    logger.info("Running LSTM forecast...")

    # Prepare data
    ts_data = data.set_index('date')['percent_resistant'].dropna()
    ts_data = ts_data.resample('M').mean().fillna(method='ffill')

    if len(ts_data) < look_back + 5:
        raise ValueError(f"Insufficient data for LSTM (need >= {look_back + 5} points, got {len(ts_data)})")

    logger.info(f"LSTM training on {len(ts_data)} data points")

    # Scale data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(ts_data.values.reshape(-1, 1))

    # Create training data
    def create_dataset(data, look_back):
        X, y = [], []
        for i in range(len(data) - look_back):
            X.append(data[i:i+look_back, 0])
            y.append(data[i+look_back, 0])
        return np.array(X), np.array(y)

    X_train, y_train = create_dataset(scaled_data, look_back)

    # Reshape for LSTM [samples, time steps, features]
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

    # Build LSTM model
    model = Sequential([
        LSTM(50, activation='relu', input_shape=(look_back, 1), return_sequences=False),
        Dense(25, activation='relu'),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    # Train model with silent output
    logger.info(f"Training LSTM for {epochs} epochs...")
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)

    # Generate forecasts
    predictions = []
    current_sequence = scaled_data[-look_back:].reshape(1, look_back, 1)

    for _ in range(periods):
        # Predict next value
        next_pred = model.predict(current_sequence, verbose=0)[0][0]
        predictions.append(next_pred)

        # Update sequence with new prediction
        current_sequence = np.roll(current_sequence, -1, axis=1)
        current_sequence[0, -1, 0] = next_pred

    # Inverse transform predictions
    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

    # Create result DataFrame
    last_date = ts_data.index[-1]
    future_dates = pd.date_range(start=last_date, periods=periods+1, freq='M')[1:]

    result = pd.DataFrame({
        "ds": future_dates,
        "yhat": predictions.flatten()
    })

    result["model"] = "LSTM"

    logger.info(f"LSTM forecast completed: {len(result)} predictions")
    return result

def get_forecast(data: pd.DataFrame,
                 model: str = "prophet",
                 periods: int = 24,
                 **kwargs) -> pd.DataFrame:
    """
    Unified interface for running any forecasting model.

    Args:
        data: DataFrame with 'date' and 'percent_resistant' columns
        model: Model to use ('prophet', 'arima', 'lstm')
        periods: Number of periods to forecast
        **kwargs: Additional model-specific parameters

    Returns:
        DataFrame with forecast results
    """
    model = model.lower()

    if model == "prophet":
        return run_prophet(data, periods, **kwargs)
    elif model == "arima":
        return run_arima(data, periods, **kwargs)
    elif model == "lstm":
        return run_lstm(data, periods, **kwargs)
    else:
        raise ValueError(f"Unknown model: {model}. Choose from 'prophet', 'arima', 'lstm'")

def compare_models(data: pd.DataFrame,
                   models: List[str] = None,
                   periods: int = 24,
                   **kwargs) -> Dict[str, pd.DataFrame]:
    """
    Compare multiple forecasting models side-by-side.

    Args:
        data: DataFrame with 'date' and 'percent_resistant' columns
        models: List of models to compare (default: all)
        periods: Number of periods to forecast
        **kwargs: Additional parameters for individual models

    Returns:
        Dictionary of model name -> forecast DataFrame
    """
    if models is None:
        models = ["prophet", "arima", "lstm"]

    results = {}

    for model_name in models:
        try:
            logger.info(f"Running {model_name} forecast...")
            forecast_df = get_forecast(data, model_name, periods, **kwargs)
            results[model_name] = forecast_df
            logger.info(f"{model_name} forecast completed successfully")
        except Exception as e:
            logger.error(f"{model_name} forecast failed: {e}")
            # Create empty DataFrame for failed model
            results[model_name] = pd.DataFrame()

    return results

def evaluate_forecasts(actual: pd.Series,
                       forecasts: Dict[str, pd.DataFrame],
                       train_split: float = 0.8) -> Dict[str, Dict[str, float]]:
    """
    Evaluate forecast accuracy against holdout data.

    Args:
        actual: Actual resistance values (pd.Series or DataFrame)
        forecasts: Dictionary of model forecasts
        train_split: Fraction of data to use for training

    Returns:
        Dictionary of model evaluation metrics
    """
    if isinstance(actual, pd.DataFrame):
        actual = actual['percent_resistant'] if 'percent_resistant' in actual.columns else actual.iloc[:, 0]

    # Split data
    split_idx = int(len(actual) * train_split)
    train_data = actual[:split_idx]
    test_data = actual[split_idx:split_idx+len(actual)-split_idx]  # Match forecast length

    results = {}

    for model_name, forecast_df in forecasts.items():
        if forecast_df.empty:
            results[model_name] = {"error": "Model failed to produce forecast"}
            continue

        try:
            # Get predictions for test period
            pred_values = forecast_df['yhat'].values

            if len(pred_values) != len(test_data):
                # Adjust lengths
                min_len = min(len(pred_values), len(test_data))
                pred_values = pred_values[:min_len]
                actual_values = test_data.values[:min_len]
            else:
                actual_values = test_data.values

            # Calculate metrics
            mse = np.mean((actual_values - pred_values) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(actual_values - pred_values))
            mape = np.mean(np.abs((actual_values - pred_values) / actual_values)) * 100

            results[model_name] = {
                "MSE": mse,
                "RMSE": rmse,
                "MAE": mae,
                "MAPE": mape
            }

        except Exception as e:
            results[model_name] = {"error": f"Evaluation failed: {e}"}

    return results
