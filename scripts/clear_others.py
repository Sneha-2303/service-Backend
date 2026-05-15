from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:1223@localhost:5432/myproject_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Delete all attendance records except for user_id 4
    query = text("DELETE FROM attendances WHERE user_id != 4")
    result = conn.execute(query)
    conn.commit()
    print(f"Deleted {result.rowcount} attendance records for all users except user 4.")
