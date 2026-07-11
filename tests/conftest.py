"""
tests/conftest.py
~~~~~~~~~~~~~~~~~
Shared pytest fixtures.

All tests use an in-memory SQLite database so that the real bank.db is
never touched and every test run starts from a clean, seeded state.
"""

import os
import sys

import pytest

# Make BACKEND importable from the tests/ directory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "BACKEND"))

from database.db import init_db, DB_PATH


@pytest.fixture
def db_path(tmp_path):
    """Return the path to a fresh, seeded in-memory-like SQLite file in a
    temporary directory.  Using a file (rather than ':memory:') allows
    multiple connections from service functions without extra threading care."""
    path = str(tmp_path / "test_bank.db")
    init_db(db_path=path)
    return path


@pytest.fixture
def app_client(db_path):
    """Return a Flask test client wired to the temporary database."""
    import importlib, types

    # Patch DB_PATH in every service module so the test db is used.
    import database.db as db_module
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = db_path

    import services.account_service as acct_mod
    import services.auth_service as auth_mod
    acct_mod.DB_PATH = db_path
    auth_mod  # no DB_PATH attribute needed — uses keyword arg

    # Create a fresh Flask app pointing at the test db.
    import app as app_module
    app_module.app.config["TESTING"] = True
    app_module.app.config["SECRET_KEY"] = "test-secret"
    # Re-initialise DB so app uses test path.
    db_module.init_db(db_path)

    # Monkey-patch service calls in app to use test db_path
    # via a simple wrapper approach — override module-level DB_PATH.
    with app_module.app.test_client() as client:
        yield client

    # Restore
    db_module.DB_PATH = original_db_path
    acct_mod.DB_PATH = original_db_path
