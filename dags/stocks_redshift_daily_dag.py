from datetime import datetime, timedelta
import os
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

# Importamos tu código de la app
from app.src.get_data import get_stock_data
from app.constants import stocks_list
from app.src.redshift_loader import load_parquet_to_redshift 


# Ruta donde se va a guardar el histórico dentro del contenedor de Airflow
STOCKS_FILE = "/opt/airflow/data/stock_prices_history.csv"


def run_stocks_job(**context):
    """
    Job diario:
    - Usa la lista de tickers de app.constants
    - Llama a get_stock_data (que usa yfinance)
    - Fuerza la columna Date a la fecha lógica del DAG (data_interval_start)
    - Actualiza el CSV histórico evitando duplicados (Date + Ticker)
    """
    # Fecha lógica manejada por Airflow (backfill incluido)
    run_date = context["data_interval_start"].to_date_string()  # YYYY-MM-DD

    # 1) Obtener precios (tu función actual)
    df_today = get_stock_data(stocks_list)

    # 2) Sobrescribimos Date con la fecha lógica del DAG
    if not df_today.empty:
        df_today["Date"] = run_date

    # 3) Append / upsert al CSV histórico
    if os.path.exists(STOCKS_FILE):
        df_history = pd.read_csv(STOCKS_FILE)
        df_combined = (
            pd.concat([df_history, df_today], ignore_index=True)
            .drop_duplicates(subset=["Date", "Ticker"], keep="last")
        )
    else:
        df_combined = df_today

    # Crear carpeta destino si no existe
    os.makedirs(os.path.dirname(STOCKS_FILE), exist_ok=True)

    df_combined.to_csv(STOCKS_FILE, index=False)

    print(f"[{run_date}] Data saved/updated in: {STOCKS_FILE}")
    print(df_combined.tail())


default_args = {
    "owner": "airflow",
    "depends_on_past": True,          # para backfill ordenado
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stocks_daily_dag",
    default_args=default_args,
    description="Descarga diaria de precios de acciones con yfinance",
    schedule_interval="0 10 * * *",   # todos los días 10:00 UTC
    start_date=datetime(2025, 10, 1), # ajustá desde cuándo querés backfill
    catchup=True,                     # Airflow maneja el backfill
    max_active_runs=1,
    tags=["stocks", "yfinance", "batch"],
) as dag:

    fetch_stocks = PythonOperator(
        task_id="fetch_stocks_daily",
        python_callable=run_stocks_job,
    )

    fetch_stocks
