import requests
import time

def trigger_fix():
    print("Waiting 10 seconds for deployment...")
    time.sleep(10)
    res = requests.get("https://nagarik-backend-909339119086.asia-south1.run.app/fix-regions")
    print("Fix endpoint response:", res.status_code, res.text)

trigger_fix()
