"""
app.py
~~~~~~
Flask application entry point.
Run this file directly to start the development server:

    cd BACKEND
    python app.py
"""

import os
import sys

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# ---------------------------------------------------------------------------
# Path setup - allow importing from BACKEND/ regardless of working directory.
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BACKEND_DIR)

from database.db import init_db
from services.auth_service import login_required, verify_login
from services.account_service import deposit, get_account, withdraw

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
_TEMPLATES_DIR = os.path.join(_BACKEND_DIR, "..", "FRONTEND", "templates")

app = Flask(__name__, template_folder=_TEMPLATES_DIR)

# Read SECRET_KEY from the environment; fall back to a development default.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

# Initialise the database (creates tables + seeds demo account if needed).
init_db()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Root URL - redirect straight to /login."""
    return redirect(url_for("login"))


# --- Authentication -----------------------------------------------------------


@app.route("/login", methods=["GET", "POST"])
def login():
    # If already authenticated, skip the login page.
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Emptiness checks at the route layer.
        if not username:
            error = "Invalid username or password."
        elif not password:
            error = "Invalid username or password."
        else:
            user = verify_login(username, password)
            if user:
                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


# --- Dashboard ---------------------------------------------------------------


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    account = get_account(user_id)
    return render_template("dashboard.html", account=account)


# --- Transactions -------------------------------------------------------------


@app.route("/deposit", methods=["POST"])
@login_required
def deposit_route():
    raw_amount = request.form.get("amount", "").strip()

    if not raw_amount:
        flash("Please enter a deposit amount.", "error")
        return redirect(url_for("dashboard"))

    try:
        amount = float(raw_amount)
    except ValueError:
        flash("Deposit amount must be a valid number.", "error")
        return redirect(url_for("dashboard"))

    success, message = deposit(session["user_id"], amount)
    flash(message, "success" if success else "error")
    return redirect(url_for("dashboard"))


@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw_route():
    raw_amount = request.form.get("amount", "").strip()

    # Validation check 1: amount field must not be empty
    if not raw_amount:
        flash("Amount is required", "error")
        return redirect(url_for("dashboard"))

    try:
        amount = float(raw_amount)
    except ValueError:
        flash("Withdrawal amount must be a valid number.", "error")
        return redirect(url_for("dashboard"))

    # Validation check 2: amount must be a positive number
    if amount <= 0:
        flash("Amount must be greater than zero", "error")
        return redirect(url_for("dashboard"))

    # Validation check 3: amount must not exceed current balance
    account = get_account(session["user_id"])
    if account and amount > account["balance"]:
        flash("Insufficient funds", "error")
        return redirect(url_for("dashboard"))

    success, message = withdraw(session["user_id"], amount)
    flash(message, "success" if success else "error")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# Development server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)