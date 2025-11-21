
import pandas as pd
from app.src.get_data import get_stock_data 
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

@patch("stocks.yf.Ticker")
@patch("stocks.datetime")


def test_get_stock_data_converts_float_to_int(mock_datetime, mock_ticker):
    # 🔹 Mock de fecha fija
    mock_datetime.now.return_value = datetime(2025, 11, 14, 12, 0, 0)

    # 🔹 Simular que yfinance devuelve un DataFrame con un float
    df_mock = pd.DataFrame({"Close": [123.45]})
    mock_ticker.return_value.history.return_value = df_mock

    # 🔹 Ejecutar función
    tickers = ["AAPL"]
    result_df = get_stock_data(tickers)

    # 🔹 Verificar que el resultado sea un entero
    assert result_df.loc[0, "Price"] == 123  # 123.45 → 123
    assert isinstance(result_df.loc[0, "Price"], int)
    assert result_df.loc[0, "Ticker"] == "AAPL"
    assert result_df.loc[0, "Date"] == "2025-11-14"