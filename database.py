from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:1223@localhost:5432/myproject_db"

engine = create_engine(
    DATABASE_URL,
    echo=True  # enable logs for debugging
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test connection
try:
    with engine.connect() as conn:
        print("Database connected successfully")
except Exception as e:
    print(f"Database connection failed: {e}")