from datetime import datetime
from database import SessionLocal
import models
import uuid

def seed_test_complaints():
    db = SessionLocal()
    try:
        # Get a customer
        customer = db.query(models.Customer).first()
        if not customer:
            print("No customers found. Please add a customer first.")
            return

        # Get a machine
        machine = db.query(models.Machine).first()
        if not machine:
            print("No machines found. Please add a machine first.")
            return

        # Get a category
        category = db.query(models.ComplaintCategory).first()
        if not category:
            # Create a default category if none exists
            category = models.ComplaintCategory(name="General", description="General issues")
            db.add(category)
            db.flush()

        # Get a subcategory
        subcategory = db.query(models.ComplaintSubCategory).filter(models.ComplaintSubCategory.category_id == category.id).first()
        if not subcategory:
            subcategory = models.ComplaintSubCategory(name="General Issue", category_id=category.id)
            db.add(subcategory)
            db.flush()
        
        # Get an engineer
        engineer = db.query(models.User).filter(models.User.role == "service_engineer").first()

        statuses = ["Hold", "Closed", "Resolved"]
        
        for status in statuses:
            complaint_id = f"TEST-{uuid.uuid4().hex[:6].upper()}"
            new_complaint = models.Complaint(
                complaint_id=complaint_id,
                customer_id=customer.id,
                machine_id=machine.id,
                category_id=category.id,
                subcategory_id=subcategory.id,
                problem_description=f"Automated test complaint for status: {status}",
                status=status,
                assigned_to=engineer.id if engineer else None,
                complaint_date=datetime.now()
            )
            db.add(new_complaint)
            print(f"Created complaint {complaint_id} with status {status}")

        db.commit()
        print("\nSUCCESS: Successfully added 3 test complaints.")
        print("You can now refresh your dashboard to see 'Hold Complaints' and 'Closed Complaints' update.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding test complaints: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_complaints()
