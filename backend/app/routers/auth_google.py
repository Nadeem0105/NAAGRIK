from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import secrets

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repo import user_repo

router = APIRouter(tags=["Auth Google"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID if hasattr(settings, 'GOOGLE_CLIENT_ID') else "dummy",
    client_secret=settings.GOOGLE_CLIENT_SECRET if hasattr(settings, 'GOOGLE_CLIENT_SECRET') else "dummy",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/login")
async def google_login(request: Request):
    # Ensure GOOGLE_REDIRECT_URI is set or build it dynamically
    redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', str(request.url_for('google_callback')))
    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)

@router.get("/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    # CSRF check
    state = request.query_params.get("state")
    if not state or state != request.session.get("oauth_state"):
        raise HTTPException(status_code=400, detail="CSRF Check Failed.")
    
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")

    if not userinfo or not userinfo.get("email_verified"):
        raise HTTPException(status_code=400, detail="Google account email not verified.")

    email = userinfo["email"]
    google_id = userinfo["sub"]

    # Account linking logic
    user = await user_repo.get_by_email(db, email)

    if user is None:
        # Brand new account - CITIZEN ONLY
        new_user_data = {
            "email": email,
            "name": userinfo.get("name", email.split("@")[0]),
            "auth_provider": "google",
            "google_id": google_id,
            "password_hash": None,
            "role": "citizen",
            "admin_scope": None,
            "region_id": None,
        }
        user = await user_repo.create(db, new_user_data)
        await db.commit()
        await db.refresh(user)
    elif user.google_id is None:
        # Link existing account to Google ID without modifying existing scopes/roles
        user.google_id = google_id
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Issue token using the exact same shape as email/password login
    extra_claims = {}
    if user.role == "admin":
        extra_claims["admin_scope"] = user.admin_scope
        extra_claims["region_id"] = str(user.region_id) if user.region_id else None

    access_token = create_access_token(subject=user.id, extra_claims=extra_claims)
    
    # We redirect to the frontend callback page passing the token in the URL fragment or query param
    frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000"
    return RedirectResponse(url=f"{frontend_url}/auth/callback?token={access_token}")
