import json

with open("boundaries.json", "r") as f:
    bounds = json.load(f)

karnataka_gj = json.dumps(bounds["Karnataka"])
tn_gj = json.dumps(bounds["Tamil Nadu"])
blr_gj = json.dumps(bounds["Bengaluru Urban"])
chennai_gj = json.dumps(bounds["Chennai"])

with open("app/main.py", "r") as f:
    content = f.read()

# Replace the fix_regions function body
new_func = f'''    @application.get("/fix-regions", tags=["Admin"])
    async def fix_regions(db: AsyncSession = Depends(get_db)):
        from sqlalchemy import text
        try:
            await db.execute(text("""
                UPDATE regions 
                SET bbox_south = 11.5, bbox_north = 18.5, bbox_west = 74.0, bbox_east = 78.5,
                    boundary_geojson = :gj
                WHERE name = 'Karnataka'
            """), {{"gj": r"""{karnataka_gj}"""}})
            
            await db.execute(text("""
                UPDATE regions 
                SET bbox_south = 12.83, bbox_north = 13.14, bbox_west = 77.46, bbox_east = 77.78,
                    boundary_geojson = :gj
                WHERE name = 'Bengaluru Urban'
            """), {{"gj": r"""{blr_gj}"""}})
            
            await db.execute(text("""
                UPDATE regions 
                SET bbox_south = 8.0, bbox_north = 13.5, bbox_west = 76.2, bbox_east = 80.3,
                    boundary_geojson = :gj
                WHERE name = 'Tamil Nadu'
            """), {{"gj": r"""{tn_gj}"""}})
            
            await db.execute(text("""
                UPDATE regions 
                SET bbox_south = 12.98, bbox_north = 13.25, bbox_west = 80.16, bbox_east = 80.33,
                    boundary_geojson = :gj
                WHERE name = 'Chennai'
            """), {{"gj": r"""{chennai_gj}"""}})
            
            await db.commit()
            return {{"status": "success", "message": "Regions updated successfully with exact GeoJSON polygons"}}
        except Exception as e:
            return {{"status": "error", "message": str(e)}}
'''

import re
# Regex to match the fix_regions method entirely
content = re.sub(r'    @application.get\("/fix-regions".*?return {"status": "error", "message": str\(e\)}', new_func, content, flags=re.DOTALL)

with open("app/main.py", "w") as f:
    f.write(content)

print("Updated app/main.py")
