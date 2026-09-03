"""
Access proof: CHIRPS3-GEFS forecast data — discovery step.

Confirmed from CHC's own site (https://www.chc.ucsb.edu/data/chirps-gefs):
  - CHIRPS3-GEFS is now the primary product (CHIRPS2-GEFS ended July 2026)
  - Real-time data: Oct 2020-present (covers our Aug 2022 event window)
  - Historical reforecast: 2000-2019
  - Files identified by "c3g"/"CHIRPS3-GEFS" in filenames, GeoTIFF format
  - Filenames DO separate forecast issue date from lead time (confirmed —
    this was the critical open question)

We do NOT guess the exact file path pattern here — instead this script
lists what's actually on the public data server for our date range, so
you confirm the real structure before hardcoding anything. This IS the
Phase 1 "access proof" step, not a shortcut around it.
"""

import requests
from datetime import datetime, timedelta
from config import EVENT_START

# CHC's public data server — browse this directly in a browser too:
BASE_URL = "https://data.chc.ucsb.edu/products/EWX/data/forecasts/"

print(f"Browsing: {BASE_URL}")
print("(If this specific path 404s, browse from https://data.chc.ucsb.edu/"
      "products/ manually in a browser and look for the CHIRPS3-GEFS "
      "folder — CHC sometimes restructures paths between versions.)\n")

try:
    resp = requests.get(BASE_URL, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        # crude listing — just show lines that look like folder/file links
        lines = [l for l in resp.text.splitlines() if "href=" in l.lower()]
        print(f"Found {len(lines)} linked entries. First 20:")
        for line in lines[:20]:
            print(" ", line.strip()[:120])
    else:
        print("Non-200 response — confirm the correct base path manually "
              "at https://data.chc.ucsb.edu/products/ in a browser.")
except requests.RequestException as e:
    print(f"Request failed: {e}")
    print("Confirm network access and the correct path manually in a browser.")

print(f"\nTarget event date to locate once path is confirmed: {EVENT_START}")
print("Once you find a real file URL for this date in a browser, paste it "
      "back and we'll finish this script to actually download + inspect it.")
