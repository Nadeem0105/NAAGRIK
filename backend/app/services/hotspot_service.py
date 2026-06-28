import uuid
import logging
import json
from datetime import datetime
from collections import Counter
from typing import Optional, List
import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.issue_repo import issue_repo
from app.core.redis import cache

logger = logging.getLogger(__name__)


class HotspotService:
    async def detect_hotspots(self, db: AsyncSession, category: Optional[str] = None, days: int = 90, region_ids: Optional[list[uuid.UUID]] = None) -> list[dict]:
        """Fetch issue coordinates via repository and run DBSCAN clustering. Cached in Redis (1h TTL)."""
        region_key = ",".join(sorted([str(r) for r in region_ids])) if region_ids else "global"
        cache_key = f"map:hotspots:{category or 'all'}:{days}:{region_key}"
        
        # Read from cache
        cached_data = await cache.get(cache_key)
        if cached_data:
            try:
                return json.loads(cached_data)
            except Exception:
                pass

        # 1. Fetch coordinates via repository
        issues_coords = await issue_repo.get_coordinates_for_clustering(db, days, region_ids=region_ids)

        # Filter by category in memory if needed
        if category:
            issues_coords = [item for item in issues_coords if item["category"].lower() == category.lower()]

        if len(issues_coords) < 3:
            return []

        # 2. Extract coordinates for clustering
        coords = []
        issue_ids = []
        categories = []
        for item in issues_coords:
            lat, lng = item["lat"], item["lng"]
            if lat is not None and lng is not None:
                coords.append([lat, lng])
                issue_ids.append(str(item["id"]))
                categories.append(item["category"])

        if len(coords) < 3:
            return []

        # Convert to radians for Haversine DBSCAN
        coords_rad = np.radians(coords)
        
        # Earth's radius in kilometers
        kms_per_radian = 6371.0
        # 200 meters in radians
        epsilon = 0.2 / kms_per_radian
        min_samples = 3  # at least 3 issues to form a cluster

        # Run DBSCAN
        dbscan = DBSCAN(
            eps=epsilon,
            min_samples=min_samples,
            metric="haversine",
            algorithm="ball_tree"
        )
        dbscan.fit(coords_rad)
        labels = dbscan.labels_

        # 3. Process clusters
        unique_labels = set(labels)
        hotspots = []

        for label in unique_labels:
            if label == -1:
                # noise points
                continue

            # Get issues belonging to this cluster
            cluster_mask = (labels == label)
            cluster_coords = np.array(coords)[cluster_mask]
            
            cluster_issue_ids = [issue_ids[i] for i, mask in enumerate(cluster_mask) if mask]
            cluster_categories = [categories[i] for i, mask in enumerate(cluster_mask) if mask]

            # Calculate cluster centroid
            centroid_lat = float(np.mean(cluster_coords[:, 0]))
            centroid_lng = float(np.mean(cluster_coords[:, 1]))

            # Calculate max distance to centroid (approximate radius in meters)
            max_dist_m = 0.0
            for lat, lng in cluster_coords:
                # Haversine distance in meters
                lat1, lon1, lat2, lon2 = map(np.radians, [centroid_lat, centroid_lng, lat, lng])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
                c = 2 * np.arcsin(np.sqrt(a))
                dist_m = c * 6371.0 * 1000.0
                if dist_m > max_dist_m:
                    max_dist_m = dist_m

            # Get top category in this cluster
            top_category = Counter(cluster_categories).most_common(1)[0][0]

            hotspots.append({
                "latitude": centroid_lat,
                "longitude": centroid_lng,
                "radius_meters": round(max_dist_m, 2),
                "issue_count": len(cluster_issue_ids),
                "top_category": top_category,
                "issue_ids": cluster_issue_ids
            })

        # Sort hotspots by issue count descending
        hotspots.sort(key=lambda x: x["issue_count"], reverse=True)

        # Cache results in Redis for 1 hour (3600 seconds)
        await cache.set(cache_key, hotspots, ex=3600)

        return hotspots


# Singleton instance
hotspot_service = HotspotService()
