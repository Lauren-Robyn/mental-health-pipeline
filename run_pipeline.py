from pathlib import Path
from src.db.session import get_engine, init_db, get_session
from src.db.loader import load_survey_data
from src.db.views import create_views

RAW_DATA_PATH = Path(__file__).resolve().parent / "data" / "raw" / "survey.csv"


def main():
    print("1. Creating database engine...")
    engine = get_engine()

    print("2. Initializing database schema...")
    init_db(engine)

    print(f"3. Cleaning and loading survey records from {RAW_DATA_PATH}...")
    session = get_session(engine)
    try:
        inserted_count = load_survey_data(RAW_DATA_PATH, session)
        print(f"   -> Successfully processed/loaded records: {inserted_count}")
    finally:
        session.close()

    print("4. Executing analytical view DDL scripts in db/views/...")
    create_views(engine)
    print("   -> All analytical views successfully registered.")

    print("\nPipeline execution complete!")


if __name__ == "__main__":
    main()