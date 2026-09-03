"""
Pull-and-inspect: CHIRPS v3 daily rainfall for Dadu district, event + control window.

Access route: Google Earth Engine — verified public dataset:
  UCSB-CHC/CHIRPS/V3/DAILY_RNL
  https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHC_CHIRPS_V3_DAILY_RNL

Why GEE instead of raw file download: no manual file-format wrangling,
free, and gives you a pandas-ready time series in a few lines. Good enough
for a feasibility spike; the real FYP pipeline may switch to direct file
ingestion from https://www.chc.ucsb.edu/data/chirps3 for full reproducibility.

SETUP (one-time, do this first):
  pip install earthengine-api pandas
  earthengine authenticate      # opens a browser, needs a free GEE account
                                 # (sign up at https://earthengine.google.com)
"""

import ee
import pandas as pd
from config import BBOX, EVENT_START, EVENT_END, CONTROL_START, CONTROL_END

ee.Initialize()  # uses your authenticated GEE credentials

REGION = ee.Geometry.Rectangle(
    [BBOX["min_lon"], BBOX["min_lat"], BBOX["max_lon"], BBOX["max_lat"]]
)


def pull_window(start_date, end_date, label):
    collection = (
        ee.ImageCollection("UCSB-CHC/CHIRPS/V3/DAILY_RNL")
        .filterDate(start_date, end_date)
        .filterBounds(REGION)
    )

    def daily_mean(image):
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=REGION, scale=5000
        )
        return image.set("date", image.date().format("YYYY-MM-dd")).set(
            "precip_mm", stats.get("precipitation")
        )

    features = collection.map(daily_mean)
    data = features.aggregate_array("date").getInfo()
    values = features.aggregate_array("precip_mm").getInfo()

    df = pd.DataFrame({"date": data, "precip_mm": values})
    df["window"] = label
    return df


if __name__ == "__main__":
    event_df = pull_window(EVENT_START, EVENT_END, "event")
    control_df = pull_window(CONTROL_START, CONTROL_END, "control")
    result = pd.concat([event_df, control_df], ignore_index=True)

    print(result.to_string(index=False))
    print(f"\nRows: {len(result)}")
    print(f"Event window mean precip_mm: {event_df['precip_mm'].mean():.2f}")
    print(f"Control window mean precip_mm: {control_df['precip_mm'].mean():.2f}")

    result.to_csv("../data/raw/chirps3/dadu_sample.csv", index=False)
    print("\nSaved to ../data/raw/chirps3/dadu_sample.csv")

    # SANITY CHECK to look for yourself, not just trust:
    # event window mean should be meaningfully HIGHER than control window
    # mean, given Dadu's confirmed flood exposure in Aug-Sep 2022.
