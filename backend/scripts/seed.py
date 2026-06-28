import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models.region import Region
from app.models.department import Department
from app.models.badge import Badge
from app.models.user import User
from app.models.issue import Issue
from app.models.verification import Verification
from app.models.comment import Comment
from app.models.status_history import StatusHistory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

# Core seed data lists
DEPARTMENTS_SEED = [
    {"name": "Roads & Infrastructure", "category_mapping": ["pothole", "road_damage", "encroachment"]},
    {"name": "Water & Sewerage", "category_mapping": ["water_leak", "drainage"]},
    {"name": "Solid Waste Management", "category_mapping": ["garbage"]},
    {"name": "Electricity & Streetlights", "category_mapping": ["streetlight"]},
    {"name": "Environment & Noise Control", "category_mapping": ["noise", "other"]}
]

BADGES_SEED = [
    {
        "name": "First Reporter",
        "description": "Reported your first local civic issue!",
        "criteria": {"type": "reports_count", "threshold": 1}
    },
    {
        "name": "Local Watchdog",
        "description": "Reported 10 civic issues to help your city.",
        "criteria": {"type": "reports_count", "threshold": 10}
    },
    {
        "name": "Community Hero",
        "description": "Reported 50 civic issues! Outstanding contribution.",
        "criteria": {"type": "reports_count", "threshold": 50}
    },
    {
        "name": "Active Verifier",
        "description": "Verified/upvoted 10 other citizens' reports.",
        "criteria": {"type": "verifications_count", "threshold": 10}
    },
    {
        "name": "Problem Solver",
        "description": "Have 5 of your reported issues fully resolved by the city.",
        "criteria": {"type": "resolved_reports", "threshold": 5}
    }
]


async def seed_data():
    logger.info("Starting database seeding...")
    
    # Create engine and session local
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        # 0. Seed Regions
        regions = {}

        # State: Karnataka
        result = await db.execute(select(Region).where(Region.name == "Karnataka", Region.type == "state"))
        karnataka = result.scalars().first()
        if not karnataka:
            karnataka = Region(id=uuid.uuid4(), name="Karnataka", type="state", parent_region_id=None)
            db.add(karnataka)
            logger.info("Seeded region: Karnataka (state)")
        regions["Karnataka"] = karnataka

        await db.flush()

        # Districts under Karnataka
        for district_name in ["Bengaluru Urban", "Mysuru"]:
            result = await db.execute(
                select(Region).where(Region.name == district_name, Region.type == "district")
            )
            district = result.scalars().first()
            if not district:
                district = Region(
                    id=uuid.uuid4(),
                    name=district_name,
                    type="district",
                    parent_region_id=karnataka.id
                )
                db.add(district)
                logger.info(f"Seeded region: {district_name} (district)")
            regions[district_name] = district

        await db.flush()

        # --- Second state: Tamil Nadu → Chennai (for cross-state isolation testing)
        result = await db.execute(select(Region).where(Region.name == "Tamil Nadu", Region.type == "state"))
        tamil_nadu = result.scalars().first()
        if not tamil_nadu:
            tamil_nadu = Region(id=uuid.uuid4(), name="Tamil Nadu", type="state", parent_region_id=None)
            db.add(tamil_nadu)
            logger.info("Seeded region: Tamil Nadu (state)")
        regions["Tamil Nadu"] = tamil_nadu

        await db.flush()

        result = await db.execute(select(Region).where(Region.name == "Chennai", Region.type == "district"))
        chennai = result.scalars().first()
        if not chennai:
            chennai = Region(id=uuid.uuid4(), name="Chennai", type="district", parent_region_id=tamil_nadu.id)
            db.add(chennai)
            logger.info("Seeded region: Chennai (district)")
        regions["Chennai"] = chennai

        await db.flush()

        # 1. Seed Departments
        departments = {}
        for dept_data in DEPARTMENTS_SEED:
            result = await db.execute(select(Department).where(Department.name == dept_data["name"]))
            dept = result.scalars().first()
            if not dept:
                dept = Department(
                    id=uuid.uuid4(),
                    name=dept_data["name"],
                    category_mapping=dept_data["category_mapping"]
                )
                db.add(dept)
                logger.info(f"Seeded department: {dept.name}")
            departments[dept_data["name"]] = dept
        
        await db.flush()

        # 2. Seed Badges
        for badge_data in BADGES_SEED:
            result = await db.execute(select(Badge).where(Badge.name == badge_data["name"]))
            badge = result.scalars().first()
            if not badge:
                badge = Badge(
                    id=uuid.uuid4(),
                    name=badge_data["name"],
                    description=badge_data["description"],
                    criteria=badge_data["criteria"]
                )
                db.add(badge)
                logger.info(f"Seeded badge: {badge.name}")
        
        await db.flush()

        # 3. Seed Users (1 Admin, 3 Citizens)
        users = {}
        
        # Super-Admin (global access — no region)
        admin_email = "admin@communityhero.gov.in"
        result = await db.execute(select(User).where(User.email == admin_email))
        admin = result.scalars().first()
        if not admin:
            admin = User(
                id=uuid.uuid4(),
                name="Municipal Admin",
                email=admin_email,
                password_hash=hash_password("adminpass"),
                role="admin",
                admin_scope="super",
                region_id=None,
                points=100,
                department_id=departments["Roads & Infrastructure"].id
            )
            db.add(admin)
            logger.info("Seeded super-admin user.")
        else:
            # Upgrade existing flat admin to super-admin
            if admin.admin_scope is None:
                admin.admin_scope = "super"
                db.add(admin)
                logger.info("Upgraded existing admin to super-admin scope.")
        users["admin"] = admin

        # District Admin — scoped to Bengaluru Urban
        district_admin_email = "bengaluru.admin@communityhero.gov.in"
        result = await db.execute(select(User).where(User.email == district_admin_email))
        district_admin = result.scalars().first()
        if not district_admin:
            district_admin = User(
                id=uuid.uuid4(),
                name="Bengaluru Urban District Admin",
                email=district_admin_email,
                password_hash=hash_password("districtpass"),
                role="admin",
                admin_scope="district",
                region_id=regions["Bengaluru Urban"].id,
                points=0
            )
            db.add(district_admin)
            logger.info("Seeded district admin (Bengaluru Urban).")
        users["district_admin"] = district_admin

        # State Admin — scoped to Karnataka (sees all districts)
        state_admin_email = "karnataka.admin@communityhero.gov.in"
        result = await db.execute(select(User).where(User.email == state_admin_email))
        state_admin = result.scalars().first()
        if not state_admin:
            state_admin = User(
                id=uuid.uuid4(),
                name="Karnataka State Admin",
                email=state_admin_email,
                password_hash=hash_password("statepass"),
                role="admin",
                admin_scope="state",
                region_id=regions["Karnataka"].id,
                points=0
            )
            db.add(state_admin)
            logger.info("Seeded state admin (Karnataka).")
        users["state_admin"] = state_admin

        # Tamil Nadu State Admin
        tn_state_admin_email = "tamilnadu.admin@communityhero.gov.in"
        result = await db.execute(select(User).where(User.email == tn_state_admin_email))
        tn_state_admin = result.scalars().first()
        if not tn_state_admin:
            tn_state_admin = User(
                id=uuid.uuid4(),
                name="Tamil Nadu State Admin",
                email=tn_state_admin_email,
                password_hash=hash_password("tnstatepass"),
                role="admin",
                admin_scope="state",
                region_id=regions["Tamil Nadu"].id,
                points=0
            )
            db.add(tn_state_admin)
            logger.info("Seeded state admin (Tamil Nadu).")
        users["tn_state_admin"] = tn_state_admin

        # Chennai District Admin
        chennai_admin_email = "chennai.admin@communityhero.gov.in"
        result = await db.execute(select(User).where(User.email == chennai_admin_email))
        chennai_admin = result.scalars().first()
        if not chennai_admin:
            chennai_admin = User(
                id=uuid.uuid4(),
                name="Chennai District Admin",
                email=chennai_admin_email,
                password_hash=hash_password("chennaipass"),
                role="admin",
                admin_scope="district",
                region_id=regions["Chennai"].id,
                points=0
            )
            db.add(chennai_admin)
            logger.info("Seeded district admin (Chennai).")
        users["chennai_admin"] = chennai_admin

        # Citizens
        citizen_emails = [
            ("Aarav Sharma", "aarav@example.com", 85),
            ("Ananya Rao", "ananya@example.com", 120),
            ("Vikram Singh", "vikram@example.com", 40)
        ]
        
        for name, email, points in citizen_emails:
            result = await db.execute(select(User).where(User.email == email))
            citizen = result.scalars().first()
            if not citizen:
                citizen = User(
                    id=uuid.uuid4(),
                    name=name,
                    email=email,
                    password_hash=hash_password("password123"),
                    role="citizen",
                    points=points
                )
                db.add(citizen)
                logger.info(f"Seeded citizen: {name}")
            users[email] = citizen
            
        await db.flush()


        # 4. Seed Issues around Bangalore
        # Bangalore base coordinates: Lat 12.9716, Lng 77.5946
        # Let's seed issues at different offsets to simulate real neighborhood issues
        issues_data = [
            {
                "title": "Massive pothole on Outer Ring Road",
                "description": "A huge pothole has formed near the flyover. It's causing heavy traffic delays and is dangerous for two-wheelers.",
                "category": "pothole",
                "severity": "high",
                "status": "assigned",
                "lat": 12.9782,
                "lng": 77.6435,
                "address": "Outer Ring Road, Indiranagar, Bengaluru, Karnataka 560038",
                "reporter": "aarav@example.com",
                "department": "Roads & Infrastructure",
                "images": ["https://picsum.photos/seed/pothole1/800/600"]
            },
            {
                "title": "Broken streetlight near playground",
                "description": "The streetlight next to the kids playground is broken. The area gets completely pitch dark after 6 PM, raise safety concerns.",
                "category": "streetlight",
                "severity": "medium",
                "status": "reported",
                "lat": 12.9654,
                "lng": 77.5890,
                "address": "Lalbagh Road, Sudhama Nagar, Bengaluru, Karnataka 560027",
                "reporter": "ananya@example.com",
                "department": "Electricity & Streetlights",
                "images": ["https://picsum.photos/seed/light1/800/600"]
            },
            {
                "title": "Sewage water leaking onto road",
                "description": "Open drainage/sewage pipeline leak is flooding the street with foul-smelling water. Pedestrians cannot walk.",
                "category": "drainage",
                "severity": "high",
                "status": "in_progress",
                "lat": 12.9592,
                "lng": 77.6144,
                "address": "Koramangala 3rd Block, Bengaluru, Karnataka 560034",
                "reporter": "vikram@example.com",
                "department": "Water & Sewerage",
                "images": ["https://picsum.photos/seed/leak1/800/600"]
            },
            {
                "title": "Garbage dumping site in residential area",
                "description": "Garbage has not been cleared for over a week here. Strays are scattering it and it's producing a terrible stench.",
                "category": "garbage",
                "severity": "medium",
                "status": "resolved",
                "lat": 12.9850,
                "lng": 77.6050,
                "address": "Ulsoor Road, Sivanchetti Gardens, Bengaluru, Karnataka 560008",
                "reporter": "aarav@example.com",
                "department": "Solid Waste Management",
                "images": ["https://picsum.photos/seed/garbage1/800/600"],
                "resolved": True
            },
            {
                "title": "Illegal road encroachment by construction materials",
                "description": "Construction sand and bricks have blocked half of the narrow sub-road, causing traffic jams.",
                "category": "encroachment",
                "severity": "low",
                "status": "reported",
                "lat": 12.9710,
                "lng": 77.6210,
                "address": "Domlur, Bengaluru, Karnataka 560071",
                "reporter": "ananya@example.com",
                "department": "Roads & Infrastructure",
                "images": ["https://picsum.photos/seed/encroach1/800/600"]
            },
            {
                "title": "Severe flooding on GNT Road",
                "description": "Heavy monsoon rains have caused severe waterlogging and flooding on GNT Road near Chennai.",
                "category": "drainage",
                "severity": "high",
                "status": "reported",
                "lat": 13.0827,
                "lng": 80.2707,
                "address": "Grand Northern Trunk Rd, Chennai, Tamil Nadu 600001",
                "reporter": "aarav@example.com",
                "department": "Water & Sewerage",
                "images": ["https://picsum.photos/seed/chennaiflood/800/600"],
                "region_name": "Chennai"
            }
        ]

        for issue_item in issues_data:
            # Check if issue already exists by title
            result = await db.execute(select(Issue).where(Issue.title == issue_item["title"]))
            if not result.scalars().first():
                # Get reporter and department
                rep = users.get(issue_item["reporter"])
                dept = departments.get(issue_item["department"])
                
                resolved_at = None
                if issue_item.get("resolved"):
                    resolved_at = datetime.utcnow() - timedelta(days=2)

                new_issue = Issue(
                    id=uuid.uuid4(),
                    reporter_id=rep.id if rep else None,
                    title=issue_item["title"],
                    description=issue_item["description"],
                    category=issue_item["category"],
                    severity=issue_item["severity"],
                    status=issue_item["status"],
                    latitude=issue_item["lat"],
                    longitude=issue_item["lng"],
                    address=issue_item["address"],
                    image_urls=issue_item["images"],
                    assigned_department_id=dept.id if dept else None,
                    region_id=regions[issue_item.get("region_name", "Bengaluru Urban")].id,
                    created_at=datetime.utcnow() - timedelta(days=10),
                    updated_at=datetime.utcnow() - timedelta(days=2),
                    resolved_at=resolved_at
                )
                db.add(new_issue)
                logger.info(f"Seeded issue: {new_issue.title}")
                
                # Add status history
                history = StatusHistory(
                    id=uuid.uuid4(),
                    issue_id=new_issue.id,
                    status=new_issue.status,
                    note="Initial report seeded",
                    created_at=new_issue.created_at
                )
                db.add(history)
                
                # If resolved, add resolved status history
                if resolved_at:
                    res_history = StatusHistory(
                        id=uuid.uuid4(),
                        issue_id=new_issue.id,
                        status="resolved",
                        note="Marked resolved by municipal authorities",
                        created_at=resolved_at
                    )
                    db.add(res_history)

        await db.commit()
        logger.info("Database seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
