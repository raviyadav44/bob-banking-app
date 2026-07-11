"""
tests/test_account_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the account service layer.  All tests use a temporary
SQLite database via the `db_path` fixture so they never touch bank.db.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "BACKEND"))

from database.db import init_db
from services.account_service import deposit, get_account, withdraw


# ---------------------------------------------------------------------------
# get_account
# ---------------------------------------------------------------------------


class TestGetAccount:
    def test_returns_name_and_balance_for_demo_user(self, db_path):
        account = get_account(1, db_path=db_path)
        assert account is not None
        assert account["name"] == "Demo Customer"
        assert account["balance"] == pytest.approx(1000.00)

    def test_returns_none_for_nonexistent_user(self, db_path):
        account = get_account(9999, db_path=db_path)
        assert account is None


# ---------------------------------------------------------------------------
# deposit
# ---------------------------------------------------------------------------


class TestDeposit:
    def test_valid_deposit_increases_balance(self, db_path):
        success, msg = deposit(1, 200.00, db_path=db_path)
        assert success is True
        account = get_account(1, db_path=db_path)
        assert account["balance"] == pytest.approx(1200.00)

    def test_deposit_zero_returns_failure(self, db_path):
        success, _ = deposit(1, 0, db_path=db_path)
        assert success is False

    def test_deposit_negative_returns_failure(self, db_path):
        success, _ = deposit(1, -50.00, db_path=db_path)
        assert success is False

    def test_deposit_negative_does_not_change_balance(self, db_path):
        deposit(1, -50.00, db_path=db_path)
        account = get_account(1, db_path=db_path)
        assert account["balance"] == pytest.approx(1000.00)

    def test_deposit_infinity_returns_failure(self, db_path):
        success, _ = deposit(1, float("inf"), db_path=db_path)
        assert success is False

    def test_deposit_nan_returns_failure(self, db_path):
        success, _ = deposit(1, float("nan"), db_path=db_path)
        assert success is False

    def test_multiple_deposits_accumulate(self, db_path):
        deposit(1, 100.00, db_path=db_path)
        deposit(1, 50.00, db_path=db_path)
        account = get_account(1, db_path=db_path)
        assert account["balance"] == pytest.approx(1150.00)


# ---------------------------------------------------------------------------
# withdraw
# ---------------------------------------------------------------------------


class TestWithdraw:
    def test_valid_withdrawal_decreases_balance(self, db_path):
        success, _ = withdraw(1, 200.00, db_path=db_path)
        assert success is True
        account = get_account(1, db_path=db_path)
        assert account["balance"] == pytest.approx(800.00)

    def test_withdraw_exact_balance_leaves_zero(self, db_path):
        success, _ = withdraw(1, 1000.00, db_path=db_path)
        assert success is True
        account = get_account(1, db_path=db_path)
        assert account["balance"] == pytest.approx(0.00)

    def test_withdraw_more_than_balance_returns_failure(self, db_path):
        success, msg = withdraw(1, 9999.00, db_path=db_path)
        assert success is False
        assert "insufficient" in msg.lower()

    def test_withdraw_over_balance_does_not_change_balance(self, db_path):
        withdraw(1, 9999.00, db_path=db_path)
        account = get_account(1, db_path=db_path)
        assert account["balance"] == pytest.approx(1000.00)

    def test_withdraw_zero_returns_failure(self, db_path):
        success, _ = withdraw(1, 0, db_path=db_path)
        assert success is False

    def test_withdraw_negative_returns_failure(self, db_path):
        success, _ = withdraw(1, -100.00, db_path=db_path)
        assert success is False

    def test_withdraw_infinity_returns_failure(self, db_path):
        success, _ = withdraw(1, float("inf"), db_path=db_path)
        assert success is False
