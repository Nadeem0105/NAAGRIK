import requests
import json
import time

queries = [
    ("Karnataka", "Karnataka state, India"),
    ("Tamil Nadu", "Tamil Nadu state, India"),
    ("Bengaluru Urban", "Bengaluru Urban district, Karnataka, India"),
    ("Chennai", "Chennai district, Tamil Nadu, India")
]

results = {}

for name, query in queries:
    # polygon_threshold=0.02 significantly simplifies the geometry to a few kb
    url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&polygon_geojson=1&polygon_threshold=0.02"
    print(f"Fetching {name}...")
    headers = {"User-Agent": "CommunityHero/1.0"}
    res = requests.get(url, headers=headers)
    
    if res.status_code == 200:
        data = res.json()
        if data:
            # First result is usually best
            item = data[0]
            geojson = item.get("geojson")
            if geojson:
                # Wrap it in a Feature
                feature = {
                    "type": "Feature",
                    "properties": {"name": name},
                    "geometry": geojson
                }
                results[name] = feature
                print(f"Got GeoJSON for {name}")
    time.sleep(1.5)

with open("boundaries.json", "w") as f:
    json.dump(results, f)
print("Saved to boundaries.json")
