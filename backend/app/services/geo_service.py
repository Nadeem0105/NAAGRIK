# f:\CN Hackathon\backend\app\services\geo_service.py
import logging
import httpx
import uuid
from sqlalchemy import func, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import Issue

logger = logging.getLogger(__name__)


async def reverse_geocode(lat: float, lng: float) -> str:
    """Reverse geocode latitude and longitude to a human-readable address using OSM Nominatim."""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
    headers = {
        "User-Agent": "CommunityHeroCivicSolver/1.0 (contact: support@communityhero.app)"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                display_name = data.get("display_name")
                if display_name:
                    return display_name
    except Exception as e:
        logger.error(f"Nominatim geocoding failed: {e}")
    
    # Fallback address format
    return f"Location coordinates: ({lat:.5f}, {lng:.5f})"


import asyncio

async def fetch_region_geometry(name: str, parent_name: str | None = None) -> dict | None:
    """Query Nominatim's search endpoint to get bbox and GeoJSON boundary."""
    # Respect Nominatim's strict 1 request/second usage policy for batch operations
    await asyncio.sleep(1.2)
    
    query = f"{name}, {parent_name}" if parent_name else name
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "polygon_geojson": 1,
        "limit": 1
    }
    headers = {
        "User-Agent": "CommunityHeroCivicSolver/1.0 (contact: support@communityhero.app)"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    return None
                result = data[0]
                bbox = result.get("boundingbox")  # [south, north, west, east]
                if bbox and len(bbox) == 4:
                    return {
                        "bbox": {
                            "south": float(bbox[0]), "north": float(bbox[1]),
                            "west": float(bbox[2]), "east": float(bbox[3]),
                        },
                        "geojson": result.get("geojson"),
                    }
    except Exception as e:
        logger.error(f"Nominatim region geometry search failed for {query}: {e}")
    return None


async def get_or_create_region(
    db: AsyncSession,
    name: str,
    region_type: str,
    parent_region_id: uuid.UUID | None = None
):
    """Look up a Region by (name, type), creating it if it doesn't exist."""
    from app.models.region import Region

    stmt = select(Region).where(
        Region.name == name,
        Region.type == region_type
    )
    result = await db.execute(stmt)
    region = result.scalar_one_or_none()

    if not region:
        # Fetch parent name for better query accuracy
        parent_name = None
        if parent_region_id:
            parent_stmt = select(Region.name).where(Region.id == parent_region_id)
            parent_res = await db.execute(parent_stmt)
            parent_name = parent_res.scalar()

        # Fetch geometry
        geometry = await fetch_region_geometry(name, parent_name)

        region = Region(
            id=uuid.uuid4(),
            name=name,
            type=region_type,
            parent_region_id=parent_region_id,
            bbox_south=geometry["bbox"]["south"] if geometry else None,
            bbox_north=geometry["bbox"]["north"] if geometry else None,
            bbox_west=geometry["bbox"]["west"] if geometry else None,
            bbox_east=geometry["bbox"]["east"] if geometry else None,
            boundary_geojson=geometry["geojson"] if geometry else None
        )
        db.add(region)
        await db.flush()  # assigns ID within current transaction
        logger.info(f"Auto-created region: {name} ({region_type})")

    return region


async def reverse_geocode_region(lat: float, lng: float, db: AsyncSession):
    """
    Resolve the administrative region (state + district) for a coordinate via Nominatim.
    Returns (state_region, district_region) — either may be None on failure.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
    headers = {
        "User-Agent": "CommunityHeroCivicSolver/1.0 (contact: support@communityhero.app)"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.warning(f"Nominatim region geocode returned {response.status_code}")
                return None, None

            data = response.json()
            address = data.get("address", {})

            state_name = address.get("state")
            district_name = address.get("county") or address.get("state_district")

            if not state_name:
                logger.warning(f"No state found in Nominatim response for ({lat}, {lng})")
                return None, None

            state_region = await get_or_create_region(
                db=db,
                name=state_name,
                region_type="state",
                parent_region_id=None
            )

            if not district_name:
                logger.warning(f"No district found for ({lat}, {lng}), attaching to state only")
                return state_region, None

            district_region = await get_or_create_region(
                db=db,
                name=district_name,
                region_type="district",
                parent_region_id=state_region.id
            )

            return state_region, district_region

    except Exception as e:
        logger.error(f"Nominatim region resolution failed: {e}")
        return None, None


async def find_nearby_issues(
    lat: float,
    lng: float,
    radius_meters: float,
    db: AsyncSession,
    category: str | None = None,
    exclude_id: str | None = None
) -> list[Issue]:
    """Find issues within a certain radius in meters using indexed bounding box and Haversine formula."""
    import math
    lat_delta = radius_meters / 111000.0
    cos_lat = math.cos(math.radians(lat))
    lng_delta = radius_meters / (111000.0 * cos_lat) if cos_lat > 0 else 0.0
    
    bbox_filters = [
        Issue.latitude.between(lat - lat_delta, lat + lat_delta),
        Issue.longitude.between(lng - lng_delta, lng + lng_delta)
    ]
    
    rad_lat = math.radians(lat)
    rad_lng = math.radians(lng)
    
    acos_arg = (
        func.sin(rad_lat) * func.sin(func.radians(Issue.latitude)) +
        func.cos(rad_lat) * func.cos(func.radians(Issue.latitude)) * 
        func.cos(func.radians(Issue.longitude) - rad_lng)
    )
    clamped_acos_arg = func.greatest(-1.0, func.least(1.0, acos_arg))
    distance_expr = 6371000 * func.acos(clamped_acos_arg)
    
    query = select(Issue).where(
        and_(
            *bbox_filters,
            distance_expr <= radius_meters
        )
    )
    
    if category:
        query = query.where(Issue.category == category)
        
    if exclude_id:
        query = query.where(Issue.id != exclude_id)
        
    # We only match open/active issues (not resolved) for duplicate checks
    query = query.where(Issue.status != "resolved")
    
    result = await db.execute(query)
    return list(result.scalars().all())


def get_bbox_filter(min_lat: float, min_lng: float, max_lat: float, max_lng: float):
    """Generate a standard filter for issues within a bounding box."""
    return and_(
        Issue.latitude.between(min_lat, max_lat),
        Issue.longitude.between(min_lng, max_lng)
    )
