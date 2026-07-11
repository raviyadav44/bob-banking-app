"""
services/account_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business logic for account balance enquiry, deposits, and withdrawals.
All database writes use a single transaction to prevent partial updates.
"""

import math
import os
import sys
from typing import Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import get_connection, DB_PATH


def get_account(user_id: int, db_path: str = None) -> Optional[dict]:
    """Return {'name': str, 'balance': float} for the given user_id, or None."""
    path = db_path or DB_PATH
    conn = get_connection(path)
    try:
        row = conn.execute(
            "SELECT name, balance FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return {"name": row["name"], "balance": row["balance"]}


def deposit(user_id: int, amount: float, db_path: str = None) -> Tuple[bool, str]:
    """Credit *amount* to the user's balance and record a transaction.

    Returns (success: bool, message: str).
    Business-rule validation lives here; type/emptiness checks are in the route.
    """
    if not math.isfinite(amount):
        return False, "Amount must be a finite number."
    if amount <= 0:
        return False, "Deposit amount must be greater than zero."

    path = db_path or DB_PATH
    conn = get_connection(path)
    try:
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id)
        )
        conn.execute(
            "INSERT INTO transactions (user_id, type, amount) VALUES (?, 'deposit', ?)",
            (user_id, amount),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return False, f"Database error: {exc}"
    finally:
        conn.close()

    return True, f"Successfully deposited ${amount:,.2f}."


def withdraw(user_id: int, amount: float, db_path: str = None) -> Tuple[bool, str]:
    """Debit *amount* from the user's balance and record a transaction.

    Returns (success: bool, message: str).
    """
    if not math.isfinite(amount):
        return False, "Amount must be a finite number."
    if amount <= 0:
        return False, "Withdrawal amount must be greater than zero."

    path = db_path or DB_PATH
    conn = get_connection(path)
    try:
        row = conn.execute(
            "SELECT balance FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return False, "Account not found."

        current_balance = row["balance"]
        if amount > current_balance:
            return False, "Insufficient funds."

        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user_id)
        )
        conn.execute(
            "INSERT INTO transactions (user_id, type, amount) VALUES (?, 'withdrawal', ?)",
            (user_id, amount),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return False, f"Database error: {exc}"
    finally:
        conn.close()

    return True, f"Successfully withdrew ${amount:,.2f}."
