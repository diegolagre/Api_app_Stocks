
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from app.src.get_data import get_stock_data, transform_stock_data


# ------------------------------------------------------------------------------
# TEST 1 — Mock de yfinance + validación de estructura + conversión int SOLO en el test
# ------------------------------------------------------------------------------
@patch("app.src.get_data.yf.Ticker")
def test_get_stock_data_can_convert_price_to_int(mock_ticker):
    """
    Este test NO requiere modificar el código productivo.
    - yfinance es mockeado
    - get_stock_data devuelve Price en float
    - el test valida que puede convertirse a int si se necesita
    """

    # Mock del DataFrame devuelto por yfinance
    df_mock = pd.DataFrame({"Close": [150.7, 200.9]})

    mock_instance = MagicMock()
    mock_instance.history.return_value = df_mock
    mock_ticker.return_value = mock_instance

    tickers = ["AAPL"]

    df = get_stock_data(tickers)

    # Debe tener una fila (último precio del mock)
    assert len(df) == 1

    # Price debe ser float
    price = df.loc[0, "Price"]
    assert isinstance(price, float)

    # Conversión a int SOLO PARA EL TEST (no para el pipeline)
    price_int = int(price)
    assert isinstance(price_int, int)
    assert price_int == 200  # int(200.9) → 200


# ------------------------------------------------------------------------------
# TEST 2 — Verificar transformaciones de negocio
# ------------------------------------------------------------------------------
def test_transform_stock_data_applies_business_logic_correctly():
    """
    Valida que:
    - Ticker se normalice a uppercase
    - Price sea float
    - Price_Bucket se asigne correctamente
    """

    df_input = pd.DataFrame(
        {
            "Date": ["2025-01-01", "2025-01-01", "2025-01-01"],
            "Ticker": ["aapl", "msft", "goog"],
            "Price": [50.0, 300.0, 900.0],
        }
    )

    df_out = transform_stock_data(df_input)

    # 1) Ticker uppercase
    assert list(df_out["Ticker"]) == ["AAPL", "MSFT", "GOOG"]

    # 2) Price sigue siendo float
    assert df_out["Price"].dtype in [float, np.float64]

    # 3) Price_Bucket correcto
    assert list(df_out["Price_Bucket"]) == ["LOW", "MEDIUM", "HIGH"]