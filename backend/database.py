import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "financasai.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            salary REAL DEFAULT 0,
            reference_month TEXT DEFAULT '',
            emergency_reserve_goal REAL DEFAULT 0,
            investment_pct REAL DEFAULT 20,
            investor_profile TEXT DEFAULT 'moderado',
            budget_essential_pct REAL DEFAULT 50,
            budget_important_pct REAL DEFAULT 30,
            budget_optional_pct REAL DEFAULT 20
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("SELECT COUNT(*) FROM settings")
    if c.fetchone()[0] == 0:
        month = datetime.now().strftime("%Y-%m")
        c.execute(
            "INSERT INTO settings (id,salary,reference_month,emergency_reserve_goal,investment_pct,investor_profile,budget_essential_pct,budget_important_pct,budget_optional_pct) VALUES (1,0,?,0,20,'moderado',50,30,20)",
            (month,)
        )
    conn.commit()
    conn.close()
