# tests/test_views.py
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


# --- User Story 1 (Issue 5: Treatment Rate) ---
def test_view_treatment_rate_returns_correct_ratio(db_session):
    sample_records = [
        {"age": 28, "gender": "Female", "country": "United States", "treatment": "Yes", "remote_work": "Yes", "benefits": "Yes", "care_options": "Yes", "no_employees": "6-25"},
        {"age": 32, "gender": "Male", "country": "United States", "treatment": "No", "remote_work": "Yes", "benefits": "No", "care_options": "No", "no_employees": "26-100"},
        {"age": 45, "gender": "Male", "country": "United States", "treatment": "Yes", "remote_work": "No", "benefits": "Yes", "care_options": "Yes", "no_employees": "100-500"},
        {"age": 22, "gender": "Female", "country": "United States", "treatment": "Yes", "remote_work": "No", "benefits": "Yes", "care_options": "Not sure", "no_employees": "1-5"},
    ]
    seed_sample_records(db_session, sample_records)
    create_views(db_session.bind)

    result = db_session.execute(
        text("SELECT remote_work, total_respondents, treatment_seeking_count, treatment_rate FROM v_treatment_rate ORDER BY remote_work DESC")
    ).fetchall()

    remote_row = result[0]
    assert remote_row.remote_work == "Yes"
    assert remote_row.total_respondents == 2
    assert remote_row.treatment_seeking_count == 1
    assert pytest.approx(remote_row.treatment_rate, 0.001) == 0.5

    onsite_row = result[1]
    assert onsite_row.remote_work == "No"
    assert onsite_row.total_respondents == 2
    assert onsite_row.treatment_seeking_count == 2
    assert pytest.approx(onsite_row.treatment_rate, 0.001) == 1.0


def test_view_treatment_rate_returns_zero_on_empty_segment(db_session):
    create_views(db_session.bind)
    result = db_session.execute(text("SELECT * FROM v_treatment_rate")).fetchall()
    assert len(result) == 0


# --- User Story 2 (Issue 6: Work Interference) ---
def test_view_work_interference_aggregates_include_null_bucket(db_session):
    sample_records = [
        {"age": 29, "gender": "Female", "country": "United States", "treatment": "Yes", "remote_work": "No", "benefits": "Yes", "care_options": "Yes", "no_employees": "6-25", "work_interference_level": "Often"},
        {"age": 31, "gender": "Male", "country": "United States", "treatment": "No", "remote_work": "Yes", "benefits": "No", "care_options": "No", "no_employees": "6-25", "work_interference_level": "Often"},
        {"age": 35, "gender": "Male", "country": "United States", "treatment": "No", "remote_work": "No", "benefits": "No", "care_options": "No", "no_employees": "6-25", "work_interference_level": None},
        {"age": 40, "gender": "Female", "country": "United States", "treatment": "Yes", "remote_work": "Yes", "benefits": "Yes", "care_options": "Yes", "no_employees": "100-500", "work_interference_level": "Sometimes"},
    ]
    seed_sample_records(db_session, sample_records)
    create_views(db_session.bind)

    query = text("SELECT no_employees, work_interference_level, response_count FROM v_work_interference ORDER BY no_employees, work_interference_level")
    rows = db_session.execute(query).fetchall()
    result_map = {(r.no_employees, r.work_interference_level): r.response_count for r in rows}

    assert result_map.get(("6-25", "Often")) == 2
    assert result_map.get(("6-25", "Unspecified")) == 1
    assert result_map.get(("100-500", "Sometimes")) == 1


# --- User Story 3 (Issue 7: Stigma Index) ---
def test_view_stigma_index_calculates_weighted_scores_correctly(db_session):
    sample_records = [
        {"age": 25, "gender": "Male", "country": "United States", "treatment": "No", "remote_work": "No", "benefits": "No", "care_options": "No", "no_employees": "6-25", "mental_health_consequence": "Yes", "coworkers": "No", "supervisor": "No"},
        {"age": 30, "gender": "Female", "country": "United States", "treatment": "Yes", "remote_work": "Yes", "benefits": "Yes", "care_options": "Yes", "no_employees": "6-25", "mental_health_consequence": "No", "coworkers": "Yes", "supervisor": "Yes"},
        {"age": 42, "gender": "Other", "country": "Canada", "treatment": "Yes", "remote_work": "No", "benefits": "Yes", "care_options": "Yes", "no_employees": "100-500", "mental_health_consequence": "Maybe", "coworkers": "Some of them", "supervisor": "Yes"},
    ]
    seed_sample_records(db_session, sample_records)
    create_views(db_session.bind)

    query = text("SELECT no_employees, respondent_count, avg_stigma_score FROM v_stigma_index ORDER BY no_employees")
    rows = db_session.execute(query).fetchall()
    result_map = {r.no_employees: (r.respondent_count, r.avg_stigma_score) for r in rows}

    count_small, avg_small = result_map.get("6-25")
    assert count_small == 2
    assert pytest.approx(avg_small, 0.01) == 3.00

    count_med, avg_med = result_map.get("100-500")
    assert count_med == 1
    assert pytest.approx(avg_med, 0.01) == 2.00


# --- User Story 4 (Issue 8: Support Awareness) ---
def test_view_support_awareness_calculates_metrics_correctly(db_session):
    sample_records = [
        {"age": 28, "gender": "Female", "country": "United States", "treatment": "No", "remote_work": "No", "benefits": "Yes", "care_options": "Yes", "no_employees": "6-25"},
        {"age": 34, "gender": "Male", "country": "United States", "treatment": "No", "remote_work": "Yes", "benefits": "Don't know", "care_options": "No", "no_employees": "6-25"},
        {"age": 45, "gender": "Male", "country": "United States", "treatment": "Yes", "remote_work": "No", "benefits": "Yes", "care_options": "Yes", "no_employees": "100-500"},
        {"age": 29, "gender": "Female", "country": "Canada", "treatment": "Yes", "remote_work": "No", "benefits": "Yes", "care_options": "Yes", "no_employees": "100-500"},
    ]
    seed_sample_records(db_session, sample_records)
    create_views(db_session.bind)

    query = text("SELECT no_employees, total_respondents, benefits_yes_count, benefits_dont_know_count, care_options_yes_count, awareness_rate FROM v_support_awareness ORDER BY no_employees")
    rows = db_session.execute(query).fetchall()
    result_map = {r.no_employees: r for r in rows}

    r_small = result_map.get("6-25")
    assert r_small.total_respondents == 2
    assert r_small.benefits_yes_count == 1
    assert r_small.benefits_dont_know_count == 1
    assert r_small.care_options_yes_count == 1
    assert pytest.approx(r_small.awareness_rate, 0.0001) == 0.5000

    r_med = result_map.get("100-500")
    assert r_med.total_respondents == 2
    assert r_med.benefits_yes_count == 2
    assert r_med.benefits_dont_know_count == 0
    assert r_med.care_options_yes_count == 2
    assert pytest.approx(r_med.awareness_rate, 0.0001) == 1.0000


# --- User Story 5 (Issue 9: Openness Comparison) ---
def test_view_openness_comparison_calculates_rates_and_gap_correctly(db_session):
    sample_records = [
        {"age": 30, "gender": "Female", "country": "United States", "treatment": "Yes", "remote_work": "Yes", "benefits": "Yes", "care_options": "Yes", "mental_health_consequence": "Yes", "phys_health_consequence": "No", "no_employees": "26-100"},
        {"age": 35, "gender": "Male", "country": "United States", "treatment": "No", "remote_work": "Yes", "benefits": "Yes", "care_options": "Yes", "mental_health_consequence": "Yes", "phys_health_consequence": "Yes", "no_employees": "26-100"},
        {"age": 28, "gender": "Male", "country": "United States", "treatment": "No", "remote_work": "No", "benefits": "Yes", "care_options": "Yes", "mental_health_consequence": "No", "phys_health_consequence": "No", "no_employees": "1-5"},
        {"age": 40, "gender": "Female", "country": "United States", "treatment": "Yes", "remote_work": "No", "benefits": "Yes", "care_options": "Yes", "mental_health_consequence": "Yes", "phys_health_consequence": "Yes", "no_employees": "1-5"},
    ]
    seed_sample_records(db_session, sample_records)
    create_views(db_session.bind)

    query = text("""
        SELECT
            remote_work,
            total_respondents,
            mental_consequence_yes_count,
            physical_consequence_yes_count,
            mental_consequence_rate,
            physical_consequence_rate,
            consequence_gap
        FROM v_openness_comparison
        ORDER BY remote_work DESC
    """)
    rows = db_session.execute(query).fetchall()
    result_map = {r.remote_work: r for r in rows}

    remote_row = result_map.get("Yes")
    assert remote_row.total_respondents == 2
    assert remote_row.mental_consequence_yes_count == 2
    assert remote_row.physical_consequence_yes_count == 1
    assert pytest.approx(remote_row.mental_consequence_rate, 0.0001) == 1.0000
    assert pytest.approx(remote_row.physical_consequence_rate, 0.0001) == 0.5000
    assert pytest.approx(remote_row.consequence_gap, 0.0001) == 0.5000

    onsite_row = result_map.get("No")
    assert onsite_row.total_respondents == 2
    assert onsite_row.mental_consequence_yes_count == 1
    assert onsite_row.physical_consequence_yes_count == 1
    assert pytest.approx(onsite_row.mental_consequence_rate, 0.0001) == 0.5000
    assert pytest.approx(onsite_row.physical_consequence_rate, 0.0001) == 0.5000
    assert pytest.approx(onsite_row.consequence_gap, 0.0001) == 0.0000