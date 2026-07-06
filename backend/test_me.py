import requests

res = requests.post("https://community-hero-backend-716260831034.asia-south1.run.app/auth/login", json={
    "email": "bengaluru.admin@communityhero.gov.in",
    "password": "districtpass"
})
print(res.status_code)
print(res.text)
