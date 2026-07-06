import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, and_
from app.models.issue import Issue
from app.core.config import settings

async def main():
    # Use the live database URL since it's publicly accessible!
    DATABASE_URL = "postgresql+asyncpg://postgres:01051234@34.93.8.111:5432/postgres"
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine)
    
    # Wait, 34.93.8.111 is the WRONG database!
    pass

asyncio.run(main())
