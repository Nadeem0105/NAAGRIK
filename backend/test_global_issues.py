import requests
import json

res = requests.get("https://nagarik-backend-909339119086.asia-south1.run.app/issues")
issues = res.json().get("items", [])
print(f"Total Global Issues: {len(issues)}")
for i in issues:
    print(f"Title: {i.get('title')}, Region: {i.get('region_id')}")
