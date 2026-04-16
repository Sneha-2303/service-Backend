# backend/test_db.py
from sqlalchemy import create_engine, text

# Test different password options
passwords_to_try = ["1223", "123456", "postgres", ""]

for pwd in passwords_to_try:
    try:
        url = f"postgresql://postgres:{pwd}@localhost:5432/myproject_db"
        print(f"Trying with password: '{pwd}'")
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✓ SUCCESS! Password is: '{pwd}'")
            break
    except Exception as e:
        print(f"✗ Failed with password '{pwd}': {str(e)[:50]}")