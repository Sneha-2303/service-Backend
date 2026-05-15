from sqlalchemy import text
from database import engine

def alter_tables():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE machines ADD COLUMN IF NOT EXISTS photo TEXT;"))
            conn.execute(text("ALTER TABLE parts ADD COLUMN IF NOT EXISTS photo TEXT;"))
            print("Successfully added 'photo' column to machines and parts tables.")
        except Exception as e:
            print(f"Error altering tables: {e}")

if __name__ == "__main__":
    alter_tables()
