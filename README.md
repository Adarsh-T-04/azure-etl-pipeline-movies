# 🎬 Azure ETL Pipeline — Movies Dataset

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-green?style=flat-square&logo=pandas)
![Azure SQL](https://img.shields.io/badge/Azure-SQL%20Database-0078D4?style=flat-square&logo=microsoft-azure)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red?style=flat-square)

A **production-ready ETL (Extract → Transform → Load) pipeline** that processes **19,808 IMDb movie records** from CSV and bulk-loads them into **Azure SQL Database** using Python, Pandas, and SQLAlchemy.

---

## 📌 Project Overview

| Item | Details |
|---|---|
| **Dataset** | IMDb Movies — 19,808 rows, 14 columns |
| **Source** | CSV file (local) |
| **Destination** | Azure SQL Database |
| **Language** | Python 3.10+ |
| **Key Libraries** | Pandas, SQLAlchemy, pyodbc, PyYAML |

---

## 🗂️ Project Structure

```
azure_etl_pipeline/
│
├── src/
│   ├── pipeline.py         # Main orchestrator — runs E → T → L
│   ├── extractor.py        # CSV reader + schema validation
│   ├── transformer.py      # Data cleaning & normalization
│   ├── loader.py           # Azure SQL bulk loader
│   └── config_loader.py    # YAML config + env variable injection
│
├── config/
│   └── config.yaml         # Pipeline configuration
│
├── data/
│   └── movies.csv          # IMDb movies dataset (19,808 rows)
│
├── tests/
│   └── test_pipeline.py    # Pytest unit tests
│
├── logs/                   # Auto-generated daily log files
├── requirements.txt
└── README.md
```

---

## 🔄 ETL Flow

```
📁 movies.csv (19,808 rows)
        │
        ▼
┌─────────────────────────────────┐
│         EXTRACT                 │
│  • Read CSV with Pandas         │
│  • Validate required columns    │
│  • Detect encoding & delimiter  │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│         TRANSFORM               │
│  • votes: "1,220" → 1220        │
│  • gross_income: strip commas   │
│  • duration: "175 min" → 175    │
│  • Drop nulls on key columns    │
│  • Fill missing certificates    │
│  • Deduplicate on movie ID      │
│  • Add ETL audit columns        │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│           LOAD                  │
│  • Bulk INSERT via SQLAlchemy   │
│  • fast_executemany=True        │
│  • 500 rows per batch           │
│  • Target: [dbo].[movies]       │
└────────────────┬────────────────┘
                 │
                 ▼
     ✅ Azure SQL Database
```

---

## 📊 Dataset — Column Details

| Column | Raw Type | After Transform | Description |
|---|---|---|---|
| `id` | string | string | IMDb movie ID (e.g. tt0068646) |
| `name` | string | string | Movie title |
| `year` | int | int | Release year |
| `rating` | float | float | IMDb rating (0–10) |
| `certificate` | string | string | Age certificate (filled if null) |
| `duration` | `"175 min"` | `175` (int) | Runtime in minutes |
| `genre` | string | string | Comma-separated genres |
| `votes` | `"1,220,500"` | `1220500` (int) | Number of votes |
| `gross_income` | `"134,966,411"` | `134966411` (int) | Box office gross |
| `directors_name` | string | string | Director name(s) |
| `stars_name` | string | string | Lead actor name(s) |
| `description` | string | string | Plot summary |
| `etl_load_timestamp` | — | datetime | Audit: when loaded |
| `etl_source` | — | string | Audit: pipeline source |

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/azure-etl-pipeline-movies.git
cd azure-etl-pipeline-movies
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install ODBC Driver for Azure SQL
- **Windows:** [Download ODBC Driver 18](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
- **Ubuntu/Debian:**
```bash
sudo apt-get install msodbcsql18
```

### 4. Set Environment Variables
> ⚠️ **Never hardcode credentials.** Always use environment variables.

```bash
# Windows (Command Prompt)
set AZURE_SQL_SERVER=your-server.database.windows.net
set AZURE_SQL_DATABASE=your-database
set AZURE_SQL_USER=your-username
set AZURE_SQL_PASSWORD=your-password

# Linux / macOS
export AZURE_SQL_SERVER=your-server.database.windows.net
export AZURE_SQL_DATABASE=your-database
export AZURE_SQL_USER=your-username
export AZURE_SQL_PASSWORD=your-password
```

---

## ▶️ Run the Pipeline

```bash
cd src
python pipeline.py --csv ../data/movies.csv --config ../config/config.yaml
```

**Expected Output:**
```
2024-01-20 [INFO] AzureETL - ▶ EXTRACT phase started
2024-01-20 [INFO] AzureETL - Extracted 19808 rows from movies.csv
2024-01-20 [INFO] AzureETL - ▶ TRANSFORM phase started
2024-01-20 [INFO] AzureETL - Removed 0 duplicate rows on ['id']
2024-01-20 [INFO] AzureETL - Transform complete — output rows: 19808
2024-01-20 [INFO] AzureETL - ▶ LOAD phase started
2024-01-20 [INFO] AzureETL - Loaded 19808 rows into Azure SQL → movies
2024-01-20 [INFO] AzureETL - ✅ Pipeline complete
```

---

## 🧪 Run Tests

```bash
pip install pytest
pytest tests/ -v
```

**Test Coverage:**
- ✅ CSV extraction and schema validation
- ✅ Votes / gross_income / duration cleaning
- ✅ Null handling and fill values
- ✅ Deduplication on movie ID
- ✅ Audit column injection
- ✅ Full pipeline test on real 19K dataset

---

## 🔧 Configuration (`config/config.yaml`)

```yaml
extract:
  required_cols: [id, name, year, rating]

transform:
  drop_nulls_in: [id, name, rating]
  fill_nulls:
    certificate: "Not Rated"
  deduplicate_on: [id]

load:
  table_name: movies
  if_exists: append      # append | replace | fail
  chunksize: 500
```

---

## 🌐 Environment Variable Reference

| Env Variable | Maps To |
|---|---|
| `AZURE_SQL_SERVER` | `load.server` |
| `AZURE_SQL_DATABASE` | `load.database` |
| `AZURE_SQL_USER` | `load.username` |
| `AZURE_SQL_PASSWORD` | `load.password` |
| `AZURE_SQL_TABLE` | `load.table_name` |

---

## 🛠️ Tech Stack

- **Python 3.10+** — Core language
- **Pandas** — Data extraction and transformation
- **SQLAlchemy 2.0** — ORM and bulk loading engine
- **pyodbc** — ODBC connection to Azure SQL
- **PyYAML** — Config management
- **Pytest** — Unit testing
- **Azure SQL Database** — Cloud destination

---

## 👨‍💻 Author

**Adarsh Tripathi**
B.Tech Data Science | Noida International University



