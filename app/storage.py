from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import sqlite3

from app.config import DB_PATH


def timestamp():
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(timespec="seconds")


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH, timeout=10) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = sqlite3.Row
        yield db


def initialize():
    with connection() as db:
        db.execute("CREATE TABLE IF NOT EXISTS complaints (number INTEGER PRIMARY KEY AUTOINCREMENT, body TEXT NOT NULL)")


def all_records():
    with connection() as db:
        rows = db.execute("SELECT body FROM complaints ORDER BY number DESC").fetchall()
    return [json.loads(row["body"]) for row in rows]


def get_record(record_id):
    try:
        number = int(record_id.removeprefix("CMP-"))
    except ValueError:
        return None
    with connection() as db:
        row = db.execute("SELECT body FROM complaints WHERE number=?", (number,)).fetchone()
    return json.loads(row["body"]) if row else None


def insert(record):
    value = {**record, "created_at": record.get("created_at", timestamp())}
    with connection() as db:
        cursor = db.execute("INSERT INTO complaints(body) VALUES (?)", ("{}",))
        value["id"] = f"CMP-{cursor.lastrowid:04d}"
        db.execute("UPDATE complaints SET body=? WHERE number=?", (json.dumps(value), cursor.lastrowid))
    return value


def update(record_id, updates):
    # Read and write in the same transaction so a status change and completed
    # LLM explanation cannot overwrite one another with a stale JSON snapshot.
    number = int(record_id.removeprefix("CMP-"))
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT body FROM complaints WHERE number=?", (number,)).fetchone()
        if not row:
            return None
        value = json.loads(row["body"])
        value.update(updates)
        db.execute("UPDATE complaints SET body=? WHERE number=?", (json.dumps(value), number))
    return value
