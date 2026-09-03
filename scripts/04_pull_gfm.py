"""
Pull-and-inspect: Copernicus Global Flood Monitoring (GFM) — flood extent
for Dadu district, event vs control window.

Access route: openEO Platform — this is a VERIFIED, real code pattern,
adapted directly from openEO's own official GFM documentation, which
notably uses Pakistan's September 2022 floods as its own demo case:
https://docs.openeo.cloud/usecases/gfm/

SETUP (one-time):
  pip install openeo
  Free trial registration: https://docs.openeo.cloud/join/free_trial.html
  First run will open a browser for OIDC login (authenticate_oidc()).
"""

import openeo
from openeo.processes import mean
from config import BBOX, EVENT_START, EVENT_END, CONTROL_START, CONTROL_END

conn = openeo.connect("openeo.cloud").authenticate_oidc()

spatial_extent = {
    "west": BBOX["min_lon"],
    "east": BBOX["max_lon"],
    "south": BBOX["min_lat"],
    "north": BBOX["max_lat"],
}


def pull_window(start_date, end_date, label):
    gfm_data = conn.load_collection(
        "GFM",
        spatial_extent=spatial_extent,
        temporal_extent=[start_date, end_date],
        bands=["ensemble_flood_extent"],
    )

    # mean over time = flood FREQUENCY per pixel across the window
    # (0 = never flooded in this window, 1 = flooded every observation)
    flood_freq = gfm_data.reduce_dimension(dimension="t", reducer=mean)

    result = flood_freq.save_result(
        format="GTiff", options={"tile_grid": "wgs84-1degree"}
    )
    job = result.create_job(title=f"gfm_dadu_{label}")
    job.start_and_wait()
    job.get_results().download_files(f"../data/raw/gfm/{label}/")
    print(f"[{label}] downloaded to ../data/raw/gfm/{label}/")


if __name__ == "__main__":
    print("Pulling GFM flood extent for EVENT window...")
    pull_window(EVENT_START, EVENT_END, "event")

    print("Pulling GFM flood extent for CONTROL window...")
    pull_window(CONTROL_START, CONTROL_END, "control")

    # SANITY CHECK (do this by hand after download, in QGIS or rasterio):
    # open both GeoTIFFs — the "event" one should show meaningfully higher
    # flood-frequency values over Dadu than the "control" one.
    # If they look similar, that's your most important red flag — see
    # Phase 3 of the phase plan.
    print("\nNext: open both GeoTIFFs and compare flood-frequency values "
          "over Dadu district. Event should be visibly higher than control.")
