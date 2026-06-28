from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse, UpdateStateRequest, UpdateLocationRequest
from app.services.user_service import user_service
from sqlalchemy import select

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new citizen user and return a JWT access token."""
    token = await user_service.register_user(
        db=db,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        state_id=payload.state_id
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user credentials and return a JWT access token."""
    token = await user_service.login_user(
        db=db,
        email=payload.email,
        password=payload.password
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get profile information for the currently authenticated user."""
    return current_user


@router.patch("/me/state", response_model=UserResponse)
async def update_my_state(
    payload: UpdateStateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set or update the authenticated user's state."""
    current_user.state_id = payload.state_id
    db.add(current_user)
    await db.commit()
    
    from sqlalchemy.orm import joinedload
    result = await db.execute(
        select(User)
        .options(joinedload(User.region))
        .where(User.id == current_user.id)
    )
    return result.scalars().first()


@router.patch("/me/location", response_model=UserResponse)
async def update_my_location_region(
    payload: UpdateLocationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve coordinates to state/district regions and update the user's location profile."""
    from app.services.geo_service import reverse_geocode_region
    
    state_reg, district_reg = await reverse_geocode_region(payload.latitude, payload.longitude, db)
    
    if state_reg:
        current_user.state_id = state_reg.id
    if district_reg:
        current_user.region_id = district_reg.id
        
    db.add(current_user)
    await db.commit()
    
    from sqlalchemy.orm import joinedload
    result = await db.execute(
        select(User)
        .options(joinedload(User.region))
        .where(User.id == current_user.id)
    )
    return result.scalars().first()
