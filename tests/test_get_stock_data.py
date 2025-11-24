
import pandas as pd
import numpy as np
from app.src.get_data import get_stock_data, transform_stock_data
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


def test_transform_stock_data_adds_bucket_and_casts_int():
    # DataFrame de ejemplo sin pasar por yfinance
    df = pd.DataFrame({
        "Date": ["2025-01-01", "2025-01-01", "2025-01-01"],
        "Ticker": ["aapl", "NVDA", "GOOGL"],
        "Price": [50.9, 250.1, 900.0],
    })

    transformed = transform_stock_data(df)

    # Debe tener la nueva columna
    assert "Price_Bucket" in transformed.columns

    # Tickers normalizados a mayúsculas
    assert transformed["Ticker"].tolist() == ["AAPL", "NVDA", "GOOGL"]

    # Price debe ser entero (int o numpy int)
    assert transformed["Price"].dtype.kind in ("i", "u")  # signed/unsigned int

    # Validar los buckets por ticker
    bucket_map = dict(
        zip(
            transformed["Ticker"],
            transformed["Price_Bucket"].astype(str)
        )
    )

    assert bucket_map["AAPL"] == "LOW"      # 50 → LOW
    assert bucket_map["NVDA"] == "MEDIUM"   # 250 → MEDIUM
    assert bucket_map["GOOGL"] == "HIGH"    # 900 → HIGH