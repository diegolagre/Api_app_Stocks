
import pandas as pd
import numpy as np
from app.src.get_data import get_stock_data 
from unittest.mock import patch, Mock, MagicMock


@patch("app.src.get_data.yf.Ticker")

    # @patch("app.src.get_data.yf.Ticker")
    # es EXACTAMENTE el target a parchear porque:
    # el archivo está en app/src/get_data.py
    # adentro importo "import yfinance as yf"
    # por lo tanto Airflow lo resuelve como app.src.get_data.yf.Ticker


def test_get_stock_data_converts_float_to_int(mock_ticker):
    # simulo la respuesta de yfinance.history()
    df_mock = pd.DataFrame({"Close": [150.7, 200.9]})

    mock_instance = MagicMock()
    mock_instance.history.return_value = df_mock
    mock_ticker.return_value = mock_instance

    tickers = ["AAPL"]

    result = get_stock_data(tickers)

    # debe haber solo 1 fila
    assert len(result) == 1

    # último Close = 200.9 -> convertido a int = 200
    price = result.loc[0, "Price"]

    assert price == 200
    assert isinstance(price, (int, np.int64))
    assert not isinstance(price, float)
    assert result.loc[0, "Ticker"] == "AAPL"

@patch("app.src.get_data.yf.Ticker")
def test_get_stock_data_ignores_empty_history(mock_ticker, capsys):
    # simulamos que history() devuelve vacío
    mock_instance = MagicMock()
    mock_instance.history.return_value = pd.DataFrame()
    mock_ticker.return_value = mock_instance

    tickers = ["SAN"]

    result = get_stock_data(tickers)

    # DataFrame vacío → no debe agregar filas
    assert result.empty

    # validar mensaje por consola
    captured = capsys.readouterr()
    assert "No data found for SAN" in captured.out
