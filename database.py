import sqlite3
import os
from config import DB_PATH

def init_db():
    """Initialize database with proper schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaks (
                id INTEGER PRIMARY KEY,
                source TEXT,
                data TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_critical INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        print("[SUCCESS] Database initialized")
        return conn, cursor
    except Exception as e:
        print(f"[ERROR] Database init failed: {e}")
        raise

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
