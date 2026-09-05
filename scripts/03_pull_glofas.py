"""
Pull and inspect GloFAS historical river discharge for Dadu district (event vs control).
Uses the updated EWDS schema.
"""

from pathlib import Path
import cdsapi
import pandas as pd
import xarray as xr

import sys
scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(scripts_dir))
from config import BBOX, EVENT_START, EVENT_END, CONTROL_START, CONTROL_END

base_dir = Path(__file__).resolve().parents[1]
output_dir = base_dir / "data" / "raw" / "glofas"
output_dir.mkdir(parents=True, exist_ok=True)

client = cdsapi.Client()
DATASET = "cems-glofas-historical"

# GloFAS coordinate ordering: [North, West, South, East]
AREA = [BBOX["max_lat"], BBOX["min_lon"], BBOX["min_lat"], BBOX["max_lon"]]


def date_range_to_lists(start_date, end_date):
    dates = pd.date_range(start_date, end_date)
    years = sorted({str(d.year) for d in dates})
    months = sorted({f"{d.month:02d}" for d in dates})
    days = sorted({f"{d.day:02d}" for d in dates})
    return years, months, days


def pull_window(start_date, end_date, label):
    years, months, days = date_range_to_lists(start_date, end_date)

    request = {
        "system_version": ["version_4_0"],
        "hydrological_model": ["lisflood"],
        "product_type": ["consolidated"],
        "timespan": ["time_mean"],
        "variable": ["average_river_discharge_in_the_last_24_hours"],
        "year": years,
        "month": months,
        "day": days,
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": AREA,
    }

    target = output_dir / f"dadu_{label}.nc"
    print(f"\n[{label}] Requesting GloFAS discharge from EWDS ({start_date} to {end_date})...")
    client.retrieve(DATASET, request).download(str(target))
    print(f"[{label}] Successfully downloaded to {target}")
    return target


if __name__ == "__main__":
    event_file = pull_window(EVENT_START, EVENT_END, "event")
    control_file = pull_window(CONTROL_START, CONTROL_END, "control")

    print("\n=== GloFAS Hydrological Sanity Inspection ===")
    for label, fpath in [("event", event_file), ("control", control_file)]:
        try:
            ds = xr.open_dataset(fpath)
            var_name = list(ds.data_vars)[0]
            data = ds[var_name]
            mean_q = float(data.mean().values)
            max_q = float(data.max().values)
            print(f"[{label}] Var: '{var_name}' | Mean Discharge: {mean_q:.2f} m3/s | Max Discharge: {max_q:.2f} m3/s")
        except Exception as e:
            print(f"[{label}] Could not parse {fpath}: {e}")
