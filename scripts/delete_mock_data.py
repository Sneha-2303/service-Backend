from database import SessionLocal
import models

db = SessionLocal()

# Find the mock users
mock_usernames = ["7774068801", "8483841722", "7499397726"]
mock_users = db.query(models.User).filter(models.User.username.in_(mock_usernames)).all()

for user in mock_users:
    # Find any teams where this user is the lead
    teams = db.query(models.Team).filter(models.Team.team_lead_id == user.id).all()
    for team in teams:
        # Delete team members first
        db.query(models.TeamMember).filter(models.TeamMember.team_id == team.id).delete()
        # Delete the team
        db.delete(team)
    
    # Delete team member entries for this user
    db.query(models.TeamMember).filter(models.TeamMember.user_id == user.id).delete()
    
    # Delete the user
    db.delete(user)

db.commit()
print("Successfully removed mock data from the database.")
