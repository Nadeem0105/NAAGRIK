import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import structlog

from app.core.config import settings
from app.core.logging_config import setup_logging, request_id_ctx, user_id_ctx
from app.core.exceptions import NagarikException, IssueNotFoundException, UnauthorizedActionException, DuplicateIssueException
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Setup structlog
setup_logging()
logger = structlog.get_logger(__name__)

# Initialize slowapi rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # 1. Initialize Redis / InMemory Cache
    from app.core.redis import cache
    await cache.initialize()
    logger.info("Application startup complete.")
    yield
    logger.info("Application shutting down.")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Nagarik - API Gateway",
        description="Backend API for Nagarik civic engagement platform.",
        version="1.0.0",
        lifespan=lifespan
    )

    # Set rate limiter state and exception handler
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add CORS Middleware
    if settings.CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Request ID and Telemetry Middleware
    @application.middleware("http")
    async def request_middleware(request: Request, call_next):
        # 1. Tracing ID
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(req_id)
        
        # 2. Telemetry and slow request warning
        start_time = time.time()
        logger.info("Request started", method=request.method, path=request.url.path)
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Warn if requests take longer than 500ms
            if duration_ms > 500:
                logger.warning("Request slow", duration_ms=duration_ms, method=request.method, path=request.url.path, status_code=response.status_code)
            else:
                logger.info("Request completed", duration_ms=duration_ms, method=request.method, path=request.url.path, status_code=response.status_code)
            
            response.headers["X-Request-ID"] = req_id
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error("Request failed", error=str(e), duration_ms=duration_ms, method=request.method, path=request.url.path, exc_info=True)
            # Re-raise so exception handlers can map to user-friendly response
            raise e

    # Exception Handlers
    @application.exception_handler(NagarikException)
    async def nagarik_exception_handler(request: Request, exc: NagarikException):
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, IssueNotFoundException):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, UnauthorizedActionException):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, DuplicateIssueException):
            status_code = status.HTTP_400_BAD_REQUEST
            
        logger.warning("Domain exception occurred", error=exc.message, type=exc.__class__.__name__)
        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.message}
        )

    @application.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please contact support."}
        )

    # Health-check route
    @application.get("/health", tags=["Health"])
    async def health_check(db: AsyncSession = Depends(get_db)):
        db_status = "healthy"
        cache_status = "healthy"
        
        # Check DB
        try:
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
        except Exception as e:
            logger.error("Health check database error", error=str(e))
            db_status = "unhealthy"

        # Check Cache
        try:
            from app.core.redis import cache as redis_cache
            if not await redis_cache.ping():
                cache_status = "unhealthy"
        except Exception as e:
            logger.error("Health check cache error", error=str(e))
            cache_status = "unhealthy"

        status_code = status.HTTP_200_OK
        if db_status == "unhealthy" or cache_status == "unhealthy":
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if status_code == 200 else "unhealthy",
                "db": db_status,
                "cache": cache_status,
                "version": "1.0.0"
            }
        )

    # Temporary Seed route
    @application.get("/seed", tags=["Admin"])
    async def seed_database():
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if backend_dir not in sys.path:
            sys.path.append(backend_dir)
        try:
            from scripts.seed import seed_data
            await seed_data()
            return JSONResponse(status_code=200, content={"status": "success", "message": "Database seeded successfully!"})
        except Exception as e:
            return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


    # Add Session Middleware for OAuth
    from starlette.middleware.sessions import SessionMiddleware
    application.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)

    # Include Routers
    from app.routers.auth import router as auth_router
    from app.routers.auth_google import router as auth_google_router
    from app.routers.issues import router as issues_router
    from app.routers.departments import router as departments_router
    from app.routers.admin import router as admin_router
    from app.routers.gamification import router as gamification_router
    from app.routers.dashboard import router as dashboard_router
    from app.routers.notifications import router as notifications_router

    application.include_router(auth_router, prefix="/auth")
    application.include_router(auth_google_router, prefix="/auth/google")
    application.include_router(issues_router, prefix="/issues")
    application.include_router(departments_router, prefix="/departments")
    application.include_router(admin_router)
    application.include_router(gamification_router)
    application.include_router(dashboard_router)
    application.include_router(notifications_router)

    return application

app = create_app()
