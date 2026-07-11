"""
services/auth_service.py
~~~~~~~~~~~~~~~~~~~~~~~~
Authentication helpers: verifying credentials and protecting routes.
"""

import functools
from typing import Optional
from flask import session, redirect, url_for
from werkzeug.security import check_password_hash

import sys
import os

# Allow imports from the BACKEND root when running tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import get_connection


def verify_login(username: str, password: str, db_path: str = None) -> Optional[dict]:
    """Return the user row dict on success, or None on failure.

    Never reveal whether the username or password was the invalid field.
    """
    kwargs = {"db_path": db_path} if db_path else {}
    from database.db import DB_PATH
    path = db_path or DB_PATH
    conn = get_connection(path)
    try:
        row = conn.execute(
            "SELECT id, name, password FROM users WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    if not check_password_hash(row["password"], password):
        return None

    return {"id": row["id"], "name": row["name"]}


def login_required(view_func):
    """Decorator that redirects unauthenticated requests to /login."""

    @functools.wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped
