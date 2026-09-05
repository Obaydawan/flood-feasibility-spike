"""
Phase 2: Spatio-temporal alignment.

Reprojects GFM's native Equi7Grid rasters (20m) onto a common 0.05-degree WGS84
grid matching CHIRPS3 resolution using Resampling.average to compute flood fraction.
"""

import glob
import os
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject, Resampling

from config import BBOX

base_dir = Path(__file__).resolve().parents[1]
data_root = base_dir / "data" / "raw" / "gfm"
TARGET_CRS = "EPSG:4326"
TARGET_RES_DEG = 0.05  # match CHIRPS3 native resolution

DATE_PATTERN = re.compile(r"ENSEMBLE_FLOOD_(\d{8})T")


def target_grid():
    west, south, east, north = (
        BBOX["min_lon"], BBOX["min_lat"], BBOX["max_lon"], BBOX["max_lat"]
    )
    width = max(1, round((east - west) / TARGET_RES_DEG))
    height = max(1, round((north - south) / TARGET_RES_DEG))
    transform = rasterio.transform.from_bounds(west, south, east, north, width, height)
    return transform, width, height


def reproject_one(fpath, dst_transform, width, height):
    with rasterio.open(fpath) as src:
        # Mask out 255 nodata so Resampling.average only averages valid 0/1 pixels
        nodata_val = src.nodata if src.nodata is not None else 255
        dst = np.full((height, width), np.nan, dtype="float32")

        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=nodata_val,
            dst_transform=dst_transform,
            dst_crs=TARGET_CRS,
            dst_nodata=np.nan,
            resampling=Resampling.average,
        )
        return dst


def group_files_by_date(label):
    pattern = str(data_root / label / "**" / "*.tif")
    files = glob.glob(pattern, recursive=True)
    by_date = defaultdict(list)
    for f in files:
        m = DATE_PATTERN.search(os.path.basename(f))
        if m:
            by_date[m.group(1)].append(f)
    return by_date


def build_daily_series(label, dst_transform, width, height):
    by_date = group_files_by_date(label)
    rows = []
    for date_str, files in sorted(by_date.items()):
        stacks = [reproject_one(f, dst_transform, width, height) for f in files]
        
        # Max pool across same-day overlapping tiles
        with np.errstate(all='ignore'):
            stacked = np.stack(stacks)
            all_nan = np.isnan(stacked).all(axis=0)
            combined = np.nanmax(stacked, axis=0)
            combined[all_nan] = np.nan
            
            # AOI spatial mean flood fraction across valid cells
            valid_cells = combined[~np.isnan(combined)]
            mean_frac = float(np.mean(valid_cells)) if valid_cells.size > 0 else np.nan

        rows.append({
            "date": pd.to_datetime(date_str, format="%Y%m%d").strftime("%Y-%m-%d"),
            "flood_fraction": mean_frac,
            "valid_cells": int(valid_cells.size),
            "n_scenes": len(files),
        })
    return pd.DataFrame(rows).sort_values("date")


if __name__ == "__main__":
    dst_transform, width, height = target_grid()
    print(f"Target grid: {width}x{height} cells at {TARGET_RES_DEG} deg over Dadu bbox")

    print("\nProcessing EVENT window...")
    event_df = build_daily_series("event", dst_transform, width, height)

    print("Processing CONTROL window...")
    control_df = build_daily_series("control", dst_transform, width, height)

    print("\n=== EVENT WINDOW Daily Flood Fraction ===")
    print(event_df.to_string(index=False))

    print("\n=== CONTROL WINDOW Daily Flood Fraction ===")
    print(control_df.to_string(index=False))

    event_out = data_root / "event_daily_flood_fraction.csv"
    control_out = data_root / "control_daily_flood_fraction.csv"
    event_df.to_csv(event_out, index=False)
    control_df.to_csv(control_out, index=False)
    print(f"\nSaved aligned series to:\n- {event_out}\n- {control_out}")
