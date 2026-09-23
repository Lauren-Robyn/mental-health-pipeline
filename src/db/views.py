# src/db/views.py
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.engine import Engine

VIEWS_DIR = Path(__file__).resolve().parent.parent.parent / "db" / "views"


def create_views(engine: Engine) -> None:
    """Reads and executes all .sql view definitions against the database engine."""
    if not VIEWS_DIR.exists():
        return

    with engine.connect() as conn:
        for sql_file in sorted(VIEWS_DIR.glob("*.sql")):
            with open(sql_file, "r", encoding="utf-8") as f:
                ddl = f.read().strip()
            if ddl:
                conn.execute(text(ddl))
        conn.commit()