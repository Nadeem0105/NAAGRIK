import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import safe_transaction
from app.repositories.user_repo import user_repo
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import DuplicateIssueException, UnauthorizedActionException
from app.models.user import User

logger = logging.getLogger(__name__)


class UserService:
    async def register_user(self, db: AsyncSession, name: str, email: str, password: str, state_id: uuid.UUID | None = None) -> str:
        """Register a new user and return a JWT access token."""
        # Wrap in a transaction block
        async with safe_transaction(db):
            existing = await user_repo.get_by_email(db, email.lower())
            if existing:
                raise DuplicateIssueException("A user with this email already exists.")

            user_data = {
                "name": name,
                "email": email.lower(),
                "password_hash": hash_password(password),
                "role": "citizen",
                "points": 0,
                "state_id": state_id
            }
            user = await user_repo.create(db, user_data)
            
        # Generate access token
        return create_access_token(subject=user.id)

    async def login_user(self, db: AsyncSession, email: str, password: str) -> str:
        """Authenticate user credentials and return a JWT access token."""
        # No write transaction needed for simple login
        user = await user_repo.get_by_email(db, email.lower())
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedActionException("Incorrect email or password.")
        
        # Build scope claims for admin users so every request carries its own scope
        extra_claims = {}
        if user.role == "admin":
            extra_claims["admin_scope"] = user.admin_scope  # 'district', 'state', 'super', or None
            extra_claims["region_id"] = str(user.region_id) if user.region_id else None

        return create_access_token(subject=user.id, extra_claims=extra_claims)


# Singleton instance
user_service = UserService()
