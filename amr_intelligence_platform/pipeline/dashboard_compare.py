import streamlit as st
import pandas as pd
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras import Sequential
from tensorflow.keras.layers import LSTM, Dense
import numpy as np

st.title("🦠 AMR Forecast Model Comparison")

df = pd.read_csv("data/amr_merged.csv")
df["date"] = pd.to_datetime(df["date"], errors="coerce")

country = st.sidebar.selectbox("Country", sorted(df["country"].dropna().unique()))
subset_country = df[df["country"] == country]

pathogen = st.sidebar.selectbox("Pathogen", sorted(subset_country["pathogen"].dropna().unique()))
subset_pathogen = subset_country[subset_country["pathogen"] == pathogen]

antibiotic = st.sidebar.selectbox("Antibiotic", sorted(subset_pathogen["antibiotic"].dropna().unique()))
subset = subset_pathogen[subset_pathogen["antibiotic"] == antibiotic]

if subset.empty:
    st.error("No data available.")
else:
    st.subheader(f"Comparing forecasts for {pathogen} vs {antibiotic} in {country}")

    # Prepare data
    data = subset[["date","percent_resistant"]].rename(columns={"date":"ds","percent_resistant":"y"}).dropna()

    # Prophet
    prophet = Prophet()
    prophet.fit(data)
    future = prophet.make_future_dataframe(periods=24, freq="M")
    forecast_prophet = prophet.predict(future)
    forecast_prophet["model"] = "Prophet"

    # ARIMA
    series = data.set_index("ds")["y"]
    arima_model = ARIMA(series, order=(2,1,2))
    arima_fit = arima_model.fit()
    forecast_arima = arima_fit.forecast(steps=24)
    future_dates = pd.date_range(start=series.index[-1], periods=24+1, freq="M")[1:]
    forecast_arima_df = pd.DataFrame({"ds": future_dates, "yhat": forecast_arima.values, "model": "ARIMA"})

    # LSTM
    values = series.values.reshape(-1,1)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(values)
    look_back = 5

    def create_dataset(dataset, look_back=5):
        X, Y = [], []
        for i in range(len(dataset)-look_back):
            X.append(dataset[i:i+look_back,0])
            Y.append(dataset[i+look_back,0])
        return np.array(X), np.array(Y)

    X, y = create_dataset(scaled, look_back)
    X = X.reshape((X.shape[0], look_back, 1))

    model = Sequential([
        LSTM(50, input_shape=(look_back,1)),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=20, batch_size=8, verbose=0)

    last_seq = scaled[-look_back:].reshape(1,look_back,1)
    preds = []
    current_seq = last_seq.copy()
    for _ in range(24):
        pred = model.predict(current_seq, verbose=0)[0][0]
        preds.append(pred)
        current_seq = np.roll(current_sequence, -1)
        current_seq[0,-1,0] = pred
    forecast_lstm = scaler.inverse_transform(np.array(preds).reshape(-1,1))
    future_dates_lstm = pd.date_range(start=data["ds"].max(), periods=24+1, freq="M")[1:]
    forecast_lstm_df = pd.DataFrame({"ds": future_dates_lstm, "yhat": forecast_lstm.flatten(), "model": "LSTM"})

    # Combine forecasts
    combined_forecasts = pd.concat([
        forecast_prophet[["ds", "yhat", "model"]],
        forecast_arima_df[["ds", "yhat", "model"]],
        forecast_lstm_df[["ds", "yhat", "model"]]
    ])

    # Plot comparison
    st.write("### Model Comparison Chart")
    st.line_chart(combined_forecasts.pivot(index="ds", columns="model", values="yhat"))

    # Data table
    st.write("### Forecast Data")
    st.dataframe(combined_forecasts)

    # Download button
    csv_data = combined_forecasts.to_csv(index=False)
    st.download_button("Download Forecasts", csv_data, "forecast_models.csv", "text/csv")
