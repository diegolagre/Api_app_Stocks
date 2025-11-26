# dags/stocks_redshift_daily_dag.py

from datetime import datetime, timedelta
import os
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

from app.src.get_data import get_stock_data
from app.constants import stocks_list
from app.src.redshift_loader import load_parquet_to_redshift


# Rutas de datos dentro del contenedor de Airflow
DATA_DIR = Path("/opt/airflow/data")
CSV_PATH = DATA_DIR / "stock_prices_history.csv"
PARQUET_PATH = DATA_DIR / "staging" / "stock_prices_history.parquet"


def fetch_stocks_daily(**context):
    """Tarea 1: obtiene precios, actualiza CSV y genera Parquet."""
    run_date = context["data_interval_start"].to_date_string()

    df_today = get_stock_data(stocks_list)

    if df_today.empty:
        print(f"[{run_date}] No hay datos.")
        return

    df_today["Date"] = run_date

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Actualizar CSV
    if CSV_PATH.exists():
        df_history = pd.read_csv(CSV_PATH)
        df_combined = (
            pd.concat([df_history, df_today], ignore_index=True)
            .drop_duplicates(subset=["Date", "Ticker"], keep="last")
        )
    else:
        df_combined = df_today

    df_combined.to_csv(CSV_PATH, index=False)

    # Generar Parquet en staging
    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_combined.to_parquet(PARQUET_PATH, index=False)

    print(f"[{run_date}] CSV y Parquet actualizados.")
    print(df_combined.tail())


def load_to_redshift_task(**context):
    """Tarea 2: carga el Parquet a Redshift."""
    schema = os.getenv("REDSHIFT_SCHEMA", "public")
    table_name = os.getenv("REDSHIFT_TABLE", "stock_prices_history")

    if not PARQUET_PATH.exists():
        raise FileNotFoundError(f"No existe el Parquet: {PARQUET_PATH}")

    load_parquet_to_redshift(
        parquet_path=PARQUET_PATH,
        table_name=table_name,
        schema=schema,
        if_exists="append",
        recreate_table=False,  # cambio: dropea la tabla y la recrea con el schema actual
    )


default_args = {
    "owner": "airflow",
    "depends_on_past": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stocks_redshift_daily_dag",
    default_args=default_args,
    schedule_interval="0 10 * * *",
    start_date=datetime(2025, 10, 1),
    catchup=True,
    max_active_runs=1,
    tags=["stocks", "yfinance", "redshift"],
) as dag:

    fetch_task = PythonOperator(
        task_id="fetch_stocks_daily",
        python_callable=fetch_stocks_daily,
    )

    load_redshift_task = PythonOperator(
        task_id="load_to_redshift",
        python_callable=load_to_redshift_task,
    )

    # Pipeline final:
    fetch_task >> load_redshift_task

