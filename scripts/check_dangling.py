from database import SessionLocal
import models

db = SessionLocal()

print("Checking for dangling TeamMember records...")
members = db.query(models.TeamMember).all()
for m in members:
    user = db.query(models.User).filter(models.User.id == m.user_id).first()
    if not user:
        print(f"Dangling member found: ID {m.id}, user_id {m.user_id}")
    team = db.query(models.Team).filter(models.Team.id == m.team_id).first()
    if not team:
        print(f"Dangling member found: ID {m.id}, team_id {m.team_id}")

print("Checking for dangling Team leads...")
teams = db.query(models.Team).all()
for t in teams:
    lead = db.query(models.User).filter(models.User.id == t.team_lead_id).first()
    if not lead:
        print(f"Dangling lead found: Team ID {t.id}, lead_id {t.team_lead_id}")

db.close()
