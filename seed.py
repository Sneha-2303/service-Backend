from database import engine
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("INSERT INTO states (id, name) VALUES (1, 'Maharashtra') ON CONFLICT (id) DO NOTHING;"))
    conn.execute(text("INSERT INTO districts (id, name, state_id) VALUES (1, 'Nashik', 1) ON CONFLICT (id) DO NOTHING;"))
    conn.execute(text("INSERT INTO talukas (id, name, district_id) VALUES (1, 'Sinnar', 1) ON CONFLICT (id) DO NOTHING;"))
    
    print("Seed data inserted successfully.")
