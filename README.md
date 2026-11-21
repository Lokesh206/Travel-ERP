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

## 🔑 Verified Live Sample Credentials

The system includes pre-configured, authentic accounts for all operational tiers:

| Role & Tier | Representative Name & Agency | Login Email | Password | Partner Code | Tier / Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **👑 Administrator** | **Aarav Mehta** (*Head of Operations*) | `admin@wanderwise.local` | `Admin@123` | `HQ-ADMIN-01` | Executive HQ Controls |
| **💼 Principal Partner** | **Priya Sharma** (*Apex Travel Holidays*) | `agent@wanderwise.local` | `Agent@123` | `WW-1001` | **Tier 4** (0.5% Apex Override) |
| **💼 Senior Partner** | **Rohan Das** (*Odyssey India Tours*) | `rohan@wanderwise.local` | `Agent@123` | `WW-1002` | **Tier 3** (1.0% Senior Override) |
| **💼 Associate Partner** | **Nisha Rao** (*Deccan Voyages*) | `nisha@wanderwise.local` | `Agent@123` | `WW-1003` | **Tier 2** (2.0% Upline Override) |
| **💼 Junior Partner** | **Kabir Singh** (*Heritage Trails Punjab*) | `kabir@wanderwise.local` | `Agent@123` | `WW-1004` | **Tier 1** (5.0% Direct Booking) |
| **✈️ Verified Customer** | **Maya Kapoor** (*Traveller - Mumbai*) | `customer@wanderwise.local` | `Travel@123` | *Guest* | Active Itineraries |
| **✈️ Verified Customer** | **Vikramaditya Singhania** (*Traveller - Jaipur*) | `vikram@wanderwise.local` | `Vikram@123` | *Guest* | Completed Journeys |

*(On the sign-in screen, use the **1-Click Quick Demo Login** pills to pre-fill credentials instantly).*

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Client Presentation Tier                    │
│   Jinja2 SSR Templates · DM Sans & Manrope Typography       │
│   Landmarks Photo Marquee · Glassmorphic UI · CSS Variables │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│             Application & Security Tier (Flask 3.x)          │
│   HTTP Routing · CSRF Session Tokens · @roles_required      │
│   Scrypt Password Hasher · Recursive Commission Engine      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│           Persistence & Relational Data Tier (SQLite3)       │
│   ACID WAL Mode · Double-Entry Ledger · Foreign Keys        │
│   users · agents · packages · bookings · wallet · audit     │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 Multi-Level Commission Calculation Logic

When a tour package booking is marked **Completed**, the commission engine traverses up the agent referral hierarchy up to 4 generations:

### Commission Ladder
- **Tier 1 (Direct Booking Partner)**: **5.0%** (`500 bps`)
- **Tier 2 (Direct Parent / L1 Upline)**: **2.0%** (`200 bps`)
- **Tier 3 (Senior Partner / L2 Upline)**: **1.0%** (`100 bps`)
- **Tier 4 (Apex Principal / L3 Upline)**: **0.5%** (`50 bps`)
- **Platform Net Retained Margin**: **91.5%** (`9,150 bps`)

### Worked Example (₹57,000 Booking)
For 2 passengers on the *Kedarnath & Badrinath Sacred Do Dham Yatra* (₹28,500 × 2 = **₹57,000.00**):
- **Tier 1 (Kabir Singh, WW-1004)**: ₹57,000 × 5.0% = **₹2,850.00**
- **Tier 2 (Nisha Rao, WW-1003)**: ₹57,000 × 2.0% = **₹1,140.00**
- **Tier 3 (Rohan Das, WW-1002)**: ₹57,000 × 1.0% = **₹570.00**
- **Tier 4 (Priya Sharma, WW-1001)**: ₹57,000 × 0.5% = **₹285.00**
- **Total Partner Network Commission**: **₹4,845.00 (8.5%)**
- **Wanderwise Net Retained Margin**: **₹52,155.00 (91.5%)**

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
