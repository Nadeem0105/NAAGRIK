import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, bbox_south FROM regions WHERE name='Bengaluru Urban'"))
        for row in res.fetchall():
            print(row)

asyncio.run(check())
