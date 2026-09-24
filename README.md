# Mental Health in Tech Data Pipeline

An end-to-end ELT data engineering pipeline that ingests, cleans, validates, and models workplace mental health survey data using Python, SQLAlchemy, SQLite, and analytical SQL views. Built adhering to Test-Driven Development (TDD) practices with automated GitHub Actions CI.

---

## Architecture Overview
                  +-----------------------------+
                  |   data/raw/survey.csv       |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   Ingestion & Cleaning      |
                  |   (src/ingestion/cleaner.py)|
                  | - Range validation (18-100) |
                  | - Gender 3-way bucket       |
                  | - Boolean normalization     |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   Relational Persistence    |
                  |   (src/db/loader.py)        |
                  | - SQLAlchemy ORM Models     |
                  | - Idempotent Batch Loading  |
                  | - Check Constraints         |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   Analytical SQL Views      |
                  |   (db/views/*.sql)          |
                  | - v_treatment_rate          |
                  | - v_work_interference       |
                  | - v_stigma_index            |
                  | - v_support_awareness       |
                  | - v_openness_comparison     |
                  +-----------------------------+

---

## Analytical Views & User Stories

The pipeline computes 5 analytical SQL views designed for People Operations and leadership analytics:

| View Name | Business Metric / Goal | Grouping / Aggregation Key |
| :--- | :--- | :--- |
| **`v_treatment_rate`** | Computes the proportion of respondents who sought mental health care. | Grouped by `remote_work`. Defensive float division with `NULLIF`. |
| **`v_work_interference`** | Evaluates how mental health impacts day-to-day work, mapping missing values to `'Unspecified'`. | Grouped by `no_employees` and `work_interference_level`. |
| **`v_stigma_index`** | Calculates a composite workplace stigma score (0–6) based on fear of employer consequence and reluctance to discuss with coworkers/supervisors. | Grouped by `no_employees`, calculating `avg_stigma_score`. |
| **`v_support_awareness`** | Tracks awareness and knowledge of employer-provided benefits and care programs. | Grouped by `no_employees`, calculating `awareness_rate`. |
| **`v_openness_comparison`** | Evaluates perceived consequences of disclosing mental health versus physical health issues. | Grouped by `remote_work`, calculating `consequence_gap`. |

---

## Directory Structure

```text
              mental-health-pipeline/
              ├── .github/
              │   └── workflows/
              │       └── ci.yml               # GitHub Actions CI workflow
              ├── data/
              │   ├── raw/
              │   │   └── survey.csv           # Raw OSMI survey dataset
              │   └── survey.db                # SQLite database (generated)
              ├── db/
              │   └── views/
              │       ├── v_openness_comparison.sql
              │       ├── v_stigma_index.sql
              │       ├── v_support_awareness.sql
              │       ├── v_treatment_rate.sql
              │       └── v_work_interference.sql
              ├── src/
              │   ├── db/
              │   │   ├── loader.py            # Data loading & idempotency logic
              │   │   ├── models.py            # SQLAlchemy declarative models & table constraints
              │   │   ├── session.py           # Database engine & session management
              │   │   └── views.py             # View registration DDL execution runner
              │   └── ingestion/
              │       └── cleaner.py           # Data cleaning & normalization functions
              ├── tests/
              │   ├── conftest.py              # In-memory test session fixture
              │   ├── test_ingestion.py        # Ingestion & cleaning test suite
              │   ├── test_loader.py           # Database loading & idempotency tests
              │   ├── test_models.py           # ORM models and schema constraint tests
              │   ├── test_schema.py           # Database schema tests
              │   ├── test_smoke.py            # Environment health check
              │   └── test_views.py            # Analytical SQL view verification suite
              ├── requirements.txt             # Python dependencies
              ├── run_pipeline.py              # Orchestration entry point
              └── README.md
              
```
## Getting Started
### Prerequisites
- Python 3.11+
- Git

## Installation
### Clone the repository:
git clone [https://github.com/lauren-robyn/mental-health-pipeline.git](https://github.com/lauren-robyn/mental-health-pipeline.git)
cd mental-health-pipeline

### Create and activate a virtual environment:
```
python3 -m venv .venv
source .venv/bin/activate
```
### Install dependencies:
```
pip install --upgrade pip
pip install -r requirements.txt
```
---
## Execution Guide
### 1. Running the Pipeline
Run the main orchestration script to initialize tables, clean raw records, load data, and compile all views:
```
python run_pipeline.py
```
Expected terminal output:

```
1. Creating database engine...
2. Initializing database schema...
3. Cleaning and loading survey records from .../data/raw/survey.csv...
   -> Successfully processed/loaded records: 1251
4. Executing analytical view DDL scripts in db/views/...
   -> All analytical views successfully registered.

Pipeline execution complete!
```
## 2. Inspecting View Data
To query and inspect the aggregated output tables directly from SQLite:
```
python -c "
from sqlalchemy import text
from src.db.session import get_engine

views = [
    'v_treatment_rate',
    'v_work_interference',
    'v_stigma_index',
    'v_support_awareness',
    'v_openness_comparison'
]

with get_engine().connect() as conn:
    for view in views:
        print(f'\n=== {view} ===')
        res = conn.execute(text(f'SELECT * FROM {view}'))
        print(' | '.join(res.keys()))
        for row in res.fetchall():
            print(row)
"
```

## Testing
The project maintains 53 automated unit and integration tests across data ingestion, database constraints, loader operations, and SQL views.

Run the test suite with pytest:
```
python -m pytest -v
```
Run view-specific tests:
```
python -m pytest tests/test_views.py -v
```
## Continuous Integration (CI)
Automated testing is configured via `.github/workflows/ci.yml.` On every push or pull request to the `main` branch, GitHub Actions:

1. Provisions a Python environment.

2. Installs dependencies from requirements.txt.

3. Runs the test suite via 'pytest' to prevent regressions.
EOF





