from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# Create database engine
# postgresql+asyncpg is required for async execution
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for debug logging of queries
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get db session in FastAPI routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


from contextlib import asynccontextmanager

@asynccontextmanager
async def safe_transaction(db: AsyncSession):
    """Context manager to run database operations safely inside a transaction.
    If a transaction is already active on the session (e.g. from a prior query
    in the request context), it will execute inside that transaction and commit/rollback
    appropriately. If no transaction is active, it starts a new one.
    """
    if db.in_transaction():
        try:
            yield
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    else:
        async with db.begin():
            yield


