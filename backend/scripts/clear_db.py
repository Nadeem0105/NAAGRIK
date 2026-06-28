import asyncio
import logging
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.issue import Issue
from app.models.verification import Verification
from app.models.comment import Comment
from app.models.status_history import StatusHistory
from app.models.notification import Notification
from app.models.user_badge import UserBadge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clear_db")

async def clear_database():
    logger.info("Initializing database connection for cleanup...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        # Delete related tables first (to avoid foreign key constraint violations)
        logger.info("Deleting comments...")
        await db.execute(delete(Comment))
        
        logger.info("Deleting verifications...")
        await db.execute(delete(Verification))
        
        logger.info("Deleting status histories...")
        await db.execute(delete(StatusHistory))
        
        logger.info("Deleting notifications...")
        await db.execute(delete(Notification))
        
        logger.info("Deleting user badges...")
        await db.execute(delete(UserBadge))
        
        logger.info("Deleting issues...")
        await db.execute(delete(Issue))
        
        logger.info("Deleting citizen users (keeping admin)...")
        await db.execute(delete(User).where(User.role != "admin"))
        
        await db.commit()
        logger.info("Cleanup completed successfully. Non-admin user data deleted.")

if __name__ == "__main__":
    asyncio.run(clear_database())
