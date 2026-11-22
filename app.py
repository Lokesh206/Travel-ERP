from __future__ import annotations

import os
import secrets
import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import wraps
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlsplit

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
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
    level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 4),
    parent_id INTEGER REFERENCES agents(id),
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
    travellers INTEGER NOT NULL CHECK (travellers BETWEEN 1 AND 20),
    total_paise INTEGER NOT NULL CHECK (total_paise > 0),
    status TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled')),
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
CREATE INDEX IF NOT EXISTS bookings_customer_idx ON bookings(customer_id, created_at);
CREATE INDEX IF NOT EXISTS bookings_agent_idx ON bookings(agent_id, created_at);
CREATE INDEX IF NOT EXISTS wallet_agent_idx ON wallet_transactions(agent_id, created_at);
CREATE INDEX IF NOT EXISTS withdrawals_agent_idx ON withdrawals(agent_id, created_at);
CREATE INDEX IF NOT EXISTS reviews_created_idx ON reviews(created_at);
CREATE INDEX IF NOT EXISTS inquiries_created_idx ON contact_inquiries(created_at);
"""


def connect_db() -> sqlite3.Connection:
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 10000")
    return db


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
                ("Aarav Mehta", "admin@wanderwise.local", "admin", "Admin@123"),
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

        # Ensure payment columns exist on bookings
        b_cols = [r[1] for r in db.execute("PRAGMA table_info(bookings)").fetchall()]
        if "payment_method" not in b_cols:
            db.execute("ALTER TABLE bookings ADD COLUMN payment_method TEXT")
        if "payment_ref" not in b_cols:
            db.execute("ALTER TABLE bookings ADD COLUMN payment_ref TEXT")

    try:
        from seed_data import run_seed
        run_seed()
    except Exception as err:
        print("Seed warning:", err)


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
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = g.db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            next_url = safe_local_next(request.form.get("next") or request.args.get("next"))
            session.clear()
            session["user_id"] = user["id"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            return redirect(next_url or url_for("dashboard"))
        flash("That email and password combination wasn’t recognized.", "error")
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
        if not name or len(name) > 80 or "@" not in email or len(email) > 254:
            flash("Add a valid name and email address.", "error")
        elif len(password) < 10:
            flash("Choose a password with at least 10 characters.", "error")
        elif role not in ("customer", "agent"):
            flash("Choose a valid account type.", "error")
        elif g.db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            flash("An account with that email already exists.", "error")
        else:
            parent = None
            if referral:
                parent = g.db.execute("SELECT * FROM agents WHERE code=?", (referral,)).fetchone()
                if parent is None:
                    flash("We couldn’t find that referral code.", "error")
                    return render_template("login.html", register=True)
                if role == "agent" and parent["level"] < 2:
                    flash("That partner is at the bottom of the referral ladder and can’t refer another agent.", "error")
                    return render_template("login.html", register=True)
            try:
                with g.db:
                    cursor = g.db.execute(
                        "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                        (name, email, generate_password_hash(password), role),
                    )
                    if role == "agent":
                        agent_code = f"WW-{cursor.lastrowid + 1000:04d}"
                        g.db.execute(
                            "INSERT INTO agents(user_id,code,level,parent_id) VALUES(?,?,?,?)",
                            (cursor.lastrowid, agent_code, max(1, (parent["level"] - 1) if parent else 1),
                             parent["id"] if parent else None),
                        )
                    audit("Account registered", role, cursor.lastrowid)
                flash("Your account is ready. Sign in to get started.", "success")
                return redirect(url_for("login", next=safe_local_next(
                    request.form.get("next") or request.args.get("next")
                )))
            except sqlite3.IntegrityError:
                flash("We couldn’t create that account. Please check the details and try again.", "error")
    return render_template("login.html", register=True)


@app.route("/logout", methods=["GET", "POST"])
def logout() -> Any:
    session.clear()
    flash("You have been signed out safely.", "success")
    return redirect(url_for("public_home"))


@app.get("/")
def public_home() -> Any:
    destination = request.args.get("destination", "").strip()
    category = request.args.get("category", "").strip()
    destinations = g.db.execute(
        "SELECT DISTINCT destination FROM packages WHERE status='active' ORDER BY destination"
    ).fetchall()
    categories = g.db.execute(
        "SELECT DISTINCT category FROM packages WHERE status='active' ORDER BY category"
    ).fetchall()
    package_query = "SELECT *, capacity-reserved AS available FROM packages WHERE status='active'"
    package_args: list[str] = []
    if destination:
        package_query += " AND destination=?"
        package_args.append(destination)
    if category:
        package_query += " AND category=?"
        package_args.append(category)
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
        destinations=destinations, categories=categories,
        selected_destination=destination, selected_category=category,
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
    return render_template("trip_details.html", package=trip)


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
            """SELECT b.*,p.title,p.destination,
                      EXISTS(SELECT 1 FROM reviews r WHERE r.booking_id=b.id) AS reviewed
               FROM bookings b JOIN packages p ON p.id=b.package_id
               WHERE b.customer_id=? ORDER BY b.created_at DESC""", (g.user["id"],)
        ).fetchall()
    elif role == "agent":
        bookings = g.db.execute(
            """SELECT b.*,p.title,p.destination,u.name AS customer_name,
                      EXISTS(SELECT 1 FROM reviews r WHERE r.booking_id=b.id) AS reviewed FROM bookings b
               JOIN packages p ON p.id=b.package_id JOIN users u ON u.id=b.customer_id
               WHERE b.agent_id=? ORDER BY b.created_at DESC""", (my_agent["id"],)
        ).fetchall()
    else:
        bookings = g.db.execute(
            """SELECT b.*,p.title,p.destination,u.name AS customer_name,
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
    return render_template(
        "dashboard.html", view=view, packages=packages, all_packages=all_packages, bookings=bookings, stats=stats,
        my_agent=my_agent, agents=agents, rules=rules, withdrawals=withdrawals,
        transactions=transactions, balance=balance, reserved=reserved,
        available_balance=max(0, balance - reserved), team=team, logs=logs,
        inquiries=inquiries, public_reviews=public_reviews,
    )


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
    return_to = safe_local_next(request.form.get("return_to")) or url_for("dashboard", view="packages")
    package_id = request.form.get("package_id", type=int)
    travel_date = request.form.get("travel_date", "")
    travellers = request.form.get("travellers", type=int)
    referral = request.form.get("agent_code", "").strip().upper()
    payment_method_input = request.form.get("payment_method", "upi").strip().lower()
    upi_id = request.form.get("upi_id", "").strip()
    card_number = request.form.get("card_number", "").strip()
    bank_name = request.form.get("bank_name", "").strip()

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
            agent = None
            if g.user["role"] == "agent":
                agent = get_my_agent()
            elif referral:
                agent = g.db.execute("SELECT * FROM agents WHERE code=?", (referral,)).fetchone()
                if agent is None:
                    raise ValueError("That agent referral code wasn’t found.")
            reservation = g.db.execute(
                "UPDATE packages SET reserved=reserved+? WHERE id=? AND status='active' AND capacity-reserved>=?",
                (travellers, package_id, travellers),
            )
            if reservation.rowcount != 1:
                raise ValueError("Those seats have just been booked. Please choose another date or package.")
            reference = f"WW-{secrets.token_hex(4).upper()}"
            total_amount = package["price_paise"] * travellers

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
                """INSERT INTO bookings(reference,customer_id,agent_id,package_id,travel_date,
                   travellers,total_paise,status,payment_method,payment_ref) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (reference, g.user["id"], agent["id"] if agent else None, package_id,
                 travel_date, travellers, total_amount, status, method_name, payment_ref),
            )
            if status == "confirmed":
                audit(f"Booking {reference} confirmed with payment ({method_name})", "booking", reference)
                flash(f"Payment of ₹{total_amount / 100:,.0f} successful via {method_name}! Booking {reference} is confirmed.", "success")
            else:
                audit(f"Booking {reference} reserved (Pay Later)", "booking", reference)
                flash(f"Trip reserved! Booking {reference} is awaiting payment. You can pay online anytime from your bookings ledger.", "success")
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
            audit(f"Payment recorded via {pay_method} (Ref: {txn_ref})", "booking", booking["reference"])
        flash(f"Payment verified via {pay_method}! Booking {booking['reference']} is now confirmed.", "success")
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
                if booking["agent_id"]:
                    agent_id = booking["agent_id"]
                    amount = booking["total_paise"]
                    for _ in range(4):
                        agent = g.db.execute(
                            "SELECT id,level,parent_id FROM agents WHERE id=?", (agent_id,)
                        ).fetchone()
                        if agent is None:
                            break
                        rule = g.db.execute(
                            "SELECT rate_bps FROM commission_rules WHERE level=?", (agent["level"],)
                        ).fetchone()
                        commission = (amount * rule["rate_bps"] // 10000) if rule else 0
                        if commission:
                            g.db.execute(
                                """INSERT OR IGNORE INTO wallet_transactions(agent_id,amount_paise,kind,reference)
                                   VALUES(?,?,'commission',?)""",
                                (agent_id, commission, booking["reference"]),
                            )
                        if not agent["parent_id"]:
                            break
                        agent_id = agent["parent_id"]
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
            flash(f"Booking {booking['reference']} marked completed. Eligible commissions have been added to the agent wallet ledger.", "success")
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
    initialize_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
