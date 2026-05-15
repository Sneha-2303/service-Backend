from database import SessionLocal
import models

db = SessionLocal()

engineers = db.query(models.User).filter(models.User.role == "service_engineer").all()
print("Engineers:")
for e in engineers:
    print(f"ID: {e.id}, Name: {e.full_name}, Username: {e.username}, email: {e.email}")

teams = db.query(models.Team).all()
print("\nTeams:")
for t in teams:
    print(f"ID: {t.id}, Name: {t.name}")
