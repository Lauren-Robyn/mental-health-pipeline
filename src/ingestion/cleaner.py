# src/ingestion/cleaner.py
import pandas as pd

# Standard controlled buckets for gender
MALE_VARIANTS = {
    "male", "m", "male-ish", "maile", "mal", "male (cis)", "make", "male ",
    "man", "msle", "mail", "malr", "cis man", "cis male"
}

FEMALE_VARIANTS = {
    "female", "cis female", "f", "woman", "femake", "female ", "cis-female/femme",
    "female (cis)", "femail"
}

def clean_age(val):
    """
    Validates age is within 18 and 100.
    Returns integer age or None if invalid/corrupt.
    """
    try:
        age = int(val)
        if 18 <= age <= 100:
            return age
        return None
    except (ValueError, TypeError):
        return None

def standardize_gender(val):
    """
    Maps free-text gender inputs to 'Male', 'Female', or 'Other'.
    """
    if not val or pd.isna(val):
        return "Other"
    
    cleaned = str(val).strip().lower()
    if cleaned in MALE_VARIANTS:
        return "Male"
    elif cleaned in FEMALE_VARIANTS:
        return "Female"
    else:
        return "Other"

def standardize_boolean(val):
    """
    Maps diverse truthy/falsy inputs to clean 'Yes' or 'No'.
    """
    if pd.isna(val) or val is None:
        return "No"
    
    cleaned = str(val).strip().lower()
    if cleaned in {"yes", "y", "1", "true"}:
        return "Yes"
    elif cleaned in {"no", "n", "0", "false"}:
        return "No"
    return "No"

def clean_survey_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a raw OSMI DataFrame, cleans columns, aligns names with DB models,
    and drops rows with fatal errors (like invalid ages).
    """
    df = df.copy()

    # Standardize column names to lowercase snake_case
    df.columns = [c.strip().lower() for c in df.columns]

    # Map raw CSV column names to our DB model column names
    column_mapping = {
        "timestamp": "time_stamp",
        "state": "state_",
        "work_interfere": "work_interference_level"
    }
    df.rename(columns=column_mapping, inplace=True)

    # Sanitize Age and drop rows that violate our 18-100 boundary rule
    df["age"] = df["age"].apply(clean_age)
    df = df.dropna(subset=["age"]).copy()
    df["age"] = df["age"].astype(int)

    # Standardize Gender
    df["gender"] = df["gender"].apply(standardize_gender)

    # Standardize Boolean columns
    bool_cols = ["treatment", "remote_work"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].apply(standardize_boolean)

    # Fill empty comments with empty string or None (safe for DB)
    if "comments" in df.columns:
        df["comments"] = df["comments"].where(pd.notna(df["comments"]), None)

    return df