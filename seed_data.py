from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DATABASE = Path(
    os.environ.get("TRAVEL_ERP_DATABASE", Path(__file__).resolve().parent / "travel_erp.sqlite3")
)

def run_seed():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row

    cols = [r[1] for r in db.execute("PRAGMA table_info(packages)").fetchall()]
    if "image_file" not in cols:
        db.execute("ALTER TABLE packages ADD COLUMN image_file TEXT")
    if "official_url" not in cols:
        db.execute("ALTER TABLE packages ADD COLUMN official_url TEXT")
    if "activities" not in cols:
        db.execute("ALTER TABLE packages ADD COLUMN activities TEXT")
    db.commit()

    existing_updates = {
        "Coastal calm, Goa": (
            "gallery-coast.jpg",
            "https://goa-tourism.com/",
            "Sunset beach walks, Old Goa cathedral walk, coastal catamaran cruise",
        ),
        "Into the Himalayas": (
            "gallery-himalaya.jpg",
            "https://himachaltourism.gov.in/",
            "Pine forest nature trail, Solang valley excursion, Old Manali cafe trail",
        ),
        "Backwaters & beyond": (
            "gallery-backwaters.jpg",
            "https://www.keralatourism.org/",
            "Vembanad backwater cruise, spice plantation tour, village canoe ride",
        ),
        "Desert after dark": (
            "gallery-desert.jpg",
            "https://www.tourism.rajasthan.gov.in/",
            "Jaisalmer Fort walk, Sam sand dunes camel safari, starry desert camp dinner",
        ),
    }
    for title, (img, url, acts) in existing_updates.items():
        db.execute(
            "UPDATE packages SET image_file=?, official_url=?, activities=? WHERE title=?",
            (img, url, acts, title),
        )
    db.commit()

    new_places = [
        (
            "Coastal calm, Goa",
            "Goa, India",
            "Beach",
            "Slow mornings, golden-hour shores and a stay made for switching off.",
            "3 days · 2 nights",
            1200000,
            24,
            "gallery-coast.jpg",
            "https://goa-tourism.com/",
            "Sunset beach walks, Old Goa cathedral walk, coastal catamaran cruise",
            (
                "Boutique beach hotel",
                "Daily breakfast",
                "Airport transfers and local transfers",
                "2 nights’ accommodation\nDaily breakfast\nAirport transfers\nLocal travel desk support",
                "Day 1 — Arrive in Goa, check in and enjoy a relaxed beach evening.\nDay 2 — Explore the coastline and nearby markets at your own pace.\nDay 3 — Breakfast, check out and depart.",
            ),
        ),
        (
            "Into the Himalayas",
            "Manali, India",
            "Adventure",
            "Mountain air, pine trails and a tucked-away boutique mountain stay.",
            "5 days · 4 nights",
            1850000,
            18,
            "gallery-himalaya.jpg",
            "https://himachaltourism.gov.in/",
            "Pine forest nature trail, Solang valley excursion, Old Manali cafe trail",
            (
                "Boutique mountain lodge",
                "Daily breakfast",
                "Private local transfers",
                "4 nights’ accommodation\nDaily breakfast\nLocal transfers\nGuided nature walk",
                "Day 1 — Arrive in Manali and settle into your mountain lodge.\nDay 2 — Explore the old town and nearby viewpoints.\nDay 3 — Take a guided nature walk through pine-scented trails.\nDay 4 — Enjoy a flexible day for local sightseeing.\nDay 5 — Breakfast, check out and depart.",
            ),
        ),
        (
            "Backwaters & beyond",
            "Alappuzha, India",
            "Culture",
            "Drift through Kerala’s backwaters, spice gardens and leafy landscapes.",
            "4 days · 3 nights",
            1500000,
            15,
            "gallery-backwaters.jpg",
            "https://www.keralatourism.org/",
            "Vembanad backwater cruise, spice plantation tour, village canoe ride",
            (
                "Heritage homestay and one houseboat night",
                "Breakfast and one traditional lunch",
                "Local transfers and backwater cruise",
                "3 nights’ accommodation\nBreakfast and one traditional lunch\nBackwater cruise\nLocal travel desk support",
                "Day 1 — Arrive in Alappuzha and check in.\nDay 2 — Cruise the backwaters and enjoy a traditional lunch.\nDay 3 — Visit a village and enjoy an unhurried local experience.\nDay 4 — Breakfast, check out and depart.",
            ),
        ),
        (
            "Desert after dark",
            "Jaisalmer, India",
            "Culture",
            "Old-city lanes, a golden fort and an unforgettable night beneath the stars.",
            "3 days · 2 nights",
            1680000,
            12,
            "gallery-desert.jpg",
            "https://www.tourism.rajasthan.gov.in/",
            "Jaisalmer Fort walk, Sam sand dunes camel safari, starry desert camp dinner",
            (
                "Heritage hotel and one desert camp night",
                "Daily breakfast and camp dinner",
                "Local transfers and shared desert excursion",
                "2 nights’ accommodation\nDaily breakfast\nOne camp dinner\nShared desert excursion",
                "Day 1 — Arrive in Jaisalmer and explore the old city.\nDay 2 — Visit the fort, then enjoy a desert camp evening.\nDay 3 — Breakfast, check out and depart.",
            ),
        ),
        (
            "Taj Mahal & Mughal Splendour",
            "Agra, Uttar Pradesh",
            "Heritage & Wonders",
            "Witness sunrise over the world’s most iconic marble monument of eternal love, explore the Agra Fort, and wander ancient Mughal gardens.",
            "3 days · 2 nights",
            1450000,
            30,
            "place-tajmahal.jpg",
            "https://tajmahal.gov.in/",
            "Sunrise Taj Mahal guided tour, Agra Fort royal chambers walk, Mehtab Bagh sunset viewpoint, Marble inlay artisan craft workshop",
            (
                "5-Star Heritage Hotel with view of the Taj Mahal",
                "Daily breakfast buffet, authentic Mughlai feast & evening refreshments",
                "Private luxury AC Sedan transfers from Delhi NCR & local chauffeur",
                "Priority Taj Mahal sunrise ticket\nAgra Fort guided heritage walk\nMehtab Bagh sunset visit\nTraditional marble inlay artisan workshop\nEnglish & Hindi speaking licensed historian guide",
                "Day 1 — Pickup from Delhi, scenic Yamuna Expressway drive to Agra. Check-in to luxury hotel and sunset visit to Mehtab Bagh with panoramic views of the Taj Mahal.\nDay 2 — Early morning sunrise guided exploration of the Taj Mahal. Return for breakfast, followed by an in-depth tour of the historic Agra Fort and local artisan bazaars.\nDay 3 — Relaxed breakfast, visit to Itmad-ud-Daulah (Baby Taj), followed by comfortable return transfer to Delhi.",
            ),
        ),
        (
            "Golden Temple & Sacred Heritage",
            "Amritsar, Punjab",
            "Spiritual & Pilgrimage",
            "Experience the sublime serenity of Sri Harmandir Sahib, peaceful lakeside prayers, community Langar seva, and the patriotic Wagah Border ceremony.",
            "3 days · 2 nights",
            1380000,
            25,
            "place-goldentemple.jpg",
            "https://goldentempleamritsar.org/",
            "Golden Temple Parikrama, Palki Sahib night ceremony, Langar kitchen seva, Jallianwala Bagh memorial tour, Wagah Border retreat parade",
            (
                "Boutique heritage hotel near the sacred parikrama promenade",
                "Daily Punjabi breakfast, community Langar experience & traditional dinner",
                "Airport/railway station AC transfers & private sightseeing vehicle",
                "VIP Golden Temple parikrama & Palki Sahib night ceremony\nJallianwala Bagh memorial guided visit\nWagah Border retreat ceremony VIP seating\nAmritsar old street food trail & phulkari crafts walk",
                "Day 1 — Arrive in Amritsar, hotel check-in. Evening parikrama at Golden Temple with holy hymns (Kirtan) and participate in Langar.\nDay 2 — Morning historic walk through Jallianwala Bagh and Partition Museum. Afternoon drive to Wagah Border for the ceremonial flag-lowering parade. Night Palki ceremony at the Golden Temple.\nDay 3 — Morning prayers at Sri Akal Takht Sahib, traditional Amritsari Kulcha breakfast, check out and departure.",
            ),
        ),
        (
            "Statue of Unity & Narmada Eco-Valley",
            "Kevadia, Gujarat",
            "Modern Wonders & Nature",
            "Stand before the world’s tallest statue (182m), marvel at the viewing gallery 153m high, cruise the Narmada River, and explore the Valley of Flowers.",
            "3 days · 2 nights",
            1520000,
            30,
            "place-statueofunity.jpg",
            "https://www.statueofunity.in/",
            "High-speed viewing gallery elevator (153m), Valley of Flowers nature stroll, Narmada River boat cruise, 3D laser projection sound & light show, Sardar Sarovar Dam overlook",
            (
                "Luxury riverside tented resort in Ekta Nagar",
                "All meals included (Gujarati & multi-cuisine buffet breakfasts and dinners)",
                "AC coach / private cab from Vadodara / Ahmedabad with electric shuttle passes",
                "Statue of Unity Express Entry & Viewing Gallery (153m) ticket\nSound & Light laser projection show passes\nValley of Flowers & Butterfly Garden access\nNarmada River cruise & Sardar Sarovar Dam viewpoint\nJungle Safari & Ekta Cruise experience",
                "Day 1 — Pickup from Vadodara/Ahmedabad, arrive at Ekta Nagar. Check into luxury riverside resort. Evening Sound & Light laser projection show.\nDay 2 — Morning high-speed elevator ascent to the 153m chest-level Viewing Gallery. Afternoon Jungle Safari, Cactus Garden, and sunset boat cruise on Narmada River.\nDay 3 — Visit Sardar Sarovar Dam view point, Valley of Flowers nature stroll, breakfast, check-out and return transfer.",
            ),
        ),
        (
            "Mysore Palace & Royal Wodeyar Splendour",
            "Mysuru, Karnataka",
            "Royal Heritage",
            "Step inside the opulent Amba Vilas Palace with its stained-glass ceilings and golden throne, explore Chamundi Hills, and witness dazzling illuminations.",
            "3 days · 2 nights",
            1290000,
            24,
            "place-mysorepalace.jpg",
            "https://mysorepalace.karnataka.gov.in/",
            "Mysore Palace interior royal halls tour, Chamundi Hill temple darshan, weekend 100,000 bulb illumination spectacle, Brindavan musical fountains, Silk weaving workshop",
            (
                "Heritage palace estate hotel with lush royal gardens",
                "Authentic Karnataka & Mysore breakfasts, royal dinner feast",
                "Private AC car transfers from Bengaluru & local sightseeing",
                "Special entry passes to Mysore Palace & Private Residential Museum\nWeekend night illumination viewing & Sound and Light Show\nChamundeshwari Temple VIP darshan at Chamundi Hills\nBrindavan Gardens musical fountain visit\nMysore silk weaving & sandalwood craft artisan tour",
                "Day 1 — Scenic drive from Bengaluru to Mysuru. Check-in to heritage estate. Evening visit to Brindavan Gardens for musical fountain display.\nDay 2 — Comprehensive guided tour of Mysore Palace interior halls, Durbar hall, and royal collections. Afternoon climb to Chamundi Hill temple. Evening palace illumination spectacle with 100,000 bulbs.\nDay 3 — Morning visit to Devaraja spice & flower market, Sandalwood factory, traditional Mysore Pak tasting, return drive to Bengaluru.",
            ),
        ),
        (
            "Madurai Meenakshi & Tamil Heritage Trail",
            "Madurai, Tamil Nadu",
            "Dravidian Heritage & Temple",
            "Marvel at the majestic 14 towering gopurams carved with divine sculptures, witness the evening celestial chariot procession, and explore thousand-pillar halls.",
            "3 days · 2 nights",
            1340000,
            20,
            "place-meenakshi.jpg",
            "https://maduraimeenakshi.hrce.tn.gov.in/",
            "Special quick temple darshan, 1000-pillar hall exploration, evening Palliarai celestial procession, Thirumalai Nayakkar Mahal light show, Sungudi textile tour",
            (
                "Traditional Chettinad-style heritage resort",
                "Authentic South Indian vegetarian banana leaf meals & daily breakfast",
                "AC private vehicle for temple transfers and Madurai sightseeing",
                "Special quick darshan passes at Meenakshi Sundareswarar shrine\nNight Palliarai celestial wedding ritual procession viewing\nThirumalai Nayakkar Mahal & Sound & Light show\nThousand Pillar Hall & Temple Art Museum guided walkthrough\nTraditional Madurai Sungudi saree weaving & street food tour",
                "Day 1 — Arrive in Madurai, traditional welcome. Evening visit to Meenakshi Temple for the dramatic night procession where Lord Sundareswarar is carried to the goddess shrine.\nDay 2 — Morning architecture and spiritual tour of the Hall of 1,000 Pillars. Afternoon visit to the grand 17th-century Thirumalai Nayakkar Palace. Evening cultural aarti.\nDay 3 — Visit to Gandhi Memorial Museum, traditional South Indian filter coffee & breakfast, check-out and drop at Madurai Airport/station.",
            ),
        ),
        (
            "Tirumala Tirupati Balaji Sacred Darshan",
            "Tirupati, Andhra Pradesh",
            "Spiritual & Pilgrimage",
            "Seek divine blessings at the world-renowned hill shrine of Lord Venkateswara at Seven Hills, accompanied by seamless darshan assistance and sacred prasadam.",
            "3 days · 2 nights",
            1420000,
            30,
            "place-tirupati.jpg",
            "https://www.tirumala.org/",
            "Assisted Special Entry Darshan of Lord Balaji, sacred laddu prasadam collection, Silathoranam natural rock arch hike, Sri Padmavathi Ammavari darshan, Kapila Theertham sacred dip",
            (
                "4-Star pilgrimage resort at the foothills of Tirumala",
                "Pure vegetarian satvik breakfast and meals + authentic Tirupati Laddu Prasadam",
                "Dedicated AC cab for uphill and downhill ghat roads & city transfers",
                "Assisted Special Entry Darshan (SED) coordination\nSacred Tirupati Laddu prasadam packaging\nSri Padmavathi Ammavari Temple (Tiruchanur) darshan\nKapila Theertham water falls & ancient rock-cut temple visit\nSrivari Padalu & Silathoranam natural geological arch exploration",
                "Day 1 — Arrival at Tirupati / Renigunta. Check-in and afternoon visit to Sri Padmavathi Ammavari Temple at Tiruchanur and Kapila Theertham.\nDay 2 — Early morning ascent through the scenic Seshachalam Seven Hills to Tirumala. Assisted Special Darshan of Lord Venkateswara at Ananda Nilayam. Visit Silathoranam geological arch and Chakratheertham. Downhill evening return.\nDay 3 — Morning visit to Sri Govindaraja Swamy Temple, authentic Andhra breakfast, check out and departure.",
            ),
        ),
        (
            "Vaishno Devi Bhawan & Trikuta Hills Pilgrimage",
            "Katra, Jammu & Kashmir",
            "Holy Shrine & Mountains",
            "A soul-enriching trek through the pine-scented Trikuta Mountains to the holy cave shrine of Mata Vaishno Devi, with optional battery car and ropeway.",
            "4 days · 3 nights",
            1650000,
            25,
            "place-vaishnodevi.jpg",
            "https://www.maavaishnodevi.org/",
            "Holy Cave Bhawan Darshan of Natural Pindies, Bhairon Ghati aerial passenger ropeway, Ardhkuwari cave visit, Ban Ganga ritual walk, Katra walnut market trail",
            (
                "Premium mountain hotel in Katra with scenic valley views",
                "Satvik vegetarian meals, continuous tea/refreshments on trail",
                "Jammu Tawi railway / airport private AC transfers to Katra",
                "Yatra registration RFID card facilitation\nAssisted battery-car / cable car / pony arrangement support\nBhairon Ghati passenger ropeway ticket\nArdhkuwari cave temple priority visit\nComplimentary trekking poles and holy chunri kit",
                "Day 1 — Arrive at Jammu, scenic drive through foothills to Katra. Hotel check-in, orientation, and rest.\nDay 2 — Early morning departure for Vaishno Devi Bhawan (13 km). Sacred darshan of the natural rock formations (Pindies). Afternoon cable car ride to Bhairon Temple.\nDay 3 — Gentle descent back to Katra via Sanjichhat and Ardhkuwari. Ayurvedic reflexology foot massage and relaxed evening in Katra market.\nDay 4 — Hearty breakfast, dry-fruit market shopping, transfer back to Jammu airport/station.",
            ),
        ),
        (
            "Kedarnath & Badrinath Sacred Do Dham Yatra",
            "Rudraprayag & Chamoli, Uttarakhand",
            "Himalayan Pilgrimage",
            "Journey deep into the Garhwal Himalayas to Kedarnath amidst snow-clad peaks and Badrinath beside the Alaknanda River, tracing holy river confluences.",
            "6 days · 5 nights",
            2850000,
            16,
            "place-badrinathkedarnath.jpg",
            "https://badrinath-kedarnath.gov.in/",
            "Kedarnath Jyotirlinga high-altitude aarti & darshan, Badrinath Temple evening prayers, Tapt Kund natural hot springs, Mana Village border exploration, Devprayag sangam viewing",
            (
                "Comfortable alpine lodges & riverside pilgrim cottages",
                "Wholesome hot vegetarian pahadi and north Indian meals + high-altitude herbal teas",
                "Specially equipped high-clearance mountain vehicle with experienced hill driver",
                "Do Dham biometric registration passes\nKedarnath temple evening aarti & morning VIP darshan\nBadrinath temple darshan & Tapt Kund natural hot springs\nVisit to Mana Village (India's first border village) and Saraswati river origin\nExperienced mountain yatra coordinator and medical oxygen canister",
                "Day 1 — Dehradun/Rishikesh to Guptkashi via Devprayag & Rudraprayag sangams.\nDay 2 — Trek or heli-transfer from Sonprayag to Kedarnath; evening Kedarnath temple aarti.\nDay 3 — Morning darshan at Kedarnath, descend to Guptkashi/Chopta.\nDay 4 — Scenic mountain drive along Alaknanda to Badrinath, check-in and evening darshan.\nDay 5 — Morning prayers at Badrinath, visit Mana Village, Vyas Gufa, drive to Joshimath/Pipalkoti.\nDay 6 — Return scenic descent to Rishikesh/Haridwar with unforgettable Himalayan memories.",
            ),
        ),
        (
            "Somnath First Jyotirlinga & Coastal Heritage",
            "Prabhas Patan, Gujarat",
            "Spiritual & Coastal",
            "Visit the Eternal Shrine on the shores of the Arabian Sea, the first among the twelve holy Jyotirlingas, and witness the captivating sound & light ocean show.",
            "3 days · 2 nights",
            1390000,
            25,
            "place-somnath.jpg",
            "https://somnath.org/",
            "Somnath Jyotirlinga Abhishek & Aarti, 'Jai Somnath' 3D ocean laser sound & light show, Bhalka Tirth pilgrimage, Triveni Sangam boat ride, sunset Arabian Sea promenade stroll",
            (
                "Sea-facing deluxe hotel overlooking the Arabian shoreline",
                "Pure vegetarian Kathiyawadi & Gujarati thali meals, breakfast included",
                "AC sedan / Innova transfers from Rajkot/Veraval and local transport",
                "VIP special darshan passes at Somnath Jyotirlinga temple\nOceanfront 'Jai Somnath' 3D Sound & Light laser show tickets\nBhalka Tirth & Triveni Sangam boat ride\nPrabhas Patan Museum & ancient ruins exploration\nSunset sea promenade guided walk",
                "Day 1 — Arrive from Rajkot/Veraval, check in to sea-view hotel. Evening visit to Somnath Temple for twilight Maha Aarti and spectacular Sound & Light laser show on temple walls.\nDay 2 — Morning abhishek and darshan at Somnath temple. Visit Triveni Sangam (confluence of Hiran, Kapila and Saraswati rivers) and Bhalka Tirth. Afternoon beach stroll and museum visit.\nDay 3 — Breakfast overlooking the sea, visit Gita Mandir and Parshuram Temple, check out and departure transfer.",
            ),
        ),
        (
            "Kashi Vishwanath & Ganga Aarti Divine Varanasi",
            "Varanasi, Uttar Pradesh",
            "Ancient Culture & Spiritual",
            "Wander the ancient spiritual heart of India, walk the magnificent Kashi Vishwanath Corridor to the Ganga, and experience the world-famous Dashashwamedh Ghat Aarti.",
            "3 days · 2 nights",
            1400000,
            22,
            "place-kashivishwanath.jpg",
            "https://shrikashivishwanath.org/",
            "Kashi Vishwanath Sugam Darshan, sunrise private wooden boat cruise along 84 Ghats, VIP terrace reserved seating for Ganga Aarti, Manikarnika Ghat heritage walk, Sarnath Buddhist stupa excursion",
            (
                "Heritage riverside Haveli on the Ghats of Varanasi",
                "Daily Banarasi breakfast (kachori-jalebi), traditional satvik dinners",
                "Private airport transfers & chartered wooden rowing boat on the Ganges",
                "Kashi Vishwanath Corridor Sugam Darshan priority passes\nPrivate sunrise boat ride along 84 Ghats from Assi to Manikarnika\nReserved VIP terrace seats for Dashashwamedh Ghat Evening Ganga Aarti\nGuided heritage walk of ancient alleys, Sankat Mochan & Annapurna temples\nSarnath Buddhist peace stupa excursion",
                "Day 1 — Arrival in Varanasi, transfer to heritage Haveli. Sunset boat cruise to Dashashwamedh Ghat for the spellbinding evening Maha Aarti ceremony with brass lamps.\nDay 2 — Dawn boat ride to witness morning prayers and yoga on the ghats. Priority Sugam Darshan at Kashi Vishwanath Jyotirlinga Temple and Annapurna Temple. Afternoon trip to Sarnath Deer Park.\nDay 3 — Morning Banarasi silk weaving studio tour, local food tasting (thandai and malaiyo), check out and transfer to airport/station.",
            ),
        ),
        (
            "Swaminarayan Akshardham & Capital Heritage",
            "New Delhi",
            "Architectural Marvel & Culture",
            "Marvel at the monumental pink sandstone and Italian Carrara marble temple with 20,000 statues, the Sahaj Anand water laser show, and cultural boat ride.",
            "2 days · 1 night",
            980000,
            30,
            "place-akshardham.jpg",
            "https://akshardham.com/",
            "Akshardham Mandir guided architectural tour, Sanskruti Vihar 10,000-year Indian history boat ride, Sahaj Anand musical water fountain laser show, Bharat Upavan garden walk, Delhi monument drive",
            (
                "5-Star luxury hotel in Central / East Delhi",
                "Deluxe buffet breakfast and authentic pure vegetarian dinner banquet",
                "Private luxury chauffeur-driven AC car throughout the trip",
                "Akshardham Temple complex priority access & exhibitions package\nSanskruti Vihar cultural boat ride journey through 10,000 years of India\nSahaj Anand Multi-media water fountain & laser spectacular passes\nBharat Upavan lush thematic gardens exploration\nGuided Delhi heritage highlights (Humayun's Tomb & India Gate drive)",
                "Day 1 — Morning pickup from Delhi airport/railway or residence. Afternoon comprehensive visit to Swaminarayan Akshardham: explore Mandir architecture, attend the Sahajanand exhibition and cultural boat ride. Sunset Sahaj Anand musical fountain & laser show.\nDay 2 — Morning breakfast at hotel, scenic drive past India Gate and Rashtrapati Bhavan, optional visit to Humayun's Tomb, drop-off at airport or desired destination.",
            ),
        ),
        (
            "Hampi Boulder Trails & Vijayanagara Empire",
            "Vijayanagara, Karnataka",
            "UNESCO World Heritage",
            "Step back into the 14th century among ancient granite boulders, iconic stone chariot, Virupaksha temple, and the serene Tungabhadra River.",
            "3 days · 2 nights",
            1360000,
            20,
            "place-hampi.jpg",
            "https://hampi.in/",
            "Vijaya Vittala Temple & musical pillars exploration, iconic Stone Chariot photography, Tungabhadra round coracle boat ride, sunset climb on Hemakuta Hill, Royal Enclosure walkthrough",
            (
                "Boutique stone resort with Tungabhadra riverfront setting",
                "South Indian buffet breakfast, clay-pot dinners & afternoon chai",
                "Private AC car transfers from Hospet / Ballari / Bengaluru and coracle boat",
                "Vijaya Vittala Temple & iconic Stone Chariot guided exploration\nTraditional Tungabhadra round coracle boat ride\nVirupaksha Temple sunset blessings and elephant Lakshmi darshan\nLotus Mahal, Elephant Stables & Queen's Bath royal enclosure tour\nLicensed ASI heritage archaeologist guide",
                "Day 1 — Arrive at Hospet/Hampi, check-in to stone riverside resort. Late afternoon climb to Hemakuta Hill for panoramic sunset view over Virupaksha temple.\nDay 2 — Morning visit to Vijaya Vittala temple complex to see the musical pillars and the Stone Chariot. Coracle boat ride on Tungabhadra River. Afternoon tour of the Royal Enclosure, Lotus Mahal and Elephant Stables.\nDay 3 — Morning Matanga Hill sunrise view, heritage breakfast, souvenir market stroll, check-out and return transfer.",
            ),
        ),
    ]

    for title, dest, cat, desc, dur, price, cap, img, url, acts, details in new_places:
        existing = db.execute("SELECT id FROM packages WHERE title=?", (title,)).fetchone()
        if existing:
            pkg_id = existing["id"]
            db.execute(
                """UPDATE packages SET destination=?, category=?, description=?, duration=?,
                                      price_paise=?, capacity=?, image_file=?, official_url=?, activities=?
                   WHERE id=?""",
                (dest, cat, desc, dur, price, cap, img, url, acts, pkg_id),
            )
        else:
            cur = db.execute(
                """INSERT INTO packages(title, destination, category, description, duration,
                                        price_paise, capacity, image_file, official_url, activities)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (title, dest, cat, desc, dur, price, cap, img, url, acts),
            )
            pkg_id = cur.lastrowid

        db.execute(
            """INSERT OR REPLACE INTO package_details(package_id, stay_type, meal_plan, transport, inclusions, itinerary)
               VALUES(?,?,?,?,?,?)""",
            (pkg_id, *details),
        )

    db.commit()
    print("Packages and itineraries seeded successfully with 0 fake bookings!")
    db.close()

if __name__ == "__main__":
    run_seed()
