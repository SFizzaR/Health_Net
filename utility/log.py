import sqlite3
from datetime import datetime, timedelta

RETENTION_DAYS = 365  # e.g., delete patient data older than 1 year

conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor()

def log_action(user_id, role, action_type, details=""):
    c.execute("""
        INSERT INTO logs (user_id, role, action, details)
        VALUES (?, ?, ?, ?)
    """, (user_id , role, action_type, details))

    conn.commit()

def clean_old_data():
    try:
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        c.execute("DELETE FROM patients WHERE date_added < ?", (cutoff_date,))
        conn.commit()
        print(f"Deleted patients added before {cutoff_date}")
    except sqlite3.Error as e:
        print(f"Error cleaning old data: {e}")
