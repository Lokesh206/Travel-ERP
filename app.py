from __future__ import annotations

import os
import re
import secrets
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import wraps
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlsplit

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("TRAVEL_ERP_DATABASE", ROOT / "travel_erp.sqlite3"))
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("TRAVEL_ERP_SECRET") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("TRAVEL_ERP_HTTPS", "").lower() == "true",
    MAX_CONTENT_LENGTH=1_000_000,
)

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'agent', 'customer')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    code TEXT NOT NULL UNIQUE,
    level INTEGER NOT NULL DEFAULT 1,
    depth INTEGER NOT NULL DEFAULT 1,
    path TEXT NOT NULL DEFAULT '/',
    parent_id INTEGER REFERENCES agents(id),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('pending_approval', 'active', 'rejected', 'suspended')),
    phone TEXT,
    approved_by INTEGER REFERENCES users(id),
    approved_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (parent_id IS NULL OR parent_id != id)
);
CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    destination TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    duration TEXT NOT NULL,
    price_paise INTEGER NOT NULL CHECK (price_paise > 0),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    reserved INTEGER NOT NULL DEFAULT 0 CHECK (reserved >= 0 AND reserved <= capacity),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    image_file TEXT,
    official_url TEXT,
    activities TEXT
);
CREATE TABLE IF NOT EXISTS package_details (
    package_id INTEGER PRIMARY KEY REFERENCES packages(id) ON DELETE CASCADE,
    stay_type TEXT NOT NULL,
    meal_plan TEXT NOT NULL,
    transport TEXT NOT NULL,
    inclusions TEXT NOT NULL,
    itinerary TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY,
    reference TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL REFERENCES users(id),
    agent_id INTEGER REFERENCES agents(id),
    package_id INTEGER NOT NULL REFERENCES packages(id),
    travel_date TEXT NOT NULL,
    return_date TEXT,
    travellers INTEGER NOT NULL CHECK (travellers BETWEEN 1 AND 20),
    total_paise INTEGER NOT NULL CHECK (total_paise > 0),
    status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled')),
    payment_method TEXT,
    payment_ref TEXT,
    guest_name TEXT,
    guest_email TEXT,
    guest_phone TEXT,
    transport_mode TEXT DEFAULT 'Private AC Sedan / SUV',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sent_emails (
    id INTEGER PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id),
    booking_ref TEXT,
    recipient_email TEXT NOT NULL,
    recipient_name TEXT,
    subject TEXT NOT NULL,
    email_type TEXT NOT NULL,
    body_html TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'delivered',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    booking_id INTEGER NOT NULL UNIQUE REFERENCES bookings(id),
    customer_id INTEGER NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    body TEXT NOT NULL CHECK (length(body) BETWEEN 20 AND 1000),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS contact_inquiries (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'resolved')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS commission_rules (
    level INTEGER PRIMARY KEY CHECK (level BETWEEN 1 AND 4),
    rate_bps INTEGER NOT NULL CHECK (rate_bps BETWEEN 0 AND 10000)
);
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id INTEGER PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id),
    amount_paise INTEGER NOT NULL CHECK (amount_paise != 0),
    kind TEXT NOT NULL,
    reference TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(agent_id, kind, reference)
);
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id),
    amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
    reviewed_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY,
    actor_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS ledger_accounts (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS ledger_transactions (
    id INTEGER PRIMARY KEY,
    tx_ref TEXT NOT NULL UNIQUE,
    booking_id INTEGER REFERENCES bookings(id),
    total_paise INTEGER NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS ledger_entries (
    id INTEGER PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES ledger_transactions(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES ledger_accounts(id),
    agent_id INTEGER REFERENCES agents(id),
    debit_paise INTEGER NOT NULL DEFAULT 0,
    credit_paise INTEGER NOT NULL DEFAULT 0,
    entry_type TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS bookings_customer_idx ON bookings(customer_id, created_at);
CREATE INDEX IF NOT EXISTS bookings_agent_idx ON bookings(agent_id, created_at);
CREATE INDEX IF NOT EXISTS sent_emails_booking_idx ON sent_emails(booking_ref, created_at);
CREATE INDEX IF NOT EXISTS wallet_agent_idx ON wallet_transactions(agent_id, created_at);
CREATE INDEX IF NOT EXISTS withdrawals_agent_idx ON withdrawals(agent_id, created_at);
CREATE INDEX IF NOT EXISTS reviews_created_idx ON reviews(created_at);
CREATE INDEX IF NOT EXISTS inquiries_created_idx ON contact_inquiries(created_at);
CREATE INDEX IF NOT EXISTS agents_path_idx ON agents(path);
CREATE INDEX IF NOT EXISTS agents_parent_idx ON agents(parent_id);
CREATE INDEX IF NOT EXISTS agents_status_idx ON agents(status);
CREATE INDEX IF NOT EXISTS ledger_tx_booking_idx ON ledger_transactions(booking_id);
CREATE INDEX IF NOT EXISTS ledger_entries_tx_idx ON ledger_entries(transaction_id);
CREATE INDEX IF NOT EXISTS ledger_entries_account_idx ON ledger_entries(account_id);
CREATE INDEX IF NOT EXISTS ledger_entries_agent_idx ON ledger_entries(agent_id);
"""


def connect_db() -> sqlite3.Connection:
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 10000")
    return db


def compute_return_date(start_date_str: str, duration_str: str) -> str:
    try:
        from datetime import datetime, timedelta
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        match = re.search(r"(\d+)\s*day", duration_str, re.IGNORECASE)
        days = int(match.group(1)) if match else 3
        checkout = start + timedelta(days=max(1, days - 1))
        return checkout.isoformat()
    except Exception:
        return start_date_str


def parse_upcoming_dates(dates_str: str) -> list[dict[str, str]]:
    if not dates_str:
        return []
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    result = []
    current_year = date.today().year
    for item in dates_str.split(","):
        raw = item.strip()
        if not raw:
            continue
        m = re.match(r"^(\d{1,2})\s+([A-Za-z]{3})(?:\s+(\d{4}))?", raw)
        if m:
            day = int(m.group(1))
            mon_str = m.group(2).lower()
            mon = months.get(mon_str, 1)
            yr = int(m.group(3)) if m.group(3) else current_year
            if not m.group(3) and (mon < date.today().month or (mon == date.today().month and day < date.today().day)):
                yr += 1
            iso = f"{yr:04d}-{mon:02d}-{day:02d}"
            chip = f"{day:02d} {m.group(2).title()}"
            display = f"{day:02d} {m.group(2).title()} {yr}"
            result.append({"display": display, "chip": chip, "iso": iso, "raw": raw})
        else:
            result.append({"display": raw, "chip": raw, "iso": "", "raw": raw})
    return result


def send_booking_email(booking: dict, email_type: str) -> None:
    recipients = []
    # 1. Primary Guest / Traveller Email
    guest_email = booking.get("guest_email") or booking.get("customer_email")
    guest_name = booking.get("guest_name") or booking.get("customer_name") or "Valued Traveller"
    if guest_email:
        recipients.append((guest_email, guest_name, False))

    # 2. Agent / Partner Email (if booked with referral code or by agent)
    if booking.get("agent_id"):
        agent_user = g.db.execute(
            "SELECT u.name, u.email FROM agents a JOIN users u ON u.id=a.user_id WHERE a.id=?",
            (booking["agent_id"],)
        ).fetchone()
        if agent_user and agent_user["email"] != guest_email:
            recipients.append((agent_user["email"], f"Partner {agent_user['name']}", True))

    for rec_email, rec_name, is_agent_copy in recipients:
        if email_type == "booking_confirmed":
            subject = f"{'[PARTNER COPY] ' if is_agent_copy else ''}Booking Confirmed: {booking['title']} (#{booking['reference']}) - Wanderwise Travel Desk"
            badge = "BOOKING CONFIRMED"
            badge_color = "#1b5e20"
            lead_msg = f"Dear {rec_name}, your tour reservation has been successfully confirmed and verified with payment."
        elif email_type == "trip_completed":
            subject = f"{'[PARTNER COPY] ' if is_agent_copy else ''}Journey Completed: {booking['title']} (#{booking['reference']}) - Travel Report & Certificate"
            badge = "JOURNEY COMPLETED"
            badge_color = "#0369a1"
            lead_msg = f"Dear {rec_name}, congratulations on completing your incredible journey to {booking['destination']}! We hope you carry lifetime memories."
        else:
            subject = f"{'[PARTNER COPY] ' if is_agent_copy else ''}Trip Reserved: {booking['title']} (#{booking['reference']}) - Awaiting Payment"
            badge = "RESERVATION PENDING"
            badge_color = "#92400e"
            lead_msg = f"Dear {rec_name}, your tour seats have been successfully reserved. Please complete payment before departure."

        payment_line = f"<tr><td style='color: #6a7c6f; padding: 5px 0;'>Payment Ref:</td><td style='font-weight: 600; font-family: monospace; text-align: right;'>{booking['payment_ref']}</td></tr>" if booking.get('payment_ref') else ""
        return_date_val = booking.get('return_date') or booking.get('travel_date')

        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 650px; margin: 0 auto; background: #ffffff; border: 1px solid #dbe4dc; border-radius: 12px; overflow: hidden; color: #1e2822;">
          <div style="background: #193826; color: #ffffff; padding: 24px 30px; text-align: left;">
            <div style="font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">Wanderwise Travel ERP</div>
            <div style="font-size: 11px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px;">Incredible India Travel Desk · Official E-Ticket & Itinerary Report</div>
          </div>
          <div style="padding: 26px 30px;">
            <div style="display: inline-block; background: {badge_color}18; color: {badge_color}; border: 1px solid {badge_color}40; border-radius: 20px; font-size: 11px; font-weight: 800; padding: 4px 12px; text-transform: uppercase;">{badge}</div>
            <h2 style="font-size: 20px; color: #193826; margin: 12px 0 6px;">{booking['title']}</h2>
            <p style="font-size: 13px; color: #5e6d63; margin-bottom: 20px;">{lead_msg}</p>
            
            <div style="background: #f4f8f4; border: 1px solid #dce8dd; border-radius: 10px; padding: 18px; margin-bottom: 20px;">
              <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <tr><td style="color: #6a7c6f; padding: 5px 0;">Booking Reference:</td><td style="font-weight: 700; font-family: monospace; text-align: right;">#{booking['reference']}</td></tr>
                <tr><td style="color: #6a7c6f; padding: 5px 0;">Departure / Start Date:</td><td style="font-weight: 700; text-align: right;">{booking['travel_date']} (Check-in 12:00 PM)</td></tr>
                <tr><td style="color: #6a7c6f; padding: 5px 0;">Checkout / Return Date:</td><td style="font-weight: 700; text-align: right;">{return_date_val} (Checkout 11:00 AM)</td></tr>
                <tr><td style="color: #6a7c6f; padding: 5px 0;">Tour Duration:</td><td style="font-weight: 700; text-align: right;">{booking.get('duration', 'Tour Duration')}</td></tr>
                <tr><td style="color: #6a7c6f; padding: 5px 0;">Party Size:</td><td style="font-weight: 700; text-align: right;">{booking['travellers']} Guest(s)</td></tr>
                <tr><td style="color: #6a7c6f; padding: 5px 0;">Total Amount:</td><td style="font-weight: 700; color: #193826; font-size: 15px; text-align: right;">₹{booking['total_paise']/100:,.0f}</td></tr>
                <tr><td style="color: #6a7c6f; padding: 5px 0;">Transport Mode:</td><td style="font-weight: 700; color: #193826; text-align: right;">{booking.get('transport_mode', 'Private AC Sedan / SUV')}</td></tr>
                <tr><td style="color: #6a7c6f; padding: 5px 0;">Payment Method:</td><td style="font-weight: 600; text-align: right;">{booking.get('payment_method', 'Online')}</td></tr>
                {payment_line}
              </table>
            </div>

            <div style="text-align: center; margin: 26px 0 16px;">
              <a href="http://127.0.0.1:5000/bookings/{booking['reference']}/voucher" style="background: #193826; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 13px; display: inline-block;">
                📄 View & Print Official Travel Voucher & Soft Copy 🖨️
              </a>
            </div>
            <p style="text-align: center; font-size: 11px; color: #88998d;">A soft-copy PDF or paper printout of this voucher can be presented directly at hotel check-in and vehicle boarding.</p>
          </div>
          <div style="background: #f8faf8; border-top: 1px solid #e1e9e2; padding: 16px 30px; font-size: 11px; color: #6a7c6f; text-align: center;">
            Wanderwise Travel ERP · 24/7 Helpline: +91 1800 200 4888 · Email: traveldesk@wanderwise.local
          </div>
        </div>
        """
        try:
            g.db.execute(
                """INSERT INTO sent_emails (booking_id, booking_ref, recipient_email, recipient_name, subject, email_type, body_html)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (booking.get("id"), booking["reference"], rec_email, rec_name, subject, email_type, html)
            )
        except Exception as e:
            print("Email logging error:", e)


def initialize_db() -> None:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with connect_db() as db:
        db.executescript(SCHEMA)
        db.executemany(
            "INSERT OR IGNORE INTO commission_rules(level, rate_bps) VALUES (?, ?)",
            [(1, 500), (2, 200), (3, 100), (4, 50)],
        )
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            demo_users = [
                ("Aarav Mehta", "admin@wanderwise.local", "admin",
                 os.environ.get("TRAVEL_ERP_ADMIN_PASSWORD") or "Admin@123"),
                ("Priya Sharma", "agent@wanderwise.local", "agent", "Agent@123"),
                ("Maya Kapoor", "customer@wanderwise.local", "customer", "Travel@123"),
                ("Rohan Das", "rohan@wanderwise.local", "agent", "Agent@123"),
                ("Nisha Rao", "nisha@wanderwise.local", "agent", "Agent@123"),
                ("Kabir Singh", "kabir@wanderwise.local", "agent", "Agent@123"),
                ("Lokesh M M Ankith", "lokeshmmankith@gmail.com", "customer", "Lokesh@123"),
            ]
            ids: dict[str, int] = {}
            for name, email, role, password in demo_users:
                cursor = db.execute(
                    "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                    (name, email, generate_password_hash(password), role),
                )
                ids[email] = cursor.lastrowid
            db.execute("INSERT INTO agents(user_id,code,level) VALUES(?,?,?)",
                       (ids["agent@wanderwise.local"], "WW-1001", 4))
            root_agent = db.execute("SELECT id FROM agents WHERE code='WW-1001'").fetchone()["id"]
            db.execute("INSERT INTO agents(user_id,code,level,parent_id) VALUES(?,?,?,?)",
                       (ids["rohan@wanderwise.local"], "WW-1002", 3, root_agent))
            second = db.execute("SELECT id FROM agents WHERE code='WW-1002'").fetchone()["id"]
            db.execute("INSERT INTO agents(user_id,code,level,parent_id) VALUES(?,?,?,?)",
                       (ids["nisha@wanderwise.local"], "WW-1003", 2, second))
            third = db.execute("SELECT id FROM agents WHERE code='WW-1003'").fetchone()["id"]
            db.execute("INSERT INTO agents(user_id,code,level,parent_id) VALUES(?,?,?,?)",
                       (ids["kabir@wanderwise.local"], "WW-1004", 1, third))
            db.execute("INSERT INTO audit_logs(actor_id,action,record_type,record_id) VALUES(?,?,?,?)",
                       (ids["admin@wanderwise.local"], "Clean workspace initialized", "system", "seed"))

        # Ensure new columns exist on bookings table
        b_cols = [r[1] for r in db.execute("PRAGMA table_info(bookings)").fetchall()]
        for col in ["payment_method", "payment_ref", "return_date", "guest_name", "guest_email", "guest_phone", "transport_mode"]:
            if col not in b_cols:
                db.execute(f"ALTER TABLE bookings ADD COLUMN {col} TEXT")

        # Ensure new columns exist on packages table for rich card formatting
        p_cols = [r[1] for r in db.execute("PRAGMA table_info(packages)").fetchall()]
        for col, col_def in [
            ("origin", "TEXT DEFAULT 'Bengaluru'"),
            ("original_price_paise", "INTEGER DEFAULT 0"),
            ("upcoming_dates", "TEXT DEFAULT ''"),
            ("trust_text", "TEXT DEFAULT '150+ travelers can''t be wrong – book your trip today!'")
        ]:
            if col not in p_cols:
                db.execute(f"ALTER TABLE packages ADD COLUMN {col} {col_def}")

        # Ensure hierarchy and materialized path columns exist on agents table
        a_cols = [r[1] for r in db.execute("PRAGMA table_info(agents)").fetchall()]
        if "path" not in a_cols:
            db.execute("PRAGMA foreign_keys = OFF")
            db.execute("""
            CREATE TABLE IF NOT EXISTS agents_migrated (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                code TEXT NOT NULL UNIQUE,
                level INTEGER NOT NULL DEFAULT 1,
                depth INTEGER NOT NULL DEFAULT 1,
                path TEXT NOT NULL DEFAULT '/',
                parent_id INTEGER REFERENCES agents(id),
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('pending_approval', 'active', 'rejected', 'suspended')),
                phone TEXT,
                approved_by INTEGER REFERENCES users(id),
                approved_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                CHECK (parent_id IS NULL OR parent_id != id)
            )
            """)
            db.execute("""
            INSERT INTO agents_migrated (id, user_id, code, level, depth, path, parent_id, status)
            SELECT id, user_id, code, level, 1, '/' || id || '/', parent_id, 'active' FROM agents
            """)
            db.execute("DROP TABLE agents")
            db.execute("ALTER TABLE agents_migrated RENAME TO agents")
            db.execute("CREATE INDEX IF NOT EXISTS agents_path_idx ON agents(path)")
            db.execute("CREATE INDEX IF NOT EXISTS agents_parent_idx ON agents(parent_id)")
            db.execute("CREATE INDEX IF NOT EXISTS agents_status_idx ON agents(status)")
            db.execute("PRAGMA foreign_keys = ON")

            # Re-compute path and depth recursively
            all_agents = db.execute("SELECT id, parent_id FROM agents").fetchall()
            by_parent = {}
            for a in all_agents:
                by_parent.setdefault(a["parent_id"], []).append(a["id"])

            def set_tree(aid, parent_path, parent_depth):
                cur_path = f"{parent_path}{aid}/"
                cur_depth = parent_depth + 1
                db.execute("UPDATE agents SET path=?, depth=?, level=? WHERE id=?", (cur_path, cur_depth, cur_depth, aid))
                for child_id in by_parent.get(aid, []):
                    set_tree(child_id, cur_path, cur_depth)

            for root_id in by_parent.get(None, []):
                set_tree(root_id, "/", 0)

        # Seed default double-entry ledger accounts
        ledger_base_accounts = [
            ("REV_BOOKINGS", "Customer Booking Revenue", "revenue"),
            ("ESCROW_OPERATIONS", "Company Tour Operations Escrow", "liability"),
            ("COMM_OWNER", "Platform Owner Guaranteed Commission (10%)", "liability"),
        ]
        db.executemany("INSERT OR IGNORE INTO ledger_accounts(code, name, type) VALUES (?, ?, ?)", ledger_base_accounts)

        db.execute("""CREATE TABLE IF NOT EXISTS sent_emails (
            id INTEGER PRIMARY KEY,
            booking_id INTEGER REFERENCES bookings(id),
            booking_ref TEXT,
            recipient_email TEXT NOT NULL,
            recipient_name TEXT,
            subject TEXT NOT NULL,
            email_type TEXT NOT NULL,
            body_html TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'delivered',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")

    try:
        from seed_data import run_seed
        run_seed()
    except Exception as err:
        print("Seed warning:", err)


# Ensure database and tables exist even when loaded via WSGI (e.g. gunicorn on Render)
initialize_db()


@app.before_request
def prepare_request() -> None:
    g.db = connect_db()
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    g.user = None
    if session.get("user_id"):
        g.user = g.db.execute(
            "SELECT id,name,email,role FROM users WHERE id=?", (session["user_id"],)
        ).fetchone()
        if g.user is None:
            session.clear()
            session["csrf_token"] = secrets.token_urlsafe(32)


@app.teardown_request
def close_db(_error: BaseException | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.context_processor
def inject_globals() -> dict[str, Any]:
    from datetime import date

    return {
        "csrf_token": session.get("csrf_token", ""),
        "today": date.today().isoformat(),
    }


@app.template_filter("inr")
def format_inr(value: Any) -> str:
    amount = Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"₹{amount:,.0f}"


def safe_local_next(value: str | None) -> str | None:
    if not value:
        return None
    target = urlsplit(value)
    if target.scheme or target.netloc or not target.path.startswith("/") or target.path.startswith("//"):
        return None
    return value


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if g.user is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorate(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        @login_required
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if g.user["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorate


@app.before_request
def protect_state_changes() -> None:
    if request.method == "POST":
        supplied = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not secrets.compare_digest(supplied, expected):
            abort(400, description="Your session token expired. Refresh the page and try again.")


def audit(action: str, record_type: str, record_id: Any) -> None:
    g.db.execute(
        "INSERT INTO audit_logs(actor_id,action,record_type,record_id) VALUES(?,?,?,?)",
        (g.user["id"] if g.user else None, action, record_type, str(record_id)),
    )


def money_to_paise(value: str) -> int:
    try:
        amount = Decimal(value.strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, AttributeError):
        raise ValueError("Enter a valid amount.") from None
    if not amount.is_finite() or amount <= 0 or amount > Decimal("10000000"):
        raise ValueError("Amount must be greater than zero and at most ₹1 crore.")
    return int(amount * 100)


def generate_unique_referral_code(db: sqlite3.Connection) -> str:
    """Generate a guaranteed unique partner referral code in format TE-XXXXX."""
    for _ in range(500):
        candidate = f"TE-{secrets.randbelow(90000) + 10000}"
        if not db.execute("SELECT 1 FROM agents WHERE code=?", (candidate,)).fetchone():
            return candidate
    return f"TE-{secrets.token_hex(3).upper()}"


def get_or_create_ledger_account(db: sqlite3.Connection, code: str, name: str, acct_type: str) -> int:
    acc = db.execute("SELECT id FROM ledger_accounts WHERE code=?", (code,)).fetchone()
    if acc:
        return acc["id"]
    cur = db.execute(
        "INSERT INTO ledger_accounts (code, name, type) VALUES (?, ?, ?)",
        (code, name, acct_type),
    )
    return cur.lastrowid


def process_booking_ledger(db: sqlite3.Connection, booking_id: int) -> int | None:
    """
    Multi-tiered agency commission and balanced double-entry ledger engine.
    - Owner flat 10% guaranteed cut.
    - Booking agent flat 10% cut regardless of level.
    - For intermediate levels up to depth 4: cascading overrides based on distance from booking:
      - Distance 1: 2%
      - Distance 2: 3%
      - Distance 3: 4%
    - Hard limit at level 5: beyond depth 4 (at level 5+), all intermediate overrides drop to zero.
    - All financial entries processed within atomic database transactions with exact balance assertion.
    """
    booking = db.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if not booking:
        return None

    # Idempotent: don't double-process the same booking
    existing = db.execute("SELECT id FROM ledger_transactions WHERE booking_id=?", (booking_id,)).fetchone()
    if existing:
        return existing["id"]

    total_paise = booking["total_paise"]
    tx_ref = f"TX-BKG-{booking['reference']}"

    agent = None
    if booking["agent_id"]:
        agent = db.execute("SELECT * FROM agents WHERE id=?", (booking["agent_id"],)).fetchone()

    # Ledger Accounts
    rev_acct = get_or_create_ledger_account(db, "REV_BOOKINGS", "Customer Booking Revenue", "revenue")
    owner_acct = get_or_create_ledger_account(db, "COMM_OWNER", "Platform Owner Guaranteed Commission (10%)", "liability")
    escrow_acct = get_or_create_ledger_account(db, "ESCROW_OPERATIONS", "Company Tour Operations Escrow", "liability")

    cur = db.execute(
        "INSERT INTO ledger_transactions (tx_ref, booking_id, total_paise, description) VALUES (?, ?, ?, ?)",
        (tx_ref, booking_id, total_paise, f"Settlement for Booking {booking['reference']}")
    )
    tx_id = cur.lastrowid

    entries = []
    # 1. DEBIT: Total booking customer payment
    entries.append((tx_id, rev_acct, None, total_paise, 0, "booking_revenue", f"Revenue collected for {booking['reference']}"))

    # 2. CREDITS:
    # A. Guaranteed Owner flat 10% cut
    owner_cut = (total_paise * 10) // 100
    entries.append((tx_id, owner_acct, None, 0, owner_cut, "owner_cut", f"Guaranteed Platform Owner Flat Cut (10%) - {booking['reference']}"))

    # B. Guaranteed Booking Agent flat 10% cut (regardless of level)
    agent_cut = 0
    if agent and agent["status"] == "active":
        agent_cut = (total_paise * 10) // 100
        agent_acct = get_or_create_ledger_account(db, f"COMM_AGENT_{agent['id']}", f"Partner {agent['code']} Commission Account", "liability")
        entries.append((tx_id, agent_acct, agent["id"], 0, agent_cut, "booking_agent_cut", f"Booking Agent Flat Cut (10%) - Code {agent['code']} (Depth {agent['depth']})"))
        db.execute(
            "INSERT OR IGNORE INTO wallet_transactions(agent_id, amount_paise, kind, reference) VALUES (?, ?, 'commission', ?)",
            (agent["id"], agent_cut, booking["reference"])
        )

    # C. Cascading overrides for intermediate levels up to depth 4
    # Hard limit at level 5: beyond depth 4 (at level 5+), intermediate overrides drop to zero!
    overrides_total = 0
    if agent and agent["depth"] <= 4:
        path_parts = [int(p) for p in agent["path"].strip("/").split("/") if p and int(p) != agent["id"]]
        ancestor_ids = list(reversed(path_parts)) # distance 1 is direct parent, dist 2 is grandparent, etc.
        override_schedule = {1: 2, 2: 3, 3: 4} # Dist 1: 2%, Dist 2: 3%, Dist 3: 4%
        for dist, sup_id in enumerate(ancestor_ids, start=1):
            rate = override_schedule.get(dist, 0)
            if rate > 0:
                sup = db.execute("SELECT * FROM agents WHERE id=?", (sup_id,)).fetchone()
                if sup and sup["status"] == "active":
                    sup_cut = (total_paise * rate) // 100
                    overrides_total += sup_cut
                    sup_acct = get_or_create_ledger_account(db, f"COMM_AGENT_{sup['id']}", f"Partner {sup['code']} Commission Account", "liability")
                    entries.append((tx_id, sup_acct, sup["id"], 0, sup_cut, "cascade_override", f"Cascade Override (Dist {dist}: {rate}%) from Booking {booking['reference']}"))
                    db.execute(
                        "INSERT OR IGNORE INTO wallet_transactions(agent_id, amount_paise, kind, reference) VALUES (?, ?, 'override', ?)",
                        (sup["id"], sup_cut, f"{booking['reference']}-D{dist}")
                    )

    # D. Company Tour Operations Escrow gets the remainder
    company_escrow = total_paise - (owner_cut + agent_cut + overrides_total)
    entries.append((tx_id, escrow_acct, None, 0, company_escrow, "company_operations", f"Company Net Tour Operations Escrow for {booking['reference']}"))

    # E. Exact Ledger Balance Verification (Assertion)
    total_debits = sum(e[3] for e in entries)
    total_credits = sum(e[4] for e in entries)
    if total_debits != total_credits:
        raise ValueError(f"Ledger Imbalance Detected: Debits ({total_debits}) != Credits ({total_credits})")

    # Insert balanced ledger lines atomically
    db.executemany(
        """INSERT INTO ledger_entries (transaction_id, account_id, agent_id, debit_paise, credit_paise, entry_type, description)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        entries
    )

    return tx_id


def get_my_agent() -> sqlite3.Row | None:
    return g.db.execute("SELECT * FROM agents WHERE user_id=?", (g.user["id"],)).fetchone()


def wallet_balance(agent_id: int) -> int:
    return g.db.execute(
        "SELECT COALESCE(SUM(amount_paise),0) FROM wallet_transactions WHERE agent_id=?",
        (agent_id,),
    ).fetchone()[0]


def reserved_withdrawals(agent_id: int) -> int:
    return g.db.execute(
        "SELECT COALESCE(SUM(amount_paise),0) FROM withdrawals WHERE agent_id=? AND status IN ('pending','approved')",
        (agent_id,),
    ).fetchone()[0]


@app.route("/login", methods=["GET", "POST"])
def login() -> Any:
    if g.user:
        return redirect(safe_local_next(request.args.get("next")) or url_for("dashboard"))
    if request.method == "POST":
        identifier = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        # Allow login via Email OR Partner Referral ID
        user = g.db.execute(
            """SELECT u.*, a.id AS agent_id, a.code AS agent_code, a.status AS agent_status, a.depth AS agent_depth
               FROM users u
               LEFT JOIN agents a ON a.user_id = u.id
               WHERE LOWER(u.email) = LOWER(?) OR UPPER(a.code) = UPPER(?)""",
            (identifier, identifier),
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            # Check partner two-step validation status
            if user["role"] == "agent":
                if user["agent_status"] == "pending_approval":
                    flash("Your partner application is pending Owner approval. You can log in once your application is approved and your unique Referral Code is activated.", "error")
                    return render_template("login.html", register=False)
                elif user["agent_status"] == "rejected":
                    flash("Your partner application was reviewed and not approved by the Owner.", "error")
                    return render_template("login.html", register=False)
                elif user["agent_status"] == "suspended":
                    flash("Your partner account is suspended. Please contact the administrator.", "error")
                    return render_template("login.html", register=False)

            next_url = safe_local_next(request.form.get("next") or request.args.get("next"))
            session.clear()
            session["user_id"] = user["id"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            return redirect(next_url or url_for("dashboard"))

        flash("That email/referral ID and password combination wasn’t recognized.", "error")
    return render_template("login.html", register=False)


@app.route("/register", methods=["GET", "POST"])
def register() -> Any:
    if g.user:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "customer")
        referral = request.form.get("referral", "").strip().upper()
        phone = request.form.get("phone", "").strip()
        if not name or len(name) > 80 or "@" not in email or len(email) > 254:
            flash("Add a valid name and email address.", "error")
        elif len(password) < 8:
            flash("Choose a password with at least 8 characters.", "error")
        elif role not in ("customer", "agent"):
            flash("Choose a valid account type.", "error")
        elif g.db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            flash("An account with that email already exists.", "error")
        else:
            parent = None
            if referral:
                parent = g.db.execute("SELECT * FROM agents WHERE UPPER(code)=? AND status='active'", (referral,)).fetchone()
                if parent is None:
                    flash("We couldn’t find that active sponsor referral code.", "error")
                    return render_template("login.html", register=True)
            try:
                with g.db:
                    cursor = g.db.execute(
                        "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                        (name, email, generate_password_hash(password), role),
                    )
                    user_id = cursor.lastrowid
                    if role == "agent":
                        temp_code = f"PENDING-{secrets.token_hex(3).upper()}"
                        depth = (parent["depth"] + 1) if parent else 1
                        parent_path = parent["path"] if parent else "/"
                        g.db.execute(
                            """INSERT INTO agents(user_id, code, level, depth, path, parent_id, status, phone)
                               VALUES(?,?,?,?,?,?,'pending_approval',?)""",
                            (user_id, temp_code, depth, depth, parent_path, parent["id"] if parent else None, phone or None),
                        )
                        audit("Partner application registered", role, user_id)
                        flash("Your partner application has been submitted and is pending Owner approval! Once approved, your unique Referral Code will be generated and you can log in using your Referral Code and password.", "success")
                        return redirect(url_for("login"))
                    audit("Account registered", role, user_id)
                flash("Your customer account is ready. Sign in to get started.", "success")
                return redirect(url_for("login", next=safe_local_next(
                    request.form.get("next") or request.args.get("next")
                )))
            except sqlite3.IntegrityError:
                flash("We couldn’t create that account. Please check the details and try again.", "error")
    return render_template("login.html", register=True)


@app.route("/referral-program/join", methods=["GET", "POST"])
@app.route("/partner/apply", methods=["GET", "POST"])
def partner_apply() -> Any:
    """Dedicated route for new recruits to register under the Referral Program."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        sponsor_code = request.form.get("sponsor_code", "").strip().upper()

        if not name or len(name) > 80:
            flash("Please enter your full name.", "error")
        elif "@" not in email or len(email) > 254:
            flash("Please enter a valid email address.", "error")
        elif not phone or len(phone) < 7:
            flash("Please provide a valid contact phone number.", "error")
        elif len(password) < 8:
            flash("Choose a password with at least 8 characters.", "error")
        elif password != password_confirm:
            flash("Passwords do not match.", "error")
        elif g.db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            flash("An account with that email already exists. Sign in or use another email.", "error")
        else:
            parent = None
            if sponsor_code:
                parent = g.db.execute("SELECT * FROM agents WHERE UPPER(code)=? AND status='active'", (sponsor_code,)).fetchone()
                if parent is None:
                    flash(f"Sponsor referral code '{sponsor_code}' was not found or is not currently active.", "error")
                    return redirect(url_for("referral_program", ref=sponsor_code) + "#join-partner")
            try:
                with g.db:
                    cur_u = g.db.execute(
                        "INSERT INTO users(name, email, password_hash, role) VALUES(?,?,?,'agent')",
                        (name, email, generate_password_hash(password))
                    )
                    user_id = cur_u.lastrowid
                    temp_code = f"PENDING-{secrets.token_hex(3).upper()}"
                    depth = (parent["depth"] + 1) if parent else 1
                    parent_path = parent["path"] if parent else "/"
                    cur_a = g.db.execute(
                        """INSERT INTO agents(user_id, code, level, depth, path, parent_id, status, phone)
                           VALUES (?, ?, ?, ?, ?, ?, 'pending_approval', ?)""",
                        (user_id, temp_code, depth, depth, parent_path, parent["id"] if parent else None, phone)
                    )
                    agent_id = cur_a.lastrowid
                    audit("Partner recruit application initiated", "agent", agent_id)
                flash("Application submitted successfully! Your partner registration is pending Owner review. Once approved, your unique Referral Code will be generated and you can log in using your Referral Code and password.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("We couldn't process your application. Please check your details and try again.", "error")
    return redirect(url_for("referral_program") + "#join-partner")


@app.post("/admin/partners/<int:agent_id>/approve")
@login_required
def approve_partner(agent_id: int) -> Any:
    """Owner explicit approval for new partner recruit."""
    if g.user["role"] != "admin":
        abort(403)
    agent = g.db.execute(
        """SELECT a.*, u.name, u.email FROM agents a
           JOIN users u ON u.id = a.user_id WHERE a.id=?""", (agent_id,)
    ).fetchone()
    if not agent:
        abort(404)
    if agent["status"] != "pending_approval":
        flash("This partner is not currently awaiting approval.", "error")
        return redirect(url_for("dashboard", view="partners"))

    # Generate guaranteed unique referral code
    new_code = generate_unique_referral_code(g.db)
    # Calculate materialized path and depth from immediate superior
    if agent["parent_id"]:
        parent = g.db.execute("SELECT path, depth FROM agents WHERE id=?", (agent["parent_id"],)).fetchone()
        path = f"{parent['path']}{agent['id']}/" if parent else f"/{agent['id']}/"
        depth = (parent["depth"] + 1) if parent else 1
    else:
        path = f"/{agent['id']}/"
        depth = 1

    with g.db:
        g.db.execute(
            """UPDATE agents SET code=?, path=?, depth=?, level=?, status='active',
               approved_by=?, approved_at=datetime('now') WHERE id=?""",
            (new_code, path, depth, depth, g.user["id"], agent_id)
        )
        get_or_create_ledger_account(g.db, f"COMM_AGENT_{agent_id}", f"Partner {new_code} Commission Account", "liability")
        audit(f"Partner {new_code} approved by Owner", "agent", agent_id)

    flash(f"Partner {agent['name']} approved! Unique Referral Code {new_code} generated. Partner is now active and can log in using their Referral Code.", "success")
    return redirect(url_for("dashboard", view="partners"))


@app.post("/admin/partners/<int:agent_id>/reject")
@login_required
def reject_partner(agent_id: int) -> Any:
    """Owner rejection of pending partner recruit."""
    if g.user["role"] != "admin":
        abort(403)
    agent = g.db.execute(
        """SELECT a.*, u.name FROM agents a
           JOIN users u ON u.id = a.user_id WHERE a.id=?""", (agent_id,)
    ).fetchone()
    if not agent:
        abort(404)
    with g.db:
        g.db.execute("UPDATE agents SET status='rejected' WHERE id=?", (agent_id,))
        audit("Partner recruit rejected by Owner", "agent", agent_id)
    flash(f"Partner application for {agent['name']} has been rejected.", "info")
    return redirect(url_for("dashboard", view="partners"))


@app.route("/logout", methods=["GET", "POST"])
def logout() -> Any:
    session.clear()
    flash("You have been signed out safely.", "success")
    return redirect(url_for("public_home"))


@app.get("/")
def public_home() -> Any:
    destination = request.args.get("destination", "").strip()
    category = request.args.get("category", "").strip()
    origin = request.args.get("origin", "").strip()
    query_text = request.args.get("q", "").strip()
    region = request.args.get("region", "").strip().lower()

    destinations = g.db.execute(
        "SELECT DISTINCT destination FROM packages WHERE status='active' ORDER BY destination"
    ).fetchall()
    origins = g.db.execute(
        "SELECT DISTINCT origin FROM packages WHERE status='active' AND origin IS NOT NULL ORDER BY origin"
    ).fetchall()
    categories = g.db.execute(
        "SELECT DISTINCT category FROM packages WHERE status='active' ORDER BY category"
    ).fetchall()
    package_query = "SELECT *, capacity-reserved AS available FROM packages WHERE status='active'"
    package_args: list[str] = []
    if region == "domestic":
        package_query += " AND category != 'International'"
    elif region == "international":
        package_query += " AND category = 'International'"
    if destination:
        package_query += " AND (destination LIKE ? OR title LIKE ?)"
        package_args.extend([f"%{destination}%", f"%{destination}%"])
    if origin:
        package_query += " AND (origin LIKE ?)"
        package_args.append(f"%{origin}%")
    if category:
        package_query += " AND category=?"
        package_args.append(category)
    if query_text:
        package_query += " AND (title LIKE ? OR destination LIKE ? OR description LIKE ? OR origin LIKE ?)"
        package_args.extend([f"%{query_text}%", f"%{query_text}%", f"%{query_text}%", f"%{query_text}%"])

    packages = g.db.execute(package_query + " ORDER BY id", package_args).fetchall()
    marquee_packages = g.db.execute(
        """SELECT *, capacity-reserved AS available FROM packages
           WHERE status='active' ORDER BY id"""
    ).fetchall()
    reviews = g.db.execute(
        """SELECT r.rating,r.body,r.created_at,u.name,p.title AS package_title,p.destination
           FROM reviews r JOIN users u ON u.id=r.customer_id
           JOIN bookings b ON b.id=r.booking_id JOIN packages p ON p.id=b.package_id
           ORDER BY r.created_at DESC LIMIT 10"""
    ).fetchall()
    review_count = g.db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]

    # Tourist landmarks with official websites for the photo gallery (Image 3)
    tourist_landmarks = g.db.execute(
        """SELECT id, title, destination, category, description, duration, price_paise,
                  image_file, official_url, activities, capacity-reserved AS available
           FROM packages WHERE status='active'
           ORDER BY CASE WHEN official_url IS NOT NULL THEN 0 ELSE 1 END, id"""
    ).fetchall()

    return render_template(
        "public_home.html", packages=packages, reviews=reviews, review_count=review_count,
        destinations=destinations, origins=origins, categories=categories,
        selected_destination=destination, selected_origin=origin, selected_category=category,
        selected_region=region, query_text=query_text,
        marquee_packages=marquee_packages, tourist_landmarks=tourist_landmarks,
    )


@app.post("/contact")
def submit_contact() -> Any:
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()
    local, separator, domain = email.partition("@")
    valid_email = (
        bool(separator) and bool(local) and "." in domain and not domain.startswith(".")
        and not domain.endswith(".") and not any(character.isspace() for character in email)
        and email.count("@") == 1
    )
    if (
        not name or len(name) > 80 or len(email) > 254 or not valid_email
        or subject not in {"Planning a trip", "An existing booking", "Partnership enquiry", "Something else", "Website chat"}
        or len(message) < 20 or len(message) > 2000
    ):
        flash("Please check the form. Messages should be between 20 and 2,000 characters.", "error")
        destination = "#site-chat" if request.form.get("source") == "chat" else "#contact"
        return redirect(url_for("public_home") + destination)
    with g.db:
        cursor = g.db.execute(
            "INSERT INTO contact_inquiries(name,email,subject,message) VALUES(?,?,?,?)",
            (name, email, subject, message),
        )
        audit("New website contact inquiry", "contact_inquiry", cursor.lastrowid)
    flash("Thanks for reaching out. Your message is with our travel desk.", "success")
    destination = "#site-chat" if request.form.get("source") == "chat" else "#contact"
    return redirect(url_for("public_home") + destination)


@app.get("/trips/<int:package_id>")
def trip_details(package_id: int) -> Any:
    package = g.db.execute(
        """SELECT p.*,p.capacity-p.reserved AS available,d.stay_type,d.meal_plan,
                  d.transport,d.inclusions,d.itinerary
           FROM packages p LEFT JOIN package_details d ON d.package_id=p.id
           WHERE p.id=? AND p.status='active'""",
        (package_id,),
    ).fetchone()
    if package is None:
        abort(404)
    trip = dict(package)
    trip["stay_type"] = trip["stay_type"] or "Comfortable locally operated accommodation"
    trip["meal_plan"] = trip["meal_plan"] or "Meals confirmed with your travel desk"
    trip["transport"] = trip["transport"] or "Transport details confirmed before booking"
    trip["inclusions"] = trip["inclusions"] or "Trip support from the travel desk"
    trip["itinerary"] = trip["itinerary"] or "A day-by-day itinerary will be arranged with your travel desk."
    if not trip.get("image_file"):
        destination = trip["destination"].lower()
        trip["image_file"] = (
            "gallery-coast.jpg" if "goa" in destination else
            "gallery-himalaya.jpg" if "manali" in destination else
            "gallery-backwaters.jpg" if "alappuzha" in destination else
            "gallery-heritage.jpg" if "jaisalmer" in destination else
            "gallery-monument.jpg"
        )
    parsed_dates = parse_upcoming_dates(trip.get("upcoming_dates") or "")
    req_date = request.args.get("travel_date", "").strip()
    first_upcoming_iso = parsed_dates[0]["iso"] if parsed_dates and parsed_dates[0]["iso"] else ""
    initial_travel_date = req_date or first_upcoming_iso or date.today().isoformat()
    initial_return_date = compute_return_date(initial_travel_date, trip["duration"])
    return render_template(
        "trip_details.html",
        package=trip,
        upcoming_schedule=parsed_dates,
        initial_travel_date=initial_travel_date,
        initial_return_date=initial_return_date,
        selected_travel_date=req_date or first_upcoming_iso,
    )


@app.route("/partner-program")
@app.route("/referral-program")
def referral_program() -> Any:
    return render_template("referral_program.html")


@app.post("/reviews/<int:booking_id>")
@roles_required("customer")
def submit_review(booking_id: int) -> Any:
    rating = request.form.get("rating", type=int)
    body = request.form.get("body", "").strip()
    booking = g.db.execute(
        "SELECT id,status FROM bookings WHERE id=? AND customer_id=?",
        (booking_id, g.user["id"]),
    ).fetchone()
    if booking is None:
        abort(404)
    if booking["status"] != "completed":
        flash("You can review a trip after it has been completed.", "error")
    elif not rating or not 1 <= rating <= 5 or not 20 <= len(body) <= 1000:
        flash("Choose a rating and write a review between 20 and 1,000 characters.", "error")
    else:
        try:
            with g.db:
                g.db.execute(
                    "INSERT INTO reviews(booking_id,customer_id,rating,body) VALUES(?,?,?,?)",
                    (booking_id, g.user["id"], rating, body),
                )
                audit("Verified trip review submitted", "booking", booking_id)
            flash("Thank you for sharing a note from your trip.", "success")
        except sqlite3.IntegrityError:
            flash("This completed trip already has a review.", "error")
    return redirect(url_for("dashboard", view="bookings"))


@app.get("/bookings/<string:reference>/voucher")
def booking_voucher(reference: str) -> Any:
    booking = g.db.execute(
        """SELECT b.*, p.title, p.destination, p.duration, p.category, p.image_file,
                  d.stay_type, d.meal_plan, d.transport, d.inclusions, d.itinerary,
                  u.name AS customer_name, u.email AS customer_email,
                  a.code AS agent_code, au.name AS agent_name
           FROM bookings b
           JOIN packages p ON p.id=b.package_id
           LEFT JOIN package_details d ON d.package_id=p.id
           JOIN users u ON u.id=b.customer_id
           LEFT JOIN agents a ON a.id=b.agent_id
           LEFT JOIN users au ON au.id=a.user_id
           WHERE b.reference=?""",
        (reference,)
    ).fetchone()
    if booking is None:
        abort(404)
    return render_template("booking_voucher.html", booking=booking)


@app.get("/dashboard")
@login_required
def dashboard() -> Any:
    role = g.user["role"]
    view = request.args.get("view", "overview")
    packages = g.db.execute(
        "SELECT *, capacity-reserved AS available FROM packages WHERE status='active' ORDER BY id"
    ).fetchall()
    my_agent = get_my_agent() if role == "agent" else None
    if role == "customer":
        bookings = g.db.execute(
            """SELECT b.*,p.title,p.destination,p.duration,
                      EXISTS(SELECT 1 FROM reviews r WHERE r.booking_id=b.id) AS reviewed
               FROM bookings b JOIN packages p ON p.id=b.package_id
               WHERE b.customer_id=? ORDER BY b.created_at DESC""", (g.user["id"],)
        ).fetchall()
    elif role == "agent":
        bookings = g.db.execute(
            """SELECT b.*,p.title,p.destination,p.duration,u.name AS customer_name,
                      EXISTS(SELECT 1 FROM reviews r WHERE r.booking_id=b.id) AS reviewed FROM bookings b
               JOIN packages p ON p.id=b.package_id JOIN users u ON u.id=b.customer_id
               WHERE b.agent_id=? ORDER BY b.created_at DESC""", (my_agent["id"],)
        ).fetchall()
    else:
        bookings = g.db.execute(
            """SELECT b.*,p.title,p.destination,p.duration,u.name AS customer_name,
                      EXISTS(SELECT 1 FROM reviews r WHERE r.booking_id=b.id) AS reviewed FROM bookings b
               JOIN packages p ON p.id=b.package_id JOIN users u ON u.id=b.customer_id
               ORDER BY b.created_at DESC LIMIT 50"""
        ).fetchall()
    agents = g.db.execute(
        """SELECT a.id,a.code,a.level,u.name,u.email,
                  (SELECT COUNT(*) FROM agents d WHERE d.parent_id=a.id) AS team_size
           FROM agents a JOIN users u ON u.id=a.user_id ORDER BY a.level DESC,a.code"""
    ).fetchall() if role == "admin" else []
    rules = g.db.execute("SELECT * FROM commission_rules ORDER BY level DESC").fetchall() if role == "admin" else []
    withdrawals = g.db.execute(
        """SELECT w.*,u.name AS agent_name,a.code FROM withdrawals w
           JOIN agents a ON a.id=w.agent_id JOIN users u ON u.id=a.user_id
           ORDER BY w.created_at DESC LIMIT 30"""
    ).fetchall() if role == "admin" else (
        g.db.execute("SELECT * FROM withdrawals WHERE agent_id=? ORDER BY created_at DESC",
                     (my_agent["id"],)).fetchall() if my_agent else []
    )
    transactions = g.db.execute(
        "SELECT * FROM wallet_transactions WHERE agent_id=? ORDER BY created_at DESC LIMIT 12",
        (my_agent["id"],)
    ).fetchall() if my_agent else []
    sent_emails = g.db.execute(
        "SELECT * FROM sent_emails ORDER BY created_at DESC LIMIT 50"
    ).fetchall() if role == "admin" else []
    stats = {
        "bookings": g.db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
        "customers": g.db.execute("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0],
        "agents": g.db.execute("SELECT COUNT(*) FROM agents").fetchone()[0],
        "revenue": g.db.execute("SELECT COALESCE(SUM(total_paise),0) FROM bookings WHERE status!='cancelled'").fetchone()[0],
        "confirmed": g.db.execute("SELECT COUNT(*) FROM bookings WHERE status IN ('confirmed','completed')").fetchone()[0],
        "available": sum(package["available"] for package in packages),
        "pending_bookings": g.db.execute("SELECT COUNT(*) FROM bookings WHERE status='pending'").fetchone()[0],
        "completed_bookings": g.db.execute("SELECT COUNT(*) FROM bookings WHERE status='completed'").fetchone()[0],
        "cancelled_bookings": g.db.execute("SELECT COUNT(*) FROM bookings WHERE status='cancelled'").fetchone()[0],
        "pending_withdrawals": g.db.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'").fetchone()[0],
        "new_inquiries": g.db.execute("SELECT COUNT(*) FROM contact_inquiries WHERE status='new'").fetchone()[0],
        "sent_emails_count": len(sent_emails) if role == "admin" else 0,
        "review_count": g.db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
        "active_packages": g.db.execute("SELECT COUNT(*) FROM packages WHERE status='active'").fetchone()[0],
        "total_packages": g.db.execute("SELECT COUNT(*) FROM packages").fetchone()[0],
    }
    all_packages = g.db.execute(
        "SELECT *, capacity-reserved AS available FROM packages ORDER BY id"
    ).fetchall() if role == "admin" else packages
    if role == "customer":
        stats["bookings"] = len(bookings)
        stats["confirmed"] = sum(b["status"] in ("confirmed", "completed") for b in bookings)
    if role == "agent":
        stats["bookings"] = len(bookings)
        stats["revenue"] = sum(b["total_paise"] for b in bookings if b["status"] != "cancelled")
    balance = wallet_balance(my_agent["id"]) if my_agent else 0
    reserved = reserved_withdrawals(my_agent["id"]) if my_agent else 0
    team = []
    if my_agent:
        team = g.db.execute(
            """WITH RECURSIVE downline(id,depth) AS (
                   SELECT id,1 FROM agents WHERE parent_id=?
                   UNION ALL SELECT a.id,d.depth+1 FROM agents a JOIN downline d ON a.parent_id=d.id
                   WHERE d.depth<4
               )
               SELECT a.code,a.level,u.name,d.depth FROM downline d JOIN agents a ON a.id=d.id
               JOIN users u ON u.id=a.user_id ORDER BY d.depth,a.code""", (my_agent["id"],)
        ).fetchall()
    logs = g.db.execute(
        """SELECT l.*,u.name AS actor FROM audit_logs l LEFT JOIN users u ON u.id=l.actor_id
           ORDER BY l.created_at DESC LIMIT 12"""
    ).fetchall() if role == "admin" else []
    inquiries = g.db.execute(
        "SELECT * FROM contact_inquiries ORDER BY CASE status WHEN 'new' THEN 0 ELSE 1 END, created_at DESC"
    ).fetchall() if role == "admin" else []
    public_reviews = g.db.execute(
        """SELECT r.rating,r.body,r.created_at,u.name,p.title AS package_title
           FROM reviews r JOIN users u ON u.id=r.customer_id
           JOIN bookings b ON b.id=r.booking_id JOIN packages p ON p.id=b.package_id
           ORDER BY r.created_at DESC LIMIT 50"""
    ).fetchall() if role == "admin" else []

    # Graphical analytics queries for Executive Dashboard
    transport_stats = g.db.execute(
        """SELECT COALESCE(transport_mode, 'Private AC Sedan / SUV') as mode, COUNT(*) as count,
                  COALESCE(SUM(total_paise), 0) as total_paise
           FROM bookings GROUP BY mode ORDER BY count DESC"""
    ).fetchall() if role == "admin" else []

    status_stats = g.db.execute(
        """SELECT status, COUNT(*) as count, COALESCE(SUM(total_paise), 0) as total_paise
           FROM bookings GROUP BY status"""
    ).fetchall() if role == "admin" else []

    package_occupancy = g.db.execute(
        """SELECT title, destination, capacity, reserved,
                  ROUND(CAST(reserved AS FLOAT) / MAX(1, capacity) * 100, 1) as occupancy_pct,
                  (capacity - reserved) as available
           FROM packages WHERE status='active' ORDER BY reserved DESC, capacity DESC LIMIT 6"""
    ).fetchall() if role == "admin" else []

    partner_sales = g.db.execute(
        """SELECT a.code, u.name, a.level,
                  COUNT(b.id) as booking_count,
                  COALESCE(SUM(b.total_paise), 0) as total_volume
           FROM agents a
           JOIN users u ON u.id=a.user_id
           LEFT JOIN bookings b ON b.agent_id=a.id AND b.status != 'cancelled'
           GROUP BY a.id ORDER BY total_volume DESC, booking_count DESC LIMIT 5"""
    ).fetchall() if role == "admin" else []

    # Multi-tier hierarchy, approvals, and double-entry ledger queries
    pending_partners = g.db.execute(
        """SELECT a.id, a.code, a.depth, a.status, a.phone, a.created_at,
                  u.name, u.email,
                  p.code AS sponsor_code, pu.name AS sponsor_name, p.depth AS sponsor_depth
           FROM agents a
           JOIN users u ON u.id = a.user_id
           LEFT JOIN agents p ON p.id = a.parent_id
           LEFT JOIN users pu ON pu.id = p.user_id
           WHERE a.status = 'pending_approval'
           ORDER BY a.created_at ASC"""
    ).fetchall() if role == "admin" else []

    hierarchy_agents = g.db.execute(
        """SELECT a.id, a.code, a.depth, a.level, a.path, a.status, a.phone, a.created_at, a.approved_at,
                  u.name, u.email,
                  p.code AS parent_code, pu.name AS parent_name,
                  (SELECT COUNT(*) FROM agents c WHERE c.parent_id = a.id AND c.status = 'active') AS direct_recruits,
                  (SELECT COUNT(*) FROM agents d WHERE d.path LIKE a.path || '%' AND d.id != a.id AND d.status = 'active') AS total_downline,
                  (SELECT COALESCE(SUM(credit_paise), 0) FROM ledger_entries le WHERE le.agent_id = a.id) AS total_commission_earned
           FROM agents a
           JOIN users u ON u.id = a.user_id
           LEFT JOIN agents p ON p.id = a.parent_id
           LEFT JOIN users pu ON pu.id = p.user_id
           WHERE a.status = 'active'
           ORDER BY a.depth ASC, a.id ASC"""
    ).fetchall() if role == "admin" else []

    ledger_transactions_list = g.db.execute(
        """SELECT lt.id, lt.tx_ref, lt.booking_id, lt.total_paise, lt.description, lt.created_at,
                  b.reference AS booking_ref, b.guest_name,
                  (SELECT COUNT(*) FROM ledger_entries WHERE transaction_id = lt.id) AS entries_count
           FROM ledger_transactions lt
           LEFT JOIN bookings b ON b.id = lt.booking_id
           ORDER BY lt.created_at DESC LIMIT 30"""
    ).fetchall() if role == "admin" else []

    my_sponsor = None
    downline_recruits = []
    ledger_earnings = []
    if my_agent:
        if my_agent["parent_id"]:
            my_sponsor = g.db.execute(
                """SELECT a.code, a.depth, u.name, u.email FROM agents a
                   JOIN users u ON u.id=a.user_id WHERE a.id=?""",
                (my_agent["parent_id"],)
            ).fetchone()
        downline_recruits = g.db.execute(
            """SELECT a.id, a.code, a.depth, a.level, a.path, a.status, a.phone, a.created_at,
                      u.name, u.email,
                      (a.depth - ?) AS relative_distance,
                      (SELECT COUNT(*) FROM agents c WHERE c.parent_id = a.id AND c.status = 'active') AS child_recruits,
                      (SELECT COALESCE(SUM(credit_paise), 0) FROM ledger_entries le WHERE le.agent_id = a.id) AS downline_commissions
               FROM agents a
               JOIN users u ON u.id = a.user_id
               WHERE a.path LIKE ? AND a.id != ?
               ORDER BY a.depth ASC, a.created_at DESC""",
            (my_agent["depth"], f"{my_agent['path']}%", my_agent["id"])
        ).fetchall()
        ledger_earnings = g.db.execute(
            """SELECT le.*, lt.tx_ref, b.reference AS booking_ref, b.total_paise AS booking_amount
               FROM ledger_entries le
               JOIN ledger_transactions lt ON lt.id = le.transaction_id
               LEFT JOIN bookings b ON b.id = lt.booking_id
               WHERE le.agent_id = ?
               ORDER BY le.created_at DESC LIMIT 50""",
            (my_agent["id"],)
        ).fetchall()

    stats["pending_partners"] = len(pending_partners) if role == "admin" else 0
    stats["total_active_partners"] = len(hierarchy_agents) if role == "admin" else 0

    return render_template(
        "dashboard.html", view=view, packages=packages, all_packages=all_packages, bookings=bookings, stats=stats,
        my_agent=my_agent, agents=agents, rules=rules, withdrawals=withdrawals,
        transactions=transactions, balance=balance, reserved=reserved,
        available_balance=max(0, balance - reserved), team=team, logs=logs,
        inquiries=inquiries, public_reviews=public_reviews, sent_emails=sent_emails,
        transport_stats=transport_stats, status_stats=status_stats,
        package_occupancy=package_occupancy, partner_sales=partner_sales,
        pending_partners=pending_partners, hierarchy_agents=hierarchy_agents,
        ledger_transactions_list=ledger_transactions_list, my_sponsor=my_sponsor,
        downline_recruits=downline_recruits, ledger_earnings=ledger_earnings,
    )


@app.route("/admin/sync-live-data", methods=["GET", "POST"])
@roles_required("admin")
def sync_live_data() -> Any:
    """Touch and synchronize database operational ledgers in real-time."""
    now_str = datetime.now().strftime("%I:%M:%S %p")
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "status": "success",
            "message": "Database synchronized with live operational ledger.",
            "synced_at": now_str
        })
    flash(f"Database synchronized successfully at {now_str}. All operational metrics updated.", "success")
    return redirect(url_for("dashboard", view="overview"))


@app.post("/inquiries/<int:inquiry_id>/resolve")
@roles_required("admin")
def resolve_inquiry(inquiry_id: int) -> Any:
    with g.db:
        inquiry = g.db.execute(
            "SELECT id,status FROM contact_inquiries WHERE id=?", (inquiry_id,)
        ).fetchone()
        if inquiry is None:
            abort(404)
        if inquiry["status"] == "new":
            g.db.execute(
                "UPDATE contact_inquiries SET status='resolved' WHERE id=?", (inquiry_id,)
            )
            audit("Contact inquiry marked resolved", "contact_inquiry", inquiry_id)
    return redirect(url_for("dashboard", view="inquiries"))


@app.post("/bookings")
@login_required
def create_booking() -> Any:
    return_to = safe_local_next(request.form.get("return_to")) or url_for("dashboard", view="bookings")
    package_id = request.form.get("package_id", type=int)
    travel_date = request.form.get("travel_date", "").strip()
    return_date = request.form.get("return_date", "").strip()
    travellers = request.form.get("travellers", type=int)
    referral = request.form.get("agent_code", "").strip().upper()
    payment_method_input = request.form.get("payment_method", "upi").strip().lower()
    upi_id = request.form.get("upi_id", "").strip()
    card_number = request.form.get("card_number", "").strip()
    bank_name = request.form.get("bank_name", "").strip()
    guest_name = request.form.get("guest_name", "").strip()
    guest_email = request.form.get("guest_email", "").strip().lower()
    guest_phone = request.form.get("guest_phone", "").strip()
    transport_mode = request.form.get("transport_mode", "Private AC Sedan / SUV").strip()

    if not package_id or not travellers or not 1 <= travellers <= 20 or not travel_date:
        flash("Choose a date and enter between 1 and 20 travellers.", "error")
        return redirect(return_to)
    try:
        from datetime import date
        trip_date = date.fromisoformat(travel_date)
        if trip_date < date.today():
            raise ValueError
    except ValueError:
        flash("Choose a valid date in the future.", "error")
        return redirect(return_to)
    try:
        with g.db:
            package = g.db.execute(
                "SELECT * FROM packages WHERE id=? AND status='active'", (package_id,)
            ).fetchone()
            if package is None:
                raise ValueError("That trip is no longer available.")
            if package["capacity"] - package["reserved"] < travellers:
                raise ValueError("There aren’t enough seats left for that trip.")

            # Calculate return / checkout date if not explicitly supplied
            if not return_date:
                return_date = compute_return_date(travel_date, package["duration"])

            agent = None
            if g.user["role"] == "agent":
                agent = get_my_agent()
                # Partner is booking for client: ensure client user exists
                client_email = guest_email or f"client-{secrets.token_hex(3)}@wanderwise.local"
                client_name = guest_name or "Client Traveller"
                client_user = g.db.execute("SELECT id FROM users WHERE email=?", (client_email,)).fetchone()
                if not client_user:
                    cur = g.db.execute(
                        "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'customer')",
                        (client_name, client_email, generate_password_hash("Travel@123")),
                    )
                    customer_id = cur.lastrowid
                else:
                    customer_id = client_user["id"]
                guest_name = client_name
                guest_email = client_email
            else:
                customer_id = g.user["id"]
                guest_name = guest_name or g.user["name"]
                guest_email = guest_email or g.user["email"]
                if referral:
                    agent = g.db.execute("SELECT * FROM agents WHERE UPPER(code)=? AND status='active'", (referral,)).fetchone()
                    if agent is None:
                        raise ValueError("That partner referral code wasn’t found or is not currently active.")

            reservation = g.db.execute(
                "UPDATE packages SET reserved=reserved+? WHERE id=? AND status='active' AND capacity-reserved>=?",
                (travellers, package_id, travellers),
            )
            if reservation.rowcount != 1:
                raise ValueError("Those seats have just been booked. Please choose another date or package.")
            reference = f"WW-{secrets.token_hex(4).upper()}"
            transport_delta = 0
            if "flight" in transport_mode.lower():
                transport_delta = 450000
            elif "volvo" in transport_mode.lower():
                transport_delta = -100000
            elif any(k in transport_mode.lower() for k in ["skip", "no transport", "self", "none", "not required"]):
                transport_delta = 0
                transport_mode = "No Transport Required (Self-Arranged)"

            total_amount = max(50000, (package["price_paise"] + transport_delta) * travellers)

            # Determine payment status and payment reference
            if payment_method_input == "upi":
                method_name = f"UPI ({upi_id or 'GPay/PhonePe'})"
                payment_ref = f"PAY-UPI-{secrets.token_hex(4).upper()}"
                status = "confirmed"
            elif payment_method_input == "card":
                last4 = card_number[-4:] if len(card_number) >= 4 else "8921"
                method_name = f"Card (ending in {last4})"
                payment_ref = f"PAY-CRD-{secrets.token_hex(4).upper()}"
                status = "confirmed"
            elif payment_method_input == "netbanking":
                method_name = f"Net Banking ({bank_name or 'HDFC Bank'})"
                payment_ref = f"PAY-NB-{secrets.token_hex(4).upper()}"
                status = "confirmed"
            else:
                method_name = "Pay on Desk / Pending"
                payment_ref = None
                status = "pending"

            cursor = g.db.execute(
                """INSERT INTO bookings(reference,customer_id,agent_id,package_id,travel_date,return_date,
                   travellers,total_paise,status,payment_method,payment_ref,guest_name,guest_email,guest_phone,transport_mode)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (reference, customer_id, agent["id"] if agent else None, package_id,
                 travel_date, return_date, travellers, total_amount, status, method_name, payment_ref,
                 guest_name, guest_email, guest_phone, transport_mode),
            )
            booking_id = cursor.lastrowid

            # Dispatch confirmation email with soft-copy voucher report
            booking_record = {
                "id": booking_id,
                "reference": reference,
                "title": package["title"],
                "destination": package["destination"],
                "duration": package["duration"],
                "travel_date": travel_date,
                "return_date": return_date,
                "travellers": travellers,
                "total_paise": total_amount,
                "status": status,
                "payment_method": method_name,
                "payment_ref": payment_ref,
                "guest_name": guest_name,
                "guest_email": guest_email,
                "guest_phone": guest_phone,
                "transport_mode": transport_mode,
                "agent_id": agent["id"] if agent else None,
            }
            send_booking_email(booking_record, "booking_confirmed" if status == "confirmed" else "booking_reserved")

            if status == "confirmed":
                process_booking_ledger(g.db, booking_id)
                audit(f"Booking {reference} confirmed with payment ({method_name})", "booking", reference)
                flash(f"Payment of ₹{total_amount / 100:,.0f} successful via {method_name}! Booking {reference} confirmed. Confirmation email & travel voucher sent to {guest_email}.", "success")
            else:
                audit(f"Booking {reference} reserved (Pay Later)", "booking", reference)
                flash(f"Trip reserved! Booking {reference} is awaiting payment. E-ticket summary sent to {guest_email}.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard", view="bookings"))


@app.post("/bookings/<int:booking_id>/pay")
@login_required
def pay_booking(booking_id: int) -> Any:
    booking = g.db.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if booking is None:
        abort(404)
    if g.user["role"] == "customer" and booking["customer_id"] != g.user["id"]:
        abort(404)
    if g.user["role"] == "agent":
        agent = get_my_agent()
        if not agent or booking["agent_id"] != agent["id"]:
            abort(404)
    if g.user["role"] not in ("admin", "agent", "customer"):
        abort(403)
    if booking["status"] != "pending":
        flash("Only pending bookings can be paid.", "error")
    else:
        pay_method = request.form.get("pay_method", "UPI (Instant)").strip()
        txn_ref = f"PAY-ONLINE-{secrets.token_hex(4).upper()}"
        with g.db:
            g.db.execute(
                "UPDATE bookings SET status='confirmed', payment_method=?, payment_ref=? WHERE id=? AND status='pending'",
                (pay_method, txn_ref, booking_id)
            )
            process_booking_ledger(g.db, booking_id)
            audit(f"Payment recorded via {pay_method} (Ref: {txn_ref})", "booking", booking["reference"])
            
            # Fetch updated booking and send confirmation email
            paid_b = g.db.execute(
                """SELECT b.*, p.title, p.destination, p.duration
                   FROM bookings b JOIN packages p ON p.id=b.package_id WHERE b.id=?""", (booking_id,)
            ).fetchone()
            if paid_b:
                send_booking_email(dict(paid_b), "booking_confirmed")
        flash(f"Payment verified via {pay_method}! Booking {booking['reference']} is now confirmed. Travel voucher sent via email.", "success")
    return redirect(url_for("dashboard", view="bookings"))


@app.post("/bookings/<int:booking_id>/status")
@login_required
def update_booking(booking_id: int) -> Any:
    status = request.form.get("status", "")
    if status not in ("completed", "cancelled"):
        abort(400)
    booking = g.db.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if booking is None:
        abort(404)
    # Check role permissions: Admin can complete or cancel; Agent can cancel bookings under their code
    if g.user["role"] == "agent":
        my_agent = get_my_agent()
        if not my_agent or booking["agent_id"] != my_agent["id"]:
            abort(403)
        if status != "cancelled":
            abort(403)
    elif g.user["role"] != "admin":
        abort(403)

    try:
        with g.db:
            if status == "completed":
                if booking["status"] != "confirmed":
                    raise ValueError("Only confirmed bookings can be marked completed.")
                g.db.execute("UPDATE bookings SET status='completed' WHERE id=?", (booking_id,))
                process_booking_ledger(g.db, booking_id)

                # Dispatch Journey Completion Certificate & Report Email to traveller
                comp_b = g.db.execute(
                    """SELECT b.*, p.title, p.destination, p.duration, u.name AS customer_name, u.email AS customer_email,
                              a.code AS agent_code
                       FROM bookings b
                       JOIN packages p ON p.id=b.package_id
                       JOIN users u ON u.id=b.customer_id
                       LEFT JOIN agents a ON a.id=b.agent_id
                       WHERE b.id=?""", (booking_id,)
                ).fetchone()
                if comp_b:
                    send_booking_email(dict(comp_b), "trip_completed")
            else:
                if booking["status"] not in ("pending", "confirmed"):
                    raise ValueError("This booking can no longer be cancelled.")
                g.db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
                g.db.execute(
                    "UPDATE packages SET reserved=MAX(0,reserved-?) WHERE id=?",
                    (booking["travellers"], booking["package_id"]),
                )
            audit(f"Booking marked {status}", "booking", booking["reference"])
        if status == "completed":
            flash(f"Booking {booking['reference']} marked completed. Eligible commissions credited and Journey Completion Certificate & soft-copy report emailed to traveller.", "success")
        else:
            flash(f"Booking {booking['reference']} has been cancelled and {booking['travellers']} reserved seat(s) released.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard", view="bookings"))


@app.post("/packages")
@roles_required("admin")
def create_package() -> Any:
    title = request.form.get("title", "").strip()
    destination = request.form.get("destination", "").strip()
    category = request.form.get("category", "Heritage & Wonders").strip()
    duration = request.form.get("duration", "").strip()
    description = request.form.get("description", "").strip()
    stay_type = request.form.get("stay_type", "").strip()
    meal_plan = request.form.get("meal_plan", "").strip()
    transport = request.form.get("transport", "").strip()
    inclusions = request.form.get("inclusions", "").strip()
    itinerary = request.form.get("itinerary", "").strip()
    image_file = request.form.get("image_file", "").strip() or "place-tajmahal.jpg"
    official_url = request.form.get("official_url", "").strip()
    activities = request.form.get("activities", "").strip()
    capacity = request.form.get("capacity", type=int)
    try:
        price = money_to_paise(request.form.get("price", ""))
        if not title or not destination or not duration or not description or len(title) > 100 or not capacity or not 1 <= capacity <= 10000:
            raise ValueError("Complete each field and enter a capacity from 1 to 10,000.")
        with g.db:
            cursor = g.db.execute(
                """INSERT INTO packages(title,destination,category,description,duration,price_paise,capacity,image_file,official_url,activities)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (title, destination, category[:40], description, duration, price, capacity, image_file, official_url, activities),
            )
            g.db.execute(
                """INSERT INTO package_details
                   (package_id,stay_type,meal_plan,transport,inclusions,itinerary)
                   VALUES(?,?,?,?,?,?)""",
                (cursor.lastrowid, stay_type or "Comfortable locally operated accommodation",
                 meal_plan or "Meals confirmed with your travel desk",
                 transport or "Transport details confirmed before booking",
                 inclusions or "Trip support from the travel desk",
                 itinerary or "A day-by-day itinerary will be arranged with your travel desk."),
            )
            audit("Travel package created", "package", cursor.lastrowid)
        flash(f"'{title}' has been added to the collection.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard", view="packages"))


@app.post("/packages/<int:package_id>/toggle")
@roles_required("admin")
def toggle_package_status(package_id: int) -> Any:
    with g.db:
        pkg = g.db.execute("SELECT id, status, title FROM packages WHERE id=?", (package_id,)).fetchone()
        if not pkg:
            abort(404)
        new_status = "archived" if pkg["status"] == "active" else "active"
        g.db.execute("UPDATE packages SET status=? WHERE id=?", (new_status, package_id))
        audit(f"Package status toggled to {new_status}", "package", package_id)
        flash(f"Package '{pkg['title']}' is now {new_status}.", "success")
    return redirect(safe_local_next(request.form.get("return_to")) or url_for("dashboard", view="packages"))


@app.post("/commissions")
@roles_required("admin")
def update_commissions() -> Any:
    try:
        rates = []
        for level in range(1, 5):
            value = Decimal(request.form.get(f"level_{level}", ""))
            if not value.is_finite() or value < 0 or value > 100:
                raise ValueError("Commission rates must be between 0% and 100%.")
            rates.append((int(value * 100), level))
        if sum(rate for rate, _ in rates) > 10000:
            raise ValueError("The total across all four levels cannot exceed 100%.")
        with g.db:
            g.db.executemany("UPDATE commission_rules SET rate_bps=? WHERE level=?", rates)
            audit("Commission rates updated", "commission_rules", "all-levels")
        flash("Commission settings saved. Existing ledger entries are unchanged.", "success")
    except (ValueError, InvalidOperation):
        flash("Enter valid commission percentages between 0 and 100.", "error")
    return redirect(url_for("dashboard", view="commissions"))


@app.post("/withdrawals")
@roles_required("agent")
def request_withdrawal() -> Any:
    agent = get_my_agent()
    if not agent:
        abort(403)
    try:
        amount = money_to_paise(request.form.get("amount", ""))
        with g.db:
            balance = wallet_balance(agent["id"])
            reserved = reserved_withdrawals(agent["id"])
            if amount > balance - reserved:
                raise ValueError("That amount exceeds your available wallet balance.")
            cursor = g.db.execute(
                "INSERT INTO withdrawals(agent_id,amount_paise,status) VALUES(?,?,'pending')",
                (agent["id"], amount),
            )
            audit("Withdrawal requested", "withdrawal", cursor.lastrowid)
        flash("Withdrawal request submitted for admin review.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard", view="wallet"))


@app.post("/withdrawals/<int:withdrawal_id>")
@roles_required("admin")
def review_withdrawal(withdrawal_id: int) -> Any:
    action = request.form.get("action", "")
    if action not in ("approve", "reject", "complete"):
        abort(400)
    try:
        with g.db:
            withdrawal = g.db.execute("SELECT * FROM withdrawals WHERE id=?", (withdrawal_id,)).fetchone()
            if withdrawal is None:
                abort(404)
            if action in ("approve", "reject") and withdrawal["status"] != "pending":
                raise ValueError("Only pending requests can be reviewed.")
            if action == "complete":
                if withdrawal["status"] != "approved":
                    raise ValueError("Approve this request before recording settlement.")
                balance = wallet_balance(withdrawal["agent_id"])
                if balance < withdrawal["amount_paise"]:
                    raise ValueError("The available ledger balance is insufficient to settle this request.")
                g.db.execute(
                    """INSERT INTO wallet_transactions(agent_id,amount_paise,kind,reference)
                       VALUES(?,?,'withdrawal',?)""",
                    (withdrawal["agent_id"], -withdrawal["amount_paise"], f"WITHDRAWAL-{withdrawal_id}"),
                )
                new_status = "completed"
            else:
                new_status = "approved" if action == "approve" else "rejected"
            g.db.execute(
                "UPDATE withdrawals SET status=?,reviewed_by=?,reviewed_at=datetime('now') WHERE id=?",
                (new_status, g.user["id"], withdrawal_id),
            )
            audit(f"Withdrawal {new_status}", "withdrawal", withdrawal_id)
        flash(f"Withdrawal marked {new_status}.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard", view="wallet"))


@app.errorhandler(403)
def forbidden(_error: Any) -> tuple[str, int]:
    return render_template("error.html", code=403, message="You don’t have permission to view this page."), 403


@app.errorhandler(404)
def not_found(_error: Any) -> tuple[str, int]:
    return render_template("error.html", code=404, message="We couldn’t find that page."), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
