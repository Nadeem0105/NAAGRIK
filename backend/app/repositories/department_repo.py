import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.department import Department


class DepartmentRepository:
    async def get_by_id(self, db: AsyncSession, department_id: uuid.UUID) -> Optional[Department]:
        stmt = select(Department).where(Department.id == department_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> list[Department]:
        stmt = select(Department)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, department_data: dict) -> Department:
        dept = Department(**department_data)
        db.add(dept)
        await db.flush()
        return dept


# Singleton instance
department_repo = DepartmentRepository()
