"""
Spike 2: Generalization (Jacobabad) and Discrimination (Tharparkar) test.
"""

from pathlib import Path
import ee
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject, Resampling
from pystac_client import Client

base_dir = Path(__file__).resolve().parents[1]
output_csv = base_dir / "data" / "raw" / "district_generalization_test.csv"

EVENT_START = "2022-08-15"
EVENT_END = "2022-09-15"

DISTRICTS = {
    "dadu":       {"min_lon": 67.0, "max_lon": 68.2, "min_lat": 25.9, "max_lat": 27.3},
    "jacobabad":  {"min_lon": 68.2, "max_lon": 69.3, "min_lat": 27.9, "max_lat": 28.5},
    "tharparkar": {"min_lon": 69.0, "max_lon": 71.1, "min_lat": 24.1, "max_lat": 25.5},
}

ee.Initialize()
STAC_API_URL = "https://stac.eodc.eu/api/v1"
catalog = Client.open(STAC_API_URL)


def pull_chirps_mean(bbox):
    region = ee.Geometry.Rectangle(
        [bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"]]
    )
    collection = (
        ee.ImageCollection("UCSB-CHC/CHIRPS/V3/DAILY_RNL")
        .filterDate(EVENT_START, EVENT_END)
        .filterBounds(region)
    )
    stats = collection.mean().reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=5000
    )
    return stats.getInfo().get("precipitation")


def pull_gfm_mean_fraction(bbox, district_name):
    aoi_bbox = [bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"]]
    search = catalog.search(
        max_items=200,
        collections="GFM",
        bbox=aoi_bbox,
        datetime=f"{EVENT_START}/{EVENT_END}",
    )
    items = search.item_collection()
    if len(items) == 0:
        return None, 0

    width = max(1, round((bbox["max_lon"] - bbox["min_lon"]) / 0.05))
    height = max(1, round((bbox["max_lat"] - bbox["min_lat"]) / 0.05))
    dst_transform = rasterio.transform.from_bounds(
        bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"], width, height
    )

    fractions = []
    for item in items:
        asset = item.assets.get("ensemble_flood_extent")
        if asset is None:
            continue
        try:
            with rasterio.open(asset.href) as src:
                nodata_val = src.nodata if src.nodata is not None else 255
                dst = np.full((height, width), np.nan, dtype="float32")
                reproject(
                    source=rasterio.band(src, 1),
                    destination=dst,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=nodata_val,
                    dst_transform=dst_transform,
                    dst_crs="EPSG:4326",
                    dst_nodata=np.nan,
                    resampling=Resampling.average,
                )
                valid = dst[~np.isnan(dst)]
                if valid.size > 0:
                    fractions.append(float(np.mean(valid)))
        except Exception as e:
            print(f"    [{district_name}] skipped one scene: {e}")

    if not fractions:
        return None, len(items)
    return float(np.mean(fractions)), len(items)


if __name__ == "__main__":
    results = []
    for name, bbox in DISTRICTS.items():
        print(f"\nProcessing {name}...")
        rain = pull_chirps_mean(bbox)
        flood_frac, n_scenes = pull_gfm_mean_fraction(bbox, name)
        results.append({
            "district": name,
            "mean_rainfall_mm": rain,
            "mean_flood_fraction": flood_frac,
            "n_gfm_scenes": n_scenes,
        })

    df = pd.DataFrame(results)
    print("\n=== Generalization + Discrimination Test Results ===")
    print(df.to_string(index=False))
    df.to_csv(output_csv, index=False)
    print(f"\nSaved results to: {output_csv}")
