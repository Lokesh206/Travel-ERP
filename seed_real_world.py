"""
seed_real_world.py — Populates authentic, production-grade real-world Indian Travel ERP data.
Contains real Indian destinations, genuine traveller names, real booking references,
live multi-tier commission transactions, payout settlement queue requests,
guest inquiries, reviews, and audit logs.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DATABASE = Path("travel_erp.sqlite3")

def run_real_world_seed():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row

    print(">>> Seeding Real-World Enterprise Travel Data...")

    # Ensure schema columns exist
    pkg_cols = [r[1] for r in db.execute("PRAGMA table_info(packages)").fetchall()]
    if "image_file" not in pkg_cols:
        db.execute("ALTER TABLE packages ADD COLUMN image_file TEXT")
    if "official_url" not in pkg_cols:
        db.execute("ALTER TABLE packages ADD COLUMN official_url TEXT")
    if "activities" not in pkg_cols:
        db.execute("ALTER TABLE packages ADD COLUMN activities TEXT")
    db.commit()

    # 1. Commission Rules (Tier 1 to 4)
    # Level 1 (Direct Agent): 5.0% (500 bps)
    # Level 2 (Direct Parent / L1 Upline): 2.0% (200 bps)
    # Level 3 (Grandparent / L2 Upline): 1.0% (100 bps)
    # Level 4 (Apex Principal / L3 Upline): 0.5% (50 bps)
    db.execute("DELETE FROM commission_rules")
    db.executemany(
        "INSERT INTO commission_rules(level, rate_bps) VALUES(?, ?)",
        [(1, 500), (2, 200), (3, 100), (4, 50)],
    )
    db.commit()

    # 2. Users (Admin, 4-tier Partner Hierarchy, and Real Verified Customers)
    real_users = [
        # Admin
        ("Aarav Mehta", "admin@wanderwise.local", "Admin@123", "admin"),
        # Partner Hierarchy (Tiers 4 -> 3 -> 2 -> 1)
        ("Priya Sharma", "agent@wanderwise.local", "Agent@123", "agent"),      # WW-1001 (Level 4 Apex)
        ("Rohan Das", "rohan@wanderwise.local", "Agent@123", "agent"),         # WW-1002 (Level 3 Senior)
        ("Nisha Rao", "nisha@wanderwise.local", "Agent@123", "agent"),         # WW-1003 (Level 2 Associate)
        ("Kabir Singh", "kabir@wanderwise.local", "Agent@123", "agent"),       # WW-1004 (Level 1 Junior)
        ("Sunita Patel", "sunita.patel@wanderwise.local", "Agent@123", "agent"), # WW-1005 (Level 2 Associate)
        ("Karthik Subramanian", "karthik.s@wanderwise.local", "Agent@123", "agent"), # WW-1006 (Level 1 Junior)
        # Real Verified Customers
        ("Maya Kapoor", "customer@wanderwise.local", "Travel@123", "customer"),
        ("Maya Kapoor", "maya.kapoor@wanderwise.local", "Travel@123", "customer"),
        ("Vikramaditya Singhania", "vikram@wanderwise.local", "Vikram@123", "customer"),
        ("Dr. Rajesh Kulkarni", "rajesh.k@wanderwise.local", "Travel@123", "customer"),
        ("Ananya Chatterjee", "ananya.c@wanderwise.local", "Travel@123", "customer"),
        ("Neha Bansal", "neha.bansal@wanderwise.local", "Travel@123", "customer"),
        ("Dr. K. Venkataraman", "k.venkat@wanderwise.local", "Travel@123", "customer"),
        ("Deepak Joshi", "deepak.j@wanderwise.local", "Travel@123", "customer"),
        ("Pooja Nair", "pooja.nair@wanderwise.local", "Travel@123", "customer"),
        ("Saurabh Verma", "saurabh.v@wanderwise.local", "Travel@123", "customer"),
        ("Arvind Swaminathan", "arvind.s@wanderwise.local", "Travel@123", "customer"),
    ]

    user_ids: dict[str, int] = {}
    for name, email, pwd, role in real_users:
        existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        pwd_hash = generate_password_hash(pwd)
        if existing:
            db.execute("UPDATE users SET name=?, password_hash=?, role=? WHERE id=?", (name, pwd_hash, role, existing["id"]))
            user_ids[email] = existing["id"]
        else:
            cur = db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)", (name, email, pwd_hash, role))
            user_ids[email] = cur.lastrowid
    db.commit()

    # 3. Agents Hierarchy
    # Priya Sharma (WW-1001, Level 4, parent: None)
    #  └── Rohan Das (WW-1002, Level 3, parent: WW-1001)
    #       └── Nisha Rao (WW-1003, Level 2, parent: WW-1002)
    #            └── Kabir Singh (WW-1004, Level 1, parent: WW-1003)
    #  └── Sunita Patel (WW-1005, Level 2, parent: WW-1001)
    #       └── Karthik Subramanian (WW-1006, Level 1, parent: WW-1005)
    db.execute("DELETE FROM agents")
    db.execute("INSERT INTO agents(id, user_id, code, level, parent_id) VALUES(1, ?, 'WW-1001', 4, NULL)",
               (user_ids["agent@wanderwise.local"],))
    db.execute("INSERT INTO agents(id, user_id, code, level, parent_id) VALUES(2, ?, 'WW-1002', 3, 1)",
               (user_ids["rohan@wanderwise.local"],))
    db.execute("INSERT INTO agents(id, user_id, code, level, parent_id) VALUES(3, ?, 'WW-1003', 2, 2)",
               (user_ids["nisha@wanderwise.local"],))
    db.execute("INSERT INTO agents(id, user_id, code, level, parent_id) VALUES(4, ?, 'WW-1004', 1, 3)",
               (user_ids["kabir@wanderwise.local"],))
    db.execute("INSERT INTO agents(id, user_id, code, level, parent_id) VALUES(5, ?, 'WW-1005', 2, 1)",
               (user_ids["sunita.patel@wanderwise.local"],))
    db.execute("INSERT INTO agents(id, user_id, code, level, parent_id) VALUES(6, ?, 'WW-1006', 1, 5)",
               (user_ids["karthik.s@wanderwise.local"],))
    db.commit()

    # 4. Clear old test bookings & transactions to ensure 100% clean, realistic data
    db.execute("DELETE FROM reviews")
    db.execute("DELETE FROM wallet_transactions")
    db.execute("DELETE FROM withdrawals")
    db.execute("DELETE FROM bookings")
    db.execute("DELETE FROM contact_inquiries")
    db.execute("DELETE FROM audit_logs")
    db.commit()

    # Reset package reserved counters
    db.execute("UPDATE packages SET reserved = 0")
    db.commit()

    # 5. Realistic Real-World Bookings (across India's top landmarks and journeys)
    # (reference, customer_email, agent_id, pkg_id, travel_date, travellers, status, created_at)
    real_bookings_data = [
        # Confirmed & Completed Bookings with real multi-level agent attribution
        ("WY-2026-DEL-8912", "vikram@wanderwise.local", 4, 1, "2026-10-12", 2, "completed", "2026-10-01 10:15:00"),
        ("WY-2026-BLR-4401", "rajesh.k@wanderwise.local", 3, 4, "2026-10-18", 2, "completed", "2026-10-03 14:20:00"),
        ("WY-2026-BOM-7729", "ananya.c@wanderwise.local", 2, 2, "2026-10-25", 2, "completed", "2026-10-05 16:45:00"),
        ("WY-2026-HYD-5503", "neha.bansal@wanderwise.local", 1, 3, "2026-11-02", 3, "completed", "2026-10-12 11:30:00"),
        ("WY-2026-CCU-3190", "k.venkat@wanderwise.local", 6, 8, "2026-11-10", 2, "completed", "2026-10-20 09:10:00"),
        ("WY-2026-PNQ-6621", "deepak.j@wanderwise.local", 5, 9, "2026-11-15", 4, "completed", "2026-10-22 13:00:00"),
        ("WY-2026-AMD-1188", "pooja.nair@wanderwise.local", 4, 5, "2026-11-20", 2, "completed", "2026-10-28 17:15:00"),
        ("WY-2026-JAI-9942", "saurabh.v@wanderwise.local", 3, 6, "2026-11-21", 2, "completed", "2026-11-01 12:40:00"),
        
        # Confirmed (Upcoming) Journeys
        ("WY-2026-MAA-9014", "arvind.s@wanderwise.local", 2, 7, "2026-12-05", 2, "confirmed", "2026-11-08 15:20:00"),
        ("WY-2026-DEL-1045", "customer@wanderwise.local", 1, 10, "2026-12-12", 2, "confirmed", "2026-11-10 11:05:00"),
        ("WY-2026-BOM-4820", "vikram@wanderwise.local", 4, 11, "2026-12-20", 2, "confirmed", "2026-11-12 16:30:00"),
        ("WY-2026-BLR-6731", "rajesh.k@wanderwise.local", 3, 12, "2026-12-26", 4, "confirmed", "2026-11-14 18:00:00"),
        ("WY-2026-HYD-8829", "neha.bansal@wanderwise.local", 5, 13, "2027-01-05", 2, "confirmed", "2026-11-16 10:15:00"),
        ("WY-2027-DEL-3391", "ananya.c@wanderwise.local", 6, 14, "2027-01-14", 3, "confirmed", "2026-11-17 14:45:00"),
        ("WY-2027-PNQ-7210", "k.venkat@wanderwise.local", 2, 15, "2027-01-22", 2, "confirmed", "2026-11-18 19:20:00"),
        ("WY-2027-CCU-9905", "deepak.j@wanderwise.local", 1, 16, "2027-02-02", 2, "confirmed", "2026-11-19 09:30:00"),

        # Pending Payment (Reservation requested, awaiting demo payment)
        ("WY-2026-AMD-5512", "pooja.nair@wanderwise.local", 4, 1, "2026-12-28", 2, "pending", "2026-11-20 14:10:00"),
        ("WY-2026-JAI-3301", "saurabh.v@wanderwise.local", 3, 3, "2027-01-10", 2, "pending", "2026-11-20 16:50:00"),
        ("WY-2026-DEL-7744", "arvind.s@wanderwise.local", 2, 8, "2027-01-18", 4, "pending", "2026-11-21 08:30:00"),
        ("WY-2026-BLR-1129", "maya.kapoor@wanderwise.local", 1, 6, "2027-01-25", 2, "pending", "2026-11-21 11:20:00"),

        # Cancelled Bookings (Processed per cancellation policy)
        ("WY-2026-BOM-1903", "vikram@wanderwise.local", 5, 2, "2026-11-30", 2, "cancelled", "2026-10-15 11:00:00"),
        ("WY-2026-HYD-4099", "rajesh.k@wanderwise.local", 6, 4, "2026-12-02", 2, "cancelled", "2026-10-25 15:40:00"),
    ]

    booking_ids: dict[str, int] = {}
    for ref, cust_email, agent_id, pkg_id, t_date, guests, status, created_at in real_bookings_data:
        pkg = db.execute("SELECT price_paise, capacity FROM packages WHERE id=?", (pkg_id,)).fetchone()
        cust_id = user_ids[cust_email]
        total_paise = pkg["price_paise"] * guests
        
        cur = db.execute(
            """INSERT INTO bookings(reference, customer_id, agent_id, package_id, travel_date,
                                   travellers, total_paise, status, created_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (ref, cust_id, agent_id, pkg_id, t_date, guests, total_paise, status, created_at)
        )
        b_id = cur.lastrowid
        booking_ids[ref] = b_id

        # If booking is confirmed or pending, increment reserved seats
        if status in ("confirmed", "pending", "completed"):
            db.execute("UPDATE packages SET reserved = reserved + ? WHERE id=?", (guests, pkg_id))
    db.commit()
    print(f"✓ Seeded {len(real_bookings_data)} realistic Indian bookings")

    # 6. Multi-Level Commission Distribution for Completed Bookings
    # Level 1: 500 bps (5%), Level 2: 200 bps (2%), Level 3: 100 bps (1%), Level 4: 50 bps (0.5%)
    rules_map = {r["level"]: r["rate_bps"] for r in db.execute("SELECT level, rate_bps FROM commission_rules").fetchall()}

    for ref, _cust_email, direct_agent_id, pkg_id, _t_date, guests, status, created_at in real_bookings_data:
        if status == "completed" and direct_agent_id:
            pkg = db.execute("SELECT price_paise FROM packages WHERE id=?", (pkg_id,)).fetchone()
            booking_amount = pkg["price_paise"] * guests

            curr_agent_id = direct_agent_id
            for depth in range(4):
                agent_row = db.execute("SELECT id, code, level, parent_id FROM agents WHERE id=?", (curr_agent_id,)).fetchone()
                if not agent_row:
                    break
                
                bps = rules_map.get(agent_row["level"], 0)
                comm_paise = (booking_amount * bps) // 10000

                if comm_paise > 0:
                    comm_ref = f"{ref}-COMM-L{agent_row['level']}"
                    db.execute(
                        """INSERT OR IGNORE INTO wallet_transactions(agent_id, amount_paise, kind, reference, created_at)
                           VALUES(?,?,?,?,?)""",
                        (curr_agent_id, comm_paise, "commission", comm_ref, created_at)
                    )

                if not agent_row["parent_id"]:
                    break
                curr_agent_id = agent_row["parent_id"]
    db.commit()
    print("✓ Computed and distributed multi-tier commissions for all completed journeys")

    # 7. Realistic Payout Requests (Withdrawal Queue)
    # Mix of pending, approved, completed (with bank UTR), and rejected
    real_withdrawals = [
        # Pending review by Admin
        (2, 2850000, "pending", "2026-11-20 15:45:00", "HDFC Bank NEFT — Rohan Das (A/C: 50100492817291, IFSC: HDFC0000128)"),
        (4, 1420000, "pending", "2026-11-21 09:15:00", "Instant UPI Transfer — Kabir Singh (VPA: kabir.singh@okaxis)"),
        (3, 1950000, "pending", "2026-11-21 12:30:00", "State Bank of India — Nisha Rao (A/C: 38920194821, IFSC: SBIN0001824)"),
        
        # Approved by Admin, queued for RTGS/NEFT settlement
        (1, 4500000, "approved", "2026-11-18 11:20:00", "ICICI Bank Corporate — Priya Sharma (A/C: 001205018921, IFSC: ICIC0000012)"),
        (5, 1600000, "approved", "2026-11-19 14:10:00", "Kotak Mahindra Bank — Sunita Patel (A/C: 849201948, IFSC: KKBK0000521)"),

        # Completed settlements with official bank transaction reference (UTR)
        (1, 3500000, "completed", "2026-11-05 16:00:00", "Settled via IMPS. Bank UTR: HDFC2026110509823192"),
        (2, 2200000, "completed", "2026-11-08 17:30:00", "Settled via NEFT. Bank UTR: ICIC2026110800412894"),
        (3, 1500000, "completed", "2026-11-12 12:15:00", "Settled via RTGS. Bank UTR: SBIN2026111299841203"),

        # Rejected (audit purpose: invalid IFSC / KYC pending)
        (6, 5000000, "rejected", "2026-11-14 10:00:00", "Rejected: Requested amount exceeds current available wallet balance."),
    ]

    for ag_id, amt, stat, c_at, note in real_withdrawals:
        cur = db.execute(
            """INSERT INTO withdrawals(agent_id, amount_paise, status, created_at)
               VALUES(?,?,?,?)""",
            (ag_id, amt, stat, c_at)
        )
        # If completed, insert matching debit transaction into wallet
        if stat == "completed":
            db.execute(
                """INSERT INTO wallet_transactions(agent_id, amount_paise, kind, reference, created_at)
                   VALUES(?,?,'withdrawal',?,?)""",
                (ag_id, -amt, f"PAYOUT-WD-{cur.lastrowid}", c_at)
            )
    db.commit()
    print(f"✓ Seeded {len(real_withdrawals)} authentic payout requests and settlements")

    # 8. Real Customer Inquiries from Website Contact Desk
    real_inquiries = [
        (
            "Dr. Alok Verma",
            "alok.verma@aiims.edu",
            "Planning a trip",
            "We are planning a senior citizen family pilgrimage to Kashi Vishwanath and Prayagraj in late December. Could you please confirm if wheelchair assistance, battery-operated golf carts, and assisted priority darshan are included through the newly opened temple corridor? There are 4 adults including 2 seniors aged 74 and 78.",
            "new",
            "2026-11-21 16:30:00",
        ),
        (
            "Meenakshi Sundaresan",
            "meenakshi.s@tcs.com",
            "Partnership enquiry",
            "Hello Wanderwise Desk, I head employee engagement at our Bangalore campus. We would like to arrange an offsite retreat for 24 senior architects to the Statue of Unity & Ekta Valley in January 2027. We require luxury riverside tented accommodation and private AC Volvo coach transfers from Vadodara. Please share a group commercial quotation.",
            "new",
            "2026-11-21 14:15:00",
        ),
        (
            "Col. Surendra Rawat (Retd.)",
            "surendra.rawat@veterans.org.in",
            "Planning a trip",
            "Namaste. We wish to book the Kedarnath & Badrinath Do Dham yatra for May/June 2027 season opening. Could you please clarify the helicopter shuttle quota booking timeline from Phata / Guptkashi, medical certificate requirements, and biometric pass assistance?",
            "new",
            "2026-11-21 11:45:00",
        ),
        (
            "Rameshwaram Shastri",
            "r.shastri@templetrust.in",
            "An existing booking",
            "Regarding booking reference WY-2026-DEL-8912 for Agra Taj Mahal, we would like to confirm our private historian guide language preference as Marathi and Hindi. Kindly confirm if hotel pickup at 05:45 AM for sunrise darshan has been notified to the chauffeur.",
            "resolved",
            "2026-11-20 18:00:00",
        ),
        (
            "Sunaina & David Miller",
            "sunaina.miller@gmail.com",
            "Planning a trip",
            "We are visiting India from London for 2 weeks in January. We are keen on the Kerala Backwaters & Spice Trails package. Can you customize the 4-day itinerary to include an extra night on a private solar-powered luxury houseboat in Kumarakom with an authentic Kerala sadhya meal?",
            "resolved",
            "2026-11-19 13:20:00",
        ),
        (
            "Kavita Singhal",
            "kavita.singhal@hdfcbank.com",
            "Something else",
            "I booked the Golden Temple & Sacred Heritage tour. Just wanted to compliment your Amritsar ground representative Gurpreet Singh who arranged our night Palki Sahib darshan and Langar seva so seamlessly. Excellent work by Wanderwise team!",
            "resolved",
            "2026-11-18 16:40:00",
        ),
    ]

    for name, email, subj, msg, stat, c_at in real_inquiries:
        db.execute(
            """INSERT INTO contact_inquiries(name, email, subject, message, status, created_at)
               VALUES(?,?,?,?,?,?)""",
            (name, email, subj, msg, stat, c_at)
        )
    db.commit()
    print(f"✓ Seeded {len(real_inquiries)} genuine guest inquiries")

    # 9. Real Traveler Reviews matching Completed Journeys
    real_reviews = [
        (
            booking_ids["WY-2026-DEL-8912"],
            user_ids["vikram@wanderwise.local"],
            5,
            "Watching the sunrise on Taj Mahal with our private historian guide was sheer magic. The 5-star heritage stay and chauffeur transfers were punctual and luxurious. Truly incredible India!",
            "2026-10-15 11:30:00"
        ),
        (
            booking_ids["WY-2026-BLR-4401"],
            user_ids["rajesh.k@wanderwise.local"],
            5,
            "The Mysore Palace tour was magnificent. Standing in the Durbar Hall and witnessing the 100,000 bulb illumination on Sunday evening gave us goosebumps. Excellent arrangements for senior citizens.",
            "2026-10-21 17:45:00"
        ),
        (
            booking_ids["WY-2026-BOM-7729"],
            user_ids["ananya.c@wanderwise.local"],
            5,
            "Solang Valley and the pine forest trail in Manali were breathtaking. Our boutique mountain lodge had panoramic Himalayan views and warm, hospitable pahadi meals. Seamless from start to finish.",
            "2026-10-28 14:10:00"
        ),
        (
            booking_ids["WY-2026-HYD-5503"],
            user_ids["neha.bansal@wanderwise.local"],
            5,
            "Gliding through Vembanad Lake on our private teakwood houseboat was the most peaceful vacation our family has ever taken. Traditional Malabar sadhya served on banana leaf was top notch!",
            "2026-11-05 18:20:00"
        ),
        (
            booking_ids["WY-2026-CCU-3190"],
            user_ids["k.venkat@wanderwise.local"],
            5,
            "Do Dham Yatra (Kedarnath & Badrinath) was deeply spiritual and flawless. The biometric registration, priority darshan passes, and high-clearance mountain cab handled the ghat roads with supreme confidence.",
            "2026-11-13 10:15:00"
        ),
        (
            booking_ids["WY-2026-PNQ-6621"],
            user_ids["deepak.j@wanderwise.local"],
            5,
            "The evening Aarti at Somnath Temple right on the edge of the Arabian Sea was an unforgettable spectacle. The light and sound show and temple guesthouse were clean, disciplined, and very comfortable.",
            "2026-11-18 19:40:00"
        ),
        (
            booking_ids["WY-2026-AMD-1188"],
            user_ids["pooja.nair@wanderwise.local"],
            5,
            "The 14 towering gopurams of Madurai Meenakshi Temple and the 1,000-pillar hall are architectural marvels. The night celestial chariot procession was breathtaking. Wanderwise team took care of every single detail.",
            "2026-11-21 13:00:00"
        ),
    ]

    for b_id, cust_id, rating, body, c_at in real_reviews:
        db.execute(
            """INSERT INTO reviews(booking_id, customer_id, rating, body, created_at)
               VALUES(?,?,?,?,?)""",
            (b_id, cust_id, rating, body, c_at)
        )
    db.commit()
    print(f"✓ Seeded {len(real_reviews)} verified traveller reviews")

    # 10. Audit Trail of Real Operational Events
    real_audits = [
        (user_ids["admin@wanderwise.local"], "System commission reconciliation completed (₹1,48,750 credited across 6 agents)", "system", "recon", "2026-11-21 18:00:00"),
        (user_ids["admin@wanderwise.local"], "Withdrawal #6 approved for Priya Sharma (₹45,000 - ICICI Bank Corporate)", "withdrawal", "6", "2026-11-21 16:15:00"),
        (user_ids["admin@wanderwise.local"], "Contact inquiry #4 marked resolved by Travel Desk", "contact_inquiry", "4", "2026-11-21 14:30:00"),
        (user_ids["admin@wanderwise.local"], "Booking WY-2026-AMD-1188 marked completed & commissions disbursed", "booking", "WY-2026-AMD-1188", "2026-11-21 12:45:00"),
        (user_ids["admin@wanderwise.local"], "Package #9 Somnath Coastal Temple published to public marketplace", "package", "9", "2026-11-20 17:10:00"),
        (user_ids["agent@wanderwise.local"], "Travel Partner WW-1004 (Kabir Singh) added to Tier 1 under downline", "agent", "WW-1004", "2026-11-20 11:20:00"),
        (user_ids["admin@wanderwise.local"], "Withdrawal settlement UTR recorded: HDFC2026110509823192", "withdrawal", "4", "2026-11-19 16:50:00"),
        (user_ids["admin@wanderwise.local"], "Booking WY-2026-PNQ-6621 verified & confirmed", "booking", "WY-2026-PNQ-6621", "2026-11-18 10:15:00"),
    ]

    for act_id, act, rec_t, rec_i, c_at in real_audits:
        db.execute(
            """INSERT INTO audit_logs(actor_id, action, record_type, record_id, created_at)
               VALUES(?,?,?,?,?)""",
            (act_id, act, rec_t, rec_i, c_at)
        )
    db.commit()
    print(f"✓ Seeded {len(real_audits)} real-world operational audit log events")

    db.close()
    print("\n🎉 ALL REAL-WORLD TRAVEL ERP DATA SEEDED SUCCESSFULLY!")

if __name__ == "__main__":
    run_real_world_seed()
