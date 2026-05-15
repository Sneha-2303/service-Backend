from sqlalchemy import text
from database import engine

def alter_talukas():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE talukas ADD COLUMN IF NOT EXISTS code TEXT;"))
            conn.execute(text("ALTER TABLE talukas ADD COLUMN IF NOT EXISTS pincode TEXT;"))
            conn.execute(text("ALTER TABLE talukas ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';"))
            conn.execute(text("ALTER TABLE talukas ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
            print("Successfully altered talukas table.")
        except Exception as e:
            print(f"Error altering talukas table: {e}")

if __name__ == "__main__":
    alter_talukas()
