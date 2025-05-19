from flask import Flask, render_template
import sqlite3
from config import DB_PATH
app = Flask(__name__)

@app.route('/')
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM leaks ORDER BY date DESC")
    leaks = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM leaks WHERE is_critical=1")
    critical_count = cursor.fetchone()[0]
    
    conn.close()
    return render_template(
        'dashboard.html',
        leaks=leaks,
        critical_count=critical_count,
        total_count=len(leaks)
    
if __name__ == '__main__':
    app.run(debug=True)
