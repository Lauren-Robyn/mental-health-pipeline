# src/db/loader.py
import os
import pandas as pd
from sqlalchemy.orm import Session
from src.db.models import RespondentRecord
from src.ingestion.cleaner import clean_survey_dataframe

def load_survey_data(csv_path: str, session: Session) -> int:
    """
    Reads a raw survey CSV, sanitizes it using clean_survey_dataframe,
    clears previous records to ensure idempotency, and loads rows via ORM.
    Returns the count of successfully loaded rows.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Raw data file not found at: {csv_path}")

    # Read raw CSV
    raw_df = pd.read_csv(csv_path)

    # Sanitize using our tested cleaning pipeline
    cleaned_df = clean_survey_dataframe(raw_df)

    # Ensure idempotency: clear existing records before reloading
    session.query(RespondentRecord).delete()

    # Map cleaned DataFrame rows into ORM Model instances
    # Convert DataFrame records to dictionaries, replacing float NaNs with None
    records_to_insert = []
    for row in cleaned_df.to_dict(orient="records"):
        sanitized_row = {
            k: (None if pd.isna(v) else v)
            for k, v in row.items()
        }
        records_to_insert.append(RespondentRecord(**sanitized_row))

    # Bulk commit via session
    session.bulk_save_objects(records_to_insert)
    session.commit()

    return len(records_to_insert)