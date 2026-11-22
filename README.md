# Wanderwise Travel ERP

> **Enterprise Indian Travel Commerce & Agency Operations ERP Platform**  
> Built with Python, Flask, SQLite3, HTML5, CSS3, and modern responsive design.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/database-SQLite3%20WAL-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

---

## 🌟 Overview

**Wanderwise Travel ERP** is a full-featured travel agency enterprise resource planning prototype designed specifically for Indian tourism, heritage landmarks, and pilgrimage circuits.

It bridges visitor-facing travel discovery with complete back-office ERP operations, featuring:
- **Public Travel Marketplace**: High-definition landmarks photo marquee gallery, package search, detailed day-by-day itineraries with official government tourism links, and transparent policy checklist cards.
- **Executive Administrator Command Center**: Real-time KPI analytics (gross volume, confirmed travellers, seat inventory), package activation/archival toggles, and new package publishing.
- **Master Reservations Ledger**: Full booking lifecycle state machine (`pending` → `confirmed` → `completed` → `cancelled`) with 1-click administrative actions.
- **Multi-Level Partner Network (MLM Hierarchy)**: 4-tier commission ladder with recursive downline team tracking and unique referral codes (`WW-1001` to `WW-1006`).
- **Double-Entry Wallet Ledger & Payout Queue**: Automated commission distribution on trip completion, available vs. reserved balance tracking, and bank settlement recording with official UTR numbers.
- **Inbound Guest Support Desk**: Customer inquiry management with direct 1-click `mailto` reply and resolution workflows.
- **Prominent Multi-Location Sign Out**: Unmistakable session controls across topbar, sidebar, profile drawer, and public headers.

---

## 🔑 Verified Live Sample Credentials & Role Functions

The system separates functionality across 3 distinct operational roles:

| Operational Role | Representative Account | Login Email | Password | Scope & Specific Functions |
| :--- | :--- | :--- | :--- | :--- |
| **👑 Administrator** | **Aarav Mehta** (*HQ Operations*) | `admin@wanderwise.local` | `Admin@123` | **Full ERP Access**: Executive Cockpit, package creation & visibility, master booking ledger across all users, MLM partner tree, commission rules, payout approval, dispatched emails audit, system logs. |
| **💼 Agent (Partner)** | **Priya Sharma** (*Apex Holidays*) | `agent@wanderwise.local` | `Agent@123` | **Partner Portal**: Referral code `WW-1001`, **Book for Client ↗** (registers client bookings under partner code), manual client cancellation with seat release, earnings wallet & payout requests. |
| **✈️ Traveler (Customer)** | **Lokesh M M Ankith** (*Explorer*) | `lokeshmmankith@gmail.com` | `Lokesh@123` | **Traveler Portal**: Direct trip booking with instant UPI QR code / card / net banking, personal booking ledger, printable official soft-copy vouchers & itinerary reports. |
| **✈️ Traveler (Customer)** | **Maya Kapoor** (*Explorer*) | `customer@wanderwise.local` | `Travel@123` | **Traveler Portal**: Alternative guest profile for testing reviews and completed journeys. |

*(On the sign-in screen, the **Traveler Portal** button provides interactive profile options to select **Lokesh M M Ankith** or **Maya Kapoor** with 1-click).*

---

## 💳 Real-World Features, Schedule Dates & Communications

### 1. 100% Real Live Data (Zero Dummy Bookings Baseline)
- The database starts with **0 dummy bookings**, **0 dummy transactions**, and **0 dummy withdrawals**.
- When an explorer (e.g. Lokesh) reserves a trip, **only that authentic booking is registered** in the database.
- Direct website bookings appear only under the customer and admin master ledgers.
- Bookings created by or referred through an agent (e.g. `WW-1001`) are attributed to that agent's portal.

### 2. Departure Date AND Auto-Calculated Checkout / Return Date
- Each booking explicitly tracks both **Departure / Start Date** and **Checkout / Return Date**.
- When a traveller or agent selects a start date, the system **automatically computes the Return / Checkout Date** using the tour package's duration (e.g., *3 days / 2 nights*, *5 days / 4 nights*, *6 days / 5 nights*).
- Both departure and checkout dates are displayed across:
  - Package Booking Forms
  - Bookings Master Ledger (`📅 2026-12-15 ➔ 2026-12-17`)
  - Official Printable Soft-Copy Travel Voucher (`/bookings/<ref>/voucher`)
  - Automated Confirmation & Completion Emails.

### 3. Multi-Gateway Payment Checkout with Interactive UPI QR Code
- **⚡ Instant UPI with Dynamic QR Code**: An interactive SVG QR matrix pre-filled with the exact booking tariff. Travellers can scan with **Google Pay, PhonePe, Paytm, BHIM, Cred, Amazon Pay, or RuPay**. Includes a 1-click "Simulate QR Scan" button for instant testing.
- **⚡ Quick-Select UPI ID (VPA) Chips**: 1-click select chips for GPay (`lokesh@okhdfcbank`), PhonePe (`@ybl`), Paytm (`@paytm`), BHIM (`@upi`), and the official desk VPA (`wanderwise.travel@icici`).
- **💳 Credit / Debit Cards**: Visa, MasterCard, RuPay with CVV and expiry validation.
- **🏦 Net Banking**: Immediate simulation for all major Indian banks (SBI, HDFC, ICICI, Axis, Kotak).
- **⏳ Pay Later (Pay on Desk)**: Reserve seats with `pending` status, allowing the customer to pay online later from their dashboard.

### 4. Partner (Agent) Booking for Client & Manual Cancellation
- **Book for Client ↗**: When logged in as an Agent, partners can register a journey on behalf of their client (entering Client Name, Email, Phone, Dates, and Payment Option). The reservation is automatically attributed to the partner's referral code (`WW-1001`).
- **Confirmation emails with soft-copy vouchers are sent to BOTH the client's email and the partner's email.**
- **Manual Cancellation**: If a client requests cancellation, the agent can click **Cancel booking ✕** directly from their ledger, immediately releasing reserved seats back into package inventory.

### 5. Automated Email Communications & Soft-Copy Voucher Report
- **Booking Confirmed Email**: Dispatched immediately upon payment to the traveller's email (and partner copy if referred). Contains the booking reference, departure and checkout schedule, payment reference, and a direct button to view the official travel voucher.
- **Trip Completed Email**: When an administrator completes a journey, a formal **Journey Completion Certificate & Itinerary Report** email is automatically dispatched to the traveller.
- **Official Printable Travel Voucher (`/bookings/<reference>/voucher`)**: A print-ready A4 document with Wanderwise branding, reservation barcode, check-in/checkout schedule, stay and transport inclusions, payment receipt, and 24/7 emergency desk helpline. Supports 1-click printing or saving as PDF via `window.print()`.
- **Admin Dispatched Emails Audit (`view=emails`)**: The administrator can review all dispatched transactional emails, delivery timestamps, recipients, and subjects in real time.

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Client Presentation Tier                              │
│   • Jinja2 Server-Side Rendered Templates (SSR)                             │
│   • Typography: DM Sans (Headings) & Manrope (Body)                         │
│   • Interactive Policy Checklist Cards & Landmark Photo Marquee Showcase   │
│   • Glassmorphic Navigation, Responsive Tables, & 1-Click Role Switcher     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / Secure Session Cookies
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    Application & Business Logic Tier (Flask 3.x)             │
│   • Route Controllers: Public Discovery, Bookings, Agent Network & HQ Desk  │
│   • Cryptographic CSRF Tokens: Validated on all state-mutating POST requests│
│   • Role-Based Access Control: @login_required, @roles_required('admin')    │
│   • Password Hashing: Scrypt with salt via Werkzeug Security                │
│   • Concurrency Guard: Atomic seat allocation preventing overbooking       │
│   • Recursive Multi-Level Commission Distribution Engine                    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ SQLite Native Driver (WAL Mode)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                   Persistence & Relational Database Tier                    │
│   • SQLite3 with Foreign Keys & Write-Ahead Logging (WAL) Enabled           │
│   • users: Authentication, role separation (customer, agent, admin)         │
│   • agents: Multi-level referral tree with self-referencing parent_id       │
│   • packages & package_details: Inventory, capacity, day-by-day itineraries │
│   • bookings: Real-world reservations, payment methods & transaction refs   │
│   • wallet_transactions & withdrawals: Double-entry ledger (integer paise)  │
│   • audit_logs & contact_inquiries: Tamper-evident operational trail        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Relational Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o| AGENTS : "assigned as"
    USERS ||--o{ BOOKINGS : "places"
    AGENTS ||--o{ BOOKINGS : "referred by"
    AGENTS ||--o{ AGENTS : "parent upline"
    PACKAGES ||--|| PACKAGE_DETAILS : "has"
    PACKAGES ||--o{ BOOKINGS : "reserved in"
    AGENTS ||--o{ WALLET_TRANSACTIONS : "credited/debited"
    BOOKINGS ||--o{ WALLET_TRANSACTIONS : "generates commission"
    AGENTS ||--o{ WITHDRAWALS : "requests payout"
    USERS ||--o{ AUDIT_LOGS : "performed by"
```

---

## 💰 Multi-Level Commission Calculation Logic

When a tour package booking is completed by the travel desk, the commission engine distributes commissions up the referring agent's upline network across **up to 4 generations**.

### 1. Commission Ladder & Basis Points (BPS)
All rates are represented in **Basis Points (1 BPS = 0.01% = 1/10,000)** to guarantee exact integer calculations in paise without floating-point inaccuracies:

| Referral Tier | Hierarchy Level | Basis Points | Percentage Rate | Role Description |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Direct Booking Agent | `500 bps` | **5.00%** | The partner directly registering or referring the booking |
| **Tier 2** | Direct Parent (L1 Upline) | `200 bps` | **2.00%** | The direct mentor/sponsor of the booking partner |
| **Tier 3** | Senior Partner (L2 Upline) | `100 bps` | **1.00%** | Regional senior partner overseeing the agency cluster |
| **Tier 4** | Principal Partner (L3 Upline) | `50 bps` | **0.50%** | Apex principal partner at the root of the network |
| **HQ Retained** | Wanderwise Operations | `9150 bps` | **91.50%** | Platform gross margin covering vendor costs & operations |

### 2. Core Python Algorithm (`app.py`)

```python
# Multi-Level Commission Calculation Loop (app.py)
agent_id = booking["agent_id"]
depth = 1

while agent_id and depth <= 4:
    rule = g.db.execute(
        "SELECT rate_bps FROM commission_rules WHERE level=?", (depth,)
    ).fetchone()
    
    if rule:
        # Integer math ensures 0 floating-point rounding errors (calculated in paise)
        cut = (booking["total_paise"] * rule["rate_bps"]) // 10000
        if cut > 0:
            g.db.execute(
                """INSERT INTO wallet_transactions
                   (agent_id, booking_id, amount_paise, kind, reference)
                   VALUES (?, ?, ?, 'commission', ?)""",
                (agent_id, booking["id"], cut, f"COMM-{booking['reference']}-L{depth}")
            )
            
    # Traverse to direct parent upline
    agent = g.db.execute(
        "SELECT parent_id FROM agents WHERE id=?", (agent_id,)
    ).fetchone()
    agent_id = agent["parent_id"] if agent else None
    depth += 1
```

### 3. Worked Mathematical Example

Consider a booking for 2 guests on the **Kedarnath & Badrinath Sacred Do Dham Yatra**:
- Package Price per Traveller: **₹28,500.00** (2,850,000 paise)
- Guests: **2**
- **Total Gross Booking Volume**: ₹28,500 × 2 = **₹57,000.00** (`5,700,000 paise`)

Referred by **Kabir Singh (`WW-1004`)** whose upline chain is:
`Kabir Singh (Tier 1)` → `Nisha Rao (Tier 2)` → `Rohan Das (Tier 3)` → `Priya Sharma (Tier 4)`

The engine computes:
- **Tier 1 (Kabir Singh, `WW-1004`)**:
  $$\frac{5,700,000 \times 500}{10,000} = 285,000\text{ paise} = \mathbf{₹2,850.00}$$
- **Tier 2 (Nisha Rao, `WW-1003`)**:
  $$\frac{5,700,000 \times 200}{10,000} = 114,000\text{ paise} = \mathbf{₹1,140.00}$$
- **Tier 3 (Rohan Das, `WW-1002`)**:
  $$\frac{5,700,000 \times 100}{10,000} = 57,000\text{ paise} = \mathbf{₹570.00}$$
- **Tier 4 (Priya Sharma, `WW-1001`)**:
  $$\frac{5,700,000 \times 50}{10,000} = 28,500\text{ paise} = \mathbf{₹285.00}$$

**Summary**:
- Total Network Commission Disbursed: **₹4,845.00** (8.50%)
- Net Wanderwise Retained Gross Margin: **₹52,155.00** (91.50%)

---

## 📸 Screenshots & Demonstration Guide

### Live Feature Walkthrough

#### 1. Public Marketplace & Photo Marquee
- Visit `http://127.0.0.1:5000/`.
- Browse the interactive **India Landmarks Photo Marquee Gallery** (Somnath Temple, Statue of Unity, Golden Temple, Taj Mahal, Mysore Palace).
- Inspect the **Booking & Travel Policies** interactive checklist cards.

#### 2. Customer Booking & Payment Checkout
- Sign in with **👤 Lokesh** (`lokeshmmankith@gmail.com` / `Lokesh@123`).
- Select any package (e.g. *Taj Mahal & Mughal Splendour* or *Into the Himalayas*).
- Choose travel date, number of travellers, and select your preferred payment option:
  - **⚡ Instant UPI**: Enter your UPI ID (e.g., `lokesh@oksbi`).
  - **💳 Card**: Enter test card number.
  - **🏦 Net Banking**: Select bank.
  - **⏳ Pay on Desk**: Reserve now and pay later.
- Submit booking: notice instant confirmation with an official payment reference (e.g., `PAY-UPI-XXXX`), and seat capacity reserved.

#### 3. Agent Dashboard & Manual Booking Cancellation
- Sign in with **💼 Partner** (`agent@wanderwise.local` / `Agent@123`).
- View referred customer bookings attributed to agency code `WW-1001`.
- Direct bookings by unrelated customers are kept private.
- If a client requests cancellation, click **Cancel booking ✕**.
- Status updates immediately to `cancelled`, and the package's reserved seats are restored.

#### 4. Executive Admin Command Center
- Sign in with **👑 Admin** (`admin@wanderwise.local` / `Admin@123`).
- View real-time gross volume, confirmed bookings count, and active packages.
- View the Master Reservations Ledger with payment methods and transaction references.
- Mark journeys as **Complete trip ↗** to trigger automated upline commission distribution.

#### 5. Clean Sign Out Flow
- Click **Sign Out** from the top header or sidebar.
- You are immediately redirected to the public website homepage (`/`).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone and Setup
```bash
git clone https://github.com/Lokesh206/Travel-ERP.git
cd Travel-ERP
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Application
```bash
# Windows
run.bat
# or
python app.py
```

Open `http://127.0.0.1:5000` in your web browser.

---

## 📁 Project Structure

```
Travel-ERP/
├── app.py                  # Core Flask application, routing, auth & commission engine
├── seed_data.py            # Package inventory & initial data
├── seed_real_world.py      # Production-grade Indian bookings, agents, inquiries & reviews
├── requirements.txt        # Minimal Python dependencies (Flask, Werkzeug)
├── run.bat                 # 1-click Windows runner
├── static/
│   ├── style.css           # Global typography & layout system
│   ├── landing.css         # Public showcase, search filters & hero
│   ├── workspace.css       # Enterprise dashboard layout & table components
│   ├── enhancements.css    # Admin command center, marquee, login background & guide
│   └── *.jpg               # High-res landmarks, gallery & background photos
└── templates/
    ├── public_home.html    # Visitor portal, photo marquee & policy checklist
    ├── trip_details.html   # Day-by-day itinerary, inclusions & booking form
    ├── login.html          # Incredible India auth portal with 1-click role switcher
    ├── dashboard.html      # Complete Executive Command Center & Architecture Guide
    └── error.html          # User-friendly error boundary
```

---

## 🛡️ Security & Integrity Highlights
- **Cryptographic CSRF Validation**: Enforced across every state-changing POST endpoint.
- **Double-Entry Wallet Bookkeeping**: Commission accruals and withdrawal settlements are strictly logged with integer paise precision to prevent float rounding errors.
- **Immutable Audit Trail**: Security ledger recording actor IDs, action verbs, record IDs, and timestamps.
- **Role-Based Guards**: Decorator-enforced authorization (`@roles_required("admin")`, `@roles_required("agent")`).

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
