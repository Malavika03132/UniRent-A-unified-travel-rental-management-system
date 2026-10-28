import json
from datetime import datetime, date, timedelta
from app import create_app
from app.models import db, User, Owner, Admin, Property, Vehicle, Booking, Payment, Review, Complaint

app = create_app()

def seed_database():
    with app.app_context():
        # Clear existing data for fresh seed
        db.drop_all()
        db.create_all()
        print("Database schema created cleanly.")
        
        # 1. Seed Users
        # ADMIN
        admin_user = User(
            full_name="Anand Varma",
            email="admin@unirent.com",
            phone="+91 98470 12345",
            role="admin",
            status="active",
            kyc_document_type="pan_card",
            kyc_document_number="AAAPV1234K",
            kyc_status="verified"
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.flush()
        
        admin_profile = Admin(
            user_id=admin_user.user_id,
            admin_level="Super Admin",
            department="Kerala Operations & Heritage Curation"
        )
        db.session.add(admin_profile)
        
        # OWNERS
        owner1_user = User(
            full_name="Kavitha Menon",
            email="owner@unirent.com",
            phone="+91 94471 23456",
            role="owner",
            status="active",
            kyc_document_type="pan_card",
            kyc_document_number="ABCDE5678F",
            kyc_status="verified"
        )
        owner1_user.set_password("owner123")
        db.session.add(owner1_user)
        db.session.flush()
        
        owner1 = Owner(
            user_id=owner1_user.user_id,
            business_name="Menon Heritage Stays & Wheels",
            district="Ernakulam",
            kyc_status="verified",
            bank_account="HDFC0001234 - A/C 50100456789123",
            bio="Curator of 120-year-old restored Kerala Tharavadu homes and premium travel vehicles in Kochi & Aluva."
        )
        db.session.add(owner1)
        db.session.flush()
        
        owner2_user = User(
            full_name="George Kurian",
            email="owner2@unirent.com",
            phone="+91 97455 67890",
            role="owner",
            status="active",
            kyc_document_type="passport",
            kyc_document_number="Z8765432",
            kyc_status="verified"
        )
        owner2_user.set_password("owner123")
        db.session.add(owner2_user)
        db.session.flush()
        
        owner2 = Owner(
            user_id=owner2_user.user_id,
            business_name="Kurian Heritage Estates & Mobility",
            district="Thrissur",
            kyc_status="verified",
            bank_account="SBIN0008899 - A/C 30987654321098",
            bio="Specializing in authentic Nalukettu courtyards and adventure vehicles across the cultural capital of Thrissur."
        )
        db.session.add(owner2)
        db.session.flush()
        
        # TRAVELERS
        traveler1 = User(
            full_name="Arun Nambiar",
            email="traveler@unirent.com",
            phone="+91 99951 34567",
            role="traveler",
            status="active",
            kyc_document_type="pan_card",
            kyc_document_number="KLMNP9012Q",
            kyc_status="verified"
        )
        traveler1.set_password("traveler123")
        db.session.add(traveler1)
        
        traveler2 = User(
            full_name="Sneha Pillai",
            email="traveler2@unirent.com",
            phone="+91 98952 87654",
            role="traveler",
            status="active",
            kyc_document_type="voter_id",
            kyc_document_number="KLM7654321",
            kyc_status="verified"
        )
        traveler2.set_password("traveler123")
        db.session.add(traveler2)
        db.session.flush()
        
        # 2. Seed Heritage Properties (Ernakulam & Thrissur)
        prop1 = Property(
            owner_id=owner1.owner_id,
            property_name="Malarvadi Heritage Tharavadu",
            slug="malarvadi-heritage-tharavadu-aluva",
            property_type="Traditional Kerala House",
            description="A majestic 140-year-old authentic Nalukettu estate set alongside the serene Periyar river in Aluva. Featuring hand-carved rosewood beams, an open-air Nadumuttom central courtyard, a lotus pond, and antique Kerala brass decor. Experience monsoon rains from the covered verandah while savoring authentic sadhya breakfast.",
            address="River Road, Desom, Aluva",
            district="Ernakulam",
            latitude=10.1076,
            longitude=76.3516,
            price_per_night=5800.0,
            guest_capacity=6,
            bedrooms=3,
            bathrooms=3,
            amenities=json.dumps(["Nadumuttom Courtyard", "Riverfront Lawn", "Traditional Kerala Kitchen", "Free High-Speed Wi-Fi", "Air Conditioning", "Lotus Pond", "Ayurvedic Spa Facility", "Covered Parking"]),
            images=json.dumps([
                "/static/images/tharavadu.jpg",
                "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="/static/images/tharavadu.jpg",
            approval_status="approved",
            availability_status="available",
            featured=True
        )
        
        prop2 = Property(
            owner_id=owner1.owner_id,
            property_name="Dutch & Portuguese Heritage Manor",
            slug="dutch-portuguese-heritage-manor-fort-kochi",
            property_type="Heritage Villa",
            description="Restored colonial merchant residence located in the historic heart of Fort Kochi. High wooden ceilings, terracotta tiled floors, stained-glass arched windows, and a tranquil walled courtyard with private plunge pool. Located within walking distance from the iconic Chinese Fishing Nets and St. Francis Church.",
            address="Princess Street, Fort Kochi",
            district="Ernakulam",
            latitude=9.9658,
            longitude=76.2425,
            price_per_night=7200.0,
            guest_capacity=4,
            bedrooms=2,
            bathrooms=2,
            amenities=json.dumps(["Private Plunge Pool", "Terracotta Verandah", "Wi-Fi", "Air Conditioning", "Artisan Coffee Bar", "Heritage Walking Tour"]),
            images=json.dumps([
                "/static/images/dutch_manor.jpg",
                "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="/static/images/dutch_manor.jpg",
            approval_status="approved",
            availability_status="available",
            featured=True
        )
        
        prop3 = Property(
            owner_id=owner1.owner_id,
            property_name="Cherai Coconut Lagoon Heritage Villa",
            slug="cherai-coconut-lagoon-heritage-villa",
            property_type="Heritage Stay",
            description="A coastal wooden heritage stay tucked between the Arabian Sea and the tranquil backwaters of Cherai. Built with traditional laterite stone and teakwood, the villa offers breezy open sit-outs, swaying coconut groves, and spectacular sunset views.",
            address="Munambam Road, Cherai Beach",
            district="Ernakulam",
            latitude=10.1416,
            longitude=76.1783,
            price_per_night=4200.0,
            guest_capacity=5,
            bedrooms=2,
            bathrooms=2,
            amenities=json.dumps(["Backwater Access", "Beach Walk 200m", "Hammocks & Coconut Grove", "Wi-Fi", "Homecooked Karimeen Pollichathu", "Free Parking"]),
            images=json.dumps([
                "/static/images/cherai_lagoon.jpg",
                "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="/static/images/cherai_lagoon.jpg",
            approval_status="approved",
            availability_status="available",
            featured=False
        )
        
        prop4 = Property(
            owner_id=owner2.owner_id,
            property_name="Vadakkumnathan Heritage Illam",
            slug="vadakkumnathan-heritage-illam-thrissur",
            property_type="Traditional Kerala House",
            description="An ancestral Brahmin Illam situated close to the historic Vadakkumnathan Temple in Thrissur. Imbued with cultural heritage, sacred bronze uruli vessels, carved wooden pillars, and traditional architecture that preserves the royal cultural spirit of Thrissur Pooram.",
            address="Near Swaraj Round, Thrissur Town",
            district="Thrissur",
            latitude=10.5276,
            longitude=76.2144,
            price_per_night=4900.0,
            guest_capacity=6,
            bedrooms=3,
            bathrooms=3,
            amenities=json.dumps(["Temple Heritage Architecture", "Herbal Garden", "Traditional Brass Lamps", "Wi-Fi", "Air Conditioning", "Vegetarian Kerala Kitchen"]),
            images=json.dumps([
                "/static/images/Illam.jpg",
                "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="/static/images/Illam.jpg",
            approval_status="approved",
            availability_status="available",
            featured=True
        )
        
        prop5 = Property(
            owner_id=owner2.owner_id,
            property_name="Puzhakkal Riverfront Nalukettu",
            slug="puzhakkal-riverfront-nalukettu-thrissur",
            property_type="Heritage Villa",
            description="Panoramic riverside Nalukettu overlooking lush green paddy fields in Puzhakkal, Thrissur. Features natural clay roof tiles, an interior sunken courtyard that catches cool evening breezes, and a private wooden boat jetty for sunrise canoe rides.",
            address="Puzhakkal River Walk, Thrissur",
            district="Thrissur",
            latitude=10.5510,
            longitude=76.1850,
            price_per_night=5400.0,
            guest_capacity=8,
            bedrooms=4,
            bathrooms=3,
            amenities=json.dumps(["Riverfront Deck", "Canoe Boat Ride", "Nadumuttom", "High-Speed Wi-Fi", "Yoga Pavilion", "Lush Lawn"]),
            images=json.dumps([
                "/static/images/puzhakkal_nalukettu.jpg",
                "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="/static/images/puzhakkal_nalukettu.jpg",
            approval_status="approved",
            availability_status="available",
            featured=False
        )
        
        # PENDING PROPERTY FOR ADMIN APPROVAL DEMO
        prop_pending = Property(
            owner_id=owner2.owner_id,
            property_name="Athirappilly Rainforest Heritage Retreat",
            slug="athirappilly-rainforest-heritage-retreat",
            property_type="Heritage Stay",
            description="Secluded teakwood cottage perched on the mist-covered foothills near Athirappilly Waterfalls in Thrissur. Newly submitted for verification with handmade bamboo furnishings and solar-powered amenities.",
            address="Waterfalls Road, Chalakudy, Thrissur",
            district="Thrissur",
            latitude=10.2851,
            longitude=76.5698,
            price_per_night=6200.0,
            guest_capacity=4,
            bedrooms=2,
            bathrooms=2,
            amenities=json.dumps(["Waterfall Sound Views", "Solar Powered", "Forest Balcony", "Wi-Fi"]),
            images=json.dumps([
                "/static/images/athirappilly_retreat.jpg",
                "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="/static/images/athirappilly_retreat.jpg",
            approval_status="pending",  # PENDING APPROVAL
            availability_status="available",
            featured=False
        )
        
        prop6 = Property(
            owner_id=owner1.owner_id,
            property_name="Vembanad Luxury Backwater Houseboat & Heritage Lodge",
            slug="vembanad-luxury-backwater-houseboat-kochi",
            property_type="Heritage Stay",
            description="Authentic Kettuvallam wooden houseboat stay docked along the pristine backwaters of Kumbalangi Integrated Tourism Village. Features traditional coir and bamboo thatched roof, teakwood sundeck, air-conditioned luxury bedrooms, and private chef preparing fresh Karimeen fish fry.",
            address="Kumbalangi Backwater Jetty, Kochi",
            district="Ernakulam",
            latitude=9.8732,
            longitude=76.2891,
            price_per_night=8500.0,
            guest_capacity=4,
            bedrooms=2,
            bathrooms=2,
            amenities=json.dumps(["Sunset Sundeck", "Private Onboard Chef", "Air Conditioning", "Canoe Exploration", "Wi-Fi", "Traditional Toddy & Sadhya Meals"]),
            images=json.dumps([
                "/static/images/houseboat.jpg",
                "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="/static/images/houseboat.jpg",
            approval_status="approved",
            availability_status="available",
            featured=True
        )

        prop7 = Property(
            owner_id=owner2.owner_id,
            property_name="Shakthan Thampuran Royal Courtyard Manor",
            slug="shakthan-thampuran-royal-courtyard-manor-thrissur",
            property_type="Heritage Villa",
            description="19th-century royal palace residency adjacent to the historic Shakthan Thampuran Palace in Thrissur. Preserves classical Dutch-Kerala architectural fusion, carved teak ceilings, sweeping red oxide verandas, and a private heritage courtyard.",
            address="Palace Road, Chembukkavu, Thrissur",
            district="Thrissur",
            latitude=10.5315,
            longitude=76.2210,
            price_per_night=6400.0,
            guest_capacity=6,
            bedrooms=3,
            bathrooms=3,
            amenities=json.dumps(["Royal Heritage Courtyard", "Antique Rosewood Furniture", "Wi-Fi", "Air Conditioning", "Ayurvedic Massage Facility", "Free Parking"]),
            images=json.dumps([
                "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=False
        )

        prop8 = Property(
            owner_id=owner1.owner_id,
            property_name="Chendamangalam Handloom Heritage Kovilakam",
            slug="chendamangalam-handloom-heritage-kovilakam-paravur",
            property_type="Traditional Kerala House",
            description="Historic riverfront kovilakam situated in Chendamangalam, the ancient seat of the Paliath Achans. Overlooks the Periyar tributary, surrounded by weaving villages, traditional spice groves, and 18th-century architecture with copper roofing.",
            address="Kovilakam Road, Chendamangalam, North Paravur",
            district="Ernakulam",
            latitude=10.1582,
            longitude=76.2163,
            price_per_night=4800.0,
            guest_capacity=5,
            bedrooms=2,
            bathrooms=2,
            amenities=json.dumps(["Nadumuttom Courtyard", "River Bathing Ghat", "Handloom Weaving Workshop Tour", "Wi-Fi", "Organic Kitchen Garden"]),
            images=json.dumps([
                "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=False
        )

        prop9 = Property(
            owner_id=owner2.owner_id,
            property_name="Guruvayur Temple Heritage Illam",
            slug="guruvayur-temple-heritage-illam-thrissur",
            property_type="Traditional Kerala House",
            description="Serene traditional Illam located within gentle walking distance of the sacred Guruvayur Sri Krishna Temple. Intricate wood carvings, peaceful meditation verandah, private herbal garden, and sattvic Kerala traditional cuisine.",
            address="East Nada, Guruvayur, Thrissur",
            district="Thrissur",
            latitude=10.5947,
            longitude=76.0401,
            price_per_night=3800.0,
            guest_capacity=4,
            bedrooms=2,
            bathrooms=2,
            amenities=json.dumps(["Temple Heritage Sitout", "Pure Vegetarian Kitchen", "Air Conditioning", "Wi-Fi", "Meditation Courtyard", "Covered Car Parking"]),
            images=json.dumps([
                "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=False
        )
        
        db.session.add_all([prop1, prop2, prop3, prop4, prop5, prop_pending, prop6, prop7, prop8, prop9])
        db.session.flush()
        
        # 3. Seed Vehicles (Cars, Bikes, Scooters)
        veh1 = Vehicle(
            owner_id=owner1.owner_id,
            vehicle_name="Royal Enfield Classic 350",
            model="Stealth Black Edition (2024)",
            vehicle_type="bike",
            description="The quintessential motorcycle for Kerala backroad cruising. Impeccably maintained dual-channel ABS, comfortable touring seat, thump exhaust note, and dual luggage racks. Explore Fort Kochi alleys and coastal highways with vintage elegance.",
            price_per_day=950.0,
            district="Ernakulam",
            pickup_location="Fort Kochi Heritage Hub / Princess St",
            latitude=9.9658,
            longitude=76.2425,
            delivery_available=True,
            specifications=json.dumps({"transmission": "Manual 5-Speed", "fuel": "Petrol (BS6)", "seats": "2 Seater", "mileage": "36 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1609630875171-b1321377ee65?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1558980664-769d59546b3d?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1609630875171-b1321377ee65?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=True
        )
        
        veh2 = Vehicle(
            owner_id=owner1.owner_id,
            vehicle_name="Mahindra Thar 4x4 Hard Top",
            model="LX Automatic Diesel (2023)",
            vehicle_type="car",
            description="Tackle every Kerala terrain in style—from misty highland forest trails to monsoon drenched coastal routes. Features 4WD with low-range transfer case, touchscreen Apple CarPlay/Android Auto, climate control, and rugged all-terrain tires.",
            price_per_day=3200.0,
            district="Ernakulam",
            pickup_location="Marine Drive / Ernakulam South Railway Hub",
            latitude=9.9816,
            longitude=76.2799,
            delivery_available=True,
            specifications=json.dumps({"transmission": "Automatic 6-Speed", "fuel": "Diesel Turbo", "seats": "4 Seater", "mileage": "14 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=True
        )
        
        veh3 = Vehicle(
            owner_id=owner1.owner_id,
            vehicle_name="Vespa Elegante 125",
            model="Portofino Coral Edition (2024)",
            vehicle_type="scooter",
            description="Italian retro charm meeting Kerala seaside aesthetics. Effortless twist-and-go automatic, front disc brake, comfortable plush split seat, and a rear chrome rack. Ideal for nimble hops between heritage cafes and art galleries in Kochi.",
            price_per_day=650.0,
            district="Ernakulam",
            pickup_location="Mattancherry Jew Town Gate",
            latitude=9.9578,
            longitude=76.2592,
            delivery_available=False,
            specifications=json.dumps({"transmission": "CVT Automatic", "fuel": "Petrol", "seats": "2 Seater", "mileage": "48 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1558981408-db0ecd8a1ee4?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1591637333184-19aa84b3e01f?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=False
        )
        
        veh4 = Vehicle(
            owner_id=owner2.owner_id,
            vehicle_name="Toyota Innova Crysta",
            model="2.4 ZX 7-Seater Luxury (2023)",
            vehicle_type="car",
            description="The premier Kerala family touring vehicle. Spacious captain seats in the middle row, ambient cabin lighting, dual rear AC vents, and generous luggage capacity. Perfect for group trips across Thrissur temples and scenic Kerala heritage circuits.",
            price_per_day=2800.0,
            district="Thrissur",
            pickup_location="Thrissur Railway Station East Hub",
            latitude=10.5186,
            longitude=76.2120,
            delivery_available=True,
            specifications=json.dumps({"transmission": "Manual 5-Speed", "fuel": "Diesel D-4D", "seats": "7 Seater", "mileage": "15 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1508974239320-0a029497e820?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=True
        )
        
        veh5 = Vehicle(
            owner_id=owner2.owner_id,
            vehicle_name="Royal Enfield Himalayan 450",
            model="Kaza Brown Adventure (2024)",
            vehicle_type="bike",
            description="Built for pure adventure and mountain trails. Liquid-cooled Sherpa engine, Ride-by-Wire with navigation Google Maps casting, long travel suspension, and switchable ABS. Tackle the Sholayar jungle pass and Athirappilly rainforest with total confidence.",
            price_per_day=1200.0,
            district="Thrissur",
            pickup_location="Swaraj Round North, Thrissur",
            latitude=10.5276,
            longitude=76.2144,
            delivery_available=True,
            specifications=json.dumps({"transmission": "6-Speed Assist & Slipper", "fuel": "Petrol (Liquid Cooled)", "seats": "2 Seater", "mileage": "30 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1615172282427-9a57ef2d142e?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1558980664-769d59546b3d?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1615172282427-9a57ef2d142e?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=False
        )
        
        # PENDING VEHICLE FOR ADMIN APPROVAL DEMO
        veh_pending = Vehicle(
            owner_id=owner2.owner_id,
            vehicle_name="Force Gurkha 4x4 Heritage Edition",
            model="3-Door Green Explorer (2024)",
            vehicle_type="car",
            description="Rugged 4x4 equipped with factory snorkel, front and rear differential locks, and high ground clearance. Brand new listing awaiting admin document verification.",
            price_per_day=3000.0,
            district="Thrissur",
            pickup_location="Chalakudy Junction, Thrissur",
            latitude=10.3070,
            longitude=76.3330,
            delivery_available=True,
            specifications=json.dumps({"transmission": "Manual 5-Speed", "fuel": "Diesel CRDe", "seats": "4 Seater", "mileage": "12 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1200&q=80",
            approval_status="pending",  # PENDING APPROVAL
            availability_status="available",
            featured=False
        )
        
        veh6 = Vehicle(
            owner_id=owner1.owner_id,
            vehicle_name="Tata Harrier Dark Edition",
            model="XZA Plus Kryotec Automatic (2024)",
            vehicle_type="car",
            description="Bold, premium midnight black SUV with panoramic sunroof, 360-degree camera, wireless charging, JBL 9-speaker sound system, and comfortable ventilated seats. Seamlessly travels Kerala national highways and hill passes.",
            price_per_day=3500.0,
            security_deposit=2000.0,
            district="Ernakulam",
            pickup_location="Cochin International Airport (COK) Terminal 1 Hub",
            latitude=10.1518,
            longitude=76.4019,
            delivery_available=True,
            specifications=json.dumps({"transmission": "Automatic 6-Speed", "fuel": "Diesel Turbo", "seats": "5 Seater", "mileage": "16 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=True
        )

        veh7 = Vehicle(
            owner_id=owner1.owner_id,
            vehicle_name="Honda Activa 6G Premium Edition",
            model="Deluxe Smart Key (2024)",
            vehicle_type="scooter",
            description="Kerala's most dependable and fuel-efficient automatic scooter. Equipped with silent start, telescopic front suspension, smart remote key, and LED headlamp. The perfect economical ride for Kochi traffic and Fort Kochi lanes.",
            price_per_day=450.0,
            security_deposit=1500.0,
            district="Ernakulam",
            pickup_location="Edappally Lulu Mall Hub / Metro Station",
            latitude=10.0261,
            longitude=76.3125,
            delivery_available=True,
            specifications=json.dumps({"transmission": "CVT Automatic", "fuel": "Petrol (eSP)", "seats": "2 Seater", "mileage": "55 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1591637333184-19aa84b3e01f?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1558981408-db0ecd8a1ee4?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1591637333184-19aa84b3e01f?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=False
        )

        veh8 = Vehicle(
            owner_id=owner2.owner_id,
            vehicle_name="Jawa 42 Bobber Heritage Custom",
            model="Jasper Red Dual Tone (2024)",
            vehicle_type="bike",
            description="Eye-catching modern classic motorcycle with single floating saddle, bar-end mirrors, dual exhausts, and a punchy 334cc liquid-cooled engine. Cruise through Thrissur cultural landmarks with unmatched head-turning style.",
            price_per_day=1100.0,
            security_deposit=2000.0,
            district="Thrissur",
            pickup_location="Thrissur Round South / Shakthan Stand",
            latitude=10.5192,
            longitude=76.2168,
            delivery_available=True,
            specifications=json.dumps({"transmission": "6-Speed Manual", "fuel": "Petrol (DOHC)", "seats": "Single Rider", "mileage": "32 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1558981285-6f0c94958bb6?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1558980664-3a031cf67ea8?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1558980664-10e7170b5df9?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1558981285-6f0c94958bb6?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=False
        )

        veh9 = Vehicle(
            owner_id=owner2.owner_id,
            vehicle_name="Toyota Urban Cruiser Hyryder Hybrid",
            model="Strong Hybrid V e-Drive (2024)",
            vehicle_type="car",
            description="Next-generation self-charging strong electric hybrid SUV. Whisper-quiet EV mode in city crawl, Heads-Up Display, 27.9 kmpl incredible mileage, and luxurious dual-tone leather interior. Ideal for eco-conscious Kerala road trips.",
            price_per_day=2900.0,
            security_deposit=2000.0,
            district="Thrissur",
            pickup_location="Puzhakkal Junction / Thrissur Highway Hub",
            latitude=10.5480,
            longitude=76.1920,
            delivery_available=True,
            specifications=json.dumps({"transmission": "e-CVT Automatic", "fuel": "Strong Electric-Hybrid", "seats": "5 Seater", "mileage": "28 kmpl"}),
            images=json.dumps([
                "https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=1200&q=80"
            ]),
            featured_image="https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=1200&q=80",
            approval_status="approved",
            availability_status="available",
            featured=True
        )

        db.session.add_all([veh1, veh2, veh3, veh4, veh5, veh_pending, veh6, veh7, veh8, veh9])
        db.session.flush()
        
        # 4. Seed Bookings & Payments
        # Booking 1: Upcoming Stay for Arun Nambiar
        b1_start = date.today() + timedelta(days=5)
        b1_end = date.today() + timedelta(days=8)
        b1_days = 3
        b1_rate = prop1.price_per_night
        b1_sub = b1_rate * b1_days
        b1_fee = round(b1_sub * 0.05, 2)
        b1_tax = round(b1_sub * 0.12, 2)
        b1_total = b1_sub + b1_fee + b1_tax
        
        booking1 = Booking(
            booking_reference="UR-2026-B8491",
            user_id=traveler1.user_id,
            owner_id=owner1.owner_id,
            listing_type="property",
            property_id=prop1.property_id,
            vehicle_id=None,
            start_date=b1_start,
            end_date=b1_end,
            total_days=b1_days,
            daily_rate=b1_rate,
            service_fee=b1_fee,
            tax_amount=b1_tax,
            total_amount=b1_total,
            booking_status="confirmed",
            special_requests="Arriving around 2 PM. Please arrange authentic Kerala traditional sadhya dinner on the arrival evening."
        )
        db.session.add(booking1)
        db.session.flush()
        
        pay1 = Payment(
            booking_id=booking1.booking_id,
            amount=b1_total,
            payment_method="card",
            transaction_reference="pay_RzpDemo908123A",
            payment_status="successful",
            gateway_response="{'status': 'captured', 'order_id': 'order_kerala_881'}"
        )
        db.session.add(pay1)
        
        # Booking 2: Active Vehicle Rental for Sneha Pillai
        b2_start = date.today() - timedelta(days=1)
        b2_end = date.today() + timedelta(days=2)
        b2_days = 3
        b2_rate = veh1.price_per_day
        b2_sub = b2_rate * b2_days
        b2_fee = round(b2_sub * 0.05, 2)
        b2_tax = round(b2_sub * 0.12, 2)
        b2_total = b2_sub + b2_fee + b2_tax
        
        booking2 = Booking(
            booking_reference="UR-2026-B9022",
            user_id=traveler2.user_id,
            owner_id=owner1.owner_id,
            listing_type="vehicle",
            property_id=None,
            vehicle_id=veh1.vehicle_id,
            start_date=b2_start,
            end_date=b2_end,
            total_days=b2_days,
            daily_rate=b2_rate,
            service_fee=b2_fee,
            tax_amount=b2_tax,
            total_amount=b2_total,
            booking_status="active",
            special_requests="Requesting two sanitized helmets."
        )
        db.session.add(booking2)
        db.session.flush()
        
        pay2 = Payment(
            booking_id=booking2.booking_id,
            amount=b2_total,
            payment_method="upi",
            transaction_reference="pay_UPI981245B",
            payment_status="successful"
        )
        db.session.add(pay2)
        
        # Booking 3: Completed Stay for Arun Nambiar (Eligible for Review & Complaint demo)
        b3_start = date.today() - timedelta(days=20)
        b3_end = date.today() - timedelta(days=17)
        b3_days = 3
        b3_rate = prop2.price_per_night
        b3_sub = b3_rate * b3_days
        b3_fee = round(b3_sub * 0.05, 2)
        b3_tax = round(b3_sub * 0.12, 2)
        b3_total = b3_sub + b3_fee + b3_tax
        
        booking3 = Booking(
            booking_reference="UR-2026-B7710",
            user_id=traveler1.user_id,
            owner_id=owner1.owner_id,
            listing_type="property",
            property_id=prop2.property_id,
            vehicle_id=None,
            start_date=b3_start,
            end_date=b3_end,
            total_days=b3_days,
            daily_rate=b3_rate,
            service_fee=b3_fee,
            tax_amount=b3_tax,
            total_amount=b3_total,
            booking_status="completed"
        )
        db.session.add(booking3)
        db.session.flush()
        
        pay3 = Payment(
            booking_id=booking3.booking_id,
            amount=b3_total,
            payment_method="netbanking",
            transaction_reference="pay_NB451029C",
            payment_status="successful"
        )
        db.session.add(pay3)
        
        # 5. Seed Reviews
        rev1 = Review(
            booking_id=booking3.booking_id,
            user_id=traveler1.user_id,
            listing_type="property",
            property_id=prop2.property_id,
            vehicle_id=None,
            rating=5,
            review_title="Unforgettable Fort Kochi Colonial Experience",
            review_text="Staying at this restored manor felt like traveling back in time while enjoying 5-star modern luxury. The courtyard pool was serene, and Kavitha was an exceptional host who shared wonderful stories about the mansion's history.",
            image_url="https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80"
        )
        db.session.add(rev1)
        
        # 6. Seed Complaints (for testing Traveler, Owner & Admin workflows)
        comp1 = Complaint(
            complaint_reference="UR-CMP-104",
            booking_id=booking3.booking_id,
            user_id=traveler1.user_id,
            owner_id=owner1.owner_id,
            category="Owner/Service Issue",
            description="During check-in, there was a 35-minute delay accessing the courtyard suite because the key handoff concierge had stepped away.",
            evidence_image=None,
            status="owner_responded",
            owner_response="We sincerely apologized to Arun and offered a complimentary traditional tea ceremony on the verandah. Our concierge protocols have been restructured to prevent any further check-in delays.",
            admin_response="UniRent Ops noted host's proactive resolution and guest satisfaction."
        )
        db.session.add(comp1)
        
        db.session.commit()
        print("UniRent demo database seeded successfully with Kerala stays, vehicles, users, bookings, reviews & complaints!")

if __name__ == '__main__':
    seed_database()
