from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = "postgresql://postgres:1223@localhost:5432/myproject_db"
engine = create_engine(DATABASE_URL)

user_id = 4

with engine.connect() as conn:
    query = text("SELECT id, user_id, date, punch_in, punch_out FROM attendances WHERE user_id = :u_id ORDER BY date DESC")
    result = conn.execute(query, {"u_id": user_id})
    records = result.fetchall()
    print(f"Attendance records for user {user_id}:")
    for r in records:
        print(r)
