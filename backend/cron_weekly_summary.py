"""
Render Cron Job — Weekly Summary Email trigger.

Scheduled: every Monday at 08:00 UTC (10:00 Paris).
Calls the backend's /notifications/weekly-summary endpoint.

Usage in render.yaml:
  - type: cron
    schedule: "0 8 * * 1"
    buildCommand: pip install requests
    startCommand: python cron_weekly_summary.py
"""

import os
import sys
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "https://infinea-api.onrender.com")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")

if not ADMIN_SECRET:
    print("ERROR: ADMIN_SECRET not set — cannot trigger weekly summary")
    sys.exit(1)

url = f"{BACKEND_URL}/notifications/weekly-summary"
headers = {"X-Admin-Secret": ADMIN_SECRET}

print(f"Triggering weekly summary: POST {url}")
try:
    resp = requests.post(url, headers=headers, timeout=120)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    if resp.status_code != 200:
        sys.exit(1)
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)
