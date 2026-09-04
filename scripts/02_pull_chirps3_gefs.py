from pathlib import Path
import requests
import rasterio
from rasterio.mask import mask
from shapely.geometry import box
from config import BBOX

# Setup directories
base_dir = Path(__file__).resolve().parents[1]
raw_gefs_dir = base_dir / "data" / "raw" / "gefs"
raw_gefs_dir.mkdir(parents=True, exist_ok=True)

# Target sample: Run date 2022-08-15, Day 0 forecast (data.2022.0815.tif)
file_name = "data.2022.0815.tif"
url = f"https://data.chc.ucsb.edu/products/EWX/data/forecasts/CHIRPS-GEFS_precip_v12/daily_16day/2022/08/15/{file_name}"
local_path = raw_gefs_dir / file_name

print(f"Downloading sample GEFS forecast from:\n{url}")
response = requests.get(url, stream=True, timeout=60)
response.raise_for_status()

with open(local_path, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            f.write(chunk)

print(f"Saved to {local_path} ({local_path.stat().st_size / 1024:.1f} KB)\n")

# Inspect raster metadata
with rasterio.open(local_path) as src:
    print("--- Raster Metadata ---")
    print(f"CRS: {src.crs}")
    print(f"Dimensions: {src.width}x{src.height}")
    print(f"Bands: {src.count}")
    print(f"Pixel size (res): {src.res}")
    print(f"No-data value: {src.nodata}")

    # Clip to Dadu bounding box
    dadu_geom = [box(BBOX["min_lon"], BBOX["min_lat"], BBOX["max_lon"], BBOX["max_lat"]).__geo_interface__]
    out_img, out_transform = mask(src, dadu_geom, crop=True)
    valid_pixels = out_img[0][(out_img[0] != src.nodata) & (out_img[0] >= 0)]

    print("\n--- Dadu AOI Extraction ---")
    print(f"Valid clipped pixels: {valid_pixels.size}")
    if valid_pixels.size > 0:
        print(f"Mean forecast precip: {valid_pixels.mean():.2f} mm")
        print(f"Max forecast precip:  {valid_pixels.max():.2f} mm")
        print(f"Min forecast precip:  {valid_pixels.min():.2f} mm")
