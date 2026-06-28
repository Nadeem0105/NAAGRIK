import asyncio
import os
import dotenv
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Load .env
dotenv.load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def check_latest_issues():
    from app.models.issue import Issue
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Issue).order_by(Issue.created_at.desc()).limit(5))
        issues = result.scalars().all()
        
        if not issues:
            print("No issues found in the database.")
            return
            
        print(f"Found {len(issues)} issues:")
        for idx, issue in enumerate(issues, 1):
            print(f"\n--- Issue {idx} ---")
            print(f"ID: {issue.id}")
            print(f"Title: {issue.title}")
            print(f"Description: {issue.description}")
            print(f"Status: {issue.status}")
            print(f"Category: {issue.category}")
            print(f"Severity: {issue.severity}")
            print(f"Image URLs: {issue.image_urls}")
            print(f"Created At: {issue.created_at}")
            
            # Print verification metadata if it has any
            print(f"AI Verification: {getattr(issue, 'ai_metadata', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(check_latest_issues())
