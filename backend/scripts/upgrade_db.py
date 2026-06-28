import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.models.base import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("upgrade_db")

async def upgrade():
    logger.info("Initializing database upgrade...")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # 1. Add columns to issues if they don't exist
        logger.info("Altering issues table if columns are missing...")
        
        # Check and add resolution_image_url
        res_img_check = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='issues' AND column_name='resolution_image_url'"
        ))
        if not res_img_check.fetchone():
            await conn.execute(text("ALTER TABLE issues ADD COLUMN resolution_image_url VARCHAR"))
            logger.info("Added column resolution_image_url to issues table.")
        else:
            logger.info("Column resolution_image_url already exists.")
            
        # Check and add sla_due_at
        sla_check = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='issues' AND column_name='sla_due_at'"
        ))
        if not sla_check.fetchone():
            await conn.execute(text("ALTER TABLE issues ADD COLUMN sla_due_at TIMESTAMP WITHOUT TIME ZONE"))
            logger.info("Added column sla_due_at to issues table.")
        else:
            logger.info("Column sla_due_at already exists.")

        # 2. Create issue_followers table if it doesn't exist
        logger.info("Creating issue_followers table if missing...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS issue_followers (
                issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
                PRIMARY KEY (issue_id, user_id)
            )
        """))
        logger.info("Database upgrade complete.")

if __name__ == "__main__":
    asyncio.run(upgrade())
