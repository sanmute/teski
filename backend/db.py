# app/backend/db.py
from __future__ import annotations
from sqlmodel import SQLModel, create_engine, Session
import sqlite3
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

def _has_fts5(conn: sqlite3.Connection) -> bool:
    try:
        cur = conn.cursor()
        # Fast path: check compile options
        cur.execute("PRAGMA compile_options;")
        opts = [row[0].upper() for row in cur.fetchall()]
        if any("FTS5" in o for o in opts):
            return True
        # Slow path: try a throwaway virtual table
        cur.execute("DROP TABLE IF EXISTS __fts5_probe;")
        cur.execute("CREATE VIRTUAL TABLE __fts5_probe USING fts5(x);")
        cur.execute("DROP TABLE __fts5_probe;")
        return True
    except Exception:
        return False

def _ensure_task_columns(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(task);")
    cols = {row[1] for row in cur.fetchall()}
    alters = []
    if "link" not in cols:
        alters.append("ALTER TABLE task ADD COLUMN link TEXT")
    if "signals_json" not in cols:
        alters.append("ALTER TABLE task ADD COLUMN signals_json TEXT")
    if "task_type" not in cols:
        alters.append("ALTER TABLE task ADD COLUMN task_type TEXT")
    if "estimated_minutes" not in cols:
        alters.append("ALTER TABLE task ADD COLUMN estimated_minutes INTEGER")
    if "suggested_start_utc" not in cols:
        alters.append("ALTER TABLE task ADD COLUMN suggested_start_utc TEXT")
    if "completed_at" not in cols:
        alters.append("ALTER TABLE task ADD COLUMN completed_at TEXT")
    for stmt in alters:
        cur.execute(stmt)
    if alters:
        conn.commit()


def _ensure_help_library_tables(conn: sqlite3.Connection) -> str:
    """Create FTS-backed or fallback tables. Returns 'fts5' or 'fallback'."""
    cur = conn.cursor()
    if _has_fts5(conn):
        # FTS5 index + metadata table
        cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS docs
        USING fts5(
          url UNINDEXED,      -- unique doc URL
          title,              -- page title
          text,               -- extracted main text
          domain,             -- e.g., ocw.mit.edu
          topic,              -- our canonical topic tag
          created_at UNINDEXED,
          tokenize='porter'
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
          url TEXT PRIMARY KEY,
          domain TEXT,
          topic TEXT,
          fetched_at TEXT,
          etag TEXT,
          last_modified TEXT,
          status INTEGER
        );
        """)
        conn.commit()
        return "fts5"
    else:
        # Fallback: normal table + a few indices (not as fast, but works)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS docs_fallback (
          url TEXT PRIMARY KEY,
          title TEXT,
          text TEXT,
          domain TEXT,
          topic TEXT,
          created_at TEXT
        );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_docs_fb_topic ON docs_fallback(topic);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_docs_fb_domain ON docs_fallback(domain);")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
          url TEXT PRIMARY KEY,
          domain TEXT,
          topic TEXT,
          fetched_at TEXT,
          etag TEXT,
          last_modified TEXT,
          status INTEGER
        );
        """)
        conn.commit()
        return "fallback"

def init_db():
    print(f"[DB] init_db() starting", file=sys.stderr)
    print(f"[DB] SQLite file: {DB_PATH}", file=sys.stderr)

    # 1) ORM tables
    try:
        from .models import Task, Reminder
        from .models_studypack import StudyPack
        from .models_integrations import MoodleFeed
        from .models_leaderboard import Leaderboard, LeaderboardMember, PointsEvent, WeeklyScore
        from .models_push import PushSubscription
        SQLModel.metadata.create_all(engine)
        print("[DB] ORM tables ensured (Task, Reminder, StudyPack)", file=sys.stderr)
    except Exception as e:
        print(f"[DB] ERROR creating ORM tables: {e}", file=sys.stderr)
        raise

    # 2) Help Library tables (FTS or fallback)
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("select sqlite_version();")
        print(f"[DB] sqlite_version: {cur.fetchone()[0]}", file=sys.stderr)
        _ensure_task_columns(conn)

        mode = _ensure_help_library_tables(conn)
        print(f"[DB] Help Library tables ensured (mode={mode})", file=sys.stderr)
    except Exception as e:
        print(f"[DB] ERROR creating Help Library tables: {e}", file=sys.stderr)
        raise
    finally:
        try: conn.close()
        except: pass

def get_session():
    with Session(engine) as session:
        yield session
