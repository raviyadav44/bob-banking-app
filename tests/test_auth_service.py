"""
tests/test_auth_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the authentication service.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "BACKEND"))

from services.auth_service import verify_login


class TestVerifyLogin:
    def test_correct_credentials_return_user(self, db_path):
        # Patch DB_PATH so verify_login uses the temp db.
        import database.db as db_mod
        original = db_mod.DB_PATH
        db_mod.DB_PATH = db_path
        try:
            user = verify_login("demo", "password123", db_path=db_path)
            assert user is not None
            assert "id" in user
            assert user["name"] == "Demo Customer"
        finally:
            db_mod.DB_PATH = original

    def test_wrong_password_returns_none(self, db_path):
        user = verify_login("demo", "wrongpassword", db_path=db_path)
        assert user is None

    def test_nonexistent_username_returns_none(self, db_path):
        user = verify_login("nobody", "password123", db_path=db_path)
        assert user is None

    def test_empty_username_returns_none(self, db_path):
        user = verify_login("", "password123", db_path=db_path)
        assert user is None

    def test_empty_password_returns_none(self, db_path):
        user = verify_login("demo", "", db_path=db_path)
        assert user is None
