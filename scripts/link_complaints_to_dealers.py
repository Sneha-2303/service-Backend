from database import SessionLocal
import models
import random

def link_data():
    db = SessionLocal()
    try:
        dealers = db.query(models.Dealer).all()
        complaints = db.query(models.Complaint).all()
        
        if not dealers or not complaints:
            print("No dealers or complaints found.")
            return
            
        for c in complaints:
            # Assign a random dealer to each complaint
            c.dealer_id = random.choice(dealers).id
            
        db.commit()
        print(f"Linked {len(complaints)} complaints to random dealers.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    link_data()
