import ee
import pandas as pd
from pathlib import Path
from config import BBOX, EVENT_START, EVENT_END, CONTROL_START, CONTROL_END

ee.Initialize()

dadu_geom = ee.Geometry.Rectangle([
    BBOX["min_lon"], BBOX["min_lat"],
    BBOX["max_lon"], BBOX["max_lat"]
])

def extract_chirps(start, end, label):
    col = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(start, end)
        .filterBounds(dadu_geom)
        .select("precipitation")
    )
    
    def extract_mean(img):
        mean_val = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=dadu_geom,
            scale=5566,
            maxPixels=1e9
        ).get("precipitation")
        return ee.Feature(None, {
            "date": img.date().format("YYYY-MM-dd"),
            "precip_mm": mean_val,
            "window": label
        })

    features = col.map(extract_mean).getInfo()["features"]
    return [f["properties"] for f in features]

event_data = extract_chirps(EVENT_START, EVENT_END, "event")
control_data = extract_chirps(CONTROL_START, CONTROL_END, "control")

result = pd.DataFrame(event_data + control_data)
print(result)
print(f"\nRows: {len(result)}")
print(f"Event window mean precip_mm: {result[result['window']=='event']['precip_mm'].mean():.2f}")
print(f"Control window mean precip_mm: {result[result['window']=='control']['precip_mm'].mean():.2f}")

out_dir = Path(__file__).resolve().parents[1] / "data" / "raw" / "chirps3"
out_dir.mkdir(parents=True, exist_ok=True)
csv_path = out_dir / "dadu_sample.csv"
result.to_csv(csv_path, index=False)
print(f"\nSaved successfully to {csv_path}")
