import sqlite3
import json
from datetime import datetime

DB_PATH = "bills.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scanned_bills (
        id INTEGER PRIMARY KEY,
        user_id TEXT,
        date_scanned TEXT,
        items TEXT,
        total REAL,
        categories TEXT
    )''')
    conn.commit()
    conn.close()

def save_scan(user_id, items, total, categories):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO scanned_bills VALUES (NULL, ?, ?, ?, ?, ?)', (
        user_id,
        datetime.now().isoformat(),
        json.dumps(items),
        total,
        json.dumps(categories)
    ))
    conn.commit()
    conn.close()

def fetch_user_scans(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM scanned_bills WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows 