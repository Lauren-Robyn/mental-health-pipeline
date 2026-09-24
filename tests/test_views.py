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

# --- User Story 3 (Issue 7) ---
def test_view_stigma_index_calculates_weighted_scores_correctly(db_session):
    """
    Verifies v_stigma_index calculates the average stigma score per company size:
    - High stigma respondent (size '6-25'):
        consequence='Yes' (2) + coworkers='No' (2) + supervisor='No' (2) = 6 points
    - Low stigma respondent (size '6-25'):
        consequence='No' (0) + coworkers='Yes' (0) + supervisor='Yes' (0) = 0 points
      Expected average for '6-25' = (6 + 0) / 2 = 3.00

    - Moderate stigma respondent (size '100-500'):
        consequence='Maybe' (1) + coworkers='Some of them' (1) + supervisor='Yes' (0) = 2 points
      Expected average for '100-500' = 2 / 1 = 2.00
    """
    sample_records = [
        # Company size '6-25' - High Stigma (Score = 6)
        {
            "age": 25, "gender": "Male", "country": "United States",
            "treatment": "No", "remote_work": "No", "benefits": "No",
            "care_options": "No", "no_employees": "6-25",
            "mental_health_consequence": "Yes",
            "coworkers": "No",
            "supervisor": "No"
        },
        # Company size '6-25' - Low Stigma (Score = 0)
        {
            "age": 30, "gender": "Female", "country": "United States",
            "treatment": "Yes", "remote_work": "Yes", "benefits": "Yes",
            "care_options": "Yes", "no_employees": "6-25",
            "mental_health_consequence": "No",
            "coworkers": "Yes",
            "supervisor": "Yes"
        },
        # Company size '100-500' - Moderate Stigma (Score = 2)
        {
            "age": 42, "gender": "Other", "country": "Canada",
            "treatment": "Yes", "remote_work": "No", "benefits": "Yes",
            "care_options": "Yes", "no_employees": "100-500",
            "mental_health_consequence": "Maybe",
            "coworkers": "Some of them",
            "supervisor": "Yes"
        }
    ]

    seed_sample_records(db_session, sample_records)
    create_views(db_session.bind)

    query = text("""
        SELECT no_employees, respondent_count, avg_stigma_score
        FROM v_stigma_index
        ORDER BY no_employees
    """)
    rows = db_session.execute(query).fetchall()

    result_map = {r.no_employees: (r.respondent_count, r.avg_stigma_score) for r in rows}

    count_small, avg_small = result_map.get("6-25")
    assert count_small == 2
    assert pytest.approx(avg_small, 0.01) == 3.00

    count_med, avg_med = result_map.get("100-500")
    assert count_med == 1
    assert pytest.approx(avg_med, 0.01) == 2.00

# --- User Story 3 (Issue 7) ---
def test_view_stigma_index_calculates_weighted_scores_correctly(db_session):
    """
    Verifies v_stigma_index calculates the average stigma score per company size:
    - High stigma respondent (size '6-25'):
        consequence='Yes' (2) + coworkers='No' (2) + supervisor='No' (2) = 6 points
    - Low stigma respondent (size '6-25'):
        consequence='No' (0) + coworkers='Yes' (0) + supervisor='Yes' (0) = 0 points
      Expected average for '6-25' = (6 + 0) / 2 = 3.00

    - Moderate stigma respondent (size '100-500'):
        consequence='Maybe' (1) + coworkers='Some of them' (1) + supervisor='Yes' (0) = 2 points
      Expected average for '100-500' = 2 / 1 = 2.00
    """
    sample_records = [
        # Company size '6-25' - High Stigma (Score = 6)
        {
            "age": 25, "gender": "Male", "country": "United States",
            "treatment": "No", "remote_work": "No", "benefits": "No",
            "care_options": "No", "no_employees": "6-25",
            "mental_health_consequence": "Yes",
            "coworkers": "No",
            "supervisor": "No"
        },
        # Company size '6-25' - Low Stigma (Score = 0)
        {
            "age": 30, "gender": "Female", "country": "United States",
            "treatment": "Yes", "remote_work": "Yes", "benefits": "Yes",
            "care_options": "Yes", "no_employees": "6-25",
            "mental_health_consequence": "No",
            "coworkers": "Yes",
            "supervisor": "Yes"
        },
        # Company size '100-500' - Moderate Stigma (Score = 2)
        {
            "age": 42, "gender": "Other", "country": "Canada",
            "treatment": "Yes", "remote_work": "No", "benefits": "Yes",
            "care_options": "Yes", "no_employees": "100-500",
            "mental_health_consequence": "Maybe",
            "coworkers": "Some of them",
            "supervisor": "Yes"
        }
    ]

    seed_sample_records(db_session, sample_records)
    create_views(db_session.bind)

    query = text("""
        SELECT no_employees, respondent_count, avg_stigma_score
        FROM v_stigma_index
        ORDER BY no_employees
    """)
    rows = db_session.execute(query).fetchall()

    result_map = {r.no_employees: (r.respondent_count, r.avg_stigma_score) for r in rows}

    # Verify '6-25' group
    count_small, avg_small = result_map.get("6-25")
    assert count_small == 2
    assert pytest.approx(avg_small, 0.01) == 3.00

    # Verify '100-500' group
    count_med, avg_med = result_map.get("100-500")
    assert count_med == 1
    assert pytest.approx(avg_med, 0.01) == 2.00



# --- User Story 4 (Issue 8) ---
def test_view_support_awareness_calculates_metrics_correctly(db_session):
    """
    Verifies v_support_awareness computes benefit counts and awareness rate:
    - Size '6-25' (2 respondents):
        1 with benefits='Yes', care_options='Yes'
        1 with benefits="Don't know", care_options='No'
      -> total=2, benefits_yes=1, benefits_dont_know=1, care_options_yes=1
      -> awareness_rate = 1 / 2 = 0.5000

    - Size '100-500' (2 respondents):
        2 with benefits='Yes', care_options='Yes'
      -> total=2, benefits_yes=2, benefits_dont_know=0, care_options_yes=2
      -> awareness_rate = 2 / 2 = 1.0000
    """
    sample_records = [
        # Size '6-25'
        {
            "age": 28, "gender": "Female", "country": "United States",
            "treatment": "No", "remote_work": "No",
            "benefits": "Yes", "care_options": "Yes",
            "no_employees": "6-25"
        },
        {
            "age": 34, "gender": "Male", "country": "United States",
            "treatment": "No", "remote_work": "Yes",
            "benefits": "Don't know", "care_options": "No",
            "no_employees": "6-25"
        },
        # Size '100-500'
        {
            "age": 45, "gender": "Male", "country": "United States",
            "treatment": "Yes", "remote_work": "No",
            "benefits": "Yes", "care_options": "Yes",
            "no_employees": "100-500"
        },
        {
            "age": 29, "gender": "Female", "country": "Canada",
            "treatment": "Yes", "remote_work": "No",
            "benefits": "Yes", "care_options": "Yes",
            "no_employees": "100-500"
        }
    ]

    seed_sample_records(db_session, sample_records)
    create_views(db_session.bind)

    query = text("""
        SELECT
            no_employees,
            total_respondents,
            benefits_yes_count,
            benefits_dont_know_count,
            care_options_yes_count,
            awareness_rate
        FROM v_support_awareness
        ORDER BY no_employees
    """)
    rows = db_session.execute(query).fetchall()

    result_map = {r.no_employees: r for r in rows}

    # Verify '6-25'
    r_small = result_map.get("6-25")
    assert r_small.total_respondents == 2
    assert r_small.benefits_yes_count == 1
    assert r_small.benefits_dont_know_count == 1
    assert r_small.care_options_yes_count == 1
    assert pytest.approx(r_small.awareness_rate, 0.0001) == 0.5000

    # Verify '100-500'
    r_med = result_map.get("100-500")
    assert r_med.total_respondents == 2
    assert r_med.benefits_yes_count == 2
    assert r_med.benefits_dont_know_count == 0
    assert r_med.care_options_yes_count == 2
    assert pytest.approx(r_med.awareness_rate, 0.0001) == 1.0000
