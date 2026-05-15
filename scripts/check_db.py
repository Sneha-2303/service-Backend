import sqlite3
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute("SELECT id, full_name, role FROM users WHERE role='service_engineer';")
print("Engineers:", cursor.fetchall())
cursor.execute("SELECT id, name FROM teams;")
print("Teams:", cursor.fetchall())
