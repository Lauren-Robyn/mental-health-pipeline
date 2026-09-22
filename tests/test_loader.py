# tests/test_loader.py
import tempfile
import pandas as pd
from src.db.models import RespondentRecord
from src.db.loader import load_survey_data

def test_load_survey_data_populates_database_and_is_idempotent(db_session):
    """Verifies that load_survey_data cleans and inserts records, and re-running is idempotent."""
    raw_sample = pd.DataFrame([
        {
            "Timestamp": "2014-08-27 11:29:31",
            "Age": 28,
            "Gender": "male",
            "Country": "United States",
            "state": "CA",
            "self_employed": "No",
            "family_history": "No",
            "treatment": "Yes",
            "work_interfere": "Sometimes",
            "no_employees": "26-100",
            "remote_work": "No",
            "tech_company": "Yes",
            "benefits": "Yes",
            "care_options": "Yes",
            "wellness_program": "No",
            "seek_help": "No",
            "anonymity": "Yes",
            "leave": "Don't know",
            "mental_health_consequence": "No",
            "phys_health_consequence": "No",
            "coworkers": "Yes",
            "supervisor": "Yes",
            "mental_health_interview": "No",
            "phys_health_interview": "No",
            "mental_vs_physical": "Yes",
            "obs_consequence": "No",
            "comments": None
        },
        {
            "Timestamp": "2014-08-27 11:29:32",
            "Age": 150,  
            "Gender": "female",
            "Country": "United States",
            "state": "NY",
            "self_employed": "No",
            "family_history": "No",
            "treatment": "No",
            "work_interfere": "Never",
            "no_employees": "1-5",
            "remote_work": "Yes",
            "tech_company": "Yes",
            "benefits": "No",
            "care_options": "No",
            "wellness_program": "No",
            "seek_help": "No",
            "anonymity": "No",
            "leave": "Difficult",
            "mental_health_consequence": "Yes",
            "phys_health_consequence": "No",
            "coworkers": "No",
            "supervisor": "No",
            "mental_health_interview": "No",
            "phys_health_interview": "No",
            "mental_vs_physical": "No",
            "obs_consequence": "Yes",
            "comments": None
        }
    ])

    # Write to a temporary CSV file
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w+", delete=False) as tmp:
        raw_sample.to_csv(tmp.name, index=False)
        tmp_csv_path = tmp.name

    # First execution
    loaded_count = load_survey_data(tmp_csv_path, db_session)
    assert loaded_count == 1

    total_in_db = db_session.query(RespondentRecord).count()
    assert total_in_db == 1

    # Second execution (verifies idempotency: does not duplicate rows)
    loaded_count_again = load_survey_data(tmp_csv_path, db_session)
    assert loaded_count_again == 1
    assert db_session.query(RespondentRecord).count() == 1