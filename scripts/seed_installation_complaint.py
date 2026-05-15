from datetime import datetime
from database import SessionLocal
import models
import uuid

def seed_installation_complaint():
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

        complaint_id = f"INST-{uuid.uuid4().hex[:6].upper()}"
        new_complaint = models.Complaint(
            complaint_id=complaint_id,
            customer_id=customer.id,
            machine_id=machine.id,
            category_id=category.id,
            subcategory_id=subcategory.id,
            problem_description="Test complaint for Need Installation status",
            status="Need Installation",
            complaint_date=datetime.now()
        )
        db.add(new_complaint)
        db.commit()
        print(f"\nSUCCESS: Created complaint {complaint_id} with status 'Need Installation'.")
        print("You can now refresh your dashboard to see 'Need Installation' update.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_installation_complaint()
