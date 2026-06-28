import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.issue import Issue
from app.models.verification import Verification
from app.models.comment import Comment
from app.models.department import Department
from app.models.badge import Badge

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("view_db")

async def view_database():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        print("\n" + "="*60)
        print(" NAGARIK DATABASE REPORT")
        print("="*60)

        # 1. Departments
        print("\n--- DEPARTMENTS ---")
        depts_res = await db.execute(select(Department))
        depts = depts_res.scalars().all()
        if not depts:
            print("No departments configured.")
        for d in depts:
            print(f"- ID: {d.id} | Name: {d.name} | Categories: {', '.join(d.category_mapping)}")

        # 2. Badges
        print("\n--- GLOBAL BADGES ---")
        badges_res = await db.execute(select(Badge))
        badges = badges_res.scalars().all()
        if not badges:
            print("No badges configured.")
        for b in badges:
            print(f"- {b.name}: {b.description}")

        # 3. Users
        print("\n--- REGISTERED USERS ---")
        users_res = await db.execute(select(User))
        users = users_res.scalars().all()
        if not users:
            print("No users registered.")
        for u in users:
            print(f"- Name: {u.name} | Email: {u.email} | Role: {u.role} | Points: {u.points}")

        # 4. Issues
        print("\n--- CIVIC ISSUES ---")
        issues_res = await db.execute(select(Issue))
        issues = issues_res.scalars().all()
        if not issues:
            print("No active civic issues reported.")
        for i in issues:
            print(f"- [{i.status.upper()}] Title: '{i.title}' | Category: {i.category} | Severity: {i.severity}")
            print(f"  Location: ({i.latitude}, {i.longitude}) | Address: {i.address}")
            print(f"  Reporter ID: {i.reporter_id}")

        # 5. Comments
        print("\n--- COMMENTS / FIELD NOTES ---")
        comments_res = await db.execute(select(Comment))
        comments = comments_res.scalars().all()
        if not comments:
            print("No comments.")
        for c in comments:
            print(f"- Issue ID: {c.issue_id} | User: {c.user_name} | Content: '{c.content}'")

        # 6. Verifications
        print("\n--- VERIFICATIONS / ENDORSEMENTS ---")
        verif_res = await db.execute(select(Verification))
        verifs = verif_res.scalars().all()
        if not verifs:
            print("No verifications recorded.")
        for v in verifs:
            print(f"- Issue ID: {v.issue_id} | User ID: {v.user_id} | Type: {v.verification_type}")

        print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(view_database())
