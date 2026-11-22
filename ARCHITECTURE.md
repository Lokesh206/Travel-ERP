# Wanderwise Travel ERP Architecture

## System Overview

```mermaid
flowchart TB
    subgraph Users["Users"]
        Visitor["Public visitor"]
        Customer["Customer"]
        Agent["Travel agent"]
        Admin["Administrator"]
    end

    subgraph Presentation["Presentation tier"]
        PublicUI["Public marketplace<br/>Jinja2 templates"]
        Workspace["Role-based workspace<br/>Jinja2 dashboard"]
        Assets["HTML5 / CSS3 / images"]
    end

    subgraph Application["Flask application tier"]
        Router["HTTP route controllers<br/>app.py"]
        Session["Secure session cookies"]
        Auth["Authentication<br/>Scrypt password hashing"]
        Security["CSRF protection<br/>Login and role guards"]

        subgraph Services["Business workflows"]
            Marketplace["Package discovery"]
            Booking["Reservation and payment state"]
            Inventory["Atomic seat allocation"]
            Commission["Four-level commission engine"]
            Wallet["Wallet and payout workflow"]
            Email["Transactional email audit"]
            Inquiry["Contact inquiry management"]
            Audit["Immutable operational audit"]
        end
    end

    subgraph Persistence["Persistence tier"]
        SQLite[("SQLite3 database")]

        subgraph Tables["Core tables"]
            Identity["users<br/>agents"]
            Catalog["packages<br/>package_details"]
            Reservations["bookings"]
            Money["wallet_transactions<br/>withdrawals<br/>commission_rules"]
            Operations["sent_emails<br/>reviews<br/>contact_inquiries<br/>audit_logs"]
        end
    end

    Visitor --> PublicUI
    Customer --> Workspace
    Agent --> Workspace
    Admin --> Workspace
    PublicUI --> Assets
    PublicUI --> Router
    Workspace --> Router
    Router --> Session
    Router --> Auth
    Router --> Security
    Security --> Services
    Session --> Auth

    Marketplace --> SQLite
    Booking --> Inventory
    Inventory --> SQLite
    Booking --> Email
    Booking --> Reservations
    Commission --> Wallet
    Commission --> Money
    Wallet --> SQLite
    Email --> SQLite
    Inquiry --> SQLite
    Audit --> SQLite
    Catalog --> SQLite
    Identity --> SQLite
    Reservations --> SQLite
    Money --> SQLite
    Operations --> SQLite
```

## Request Flow

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant Flask as Flask app.py
    participant Guard as Auth / CSRF / RBAC
    participant DB as SQLite3

    User->>Browser: Open public page or sign in
    Browser->>Flask: HTTP GET / POST
    Flask->>Flask: Open database connection
    Flask->>Guard: Load session and validate request
    alt Unauthorized or invalid CSRF
        Guard-->>Browser: Redirect or 403 / 400
    else Authorized
        Guard->>Flask: Invoke route handler
        Flask->>DB: Query or transaction
        DB-->>Flask: Rows or transaction result
        Flask-->>Browser: Render Jinja2 HTML / redirect
    end
    Flask->>DB: Close per-request connection
```

## Booking Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending: Pay on desk / reserve
    [*] --> Confirmed: UPI / card / net banking
    Pending --> Confirmed: Online payment
    Pending --> Cancelled: Customer / agent / admin cancellation
    Confirmed --> Completed: Admin completes trip
    Confirmed --> Cancelled: Agent / admin cancellation
    Completed --> [*]
    Cancelled --> [*]
```

The booking workflow:

1. Reads an active package and checks available capacity.
2. Allocates seats atomically by updating `reserved` in the database.
3. Creates a booking with its travel dates, traveller count, total in paise, payment details, and optional agent referral.
4. Logs the confirmation or reservation email in `sent_emails`.
5. Allows an admin to complete confirmed trips.
6. Walks the agent upline and credits four commission levels based on `commission_rules`.

Cancelled bookings restore their reserved seat count. Monetary values use integer paise rather than floating-point currency values.

## Relational Model

```mermaid
erDiagram
    USERS ||--o| AGENTS : "has partner profile"
    USERS ||--o{ BOOKINGS : "places"
    USERS ||--o{ REVIEWS : "writes"
    USERS ||--o{ AUDIT_LOGS : "performed"

    AGENTS ||--o{ AGENTS : "has parent upline"
    AGENTS ||--o{ BOOKINGS : "refers"
    AGENTS ||--o{ WALLET_TRANSACTIONS : "earns or withdraws"
    AGENTS ||--o{ WITHDRAWALS : "requests"

    PACKAGES ||--|| PACKAGE_DETAILS : "has itinerary"
    PACKAGES ||--o{ BOOKINGS : "reserved by"

    BOOKINGS ||--o| REVIEWS : "has"
    BOOKINGS ||--o{ SENT_EMAILS : "generates"

    USERS {
        integer id PK
        text name
        text email UK
        text password_hash
        text role
        text created_at
    }

    AGENTS {
        integer id PK
        integer user_id FK
        text code UK
        integer level
        integer parent_id FK
    }

    PACKAGES {
        integer id PK
        text title
        text destination
        text category
        integer price_paise
        integer capacity
        integer reserved
        text status
    }

    PACKAGE_DETAILS {
        integer package_id PK_FK
        text stay_type
        text meal_plan
        text transport
        text inclusions
        text itinerary
    }

    BOOKINGS {
        integer id PK
        text reference UK
        integer customer_id FK
        integer agent_id FK
        integer package_id FK
        text travel_date
        text return_date
        integer travellers
        integer total_paise
        text status
        text payment_method
        text payment_ref
    }

    WALLET_TRANSACTIONS {
        integer id PK
        integer agent_id FK
        integer amount_paise
        text kind
        text reference
    }

    WITHDRAWALS {
        integer id PK
        integer agent_id FK
        integer amount_paise
        text status
        integer reviewed_by FK
    }

    COMMISSION_RULES {
        integer level PK
        integer rate_bps
    }
```

## Runtime and Deployment

- **Runtime:** Python 3.10+ and Flask 3.x.
- **Application server:** Development server started by `python app.py` or `run.bat`.
- **Database:** Local SQLite3 file (`travel_erp.sqlite3`) with foreign keys enabled.
- **Presentation:** Server-side Jinja2 templates plus CSS and static image assets.
- **Seed scripts:** `seed_data.py` maintains package catalog and `seed_real_world.py` creates demo operational data.
- **Configuration:** Optional `TRAVEL_ERP_DATABASE`, `TRAVEL_ERP_SECRET`, and `TRAVEL_ERP_HTTPS` environment variables.
