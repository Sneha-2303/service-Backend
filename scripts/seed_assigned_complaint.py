from datetime import datetime
from database import SessionLocal
import models
import uuid

def seed_assigned_complaint():
    db = SessionLocal()
    try:
        # Get a customer
        customer = db.query(models.Customer).first()
        # Get a machine
        machine = db.query(models.Machine).first()
        # Get a category
        category = db.query(models.ComplaintCategory).first()
        # Get a subcategory
        subcategory = db.query(models.ComplaintSubCategory).filter(models.ComplaintSubCategory.category_id == category.id).first()
        # Get an engineer
        engineer = db.query(models.User).filter(models.User.role == "service_engineer").first()

        if not engineer:
            print("No service engineers found. Creating one...")
            engineer = models.User(
                username="test_eng", 
                email="eng@test.com", 
                mobile="1234567890", 
                full_name="Test Engineer", 
                role="service_engineer",
                hashed_password="hashed"
            )
            db.add(engineer)
            db.flush()

        complaint_id = f"ASSIGN-{uuid.uuid4().hex[:6].upper()}"
        new_complaint = models.Complaint(
            complaint_id=complaint_id,
            customer_id=customer.id,
            machine_id=machine.id,
            category_id=category.id,
            subcategory_id=subcategory.id,
            problem_description="Test complaint for Assigned status",
            status="Assigned",
            assigned_to=engineer.id,
            complaint_date=datetime.now()
        )
        db.add(new_complaint)
        db.commit()
        print(f"\nSUCCESS: Created complaint {complaint_id} and assigned it to {engineer.full_name}.")
        print("You can now refresh your dashboard to see 'Assigned to Engineer' update.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_assigned_complaint()
