# FY-4B AGRI L1 FDI – NWP Model State Paired Database

## Overview
This database contains paired observation-background records linking FY-4B AGRI L1 FDI 4KM top-of-atmosphere brightness temperatures with NOAA GFS 0.25° 3D atmospheric model states for **25 October 2026 (UTC)** over the East China domain (20°N–45°N, 100°E–135°E).

## Dataset Manifest
- **Target Date**: 2026-10-25
- **Number of Samples**: 4
- **Nominal Times**: 00:15, 01:15, 02:15, 03:15 UTC
- **NWP Model Source**: NOAA GFS 0.25° Analysis / Short-range Forecast (NOMADS)
- **Temporal Alignment**: Mean $\Delta t = 15.0$ minutes
- **Grid Dimensions**: 101 latitudes × 141 longitudes × 8 mandatory pressure levels (1000–250 hPa)

## Channels Processed
- **WV_UPPER** (NOMChannel09): 6.25 µm
- **WV_MID** (NOMChannel10): 6.95 µm
- **WV_LOWER** (NOMChannel11): 7.42 µm
- **IR_CLEAN_WINDOW** (NOMChannel13): 10.8 µm
- **IR_SPLIT_WINDOW** (NOMChannel14): 12.0 µm
- **CO2_SLICING** (NOMChannel15): 13.3 µm

## Structure of Paired NetCDF Files
- `latitude`, `longitude`, `pressure_level`, `channel_wavelength`
- `bt_mean`: Regridded cell-mean brightness temperature (K)
- `bt_subgrid_std`: Sub-grid standard deviation across native 4 km pixels (K, sub-scale variability proxy)
- `temperature`, `specific_humidity`, `u_wind`, `v_wind`, `geopotential_height`

## Provenance and Reproducibility
Generated via `FY4B_AGRI_NWP_Paired_Dataset.ipynb` using genuine FY-4B L1 HDF files and NOAA GFS operational forecasts.
