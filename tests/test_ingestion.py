# tests/test_ingestion.py
import pytest
import pandas as pd
from src.ingestion.cleaner import (
    clean_age,
    standardize_gender,
    standardize_boolean,
    clean_survey_dataframe
)

# --- 1. Age Boundary Cleaning ---
@pytest.mark.parametrize("input_age, expected_age", [
    (25, 25),
    (18, 18),
    (100, 100),
    (-29, None),   
    (15, None),
    (101, None),   
    (329, None),
    ("invalid", None)
])
def test_clean_age_filters_out_of_range_values(input_age, expected_age):
    """Ages outside 18-100 must be converted to None/NaN."""
    assert clean_age(input_age) == expected_age


# --- 2. Gender Standardization ---
@pytest.mark.parametrize("raw_gender, expected_bucket", [
    ("Male", "Male"),
    ("male", "Male"),
    ("M", "Male"),
    ("m", "Male"),
    ("Cis Male", "Male"),
    ("man", "Male"),
    ("Female", "Female"),
    ("female", "Female"),
    ("F", "Female"),
    ("f", "Female"),
    ("Woman", "Female"),
    ("cis woman", "Female"),
    ("non-binary", "Other"),
    ("Genderqueer", "Other"),
    ("fluid", "Other"),
    (None, "Other"),
    ("p", "Other")
])
def test_standardize_gender_maps_variants_to_controlled_categories(raw_gender, expected_bucket):
    """Maps varied string inputs into 3 controlled buckets: Male, Female, Other."""
    assert standardize_gender(raw_gender) == expected_bucket


# --- 3. Boolean / Yes-No Standardization ---
@pytest.mark.parametrize("raw_val, expected_bool_str", [
    ("Yes", "Yes"),
    ("Y", "Yes"),
    ("1", "Yes"),
    (True, "Yes"),
    ("No", "No"),
    ("N", "No"),
    ("0", "No"),
    (False, "No"),
    (None, "No")
])
def test_standardize_boolean_normalizes_flags(raw_val, expected_bool_str):
    """Normalizes mixed representations of boolean columns to 'Yes' or 'No'."""
    assert standardize_boolean(raw_val) == expected_bool_str


# --- 4. Preserving 'Don't know' in DataFrame Cleaning ---
def test_clean_survey_dataframe_preserves_dont_know_and_drops_bad_ages():
    """Verifies that DataFrame cleaning keeps 'Don't know' and filters invalid ages."""
    raw_data = pd.DataFrame([
        {
            "Timestamp": "2014-08-27 11:29:31",
            "Age": 25,
            "Gender": "male",
            "Country": "United States",
            "state": "IL",
            "self_employed": "No",
            "family_history": "No",
            "treatment": "Yes",
            "work_interfere": "Often",
            "no_employees": "6-25",
            "remote_work": "1",
            "tech_company": "Yes",
            "benefits": "Don't know",      # Must be preserved!
            "care_options": "Not sure",
            "wellness_program": "No",
            "seek_help": "Don't know",
            "anonymity": "Yes",
            "leave": "Somewhat easy",
            "mental_health_consequence": "No",
            "phys_health_consequence": "No",
            "coworkers": "Some of them",
            "supervisor": "Yes",
            "mental_health_interview": "No",
            "phys_health_interview": "Maybe",
            "mental_vs_physical": "Don't know",
            "obs_consequence": "No",
            "comments": None
        },
        {
            "Timestamp": "2014-08-27 11:29:32",
            "Age": -29,                    # Invalid age -> row should be dropped or cleaned
            "Gender": "cis woman",
            "Country": "Canada",
            "state": None,
            "self_employed": "No",
            "family_history": "No",
            "treatment": "No",
            "work_interfere": None,
            "no_employees": "1-5",
            "remote_work": "No",
            "tech_company": "Yes",
            "benefits": "No",
            "care_options": "No",
            "wellness_program": "No",
            "seek_help": "No",
            "anonymity": "Don't know",
            "leave": "Don't know",
            "mental_health_consequence": "Maybe",
            "phys_health_consequence": "No",
            "coworkers": "No",
            "supervisor": "No",
            "mental_health_interview": "No",
            "phys_health_interview": "No",
            "mental_vs_physical": "No",
            "obs_consequence": "No",
            "comments": None
        }
    ])

    cleaned_df = clean_survey_dataframe(raw_data)

    # 1. Invalid age row (-29) must be filtered out so the DB constraint never crashes
    assert len(cleaned_df) == 1
    assert cleaned_df.iloc[0]["age"] == 25
    assert cleaned_df.iloc[0]["gender"] == "Male"
    assert cleaned_df.iloc[0]["remote_work"] == "Yes"
    
    # 2. 'Don't know' must NOT be turned into null/NaN
    assert cleaned_df.iloc[0]["benefits"] == "Don't know"