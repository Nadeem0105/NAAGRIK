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
    
    # 2. Run Database Upgrades (Create missing tables/columns)
    try:
        from scripts.upgrade_db import upgrade
        await upgrade()
        logger.info("Database upgrades completed successfully.")
    except Exception as e:
        logger.error("Failed to run database upgrades", error=str(e), exc_info=True)
        
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

    # Temporary fix route
    @application.get("/fix-regions", tags=["Admin"])
    async def fix_regions(db: AsyncSession = Depends(get_db)):
        from sqlalchemy import text
        try:
            await db.execute(text("""
                UPDATE regions 
                SET bbox_south = 11.5, bbox_north = 18.5, bbox_west = 74.0, bbox_east = 78.5,
                    boundary_geojson = :gj
                WHERE name = 'Karnataka'
            """), {"gj": r"""{"type": "Feature", "properties": {"name": "Karnataka"}, "geometry": {"type": "Point", "coordinates": [77.7518975, 12.9828866]}}"""})
            
            await db.execute(text("""
                UPDATE regions 
                SET bbox_south = 12.83, bbox_north = 13.14, bbox_west = 77.46, bbox_east = 77.78,
                    boundary_geojson = :gj
                WHERE name = 'Bengaluru Urban'
            """), {"gj": r"""{"type": "Feature", "properties": {"name": "Bengaluru Urban"}, "geometry": {"type": "Polygon", "coordinates": [[[77.3255304, 12.976003], [77.3366061, 12.8768929], [77.3794344, 12.8552459], [77.431301, 12.8749113], [77.4199057, 12.8262366], [77.4787826, 12.8114521], [77.4864318, 12.7428125], [77.5409501, 12.7481156], [77.5474988, 12.801405], [77.5647992, 12.7599503], [77.59213, 12.7798297], [77.5571435, 12.7275076], [77.5680703, 12.7012031], [77.6142441, 12.7119539], [77.6037013, 12.6924574], [77.5946385, 12.666797], [77.5963313, 12.6641628], [77.7410016, 12.6737335], [77.8090335, 12.7968339], [77.7925886, 12.843407], [77.8369637, 12.8703556], [77.8318426, 12.9256221], [77.7652716, 12.942299], [77.7815529, 13.0333274], [77.7664991, 13.1076287], [77.7241029, 13.1254092], [77.7272677, 13.1925113], [77.5750464, 13.1983263], [77.5517075, 13.2346762], [77.5213334, 13.2068629], [77.4792108, 13.2242132], [77.4689921, 13.1622982], [77.4317958, 13.1650843], [77.3929209, 13.1176399], [77.4237021, 13.0702699], [77.3841239, 13.0678696], [77.3720145, 12.9921528], [77.3255304, 12.976003]]]}}"""})
            
            await db.execute(text("""
                UPDATE regions 
                SET bbox_south = 8.0, bbox_north = 13.5, bbox_west = 76.2, bbox_east = 80.3,
                    boundary_geojson = :gj
                WHERE name = 'Tamil Nadu'
            """), {"gj": r"""{"type": "Feature", "properties": {"name": "Tamil Nadu"}, "geometry": {"type": "Point", "coordinates": [80.2657136, 13.0638307]}}"""})
            
            await db.execute(text("""
                UPDATE regions 
                SET bbox_south = 12.98, bbox_north = 13.25, bbox_west = 80.16, bbox_east = 80.33,
                    boundary_geojson = :gj
                WHERE name = 'Chennai'
            """), {"gj": r"""{"type": "Feature", "properties": {"name": "Chennai"}, "geometry": {"type": "Polygon", "coordinates": [[[80.1304149, 13.0448638], [80.1481335, 12.966764], [80.2028346, 12.9601675], [80.1715886, 12.9367847], [80.1821708, 12.8677863], [80.2421665, 12.852787], [80.3001371, 13.1432677], [80.201532, 13.1287776], [80.187149, 13.0234782], [80.1304149, 13.0448638]]]}}"""})
            
            await db.commit()
            return {"status": "success", "message": "Regions updated successfully with exact GeoJSON polygons"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


    @application.get("/run-migrations", tags=["Admin"])
    def run_migrations():
        try:
            from alembic.config import Config
            from alembic import command
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            return {"status": "success", "message": "Migrations applied successfully"}
        except Exception as e:
            import traceback
            return {"status": "error", "message": str(e), "trace": traceback.format_exc()}


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
