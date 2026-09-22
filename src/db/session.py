from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 
from src.db.models import Base 

def get_engine(db_url: str = "sqlite:///data/survey.db"):
    """Creates a SQLAlchemy engine for SQLite."""
    return create_engine(db_url, echo=False)

def init_db(engine):
    """Generates all tables defined in Base models if they do not exist."""
    Base.metadata.create_all(engine)

def get_session(engine):
    """Provides a database session for transactions."""
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()