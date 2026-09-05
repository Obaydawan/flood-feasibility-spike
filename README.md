# flood-feasibility-spike

A small, vertical-slice prototype proving the core data pipeline for **IndusGuard** — a 48-hour district-level flood risk forecasting system for Pakistan — works end to end, before committing to the full FYP build.

**Status: ✅ Feasibility confirmed — GO.** See [`FEASIBILITY_REPORT.md`](./FEASIBILITY_REPORT.md) for full results.

---

## What this is

Rather than building the full multi-district, multi-year IndusGuard pipeline blind, this repo shrinks it down to its smallest working version: **one district, one known flood event, all 4 real data sources** — walked end to end from raw ingestion through spatial alignment to a joined feature table. If this works at tiny scale, the full system is an engineering scaling problem, not an open research question.

**Case study:** Dadu district, Sindh, Pakistan
**Event window:** Aug 15 – Sep 15, 2022 (2022 Pakistan floods)
**Control window:** May 1–15, 2022 (pre-monsoon baseline)

---

## Key findings

- All 4 target data sources (CHIRPS3, CHIRPS-GEFS, GloFAS, Copernicus GFM) are accessible with documented, reproducible pull paths
- Copernicus GFM's flood-extent labels visually and quantitatively match real Dadu topography (dry Kirthar Range, flooded Indus floodway / Manchar Lake) — no manual correction needed
- Local rainfall alone does **not** explain district-level flooding — river discharge (GloFAS, +18x during the event) and terrain type are stronger drivers, empirically justifying their inclusion in the full FYP's feature set
- A desert-terrain control district (Tharparkar) had the *highest* rainfall of all districts tested but the *lowest* flood fraction — confirming the label pipeline discriminates real inundation rather than reacting to rainfall alone

Full detail, numbers, and caveats: [`FEASIBILITY_REPORT.md`](./FEASIBILITY_REPORT.md)

---

## Repository structure

```
flood-feasibility-spike/
│
├── data/raw/                      # gitignored — re-run scripts to regenerate
│   ├── chirps3/
│   ├── gefs/
│   ├── glofas/
│   └── gfm/
│
├── scripts/
│   ├── config.py                       # locked case-study parameters (bbox, dates)
│   ├── 01_pull_chirps3.py              # historical rainfall (Google Earth Engine)
│   ├── 02_pull_chirps3_gefs.py         # forecast rainfall access-proof / discovery
│   ├── 03_pull_glofas.py               # river discharge (EWDS / cems-glofas-historical)
│   ├── 04_pull_gfm.py                  # satellite flood extent (EODC STAC API)
│   ├── 05_inspect_gfm_rasters.py       # raw pixel-level flood-fraction sanity check
│   ├── 06_spatial_alignment.py         # Equi7Grid -> 0.05° WGS84 reprojection
│   ├── 07_build_feature_table.py       # joined feature+label table, lag correlation
│   ├── 08_district_generalization_test.py  # Jacobabad/Tharparkar cross-check
│   └── README_data_sources.md          # per-source access notes and gotchas
│
├── notebooks/                     # exploratory analysis, plots
├── FEASIBILITY_REPORT.md          # full results, per-source verdicts, risk register update
└── README.md                      # this file
```

---

## Setup

```bash
python -m venv venv
source venv/bin/activate          # or venv\Scripts\activate on Windows
pip install earthengine-api cdsapi pandas geopandas requests rasterio pystac_client numpy cfgrib xarray

# Google Earth Engine (for CHIRPS3):
earthengine authenticate --auth_mode=notebook

# GloFAS (EWDS — a SEPARATE portal from the main Copernicus CDS):
# 1. Register at https://ewds.climate.copernicus.eu
# 2. Get a personal access token from https://ewds.climate.copernicus.eu/profile
# 3. Accept the cems-glofas-historical dataset's terms & conditions on its EWDS page
# 4. Configure ~/.cdsapirc:
#      url: https://ewds.climate.copernicus.eu/api
#      key: <YOUR_EWDS_TOKEN>

# Copernicus GFM (EODC STAC): no registration required, public endpoint
```

## Running the pipeline

```bash
cd scripts
python 01_pull_chirps3.py
python 03_pull_glofas.py
python 04_pull_gfm.py
python 05_inspect_gfm_rasters.py
python 06_spatial_alignment.py
python 07_build_feature_table.py
python 08_district_generalization_test.py   # optional: cross-district check
```

`02_pull_chirps3_gefs.py` is a discovery script — run it first to confirm the live file structure on CHC's data server before relying on it for downloads.

---

## Important notes / gotchas discovered during this spike

- **GloFAS moved off the main Copernicus CDS onto a separate portal (EWDS)** — a common source of silent failures if registered on the wrong site
- **GFM is not available via the `openeo.cloud` federation** (missing `eodc` component) — use EODC's direct STAC API instead
- **Dadu straddles two Equi7Grid tiles** — same-day scenes from both tiles must be max-pooled per cell, not naively averaged or dropped
- **Sentinel-1 revisit coverage is orbit-dependent and non-uniform** — expect gaps and varying spatial footprints per date; carry `valid_cells`/`n_scenes` forward as data-quality metadata, don't discard them
- **Event and control windows must never be mixed in correlation analysis** — the 3-month calendar gap between them makes any cross-window correlation meaningless

---

## Relationship to the full IndusGuard FYP

This code is not throwaway — it's the literal starting point for the full pipeline's ingestion and alignment stages. See `FEASIBILITY_REPORT.md` Section 6 for the updated risk register carried forward into the full 20-week build.
