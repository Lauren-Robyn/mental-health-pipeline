# tests/test_models.py
import pytest
from sqlalchemy.exc import IntegrityError
from src.db.models import RespondentRecord

def test_insert_valid_record_succeeds(db_session, valid_payload):
    """Verifies that a record meeting all constraints persists cleanly."""
    record = RespondentRecord(**valid_payload)
    db_session.add(record)
    db_session.commit()

    # Query back the persisted row
    queried = db_session.query(RespondentRecord).first()
    assert queried is not None
    assert queried.id == 1
    assert queried.age == 30
    assert queried.gender == "Female"

@pytest.mark.parametrize("invalid_age", [-29, 0, 17, 101, 329, 999])
def test_orm_model_rejects_age_outside_valid_range(db_session, valid_payload, invalid_age):
    """Verifies CHECK constraint rejects any age outside 18-100 upon commit."""
    bad_payload = valid_payload.copy()
    bad_payload["age"] = invalid_age

    record = RespondentRecord(**bad_payload)
    db_session.add(record)

    with pytest.raises(IntegrityError):
        db_session.commit()

@pytest.mark.parametrize("valid_boundary_age", [18, 100])
def test_orm_model_accepts_boundary_ages(db_session, valid_payload, valid_boundary_age):
    """Verifies boundary edge cases (18 and 100) are permitted by the constraint."""
    payload = valid_payload.copy()
    payload["age"] = valid_boundary_age

    record = RespondentRecord(**payload)
    db_session.add(record)
    db_session.commit()

    assert record.id is not None
    assert record.age == valid_boundary_age