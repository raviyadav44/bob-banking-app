# Banking Web Application — Implementation Plan

---

## 1. Solution Overview

### Objective
Build a simple, browser-based banking web application that allows customers to log in, view their account balance, deposit funds, withdraw funds, and log out securely.

### Scope
| In Scope | Out of Scope |
|---|---|
| Customer login / logout | Admin portal |
| Dashboard with account summary | Multi-currency support |
| View current balance | Fund transfers between accounts |
| Deposit and withdraw funds | External payment integrations |
| Session-based authentication | Email / SMS notifications |
| SQLite persistence | Production database (PostgreSQL, MySQL) |

### Users
- **Customer** — the sole user role. A customer authenticates, manages their own account balance, and logs out.

### Functional Requirements
1. A customer can log in with a username and password.
2. After login, the customer is directed to a dashboard showing their name and current balance.
3. The customer can deposit a positive amount into their account.
4. The customer can withdraw a positive amount, subject to sufficient balance.
5. Every transaction (deposit/withdrawal) is reflected immediately on the dashboard.
6. The customer can log out, terminating their session.
7. Unauthenticated access to protected pages redirects to the login page.

### Non-Functional Requirements
- **Security:** Passwords stored as hashes (Werkzeug). Session data kept server-side.
- **Usability:** Responsive UI using Bootstrap; works on desktop and mobile browsers.
- **Maintainability:** Clean separation between frontend (HTML/Bootstrap) and backend (Flask).
- **Portability:** SQLite requires no external database service; runs locally out of the box.
- **Simplicity:** Minimal dependencies — Flask, Werkzeug, and SQLite only.

### Assumptions
- A single customer account is pre-seeded in the database for demo use.
- No account registration flow is required.
- The application runs on `localhost` during development.
- Bootstrap is loaded via CDN (no local asset pipeline needed).
- Python 3.11 is available in the runtime environment (per CI pipeline).

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                     Browser                         │
│  ┌──────────────────────────────────────────────┐   │
│  │   FRONTEND  (HTML + Bootstrap via CDN)       │   │
│  │   - login.html                               │   │
│  │   - dashboard.html                           │   │
│  └────────────────┬─────────────────────────────┘   │
└───────────────────│─────────────────────────────────┘
                    │  HTTP (form POST / GET)
┌───────────────────▼─────────────────────────────────┐
│                  BACKEND  (Python Flask)             │
│  ┌──────────────────────────────────────────────┐   │
│  │   Routes / Controllers                       │   │
│  │   - /login   /logout                         │   │
│  │   - /dashboard                               │   │
│  │   - /deposit   /withdraw                     │   │
│  └────────────────┬─────────────────────────────┘   │
│  ┌────────────────▼─────────────────────────────┐   │
│  │   Services / Business Logic                  │   │
│  │   - Auth service (hash verify, session)      │   │
│  │   - Account service (balance, transactions)  │   │
│  └────────────────┬─────────────────────────────┘   │
│  ┌────────────────▼─────────────────────────────┐   │
│  │   Data Access Layer                          │   │
│  │   - SQLite via Python sqlite3 module         │   │
│  └────────────────┬─────────────────────────────┘   │
└───────────────────│─────────────────────────────────┘
                    │  SQL queries
┌───────────────────▼─────────────────────────────────┐
│               DATABASE  (SQLite file)                │
│   bank.db  — users table + transactions table        │
└─────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

| Layer | Technology | Role |
|---|---|---|
| Frontend | HTML + Bootstrap (CDN) | Renders UI, submits forms |
| Backend | Python 3.11 + Flask | Handles routes, enforces auth, executes business logic |
| Database | SQLite (`bank.db`) | Persists user credentials and account balances |

### Request Lifecycle

1. **Browser** submits an HTTP request (GET page load or POST form action).
2. **Flask route handler** validates the session; redirects to `/login` if unauthenticated.
3. **Service layer** applies business rules (e.g., sufficient balance check for withdrawal).
4. **Data access layer** reads or writes to `bank.db` via `sqlite3`.
5. **Flask** renders the appropriate HTML template and returns the response to the browser.
6. **Browser** displays the updated page (dashboard with new balance or error message).

---

## 3. Component Design

### Frontend Responsibilities
- Present login form (username + password fields, submit button).
- Display dashboard: customer name, current balance, deposit form, withdrawal form, logout link.
- Show inline feedback messages (success / error) returned by the backend.
- Apply responsive layout via Bootstrap grid and utility classes.
- All pages are server-rendered Jinja2 templates — no JavaScript framework required.

### Backend Responsibilities
- Expose HTTP routes for: login, logout, dashboard, deposit, withdraw.
- Authenticate users by verifying hashed passwords with Werkzeug.
- Manage server-side sessions (Flask session object) to track the logged-in user.
- Guard all protected routes — redirect unauthenticated requests to `/login`.
- Enforce business rules: positive amounts only, withdrawal cannot exceed balance.
- Read and write account data through the data access layer.
- Seed the database with a demo account on first startup if it is empty.

### Database Responsibilities
- Persist user credentials (username + hashed password).
- Persist current account balance per user.
- Persist a transaction log (amount, type, timestamp) for audit trail.
- The SQLite file (`bank.db`) is created automatically by the backend on first run.

---

## 4. Folder Structure

```
banking_workshop/
├── FRONTEND/
│   └── templates/                  # Jinja2 HTML templates served by Flask
│       ├── login.html              # Login page
│       └── dashboard.html          # Dashboard, balance, deposit/withdraw forms
│
├── BACKEND/
│   ├── app.py                      # Flask application entry point, route definitions
│   ├── services/
│   │   ├── auth_service.py         # Login, logout, session management logic
│   │   └── account_service.py      # Balance retrieval, deposit, withdrawal logic
│   ├── database/
│   │   ├── db.py                   # Database connection helper, init / seed logic
│   │   └── bank.db                 # SQLite database file (auto-created at runtime)
│   └── requirements.txt            # Python dependencies (flask, werkzeug)
│
├── tests/                          # Pytest unit tests for backend services
│   └── test_account_service.py
│
└── docs/
    └── demo_setup/                 # Existing setup guides and CI template
```

### Folder Responsibilities

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | All user-facing HTML. Rendered server-side by Flask's Jinja2 engine. |
| `BACKEND/app.py` | App factory, route registration, session config, startup seeding. |
| `BACKEND/services/` | Business logic, kept separate from route handlers. |
| `BACKEND/database/` | Database initialisation, connection management, raw SQL helpers. |
| `tests/` | Automated tests for service-layer functions. |
| `docs/` | Workshop documentation and CI/CD setup guides. |

---

## 5. Module Breakdown

### Authentication Module
**Scope:** Login and logout flows.
- Accepts username and password from the login form.
- Looks up the user record in the database.
- Verifies the submitted password against the stored Werkzeug hash.
- On success: stores `user_id` in Flask session, redirects to `/dashboard`.
- On failure: re-renders login page with an error message.
- Logout clears the session and redirects to `/login`.
- A `@login_required` decorator guards all protected routes.

### Dashboard Module
**Scope:** Post-login landing page.
- Reads the authenticated user's name and current balance from the database.
- Renders the dashboard template with balance and transaction forms.
- Displays any flash messages (success / error) passed from deposit/withdraw actions.

### Account Management Module
**Scope:** Balance enquiry.
- Provides a service function to fetch the current balance for a given `user_id`.
- Called by the dashboard route on every page load.

### Transactions Module
**Scope:** Deposit and withdrawal operations.
- **Deposit:** Validates that the amount is a positive number, then increments the balance.
- **Withdraw:** Validates that the amount is positive and does not exceed the current balance; decrements the balance on success.
- Both operations append a record to the transaction log table.
- Results are communicated back to the dashboard via Flask flash messages.

---

## 6. Implementation Roadmap

### Phase 1 — Project Scaffolding
**Goal:** Create the folder structure and install dependencies so the app can start.

| Task | Effort | Depends On |
|---|---|---|
| Create `FRONTEND/templates/` and `BACKEND/` directory tree | XS | — |
| Create `BACKEND/requirements.txt` with Flask + Werkzeug | XS | — |
| Create `BACKEND/app.py` skeleton (Flask instance, no routes yet) | XS | requirements.txt |

**Status:** `[ ] pending`

---

### Phase 2 — Database Layer
**Goal:** Set up the SQLite database and auto-seed a demo account.

| Task | Effort | Depends On |
|---|---|---|
| Implement `db.py` — connection helper and `init_db()` function | S | Phase 1 |
| Define `users` and `transactions` tables in `init_db()` | S | db.py |
| Implement seed logic — insert demo account if no users exist | S | init_db() |
| Call `init_db()` from `app.py` at startup | XS | db.py, app.py |

**Status:** `[ ] pending`

---

### Phase 3 — Authentication Module
**Goal:** Customers can log in and log out securely.

| Task | Effort | Depends On |
|---|---|---|
| Implement `auth_service.py` — `verify_login()` and `logout()` | S | Phase 2 |
| Add `/login` GET and POST routes in `app.py` | S | auth_service.py |
| Add `/logout` route | XS | auth_service.py |
| Implement `@login_required` decorator | XS | Flask session |
| Build `login.html` template (form + error message display) | S | Bootstrap CDN |

**Status:** `[ ] pending`

---

### Phase 4 — Dashboard & Balance View
**Goal:** Authenticated customers can see their name and balance.

| Task | Effort | Depends On |
|---|---|---|
| Implement `account_service.py` — `get_balance()` | XS | Phase 2 |
| Add `/dashboard` GET route in `app.py` | S | auth_service, account_service |
| Build `dashboard.html` template (balance display + logout link) | S | Bootstrap CDN |

**Status:** `[ ] pending`

---

### Phase 5 — Transactions (Deposit & Withdraw)
**Goal:** Customers can deposit and withdraw funds from the dashboard.

| Task | Effort | Depends On |
|---|---|---|
| Implement `deposit()` in `account_service.py` | S | Phase 2 |
| Implement `withdraw()` with balance check in `account_service.py` | S | Phase 2 |
| Add `/deposit` and `/withdraw` POST routes in `app.py` | S | account_service.py |
| Add deposit + withdraw forms to `dashboard.html` | S | Phase 4 |
| Display flash messages (success / error) on dashboard | XS | Flask flash |

**Status:** `[ ] pending`

---

### Phase 6 — Integration & Validation
**Goal:** Verify the full user journey works end-to-end.

| Task | Effort | Depends On |
|---|---|---|
| Manual end-to-end test: login → deposit → withdraw → logout | S | Phases 1–5 |
| Write pytest unit tests for `account_service` functions | S | Phase 5 |
| Fix any bugs surfaced during testing | M | All phases |

**Status:** `[ ] pending`

---

### Effort Key
| Symbol | Meaning |
|---|---|
| XS | < 30 minutes |
| S | 30–60 minutes |
| M | 1–2 hours |

---

*This document covers planning only. Database schema, API contracts, SQL scripts, and detailed implementation steps are out of scope for this plan.*
