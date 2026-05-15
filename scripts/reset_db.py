from database import engine, Base
import models
from sqlalchemy import text

print("Dropping all tables with CASCADE...")
with engine.connect() as conn:
    # Disable foreign key checks temporarily
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.commit()
    print("All tables dropped successfully")

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("All tables created successfully")

print("Database reset complete!")