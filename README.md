![CI Status](https://github.com/diegolagre/Api_app_Stocks/actions/workflows/tests.yml/badge.svg)](https://github.com/diegolagre/Api_app_Stocks/actions/workflows/tests.yml)

# API App Stocks – Data Pipeline con Python, Airflow y Redshift

## 📌 Descripción general

Este proyecto implementa un pipeline de datos que:

- Obtiene diariamente precios de acciones desde la API de Yahoo Finance (`yfinance`).
- Aplica transformaciones explícitas sobre los datos (normalización, casting y categorización).
- Guarda el histórico en formato **CSV** y **Parquet**.
- Carga los datos transformados a **Amazon Redshift** usando SQLAlchemy.
- Orquesta todo con **Apache Airflow** corriendo en Docker.
- Asegura calidad con **tests unitarios** y **CI en GitHub Actions**.

---

## 🏗️ Arquitectura del pipeline

```text
            +----------------+
            |  yfinance API  |
            +--------+-------+
                     |
                     v
         +-----------------------+
         |  Extracción (Python)  |
         |  get_stock_data()     |
         +-----------+-----------+
                     |
                     v
      +--------------------------------+
      | Transformación (Python)        |
      | transform_stock_data()         |
      | - Normaliza Ticker             |
      | - Price float → int            |
      | - Price_Bucket (categorías)    |
      +--------------+-----------------+
                     |
                     v
     +--------------------------------------+
     | Persistencia local                   |
     | - CSV histórico                      |
     | - Parquet (data/staging)             |
     +----------------+---------------------+
                     |
                     v
         +------------------------------+
         |   Carga a Redshift (Python)  |
         | load_parquet_to_redshift()   |
         +--------------+---------------+
                     |
                     v
            +-------------------+
            |   Data Warehouse  |
            |     Redshift      |
            +-------------------+

---

## 🔧 Transformaciones de datos

La función `transform_stock_data(df)` aplica transformaciones de negocio sobre el DataFrame de precios:

- **Ticker** → convertido a mayúsculas.
- **Price** → preservado como **float** (tal cual viene desde la fuente).
- **Price_Bucket** calculado según rangos:
  - LOW → ≤ 100  
  - MEDIUM → 100–500  
  - HIGH → > 500

**Importante:**  
No se fuerza la conversión a `int` en el pipeline.  
Los tests unitarios validan que **se puede convertir** sin modificar el código productivo.

Adicionalmente:

- Eliminación de duplicados en el histórico por (`Date`, `Ticker`).
- Persistencia en CSV + Parquet.

---

## 🧪 Tests unitarios

Los tests incluidos verifican:

Incluyen:

### ✔ Test con mock de yfinance
- Simula la API sin hacer requests reales.
- Verifica que:
  - el DataFrame se produce correctamente,
  - `Price` es float,
  - puede convertirse a `int` si se necesitara.

### ✔ Test para transformaciones
- Verifica:
  - normalización del ticker,
  - tipo float de Price,
  - bucketización correcta.

### Ejecutar tests:

```bash
pytest -q

---

🗄️ Carga a Redshift

`redshift_loader.py`:

- Lee credenciales desde `.env`.
- Crea engine SQLAlchemy.
- Lee Parquet: `data/staging/stock_prices_history.parquet`.
- Ejecuta `to_sql()` hacia Redshift.

Variables necesarias:


REDSHIFT_HOST=
REDSHIFT_PORT=
REDSHIFT_USER=
REDSHIFT_PASSWORD=
REDSHIFT_DB=
REDSHIFT_SCHEMA=
REDSHIFT_TABLE=
PARQUET_PATH=data/staging/stock_prices_history.parquet


---

 🌬️ DAG de Airflow

`dags/stocks_redshift_daily_dag.py`

Tareas:

1. `fetch_stocks_daily`
2. `load_to_redshift`

Flujo:

```
fetch_stocks_daily >> load_to_redshift
```

Escribe CSV y Parquet en:

```
data/stock_prices_history.csv
data/staging/stock_prices_history.parquet
```

---

## 📂 Estructura del proyecto

```
Api_app_Stocks/
├── app/
│   ├── constants.py
│   └── src/
│       ├── get_data.py
│       ├── redshift_loader.py
│       └── __init__.py
├── dags/
│   └── stocks_redshift_daily_dag.py
├── tests/
│   └── test_get_stock_data.py
├── data/
│   └── staging/
├── .github/
│   └── workflows/
│       └── tests.yml
├── Dockerfile.airflow
├── docker-compose.yml
├── .env.example
├── pyproject.toml
└── README.md
```

---

## 💻 Ejecución local (Python)

```
uv sync
uv run python -m app.src.get_data
uv run python -m app.src.redshift_loader
```

---

## 🐳 Ejecución con Docker + Airflow

### 1. Crear archivo `.env`

```
cp .env.example .env
```

### 2. Construir la imagen:

```
docker compose build
```

### 3. Inicializar Airflow:

## 🧾 Atajos con Makefile para Airflow

Para simplificar la ejecución de Docker + Airflow, el proyecto incluye un `Makefile` con comandos de ayuda.

### Comandos disponibles

```bash
# Construir la imagen de Airflow (Dockerfile.airflow)
make airflow-build

# Inicializar la base de datos de Airflow
make airflow-init

# Crear usuario administrador de Airflow (admin / admin)
make airflow-create-user

# Levantar Airflow (webserver + scheduler + postgres)
make airflow-up

# Bajar todos los servicios de Airflow
make airflow-down

# Reset completo de Airflow:
# - baja servicios
# - borra volúmenes
# - build de imagen
# - init de DB
# - crea usuario admin
make airflow-reset

Flujo para levantar Airflow desde cero:

make airflow-build
make airflow-init
make airflow-create-user
make airflow-up

Luego, acceder a:

UI: http://localhost:8080

Usuario: admin

Password: admin

```
docker compose up airflow-init
```

### 4. Crear usuario admin:

```
docker compose run --rm airflow-webserver airflow users create   --username admin   --firstname Admin   --lastname User   --role Admin   --email admin@example.com   --password admin
```

### 5. Levantar Airflow:

```
docker compose up
```

UI: http://localhost:8080

Login: `admin / admin`

### 6. Activar y correr el DAG

1. Activar toggle del DAG  
2. "Trigger DAG"  
3. Revisar logs de `fetch_stocks_daily` y `load_to_redshift`.

---

## 🔐 Manejo de credenciales

`.env` debe estar en `.gitignore`  
`.env.example` solo contiene placeholders.

---

## ✅ Resumen de comandos

```
pytest -q
uv sync
docker compose build
docker compose up airflow-init
docker compose run --rm airflow-webserver airflow users create ...
docker compose up
docker compose down
```

