import requests
import json

res = requests.post("https://nagarik-backend-909339119086.asia-south1.run.app/auth/login", json={
    "email": "bengaluru.admin@communityhero.gov.in",
    "password": "districtpass"
})

token = res.json().get("access_token")
if token:
    res2 = requests.get("https://nagarik-backend-909339119086.asia-south1.run.app/issues", headers={
        "Authorization": f"Bearer {token}"
    })
    issues = res2.json().get("items", [])
    print(f"Bengaluru Issues: {len(issues)}")
else:
    print("Login failed")
