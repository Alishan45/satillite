# FY-4A + NWP Paired Sample Database
## Kaggle Notebook — Data Assimilation Research Prototype

---

## Overview

This notebook builds a **paired sample database** linking **FY-4A AGRI satellite observations** to matching **ERA5 NWP model states**, designed as infrastructure for future satellite data assimilation research.

> **Scientific Disclaimer:** This notebook creates *paired observations*, it does **not** perform data assimilation. ERA5 reanalysis is used as an NWP surrogate — it is **not** an operational forecast.

---

## Quick Start (Kaggle)

### Step 1 — Configure credentials

In Section 2 of the notebook, update:

```python
CONFIG["cds_api_key"] = "YOUR_UID:YOUR_API_KEY"
```

Get your key at: https://cds.climate.copernicus.eu/profile  
Or add it as a **Kaggle Secret** named `CDS_API_KEY`:

```python
from kaggle_secrets import UserSecretsClient
CONFIG["cds_api_key"] = UserSecretsClient().get_secret("CDS_API_KEY")
```

### Step 2 — Run with synthetic data (no credentials needed)

The default `CONFIG["fy4a_use_synthetic"] = True` generates physically realistic synthetic data to validate the full pipeline without requiring real data access.

### Step 3 — Switch to real data

1. Register at [data.nsmc.org.cn](https://data.nsmc.org.cn) (FY-4A)
2. Upload FY-4A HDF files as a Kaggle Dataset
3. Set:
```python
CONFIG["fy4a_use_synthetic"] = False
CONFIG["fy4a_data_dir"] = "/kaggle/input/your-fy4a-dataset"
```

---

## Data Sources

| Dataset | Source | Format | Resolution | Access |
|---------|--------|--------|------------|--------|
| FY-4A AGRI L1 | NSMC (CMA) | HDF5 (.HDF) | 4 km (IR), 0.5 km (VIS) | Registration required |
| ERA5 Reanalysis | ECMWF/Copernicus CDS | NetCDF4 | 0.25° (~28 km), hourly | Free CDS API account |

---

## Prototype Region

**East China** — 20–45°N, 100–135°E

Chosen because:
- Near-nadir view for FY-4A (104.7°E)
- High atmospheric variability (monsoon, typhoons)
- Dense in-situ observational networks for future validation

---

## Notebook Structure

| Section | Description |
|---------|-------------|
| 1 | Project Overview |
| 2 | **Configuration** (edit here) |
| 3 | Install / Import Libraries |
| 4 | Data Source Information |
| 5 | Data Discovery Agent |
| 5b | Download Module (ERA5 via CDS API) |
| 6 | FY-4A Reader (HDF5 + synthetic generator) |
| 7 | NWP Reader (ERA5 NetCDF + synthetic) |
| 8 | Temporal Matching |
| 9 | Spatial Regridding |
| 10 | Geographic Cropping |
| 11 | Quality Control (satellite + NWP) |
| 12 | Create Paired Samples |
| 13 | Validate Paired Samples (plots) |
| 14 | Dataset Statistics |
| 15 | Visualizations |
| 16 | Train/Validation/Test Split |
| 17 | Save Dataset (NetCDF4 / NPZ) |
| 18 | Final QC Report |
| 19 | Example Paired Sample |
| 20 | Limitations and Scaling |

---

## Pipeline Architecture

```
FY-4A Satellite Image          ERA5 NWP State
(HDF5, geostationary,          (NetCDF4, lat-lon,
 104.7°E, ~4 km)                0.25°, hourly)
        |                              |
        |  Temporal matching           |
        |  (max 30 min diff)           |
        +----------+   +--------------+
                   |   |
              COMMON GRID
              (0.25°, 20-45N, 100-135E)
                   |   |
                   |   |
            PAIRED SAMPLE
            ┌──────────────────────┐
            │ sample_id            │
            │ satellite:           │
            │   C09 BT (WV, K)     │
            │   C12 BT (IR, K)     │
            │   C13 BT (IR, K)     │
            │ nwp:                 │
            │   T (7 levels)       │
            │   q (7 levels)       │
            │   u, v (7 levels)    │
            │   z (7 levels)       │
            │ lat, lon             │
            │ timestamps           │
            │ QC metadata          │
            └──────────────────────┘
```

---

## Output Files

```
data/
├── raw/
│   ├── fy4a/          # HDF5 input files
│   └── nwp/           # ERA5 NetCDF files
├── processed/
│   ├── satellite/
│   └── nwp/
├── paired/
│   ├── 20230715_0600_0001.nc
│   ├── 20230715_1200_0002.nc
│   └── ...
├── reports/
│   └── qc_report.json
├── plots/
│   ├── validation_20230715_0600_0001.png
│   ├── sample_gallery.png
│   └── qc_summary.png
├── paired_samples.csv       # ← Metadata manifest
└── processing_errors.csv    # ← Error log
```

---

## Paired Samples Manifest (`paired_samples.csv`)

| Column | Description |
|--------|-------------|
| `sample_id` | Unique ID (`YYYYMMDD_HHMM_NNNN`) |
| `satellite_time` | FY-4A observation timestamp (UTC) |
| `nwp_time` | ERA5 analysis timestamp (UTC) |
| `time_difference_minutes` | Temporal offset |
| `lat_min/max`, `lon_min/max` | Geographic bounds |
| `satellite_channels` | Channels included |
| `nwp_variables` | Variables included |
| `pressure_levels` | hPa levels |
| `satellite_missing_fraction` | Fraction of NaN pixels |
| `nwp_missing_fraction` | Fraction of NaN values |
| `quality_status` | VALID / INVALID |
| `split` | train / val / test |

---

## FY-4A Channels Used

| Channel | Wavelength | Product | Use in NWP |
|---------|-----------|---------|------------|
| C09 | 6.25 μm | Water Vapour BT | Mid-upper troposphere humidity |
| C12 | 10.7 μm | IR Window BT | Surface/cloud-top temperature |
| C13 | 12.0 μm | IR Split-window | SST, cloud retrieval |

All channels operate day **and night** (IR, no solar dependence).

---

## ERA5 Variables

| Variable | Short Name | Units | Pressure Levels |
|----------|-----------|-------|-----------------|
| Temperature | T | K | 1000, 925, 850, 700, 500, 300, 250 hPa |
| Specific Humidity | q | kg/kg | Same |
| U-wind | u | m/s | Same |
| V-wind | v | m/s | Same |
| Geopotential height | z/g | m | Same |

---

## Scientific Notes

### On ERA5 as NWP Surrogate
ERA5 is produced by the ECMWF 4D-Var data assimilation system, which itself assimilates satellite radiances (including potentially FY-4A from 2018 onward). For a rigorous data assimilation experiment:
- Use an **independent NWP forecast** (GFS, ECMWF HRES)
- Or use ERA5 data **before 2018** (pre-FY-4A operational period)
- Or document this limitation explicitly (as done here)

### On Spatial Regridding
Satellite data (native ~4 km) is regridded **down** to the NWP resolution (0.25°). The reverse (interpolating NWP up to satellite resolution) would artificially create high-resolution NWP information and is scientifically unjustified.

### On Calibration
Real FY-4A calibration requires reading the per-channel Look-Up Tables from the `Calibration/` group in the HDF5 file. The prototype uses a simplified linear approximation when real files are unavailable.

### On Temporal Leakage in ML
The dataset uses a **chronological split** (train/val/test in time order), not a random split. Consecutive FY-4A images are highly correlated; random splitting would cause temporal leakage.

---

## Scaling Guide

| Stage | Samples | Storage | Notes |
|-------|---------|---------|-------|
| Stage 1 | 1 | ~2 MB | Proof of concept (this notebook) |
| Stage 2 | 10–100 | ~220 MB | Kaggle free tier |
| Stage 3 | 1,000+ | ~2+ GB | Kaggle Pro or cloud VM |
| Full dataset | 10,000+ | ~22+ GB | Cloud + Zarr format |

---

## Requirements

```
cdsapi >= 0.7.7
h5py
xarray
netCDF4
scipy
pyproj
cartopy
tqdm
pandas
matplotlib
numpy
```

All installed automatically by the notebook (`pip install` cells).

---

## Citation / Attribution

If you use this pipeline in research, please cite:
- FY-4A: China Meteorological Administration (CMA), NSMC
- ERA5: Hersbach et al. (2020), https://doi.org/10.1002/qj.3803
- This notebook: Cheng Sheng

---

## License

This code is released for research use. FY-4A data is subject to NSMC terms of use. ERA5 data is subject to the Copernicus License Agreement.
