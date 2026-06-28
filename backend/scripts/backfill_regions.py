import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.region import Region
from app.services.geo_service import fetch_region_geometry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_regions")

async def backfill_regions():
    logger.info("Initializing database connection for region backfill...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        # Get all regions missing a bounding box
        stmt = select(Region).where(Region.bbox_south == None)
        res = await db.execute(stmt)
        regions = list(res.scalars().all())

        if not regions:
            logger.info("No regions found that require backfilling.")
            return

        logger.info(f"Found {len(regions)} regions to backfill. Fetching geometries from Nominatim...")

        for region in regions:
            # For districts, get parent state name for better query accuracy
            parent_name = None
            if region.parent_region_id:
                parent_stmt = select(Region.name).where(Region.id == region.parent_region_id)
                parent_res = await db.execute(parent_stmt)
                parent_name = parent_res.scalar()

            logger.info(f"Fetching geometry for: {region.name} (type: {region.type}, parent: {parent_name})")
            
            geometry = await fetch_region_geometry(region.name, parent_name)
            if geometry:
                region.bbox_south = geometry["bbox"]["south"]
                region.bbox_north = geometry["bbox"]["north"]
                region.bbox_west = geometry["bbox"]["west"]
                region.bbox_east = geometry["bbox"]["east"]
                region.boundary_geojson = geometry["geojson"]
                logger.info(f"Successfully retrieved geometry for {region.name}: bbox={geometry['bbox']}")
            else:
                logger.warning(f"Could not retrieve geometry for {region.name}")

            # Nominatim Usage Policy: 1 request per second max
            await asyncio.sleep(1.0)

        await db.commit()
        logger.info("Region backfill completed successfully!")

if __name__ == "__main__":
    asyncio.run(backfill_regions())
