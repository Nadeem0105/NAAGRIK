import requests
import time

def trigger_fixes():
    print("Waiting 10 seconds for deployment...")
    time.sleep(10)
    
    print("Running migrations...")
    res_mig = requests.get("https://nagarik-backend-909339119086.asia-south1.run.app/run-migrations")
    print("Migrations response:", res_mig.status_code, res_mig.text)
    
    print("Running region GeoJSON fix...")
    res_fix = requests.get("https://nagarik-backend-909339119086.asia-south1.run.app/fix-regions")
    print("Fix response:", res_fix.status_code, res_fix.text)

trigger_fixes()
