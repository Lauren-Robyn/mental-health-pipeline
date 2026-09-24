from sqlalchemy import text
from src.db.session import get_engine

VIEWS = [
    "v_treatment_rate",
    "v_work_interference",
    "v_stigma_index",
    "v_support_awareness",
    "v_openness_comparison",
]


def preview_views():
    engine = get_engine()

    with engine.connect() as conn:
        for view_name in VIEWS:
            print(f"\n{'=' * 25} {view_name} {'=' * 25}")
            result = conn.execute(text(f"SELECT * FROM {view_name} LIMIT 5"))
            columns = list(result.keys())
            rows = result.fetchall()

            if not rows:
                print("  (No rows returned)")
                continue

            header_str = " | ".join(f"{col:<25}" for col in columns)
            print(header_str)
            print("-" * len(header_str))

            for row in rows:
                row_str = " | ".join(f"{str(val):<25}" for val in row)
                print(row_str)


if __name__ == "__main__":
    preview_views()
