"""
Pull-and-inspect: Copernicus GFM via EODC's direct STAC API.
Public endpoint: https://stac.eodc.eu/api/v1
"""

import os
import urllib.request
from pathlib import Path
from pystac_client import Client
from config import BBOX, EVENT_START, EVENT_END, CONTROL_START, CONTROL_END

API_URL = "https://stac.eodc.eu/api/v1"
COLLECTION_ID = "GFM"
ASSET_NAMES = ["ensemble_flood_extent"]

catalog = Client.open(API_URL)

# Bounding box: [minLon, minLat, maxLon, maxLat]
aoi_bbox = [BBOX["min_lon"], BBOX["min_lat"], BBOX["max_lon"], BBOX["max_lat"]]

base_dir = Path(__file__).resolve().parents[1]

def pull_window(start_date, end_date, label):
    time_range = f"{start_date}/{end_date}"

    search = catalog.search(
        max_items=1000,
        collections=COLLECTION_ID,
        bbox=aoi_bbox,
        datetime=time_range,
    )
    items = search.item_collection()
    print(f"[{label}] Found {len(items)} GFM items for {time_range} over Dadu bbox")

    download_root = base_dir / "data" / "raw" / "gfm" / label
    for item in items:
        download_path = download_root / item.id
        download_path.mkdir(parents=True, exist_ok=True)
        for asset_name in ASSET_NAMES:
            if asset_name not in item.assets:
                continue
            asset = item.assets[asset_name]
            fpath = download_path / os.path.basename(asset.href)
            print(f"  downloading {fpath.name}...")
            urllib.request.urlretrieve(asset.href, fpath)

    return len(items)

if __name__ == "__main__":
    event_count = pull_window(EVENT_START, EVENT_END, "event")
    control_count = pull_window(CONTROL_START, CONTROL_END, "control")

    print(f"\nEvent window items: {event_count}")
    print(f"Control window items: {control_count}")
