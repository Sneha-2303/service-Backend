from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = "postgresql://postgres:1223@localhost:5432/myproject_db"
engine = create_engine(DATABASE_URL)

today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

with engine.connect() as conn:
    query = text("SELECT a.id, a.user_id, u.username, a.date, a.punch_in FROM attendances a JOIN users u ON a.user_id = u.id WHERE a.date >= :t_start")
    result = conn.execute(query, {"t_start": today_start})
    records = result.fetchall()
    print(f"All attendance records for today ({today_start.date()}):")
    if not records:
        print("No records found for today.")
    for r in records:
        print(r)
