from database import SessionLocal
import models
from datetime import datetime

def seed_data():
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(models.Machine).first():
            print("Data already exists. Skipping seed.")
            return

        # Add Machines
        machine1 = models.Machine(name="Mitra Grapes 2.0", description="High-efficiency grapes sprayer machine")
        machine2 = models.Machine(name="Mitra Orchard", description="Professional orchard sprayer")
        db.add(machine1)
        db.add(machine2)
        db.commit()
        db.refresh(machine1)
        db.refresh(machine2)

        # Add Models
        model1 = models.MachineModel(model_name="Standard", serial_no="STD-001", machine_id=machine1.id)
        model2 = models.MachineModel(model_name="Deluxe", serial_no="DLX-001", machine_id=machine2.id)
        db.add(model1)
        db.add(model2)
        db.commit()
        db.refresh(model1)
        db.refresh(model2)

        # Add Parts
        parts = [
            models.Part(
                part_name="Engine Valve",
                part_number="EV-001",
                description="High-quality engine valve",
                price="500",
                machine_id=machine1.id,
                machine_model_id=model1.id,
                status="Active"
            ),
            models.Part(
                part_name="Fuel Filter",
                part_number="FF-002",
                description="Original fuel filter",
                price="350",
                machine_id=machine1.id,
                machine_model_id=model1.id,
                status="Active"
            ),
            models.Part(
                part_name="Air Filter",
                part_number="AF-003",
                description="Heavy duty air filter",
                price="450",
                machine_id=machine2.id,
                machine_model_id=model2.id,
                status="Active"
            ),
            models.Part(
                part_name="Spark Plug",
                part_number="SP-004",
                description="Long lasting spark plug",
                price="150",
                machine_id=machine2.id,
                machine_model_id=model2.id,
                status="Active"
            )
        ]
        db.add_all(parts)
        db.commit()

        print("Successfully seeded machines, models, and parts data!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
