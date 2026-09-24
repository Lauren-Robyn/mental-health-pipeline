import pytest 
from sqlalchemy import text 
from src.db.models import RespondentRecord
from src.db.views import create_views

def seed_sample_records(session, records):
    """Helper to insert survey records into the test database."""
    for r in records:
        record = RespondentRecord(**r)
        session.add(record)
    session.commit()


def test_view_treatment_rate_returns_correct_ratio(db_session):
    """
    Verifies that v_treatment_rate accurately calculates treatment ratios:
    - Remote ('Yes'): 2 respondents, 1 seeking treatment = 0.5000 (50%)
    - On-site ('No'): 2 respondents, 2 seeking treatment = 1.0000 (100%)
    """
    sample_records = [
        # Remote workers
        {
            "age": 28,
            "gender": "Female",
            "country": "United States",
            "treatment": "Yes",
            "remote_work": "Yes",
            "benefits": "Yes",
            "care_options": "Yes",
            "no_employees": "6-25",
        },
        {
            "age": 32,
            "gender": "Male",
            "country": "United States",
            "treatment": "No",
            "remote_work": "Yes",
            "benefits": "No",
            "care_options": "No",
            "no_employees": "26-100",
        },
        # On-site workers
        {
            "age": 45,
            "gender": "Male",
            "country": "United States",
            "treatment": "Yes",
            "remote_work": "No",
            "benefits": "Yes",
            "care_options": "Yes",
            "no_employees": "100-500",
        },
        {
            "age": 22,
            "gender": "Female",
            "country": "United States",
            "treatment": "Yes",
            "remote_work": "No",
            "benefits": "Yes",
            "care_options": "Not sure",
            "no_employees": "1-5",
        },
    ]

    seed_sample_records(db_session, sample_records)

    # Attempt to register view on test database
    create_views(db_session.bind)

    # Query the view
    result = db_session.execute(
        text(
            "SELECT remote_work, total_respondents, treatment_seeking_count, treatment_rate "
            "FROM v_treatment_rate ORDER BY remote_work DESC"
        )
    ).fetchall()

    # Remote ('Yes')
    remote_row = result[0]
    assert remote_row.remote_work == "Yes"
    assert remote_row.total_respondents == 2
    assert remote_row.treatment_seeking_count == 1
    assert pytest.approx(remote_row.treatment_rate, 0.001) == 0.5

    # On-site ('No')
    onsite_row = result[1]
    assert onsite_row.remote_work == "No"
    assert onsite_row.total_respondents == 2
    assert onsite_row.treatment_seeking_count == 2
    assert pytest.approx(onsite_row.treatment_rate, 0.001) == 1.0


def test_view_treatment_rate_returns_zero_on_empty_segment(db_session):
    """
    Confirms the SQL view safely returns 0 rows rather than raising
    a divide-by-zero database error when the table has no records.
    """
    create_views(db_session.bind)

    # Query empty view
    result = db_session.execute(
        text("SELECT * FROM v_treatment_rate")
    ).fetchall()
    assert len(result) == 0

def test_view_work_interference_aggregates_include_null_bucket(db_session):
    """
    Verifies v_work_interference aggregates interference counts by company size
    and converts NULL work interference into 'Unspecified' rather than dropping rows.
    """
    sample_records = [
        # Company size '6-25'
        {
            "age": 29, "gender": "Female", "country": "United States",
            "treatment": "Yes", "remote_work": "No", "benefits": "Yes",
            "care_options": "Yes", "no_employees": "6-25",
            "work_interference_level": "Often"
        },
        {
            "age": 31, "gender": "Male", "country": "United States",
            "treatment": "No", "remote_work": "Yes", "benefits": "No",
            "care_options": "No", "no_employees": "6-25",
            "work_interference_level": "Often"
        },
        {
            "age": 35, "gender": "Male", "country": "United States",
            "treatment": "No", "remote_work": "No", "benefits": "No",
            "care_options": "No", "no_employees": "6-25",
            "work_interference_level": None  # Missing: must become 'Unspecified'
        },
        # Company size '100-500'
        {
            "age": 40, "gender": "Female", "country": "United States",
            "treatment": "Yes", "remote_work": "Yes", "benefits": "Yes",
            "care_options": "Yes", "no_employees": "100-500",
            "work_interference_level": "Sometimes"
        }
    ]

    seed_sample_records(db_session, sample_records)

    # Register all views (including the yet-to-be-created v_work_interference)
    create_views(db_session.bind)

    # Query the new view
    query = text("""
        SELECT no_employees, work_interference_level, response_count
        FROM v_work_interference
        ORDER BY no_employees, work_interference_level
    """)
    rows = db_session.execute(query).fetchall()

    result_map = {(r.no_employees, r.work_interference_level): r.response_count for r in rows}

    # Verify counts for '6-25'
    assert result_map.get(("6-25", "Often")) == 2
    assert result_map.get(("6-25", "Unspecified")) == 1

    # Verify count for '100-500'
    assert result_map.get(("100-500", "Sometimes")) == 1