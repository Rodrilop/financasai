import sqlite3
import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

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
            logger.warning("libsql-experimental not installed. Falling back to local SQLite.")

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _column_exists(conn, table: str, column: str) -> bool:
    """Check if a column exists in a table using PRAGMA table_info."""
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == column for r in rows)
    except Exception as e:
        logger.error(f"Error checking column {column} in {table}: {e}")
        return False

def _migrate(conn):
    """
    Safely add user_id column to existing tables.
    Uses PRAGMA table_info to check column existence before ALTER TABLE,
    avoiding silent failures from the try/except approach.
    """
    tables = ["settings", "income", "expenses"]
    for table in tables:
        if not _column_exists(conn, table, "user_id"):
            logger.info(f"Migrating table '{table}': adding user_id column")
            try:
                # Use DEFAULT 1 without NOT NULL — safer for libsql ALTER TABLE
                conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER DEFAULT 1")
                conn.commit()
                logger.info(f"  -> user_id column added to '{table}' successfully")
            except Exception as e:
                logger.error(f"  -> Failed to add user_id to '{table}': {e}")
        else:
            logger.info(f"Table '{table}' already has user_id column — skipping")

def get_schema_info():
    """Return schema info for diagnostics endpoint."""
    conn = get_connection()
    result = {}
    for table in ["users", "settings", "income", "expenses"]:
        try:
            cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
            count_row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            count = count_row[0] if count_row else 0
            result[table] = {
                "columns": [r["name"] for r in cols],
                "row_count": count,
            }
        except Exception as e:
            result[table] = {"error": str(e)}
    conn.close()
    return result

def init_db():
    """Initialize the database by creating all required tables."""
    conn = get_connection()
    c = conn.cursor()

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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
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
            user_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Run migration (adds user_id to pre-existing tables)
    _migrate(conn)
    conn.close()

def ensure_user_settings(user_id: int):
    """Create a default settings row for a user if one doesn't exist."""
    if user_id is None:
        logger.error("ensure_user_settings called with user_id=None — skipping")
        return
    conn = get_connection()
    row = conn.execute("SELECT id FROM settings WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        month = datetime.now().strftime("%Y-%m")
        conn.execute(
            """INSERT INTO settings
               (user_id, salary, reference_month, emergency_reserve_goal,
                investment_pct, investor_profile, budget_essential_pct,
                budget_important_pct, budget_optional_pct)
               VALUES (?,0,?,0,20,'moderado',50,30,20)""",
            (user_id, month)
        )
        conn.commit()
        logger.info(f"Created default settings for user_id={user_id}")
    conn.close()
