import requests
import json

res = requests.post("https://nagarik-backend-909339119086.asia-south1.run.app/auth/login", json={
    "email": "bengaluru.admin@communityhero.gov.in",
    "password": "districtpass"
})

token = res.json().get("access_token")

# First get all global issues without token
res_global = requests.get("https://nagarik-backend-909339119086.asia-south1.run.app/issues")
issues = res_global.json().get("items", [])
if not issues:
    print("No issues globally?!")
    exit()

first_issue_id = issues[1]["id"]  # "Illegal road encroachment"

# Now get that specific issue WITH token
res_specific = requests.get(f"https://nagarik-backend-909339119086.asia-south1.run.app/issues/{first_issue_id}", headers={
    "Authorization": f"Bearer {token}"
})
print("Specific issue with token status:", res_specific.status_code)
if res_specific.status_code == 200:
    print("Issue region_id:", res_specific.json().get("region_id"))
else:
    print(res_specific.text)
