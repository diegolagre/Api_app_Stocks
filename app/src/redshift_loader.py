# app/src/redshift_loader.py

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_redshift_engine() -> Engine:
    """
    Crea un engine de SQLAlchemy para Redshift leyendo variables de entorno.

    Variables esperadas:
      - REDSHIFT_HOST
      - REDSHIFT_PORT
      - REDSHIFT_USER
      - REDSHIFT_PASSWORD
      - REDSHIFT_DB
    """

    host = os.getenv("REDSHIFT_HOST")
    port = os.getenv("REDSHIFT_PORT", "5439")
    user = os.getenv("REDSHIFT_USER")
    password = os.getenv("REDSHIFT_PASSWORD")
    dbname = os.getenv("REDSHIFT_DB")

    if not all([host, user, password, dbname]):
        raise ValueError(
            "Faltan variables de entorno para Redshift: "
            "REDSHIFT_HOST, REDSHIFT_USER, REDSHIFT_PASSWORD, REDSHIFT_DB"
        )

    # Formato requerido por SQLAlchemy para Redshift (driver postgres)
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(url)


def load_parquet_to_redshift(parquet_path, table_name, schema=None, if_exists="append"):
    """
    Carga un archivo Parquet a una tabla de Redshift usando pandas.to_sql.

    - parquet_path: ruta al archivo Parquet (string o Path)
    - table_name: nombre de la tabla en Redshift
    - schema: schema en Redshift (por ejemplo 'public')
    - if_exists: 'append' (default), 'replace' o 'fail'
    """
    parquet_path = Path(parquet_path)

    if not parquet_path.exists():
        raise FileNotFoundError(f"No existe el archivo Parquet: {parquet_path}")

    df = pd.read_parquet(parquet_path)

    if df.empty:
        print(f"No hay datos para cargar desde {parquet_path}")
        return

    engine = get_redshift_engine()

    print(
        f"Cargando {len(df)} filas a Redshift "
        f"(schema={schema}, table={table_name}, if_exists={if_exists})"
    )

    # Conexión y carga
    with engine.begin() as conn:
        df.to_sql(
            name=table_name,
            con=conn,
            schema=schema,
            if_exists=if_exists,
            index=False,
        )

    print("✅ Carga a Redshift finalizada.")


def main() -> None:
    """
    Entry point para ejecutar la carga a Redshift desde línea de comando.

    Usa las variables de entorno:
      - PARQUET_PATH
      - REDSHIFT_TABLE
      - REDSHIFT_SCHEMA
    """

    parquet_path = os.getenv(
        "PARQUET_PATH",
        "data/staging/stock_prices_history.parquet",
    )
    table_name = os.getenv("REDSHIFT_TABLE", "stock_prices_history")
    schema = os.getenv("REDSHIFT_SCHEMA", "public")

    load_parquet_to_redshift(
        parquet_path=parquet_path,
        table_name=table_name,
        schema=schema,
        if_exists="append",
    )


if __name__ == "__main__":
    # Para correrlo a mano:
    #   PARQUET_PATH=... REDSHIFT_...=... uv run python -m app.src.redshift_loader
    main()
