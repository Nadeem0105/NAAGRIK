import requests

res = requests.post("https://nagarik-backend-909339119086.asia-south1.run.app/auth/login", json={
    "email": "bengaluru.admin@communityhero.gov.in",
    "password": "districtpass"
})
token = res.json().get("access_token")
res2 = requests.get("https://nagarik-backend-909339119086.asia-south1.run.app/auth/me", headers={
    "Authorization": f"Bearer {token}"
})
me = res2.json()
print("GeoJSON type:", type(me.get("region", {}).get("boundary_geojson")))
print("GeoJSON:", repr(me.get("region", {}).get("boundary_geojson"))[:100])
