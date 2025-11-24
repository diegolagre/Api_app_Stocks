[![CI Status](https://github.com/diegolagre/Api_app_Stocks/actions/workflows/tests.yml/badge.svg)](https://github.com/diegolagre/Api_app_Stocks/actions/workflows/tests.yml)

[![CI Status](https://github.com/diegolagre/Api_app_Stocks/actions/workflows/tests.yml/badge.svg)](https://github.com/diegolagre/Api_app_Stocks/actions/workflows/tests.yml)

# API App Stocks – Data Pipeline con Python, Airflow y Redshift

## 📌 ABSTRACT

Este Trabajo Práctico implementa un **pipeline de ingeniería de datos moderno y automatizado**, compuesto por:

- **Ingesta diaria** de datos de acciones desde la API de Yahoo Finance (yfinance)  
- **Transformaciones explícitas** (normalización, casting, categorización)  
- Persistencia en **CSV** y **Parquet (staging)**  
- **Carga incremental a Amazon Redshift**  
- **Orquestación completa con Apache Airflow** (incluye backfill)  
- **Calidad garantizada con tests unitarios + mocking**  
- Integración continua con **GitHub Actions (CI)**  

El pipeline cumple todos los requisitos del TP:
- Fuente de datos externa  
- Transformaciones explícitas  
- DW (Redshift)  
- Tests manuales + unitarios  
- Orquestación en Airflow  
- Flujo reproducible y automatizable  

---

# 🏗️ ARQUITECTURA GENERAL DEL PIPELINE

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
 | - Parquet staging (data/staging)     |
 +----------------+----------------------+
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

# 🔧 TRANSFORMACIONES IMPLEMENTADAS

La transformación principal se realiza en **transform_stock_data(df)**:

### ✔ Normalización de datos
- `Ticker` → **mayúsculas**
- `Price` → **entero seguro** (cast with coercion)

### ✔ Creación de columna derivada (categorización)
`Price_Bucket`:
- `LOW` → precios ≤ 100  
- `MEDIUM` → 100 < precio ≤ 500  
- `HIGH` → precio > 500  

### ✔ Limpieza
- Forzar tipos  
- Manejo de nulos  
- Unificación histórico sin duplicados (`Date`, `Ticker`)  



---

# 🧪 TESTS UNITARIOS

Los tests están en `tests/test_get_stock_data.py` e incluyen:

### 🟢 Test 1 – Mock de yfinance  
Valida:
- no se llama a la API real  
- conversión Price float → int  
- DataFrame generado correctamente  

### 🟢 Test 2 – Integración básica  
Verifica columna, tipos y estructura.

### 🟢 Test 3 – transform_stock_data  
Valida que las transformaciones funcionen:

- uppercase  
- Price int  
- Price_Bucket correcto  
- estructura final

GitHub Actions ejecuta automáticamente todos los tests en cada push.

---

# 🧭 DAG DE AIRFLOW

El DAG principal es:

`dags/stocks_redshift_daily_dag.py`

Tareas:

### 1️⃣ fetch_stocks_daily
- Obtiene datos  
- Aplica transformaciones  
- Genera CSV  
- Genera Parquet en `/opt/airflow/data/staging/`

### 2️⃣ load_to_redshift
- Lee el parquet  
- Inserta en Redshift usando SQLAlchemy  

Flujo:


Se ejecuta diariamente a las 10:00 UTC.

---

# 🗄️ CARGA A REDSHIFT

`app/src/redshift_loader.py`:

- Construye un engine con SQLAlchemy desde variables de entorno  
- Lee el Parquet  
- Inserta los datos en Redshift mediante `df.to_sql()`  
- Maneja creación del schema/tablas según config  

Variables que deben estar presentes (.env):

REDSHIFT_HOST=
REDSHIFT_PORT=5439
REDSHIFT_USER=
REDSHIFT_PASSWORD=
REDSHIFT_DB=
REDSHIFT_SCHEMA=public
REDSHIFT_TABLE=stock_prices_history


---

# 📂 ESTRUCTURA DEL PROYECTO

Api_app_Stocks/
├── app/
│ ├── constants.py
│ └── src/
│ ├── get_data.py
│ ├── redshift_loader.py
│ └── init.py
│
├── dags/
│ └── stocks_redshift_daily_dag.py
│
├── tests/
│ └── test_get_stock_data.py
│
├── data/
│ └── staging/
│ └── stock_prices_history.parquet
│
├── .github/workflows/tests.yml
├── .env.example
├── pyproject.toml
└── README.md


---

# 🚀 CÓMO EJECUTAR EL PROYECTO – PASO A PASO

A continuación tenés **todo el walkthrough completo**, tal como lo pediría un evaluador del TP.

---

## 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/diegolagre/Api_app_Stocks.git
cd Api_app_Stocks



##2️⃣ Configurar entorno con uv
uv sync

##3️⃣ Crear .env

cp .env.example .env
#Completá con tus credenciales reales de Redshift.

##4️⃣ Ejecutar solo la EXTRACCIÓN (opcional)

uv run python -m app.src.get_data

Esto genera:

stock_prices_history.csv
data/staging/stock_prices_history.parquet

##5️⃣ Ejecutar solo la CARGA a Redshift (opcional)

uv run python -m app.src.redshift_loader

##6️⃣ Ejecutar TESTS UNITARIOS

pytest -q

##7️⃣ Levantar Airflow con Docker (si corresponde en tu entorno)

docker compose up airflow-init
docker compose up

#Abrir:

#👉 http://localhost:8080

#Activar DAG:

#👉 stocks_redshift_daily_dag

#El pipeline descargará datos → transformará → generará staging → cargará Redshift.

##8️⃣ Verificar los datos en Redshift

SELECT * 
FROM public.stock_prices_history
ORDER BY date DESC, ticker;
