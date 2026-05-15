from database import SessionLocal
import models

def seed_checksheets():
    db = SessionLocal()
    try:
        if db.query(models.CheckSheet).count() > 0:
            print("Checksheets already seeded.")
            return
            
        # 1. Pre-Delivery Inspection
        cs1 = models.CheckSheet(
            title="PRE-DELIVERY INSPECTION (PDI)",
            description="Inspection to be performed before the machine leaves the warehouse.",
            status="Active"
        )
        db.add(cs1)
        db.flush()
        
        # Sections for PDI
        s1 = models.CheckSheetSection(name="Physical Condition", checksheet_id=cs1.id)
        db.add(s1)
        db.flush()
        db.add(models.CheckSheetItem(description="Check for paint scratches or dents", is_required=True, section_id=s1.id))
        db.add(models.CheckSheetItem(description="Verify all decals and labels are present", is_required=True, section_id=s1.id))
        
        s2 = models.CheckSheetSection(name="Fluid Levels", checksheet_id=cs1.id)
        db.add(s2)
        db.flush()
        db.add(models.CheckSheetItem(description="Engine oil level check", is_required=True, section_id=s2.id))
        db.add(models.CheckSheetItem(description="Hydraulic oil level check", is_required=True, section_id=s2.id))
        db.add(models.CheckSheetItem(description="Coolant level check", is_required=True, section_id=s2.id))

        # 2. Installation Checklist
        cs2 = models.CheckSheet(
            title="INSTALLATION & COMMISSIONING",
            description="Checklist for onsite installation and customer handover.",
            status="Active"
        )
        db.add(cs2)
        db.flush()
        
        s3 = models.CheckSheetSection(name="Site Preparation", checksheet_id=cs2.id)
        db.add(s3)
        db.flush()
        db.add(models.CheckSheetItem(description="Verify floor leveling", is_required=True, section_id=s3.id))
        db.add(models.CheckSheetItem(description="Check power supply voltage", is_required=True, section_id=s3.id))
        
        s4 = models.CheckSheetSection(name="Training", checksheet_id=cs2.id)
        db.add(s4)
        db.flush()
        db.add(models.CheckSheetItem(description="Operational training given to operator", is_required=True, section_id=s4.id))
        db.add(models.CheckSheetItem(description="Safety protocols explained", is_required=True, section_id=s4.id))

        db.commit()
        print("Checksheets seeded successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_checksheets()
