"""
Phase 3/4: Joined feature-label table + event-window lag cross-correlation.
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import box

import sys
scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(scripts_dir))
from config import BBOX

base_dir = Path(__file__).resolve().parents[1]
data_root = base_dir / "data" / "raw"

CHIRPS_PATH = data_root / "chirps3" / "dadu_sample.csv"
GEFS_TIF_PATH = data_root / "gefs" / "data.2022.0815.tif"
GFM_EVENT_PATH = data_root / "gfm" / "event_daily_flood_fraction.csv"
GFM_CONTROL_PATH = data_root / "gfm" / "control_daily_flood_fraction.csv"


def load_chirps():
    df = pd.read_csv(CHIRPS_PATH, parse_dates=["date"])
    return df[["date", "precip_mm", "window"]]


def extract_gefs():
    """
    Extracts daily forecast precipitation from the 16-band GEFS GeoTIFF 
    issued on 2022-08-15. Band k corresponds to lead_day k.
    Target date = issue_date + lead_days.
    """
    if not GEFS_TIF_PATH.exists():
        return pd.DataFrame(columns=["date", "gefs_forecast_mm", "gefs_lead_days"])

    geom = [box(BBOX["min_lon"], BBOX["min_lat"], BBOX["max_lon"], BBOX["max_lat"])]
    issue_date = pd.to_datetime("2022-08-15")
    records = []

    with rasterio.open(GEFS_TIF_PATH) as src:
        out_image, _ = mask(src, geom, crop=True)
        # out_image shape: (bands, height, width)
        for band_idx in range(out_image.shape[0]):
            lead_day = band_idx + 1
            target_date = issue_date + pd.Timedelta(days=lead_day)
            band_data = out_image[band_idx]
            valid_vals = band_data[(band_data != src.nodata) & (~np.isnan(band_data)) & (band_data >= 0)]
            mean_val = float(np.mean(valid_vals)) if valid_vals.size > 0 else np.nan
            records.append({
                "date": target_date,
                "gefs_forecast_mm": mean_val,
                "gefs_lead_days": lead_day
            })

    return pd.DataFrame(records)


def load_gfm():
    event = pd.read_csv(GFM_EVENT_PATH, parse_dates=["date"])
    control = pd.read_csv(GFM_CONTROL_PATH, parse_dates=["date"])
    event["window"] = "event"
    control["window"] = "control"
    return pd.concat([event, control], ignore_index=True)


def build_continuous_features():
    chirps = load_chirps().sort_values(["window", "date"]).copy()

    # Hydrologic lag features computed along continuous daily dates per window
    chirps["rain_lag3"] = (
        chirps.groupby("window")["precip_mm"]
        .transform(lambda s: s.rolling(3, min_periods=1).sum())
    )
    chirps["rain_lag7"] = (
        chirps.groupby("window")["precip_mm"]
        .transform(lambda s: s.rolling(7, min_periods=1).sum())
    )

    # Pre-shift continuous rainfall for true calendar-day lag analysis
    for lag in range(1, 8):
        chirps[f"precip_lag_{lag}d"] = chirps.groupby("window")["precip_mm"].shift(lag)

    # Join GFM flood fractions
    gfm = load_gfm()
    table = chirps.merge(gfm, on=["date", "window"], how="left")

    # Join GEFS forecast stream
    gefs = extract_gefs()
    table = table.merge(gefs, on="date", how="left")

    return table


def evaluate_event_cross_correlation(table):
    """
    Evaluates physical lag correlation exclusively on the contiguous EVENT window.
    Filters to valid observations (dropping orbit passes with 0 valid cells).
    """
    event = table[table["window"] == "event"].copy()
    valid_obs = event.dropna(subset=["flood_fraction"]).copy()
    valid_obs = valid_obs[valid_obs["valid_cells"] > 0]

    print(f"\nEvaluating Event Window Hydrologic Lag Correlation (n={len(valid_obs)} observation passes)")
    print("-" * 55)

    # Correlation with cumulative antecedent precipitation
    r_lag3 = valid_obs["rain_lag3"].corr(valid_obs["flood_fraction"])
    r_lag7 = valid_obs["rain_lag7"].corr(valid_obs["flood_fraction"])
    print(f"Correlation: 3-day Antecedent Rain vs Flood Fraction: r = {r_lag3:.3f}")
    print(f"Correlation: 7-day Antecedent Rain vs Flood Fraction: r = {r_lag7:.3f}")

    print("\nCalendar Day Lag (Precipitation leading Flood Fraction):")
    lag_rows = []
    # Lag 0 (same day)
    r0 = valid_obs["precip_mm"].corr(valid_obs["flood_fraction"])
    lag_rows.append({"lag_days": 0, "r": r0})

    for lag in range(1, 8):
        col = f"precip_lag_{lag}d"
        r = valid_obs[col].corr(valid_obs["flood_fraction"])
        lag_rows.append({"lag_days": lag, "r": r})

    lag_df = pd.DataFrame(lag_rows)
    print(lag_df.to_string(index=False))

    peak_lag = lag_df.loc[lag_df["r"].idxmax()]
    print("-" * 55)
    print(f"Peak hydrologic lag: {int(peak_lag['lag_days'])} days prior (r = {peak_lag['r']:.3f})")


if __name__ == "__main__":
    feature_table = build_continuous_features()
    
    out_csv = data_root / "dadu_feature_table.csv"
    feature_table.to_csv(out_csv, index=False)
    print(f"Saved complete feature table to: {out_csv}")
    
    evaluate_event_cross_correlation(feature_table)
