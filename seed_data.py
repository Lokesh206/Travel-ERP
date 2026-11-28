from __future__ import annotations
import os
import sqlite3
from pathlib import Path

DATABASE = Path(
    os.environ.get("TRAVEL_ERP_DATABASE", Path(__file__).resolve().parent / "travel_erp.sqlite3")
)

def run_seed():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row

    # Ensure required columns exist on packages table
    cols = [r[1] for r in db.execute("PRAGMA table_info(packages)").fetchall()]
    new_cols = [
        ("image_file", "TEXT"),
        ("official_url", "TEXT"),
        ("activities", "TEXT"),
        ("origin", "TEXT DEFAULT 'Bengaluru'"),
        ("original_price_paise", "INTEGER DEFAULT 0"),
        ("upcoming_dates", "TEXT DEFAULT ''"),
        ("trust_text", "TEXT DEFAULT '150+ travelers can''t be wrong – book your trip today!'"),
    ]
    for col, col_type in new_cols:
        if col not in cols:
            db.execute(f"ALTER TABLE packages ADD COLUMN {col} {col_type}")
    db.commit()

    # 16 Diverse & Iconic Destinations (Domestic & International) with unique origins & 5-month departure schedules
    packages_data = [
        # 1. Philippines Tour (Image 1 Exact Match)
        {
            "title": "Philippines Tour",
            "destination": "Philippines",
            "origin": "Bengaluru",
            "category": "International",
            "description": "Turquoise island lagoons, Cebu whale shark sanctuaries, Kawasan waterfalls, and pristine El Nido coral beaches.",
            "duration": "8 Days / 7 Nights",
            "price_paise": 25499900,  # ₹254,999
            "original_price_paise": 26000000,  # ₹260,000 (Struck through)
            "capacity": 20,
            "reserved": 11,  # 9 Seats Left (matches screenshot)
            "image_file": "place-philippines.jpg",
            "official_url": "https://philippines.travel/",
            "activities": "El Nido island hopping boat tour, Kawasan waterfall bamboo rafting, Cebu coral snorkeling, Manila colonial Intramuros heritage walk",
            "upcoming_dates": "09 Dec 2026, 14 Jan 2027, 11 Feb 2027, 18 Mar 2027, 15 Apr 2027",
            "trust_text": "150+ travelers can't be wrong – book your trip today!",
            "details": (
                "4-Star Luxury Beachfront Island Resorts in Cebu & El Nido",
                "Daily buffet breakfast & traditional Filipino seafood boodle feast",
                "Domestic island flight transfers, private AC vans & outrigger speedboats",
                "El Nido Big Lagoon & Secret Lagoon catamaran tour\nKawasan Falls canyoneering with certified guides\nOslob whale shark swimming & coral reef snorkeling gear\nManila Spanish heritage walk in historic Intramuros\nEnglish speaking private island concierge",
                "Day 1 — Arrive in Manila, domestic transfer to Cebu, check-in to beachfront resort.\nDay 2 — Kawasan Falls bamboo rafting and crystal pool swims.\nDay 3 — Scenic island flight to El Nido, Palawan. Sunset cocktails on Nacpan beach.\nDay 4 — Big Lagoon & Secret Lagoon private island hopping catamaran cruise.\nDay 5 — Snorkeling with sea turtles and coral reef marine exploration.\nDay 6 — Cultural tour and tropical mango plantation visit.\nDay 7 — Leisurely beach day and sunset farewell seafood boodle dinner.\nDay 8 — Breakfast, check-out, domestic return flight and international departure."
            )
        },
        # 2. Kashmir Paradise & Gulmarg Valley
        {
            "title": "Kashmir Paradise Escape",
            "destination": "Kashmir, India",
            "origin": "Mumbai",
            "category": "Honeymoon & Nature",
            "description": "Snow-capped Himalayan peaks, wooden carved houseboats on Dal Lake, Shikara rides and Gulmarg high-altitude gondolas.",
            "duration": "6 Days / 5 Nights",
            "price_paise": 4299900,  # ₹42,999
            "original_price_paise": 4800000,  # ₹48,000
            "capacity": 18,
            "reserved": 11,  # 7 Seats Left
            "image_file": "gallery-himalaya.jpg",
            "official_url": "https://jktourism.jk.gov.in/",
            "activities": "Dal Lake sunset Shikara ride, Gulmarg Phase 2 Gondola ride, Pahalgam Betaab Valley horse trek, Mughal gardens walk",
            "upcoming_dates": "12 Dec 2026, 18 Jan 2027, 15 Feb 2027, 20 Mar 2027, 12 Apr 2027",
            "trust_text": "120+ travelers rated this 5 stars this season!",
            "details": (
                "Luxury heritage wooden Houseboat on Dal Lake & boutique pine cottages",
                "Daily Kashmiri Wazwan dinner, buffet breakfast & Kahwa tea ceremonies",
                "Private heated AC Innova transfers and dedicated alpine chauffeur",
                "Gulmarg Gondola Phase 1 & 2 priority passes\nDal Lake private Shikara boat cruise\nPahalgam Betaab & Aru Valley guided excursion\nNishat & Shalimar Mughal gardens heritage entry",
                "Day 1 — Arrive in Srinagar, check into royal wooden Dal Lake houseboat. Evening Shikara ride.\nDay 2 — Day trip to Gulmarg, ride the world's highest gondola to Apharwat peak.\nDay 3 — Drive to scenic Pahalgam along the Lidder River, visit Betaab Valley.\nDay 4 — Pony trek to Baisaran meadow (Mini Switzerland) and pine forest walks.\nDay 5 — Return to Srinagar, tour Shalimar & Nishat Bagh, local saffron and pashmina bazaars.\nDay 6 — Traditional breakfast with Kahwa, check-out and airport transfer."
            )
        },
        # 3. Dubai Grand Adventure
        {
            "title": "Dubai Grand Adventure",
            "destination": "Dubai, UAE",
            "origin": "Delhi",
            "category": "International",
            "description": "Futuristic skyscrapers, Burj Khalifa 124th floor views, high-octane red dune desert safaris and Marina yacht cruises.",
            "duration": "5 Days / 4 Nights",
            "price_paise": 7999900,  # ₹79,999
            "original_price_paise": 8500000,  # ₹85,000
            "capacity": 25,
            "reserved": 13,  # 12 Seats Left
            "image_file": "gallery-desert.jpg",
            "official_url": "https://www.visitdubai.com/",
            "activities": "Burj Khalifa At The Top (124th floor), 4x4 red dune desert bash, Dubai Marina luxury yacht dinner cruise, Museum of the Future",
            "upcoming_dates": "15 Dec 2026, 20 Jan 2027, 18 Feb 2027, 22 Mar 2027, 19 Apr 2027",
            "trust_text": "200+ global travelers booked this month!",
            "details": (
                "5-Star Millennium / Marriott Hotel in Downtown Dubai",
                "Daily international buffet breakfast and Bedouin desert barbecue banquet",
                "Private airport limousine transfers & air-conditioned luxury coach",
                "Burj Khalifa 124th + 125th floor observatory admission\n4x4 Land Cruiser desert dune bashing & camel riding\nDubai Marina 5-star yacht dinner cruise with live entertainment\nMuseum of the Future fast-track ticket\nGold & Spice Souk guided walk",
                "Day 1 — Arrive at Dubai International Airport, luxury transfer to hotel. Evening Dubai Mall fountain show.\nDay 2 — Morning city tour with Museum of the Future. Afternoon ascent to Burj Khalifa 124th floor.\nDay 3 — 4x4 Desert Safari adventure with dune bashing, sandboarding, camel rides and BBQ dinner.\nDay 4 — Miracle Garden, Dubai Frame, and evening Dubai Marina luxury yacht dinner cruise.\nDay 5 — Breakfast, check out, shopping at Gold Souk and departure."
            )
        },
        # 4. Bali Tropical Paradise & Nusa Penida
        {
            "title": "Bali Tropical Paradise",
            "destination": "Bali, Indonesia",
            "origin": "Bengaluru",
            "category": "International",
            "description": "Emerald rice terraces in Ubud, sacred cliffside sea temples in Uluwatu, Nusa Penida T-Rex beaches and jungle swings.",
            "duration": "6 Days / 5 Nights",
            "price_paise": 6649900,  # ₹66,499
            "original_price_paise": 7200000,  # ₹72,000
            "capacity": 20,
            "reserved": 12,  # 8 Seats Left
            "image_file": "place-somnath.jpg",
            "official_url": "https://www.indonesia.travel/",
            "activities": "Nusa Penida Kelingking T-Rex beach tour, Ubud jungle swing & Tegallalang rice terrace, Uluwatu sunset Kecak fire dance, Tanah Lot temple",
            "upcoming_dates": "10 Dec 2026, 16 Jan 2027, 14 Feb 2027, 17 Mar 2027, 21 Apr 2027",
            "trust_text": "Rated #1 tropical escape by verified guests!",
            "details": (
                "Private pool villa in Seminyak & jungle eco-resort in Ubud",
                "Daily tropical breakfast with floating breakfast option, Balinese feast",
                "Private chauffeur-driven air-conditioned vehicle & fast-boat to Nusa Penida",
                "Full-day Nusa Penida speedboat tour (Kelingking Beach, Broken Beach, Angel's Billabong)\nUbud giant jungle swing & coffee plantation tasting\nTanah Lot sunset sea temple visit\nUluwatu cliffside temple with Kecak Fire Dance\nTraditional 60-minute Balinese spa massage",
                "Day 1 — Arrive in Denpasar, transfer to private pool villa in Seminyak.\nDay 2 — Fast-boat to Nusa Penida island; photograph Kelingking T-Rex beach and swim at Crystal Bay.\nDay 3 — Transfer to Ubud, visit Tegallalang rice terraces, experience Ubud jungle swing.\nDay 4 — Sacred Monkey Forest Sanctuary, traditional art market and Balinese spa treatment.\nDay 5 — Afternoon visit to Uluwatu temple perched on 70m cliffs with sunset Kecak Fire Dance.\nDay 6 — Floating villa breakfast, souvenir shopping, check-out and airport transfer."
            )
        },
        # 5. Coastal Calm & Sunset Shores, Goa
        {
            "title": "Coastal Calm, Goa",
            "destination": "Goa, India",
            "origin": "Hyderabad",
            "category": "Beach & Leisure",
            "description": "Slow sunny mornings, private sunbeds on golden sands, Portuguese heritage villas and catamaran ocean cruises.",
            "duration": "4 Days / 3 Nights",
            "price_paise": 1399900,  # ₹13,999
            "original_price_paise": 1600000,  # ₹16,000
            "capacity": 24,
            "reserved": 10,  # 14 Seats Left
            "image_file": "gallery-coast.jpg",
            "official_url": "https://goa-tourism.com/",
            "activities": "Sunset catamaran cruise, Old Goa Latin Quarter Fontainhas heritage walk, Mandovi river dinner cruise, spice plantation tour",
            "upcoming_dates": "08 Dec 2026, 12 Jan 2027, 09 Feb 2027, 14 Mar 2027, 18 Apr 2027",
            "trust_text": "98% of travelers recommend this sunny getaway!",
            "details": (
                "5-Star Beachfront Luxury Resort in South Goa",
                "Daily continental & Goan breakfast, authentic seafood coastal meal",
                "Private AC transfers to and from Dabolim / Mopa airport",
                "Catamaran sunset cruise with dolphin spotting\nFontainhas Latin Quarter heritage guided walk\nHistoric Basilica of Bom Jesus & Se Cathedral visit\nSahakari organic spice plantation tour with lunch",
                "Day 1 — Airport pickup, check into beachfront resort, welcome coconut drink and sunset beach walk.\nDay 2 — Fontainhas colorful heritage walk, Old Goa churches, and evening catamaran cruise.\nDay 3 — Spice plantation tour, elephant interaction, and leisurely beach club afternoon.\nDay 4 — Breakfast, pool swim, check-out and departure transfer."
            )
        },
        # 6. Kerala Backwaters & Beyond
        {
            "title": "Backwaters & Beyond, Kerala",
            "destination": "Alappuzha & Munnar",
            "origin": "Chennai",
            "category": "Culture & Nature",
            "description": "Private luxury houseboats drifting through palm-fringed lagoons, spice-scented air, and misty green tea estates.",
            "duration": "5 Days / 4 Nights",
            "price_paise": 1850000,  # ₹18,500
            "original_price_paise": 2200000,  # ₹22,000
            "capacity": 15,
            "reserved": 5,  # 10 Seats Left
            "image_file": "gallery-backwaters.jpg",
            "official_url": "https://www.keralatourism.org/",
            "activities": "Exclusive Vembanad lake private houseboat cruise, Munnar tea plantation trek, Kathakali traditional performance, spice garden tour",
            "upcoming_dates": "11 Dec 2026, 15 Jan 2027, 12 Feb 2027, 16 Mar 2027, 20 Apr 2027",
            "trust_text": "Over 180 verified guest reviews on this tranquil trail!",
            "details": (
                "1 Night Private AC Houseboat & 3 Nights Luxury Tea Valley Resort",
                "Full board on houseboat (lunch, dinner, breakfast) + daily resort breakfasts",
                "Dedicated AC chauffeur throughout Kochi, Munnar and Alleppey",
                "Private deluxe houseboat backwater cruise with onboard personal chef\nTata Tea Museum guided tour with tea tasting\nEravikulam National Park Nilgiri Tahr sanctuary visit\nAuthentic Ayurvedic herbal massage session",
                "Day 1 — Pickup from Kochi, scenic drive to misty Munnar with Cheeyappara waterfalls.\nDay 2 — Tour tea gardens, visit Mattupetty Dam, Echo Point, and Tea Museum.\nDay 3 — Drive to Alappuzha, board private luxury houseboat, cruise tranquil backwaters.\nDay 4 — Village canoe ride, disembark to boutique heritage resort in Marari.\nDay 5 — Breakfast, Ayurvedic spa session, check-out and drop at Kochi airport."
            )
        },
        # 7. Taj Mahal & Mughal Splendour
        {
            "title": "Taj Mahal & Mughal Splendour",
            "destination": "Agra, Uttar Pradesh",
            "origin": "Delhi",
            "category": "Heritage & Wonders",
            "description": "Marvel at the world wonder of love at sunrise, explore royal palaces of Agra Fort, and wander ancient Mughal gardens.",
            "duration": "3 Days / 2 Nights",
            "price_paise": 1450000,  # ₹14,500
            "original_price_paise": 1800000,  # ₹18,000
            "capacity": 30,
            "reserved": 15,  # 15 Seats Left
            "image_file": "place-tajmahal.jpg",
            "official_url": "https://tajmahal.gov.in/",
            "activities": "Sunrise Taj Mahal VIP tour, Agra Fort royal halls walk, Mehtab Bagh sunset viewpoint, Marble inlay artisan craft workshop",
            "upcoming_dates": "07 Dec 2026, 11 Jan 2027, 08 Feb 2027, 13 Mar 2027, 17 Apr 2027",
            "trust_text": "Top-rated Golden Triangle heritage journey!",
            "details": (
                "5-Star Luxury Hotel with view of the Taj Mahal",
                "Daily breakfast buffet, authentic Mughlai royal feast & evening tea",
                "Private luxury AC Sedan transfers from Delhi NCR & dedicated local chauffeur",
                "Priority Taj Mahal sunrise ticket\nAgra Fort guided heritage walk\nMehtab Bagh sunset visit\nTraditional marble inlay artisan workshop\nEnglish & Hindi speaking licensed historian guide",
                "Day 1 — Pickup from Delhi, drive on Yamuna Expressway. Check into luxury hotel. Sunset at Mehtab Bagh.\nDay 2 — Early morning sunrise guided exploration of the Taj Mahal. Agra Fort in-depth tour and artisan bazaars.\nDay 3 — Visit Itmad-ud-Daulah (Baby Taj), relaxed breakfast, comfortable return transfer to Delhi."
            )
        },
        # 8. Golden Temple & Sacred Heritage
        {
            "title": "Golden Temple & Sacred Heritage",
            "destination": "Amritsar, Punjab",
            "origin": "Delhi",
            "category": "Spiritual & Pilgrimage",
            "description": "Serene lakeside prayers at Sri Harmandir Sahib, holy community Langar seva, and the patriotic Wagah Border retreat parade.",
            "duration": "3 Days / 2 Nights",
            "price_paise": 1380000,  # ₹13,800
            "original_price_paise": 1650000,  # ₹16,500
            "capacity": 25,
            "reserved": 7,  # 18 Seats Left
            "image_file": "place-goldentemple.jpg",
            "official_url": "https://goldentempleamritsar.org/",
            "activities": "Golden Temple Parikrama, Palki Sahib night ceremony, Langar kitchen seva, Jallianwala Bagh memorial tour, Wagah Border retreat parade",
            "upcoming_dates": "14 Dec 2026, 19 Jan 2027, 16 Feb 2027, 21 Mar 2027, 25 Apr 2027",
            "trust_text": "160+ pilgrims cherish this uplifting journey!",
            "details": (
                "Boutique heritage hotel near the sacred parikrama promenade",
                "Daily Punjabi breakfast, community Langar experience & traditional dinner",
                "Airport/railway station AC transfers & private sightseeing vehicle",
                "VIP Golden Temple parikrama & Palki Sahib night ceremony\nJallianwala Bagh memorial guided visit\nWagah Border retreat ceremony VIP seating\nAmritsar old street food trail & phulkari crafts walk",
                "Day 1 — Arrive in Amritsar, hotel check-in. Evening parikrama at Golden Temple with holy hymns (Kirtan) and Langar.\nDay 2 — Jallianwala Bagh and Partition Museum. Afternoon drive to Wagah Border for ceremony. Night Palki ceremony.\nDay 3 — Morning prayers at Sri Akal Takht Sahib, traditional Amritsari Kulcha breakfast, check out and departure."
            )
        },
        # 9. Statue of Unity & Narmada Eco-Valley
        {
            "title": "Statue of Unity & Narmada Valley",
            "destination": "Kevadia, Gujarat",
            "origin": "Ahmedabad",
            "category": "Modern Wonders & Nature",
            "description": "Stand before the world's tallest statue (182m), ascend to the 153m viewing gallery, and cruise the Narmada River.",
            "duration": "3 Days / 2 Nights",
            "price_paise": 1520000,  # ₹15,200
            "original_price_paise": 1900000,  # ₹19,000
            "capacity": 30,
            "reserved": 14,  # 16 Seats Left
            "image_file": "place-statueofunity.jpg",
            "official_url": "https://www.statueofunity.in/",
            "activities": "High-speed viewing gallery elevator (153m), Valley of Flowers nature stroll, Narmada River boat cruise, 3D laser projection sound & light show",
            "upcoming_dates": "16 Dec 2026, 22 Jan 2027, 19 Feb 2027, 24 Mar 2027, 28 Apr 2027",
            "trust_text": "Iconic engineering wonder visited by thousands!",
            "details": (
                "Luxury riverside tented resort in Ekta Nagar",
                "All meals included (Gujarati & multi-cuisine buffet breakfasts and dinners)",
                "AC coach / private cab from Vadodara / Ahmedabad with electric shuttle passes",
                "Statue of Unity Express Entry & Viewing Gallery (153m) ticket\nSound & Light laser projection show passes\nValley of Flowers & Butterfly Garden access\nNarmada River cruise & Sardar Sarovar Dam viewpoint\nJungle Safari & Ekta Cruise experience",
                "Day 1 — Pickup from Ahmedabad/Vadodara, check into riverside luxury resort. Evening 3D laser projection show.\nDay 2 — Morning high-speed elevator ascent to the 153m Viewing Gallery. Afternoon Jungle Safari and Narmada boat cruise.\nDay 3 — Sardar Sarovar Dam viewpoint, Valley of Flowers stroll, breakfast, check-out and return transfer."
            )
        },
        # 10. Thailand Phuket & Phi Phi Islands
        {
            "title": "Thailand Island Odyssey",
            "destination": "Phuket & Krabi, Thailand",
            "origin": "Bengaluru",
            "category": "International",
            "description": "Speedboat adventures to Phi Phi Islands, limestone karsts in Phang Nga Bay, emerald lagoons, and vibrant night markets.",
            "duration": "6 Days / 5 Nights",
            "price_paise": 5999900,  # ₹59,999
            "original_price_paise": 6800000,  # ₹68,000
            "capacity": 22,
            "reserved": 11,  # 11 Seats Left
            "image_file": "gallery-udupi.jpg",
            "official_url": "https://www.tourismthailand.org/",
            "activities": "Phi Phi Islands speedboat tour, Maya Bay swimming, James Bond Island sea canoeing, Phuket Old Town street food trail",
            "upcoming_dates": "18 Dec 2026, 24 Jan 2027, 21 Feb 2027, 26 Mar 2027, 30 Apr 2027",
            "trust_text": "Voted best value international holiday package!",
            "details": (
                "Beachfront resort in Patong Phuket & cliffside resort in Ao Nang Krabi",
                "Daily buffet breakfast & Thai seafood island barbecue lunch",
                "All airport, ferry and speedboat island transfers included",
                "Full-day Phi Phi & Maya Bay speedboat tour with snorkeling\nJames Bond Island Phang Nga Bay sea canoeing\nKrabi 4 Islands longtail boat sunset tour\nPhuket Big Buddha viewpoint & Old Town heritage walk\nEnglish speaking certified marine tour guide",
                "Day 1 — Arrive at Phuket airport, transfer to beachfront resort. Evening Patong night market.\nDay 2 — Speedboat tour to Phi Phi Don, Phi Phi Leh, and swim at world-famous Maya Bay.\nDay 3 — Ferry to Krabi, check into Ao Nang cliffside resort. Relax at Railay beach.\nDay 4 — Krabi 4 Islands tour: Koh Poda, Chicken Island, Tup Island and Phra Nang Cave.\nDay 5 — Sea kayaking in Ao Thalane mangrove forests, sunset beach dinner.\nDay 6 — Breakfast, check out, transfer to airport for departure."
            )
        },
        # 11. Royal Rajasthan Desert & Forts
        {
            "title": "Desert After Dark, Jaisalmer",
            "destination": "Jaisalmer, Rajasthan",
            "origin": "Jaipur",
            "category": "Royal Heritage",
            "description": "Golden fort ramparts, camel safaris over Sam sand dunes, folk music under starlit skies, and royal havelis.",
            "duration": "4 Days / 3 Nights",
            "price_paise": 1780000,  # ₹17,800
            "original_price_paise": 2100000,  # ₹21,000
            "capacity": 18,
            "reserved": 9,  # 9 Seats Left
            "image_file": "gallery-desert.jpg",
            "official_url": "https://www.tourism.rajasthan.gov.in/",
            "activities": "Jaisalmer living golden fort walk, Sam sand dunes camel safari, Thar desert camp folk dance, Patwon ki Haveli tour",
            "upcoming_dates": "13 Dec 2026, 17 Jan 2027, 14 Feb 2027, 19 Mar 2027, 23 Apr 2027",
            "trust_text": "An enchanting Arabian Nights experience in India!",
            "details": (
                "Royal stone haveli hotel & luxury Swiss desert tents",
                "Daily Rajasthani Dal Baati Churma dinners and buffet breakfasts",
                "Private AC car throughout Jaipur, Jodhpur, and Jaisalmer",
                "Camel safari over golden Sam sand dunes\nTraditional Kalbelia folk dance & campfire gala night\nJaisalmer Golden Fort & Jain temples guided walk\nPatwon ki Haveli & Gadisar lake evening stroll",
                "Day 1 — Arrive in Jaisalmer, check into heritage haveli hotel. Sunset walk at Gadisar Lake.\nDay 2 — In-depth tour of Jaisalmer Golden Fort, Jain temples and intricate Patwon ki Haveli.\nDay 3 — Drive to Sam Sand Dunes. Sunset camel safari, campfire gala dinner with Kalbelia folk dancers under starry desert skies.\nDay 4 — Sunrise over dunes, traditional breakfast, check-out and transfer."
            )
        },
        # 12. Himalayan Pine Trails & Manali
        {
            "title": "Into the Himalayas, Manali",
            "destination": "Manali, Himachal Pradesh",
            "origin": "Chandigarh",
            "category": "Adventure & Mountains",
            "description": "Crisp mountain air, pine forest trails, Apple orchards, Rohtang Pass snow vistas, and cozy alpine lodge stays.",
            "duration": "5 Days / 4 Nights",
            "price_paise": 1950000,  # ₹19,500
            "original_price_paise": 2400000,  # ₹24,000
            "capacity": 20,
            "reserved": 7,  # 13 Seats Left
            "image_file": "gallery-himalaya.jpg",
            "official_url": "https://himachaltourism.gov.in/",
            "activities": "Solang Valley adventure sports, Atal Tunnel & Sissu snow excursion, Old Manali cafe trail, Jogini waterfall nature trek",
            "upcoming_dates": "20 Dec 2026, 26 Jan 2027, 23 Feb 2027, 28 Mar 2027, 26 Apr 2027",
            "trust_text": "140+ mountain enthusiasts loved this alpine trail!",
            "details": (
                "Boutique alpine lodge with panoramic Himalayan cedar views",
                "Daily mountain breakfast, afternoon herbal chai, fireside dinners",
                "Private 4x4 / AC mountain vehicle and experienced hill chauffeur",
                "Solang Valley snow activities & paragliding pass\nAtal Tunnel engineering marvel drive to Lahaul valley\nGuided pine forest trek to Jogini Waterfalls\nHadimba Temple & Vashisht hot springs visit",
                "Day 1 — Scenic drive from Chandigarh to Manali, check-in to mountain lodge.\nDay 2 — Solang Valley adventures: paragliding and zorbing with snow views.\nDay 3 — Drive through Atal Tunnel to snowy Sissu in Lahaul Valley.\nDay 4 — Nature walk to Jogini Waterfall, Old Manali cafes and Hadimba temple.\nDay 5 — Breakfast, check-out and return drive."
            )
        },
        # 13. Singapore Futuristic Skyline & Sentosa
        {
            "title": "Singapore City & Island Wonders",
            "destination": "Singapore",
            "origin": "Chennai",
            "category": "International",
            "description": "Supertrees at Gardens by the Bay, Universal Studios Sentosa, Night Safari, Marina Bay Sands rooftop views and vibrant Chinatown.",
            "duration": "5 Days / 4 Nights",
            "price_paise": 8999900,  # ₹89,999
            "original_price_paise": 9500000,  # ₹95,000
            "capacity": 20,
            "reserved": 13,  # 7 Seats Left
            "image_file": "place-akshardham.jpg",
            "official_url": "https://www.visitsingapore.com/",
            "activities": "Gardens by the Bay Flower Dome & Cloud Forest, Marina Bay Sands SkyPark, Universal Studios Singapore, Night Safari tram ride",
            "upcoming_dates": "22 Dec 2026, 28 Jan 2027, 25 Feb 2027, 29 Mar 2027, 27 Apr 2027",
            "trust_text": "Singapore top-selling luxury family vacation!",
            "details": (
                "4-Star Luxury City Hotel near Orchard Road / Clarke Quay",
                "Daily international buffet breakfast and Marina Bay dinner",
                "Private airport transfers and Singapore MRT pass with tourist coach",
                "Gardens by the Bay (Flower Dome + Cloud Forest) admission\nMarina Bay Sands SkyPark Observation Deck\nUniversal Studios Singapore full day all-access pass\nWorld famous Night Safari tram tour\nSentosa Cable Car round-trip pass",
                "Day 1 — Arrive at Changi Airport, jewel waterfall visit, hotel check-in. Evening Clarke Quay river cruise.\nDay 2 — Gardens by the Bay, Cloud Forest, and Marina Bay Sands SkyPark 57th floor view.\nDay 3 — Full day at Universal Studios Singapore on Sentosa Island.\nDay 4 — Chinatown, Little India cultural trail, and evening world-first Night Safari.\nDay 5 — Breakfast, Orchard Road shopping, check-out and departure."
            )
        },
        # 14. Sacred Varanasi & Ayodhya Trail
        {
            "title": "Sacred Varanasi & Ayodhya Trail",
            "destination": "Varanasi & Ayodhya",
            "origin": "Lucknow",
            "category": "Spiritual & Pilgrimage",
            "description": "Sublime evening Ganga Aarti by boat, sunrise Kashi Vishwanath darshan, Sarnath Buddha stupa, and the magnificent Ram Mandir in Ayodhya.",
            "duration": "4 Days / 3 Nights",
            "price_paise": 1420000,  # ₹14,200
            "original_price_paise": 1750000,  # ₹17,500
            "capacity": 25,
            "reserved": 5,  # 20 Seats Left
            "image_file": "place-kashivishwanath.jpg",
            "official_url": "https://kashivishwanath.in/",
            "activities": "Sunrise Ganga private boat ride, Dashashwamedh Ghat grand evening Aarti, Kashi Vishwanath temple VIP darshan, Ayodhya Ram Janmabhoomi visit",
            "upcoming_dates": "09 Dec 2026, 13 Jan 2027, 10 Feb 2027, 15 Mar 2027, 19 Apr 2027",
            "trust_text": "A spiritually transformative journey for the soul!",
            "details": (
                "Heritage riverfront haveli hotel in Varanasi & 4-Star hotel in Ayodhya",
                "Pure vegetarian satvik breakfast and traditional Awadhi meals",
                "Private AC vehicle for Varanasi, Sarnath, and Ayodhya highway travel",
                "Private hand-rowed sunrise boat ride on River Ganga\nSpecial priority darshan ticket for Kashi Vishwanath Temple\nReserved boat seats for Dashashwamedh Ghat Ganga Aarti\nAyodhya Ram Janmabhoomi Mandir & Hanumangarhi guided darshan\nSarnath Buddhist archaeological site guided tour",
                "Day 1 — Arrive in Varanasi, hotel check-in. Evening private boat for Dashashwamedh Ghat Ganga Aarti.\nDay 2 — Sunrise boat ride along ancient ghats, Kashi Vishwanath Corridor darshan, afternoon excursion to Sarnath.\nDay 3 — Drive to Ayodhya, visit Ram Janmabhoomi Mandir, Hanumangarhi, and Saryu River sunset Aarti.\nDay 4 — Morning temple prayers, traditional breakfast, check-out and Lucknow transfer."
            )
        },
        # 15. Andaman Coral Islands & Radhanagar Beach
        {
            "title": "Andaman Island Coral Haven",
            "destination": "Port Blair & Havelock",
            "origin": "Bengaluru",
            "category": "Beach & Adventure",
            "description": "Turquoise waters of Radhanagar Beach (Asia's cleanest), live coral reef snorkeling at Elephant Beach, and historic Cellular Jail.",
            "duration": "6 Days / 5 Nights",
            "price_paise": 4699900,  # ₹46,999
            "original_price_paise": 5400000,  # ₹54,000
            "capacity": 18,
            "reserved": 10,  # 8 Seats Left
            "image_file": "gallery-tea.jpg",
            "official_url": "https://www.andamantourism.gov.in/",
            "activities": "Radhanagar Beach sunset, Elephant Beach coral snorkeling & sea walk, Makruzz luxury catamaran cruise, Cellular Jail light and sound show",
            "upcoming_dates": "25 Dec 2026, 30 Jan 2027, 27 Feb 2027, 31 Mar 2027, 29 Apr 2027",
            "trust_text": "Crystal clear waters & exotic marine life!",
            "details": (
                "Luxury Beachfront Cottages on Havelock Island & sea-facing Port Blair resort",
                "Daily buffet breakfast & fresh island catch / multi-cuisine dinners",
                "Makruzz / Nautika high-speed luxury catamaran cruise tickets",
                "Cellular Jail national memorial entry & Sound & Light show\nRadhanagar Beach excursion (voted Asia's 7th best beach)\nSpeedboat ride & complimentary snorkeling at Elephant Beach\nKalapathar Beach sunrise viewpoint tour",
                "Day 1 — Arrive at Port Blair, visit Cellular Jail and attend evening patriotic Sound & Light show.\nDay 2 — High-speed Makruzz catamaran cruise to Havelock Island, sunset at Radhanagar Beach.\nDay 3 — Speedboat to Elephant Beach for snorkeling, sea walking and water sports.\nDay 4 — Scenic morning at Kalapathar Beach, afternoon ferry back to Port Blair.\nDay 5 — Ross Island (Netaji Subhash Chandra Bose Dweep) deer sanctuary and colonial ruins.\nDay 6 — Breakfast, check-out and airport departure."
            )
        },
        # 16. Vietnam Ha Long Bay & Da Nang
        {
            "title": "Vietnam Wonders & Ha Long Cruise",
            "destination": "Ha Long Bay & Da Nang",
            "origin": "Delhi",
            "category": "International",
            "description": "Overnight 5-star cruise on emerald waters of Ha Long Bay, Golden Hand Bridge in Ba Na Hills, and lanterns of Hoi An Ancient Town.",
            "duration": "7 Days / 6 Nights",
            "price_paise": 6999900,  # ₹69,999
            "original_price_paise": 7800000,  # ₹78,000
            "capacity": 20,
            "reserved": 10,  # 10 Seats Left
            "image_file": "gallery-heritage.jpg",
            "official_url": "https://vietnam.travel/",
            "activities": "5-Star Ha Long Bay overnight cruise with kayaking, Ba Na Hills Golden Hand Bridge cable car, Hoi An ancient town lantern boat ride",
            "upcoming_dates": "27 Dec 2026, 31 Jan 2027, 28 Feb 2027, 30 Mar 2027, 28 Apr 2027",
            "trust_text": "170+ travelers fell in love with Vietnam on this journey!",
            "details": (
                "1 Night 5-Star Luxury Ha Long Bay Cruise & 5 Nights Boutique Riverfront Hotels",
                "All meals on Ha Long cruise (4 meals) + daily hotel buffet breakfasts",
                "Domestic flight Hanoi to Da Nang & private VIP limousine coach",
                "Ha Long Bay overnight cruise with private balcony cabin & cooking class\nKayaking through Luon Cave & Titop Island hike\nBa Na Hills cable car & iconic Golden Bridge walk\nHoi An Ancient Town lantern-lit boat ride\nEnglish speaking certified local guides throughout",
                "Day 1 — Arrive in Hanoi, historic Old Quarter cycle rickshaw tour, hotel check-in.\nDay 2 — Drive to Ha Long Bay, board 5-star cruise, sail past limestone karsts, kayak through caves.\nDay 3 — Sunrise Tai Chi on sundeck, explore Sung Sot cave, flight to Da Nang.\nDay 4 — Cable car to Ba Na Hills, walk on famous Golden Hands Bridge, French Village.\nDay 5 — Explore lantern-lit Hoi An Ancient Town, basket boat ride in coconut forest.\nDay 6 — Marble Mountains cave exploration, leisure afternoon on My Khe beach.\nDay 7 — Breakfast, check out and airport transfer."
            )
        }
    ]

    for p in packages_data:
        existing = db.execute(
            "SELECT id, origin, original_price_paise, upcoming_dates, trust_text, image_file, official_url, activities FROM packages WHERE title=?",
            (p["title"],),
        ).fetchone()
        if existing:
            pkg_id = existing["id"]
            # Preserve live user-facing pricing, capacity, status, and real reserved seat counts!
            # Only backfill missing metadata columns so restarts never wipe live reservations.
            db.execute(
                """UPDATE packages
                   SET origin = COALESCE(NULLIF(origin, ''), ?),
                       original_price_paise = CASE WHEN COALESCE(original_price_paise, 0) = 0 THEN ? ELSE original_price_paise END,
                       upcoming_dates = COALESCE(NULLIF(upcoming_dates, ''), ?),
                       trust_text = COALESCE(NULLIF(trust_text, ''), ?),
                       image_file = COALESCE(NULLIF(image_file, ''), ?),
                       official_url = COALESCE(NULLIF(official_url, ''), ?),
                       activities = COALESCE(NULLIF(activities, ''), ?)
                   WHERE id=?""",
                (
                    p["origin"],
                    p["original_price_paise"],
                    p["upcoming_dates"],
                    p["trust_text"],
                    p["image_file"],
                    p["official_url"],
                    p["activities"],
                    pkg_id,
                ),
            )
            has_details = db.execute("SELECT 1 FROM package_details WHERE package_id=?", (pkg_id,)).fetchone()
            if not has_details:
                db.execute(
                    """INSERT INTO package_details(package_id, stay_type, meal_plan, transport, inclusions, itinerary)
                       VALUES(?,?,?,?,?,?)""",
                    (pkg_id, *p["details"]),
                )
        else:
            cur = db.execute(
                """INSERT INTO packages(title, destination, category, description, duration,
                                        price_paise, capacity, reserved, image_file, official_url, activities,
                                        origin, original_price_paise, upcoming_dates, trust_text)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (p["title"], p["destination"], p["category"], p["description"], p["duration"],
                 p["price_paise"], p["capacity"], p["reserved"], p["image_file"], p["official_url"], p["activities"],
                 p["origin"], p["original_price_paise"], p["upcoming_dates"], p["trust_text"]),
            )
            pkg_id = cur.lastrowid
            db.execute(
                """INSERT OR REPLACE INTO package_details(package_id, stay_type, meal_plan, transport, inclusions, itinerary)
                   VALUES(?,?,?,?,?,?)""",
                (pkg_id, *p["details"]),
            )

    db.commit()
    print("TravelEasy packages verified (live reservations and user data preserved permanently).")
    db.close()

if __name__ == "__main__":
    run_seed()
