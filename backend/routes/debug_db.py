# routes/debug_db.py
from fastapi import APIRouter
import sqlite3
from ..db import DB_PATH

router = APIRouter(prefix="/api/debug", tags=["debug"])

@router.get("/db")
def db_info():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name;")
    rows = cur.fetchall()
    cur.execute("PRAGMA database_list;")
    dblist = cur.fetchall()
    conn.close()
    return {
        "db_path": str(DB_PATH),
        "tables": rows,
        "database_list": dblist
    }
