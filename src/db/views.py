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
                content = f.read() 

                statements = content.split(";")
                for stmt in statements: 
                    clean_stmt = stmt.strip()
                    if clean_stmt: 
                        conn.execute(text(clean_stmt))

        conn.commit()

