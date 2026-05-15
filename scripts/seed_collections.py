from database import SessionLocal
import models
from datetime import datetime

def seed_collections():
    db = SessionLocal()
    try:
        # Check if collections already exist
        if db.query(models.Collection).count() > 0:
            print("Collections already seeded.")
            return

        collections_to_add = [
            {
                "complaint_id": 1,
                "labour_charge": 500,
                "local_part_amt": 335,
                "part_amt": 665,
                "total_amt": 1500,
                "root_cause": "Pump blockage"
            },
            {
                "complaint_id": 2,
                "labour_charge": 0,
                "local_part_amt": 0,
                "part_amt": 0,
                "total_amt": 0,
                "root_cause": "Regular maintenance"
            },
            {
                "complaint_id": 3,
                "labour_charge": 1000,
                "local_part_amt": 200,
                "part_amt": 800,
                "total_amt": 2000,
                "root_cause": "Gearbox issue"
            },
            {
                "complaint_id": 4,
                "labour_charge": 300,
                "local_part_amt": 100,
                "part_amt": 0,
                "total_amt": 400,
                "root_cause": "Minor leak"
            },
            {
                "complaint_id": 5,
                "labour_charge": 0,
                "local_part_amt": 1500,
                "part_amt": 500,
                "total_amt": 2000,
                "root_cause": "Part replacement"
            }
        ]

        for col_data in collections_to_add:
            new_col = models.Collection(**col_data)
            db.add(new_col)
        
        db.commit()
        print(f"Successfully seeded {len(collections_to_add)} collections.")
    except Exception as e:
        print(f"Error seeding collections: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_collections()
