import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "financasai.db"
TURSO_DB_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

class CustomRow:
    def __init__(self, cursor, row):
        self._row = row
        self._keys = [col[0] for col in cursor.description] if cursor.description else []
    def keys(self):
        return self._keys
    def __getitem__(self, key):
        if isinstance(key, int): return self._row[key]
        return self._row[self._keys.index(key)]
    def __iter__(self): return iter(self._row)
    def __len__(self): return len(self._row)

class LibsqlCursorProxy:
    def __init__(self, cursor, row_factory):
        self._cursor = cursor
        self.row_factory = row_factory
    def execute(self, *args, **kwargs):
        self._cursor.execute(*args, **kwargs)
        return self
    def fetchone(self):
        row = self._cursor.fetchone()
        return self.row_factory(self, row) if row and self.row_factory else row
    def fetchall(self):
        rows = self._cursor.fetchall()
        return [self.row_factory(self, row) for row in rows] if rows and self.row_factory else rows
    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany() if size is None else self._cursor.fetchmany(size)
        return [self.row_factory(self, row) for row in rows] if rows and self.row_factory else rows
    @property
    def description(self): return self._cursor.description
    @property
    def lastrowid(self): return getattr(self._cursor, 'lastrowid', None)

class LibsqlConnectionProxy:
    def __init__(self, conn):
        self._conn = conn
        self.row_factory = None
    def cursor(self):
        return LibsqlCursorProxy(self._conn.cursor(), self.row_factory)
    def execute(self, *args, **kwargs):
        cursor = self.cursor()
        return cursor.execute(*args, **kwargs)
    def commit(self): self._conn.commit()
    def close(self): self._conn.close()

def get_connection():
    """Establish and return a connection to the Turso or local SQLite database."""
    if TURSO_DB_URL:
        try:
            import libsql_experimental as libsql
            conn = libsql.connect(TURSO_DB_URL, auth_token=TURSO_AUTH_TOKEN)
            proxy = LibsqlConnectionProxy(conn)
            proxy.row_factory = CustomRow
            return proxy
        except ImportError:
            print("libsql-experimental is not installed. Falling back to local SQLite.")
            
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    """Initialize the database by creating all required tables and default settings."""
    conn = get_connection()
    c = conn.cursor()
    
    # Tabela de Usuários (Auth)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
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

