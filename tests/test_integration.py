"""
tests/test_integration.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Integration tests using Flask's test client.  Exercises the full
request/response cycle including routes, session, flash messages, and
the database — all through an in-memory test database.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "BACKEND"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def login(client, username="demo", password="password123"):
    """Perform a POST /login and return the response."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------


class TestLoginRoute:
    def test_get_login_returns_200(self, app_client):
        resp = app_client.get("/login")
        assert resp.status_code == 200
        assert b"Login" in resp.data or b"login" in resp.data.lower()

    def test_correct_login_redirects_to_dashboard(self, app_client):
        resp = login(app_client)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_wrong_password_returns_200_with_error(self, app_client):
        resp = app_client.post(
            "/login",
            data={"username": "demo", "password": "wrong"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid" in resp.data

    def test_wrong_username_returns_200_with_error(self, app_client):
        resp = app_client.post(
            "/login",
            data={"username": "nobody", "password": "password123"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid" in resp.data

    def test_root_redirects_to_login(self, app_client):
        resp = app_client.get("/")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


class TestLogout:
    def test_logout_clears_session_and_redirects(self, app_client):
        login(app_client)
        resp = app_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_dashboard_after_logout_redirects_to_login(self, app_client):
        login(app_client)
        app_client.get("/logout")
        resp = app_client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    def test_unauthenticated_dashboard_redirects(self, app_client):
        resp = app_client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_authenticated_dashboard_returns_200(self, app_client):
        login(app_client)
        resp = app_client.get("/dashboard")
        assert resp.status_code == 200

    def test_dashboard_contains_user_name(self, app_client):
        login(app_client)
        resp = app_client.get("/dashboard")
        assert b"Demo Customer" in resp.data

    def test_dashboard_contains_balance(self, app_client):
        login(app_client)
        resp = app_client.get("/dashboard")
        assert b"1000" in resp.data


# ---------------------------------------------------------------------------
# Deposit
# ---------------------------------------------------------------------------


class TestDeposit:
    def test_valid_deposit_redirects_to_dashboard(self, app_client):
        login(app_client)
        resp = app_client.post(
            "/deposit", data={"amount": "500"}, follow_redirects=False
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_deposit_increases_balance(self, app_client):
        login(app_client)
        app_client.post("/deposit", data={"amount": "500"}, follow_redirects=True)
        resp = app_client.get("/dashboard")
        assert b"1500" in resp.data

    def test_non_numeric_deposit_shows_error(self, app_client):
        login(app_client)
        resp = app_client.post(
            "/deposit", data={"amount": "abc"}, follow_redirects=True
        )
        assert resp.status_code == 200
        assert b"valid number" in resp.data.lower() or b"number" in resp.data.lower()

    def test_zero_deposit_shows_error(self, app_client):
        login(app_client)
        resp = app_client.post(
            "/deposit", data={"amount": "0"}, follow_redirects=True
        )
        assert resp.status_code == 200
        assert b"greater than zero" in resp.data.lower() or b"error" in resp.data.lower()


# ---------------------------------------------------------------------------
# Withdraw
# ---------------------------------------------------------------------------


class TestWithdraw:
    def test_valid_withdrawal_redirects_to_dashboard(self, app_client):
        login(app_client)
        resp = app_client.post(
            "/withdraw", data={"amount": "200"}, follow_redirects=False
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_withdrawal_decreases_balance(self, app_client):
        login(app_client)
        app_client.post("/withdraw", data={"amount": "200"}, follow_redirects=True)
        resp = app_client.get("/dashboard")
        assert b"800" in resp.data

    def test_overdraft_shows_insufficient_funds(self, app_client):
        login(app_client)
        resp = app_client.post(
            "/withdraw", data={"amount": "99999"}, follow_redirects=True
        )
        assert resp.status_code == 200
        assert b"insufficient" in resp.data.lower()

    def test_overdraft_does_not_change_balance(self, app_client):
        login(app_client)
        app_client.post("/withdraw", data={"amount": "99999"}, follow_redirects=True)
        resp = app_client.get("/dashboard")
        assert b"1000" in resp.data

    def test_non_numeric_withdrawal_shows_error(self, app_client):
        login(app_client)
        resp = app_client.post(
            "/withdraw", data={"amount": "xyz"}, follow_redirects=True
        )
        assert resp.status_code == 200
        assert b"valid number" in resp.data.lower() or b"number" in resp.data.lower()
