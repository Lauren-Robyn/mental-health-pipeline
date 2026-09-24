# run_pipeline.py
import sys
from pathlib import Path
from src.db.session import get_engine, init_db, get_session
from src.db.loader import load_survey_data

def main():
    csv_path = Path("data/raw/survey.csv")
    db_path = "sqlite:///data/survey.db"

    print("========================================")
    print("   Starting Survey Data Pipeline...    ")
    print("========================================")

    if not csv_path.exists():
        print(f"Error: Missing dataset at {csv_path}")
        print("Please place the uncorrupted survey.csv inside data/raw/")
        sys.exit(1)

    # Initialize SQLite Database & Tables
    print("1. Initializing database schema...")
    engine = get_engine(db_path)
    init_db(engine)

    # Execute Data Cleaning & Loading
    print("2. Sanitizing and loading survey records...")
    session = get_session(engine)
    try:
        inserted_count = load_survey_data(str(csv_path), session)
        print(f"Successfully loaded {inserted_count} valid records into respondent_record.")
    except Exception as e:
        session.rollback()
        print(f"Pipeline failed during ingestion: {e}")
        sys.exit(1)
    finally:
        session.close()

    print("========================================")
    print("   Pipeline Execution Complete!         ")
    print("========================================")

if __name__ == "__main__":
    main()