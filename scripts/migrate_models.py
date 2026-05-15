import psycopg2

DATABASE_URL = "postgresql://postgres:1223@localhost:5432/myproject_db"

def migrate_machine_models():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if serial_no column exists
        cur.execute("""
            SELECT count(*) 
            FROM information_schema.columns 
            WHERE table_name='machine_models' AND column_name='serial_no';
        """)
        exists = cur.fetchone()[0]
        
        if not exists:
            print("Adding 'serial_no' column to 'machine_models'...")
            cur.execute("ALTER TABLE machine_models ADD COLUMN serial_no VARCHAR;")
            print("Column added successfully.")
        else:
            print("'serial_no' column already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate_machine_models()
