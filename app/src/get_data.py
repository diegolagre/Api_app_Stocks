import yfinance as yf
import pandas as pd
from datetime import datetime
from app.constants import stocks_list
# import aap_stocks.src.stocks_list as stocks_list
import os
from pathlib import Path

def get_stock_data(tickers):
    today = datetime.now().strftime("%Y-%m-%d")
    results = []

    for ticker in tickers:
        symbol = yf.Ticker(ticker)
        data = symbol.history(period="1d")
        if not data.empty:
            current_price = data["Close"].iloc[-1]

            # conversion a entro para testear 
            if isinstance(current_price, float):
                current_price = int(current_price)

            results.append({
                "Date": today,
                "Ticker": ticker,
                "Price": current_price
            })
            print(f"The current price of {ticker} is: ${current_price:.2f}")
        else:
            print(f"No data found for {ticker}. Please check the ticker symbol.")
    
    return pd.DataFrame(results)

def main():
    # Lista de tickers
    tickers_list =  stocks_list
    #print(tickers_list)
   

    # Archivo histórico donde se guardarán los datos
    stocks_diarios = "stock_prices_history.csv"

    # Obtener los precios de hoy
    df_today = get_stock_data(tickers_list)

    # Si el archivo ya existe, se agregan los nuevos registros
    if os.path.exists(stocks_diarios):
        df_history = pd.read_csv(stocks_diarios)
        # Evitar duplicados si ya se registró el mismo día
        df_combined = pd.concat([df_history, df_today]).drop_duplicates(subset=["Date", "Ticker"], keep="last")
    else:
        df_combined = df_today

    # Guardar el archivo actualizado
    df_combined.to_csv(stocks_diarios, index=False)

    # guarda también en Parquet como área de STAGING
    staging_dir = Path("data/staging")
    staging_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = staging_dir / "stock_prices_history.parquet"
    df_combined.to_parquet(parquet_path, index=False)
    print(f"Data saved/updated in Parquet: {parquet_path}")

    print(f"\nData saved/updated in: {stocks_diarios}")
    print("\nLast entries:")
    print(df_combined.tail())


if __name__ == "__main__":
    # Solo se ejecuta cuando corrés este archivo directamente:
    # uv run python -m app.src.get_data   ß
    main()