# 🚀 How to Host Wanderwise Travel ERP on Render (Free Tier)

This guide walks you through deploying **Wanderwise Travel ERP** on [Render](https://render.com) in less than 3 minutes using the free tier.

---

## 📋 What Was Prepared in Your Codebase

Your repository has already been pre-configured with everything Render requires:
1. **`render.yaml`**: Render Blueprint configuration for automated infrastructure deployment.
2. **`Procfile`**: Process definition instructing Render to boot the production WSGI server (`gunicorn`).
3. **`requirements.txt`**: Includes `Flask` and `gunicorn`.
4. **`.python-version`**: Pinned to Python `3.11.9`.
5. **Auto-seeding Engine**: On initial startup, the database automatically creates all tables, seeds the single Administrator (**Aarav Mehta**), partner agents, traveler profile (**Lokesh**), and all **16 Indian tour packages and itineraries** with zero fake bookings.

---

## 🛠️ Step-by-Step Deployment Instructions

### Method 1: Blueprint Deployment (Fastest & Recommended)

1. **Sign in to Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com/) and log in (or sign up with your GitHub account).

2. **Create New Blueprint Instance**:
   - In the top-right corner, click the **New +** button.
   - Select **Blueprint**.

3. **Connect Your GitHub Repository**:
   - Search for or select your repository: **`Lokesh206/Travel-ERP`**.
   - Click **Connect**.

4. **Approve and Deploy**:
   - Render reads `render.yaml` directly from your repository.
   - Click **Apply**.
   - Render will build your application, install dependencies, initialize database tables and seed all 16 packages, and launch Gunicorn.
   - Within 1–2 minutes, your live URL (e.g., `https://wanderwise-travel-erp.onrender.com`) will be active!

---

### Method 2: Manual Web Service Setup

If you prefer to configure the Web Service manually:

1. **Create New Web Service**:
   - In the Render dashboard, click **New +** ➔ **Web Service**.
   - Select **Build and deploy from a Git repository** ➔ **Next**.
   - Choose **`Lokesh206/Travel-ERP`** ➔ Click **Connect**.

2. **Configure Service Details**:
   - **Name**: `wanderwise-travel-erp` (or any custom name)
   - **Region**: Oregon (US West), Frankfurt (EU), or Singapore (Asia)
   - **Branch**: `main`
   - **Root Directory**: *(Leave blank)*
   - **Runtime**: **Python 3**
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python -c "from app import initialize_db; initialize_db()"
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
     ```
   - **Instance Type**: Select **Free** ($0/month).

3. **Add Environment Variables**:
   Click **Advanced** ➔ **Add Environment Variable**:
   - `PYTHON_VERSION`: `3.11.9`
   - `TRAVEL_ERP_SECRET`: Click *Generate* (or enter a random 32-character string)
   - `FLASK_ENV`: `production`

4. **Click Deploy**:
   - Click **Create Web Service**.
   - Watch the deployment logs in real time.
   - Once it logs `Listening at: http://0.0.0.0:...`, your site is live!

---

## 🔑 Live Sample Credentials for Evaluation

Once your Render app is live, use these credentials to test:

| Role | Name | Email | Password | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **👑 Administrator** | **Aarav Mehta** | `admin@wanderwise.local` | `Admin@123` | Master executive dashboard, booking management, dispatched emails audit, commission controls |
| **💼 Agent (Partner)** | **Priya Sharma** | `agent@wanderwise.local` | `Agent@123` | Partner referral portal (`WW-1001`), Book for Client ↗, manual cancellation with seat restoration |
| **✈️ Traveler** | **Lokesh M M Ankith** | `lokeshmmankith@gmail.com` | `Lokesh@123` | Direct customer bookings, interactive UPI QR code payment, official printable soft-copy vouchers |

*(On the login page, clicking the **👑 Admin**, **💼 Agent**, or **✈️ Traveler** button will automatically pre-fill these credentials in 1 click).*

---

## 💡 Notes on Render Free Tier

1. **Spin Down After Inactivity**:
   - Free Web Services spin down after 15 minutes of inactivity. When a new visitor opens the URL, Render wakes it up in about 30–50 seconds.
2. **Ephemeral Disk**:
   - The free tier uses an ephemeral filesystem. On spin-down or new deployment, the database re-seeds automatically to the pristine state with 0 dummy bookings, ensuring the app never breaks or fails.
3. **Optional Persistent Storage**:
   - If you ever upgrade to a paid Render plan and attach a persistent disk (e.g. mounted at `/var/data`), simply add the environment variable:
     `TRAVEL_ERP_DATABASE=/var/data/travel_erp.sqlite3`
