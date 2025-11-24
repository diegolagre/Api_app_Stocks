# app/src/get_data.py

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

from app.constants import stocks_list


def get_stock_data(tickers):
    """
    Descarga el precio de cierre del día actual para cada ticker de la lista.

    Devuelve un DataFrame con columnas:
      - Date (str, YYYY-MM-DD)
      - Ticker (str)
      - Price (float, tal cual viene de yfinance)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    results = []

    for ticker in tickers:
        symbol = yf.Ticker(ticker)
        data = symbol.history(period="1d")

        if not data.empty:
            # Close viene como float y se mantiene así
            current_price = data["Close"].iloc[-1]
            results.append(
                {
                    "Date": today,
                    "Ticker": ticker,
                    "Price": float(current_price),
                }
            )
            print(f"The current price of {ticker} is: ${current_price:.2f}")
        else:
            print(f"No data found for {ticker}. Please check the ticker symbol.")

    return pd.DataFrame(results)


def transform_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica transformaciones de negocio al DataFrame de stocks:

    - Normaliza el ticker a mayúsculas.
    - Se asegura de que Price sea numérico (float), pero NO lo castea a int.
    - Agrega una columna categórica Price_Bucket según el rango de precio:
        LOW    → Price <= 100
        MEDIUM → 100 < Price <= 500
        HIGH   → Price > 500
    """
    if df.empty:
        return df

    df = df.copy()

    # 1) Normalizar Ticker
    df["Ticker"] = df["Ticker"].astype(str).str.upper()

    # 2) Asegurar que Price sea numérico (float)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # 3) Agregar Price_Bucket en base al valor de Price
    df["Price_Bucket"] = pd.cut(
        df["Price"],
        bins=[-1, 100, 500, float("inf")],
        labels=["LOW", "MEDIUM", "HIGH"],
    )

    return df


def main() -> None:
    """
    Ejecuta el flujo completo en modo script:
      - Obtiene precios de los tickers definidos en app.constants.stocks_list.
      - Actualiza el CSV histórico en data/stock_prices_history.csv.
      - Aplica transformaciones de negocio.
      - Genera un Parquet en data/staging/stock_prices_history.parquet.
    """
    # Directorios de datos
    data_dir = Path("data")
    staging_dir = data_dir / "staging"
    data_dir.mkdir(parents=True, exist_ok=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / "stock_prices_history.csv"
    parquet_path = staging_dir / "stock_prices_history.parquet"

    tickers_list = stocks_list
    print(f"Tickers a consultar: {tickers_list}")

    # Obtener datos de hoy
    df_today = get_stock_data(tickers_list)

    # Merge con histórico si existe
    if csv_path.exists():
        df_history = pd.read_csv(csv_path)
        df_combined = (
            pd.concat([df_history, df_today], ignore_index=True)
            .drop_duplicates(subset=["Date", "Ticker"], keep="last")
        )
    else:
        df_combined = df_today

    # Aplicar transformaciones de negocio
    df_transformed = transform_stock_data(df_combined)

    # Guardar CSV (con Price en float)
    df_transformed.to_csv(csv_path, index=False)
    print(f"\nData saved/updated in CSV: {csv_path}")

    # Guardar Parquet (staging)
    df_transformed.to_parquet(parquet_path, index=False)
    print(f"Data saved/updated in Parquet: {parquet_path}")

    print("\nLast entries:")
    print(df_transformed.tail())


if __name__ == "__main__":
    main()