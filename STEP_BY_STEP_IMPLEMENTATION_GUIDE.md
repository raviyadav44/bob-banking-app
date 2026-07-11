# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** This guide implements the design defined in [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md).  
> Instructions are written in plain English — logic and intent only, no raw code blocks.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 — Verify Python Version

Before anything else, confirm that Python 3.11 or later is installed on your machine. Open a terminal and ask it to print the Python version. If the version is below 3.11, download and install the correct version from python.org. The application will not guarantee compatibility with older versions.

### 1.2 — Create the Project Folder Structure

Create the following directories manually or via your terminal. Every folder must exist before you create files inside it:

```
banking_workshop/
├── FRONTEND/
│   └── templates/
├── BACKEND/
│   ├── services/
│   └── database/
└── tests/
```

The `FRONTEND/templates/` folder will hold all HTML pages. Flask needs this path to find and render them. The `BACKEND/services/` folder holds business logic files. The `BACKEND/database/` folder holds the database helper and the SQLite file that gets created at runtime.

### 1.3 — Create a Virtual Environment

Navigate your terminal into the `BACKEND/` folder. Create a Python virtual environment there. A virtual environment is an isolated Python installation specific to this project — it keeps your project's dependencies separate from other Python projects on your machine.

Once created, activate the virtual environment. On Windows the activation script is inside the `Scripts/` subfolder; on macOS/Linux it is inside `bin/`. After activation, your terminal prompt will show the environment name, confirming it is active.

> Always activate the virtual environment before running the Flask app or installing packages.

### 1.4 — Create `requirements.txt`

Inside `BACKEND/`, create a plain text file named `requirements.txt`. List two dependencies, one per line:
- `flask` — the web framework
- `werkzeug` — provides the password hashing utilities

Flask already depends on Werkzeug internally, but listing it explicitly makes the hashing import reliable and documents intent.

### 1.5 — Install Dependencies

With the virtual environment active, tell pip to install everything listed in `requirements.txt`. Pip will download Flask, Werkzeug, and all of their own dependencies (Jinja2, Click, etc.) automatically. You do not need to install anything else manually.

Confirm the installation succeeded by asking pip to list installed packages. You should see `Flask` and `Werkzeug` in the output.

### 1.6 — Configure Flask to Find the Templates Folder

When you create the Flask application instance in `app.py`, you need to tell Flask where the HTML templates live. By default Flask looks for a `templates/` folder next to `app.py`. Because your templates are in `FRONTEND/templates/` rather than `BACKEND/templates/`, you must pass the custom path explicitly when constructing the Flask app object.

Use a relative path that resolves from `BACKEND/` up one level and then into `FRONTEND/templates/`. The `os.path` module or Python's `pathlib` can compute this path reliably regardless of which directory you launch the app from.

---

## 2. Backend Implementation

### 2.1 — Create the Flask Application Entry Point (`app.py`)

`app.py` is the heart of the backend. When this file runs, it starts the web server.

**What to put in `app.py`:**

- Import Flask and create the application object, pointing it at the templates folder (see 1.6).
- Set a `SECRET_KEY` on the app's configuration. Flask uses this key to sign the session cookie. Without it, sessions will not work. Use any long, random string for development. Never hard-code a real secret in production code.
- Import and call `init_db()` from the database module immediately after creating the app, so the database and tables are ready before the first request arrives.
- Register all routes (login, logout, dashboard, deposit, withdraw) in this file or import them from a separate routes module.
- At the bottom of the file, include the standard `if __name__ == "__main__"` guard that starts the development server with debug mode enabled.

### 2.2 — Database Module (`database/db.py`)

This file handles all direct interaction with SQLite. No other file should import `sqlite3` directly — they all go through `db.py`.

**Connection helper:**  
Write a function that opens a connection to `bank.db` (located in the `BACKEND/database/` folder). Configure the connection to return rows as dictionary-like objects so that you can access columns by name rather than by index number. This makes the rest of the code far more readable.

**`init_db()` function:**  
This function runs once on startup. It should:
1. Open a connection using the helper.
2. Create the `users` table if it does not already exist. The table needs columns for an auto-incrementing id, username (unique), hashed password, full name, and current balance.
3. Create the `transactions` table if it does not already exist. The table needs columns for an auto-incrementing id, a foreign key linking to the user, transaction type (deposit or withdrawal as a text label), the amount, and a timestamp that defaults to the current date and time.
4. After creating the tables, check whether any users exist. If the `users` table is empty, insert a single demo account with a known username, a Werkzeug-hashed password, a display name, and an opening balance (for example, 1000.00). This is the seeded account used for demo and testing.
5. Commit the changes and close the connection.

> The "create if not exists" pattern means `init_db()` is safe to call on every startup — it will not destroy existing data.

### 2.3 — Authentication Service (`services/auth_service.py`)

This file contains the logic for proving who a user is and managing their session.

**`verify_login(username, password)` function:**  
1. Open a database connection and query the `users` table for a row where the username matches what was submitted.
2. If no row is found, return a failure signal (for example, `None` or `False`).
3. If a row is found, use Werkzeug's `check_password_hash` function to compare the submitted plain-text password against the stored hash. If they match, return the user's record (id and name). If they do not match, return a failure signal.
4. Never tell the user specifically whether the username was wrong or the password was wrong — this leaks information. Always use a single generic error message such as "Invalid username or password."

**`@login_required` decorator:**  
Write a Python decorator function that wraps any route handler. When the decorated route is called, the decorator first checks whether `user_id` exists in the Flask session. If it does, it lets the route proceed normally. If it does not, it immediately redirects the request to the `/login` page. Apply this decorator to the dashboard, deposit, and withdraw routes.

### 2.4 — Account Service (`services/account_service.py`)

This file contains all logic related to account balances and transactions.

**`get_account(user_id)` function:**  
Query the `users` table for the row matching the given `user_id`. Return the user's display name and current balance. This is called every time the dashboard page loads.

**`deposit(user_id, amount)` function:**  
1. Receive the user id and the amount to deposit.
2. Apply validation (see Section 5).
3. If valid, open a database connection and run two operations inside the same transaction: add the amount to the user's `balance` column in the `users` table, and insert a new row into the `transactions` table recording the deposit, the amount, and the current timestamp.
4. Commit both operations together. If either fails, roll back to avoid partial writes.
5. Return a success or failure signal along with a human-readable message.

**`withdraw(user_id, amount)` function:**  
1. Receive the user id and the amount to withdraw.
2. Apply validation (see Section 5), including the balance sufficiency check.
3. Fetch the current balance first. If the withdrawal amount exceeds it, return a failure signal with a clear message.
4. If valid, run two operations in a single transaction: subtract the amount from the user's balance, and insert a withdrawal record into the `transactions` table.
5. Commit both or roll back on failure.
6. Return a success or failure signal with a message.

### 2.5 — Routes in `app.py`

Each route maps a URL path and HTTP method to a Python function.

**`GET /` (root):**  
Redirect immediately to `/login`. The root URL should never show a blank page.

**`GET /login`:**  
Check whether the user is already logged in (i.e., `user_id` is in the session). If yes, redirect to `/dashboard` — no need to show the login form again. If not, render `login.html` with no error message.

**`POST /login`:**  
Read the `username` and `password` fields from the submitted form data. Call `verify_login()` from `auth_service`. If it returns a valid user, store `user_id` and `user_name` in the Flask session, then redirect to `/dashboard`. If it returns a failure, re-render `login.html` and pass an error message string to the template so it can display it to the user.

**`GET /logout`:**  
Call `session.clear()` to remove all session data, then redirect to `/login`. Protect this route with `@login_required` so that only authenticated users can trigger it (prevents CSRF-style logout abuse).

**`GET /dashboard`:**  
Apply `@login_required`. Read `user_id` from the session, call `get_account()` to fetch the current name and balance, and render `dashboard.html` passing the account data to the template. Also retrieve and pass any flash messages so they display on the page.

**`POST /deposit`:**  
Apply `@login_required`. Read the `amount` field from the form. Call `deposit()` from the account service. Use `flash()` to store the success or error message in the session, then redirect to `/dashboard` with a `302` redirect. Never re-render the form from a POST handler — always redirect after a write operation to prevent duplicate submissions on browser refresh.

**`POST /withdraw`:**  
Apply `@login_required`. Same pattern as deposit: read amount, call `withdraw()`, flash the result message, redirect to `/dashboard`.

### 2.6 — Session Management

Flask stores session data in a cryptographically signed cookie sent to the browser. The `SECRET_KEY` on the app object is what makes the signature tamper-evident.

- Store only lightweight identifiers in the session: `user_id` (integer) and `user_name` (string for display). Never store the password or the full account object.
- On login success, write to the session.
- On logout, call `session.clear()` to remove everything.
- The `@login_required` decorator reads from the session to decide whether to allow or redirect.

Flask's `flash()` mechanism also uses the session internally — it stores a one-time message that is consumed the next time the template calls `get_flashed_messages()`. This is how deposit/withdraw results travel from a POST handler to the dashboard page after the redirect.

### 2.7 — Error Handling

Handle these failure cases gracefully so the application never crashes or shows a raw Python traceback to the user:

| Scenario | Handling Approach |
|---|---|
| Wrong username or password | Re-render login page with a generic error message; do not expose which field was wrong |
| Non-numeric deposit/withdraw amount | Flash an error message on the dashboard; do not call the service layer |
| Zero or negative amount submitted | Flash an error message; reject without touching the database |
| Withdrawal exceeds balance | Flash a specific "Insufficient funds" message; do not modify the database |
| Database file missing or corrupt | Allow Python's exception to propagate for now; log the error to the terminal |
| Access to protected route while logged out | The `@login_required` decorator handles this with a redirect |

For development, enable Flask's debug mode so that meaningful tracebacks appear in the terminal. Disable debug mode for any production deployment.

---

## 3. Frontend Implementation

### 3.1 — Bootstrap Setup

Both HTML pages load Bootstrap from a CDN link placed inside the `<head>` element. No installation is required. Include the Bootstrap CSS link and the Bootstrap JS bundle script tag (the JS bundle includes Popper, which is needed for certain Bootstrap components like alerts). Use Bootstrap version 5.

Because Flask renders these as Jinja2 templates, both pages should share the same Bootstrap CDN links. Consider creating a `base.html` layout template that both `login.html` and `dashboard.html` extend — this avoids duplicating the `<head>` block in every file.

### 3.2 — Login Page (`login.html`)

**Purpose:** Collect the customer's credentials and submit them to the backend.

**Layout logic:**
- Use a centred Bootstrap card component to contain the form — this gives a clean, professional look without custom CSS.
- The card should have a heading like "Banking Login" or "Customer Login".
- Inside the card, place a `<form>` element whose `action` attribute points to `/login` and whose `method` is `POST`.
- Add a text input for the username with the `name` attribute set to `username`.
- Add a password input for the password with the `name` attribute set to `password`.
- Add a submit button styled with a Bootstrap primary button class.
- Below the form (or above it), add a conditional block that only renders when an error message variable is passed from the backend. Use a Bootstrap `alert-danger` styled `<div>` to display the error message in red.
- Do not add a "Remember me" checkbox or a "Forgot password" link — these are out of scope.

**Jinja2 note:** The error message from the route handler is passed as a template variable. Use `{{ variable_name }}` to render it and wrap the block in `{% if variable_name %}` so that the error box is invisible when there is no error.

### 3.3 — Dashboard Page (`dashboard.html`)

**Purpose:** Show the customer's account summary and provide deposit and withdrawal forms.

**Layout logic:**  
Divide the page into sections using Bootstrap's grid:

**Navigation bar:**  
A simple Bootstrap navbar at the top showing "Banking App" on the left and a "Logout" link on the right that points to `/logout`.

**Account summary card:**  
A Bootstrap card showing the customer's display name and their current balance, formatted as a currency value (e.g. `$1,234.56`). This data is passed in from the `/dashboard` route.

**Flash message area:**  
Immediately below the summary card, include a block that loops over flash messages from the session. Each message should be displayed as a Bootstrap alert — use `alert-success` for success messages and `alert-danger` for error messages. If you use a single flash category or a simple string, a single alert style is fine for now.

**Deposit form card:**  
A Bootstrap card with a heading "Deposit Funds". Inside it, a `<form>` with `action="/deposit"` and `method="POST"`. A numeric input field for the amount (with `name="amount"`) and a submit button styled with a green Bootstrap button class.

**Withdraw form card:**  
A Bootstrap card with a heading "Withdraw Funds". Inside it, a `<form>` with `action="/withdraw"` and `method="POST"`. A numeric input field for the amount (with `name="amount"`) and a submit button styled with a red Bootstrap button class.

Place the deposit and withdraw cards side by side on wider screens using Bootstrap's two-column grid (`col-md-6`). On mobile they stack vertically automatically.

### 3.4 — Jinja2 Templating Notes

- All dynamic values (username, balance, error messages) are inserted into the HTML by the Jinja2 template engine at the moment Flask renders the template.
- Flask's `render_template()` function takes the template filename and any keyword arguments. Those arguments become variables available inside the template.
- Use `{{ variable }}` to output a value and `{% if %} / {% endif %}` for conditional blocks.
- Use `{% for message in get_flashed_messages() %} / {% endfor %}` to loop over flash messages.
- Because Flask serves these templates directly, there is no build step — saving the file is enough to see changes after a browser refresh.

---

## 4. Integration Steps

### 4.1 — Tell Flask Where the Templates Are

As noted in step 1.6, when constructing the Flask app object in `app.py`, pass the `template_folder` argument with the absolute or relative path to `FRONTEND/templates/`. Verify this is working by running the app and navigating to `/login` — if the HTML page renders, the path is correct. If Flask throws a `TemplateNotFound` error, the path is wrong.

### 4.2 — Wire Routes to Service Functions

Each route in `app.py` should call exactly one service function per operation — nothing more. The route's job is to:
1. Extract data from the incoming request (form fields, session values).
2. Call the appropriate service function with that data.
3. Use the result to either redirect or render a template.

The route should not contain any database queries or business logic directly. All of that belongs in the service layer. This separation makes the code easier to test and maintain.

### 4.3 — Connect the Database Module to the Services

Both `auth_service.py` and `account_service.py` should import the database connection helper from `database/db.py`. When a service function needs to read or write data, it calls the helper to get a connection, performs its queries, commits if writing, and closes the connection.

Because Python's `sqlite3` module is part of the standard library, no additional installation is needed for the database connection itself.

### 4.4 — Confirm the Startup Sequence

When the application starts, the sequence must be:
1. Flask app object is created.
2. `SECRET_KEY` is configured.
3. `init_db()` is called — tables are created, demo account is seeded if absent.
4. Routes are registered.
5. The development server begins accepting requests.

If `init_db()` is not called before the first request, the first login attempt will fail with a "no such table" database error. Placing the `init_db()` call right after the app object is created (before any route definitions) ensures correct ordering.

### 4.5 — Form Field Names Must Match Route Expectations

The `name` attribute on every HTML `<input>` element must exactly match what the Flask route reads from `request.form`. For example, if the login form uses `name="username"`, the route must read `request.form['username']` (not `request.form['user']` or any other spelling). A mismatch produces either a `KeyError` or an empty string silently. Double-check all field names when first integrating the forms.

---

## 5. Validation Rules

### 5.1 — Login Validation

| Rule | Where to enforce | Behaviour on failure |
|---|---|---|
| Username field must not be empty | POST `/login` route, before calling service | Re-render login with error message |
| Password field must not be empty | POST `/login` route, before calling service | Re-render login with error message |
| Username must exist in the database | `verify_login()` in auth service | Return `None`; route shows generic error |
| Password must match the stored hash | `verify_login()` using `check_password_hash` | Return `None`; route shows generic error |
| Error message must never specify which field was wrong | Route handler | Always use one generic message |

### 5.2 — Balance Validation

| Rule | Where to enforce | Behaviour on failure |
|---|---|---|
| Balance is always stored as a decimal/float — never as a string | `init_db()` seed and all UPDATE queries | Arithmetic operations work correctly |
| Balance must never go below zero | `withdraw()` in account service | Return failure; do not execute the UPDATE |
| Display balance formatted as currency | `dashboard.html` Jinja2 template | Cosmetic only — use Python's format or Jinja2 filters |

### 5.3 — Deposit Checks

| Rule | Where to enforce | Behaviour on failure |
|---|---|---|
| Amount field must not be empty | POST `/deposit` route | Flash error, redirect to dashboard |
| Amount must be a valid number | POST `/deposit` route — wrap `float()` conversion in a try/except | Flash error, redirect to dashboard |
| Amount must be greater than zero | `deposit()` service function | Return failure signal with message |
| Amount must be finite (no `inf` or `nan`) | `deposit()` service function — use Python's `math.isfinite()` | Return failure signal |
| After deposit, balance = old balance + amount | `deposit()` service function | Run as a single database transaction |

### 5.4 — Withdrawal Checks

| Rule | Where to enforce | Behaviour on failure |
|---|---|---|
| Amount field must not be empty | POST `/withdraw` route | Flash error, redirect to dashboard |
| Amount must be a valid number | POST `/withdraw` route — try/except around `float()` | Flash error, redirect to dashboard |
| Amount must be greater than zero | `withdraw()` service function | Return failure with message |
| Amount must be finite | `withdraw()` service function | Return failure |
| Amount must not exceed current balance | `withdraw()` service function — fetch balance first, compare | Flash "Insufficient funds", redirect |
| After withdrawal, balance = old balance − amount | `withdraw()` service function | Run as a single database transaction |

> **General principle:** Validate form inputs at the route layer (type conversion, emptiness), then validate business rules at the service layer (positive amounts, balance sufficiency). Never let raw user input reach a database query unsanitised.

---

## 6. Testing

### 6.1 — Unit Tests

Unit tests check individual service functions in isolation, without running the full Flask server.

**What to test in `auth_service.py`:**
- Calling `verify_login()` with the correct demo credentials returns a non-None user object.
- Calling `verify_login()` with a wrong password returns `None`.
- Calling `verify_login()` with a non-existent username returns `None`.

**What to test in `account_service.py`:**
- `get_account()` returns the correct name and opening balance for the demo user.
- `deposit()` with a valid positive amount increases the balance by exactly that amount.
- `deposit()` with zero returns a failure signal.
- `deposit()` with a negative number returns a failure signal.
- `withdraw()` with a valid amount less than the balance decreases the balance correctly.
- `withdraw()` with an amount equal to the balance leaves the balance at zero.
- `withdraw()` with an amount greater than the balance returns a failure signal and does not change the balance.
- `withdraw()` with zero or a negative number returns a failure signal.

**How to set up the test database:**  
Use a separate in-memory SQLite database for tests so that tests never touch the real `bank.db`. In your pytest `conftest.py` (or at the top of the test file), create a fresh in-memory database, call `init_db()` on it, and pass that connection to the service functions under test. Tear it down after each test.

**File location:** Place all test files in the `tests/` folder at the root of the project. Name the main test file `test_account_service.py`. Pytest discovers test files automatically if they start with `test_`.

### 6.2 — Integration Tests

Integration tests exercise the full Flask request/response cycle — forms, routes, session, and database together.

**How to create a test client:**  
Flask provides a `test_client()` method on the app object. Use this in tests to simulate HTTP requests without starting a real server. Configure the app to use a temporary in-memory or temp-file SQLite database before creating the test client.

**What to test:**
- A `GET /login` returns a 200 status code and the page contains the word "Login" or a username input field.
- A `POST /login` with correct credentials returns a redirect (302) to `/dashboard`.
- A `POST /login` with wrong credentials returns a 200 and the response contains the error message text.
- A `GET /dashboard` without being logged in returns a redirect (302) to `/login`.
- A `GET /dashboard` after a successful login returns a 200 and contains the user's name and balance.
- A `POST /deposit` with a valid amount returns a redirect to `/dashboard` and the new balance is higher.
- A `POST /withdraw` with a valid amount returns a redirect to `/dashboard` and the new balance is lower.
- A `POST /withdraw` with an amount exceeding balance returns a redirect to `/dashboard` and balance is unchanged.
- A `GET /logout` clears the session and redirects to `/login`.

### 6.3 — Manual Testing Checklist

Run through this checklist in a browser after each significant change.

**Login flow:**
- [ ] Visiting `/` redirects to `/login`
- [ ] The login page renders correctly with Bootstrap styling
- [ ] Submitting empty username shows error message
- [ ] Submitting empty password shows error message
- [ ] Submitting wrong credentials shows generic error — does not say which field was wrong
- [ ] Submitting correct credentials redirects to `/dashboard`

**Dashboard:**
- [ ] Dashboard displays the customer's full name
- [ ] Dashboard displays the current balance with correct formatting
- [ ] Dashboard is not accessible by pasting the URL while logged out (redirects to login)
- [ ] Flash messages are visible after a deposit or withdrawal
- [ ] Flash messages disappear after a page refresh

**Deposit:**
- [ ] Depositing a valid positive amount increases the balance immediately on refresh
- [ ] Submitting zero shows an error flash message
- [ ] Submitting a negative number shows an error flash message
- [ ] Submitting letters (non-numeric) shows an error flash message
- [ ] Submitting a very large number increases the balance correctly

**Withdrawal:**
- [ ] Withdrawing a valid amount less than balance decreases balance correctly
- [ ] Withdrawing the exact balance leaves balance at zero
- [ ] Withdrawing more than the balance shows "Insufficient funds" and balance is unchanged
- [ ] Submitting zero shows an error message
- [ ] Submitting a negative number shows an error message
- [ ] Submitting letters shows an error message

**Logout:**
- [ ] Clicking logout redirects to `/login`
- [ ] After logout, pressing browser Back and navigating to `/dashboard` redirects to `/login`
- [ ] Session cookie is no longer valid after logout

---

## 7. Deployment

### 7.1 — Running Locally

Follow these steps every time you want to run the application in development:

1. Open a terminal and navigate into the `BACKEND/` folder.
2. Activate the virtual environment (see step 1.3).
3. Run `app.py` using Python. Flask's development server will start and print the local URL (typically `http://127.0.0.1:5000`).
4. Open that URL in a browser. The root path `/` will redirect you to `/login`.
5. Use the demo credentials that were seeded by `init_db()` to log in.
6. To stop the server, press `Ctrl + C` in the terminal.

The SQLite database file (`bank.db`) will be created automatically in `BACKEND/database/` the first time the app runs. You can delete this file at any time to reset the database back to its seeded state — it will be recreated on the next startup.

### 7.2 — Environment Variables

For development, the `SECRET_KEY` can be a hardcoded string in `app.py`. Before moving to any shared or production environment, change this so the key is read from an environment variable rather than committed in the source code. Use `os.environ.get('SECRET_KEY', 'fallback-dev-key')` as the pattern — this reads the variable from the environment if set, and falls back to a development default if not.

### 7.3 — Production Considerations

Flask's built-in development server is **not suitable for production**. It handles only one request at a time and is not hardened against attacks. For a production deployment, consider the following changes:

| Area | Development | Production recommendation |
|---|---|---|
| Web server | Flask dev server (`flask run`) | Gunicorn or uWSGI behind Nginx |
| Debug mode | `debug=True` | `debug=False` — never expose tracebacks |
| Secret key | Hardcoded string | Read from environment variable or secrets manager |
| Database | SQLite file on disk | PostgreSQL or MySQL for multi-user concurrency |
| HTTPS | Not required locally | Required — use a TLS certificate (Let's Encrypt) |
| Static files | Served by Flask | Served by Nginx or a CDN for performance |

For the purposes of this workshop and demo, running locally with the Flask development server is the intended and correct approach. The production considerations above are included for awareness only.

### 7.4 — CI/CD Pipeline (Already Provided)

The repository already contains a GitHub Actions workflow at [`docs/demo_setup/banking-app-ci.yml`](./docs/demo_setup/banking-app-ci.yml). When copied into `.github/workflows/`, this pipeline will:
- Trigger on every push to `main` or any `feature/**` branch.
- Set up Python 3.11.
- Install Flask and Werkzeug (and anything in `requirements.txt`).
- Run all pytest tests in the `tests/` folder.

No changes to the CI file are needed as long as your test files are in `tests/` and your `requirements.txt` is at `BACKEND/requirements.txt` (adjust the pip install path in the CI file if needed).

---

*This guide covers implementation logic and instructions only. For the high-level design rationale, architecture decisions, and project scope, refer to [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md).*
