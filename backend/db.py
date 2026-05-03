"""
db.py — SQLite database setup and helpers
"""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_URL", "postnow.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables on startup."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email       TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS brand_profiles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER UNIQUE NOT NULL REFERENCES users(id),
                shop_name   TEXT NOT NULL,
                aesthetic   TEXT NOT NULL,   -- Cozy | Bold | Minimalist
                colors      TEXT NOT NULL,   -- JSON array e.g. ["#F5A623","#FFFFFF"]
                updated_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS generations (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                prompt        TEXT NOT NULL,
                template_id   TEXT,
                en_caption    TEXT,
                kh_caption    TEXT,
                hashtags      TEXT,
                image_url     TEXT,
                created_at    TEXT DEFAULT (datetime('now'))
            );
        """)
    print("✅  Database initialised")
