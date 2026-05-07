import sqlite3
import os
import logging
import json
import requests as _requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "financasai.db"
TURSO_DB_URL   = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")


# ─────────────────────────────────────────────────────────
#  Turso HTTP Client (no Rust/native libs needed)
# ─────────────────────────────────────────────────────────

class TursoRow:
    """Dict-like row from Turso HTTP response."""
    def __init__(self, columns, values):
        self._columns = columns
        self._values  = values

    def keys(self):
        return self._columns

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._values[self._columns.index(key)]

    def __iter__(self):
        return iter(zip(self._columns, self._values))

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return str(dict(zip(self._columns, self._values)))


class TursoResult:
    """Fake cursor result from a Turso HTTP query."""
    def __init__(self, columns, rows, last_insert_rowid=None, rows_affected=0):
        self._columns = columns
        self._rows    = [TursoRow(columns, r) for r in rows]
        self.lastrowid      = last_insert_rowid
        self.rows_affected  = rows_affected
        self.description    = [(c, None, None, None, None, None, None) for c in columns]

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows

    def fetchmany(self, size=1):
        return self._rows[:size]


class TursoConnection:
    """HTTP-based Turso connection that mimics the sqlite3 interface."""

    def __init__(self, url: str, token: str):
        # Turso HTTP endpoint: https://<db-name>.turso.io/v2/pipeline
        base = url.replace("libsql://", "https://")
        self._endpoint = f"{base}/v2/pipeline"
        self._headers  = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        }
        self._stmts: list = []   # batched statements before commit()
        self._autocommit = True  # will switch to False on first write

    # ── Core execute ──────────────────────────────────────
    def _http_execute(self, statements: list) -> list:
        """POST a pipeline of SQL statements to Turso."""
        payload = {
            "requests": [
                {"type": "execute", "stmt": {"sql": s["sql"], "args": [
                    self._to_arg(v) for v in s.get("args", [])
                ]}}
                for s in statements
            ] + [{"type": "close"}]
        }
        resp = _requests.post(self._endpoint, json=payload, headers=self._headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("results", []):
            if item.get("type") == "error":
                raise Exception(f"Turso error: {item.get('error', {}).get('message', 'unknown')}")
            if item.get("type") == "ok":
                response = item.get("response", {})
                if response.get("type") != "execute":
                    continue  # skip "close" responses
                res = response.get("result", {})
                cols = [c["name"] for c in res.get("cols", [])]
                # Each row is a list of {"type": ..., "value": ...} objects
                rows = [
                    [self._from_value(cell) for cell in row]
                    for row in res.get("rows", [])
                ]
                last_id = res.get("last_insert_rowid")
                results.append(TursoResult(
                    cols, rows,
                    last_insert_rowid=int(last_id) if last_id else None
                ))
        return results

    @staticmethod
    def _to_arg(v):
        if v is None:   return {"type": "null"}
        if isinstance(v, bool): return {"type": "integer", "value": str(int(v))}
        if isinstance(v, int):  return {"type": "integer", "value": str(v)}
        if isinstance(v, float): return {"type": "float",  "value": v}
        return {"type": "text", "value": str(v)}

    @staticmethod
    def _from_value(v):
        t = v.get("type")
        val = v.get("value")
        if t == "null":    return None
        if t == "integer": return int(val)
        if t == "float":   return float(val)
        return val  # text / blob

    def execute(self, sql: str, params=()):
        results = self._http_execute([{"sql": sql, "args": list(params)}])
        return results[0] if results else TursoResult([], [])

    def executemany(self, sql: str, params_list: list):
        """Execute multiple statements in a single pipeline."""
        if not params_list: return
        stmts = [{"sql": sql, "args": list(p)} for p in params_list]
        return self._http_execute(stmts)

    def cursor(self):
        return self

    def commit(self):
        if self._stmts:
            self._http_execute(self._stmts)
            self._stmts = []

    def close(self):
        pass  # HTTP is stateless


# ─────────────────────────────────────────────────────────
#  get_connection — Turso HTTP or local SQLite fallback
# ─────────────────────────────────────────────────────────

def get_connection():
    """Return a Turso HTTP connection, or local SQLite as fallback."""
    if TURSO_DB_URL and TURSO_AUTH_TOKEN:
        try:
            conn = TursoConnection(TURSO_DB_URL, TURSO_AUTH_TOKEN)
            # Quick ping
            conn.execute("SELECT 1")
            logger.debug("Turso HTTP connection established.")
            return conn
        except Exception as e:
            logger.warning(f"Turso connection failed, falling back to SQLite: {e}")

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ─────────────────────────────────────────────────────────
#  Schema helpers
# ─────────────────────────────────────────────────────────

def _column_exists(conn, table: str, column: str) -> bool:
    try:
        # Try to select the column with LIMIT 0. If it fails, column doesn't exist.
        conn.execute(f"SELECT {column} FROM {table} LIMIT 0")
        return True
    except Exception:
        return False


def _table_exists(conn, table: str) -> bool:
    try:
        result = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        ).fetchone()
        return (result[0] if result else 0) > 0
    except Exception as e:
        logger.error(f"_table_exists({table}): {e}")
        return False


def _migrate(conn):
    """Run safe schema migrations (add columns if missing)."""
    tables = ["settings", "income", "expenses", "portfolio", "notifications"]
    for table in tables:
        if _table_exists(conn, table) and not _column_exists(conn, table, "user_id"):
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER DEFAULT 1")
                conn.commit()
                logger.info(f"Migrated '{table}': added user_id")
            except Exception as e:
                logger.error(f"Migration user_id on '{table}': {e}")

    if _table_exists(conn, "income") and not _column_exists(conn, "income", "date"):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            conn.execute(f"ALTER TABLE income ADD COLUMN date TEXT DEFAULT '{today}'")
            conn.commit()
            logger.info("Migrated 'income': added date")
        except Exception as e:
            logger.error(f"Migration date on 'income': {e}")

    if _table_exists(conn, "users") and not _column_exists(conn, "users", "phone"):
        try:
            conn.execute("ALTER TABLE users ADD COLUMN phone TEXT DEFAULT NULL")
            conn.commit()
            logger.info("Migrated 'users': added phone")
        except Exception as e:
            logger.error(f"Migration phone on 'users': {e}")

    if _table_exists(conn, "users") and not _column_exists(conn, "users", "is_pro"):
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_pro INTEGER DEFAULT 0")
            conn.commit()
            logger.info("Migrated 'users': added is_pro column")
        except Exception as e:
            logger.error(f"Migration is_pro on 'users': {e}")

    # Multi-account migrations
    for table in ["income", "expenses"]:
        if _table_exists(conn, table) and not _column_exists(conn, table, "account"):
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN account TEXT DEFAULT 'Geral'")
                conn.commit()
                logger.info(f"Migrated '{table}': added account column")
            except Exception as e:
                logger.error(f"Migration account on '{table}': {e}")


# ─────────────────────────────────────────────────────────
#  init_db
# ─────────────────────────────────────────────────────────

def init_db():
    """Create all tables (idempotent) and run migrations."""
    conn = get_connection()

    ddl_statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            phone TEXT DEFAULT NULL,
            is_pro INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS settings (
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
        )""",
        """CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'Conta Corrente',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            account TEXT DEFAULT 'Geral',
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            account TEXT DEFAULT 'Geral',
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            quantity REAL NOT NULL,
            average_price REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",
    ]

    for stmt in ddl_statements:
        try:
            conn.execute(stmt)
            conn.commit()
        except Exception as e:
            logger.error(f"init_db DDL error: {e}")

    _migrate(conn)
    conn.close()
    logger.info("init_db complete.")


# ─────────────────────────────────────────────────────────
#  ensure_user_settings
# ─────────────────────────────────────────────────────────

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
