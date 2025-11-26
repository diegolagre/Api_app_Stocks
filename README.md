[![CI Status](https://github.com/diegolagre/Api_app_Stocks/actions/workflows/tests.yml/badge.svg)](https://github.com/diegolagre/Api_app_Stocks/actions/workflows/tests.yml)

# 🚀 API App Stocks  
### *Data Pipeline con Python, Airflow, Docker y Redshift*

---

# 📘 1. Descripción general

Este proyecto implementa un **pipeline de ingeniería de datos** capaz de:

✅ Extraer precios diarios de acciones desde **Yahoo Finance (yfinance)**  
✅ Transformar datos (normalización + bucketización)  
✅ Guardar histórico en **CSV y Parquet**  
✅ Cargar datos procesados en **Amazon Redshift**  
✅ Orquestar todo con **Apache Airflow** en Docker  
✅ Validación con **tests unitarios** + **CI en GitHub Actions**

---

# 🏗️ 2. Arquitectura del Pipeline


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

# 🔧 3. Transformaciones aplicadas

La función `transform_stock_data(df)` realiza:

### ✔ Normalización  
- `Ticker` → siempre en **mayúsculas**

### ✔ Mantiene tipos nativos  
- `Price` → **float**, sin convertir a int en el pipeline

### ✔ Nueva columna: `Price_Bucket`  
Según el valor:

| Rango | Categoría |
|-------|-----------|
| `≤ 100` | LOW |
| `100–500` | MEDIUM |
| `> 500` | HIGH |

### ✔ Persistencia
- Se eliminan duplicados por *Date + Ticker*
- Se genera **CSV** y **Parquet**

---

# 🧪 4. Tests unitarios

Ubicación:

tests/test_get_stock_data.py

Los tests cubren:

### ✔ Mock de yfinance  
- Simula la API  
- Evita llamadas reales

### ✔ Validación de estructura de DataFrame

### ✔ Conversión a int (solo test)
- El pipeline mantiene float  
- El test asegura que puede convertirse si se necesitara

### ✔ Prueba de transformaciones:
- Uppercase de `Ticker`
- `Price` es float
- Bucketización correcta

Ejecutar tests:


pytest -q

# 🗄️ 5. Carga a Redshift

Archivo:
app/src/redshift_loader.py

Hace:

Lee Parquet desde data/staging/

Construye motor SQLAlchemy con credenciales desde .env

Inserta los datos en Redshift usando to_sql()

Variables necesarias (.env):

```
REDSHIFT_HOST=
REDSHIFT_PORT=5439
REDSHIFT_USER=
REDSHIFT_PASSWORD=
REDSHIFT_DB=
REDSHIFT_SCHEMA=public
REDSHIFT_TABLE=stock_prices_history
PARQUET_PATH=data/staging/stock_prices_history.parquet
```
⚠ .env no debe ser committeado.
Usar .env.example como plantilla.

# 🌬️ 6. DAG de Airflow

Ruta:
dags/stocks_redshift_daily_dag.py

Tareas:

1️⃣ fetch_stocks_daily

Extrae precios

Ajusta fecha con data_interval_start

Aplica transformaciones

Actualiza CSV + Parquet

2️⃣ load_to_redshift

Lee parquet

Carga datos a Redshift

Flujo:

fetch_stocks_daily >> load_to_redshift


# 📂 7. Estructura del proyecto


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
├── .github/workflows/tests.yml
├── Dockerfile.airflow
├── docker-compose.yml
├── Makefile
├── .env.example
└── pyproject.toml
```

# 💻 8. Ejecución local (sin Docker)

```
uv sync
uv run python -m app.src.get_data
uv run python -m app.src.redshift_loader
```

# 🐳 9. Ejecución con Docker + Airflow

🔹 9.1 Crear .env

cp .env.example .env
Completar valores.

🔹 9.2 Comandos con Makefile (recomendado)

```
make airflow-build
make airflow-init
make airflow-create-user
make airflow-up
```

Airflow UI:
👉 http://localhost:8080

Usuario: admin
Password: admin

🔹 9.3 Sin Makefile

docker compose build
docker compose up airflow-init
docker compose run --rm airflow-webserver airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin
docker compose up

Activar DAG → “Trigger DAG” → Ver logs.

# 🔐 10. Manejo de credenciales



Crear un archivo .env en la raiz:

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
├── .github/workflows/tests.yml
├── Dockerfile.airflow
├── docker-compose.yml
├── Makefile
├── .env.example
├── .env
└── pyproject.toml
```

Se debe tomar como plantilla el archivo .env.example. Pegarlo en el archivo .env y completar las credenciales.

.env debe estar en .gitignore

# ✔ 11. Resumen general

```
pytest -q
uv sync
make airflow-build
make airflow-init
make airflow-create-user
make airflow-up
make airflow-down
make airflow-reset
```

