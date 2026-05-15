from database import SessionLocal
import models
from auth import get_password_hash

def seed_engineers():
    db = SessionLocal()
    try:
        # Check if we already have engineers
        if db.query(models.User).filter(models.User.role == "service_engineer").first():
            print("Engineers already exist. Skipping seed.")
            return

        engineers = [
            models.User(
                username="7774068801",
                email="devraj.magar@example.com",
                mobile="7774068801",
                full_name="Devraj Magar",
                hashed_password=get_password_hash("7774068801"),
                role="service_engineer",
                address="Nashik",
                state="Maharashtra",
                district="Nashik",
                taluka="Nashik",
                status="Active"
            ),
            models.User(
                username="8483841722",
                email="rohit.pagare@example.com",
                mobile="8483841722",
                full_name="Rohit Somnath Pagare",
                hashed_password=get_password_hash("8483841722"),
                role="service_engineer",
                address="Satpur, Nashik",
                state="Maharashtra",
                district="Nashik",
                taluka="Nashik",
                status="Active"
            ),
            models.User(
                username="7499397726",
                email="sanket.misal@example.com",
                mobile="7499397726",
                full_name="SANKET MISAL",
                hashed_password=get_password_hash("7499397726"),
                role="service_engineer",
                address="Tupewadi",
                state="Maharashtra",
                district="Chhatrapati Sambhaji Nagar",
                taluka="Pathan",
                status="Active"
            )
        ]
        
        db.add_all(engineers)
        db.commit()
        print(f"Added {len(engineers)} service engineers.")

        # Create a team
        lead = db.query(models.User).filter(models.User.full_name == "Devraj Magar").first()
        if lead:
            team = models.Team(name="Nashik Team", team_lead_id=lead.id)
            db.add(team)
            db.commit()
            db.refresh(team)
            
            # Add members
            for eng in engineers:
                member = models.TeamMember(team_id=team.id, user_id=eng.id)
                db.add(member)
            db.commit()
            print("Created Nashik Team and added members.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding engineers: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_engineers()
