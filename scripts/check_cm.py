import psycopg2
import os

# Get DB connection string from env or use default
DATABASE_URL = "postgresql://postgres:1223@localhost:5432/myproject_db"

def check_columns():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        table_name = "customer_machines"
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';")
        rows = cur.fetchall()
        
        print(f"Columns in '{table_name}' table:")
        for row in rows:
            print(f"- {row[0]} ({row[1]})")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
