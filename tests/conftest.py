# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db.models import Base

@pytest.fixture
def db_session():
    """Provides an isolated, in-memory SQLite database session for each test."""
    # Create SQLite in-memory engine
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Generate all tables defined in Base models
    Base.metadata.create_all(engine)
    
    # Bind a session maker to the engine
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Clean up after test finishes
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def valid_payload():
    """Provides a valid dictionary of survey data satisfying all constraints."""
    return {
        "time_stamp": "2014-08-27 11:29:31",
        "age": 30,
        "gender": "Female",
        "country": "United States",
        "state_": "IL",
        "self_employed": "No",
        "family_history": "No",
        "treatment": "Yes",
        "work_interference_level": "Often",
        "no_employees": "6-25",
        "remote_work": "No",
        "tech_company": "Yes",
        "benefits": "Yes",
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
    }