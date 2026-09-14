"""
database.py

Minimal SQLite persistence layer. Each analyzed resume gets a row so
the (optional) history/dashboard views have something real to read
from instead of only in-memory state.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "resume_analyzer.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            candidate_name TEXT,
            profile_role TEXT,
            ats_score INTEGER,
            result_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_analysis(result):
    conn = get_connection()
    conn.execute(
        "INSERT INTO analyses (created_at, candidate_name, profile_role, ats_score, result_json) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            datetime.now(timezone.utc).isoformat(),
            result.get("contact", {}).get("name"),
            result.get("profile_role"),
            result.get("ats_score"),
            json.dumps(result),
        ),
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.close()
    return row_id


def get_recent_analyses(limit=10):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, created_at, candidate_name, profile_role, ats_score "
        "FROM analyses ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
