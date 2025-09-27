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
    if not prophet_available:
        raise ImportError("Prophet not available. Install with: pip install prophet")

    logger.info("Running Prophet forecast...")

    prophet_data = data.copy()
    prophet_data.columns = ['ds', 'y'] if len(prophet_data.columns) >= 2 else prophet_data.columns

    model = Prophet(
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0
    )

    model.fit(prophet_data)

    future = model.make_future_dataframe(periods=periods, freq="M")
    forecast = model.predict(future)

    columns = ["ds", "yhat"]
    if include_confidence:
        columns.extend(["yhat_lower", "yhat_upper"])

    result = forecast[columns].copy()
    result["model"] = "Prophet"

    logger.info(f"Prophet forecast completed: {len(result)} predictions")
    return result

def run_arima(data: pd.DataFrame,
               periods: int = 24,
               order: Tuple[int, int, int] = (2, 1, 2)) -> pd.DataFrame:
    if not statsmodels_available:
        raise ImportError("Statsmodels not available. Install with: pip install statsmodels")

    logger.info("Running ARIMA forecast...")

    ts_data = data.set_index('date')['percent_resistant'].dropna()
    ts_data = ts_data.resample('M').mean().fillna(method='ffill')

    logger.info(f"ARIMA training on {len(ts_data)} data points")

    model = ARIMA(ts_data, order=order)
    try:
        model_fit = model.fit()
    except Exception as e:
        logger.warning(f"ARIMA fit failed with order {order}, trying simpler model: {e}")
        model = ARIMA(ts_data, order=(1, 1, 1))
        model_fit = model.fit()

    forecast = model_fit.forecast(steps=periods)

    last_date = ts_data.index[-1]
    future_dates = pd.date_range(start=last_date, periods=periods+1, freq='M')[1:]

    result = pd.DataFrame({
        "ds": future_dates,
        "yhat": forecast.values
    })

    result["model"] = "ARIMA"

    logger.info(f"ARIMA forecast completed: {len(result)} predictions")
    return result

def run_lstm(data: pd.DataFrame,
              periods: int = 24,
              look_back: int = 5,
              epochs: int = 50,
              batch_size: int = 8) -> pd.DataFrame:
    if not tensorflow_available:
        raise ImportError("TensorFlow not available. Install with: pip install tensorflow scikit-learn")

    logger.info("Running LSTM forecast...")

    ts_data = data.set_index('date')['percent_resistant'].dropna()
    ts_data = ts_data.resample('M').mean().fillna(method='ffill')

    if len(ts_data) < look_back + 5:
        raise ValueError(f"Insufficient data for LSTM (need >= {look_back + 5} points, got {len(ts_data)})")

    logger.info(f"LSTM training on {len(ts_data)} data points")

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(ts_data.values.reshape(-1, 1))

    def create_dataset(data, look_back):
        X, y = [], []
        for i in range(len(data) - look_back):
            X.append(data[i:i+look_back, 0])
            y.append(data[i+look_back, 0])
        return np.array(X), np.array(y)

    X_train, y_train = create_dataset(scaled_data, look_back)

    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

    model = Sequential([
        LSTM(50, activation='relu', input_shape=(look_back, 1), return_sequences=False),
        Dense(25, activation='relu'),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    logger.info(f"Training LSTM for {epochs} epochs...")
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)

    predictions = []
    current_sequence = scaled_data[-look_back:].reshape(1, look_back, 1)

    for _ in range(periods):
        next_pred = model.predict(current_sequence, verbose=0)[0][0]
        predictions.append(next_pred)

        current_sequence = np.roll(current_sequence, -1, axis=1)
        current_sequence[0, -1, 0] = next_pred

    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

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
            results[model_name] = pd.DataFrame()

    return results
