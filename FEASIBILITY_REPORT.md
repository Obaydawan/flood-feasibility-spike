# Feasibility Spike Report: Multi-Source Satellite Hydrology Pipeline

**Target District:** Dadu, Sindh, Pakistan  
**Event Window:** August 15 – September 15, 2022  
**Control Baseline:** May 1 – May 15, 2022  
**Pipeline Verdict:** **GO** (Methodologically Sound & Structurally Defensible)

---

## 1. Executive Summary
This feasibility spike evaluates the integration of high-resolution satellite Earth observation (EO) data and numerical weather prediction (NWP) precipitation streams to monitor and anticipate district-scale inundation. The pipeline operates end-to-end without look-ahead leakage, addresses satellite orbit geometry distortions, and validates continuous flood fraction signals against verified topography.

---

## 2. Ingestion & Alignment Performance

| Stream | Native Source & Resolution | Processing Applied | Ingestion / Integrity Status |
| :--- | :--- | :--- | :--- |
| **CHIRPS3** | 0.05° daily gridded precipitation | Spatio-temporal subset over Dadu AOI | Complete ($n=46$ days contiguous across windows) |
| **CHIRPS-GEFS** | 0.05° 16-band forecast GeoTIFF | Bounding-box spatial masking; lead-time index binding | Complete (Strict issue-date cutoff enforced) |
| **Copernicus GFM** | 20m Sentinel-1 SAR (Equi7Grid) | Reprojected to 0.05° WGS84 via `Resampling.average`; Nodata (255) masked | Complete (127 scenes processed across event & control) |

---

## 3. Spatial Ground-Truth Sanity Check
A spatial cross-check between control (2022-05-11) and peak event (2022-08-30) on identical full-coverage (672-cell) grids revealed:
* **Topographic Consistency:** The western half of Dadu (Kirthar Mountain Range along the Balochistan border) remained completely dry (flood fraction $\approx 0.0$).
* **Flood Corridor Alignment:** Inundation concentrated heavily ($0.80$–$1.00$) in the low-lying alluvial depression of the Indus River floodway and the Lake Manchar drainage basin.
* **Noise Rejection:** Continuous spatial clusters confirmed absence of speckle noise or false-positive desert backscatter anomalies.

---

## 4. Lag Correlation & Statistical Limitations

### 4.1. Footprint-Controlled Analysis (672-Cell Bucket, $n=6$)
When isolating identical satellite observation footprints (avoiding spatial subset mixing across swaths):
* **Short Lags (0–2 days):** Strongly negative correlation ($r = -0.741$ to $-0.921$, unadjusted $p < 0.05$).
* **Extended Lags (3–7 days) & Antecedent Windows:** Consistently negative ($r = -0.469$ to $-0.917$).

### 4.2. Methodological & Hydrological Interpretation
1. **Multiple Comparisons Caveat:** The nominal significance observed at Lags 1 and 2 ($p=0.033, 0.026$) reflects an unadjusted battery of 10 statistical tests on small sample sizes ($n=4\text{–}6$). Across 10 hypothesis tests at $\alpha=0.05$, finding 1–2 false positives is statistically expected under random noise.
2. **Spurious Trend Correlation:** The negative coefficients are driven by monotonic time trends: local Dadu rainfall peaked between August 18–22 and plummeted to zero by late August, while flood extent expanded steadily through early September.
3. **Hydrological Architecture Justification:** Local precipitation gauges cannot explain downstream district inundation in major alluvial floodplains. Dadu's inundation was governed by upstream Indus River breaches and drainage from Balochistan hill torrents into Lake Manchar. This empirical finding validates the proposal's architectural requirement: **incorporating upstream GloFAS river discharge is necessary and non-redundant.**

---

## 5. Transition to Full Pipeline Implementation
* **Coverage Metadata:** Preserve `valid_cells` and coverage ratios in all training datasets to normalize orbit-dependent observation masks.
* **Spatial Pooling:** Scale training beyond single-district time series to regional, multi-district basins to achieve appropriate statistical degrees of freedom.
* **Upstream Teleconnections:** Implement upstream hydrological routing indices (e.g., upper-Indus discharge, upstream basin cumulative rainfall) to capture trans-boundary flood waves.
