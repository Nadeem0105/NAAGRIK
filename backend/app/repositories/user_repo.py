import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, user_data: dict) -> User:
        user = User(**user_data)
        db.add(user)
        await db.flush()
        return user

    async def increment_points(self, db: AsyncSession, user_id: uuid.UUID, points: int) -> Optional[User]:
        user = await self.get_by_id(db, user_id)
        if user:
            user.points += points
            db.add(user)
            await db.flush()
        return user


# Singleton instance
user_repo = UserRepository()
