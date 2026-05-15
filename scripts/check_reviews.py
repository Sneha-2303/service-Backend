from database import SessionLocal
import models

db = SessionLocal()
try:
    reviews = db.query(models.Review).all()
    print(f"Found {len(reviews)} reviews.")
    for r in reviews:
        print(f"ID: {r.id}, Rating: {r.rating}, Text: {r.review_text}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
