import openeo
from pathlib import Path
from config import BBOX

base_dir = Path(__file__).resolve().parents[1]
raw_gfm_dir = base_dir / "data" / "raw" / "gfm"
raw_gfm_dir.mkdir(parents=True, exist_ok=True)

backend_url = "https://openeo.dataspace.copernicus.eu"
print(f"Connecting to openEO backend: {backend_url}...")
conn = openeo.connect(backend_url)

print("Checking available GFM / flood collections...")
collections = conn.list_collections()
flood_collections = [
    c["id"] for c in collections 
    if any(k in c["id"].lower() for k in ["flood", "gfm", "glofas"])
]

print("\n--- Identified Flood-Related Collections ---")
for col_id in flood_collections:
    print(f"- {col_id}")

if not flood_collections:
    print("No direct flood/GFM collection ID match found. Listing first 10 general collections:")
    for c in collections[:10]:
        print(f"- {c['id']}")
