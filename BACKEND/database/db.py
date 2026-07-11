"""
database/db.py
~~~~~~~~~~~~~~
Low-level database helpers. All other modules must use these functions
instead of importing sqlite3 directly.
"""

import os
import sqlite3

from werkzeug.security import generate_password_hash

# Absolute path to the SQLite file so the app can be launched from any CWD.
_DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_DB_DIR, "bank.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open and return a SQLite connection with row_factory set to Row
    so that columns are accessible by name (e.g. row['balance'])."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Create tables if they do not exist and seed a demo account if the
    users table is empty. Safe to call on every application startup."""
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()

        # --- users table ---
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL,
                name     TEXT    NOT NULL,
                balance  REAL    NOT NULL DEFAULT 0.0
            )
            """
        )

        # --- transactions table ---
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id         INTEGER  PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER  NOT NULL REFERENCES users(id),
                type       TEXT     NOT NULL,
                amount     REAL     NOT NULL,
                created_at DATETIME NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

        # --- seed demo account if table is empty ---
        row = cur.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        if row["cnt"] == 0:
            cur.execute(
                "INSERT INTO users (username, password, name, balance) VALUES (?, ?, ?, ?)",
                (
                    "demo",
                    generate_password_hash("password123"),
                    "Demo Customer",
                    1000.00,
                ),
            )

        conn.commit()
    finally:
        conn.close()
