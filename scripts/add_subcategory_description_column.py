from sqlalchemy import text
from database import engine

def alter_tables():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE complaint_subcategories ADD COLUMN IF NOT EXISTS description VARCHAR;"))
            print("Successfully added 'description' column to complaint_subcategories table.")
        except Exception as e:
            print(f"Error altering tables: {e}")

if __name__ == "__main__":
    alter_tables()
