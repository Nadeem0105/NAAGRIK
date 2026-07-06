import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:01051234@34.93.8.111:5432/community_hero"

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, bbox_south FROM regions WHERE name='Bengaluru Urban'"))
        for row in res.fetchall():
            print(row)

asyncio.run(check())
