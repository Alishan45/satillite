# =============================================================================
# FY-4A + NWP PAIRED SAMPLE DATABASE FOR DATA ASSIMILATION RESEARCH
# =============================================================================
# Kaggle-Ready Notebook  |  Python Script Format
# Author: Cheng Sheng
#
# PURPOSE:
#   Build a paired sample database linking FY-4A satellite observations to
#   matching NWP (ERA5 reanalysis) model states, for studying how satellite
#   imagery can be assimilated into numerical weather prediction models.
#
# SCIENTIFIC DISCLAIMER:
#   This notebook creates PAIRED OBSERVATIONS for future assimilation research.
#   It does NOT perform data assimilation itself. ERA5 reanalysis is used as
#   the NWP surrogate -- it is NOT an operational forecast.
#
# NOTEBOOK STRUCTURE:
#   Section  1:  Project Overview
#   Section  2:  Configuration
#   Section  3:  Install / Import Libraries
#   Section  4:  Data Source Information
#   Section  5:  Dataset Inspection / Data Discovery Agent
#   Section  6:  FY-4A Reader
#   Section  7:  NWP (ERA5) Reader
#   Section  8:  Temporal Matching
#   Section  9:  Spatial Regridding
#   Section 10:  Geographic Cropping
#   Section 11:  Quality Control
#   Section 12:  Create Paired Samples
#   Section 13:  Validate Paired Samples
#   Section 14:  Dataset Statistics
#   Section 15:  Visualizations
#   Section 16:  Train/Validation/Test Split
#   Section 17:  Save Dataset
#   Section 18:  Final QC Report
#   Section 19:  Example Paired Sample
#   Section 20:  Limitations and Scaling
# =============================================================================


# %%
# =============================================================================
# SECTION 1: PROJECT OVERVIEW
# =============================================================================
print("=" * 70)
print("FY-4A + NWP PAIRED SAMPLE DATABASE")
print("Data Assimilation Research Prototype")
print("=" * 70)
print()
print("Stage 1: Single paired sample (proof of concept)")
print("Stage 2: 10-100 paired samples")
print("Stage 3: 1000+ samples (requires data access scaling)")
print()
print("KEY LIMITATION:")
print("  ERA5 reanalysis is used as NWP surrogate (NOT operational forecast).")
print("  See Section 20 for full limitations and scaling guidance.")
print()


# %%
# =============================================================================
# SECTION 2: CONFIGURATION
# =============================================================================
import os
import random
import numpy as np

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
os.environ["PYTHONHASHSEED"] = str(RANDOM_SEED)

# All configurable parameters live here.
# Change these to target a different region, period, or data source.
CONFIG = {
    # --- Geographic bounds (East China prototype region) ---
    # FY-4A is positioned at 104.7 deg E; this region is near nadir.
    # High atmospheric variability (monsoon, typhoon) supports research value.
    "lat_min": 20.0,
    "lat_max": 45.0,
    "lon_min": 100.0,
    "lon_max": 135.0,

    # --- Common grid resolution ---
    # 0.25 deg chosen to match ERA5 native resolution.
    # We interpolate satellite TO NWP grid, not the reverse.
    # Rationale: avoids creating artificial high-res NWP information.
    "target_resolution_deg": 0.25,

    # --- Temporal matching threshold ---
    # 30 min allows one ERA5 hourly step as tolerance.
    # Tighten to 15 min for operational NWP applications.
    "max_time_difference_minutes": 30,

# =============================================================================
# FY-4A vs FY-4B AGRI WAVELENGTH-KEYED CHANNEL MAPPING
# =============================================================================
# FY-4A: 14 channels, sub-satellite point 104.7°E (archive reference)
# FY-4B: 15 channels, sub-satellite point 105.0°E (current operational platform)
# FY-4B introduces an extra mid-lower WV band (7.42 µm), which shifts subsequent channel indices.
# Keying by physical wavelength ensures cross-satellite compatibility.
AGRI_WAVELENGTH_CHANNEL_MAP = {
    "WV_6.25": {
        "wavelength_um": 6.25,
        "FY4A": "C09",
        "FY4B": "C09",
        "name": "Upper-tropospheric water vapor",
    },
    "WV_7.0": {
        "wavelength_um": 7.00,
        "FY4A": "C10",  # 7.1 µm on 4A
        "FY4B": "C10",  # 7.0 µm on 4B
        "name": "Mid-tropospheric water vapor",
    },
    "WV_7.4": {
        "wavelength_um": 7.42,
        "FY4A": None,   # Not present on FY-4A
        "FY4B": "C11",  # Added on FY-4B
        "name": "Mid-lower tropospheric water vapor",
    },
    "IR_8.5": {
        "wavelength_um": 8.50,
        "FY4A": "C11",
        "FY4B": "C12",
        "name": "Cloud phase / SO2 / surface",
    },
    "IR_10.8": {
        "wavelength_um": 10.8,
        "FY4A": "C12",  # 10.7 µm on 4A
        "FY4B": "C13",  # 10.8 µm on 4B
        "name": "Clean infrared window",
    },
    "IR_12.0": {
        "wavelength_um": 12.0,
        "FY4A": "C13",
        "FY4B": "C14",
        "name": "Dirty / split-window",
    },
    "CO2_13.5": {
        "wavelength_um": 13.5,
        "FY4A": "C14",
        "FY4B": "C15",
        "name": "CO2 slicing (cloud-top pressure)",
    },
}

def resolve_satellite_channel(satellite: str, band_key: str) -> str:
    """Return channel code (e.g. 'C09') for a given satellite and physical band."""
    sat = satellite.upper().replace("-", "").replace("_", "")
    key = "FY4B" if "4B" in sat else "FY4A"
    mapping = AGRI_WAVELENGTH_CHANNEL_MAP.get(band_key)
    if not mapping or not mapping[key]:
        raise ValueError(f"Band '{band_key}' not available on satellite {satellite}")
    return mapping[key]

    # --- FY-4A/B channels (Wavelength-keyed) ---
    # C09: 6.25 um Water Vapour   -- mid-upper troposphere moisture
    # C12: 10.7 um IR window      -- surface/cloud-top temperature (C13 on FY-4B)
    # C13: 12.0 um IR split-window -- cloud/SST retrieval pair (C14 on FY-4B)
    # All are IR (day + night operation).
    "satellite_channels": ["C09", "C12", "C13"],

    # --- ERA5 pressure-level variables ---
    "nwp_variables": [
        "temperature",
        "specific_humidity",
        "u_component_of_wind",
        "v_component_of_wind",
        "geopotential",
    ],

    # --- ERA5 single-level variables ---
    "nwp_single_level_variables": [
        "surface_pressure",
        "2m_temperature",
        "total_precipitable_water",
    ],

    # --- Pressure levels (hPa) ---
    # Standard mandatory levels used in NWP and radiosonde networks.
    "pressure_levels": [1000, 925, 850, 700, 500, 300, 250],

    # --- Prototype date/time ---
    "prototype_date": "2024-01-05",
    "prototype_hours": ["22", "23"],

    # --- Quality control thresholds ---
    "max_satellite_missing_fraction": 0.30,
    "max_nwp_missing_fraction": 0.05,

    # --- Storage ---
    # On Kaggle: /kaggle/working is the writable directory.
    "data_dir": "/kaggle/working/data",
    "output_format": "netcdf",   # "netcdf", "zarr", or "numpy"

    # --- CDS API credentials ---
    # Copernicus CDS new-format key (UUID only, no UID prefix needed for cdsapi>=0.7).
    # On Kaggle: store this in a Secret named CDS_API_KEY instead of hard-coding:
    #   from kaggle_secrets import UserSecretsClient
    #   CONFIG["cds_api_key"] = UserSecretsClient().get_secret("CDS_API_KEY")
    # Or locally via environment variable: export CDS_API_KEY="your-key-here"
    "cds_api_url": "https://cds.climate.copernicus.eu/api",
    "cds_api_key": os.environ.get("CDS_API_KEY", "YOUR_UID:YOUR_API_KEY"),

    # --- FY-4A data ---
    # OPTION A: Kaggle dataset mounted at /kaggle/input/fy4a-agri-data
    # OPTION B: Download from NSMC (requires registration)
    # OPTION C: Synthetic data for pipeline validation (default until real files mounted)
    "fy4a_data_dir": "/kaggle/input/fy4a-agri-data",
    "fy4a_use_synthetic": False,   # Set False: using real downloaded FY-4A HDF files
    "fy4a_synthetic_seed": 42,
}

# Adapt data_dir for local (non-Kaggle) execution
if not os.path.exists("/kaggle"):
    CONFIG["data_dir"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data"
    )

print("=" * 70)
print("CONFIGURATION")
print("=" * 70)
for key, value in CONFIG.items():
    if "key" in key.lower() or "password" in key.lower():
        print(f"  {key}: {'*' * 8} (hidden)")
    else:
        print(f"  {key}: {value}")
print()

# Create directory structure
DIRS = {
    "raw_fy4a":      os.path.join(CONFIG["data_dir"], "raw", "fy4a"),
    "raw_nwp":       os.path.join(CONFIG["data_dir"], "raw", "nwp"),
    "processed_sat": os.path.join(CONFIG["data_dir"], "processed", "satellite"),
    "processed_nwp": os.path.join(CONFIG["data_dir"], "processed", "nwp"),
    "paired":        os.path.join(CONFIG["data_dir"], "paired"),
    "reports":       os.path.join(CONFIG["data_dir"], "reports"),
    "plots":         os.path.join(CONFIG["data_dir"], "plots"),
}

for name, path in DIRS.items():
    os.makedirs(path, exist_ok=True)

if not os.path.exists("/kaggle"):
    local_fy4a = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fy4a_data")
    CONFIG["fy4a_data_dir"] = local_fy4a if os.path.exists(local_fy4a) else DIRS["raw_fy4a"]

print("Directory structure created.")
for k, v in DIRS.items():
    print(f"  {k:20s}: {v}")


# %%
# =============================================================================
# SECTION 3: INSTALL / IMPORT LIBRARIES
# =============================================================================
import sys
import subprocess
import importlib
import warnings
warnings.filterwarnings("ignore")


def install_if_missing(package, import_name=None):
    """Install a package if not already importable."""
    name = import_name or package
    try:
        importlib.import_module(name)
        print(f"  [OK] {package}")
    except ImportError:
        print(f"  [INSTALLING] {package} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
        print(f"  [OK] {package} (just installed)")


print("Checking / installing required libraries ...")
print("-" * 50)

REQUIRED = [
    ("cdsapi",     "cdsapi"),
    ("h5py",       "h5py"),
    ("xarray",     "xarray"),
    ("netCDF4",    "netCDF4"),
    ("scipy",      "scipy"),
    ("pyproj",     "pyproj"),
    ("cartopy",    "cartopy"),
    ("tqdm",       "tqdm"),
    ("pandas",     "pandas"),
    ("matplotlib", "matplotlib"),
]
for pkg, imp in REQUIRED:
    install_if_missing(pkg, imp)

print("-" * 50)

import datetime
import json
import csv
import gc
import time
import hashlib
import traceback
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple, Any

import pandas as pd
import xarray as xr
import h5py
import scipy.interpolate
import scipy.ndimage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False
    print("  [WARN] cartopy unavailable; using basic matplotlib maps")

try:
    import cdsapi
    HAS_CDSAPI = True
except ImportError:
    HAS_CDSAPI = False
    print("  [WARN] cdsapi unavailable")

try:
    import pyproj
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False
    print("  [WARN] pyproj unavailable")

print()
print("=" * 70)
print("LIBRARY VERSIONS (reproducibility record)")
print("=" * 70)
print(f"  Python    : {sys.version}")
print(f"  NumPy     : {np.__version__}")
print(f"  Pandas    : {pd.__version__}")
print(f"  Xarray    : {xr.__version__}")
print(f"  Matplotlib: {matplotlib.__version__}")
try:
    print(f"  h5py      : {h5py.__version__}")
except Exception:
    pass
try:
    import scipy
    print(f"  SciPy     : {scipy.__version__}")
except Exception:
    pass


# %%
# =============================================================================
# SECTION 4: DATA SOURCE INFORMATION
# =============================================================================
"""
--- FY-4A (Fengyun-4A) ---
Operator   : CMA / NSMC (China Meteorological Administration)
Instrument : AGRI (Advanced Geostationary Radiation Imager)
Position   : 104.7 deg E geostationary
Channels   : 14 (C01-C14)
  C01: 0.47 um VIS,  0.5 km, Reflectance
  C02: 0.65 um VIS,  0.5 km, Reflectance
  C03: 0.83 um NIR,  1.0 km, Reflectance
  C04: 1.37 um SWIR, 2.0 km, Reflectance
  C05: 1.61 um SWIR, 2.0 km, Reflectance
  C06: 2.25 um SWIR, 2.0 km, Reflectance
  C07: 3.75 um MWIR, 2.0 km, BT (K)
  C08: 3.75 um MWIR, 2.0 km, BT (K)
  C09: 6.25 um WV,   4.0 km, BT (K)  <-- used in prototype
  C10: 7.10 um WV,   4.0 km, BT (K)
  C11: 8.50 um IR,   4.0 km, BT (K)
  C12: 10.7 um IR,   4.0 km, BT (K)  <-- used in prototype
  C13: 12.0 um IR,   4.0 km, BT (K)  <-- used in prototype
  C14: 13.5 um CO2,  4.0 km, BT (K)
Format     : HDF5 (.HDF)
Temporal   : Full-disk every 15 minutes
Access     : data.nsmc.org.cn (registration ~7 working days)
File name  : FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_<start>_<end>_4000M_V0001.HDF

--- ERA5 Reanalysis (NWP Surrogate) ---
Operator   : ECMWF / Copernicus Climate Change Service
Type       : REANALYSIS (4D-Var assimilation) -- NOT operational NWP forecast
Variables  : T, q, u, v, z (pressure levels); sp, t2m, tcwv (surface)
Resolution : 0.25 deg (~28 km), hourly
Format     : NetCDF4
Access     : CDS API (cdsapi), free registration
             https://cds.climate.copernicus.eu

*** SCIENTIFIC NOTE on ERA5 vs Operational NWP ***
ERA5 may have already assimilated FY-4A data (2018 onwards).
For a clean assimilation experiment, use either:
  (a) An independent NWP forecast (GFS, ECMWF HRES)
  (b) ERA5 data pre-dating FY-4A operations (before 2018)
  (c) ERA5 with the understanding that it serves as a climatological
      reference state, not a true NWP background.
This prototype documents this limitation and uses ERA5 for reproducibility.
"""

DATA_SOURCES = {
    "satellite": {
        "name": "FY-4A AGRI Level 1",
        "operator": "CMA/NSMC",
        "portal": "https://data.nsmc.org.cn",
        "format": "HDF5",
        "projection": "Geostationary NOM (104.7 E)",
        "temporal_resolution_min": 15,
        "spatial_resolution_km": {"VIS": 0.5, "NIR": 1.0, "IR": 2.0, "WV": 4.0},
        "n_channels": 14,
        "units": {"VIS/NIR/SWIR": "Reflectance [0-1]", "IR/WV": "BT [K]"},
        "access": "Registration required (international users accepted)",
    },
    "nwp": {
        "name": "ERA5 Reanalysis",
        "operator": "ECMWF/Copernicus",
        "portal": "https://cds.climate.copernicus.eu",
        "format": "NetCDF4",
        "projection": "Regular lat-lon",
        "temporal_resolution_hr": 1,
        "spatial_resolution_deg": 0.25,
        "pressure_levels_hPa": [1000, 925, 850, 700, 500, 300, 250],
        "units": {"T": "K", "q": "kg/kg", "u/v": "m/s", "z": "m2/s2", "sp": "Pa"},
        "access": "CDS API (free registration)",
        "important_note": "REANALYSIS -- not an operational NWP forecast",
    },
}

print("=" * 70)
print("SECTION 4: DATA SOURCE METADATA TABLE")
print("=" * 70)
for ds_type, ds_info in DATA_SOURCES.items():
    label = "[SATELLITE]" if ds_type == "satellite" else "[NWP SURROGATE]"
    print(f"\n{label}")
    for k, v in ds_info.items():
        print(f"  {k:35s}: {v}")
print()


# %%
# =============================================================================
# SECTION 5: DATA DISCOVERY AGENT
# =============================================================================

# Global error and processing log
AGENT_ERRORS: List[dict] = []
PROCESSING_LOG: List[dict] = []


def log_event(event: str, status: str, details: str = ""):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event": event,
        "status": status,
        "details": details,
    }
    PROCESSING_LOG.append(entry)
    print(f"  [{status:8s}] {event}: {details[:100]}")


def log_error(filepath: str, stage: str, step: str, error: str):
    AGENT_ERRORS.append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "file": filepath,
        "stage": stage,
        "step": step,
        "error": error,
    })
    print(f"  [ERROR] {stage}/{step}: {error[:120]}")


class DataDiscoveryAgent:
    """
    Orchestration agent for data discovery.

    Responsibilities:
      - Scan directories for available files
      - Extract metadata from filenames
      - Build availability tables
      - Log errors (but never silently swallow them)

    Scientific operations (reading, calibrating, interpolating) are
    delegated to the reader functions below.
    """

    def __init__(self, config: dict):
        self.config = config
        self.found_fy4a: List[dict] = []
        self.found_nwp: List[dict] = []

    def scan_fy4a(self, directory: str) -> List[dict]:
        results = []
        path = Path(directory)
        if not path.exists():
            log_error(directory, "discovery", "scan_fy4a",
                      f"Directory not found: {directory}")
            return results

        files = (list(path.glob("**/*.HDF"))
                 + list(path.glob("**/*.hdf"))
                 + list(path.glob("**/*.h5")))
        print(f"  Found {len(files)} HDF/H5 files in {directory}")

        for f in files:
            meta = self._parse_fy4a_filename(f)
            meta["filepath"] = str(f)
            meta["size_mb"] = f.stat().st_size / 1e6
            results.append(meta)

        self.found_fy4a = results
        return results

    def scan_nwp(self, directory: str) -> List[dict]:
        results = []
        path = Path(directory)
        if not path.exists():
            log_error(directory, "discovery", "scan_nwp",
                      f"Directory not found: {directory}")
            return results

        files = (list(path.glob("**/*.nc"))
                 + list(path.glob("**/*.nc4"))
                 + list(path.glob("**/*.grib")))
        print(f"  Found {len(files)} NWP files in {directory}")

        for f in files:
            results.append({
                "filename": f.name,
                "filepath": str(f),
                "size_mb": f.stat().st_size / 1e6,
                "dataset": "ERA5",
            })

        self.found_nwp = results
        return results

    @staticmethod
    def _parse_fy4a_filename(fpath: Path) -> dict:
        """
        Parse NSMC standard FY-4A filename.
        Pattern: FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_<T1>_<T2>_<RES>_V0001.HDF
        """
        fname = fpath.name
        meta = {
            "filename": fname,
            "satellite": "FY-4A",
            "instrument": "AGRI",
            "start_time": None,
            "end_time": None,
            "resolution": None,
        }
        parts = fname.split("_")
        for part in parts:
            if len(part) == 14 and part.isdigit():
                ts = datetime.datetime.strptime(part, "%Y%m%d%H%M%S")
                if meta["start_time"] is None:
                    meta["start_time"] = ts
                else:
                    meta["end_time"] = ts
            if part.endswith("M") and part[:-1].isdigit():
                meta["resolution"] = part
        return meta

    def build_availability_table(self) -> pd.DataFrame:
        rows = []
        for item in self.found_fy4a:
            rows.append({
                "dataset": "FY-4A AGRI",
                "source": "NSMC",
                "timestamp": str(item.get("start_time", "")),
                "filename": item.get("filename", ""),
                "format": "HDF5",
                "resolution": item.get("resolution", ""),
                "status": "found",
            })
        for item in self.found_nwp:
            rows.append({
                "dataset": "ERA5",
                "source": "CDS",
                "timestamp": "",
                "filename": item.get("filename", ""),
                "format": "NetCDF4",
                "resolution": "0.25deg",
                "status": "found",
            })
        return pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["dataset", "source", "timestamp", "filename",
                     "format", "resolution", "status"])

    def summary(self) -> dict:
        return {
            "fy4a_files": len(self.found_fy4a),
            "nwp_files": len(self.found_nwp),
            "errors": len(AGENT_ERRORS),
        }


print("=" * 70)
print("SECTION 5: DATA DISCOVERY AGENT")
print("=" * 70)

agent = DataDiscoveryAgent(CONFIG)
agent.scan_fy4a(CONFIG["fy4a_data_dir"])
agent.scan_nwp(DIRS["raw_nwp"])

avail_df = agent.build_availability_table()
print(f"\nDiscovery summary: {agent.summary()}")
if not avail_df.empty:
    print(avail_df.to_string(index=False))
else:
    print("No pre-existing files found.")
    print("Pipeline will use:")
    print("  - Synthetic FY-4A data (CONFIG['fy4a_use_synthetic'] = True)")
    print("  - ERA5 via CDS API (or synthetic ERA5 if key not configured)")


# %%
# =============================================================================
# SECTION 5b: DOWNLOAD / INGESTION MODULE
# =============================================================================

def check_file_valid(filepath: str, min_bytes: int = 1000) -> Tuple[bool, str]:
    p = Path(filepath)
    if not p.exists():
        return False, "does not exist"
    sz = p.stat().st_size
    if sz < min_bytes:
        return False, f"too small ({sz} bytes)"
    return True, "OK"


def download_era5_pressure_levels(
    variables: List[str],
    pressure_levels: List[int],
    year: str, month: str, day: str,
    hours: List[str],
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    output_dir: str,
    api_key: str = "",
    api_url: str = "https://cds.climate.copernicus.eu/api",
) -> Optional[str]:
    """
    Download ERA5 pressure-level data via CDS API.

    CDS 'area' convention: [North, West, South, East]
    (opposite of lat_min/lat_max convention used internally).

    Returns path to downloaded file or None.
    """
    if not HAS_CDSAPI:
        log_event("era5_pl_download", "SKIP", "cdsapi not installed")
        return None
    if not api_key or api_key in ("YOUR_UID:YOUR_API_KEY", ""):
        log_event("era5_pl_download", "SKIP", "CDS API key not configured")
        return None

    fname = (f"era5_pl_{year}{month}{day}_{''.join(hours)}_"
             f"{lat_min:.0f}N{lat_max:.0f}N_{lon_min:.0f}E{lon_max:.0f}E.nc")
    fpath = os.path.join(output_dir, fname)

    ok, reason = check_file_valid(fpath, min_bytes=10_000)
    if ok:
        log_event("era5_pl_download", "SKIP", f"Already exists: {fname}")
        return fpath

    for attempt in range(1, 4):
        try:
            log_event("era5_pl_download", "START",
                      f"Attempt {attempt}/3 -- {len(variables)} vars, "
                      f"{len(pressure_levels)} levels")
            client = cdsapi.Client(url=api_url, key=api_key, quiet=True)
            client.retrieve(
                "reanalysis-era5-pressure-levels",
                {
                    "product_type": "reanalysis",
                    "format": "netcdf",
                    "variable": variables,
                    "pressure_level": [str(p) for p in pressure_levels],
                    "year": year,
                    "month": month,
                    "day": day,
                    "time": [f"{h}:00" for h in hours],
                    # CDS area: [North, West, South, East]
                    "area": [lat_max, lon_min, lat_min, lon_max],
                },
                fpath,
            )
            log_event("era5_pl_download", "OK", f"Saved: {fname}")
            return fpath
        except Exception as exc:
            log_error(fpath, "download", "era5_pl", str(exc))
            if attempt < 3:
                time.sleep(2 ** attempt)

    return None


def download_era5_single_levels(
    variables: List[str],
    year: str, month: str, day: str,
    hours: List[str],
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    output_dir: str,
    api_key: str = "",
    api_url: str = "https://cds.climate.copernicus.eu/api",
) -> Optional[str]:
    """Download ERA5 single-level (surface) variables via CDS API."""
    if not HAS_CDSAPI:
        return None
    if not api_key or api_key in ("YOUR_UID:YOUR_API_KEY", ""):
        return None

    fname = (f"era5_sl_{year}{month}{day}_{''.join(hours)}_"
             f"{lat_min:.0f}N{lat_max:.0f}N_{lon_min:.0f}E{lon_max:.0f}E.nc")
    fpath = os.path.join(output_dir, fname)

    ok, _ = check_file_valid(fpath, min_bytes=5_000)
    if ok:
        log_event("era5_sl_download", "SKIP", f"Already exists: {fname}")
        return fpath

    for attempt in range(1, 4):
        try:
            log_event("era5_sl_download", "START",
                      f"Attempt {attempt}/3 -- {len(variables)} SL vars")
            client = cdsapi.Client(url=api_url, key=api_key, quiet=True)
            client.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "format": "netcdf",
                    "variable": variables,
                    "year": year,
                    "month": month,
                    "day": day,
                    "time": [f"{h}:00" for h in hours],
                    "area": [lat_max, lon_min, lat_min, lon_max],
                },
                fpath,
            )
            log_event("era5_sl_download", "OK", f"Saved: {fname}")
            return fpath
        except Exception as exc:
            log_error(fpath, "download", "era5_sl", str(exc))
            if attempt < 3:
                time.sleep(2 ** attempt)

    return None


# %%
# =============================================================================
# SECTION 6: FY-4A READER
# =============================================================================
"""
FY-4A AGRI HDF5 File Structure (from NSMC documentation):
  /Calibration/CALCOEFF_CHxx  -- calibration coefficients
  /Navigation/NOMCenterLat    -- pixel centre latitudes
  /Navigation/NOMCenterLon    -- pixel centre longitudes
  /Data/NOMChannelNN          -- raw DN values per channel (uint16)
  Root attributes include:
    "Observing Beginning Time"
    "Satellite SubSatellite Point LongitudeE"

Calibration summary:
  IR channels (C07-C14): DN -> radiance -> brightness temperature (K)
  VIS/NIR (C01-C06):     DN -> reflectance [0-1]

  NOTE: The reader below applies a simplified linear scaling when the
  actual LUT/coefficients are not present (synthetic mode). In production
  with real NSMC files, the Calibration group must be read.
"""

GRAVITY = 9.80665  # WMO standard gravity (m/s^2)

ERA5_VAR_MAPPING = {
    "temperature":            "t",
    "specific_humidity":      "q",
    "u_component_of_wind":    "u",
    "v_component_of_wind":    "v",
    "geopotential":           "z",
    "surface_pressure":       "sp",
    "2m_temperature":         "t2m",
    "total_precipitable_water": "tcwv",
}

ERA5_PHYSICAL_RANGES = {
    "t":    (170.0, 340.0),
    "q":    (0.0,   0.05),
    "u":    (-150.0, 150.0),
    "v":    (-150.0, 150.0),
    "z":    (-10000.0, 600000.0),
    "sp":   (40000.0, 110000.0),
    "t2m":  (180.0, 340.0),
    "tcwv": (0.0, 100.0),
}

FY4A_BT_RANGES = {
    "C09": (170.0, 310.0),
    "C12": (170.0, 340.0),
    "C13": (170.0, 340.0),
}


def inspect_hdf5_structure(filepath: str) -> dict:
    """
    Recursively inspect an HDF5 file and print its structure.
    Scientific purpose: never assume variable names -- always inspect first.
    """
    summary = {"filepath": filepath, "groups": [], "datasets": [], "attributes": {}}

    def _visitor(name, obj):
        if isinstance(obj, h5py.Group):
            summary["groups"].append(name)
        elif isinstance(obj, h5py.Dataset):
            summary["datasets"].append({
                "path": name,
                "shape": list(obj.shape),
                "dtype": str(obj.dtype),
                "attrs": {k: str(v) for k, v in obj.attrs.items()},
            })

    try:
        with h5py.File(filepath, "r") as hf:
            summary["attributes"] = {k: str(v) for k, v in hf.attrs.items()}
            hf.visititems(_visitor)

        print(f"\n{'=' * 60}")
        print(f"HDF5 STRUCTURE: {Path(filepath).name}")
        print(f"{'=' * 60}")
        print(f"Root attributes ({len(summary['attributes'])}):")
        for k, v in list(summary["attributes"].items())[:15]:
            print(f"  {k}: {v[:80]}")
        print(f"\nGroups ({len(summary['groups'])}):")
        for g in summary["groups"][:10]:
            print(f"  /{g}/")
        print(f"\nDatasets ({len(summary['datasets'])}):")
        for ds in summary["datasets"][:20]:
            print(f"  /{ds['path']}  shape={ds['shape']}  dtype={ds['dtype']}")
    except Exception as exc:
        log_error(filepath, "inspect_hdf5", "open", str(exc))

    return summary


def read_fy4a_channel(
    filepath: str,
    channel_name: str,
    calibrate: bool = True,
) -> Optional[dict]:
    """
    Read one FY-4A AGRI channel from an HDF5 file.

    Steps:
      1. Open HDF5
      2. Locate channel data (tries multiple path conventions)
      3. Extract timestamp from root attributes
      4. Handle fill values -> NaN
      5. Apply calibration (simplified linear; production needs LUT)
      6. Return structured result
    """
    channel_num = channel_name.replace("C", "").zfill(2)
    is_ir = int(channel_num) >= 7

    try:
        with h5py.File(filepath, "r") as hf:
            # Extract timestamp
            timestamp = None
            date_val = hf.attrs.get("Observing Beginning Date") or hf.attrs.get("ObservingBeginningDate")
            time_val = hf.attrs.get("Observing Beginning Time") or hf.attrs.get("ObservingBeginningTime")
            if date_val is not None and time_val is not None:
                d_str = date_val.decode("utf-8") if isinstance(date_val, bytes) else str(date_val)
                t_str = time_val.decode("utf-8") if isinstance(time_val, bytes) else str(time_val)
                try:
                    timestamp = datetime.datetime.strptime(f"{d_str.strip()} {t_str.strip().split('.')[0]}", "%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

            if timestamp is None:
                for ts_key in ["Observing Beginning Time", "ObservingBeginningTime",
                                "Start_Time", "start_time", "TIME_BEGIN"]:
                    val = hf.attrs.get(ts_key)
                    if val is not None:
                        ts_str = val.decode("utf-8") if isinstance(val, bytes) else str(val)
                        for fmt in ["%Y-%m-%d %H:%M:%S.%f",
                                     "%Y-%m-%d %H:%M:%S",
                                     "%Y%m%d%H%M%S"]:
                            try:
                                timestamp = datetime.datetime.strptime(ts_str.strip(), fmt)
                                break
                            except ValueError:
                                continue
                        if timestamp:
                            break

            # Locate channel data
            data_arr = None
            for cpath in [
                f"NOMChannel{channel_num}",
                f"Data/NOMChannel{channel_num}",
                f"NOM{channel_name}",
                f"Channel{channel_num}",
                f"DN_{channel_name}",
                channel_name,
            ]:
                if cpath in hf:
                    data_arr = hf[cpath][()]
                    break

            if data_arr is None:
                raise ValueError(f"Channel {channel_name} not found")

            # Extract geolocation arrays if present
            lat_arr = lon_arr = None
            for lp in ["Navigation/NOMCenterLat", "NOMCenterLat", "Latitude", "lat"]:
                if lp in hf:
                    lat_arr = hf[lp][()].astype(np.float32)
                    break
            for lp in ["Navigation/NOMCenterLon", "NOMCenterLon", "Longitude", "lon"]:
                if lp in hf:
                    lon_arr = hf[lp][()].astype(np.float32)
                    break

            # Calibration via CAL LUT if present, otherwise linear
            cal_key = f"CALChannel{channel_num}"
            if calibrate and is_ir and cal_key in hf:
                lut = hf[cal_key][()]
                valid_mask = (data_arr < len(lut))
                data_f = np.full(data_arr.shape, np.nan, dtype=np.float32)
                data_f[valid_mask] = lut[data_arr[valid_mask]]
                data_f[data_arr == 65535] = np.nan
                units = f"K (FY-4A AGRI {channel_name} BT)"
            elif calibrate:
                data_f = data_arr.astype(np.float32)
                if data_arr.dtype == np.uint16:
                    data_f[data_arr == 65535] = np.nan
                elif data_arr.dtype == np.uint8:
                    data_f[data_arr == 255] = np.nan
                if is_ir:
                    data_f = data_f * (330.0 - 180.0) / 65534.0 + 180.0
                    units = "K (BT, simplified calibration)"
                else:
                    data_f = data_f / 65534.0  # -> Reflectance [0, 1]
                    units = "Reflectance [0-1]"
            else:
                data_f = data_arr.astype(np.float32)
                units = "DN (uncalibrated)"

        missing_frac = float(np.isnan(data_f).mean())
        return {
            "data": data_f,
            "lat": lat_arr,
            "lon": lon_arr,
            "timestamp": timestamp,
            "channel": channel_name,
            "units": units,
            "missing_fraction": missing_frac,
            "shape": data_f.shape,
            "is_synthetic": False,
        }

    except Exception as exc:
        log_error(filepath, "read_fy4a_channel", channel_name, str(exc))
        return None


def generate_synthetic_fy4a(
    channel_name: str,
    timestamp: datetime.datetime,
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    resolution_deg: float = 0.04,
    seed: int = 42,
) -> dict:
    """
    Generate physically realistic synthetic FY-4A data.
    Used ONLY for pipeline validation when real data is unavailable.
    All outputs are clearly labelled SYNTHETIC.

    Physical basis:
      C09 (WV  6.25 um): BT 210-270 K (upper troposphere moisture)
      C12 (IR  10.7 um): BT 200-305 K (surface + cloud tops)
      C13 (IR  12.0 um): BT 200-303 K (split-window pair of C12)

    Features:
      - Realistic latitudinal gradient
      - Simulated convective cloud cold patches
      - Gaussian detector noise (~0.5 K)
      - ~3% random missing pixels
    """
    rng = np.random.default_rng(seed + abs(hash(channel_name)) % 1000)

    bt_ranges = {
        "C09": (210.0, 270.0),
        "C12": (200.0, 305.0),
        "C13": (200.0, 303.0),
    }
    t_min, t_max = bt_ranges.get(channel_name, (200.0, 310.0))

    n_lat = int((lat_max - lat_min) / resolution_deg) + 1
    n_lon = int((lon_max - lon_min) / resolution_deg) + 1
    lats = np.linspace(lat_min, lat_max, n_lat)
    lons = np.linspace(lon_min, lon_max, n_lon)
    lat_g, lon_g = np.meshgrid(lats, lons, indexing="ij")

    # Latitudinal gradient
    lat_frac = (lat_max - lat_g) / (lat_max - lat_min)
    base = t_min + lat_frac * (t_max - t_min) * 0.7

    # Large-scale pattern
    x = (lon_g - lon_min) / (lon_max - lon_min)
    y = (lat_g - lat_min) / (lat_max - lat_min)
    pattern = (10.0 * np.sin(3 * np.pi * x) * np.cos(2 * np.pi * y)
               + 5.0 * np.sin(5 * np.pi * x + 1.2) * np.sin(4 * np.pi * y))

    # Cloud patches
    cloud_cool = np.zeros((n_lat, n_lon), dtype=np.float32)
    n_clouds = rng.integers(3, 8)
    for _ in range(n_clouds):
        cy = rng.integers(n_lat // 5, 4 * n_lat // 5)
        cx = rng.integers(n_lon // 5, 4 * n_lon // 5)
        ry = rng.integers(5, 20)
        rx = int(ry * rng.uniform(1.0, 2.0))
        yr, xr = np.ogrid[-cy:n_lat - cy, -cx:n_lon - cx]
        disk = (yr ** 2 / max(ry, 1) ** 2 + xr ** 2 / max(rx, 1) ** 2) <= 1
        cool = rng.uniform(-70, -20)
        cloud_cool[disk] = cool

    noise = rng.normal(0.0, 0.5, (n_lat, n_lon)).astype(np.float32)
    data = (base + pattern + cloud_cool + noise).astype(np.float32)
    data = np.clip(data, t_min - 10, t_max + 10)

    # Missing pixels (~3 %)
    miss_mask = rng.random((n_lat, n_lon)) < 0.03
    data[miss_mask] = np.nan

    return {
        "data": data,
        "lat": lats.astype(np.float32),
        "lon": lons.astype(np.float32),
        "lat_grid": lat_g.astype(np.float32),
        "lon_grid": lon_g.astype(np.float32),
        "timestamp": timestamp,
        "channel": channel_name,
        "units": "K (Brightness Temperature) [SYNTHETIC]",
        "missing_fraction": float(np.isnan(data).mean()),
        "shape": data.shape,
        "is_synthetic": True,
    }


def load_fy4a_scene(
    source,            # str filepath OR datetime (synthetic)
    channels: List[str],
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    use_synthetic: bool = False,
    seed: int = 42,
) -> Optional[dict]:
    """
    Load a multi-channel FY-4A scene from file or generate synthetic data.

    Returns:
      scene_data: {channel: channel_dict}
      timestamp : datetime
      lat       : 1D latitude array of native grid
      lon       : 1D longitude array of native grid
      is_synthetic: bool
    """
    scene = {"scene_data": {}, "timestamp": None,
             "lat": None, "lon": None, "is_synthetic": use_synthetic}

    if use_synthetic:
        ts = source if isinstance(source, datetime.datetime) else \
             datetime.datetime(2023, 7, 15, 6, 0, 0)
        log_event("load_fy4a", "SYNTHETIC", f"Generating scene @ {ts.isoformat()}")
        for i, ch in enumerate(channels):
            ch_data = generate_synthetic_fy4a(
                ch, ts, lat_min, lat_max, lon_min, lon_max, seed=seed + i)
            scene["scene_data"][ch] = ch_data
            if scene["lat"] is None:
                scene["lat"] = ch_data["lat"]
                scene["lon"] = ch_data["lon"]
        scene["timestamp"] = ts
        return scene

    # Real file
    filepath = str(source)
    ok, reason = check_file_valid(filepath)
    if not ok:
        log_error(filepath, "load_fy4a_scene", "file_check", reason)
        return None

    # Inspect on first call
    if not getattr(load_fy4a_scene, "_inspected", False):
        inspect_hdf5_structure(filepath)
        load_fy4a_scene._inspected = True

    for ch in channels:
        ch_data = read_fy4a_channel(filepath, ch)
        if ch_data:
            scene["scene_data"][ch] = ch_data
            if scene["lat"] is None and ch_data.get("lat") is not None:
                scene["lat"] = ch_data["lat"]
                scene["lon"] = ch_data["lon"]
            if scene["timestamp"] is None:
                scene["timestamp"] = ch_data["timestamp"]

    return scene if scene["scene_data"] else None


# %%
# =============================================================================
# SECTION 7: NWP (ERA5) READER
# =============================================================================
"""
ERA5 NetCDF coordinate conventions:
  latitude  : float32, DESCENDING (90 -> -90)
  longitude : float32, 0-360 or -180/180 depending on request settings
  level     : float32, pressure in hPa
  time      : decoded datetime64 by xarray (hours since 1900-01-01)

Geopotential: ERA5 stores z in m^2/s^2.
  Geopotential height (m) = z / g   where g = 9.80665 m/s^2
  Always document this conversion.
"""


def inspect_era5_file(filepath: str) -> dict:
    """
    Inspect an ERA5 NetCDF file and print its structure.
    Scientific purpose: verify variable names, units, coordinate ranges.
    """
    summary = {}
    try:
        ds = xr.open_dataset(filepath, decode_times=True)
        print(f"\n{'=' * 60}")
        print(f"ERA5 FILE INSPECTION: {Path(filepath).name}")
        print(f"{'=' * 60}")
        print(f"Dimensions : {dict(ds.dims)}")
        if "latitude" in ds.coords:
            print(f"Latitudes  : {float(ds.latitude.min()):.2f} to "
                  f"{float(ds.latitude.max()):.2f}")
        if "longitude" in ds.coords:
            print(f"Longitudes : {float(ds.longitude.min()):.2f} to "
                  f"{float(ds.longitude.max()):.2f}")
        t_coord = "valid_time" if "valid_time" in ds.coords else ("time" if "time" in ds.coords else None)
        l_coord = "pressure_level" if "pressure_level" in ds.coords else ("level" if "level" in ds.coords else None)
        if t_coord:
            print(f"Time range : {str(ds[t_coord].values[0])} -- "
                  f"{str(ds[t_coord].values[-1])}")
        if l_coord:
            print(f"Levels(hPa): {sorted([int(l) for l in ds[l_coord].values])}")
        print(f"\nVariables:")
        for v in ds.data_vars:
            units = ds[v].attrs.get("units", "?")
            long  = ds[v].attrs.get("long_name", "")[:40]
            print(f"  {v:12s} shape={list(ds[v].shape)}  units={units}  {long}")
        ds.close()
    except Exception as exc:
        log_error(filepath, "inspect_era5", "open", str(exc))
    return summary


def read_era5_state(
    filepath: str,
    target_time: datetime.datetime,
    variables: List[str],
    pressure_levels: List[int],
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
) -> Optional[dict]:
    """
    Read ERA5 atmospheric state nearest to target_time.

    Returns:
      data             : {var_name: ndarray (levels, lat, lon)}
      timestamp        : actual ERA5 time selected
      time_diff_minutes: |target - selected| in minutes
      lat, lon         : coordinate arrays
      levels           : pressure levels used
      units            : {var: unit_string}
      missing_fraction : {var: float}
    """
    try:
        ds = xr.open_dataset(filepath, decode_times=True)

        time_coord = "valid_time" if "valid_time" in ds.coords or "valid_time" in ds.dims else "time"
        level_coord = "pressure_level" if ("pressure_level" in ds.coords or "pressure_level" in ds.dims) else ("level" if ("level" in ds.coords or "level" in ds.dims) else None)
        lat_coord = "latitude" if "latitude" in ds.coords else "lat"
        lon_coord = "longitude" if "longitude" in ds.coords else "lon"

        # Normalize longitudes to [-180, 180] if needed
        if float(ds[lon_coord].max()) > 180.0:
            new_lon = ds[lon_coord].values.copy()
            new_lon[new_lon > 180] -= 360.0
            ds = ds.assign_coords({lon_coord: new_lon}).sortby(lon_coord)

        # Select nearest time
        target_np = np.datetime64(target_time.replace(tzinfo=None))
        diffs = np.abs(ds[time_coord].values - target_np)
        idx = int(np.argmin(diffs))
        era5_ts = pd.Timestamp(ds[time_coord].values[idx]).to_pydatetime()
        time_diff_min = abs((era5_ts - target_time).total_seconds()) / 60.0

        print(f"  ERA5 time select: target={target_time.isoformat()}  "
              f"found={era5_ts.isoformat()}  diff={time_diff_min:.1f} min")

        # Crop geographic region
        lat_vals = ds[lat_coord].values
        lat_slice = slice(lat_max, lat_min) if lat_vals[0] > lat_vals[-1] else slice(lat_min, lat_max)
        lon_vals = ds[lon_coord].values
        lon_slice = slice(lon_min, lon_max) if lon_vals[0] < lon_vals[-1] else slice(lon_max, lon_min)

        ds_t = ds.isel({time_coord: idx}).sel({lat_coord: lat_slice, lon_coord: lon_slice})

        result_data = {}
        result_units = {}
        result_missing = {}
        has_levels = level_coord is not None and (level_coord in ds_t.dims or level_coord in ds_t.coords)

        for var in variables:
            sn = ERA5_VAR_MAPPING.get(var, var)
            if sn not in ds_t:
                print(f"  [WARN] {var} ({sn}) not found; skipping")
                continue

            da = ds_t[sn]
            if has_levels and level_coord in da.dims:
                avail = [int(l) for l in ds_t[level_coord].values]
                sel_levels = [l for l in pressure_levels if l in avail]
                if not sel_levels:
                    print(f"  [WARN] No matching levels for {var}")
                    continue
                da = da.sel({level_coord: sel_levels})

            vals = da.values.astype(np.float32)

            # Handle fill / missing
            for fill_attr in ["_FillValue", "missing_value"]:
                fill = da.attrs.get(fill_attr)
                if fill is not None:
                    vals[np.abs(vals - float(fill)) < 1.0] = np.nan

            # Geopotential: m^2/s^2 -> geopotential height m
            if sn == "z":
                vals = vals / GRAVITY
                units = "m (geopotential height = z/g)"
            else:
                units = da.attrs.get("units", "unknown")

            result_data[var] = vals
            result_units[var] = units
            result_missing[var] = float(np.isnan(vals).mean())

        lat_arr = ds_t[lat_coord].values.astype(np.float32)
        lon_arr = ds_t[lon_coord].values.astype(np.float32)
        if has_levels and level_coord in ds_t.coords:
            lev_arr = np.array(
                [l for l in pressure_levels
                 if l in [int(x) for x in ds_t[level_coord].values]],
                dtype=np.float32)
        else:
            lev_arr = None

        ds.close()

        print(f"  [OK] ERA5 state: {len(result_data)} vars, "
              f"lat={lat_arr.shape}, lon={lon_arr.shape}")
        return {
            "data": result_data,
            "timestamp": era5_ts,
            "time_diff_minutes": time_diff_min,
            "lat": lat_arr,
            "lon": lon_arr,
            "levels": lev_arr,
            "units": result_units,
            "missing_fraction": result_missing,
            "is_synthetic": False,
        }

    except Exception as exc:
        log_error(filepath, "read_era5_state", "read", str(exc))
        traceback.print_exc()
        return None


def generate_synthetic_era5(
    timestamp: datetime.datetime,
    variables: List[str],
    pressure_levels: List[int],
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    resolution_deg: float = 0.25,
    seed: int = 42,
) -> dict:
    """
    Generate physically realistic synthetic ERA5-like NWP state.
    Used ONLY for pipeline validation. Clearly labelled SYNTHETIC.

    Physical basis:
      Temperature: US Standard Atmosphere lapse rate (6.5 K/km)
      Humidity   : Decreases with altitude (scale height ~2 km)
      Wind       : Mid-latitude westerlies, jet at ~300 hPa
      Geopotential: Computed via hypsometric approximation
    """
    rng = np.random.default_rng(seed)
    lats = np.arange(lat_min, lat_max + resolution_deg / 2, resolution_deg)
    lons = np.arange(lon_min, lon_max + resolution_deg / 2, resolution_deg)
    n_lat, n_lon = len(lats), len(lons)
    n_lev = len(pressure_levels)
    lat_g, lon_g = np.meshgrid(lats, lons, indexing="ij")

    result_data = {}

    for var in variables:
        sn = ERA5_VAR_MAPPING.get(var, var)

        if sn == "t":
            arr = np.zeros((n_lev, n_lat, n_lon), np.float32)
            for i, p in enumerate(pressure_levels):
                z_approx = -7000.0 * np.log(p / 1013.25)
                t_surf = 300.0 - 0.4 * (lat_g - 20.0)
                arr[i] = (t_surf - 6.5e-3 * z_approx).astype(np.float32)
                arr[i] += rng.normal(0, 1.5, (n_lat, n_lon)).astype(np.float32)
            units = "K"

        elif sn == "q":
            arr = np.zeros((n_lev, n_lat, n_lon), np.float32)
            for i, p in enumerate(pressure_levels):
                q_sfc = 0.015 * np.exp(-(lat_g - 20.0) ** 2 / 200.0)
                arr[i] = np.clip(q_sfc * (p / 1000.0) ** 2.5, 0, 0.05).astype(np.float32)
            units = "kg/kg"

        elif sn == "u":
            arr = np.zeros((n_lev, n_lat, n_lon), np.float32)
            for i, p in enumerate(pressure_levels):
                jet = np.exp(-((p - 300.0) / 100.0) ** 2)
                u_base = 10.0 * jet * np.sin(np.pi * (lat_g - lat_min) /
                                               (lat_max - lat_min))
                arr[i] = u_base.astype(np.float32) + rng.normal(0, 2, (n_lat, n_lon)).astype(np.float32)
            units = "m/s"

        elif sn == "v":
            arr = rng.normal(0, 3, (n_lev, n_lat, n_lon)).astype(np.float32)
            units = "m/s"

        elif sn == "z":
            arr = np.zeros((n_lev, n_lat, n_lon), np.float32)
            for i, p in enumerate(pressure_levels):
                z_std = -7000.0 * np.log(p / 1013.25)
                arr[i] = (z_std + rng.normal(0, 10, (n_lat, n_lon))).astype(np.float32)
            units = "m (geopotential height) [SYNTHETIC]"

        else:
            arr = rng.normal(0, 1, (n_lev, n_lat, n_lon)).astype(np.float32)
            units = "unknown"

        result_data[var] = arr

    return {
        "data": result_data,
        "timestamp": timestamp,
        "time_diff_minutes": 0.0,
        "lat": lats.astype(np.float32),
        "lon": lons.astype(np.float32),
        "levels": np.array(pressure_levels, dtype=np.float32),
        "units": {v: "K/kg/kg/m/s/m" for v in variables},
        "missing_fraction": {v: 0.0 for v in variables},
        "is_synthetic": True,
    }


# %%
# =============================================================================
# SECTION 8: TEMPORAL MATCHING
# =============================================================================
"""
Temporal Matching
=================
Scientific rationale:
  NWP data is only valid at the analysis time.
  Pairing satellite observations with NWP states that differ by more than
  ~30 minutes (for synoptic-scale features) introduces representativeness error.
  Fast-evolving phenomena (convection) require tighter tolerances (~15 min).

  Every paired sample records:
    satellite_time, nwp_time, time_difference_minutes
  Samples exceeding MAX_TIME_DIFF are rejected and logged.
"""


def match_satellite_to_nwp(
    sat_timestamps: List[datetime.datetime],
    nwp_timestamps: List[datetime.datetime],
    max_diff_minutes: float,
) -> List[dict]:
    """
    Match each satellite timestamp to the nearest NWP timestamp.

    Returns list of dicts:
      sat_time        : satellite timestamp
      nwp_time        : matched NWP timestamp
      time_diff_min   : absolute time difference in minutes
      match_status    : "ACCEPTED" or "REJECTED"
      reject_reason   : reason if rejected, else ""
    """
    pairs = []

    if not nwp_timestamps:
        print("[WARN] No NWP timestamps available for matching")
        return pairs

    nwp_arr = np.array([t.timestamp() for t in nwp_timestamps])

    for sat_ts in sat_timestamps:
        sat_epoch = sat_ts.timestamp()
        nearest_idx = int(np.argmin(np.abs(nwp_arr - sat_epoch)))
        nwp_ts = nwp_timestamps[nearest_idx]
        diff_min = abs((sat_ts - nwp_ts).total_seconds()) / 60.0

        if diff_min <= max_diff_minutes:
            status = "ACCEPTED"
            reason = ""
        else:
            status = "REJECTED"
            reason = (f"time_diff={diff_min:.1f} min > "
                      f"threshold={max_diff_minutes:.1f} min")

        pairs.append({
            "sat_time": sat_ts,
            "nwp_time": nwp_ts,
            "time_diff_min": diff_min,
            "match_status": status,
            "reject_reason": reason,
        })

    accepted = sum(1 for p in pairs if p["match_status"] == "ACCEPTED")
    print(f"  Temporal matching: {len(pairs)} pairs, "
          f"{accepted} accepted, {len(pairs) - accepted} rejected")
    print(f"  Max allowed diff: {max_diff_minutes:.0f} min")
    return pairs


# %%
# =============================================================================
# SECTION 9: SPATIAL REGRIDDING
# =============================================================================
"""
Spatial Regridding
==================
Scientific rationale:
  FY-4A: Geostationary projection (NOM), native ~4 km at nadir
  ERA5 : Regular lat-lon, 0.25 deg (~28 km)

  We regrid the SATELLITE to the NWP grid (not the reverse).
  Rationale: NWP is on the coarser grid. Interpolating satellite
  data DOWN to a coarser grid is scientifically safe. The reverse
  (interpolating NWP up to satellite resolution) would artificially
  invent high-resolution atmospheric information.

  Methods by variable type:
    Continuous (BT, temperature, humidity, wind): bilinear interpolation
    Categorical masks/flags: nearest-neighbour (NOT bilinear)

  The common target grid is defined by CONFIG parameters.
"""


def build_target_grid(
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    resolution_deg: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build the common lat-lon target grid.
    Both satellite and NWP data will be regridded to this grid.

    Returns:
      target_lat : 1D array, ascending
      target_lon : 1D array, ascending
    """
    target_lat = np.arange(lat_min, lat_max + resolution_deg / 2, resolution_deg)
    target_lon = np.arange(lon_min, lon_max + resolution_deg / 2, resolution_deg)
    return target_lat.astype(np.float32), target_lon.astype(np.float32)


def reproject_satellite(
    sat_data: np.ndarray,
    sat_lat: np.ndarray,
    sat_lon: np.ndarray,
    target_lat: np.ndarray,
    target_lon: np.ndarray,
    method: str = "linear",
) -> np.ndarray:
    """
    Reproject satellite data from its native grid to the common target grid.

    Uses scipy.interpolate.RegularGridInterpolator for structured grids,
    or griddata for scattered/irregular satellite grids.

    Parameters:
      sat_data  : 2D array (n_sat_lat, n_sat_lon)
      sat_lat   : 1D lat array of satellite grid
      sat_lon   : 1D lon array of satellite grid
      target_lat: 1D lat array of common grid
      target_lon: 1D lon array of common grid
      method    : "linear" (bilinear) for continuous, "nearest" for masks

    Returns:
      2D array on (target_lat, target_lon) grid
    """
    tgt_lat_g, tgt_lon_g = np.meshgrid(target_lat, target_lon, indexing="ij")

    # Determine if satellite grid is regular
    if sat_data.ndim == 2 and sat_lat.ndim == 1 and sat_lon.ndim == 1:
        # Regular grid: use RegularGridInterpolator
        # Ensure lat is ascending for the interpolator
        if sat_lat[0] > sat_lat[-1]:
            sat_data = sat_data[::-1, :]
            sat_lat = sat_lat[::-1]
        if sat_lon[0] > sat_lon[-1]:
            sat_data = sat_data[:, ::-1]
            sat_lon = sat_lon[::-1]

        # Mask NaN before interpolation
        filled = sat_data.copy()
        nan_mask = np.isnan(filled)
        if nan_mask.any():
            # Simple fill with local mean for interpolation (NaNs restored after)
            from scipy.ndimage import generic_filter
            filled_temp = filled.copy()
            filled_temp[nan_mask] = 0.0
            count = (~nan_mask).astype(float)
            filled[nan_mask] = scipy.ndimage.uniform_filter(
                filled_temp, size=5)[nan_mask]

        interp_fn = scipy.interpolate.RegularGridInterpolator(
            (sat_lat, sat_lon), filled,
            method=method,
            bounds_error=False,
            fill_value=np.nan,
        )
        pts = np.column_stack([tgt_lat_g.ravel(), tgt_lon_g.ravel()])
        result = interp_fn(pts).reshape(tgt_lat_g.shape).astype(np.float32)

    else:
        # Irregular grid: use griddata (slower but handles geostationary proj.)
        if sat_lat.ndim == 1 and sat_lon.ndim == 1:
            sat_lat_2d, sat_lon_2d = np.meshgrid(sat_lat, sat_lon, indexing="ij")
        else:
            sat_lat_2d, sat_lon_2d = sat_lat, sat_lon

        valid = ~np.isnan(sat_data.ravel())
        if valid.sum() < 10:
            return np.full(tgt_lat_g.shape, np.nan, dtype=np.float32)

        result = scipy.interpolate.griddata(
            points=np.column_stack([sat_lat_2d.ravel()[valid],
                                     sat_lon_2d.ravel()[valid]]),
            values=sat_data.ravel()[valid],
            xi=(tgt_lat_g, tgt_lon_g),
            method=method,
            fill_value=np.nan,
        ).astype(np.float32)

    return result


def regrid_nwp(
    nwp_data: np.ndarray,
    nwp_lat: np.ndarray,
    nwp_lon: np.ndarray,
    target_lat: np.ndarray,
    target_lon: np.ndarray,
    method: str = "linear",
) -> np.ndarray:
    """
    Regrid NWP data to the common target grid.

    NWP data may be 2D (lat, lon) or 3D (levels, lat, lon).
    ERA5 lat is typically descending; we handle both orders.

    Scientific note: This is spatial interpolation within the NWP grid.
    It does NOT create new atmospheric information. At 0.25 deg target
    matching the ERA5 native resolution, this is essentially a pass-through.
    """
    if nwp_data.ndim == 2:
        return reproject_satellite(nwp_data, nwp_lat, nwp_lon,
                                    target_lat, target_lon, method)
    elif nwp_data.ndim == 3:
        # Process level by level
        n_levels = nwp_data.shape[0]
        n_lat_t = len(target_lat)
        n_lon_t = len(target_lon)
        result = np.full((n_levels, n_lat_t, n_lon_t), np.nan, dtype=np.float32)
        for lev_i in range(n_levels):
            result[lev_i] = reproject_satellite(
                nwp_data[lev_i], nwp_lat, nwp_lon,
                target_lat, target_lon, method)
        return result
    else:
        raise ValueError(f"Unexpected NWP data shape: {nwp_data.shape}")


# %%
# =============================================================================
# SECTION 10: GEOGRAPHIC CROPPING
# =============================================================================
"""
Geographic Cropping
===================
Scientific rationale:
  Processing full FY-4A full-disk images (~11000x11000 pixels at 4km) is
  unnecessary and memory-prohibitive in Kaggle. We crop to the target region
  before all subsequent processing.

  Prototype region: 20-45N, 100-135E (East China)
  This region contains:
    - Dense observational networks for future validation
    - High variability (monsoon, frontal systems, typhoons)
    - FY-4A near-nadir imagery (minimal geometric distortion)

  The crop is applied to BOTH datasets before regridding.
"""


def crop_satellite_to_region(
    data: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Crop a 2D satellite array and its coordinate arrays to the target region.
    Handles both 1D coordinate arrays (regular grid) and 2D (irregular).

    Returns: cropped_data, cropped_lat, cropped_lon
    """
    if lat.ndim == 1 and lon.ndim == 1:
        lat_mask = (lat >= lat_min) & (lat <= lat_max)
        lon_mask = (lon >= lon_min) & (lon <= lon_max)
        cropped = data[np.ix_(lat_mask, lon_mask)]
        return cropped, lat[lat_mask], lon[lon_mask]

    elif lat.ndim == 2 and lon.ndim == 2:
        # Irregular grid (geostationary native)
        region_mask = ((lat >= lat_min) & (lat <= lat_max) &
                       (lon >= lon_min) & (lon <= lon_max))
        rows = np.where(region_mask.any(axis=1))[0]
        cols = np.where(region_mask.any(axis=0))[0]
        if len(rows) == 0 or len(cols) == 0:
            return data, lat, lon
        r0, r1 = rows[0], rows[-1] + 1
        c0, c1 = cols[0], cols[-1] + 1
        return data[r0:r1, c0:c1], lat[r0:r1, c0:c1], lon[r0:r1, c0:c1]

    return data, lat, lon


# %%
# =============================================================================
# SECTION 11: QUALITY CONTROL
# =============================================================================
"""
Quality Control
===============
Satellite QC (FY-4A):
  1. Missing pixel fraction  -- reject if > threshold
  2. Physical range check    -- flag pixels outside expected BT range
  3. Timestamp validity      -- reject if timestamp is missing/implausible
  4. Geographic coverage     -- verify data covers target region

NWP QC (ERA5):
  1. NaN fraction            -- reject if > threshold
  2. Physical range check    -- flag values outside known atmospheric ranges
  3. Missing variables       -- warn if requested variable absent
  4. Missing pressure levels -- warn if levels absent

QC results are stored in the metadata manifest.
We NEVER silently clip or fill values without documenting it.
"""


def qc_satellite(
    scene: dict,
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    max_missing: float,
    regridded_data: Optional[Dict[str, np.ndarray]] = None,
) -> dict:
    """
    Run quality control on an FY-4A scene.

    Returns a QC report dict:
      overall_status: "PASS" or "FAIL"
      checks: list of individual check results
      missing_fraction_per_channel: dict
      physical_range_violations: dict
    """
    qc = {
        "overall_status": "PASS",
        "checks": [],
        "missing_fraction_per_channel": {},
        "physical_range_violations": {},
        "reject_reasons": [],
    }

    if not scene or not scene.get("scene_data"):
        qc["overall_status"] = "FAIL"
        qc["reject_reasons"].append("empty_scene")
        return qc

    # Timestamp check
    ts = scene.get("timestamp")
    if ts is None:
        qc["checks"].append({"check": "timestamp", "status": "WARN",
                              "detail": "timestamp missing"})
    else:
        # Plausibility: FY-4A operational 2017-2025
        if ts.year < 2017 or ts.year > 2026:
            qc["checks"].append({"check": "timestamp", "status": "FAIL",
                                  "detail": f"implausible year {ts.year}"})
            qc["overall_status"] = "FAIL"
            qc["reject_reasons"].append("implausible_timestamp")
        else:
            qc["checks"].append({"check": "timestamp", "status": "PASS",
                                  "detail": ts.isoformat()})

    # Per-channel checks (evaluated on target domain if regridded_data provided)
    for ch, ch_data in scene["scene_data"].items():
        arr = regridded_data[ch] if (regridded_data is not None and ch in regridded_data) else ch_data["data"]
        missing_frac = float(np.isnan(arr).mean())
        qc["missing_fraction_per_channel"][ch] = missing_frac

        # Missing fraction check
        if missing_frac > max_missing:
            qc["checks"].append({"check": f"missing_{ch}", "status": "FAIL",
                                  "detail": f"{missing_frac:.3f} > {max_missing}"})
            qc["overall_status"] = "FAIL"
            qc["reject_reasons"].append(f"too_many_missing_{ch}")
        else:
            qc["checks"].append({"check": f"missing_{ch}", "status": "PASS",
                                  "detail": f"{missing_frac:.3f}"})

        # Physical range check (IR channels only, after calibration)
        if ch in FY4A_BT_RANGES:
            bt_min, bt_max = FY4A_BT_RANGES[ch]
            valid = arr[~np.isnan(arr)]
            if len(valid) > 0:
                pct_below = float((valid < bt_min).mean())
                pct_above = float((valid > bt_max).mean())
                if pct_below > 0.01 or pct_above > 0.01:
                    qc["physical_range_violations"][ch] = {
                        "pct_below_min": pct_below,
                        "pct_above_max": pct_above,
                    }
                    qc["checks"].append({
                        "check": f"phys_range_{ch}", "status": "WARN",
                        "detail": (f"{pct_below*100:.1f}% below {bt_min}K, "
                                   f"{pct_above*100:.1f}% above {bt_max}K")
                    })
                else:
                    qc["checks"].append({"check": f"phys_range_{ch}",
                                          "status": "PASS", "detail": "OK"})

    return qc


def qc_nwp(
    nwp_state: dict,
    max_missing: float,
    required_variables: List[str],
    required_levels: List[int],
) -> dict:
    """
    Run quality control on an ERA5 NWP state.

    Returns a QC report dict.
    """
    qc = {
        "overall_status": "PASS",
        "checks": [],
        "missing_fraction_per_variable": {},
        "physical_range_violations": {},
        "reject_reasons": [],
    }

    if not nwp_state or not nwp_state.get("data"):
        qc["overall_status"] = "FAIL"
        qc["reject_reasons"].append("empty_nwp_state")
        return qc

    # Check all required variables are present
    for var in required_variables:
        if var not in nwp_state["data"]:
            qc["checks"].append({"check": f"var_{var}", "status": "WARN",
                                  "detail": "missing variable"})
        else:
            arr = nwp_state["data"][var]
            miss = float(np.isnan(arr).mean())
            qc["missing_fraction_per_variable"][var] = miss

            if miss > max_missing:
                qc["checks"].append({"check": f"missing_{var}", "status": "FAIL",
                                      "detail": f"{miss:.4f} > {max_missing}"})
                qc["overall_status"] = "FAIL"
                qc["reject_reasons"].append(f"too_many_missing_{var}")
            else:
                qc["checks"].append({"check": f"missing_{var}", "status": "PASS",
                                      "detail": f"{miss:.4f}"})

            # Physical range check
            sn = ERA5_VAR_MAPPING.get(var, var)
            if sn in ERA5_PHYSICAL_RANGES:
                v_min, v_max = ERA5_PHYSICAL_RANGES[sn]
                valid = arr[~np.isnan(arr)]
                if len(valid) > 0:
                    pct_out = float(((valid < v_min) | (valid > v_max)).mean())
                    if pct_out > 0.001:
                        qc["physical_range_violations"][var] = pct_out
                        qc["checks"].append({
                            "check": f"phys_range_{var}", "status": "WARN",
                            "detail": f"{pct_out*100:.2f}% out of [{v_min},{v_max}]"
                        })
                    else:
                        qc["checks"].append({"check": f"phys_range_{var}",
                                              "status": "PASS", "detail": "OK"})

    # Check pressure levels
    actual_levels = set()
    if nwp_state.get("levels") is not None:
        actual_levels = set(int(l) for l in nwp_state["levels"])
    missing_levels = [l for l in required_levels if l not in actual_levels]
    if missing_levels:
        qc["checks"].append({"check": "pressure_levels", "status": "WARN",
                              "detail": f"missing levels: {missing_levels}"})
    else:
        qc["checks"].append({"check": "pressure_levels", "status": "PASS",
                              "detail": str(sorted(actual_levels))})

    return qc


# %%
# =============================================================================
# SECTION 12: CREATE PAIRED SAMPLES
# =============================================================================

@dataclass
class PairedSample:
    """
    Represents one paired satellite + NWP sample.

    Fields are documented here for schema clarity.
    Every field must be set explicitly; nothing should be inferred.
    """
    sample_id: str

    # Satellite
    sat_channels: Dict[str, np.ndarray]   # {channel: 2D array on common grid}
    sat_channel_units: Dict[str, str]
    sat_time: datetime.datetime
    sat_missing_fraction: Dict[str, float]
    sat_is_synthetic: bool

    # NWP
    nwp_variables: Dict[str, np.ndarray]  # {var: array (levels, lat, lon) or (lat, lon)}
    nwp_variable_units: Dict[str, str]
    nwp_time: datetime.datetime
    nwp_missing_fraction: Dict[str, float]
    nwp_pressure_levels: Optional[np.ndarray]
    nwp_is_synthetic: bool

    # Common grid
    target_lat: np.ndarray
    target_lon: np.ndarray

    # Temporal
    time_difference_minutes: float

    # Region
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float

    # Quality
    sat_qc: dict
    nwp_qc: dict
    overall_valid: bool

    # Metadata
    notes: str = ""


def create_paired_sample(
    sample_id: str,
    fy4a_source,             # datetime (synthetic) or filepath (real)
    era5_filepath: Optional[str],
    target_time: datetime.datetime,
    config: dict,
    use_synthetic_sat: bool = True,
    use_synthetic_nwp: bool = True,
) -> Optional[PairedSample]:
    """
    Create one paired FY-4A + ERA5 sample.

    Pipeline:
      1. Load FY-4A scene (or synthetic)
      2. Load ERA5 state (or synthetic)
      3. Temporal matching check
      4. Build common grid
      5. Crop satellite to region
      6. Reproject satellite to common grid
      7. Regrid NWP to common grid
      8. Satellite QC
      9. NWP QC
      10. Assemble PairedSample
    """
    print(f"\n{'=' * 60}")
    print(f"Creating paired sample: {sample_id}")
    print(f"Target time: {target_time.isoformat()}")
    print(f"{'=' * 60}")

    lat_min = config["lat_min"]
    lat_max = config["lat_max"]
    lon_min = config["lon_min"]
    lon_max = config["lon_max"]
    channels = config["satellite_channels"]
    variables = config["nwp_variables"]
    pressure_levels = config["pressure_levels"]
    res = config["target_resolution_deg"]
    max_tdiff = config["max_time_difference_minutes"]

    # 1. Load satellite
    print("\n[Step 1] Loading FY-4A scene ...")
    sat_scene = load_fy4a_scene(
        fy4a_source, channels, lat_min, lat_max, lon_min, lon_max,
        use_synthetic=use_synthetic_sat, seed=config["fy4a_synthetic_seed"],
    )
    if sat_scene is None:
        log_error(str(fy4a_source), "create_pair", "load_satellite",
                  "Failed to load FY-4A scene")
        return None

    # 2. Load NWP
    print("\n[Step 2] Loading ERA5 state ...")
    if use_synthetic_nwp:
        nwp_state = generate_synthetic_era5(
            target_time, variables, pressure_levels,
            lat_min, lat_max, lon_min, lon_max,
            seed=config["fy4a_synthetic_seed"])
    elif era5_filepath and check_file_valid(era5_filepath)[0]:
        nwp_state = read_era5_state(
            era5_filepath, target_time, variables, pressure_levels,
            lat_min, lat_max, lon_min, lon_max)
        if nwp_state is not None and nwp_state.get("time_diff_minutes", 0) > max_tdiff:
            print(f"  [FALLBACK] Real ERA5 time offset ({nwp_state['time_diff_minutes']:.1f} min > {max_tdiff} min). Using synthetic NWP.")
            nwp_state = generate_synthetic_era5(
                target_time, variables, pressure_levels,
                lat_min, lat_max, lon_min, lon_max,
                seed=config["fy4a_synthetic_seed"])
    else:
        log_error(str(era5_filepath), "create_pair", "load_nwp",
                  "ERA5 file not available")
        return None

    if nwp_state is None:
        return None

    # 3. Temporal matching check
    print("\n[Step 3] Temporal matching ...")
    sat_time = sat_scene["timestamp"] or target_time
    nwp_time = nwp_state["timestamp"]
    time_diff_min = abs((sat_time - nwp_time).total_seconds()) / 60.0
    print(f"  Sat time : {sat_time.isoformat()}")
    print(f"  NWP time : {nwp_time.isoformat()}")
    print(f"  Diff     : {time_diff_min:.1f} min (threshold: {max_tdiff} min)")

    if time_diff_min > max_tdiff and not use_synthetic_nwp:
        log_error(sample_id, "create_pair", "temporal_match",
                  f"Time diff {time_diff_min:.1f} min > {max_tdiff} min")
        return None

    # 4. Build common grid
    print("\n[Step 4] Building common grid ...")
    target_lat, target_lon = build_target_grid(lat_min, lat_max, lon_min, lon_max, res)
    print(f"  Grid: {len(target_lat)} lat x {len(target_lon)} lon "
          f"@ {res} deg resolution")

    # 5 & 6. Crop and reproject satellite channels
    print("\n[Step 5-6] Reprojecting satellite channels ...")
    sat_regridded = {}
    sat_units = {}
    sat_missing = {}

    for ch, ch_data in sat_scene["scene_data"].items():
        arr = ch_data["data"]
        sat_lat = sat_scene["lat"]
        sat_lon = sat_scene["lon"]

        if sat_lat is None:
            # FY-4A AGRI REGC Geostationary projection mapping directly to target grid
            p = pyproj.Proj(proj="geos", h=35786000.0, lon_0=104.7, sweep="y")
            tgt_lat_g, tgt_lon_g = np.meshgrid(target_lat, target_lon, indexing="ij")
            tgt_x, tgt_y = p(tgt_lon_g, tgt_lat_g)
            dx = 4004.7
            cols = (tgt_x / dx) + 1373.5
            lines = 1373.5 - (tgt_y / dx) - 175
            coords = np.array([lines.ravel(), cols.ravel()])
            arr_rg = scipy.ndimage.map_coordinates(arr, coords, order=1, cval=np.nan).reshape(tgt_lat_g.shape).astype(np.float32)
            arr_crop = arr
        else:
            # Crop
            arr_crop, lat_crop, lon_crop = crop_satellite_to_region(
                arr, sat_lat, sat_lon, lat_min, lat_max, lon_min, lon_max)

            if arr_crop.size == 0:
                print(f"  [WARN] Channel {ch}: empty after crop")
                continue

            # Reproject to common grid (bilinear for BT -- continuous variable)
            arr_rg = reproject_satellite(
                arr_crop, lat_crop, lon_crop, target_lat, target_lon, method="linear")

        sat_regridded[ch] = arr_rg
        sat_units[ch] = ch_data["units"]
        sat_missing[ch] = float(np.isnan(arr_rg).mean())
        print(f"  {ch}: cropped={arr_crop.shape} -> regridded={arr_rg.shape}  "
              f"missing={sat_missing[ch]:.3f}")

    # 7. Regrid NWP
    print("\n[Step 7] Regridding NWP variables ...")
    nwp_regridded = {}
    nwp_units = {}
    nwp_missing = {}

    for var, arr in nwp_state["data"].items():
        # NWP lat may be descending; normalize
        nwp_lat = nwp_state["lat"]
        nwp_lon = nwp_state["lon"]
        if nwp_lat[0] > nwp_lat[-1]:
            nwp_lat = nwp_lat[::-1]
            arr = arr[..., ::-1, :] if arr.ndim == 3 else arr[::-1, :]

        arr_rg = regrid_nwp(arr, nwp_lat, nwp_lon, target_lat, target_lon,
                             method="linear")
        nwp_regridded[var] = arr_rg
        nwp_units[var] = nwp_state["units"].get(var, "unknown")
        nwp_missing[var] = float(np.isnan(arr_rg).mean())
        print(f"  {var}: native={arr.shape} -> regridded={arr_rg.shape}  "
              f"missing={nwp_missing[var]:.4f}")

    # 8. Satellite QC
    print("\n[Step 8] Satellite QC ...")
    sat_qc = qc_satellite(
        sat_scene, lat_min, lat_max, lon_min, lon_max,
        config["max_satellite_missing_fraction"],
        regridded_data=sat_regridded)
    print(f"  Sat QC: {sat_qc['overall_status']}")

    # 9. NWP QC
    print("\n[Step 9] NWP QC ...")
    nwp_qc = qc_nwp(
        nwp_state,
        config["max_nwp_missing_fraction"],
        variables,
        pressure_levels)
    print(f"  NWP QC: {nwp_qc['overall_status']}")

    overall_valid = (sat_qc["overall_status"] == "PASS" and
                     nwp_qc["overall_status"] == "PASS")

    # 10. Assemble sample
    notes = []
    if sat_scene.get("is_synthetic"):
        notes.append("SYNTHETIC_SATELLITE")
    if nwp_state.get("is_synthetic"):
        notes.append("SYNTHETIC_NWP")
    if notes:
        notes.append("DO_NOT_USE_FOR_SCIENTIFIC_CONCLUSIONS")

    sample = PairedSample(
        sample_id=sample_id,
        sat_channels=sat_regridded,
        sat_channel_units=sat_units,
        sat_time=sat_time,
        sat_missing_fraction=sat_missing,
        sat_is_synthetic=bool(sat_scene.get("is_synthetic", False)),
        nwp_variables=nwp_regridded,
        nwp_variable_units=nwp_units,
        nwp_time=nwp_time,
        nwp_missing_fraction=nwp_missing,
        nwp_pressure_levels=nwp_state.get("levels"),
        nwp_is_synthetic=bool(nwp_state.get("is_synthetic", False)),
        target_lat=target_lat,
        target_lon=target_lon,
        time_difference_minutes=time_diff_min,
        lat_min=lat_min, lat_max=lat_max,
        lon_min=lon_min, lon_max=lon_max,
        sat_qc=sat_qc,
        nwp_qc=nwp_qc,
        overall_valid=overall_valid,
        notes=" | ".join(notes),
    )

    status = "VALID" if overall_valid else "INVALID"
    print(f"\n[OK] Sample {sample_id}: {status}")
    return sample


# %%
# =============================================================================
# SECTION 13: VALIDATE PAIRED SAMPLES (visualize + inspect)
# =============================================================================

def validate_paired_sample(sample: PairedSample, save_dir: Optional[str] = None):
    """
    Produce validation plots and print metadata for a paired sample.

    Plots generated:
      1. FY-4A channel(s) on common grid
      2. ERA5 temperature at 850 hPa
      3. ERA5 specific humidity at 850 hPa
      4. ERA5 wind speed at 850 hPa
      5. Side-by-side comparison (satellite vs NWP)
    """
    print(f"\n{'=' * 70}")
    print(f"VALIDATING SAMPLE: {sample.sample_id}")
    print(f"{'=' * 70}")
    print(f"  Satellite time : {sample.sat_time.isoformat()}")
    print(f"  NWP time       : {sample.nwp_time.isoformat()}")
    print(f"  Time diff      : {sample.time_difference_minutes:.1f} min")
    print(f"  Region         : {sample.lat_min}N-{sample.lat_max}N, "
          f"{sample.lon_min}E-{sample.lon_max}E")
    print(f"  Grid shape     : {len(sample.target_lat)} x {len(sample.target_lon)}")
    print(f"  SAT synthetic  : {sample.sat_is_synthetic}")
    print(f"  NWP synthetic  : {sample.nwp_is_synthetic}")
    print(f"  Overall valid  : {sample.overall_valid}")
    print(f"  Notes          : {sample.notes}")
    print()
    print("  Satellite missing fractions:")
    for ch, mf in sample.sat_missing_fraction.items():
        print(f"    {ch}: {mf:.4f}")
    print("  NWP missing fractions:")
    for var, mf in sample.nwp_missing_fraction.items():
        print(f"    {var}: {mf:.6f}")
    print()

    # Build figure
    tgt_lat = sample.target_lat
    tgt_lon = sample.target_lon

    # Determine subplot count
    n_sat_ch = len(sample.sat_channels)
    n_nwp_panels = 3  # T @ 850, q @ 850, wind speed @ 850
    n_cols = 3
    n_rows = max(n_sat_ch, n_nwp_panels)

    fig, axes = plt.subplots(n_rows, n_cols,
                              figsize=(18, 5 * n_rows),
                              squeeze=False)
    fig.suptitle(
        f"Paired Sample: {sample.sample_id}\n"
        f"SAT {sample.sat_time.strftime('%Y-%m-%d %H:%M UTC')}  |  "
        f"NWP {sample.nwp_time.strftime('%Y-%m-%d %H:%M UTC')}  |  "
        f"Diff: {sample.time_difference_minutes:.1f} min\n"
        f"{'*** SYNTHETIC DATA -- PIPELINE VALIDATION ONLY ***' if sample.sat_is_synthetic else ''}",
        fontsize=13, fontweight="bold",
    )

    # --- Column 1: Satellite channels ---
    for row, (ch, arr) in enumerate(sample.sat_channels.items()):
        if row >= n_rows:
            break
        ax = axes[row][0]
        vmin = np.nanpercentile(arr, 2)
        vmax = np.nanpercentile(arr, 98)
        im = ax.pcolormesh(tgt_lon, tgt_lat, arr,
                           cmap="gray_r", vmin=vmin, vmax=vmax, shading="auto")
        plt.colorbar(im, ax=ax, label=sample.sat_channel_units.get(ch, ""))
        ax.set_title(f"FY-4A {ch}\n{sample.sat_time.strftime('%H:%M UTC')}")
        ax.set_xlabel("Longitude (E)")
        ax.set_ylabel("Latitude (N)")
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.3)
    for row in range(len(sample.sat_channels), n_rows):
        axes[row][0].axis("off")

    # --- Column 2: NWP Temperature @ 850 hPa ---
    t_var = "temperature"
    lev_850_idx = None
    if sample.nwp_pressure_levels is not None:
        levs = [int(l) for l in sample.nwp_pressure_levels]
        if 850 in levs:
            lev_850_idx = levs.index(850)

    for row in range(n_rows):
        ax = axes[row][1]
        if row == 0 and t_var in sample.nwp_variables:
            arr = sample.nwp_variables[t_var]
            data2d = arr[lev_850_idx] if (arr.ndim == 3 and lev_850_idx is not None) \
                else arr if arr.ndim == 2 else arr[0]
            vmin = np.nanpercentile(data2d, 2)
            vmax = np.nanpercentile(data2d, 98)
            im = ax.pcolormesh(tgt_lon, tgt_lat, data2d,
                               cmap="RdYlBu_r", vmin=vmin, vmax=vmax, shading="auto")
            plt.colorbar(im, ax=ax, label="K")
            lev_label = f" @ {sample.nwp_pressure_levels[lev_850_idx]:.0f} hPa" \
                if lev_850_idx is not None else ""
            ax.set_title(f"ERA5 Temperature{lev_label}\n"
                         f"{sample.nwp_time.strftime('%H:%M UTC')}")
            ax.set_xlabel("Longitude (E)")
            ax.set_ylabel("Latitude (N)")
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True, alpha=0.3)
        elif row == 1 and "specific_humidity" in sample.nwp_variables:
            arr = sample.nwp_variables["specific_humidity"]
            data2d = arr[lev_850_idx] if (arr.ndim == 3 and lev_850_idx is not None) \
                else arr if arr.ndim == 2 else arr[0]
            data2d_g = data2d * 1000.0   # kg/kg -> g/kg for readability
            im = ax.pcolormesh(tgt_lon, tgt_lat, data2d_g,
                               cmap="YlGnBu", shading="auto")
            plt.colorbar(im, ax=ax, label="g/kg")
            ax.set_title(f"ERA5 Specific Humidity @ 850 hPa\n"
                         f"{sample.nwp_time.strftime('%H:%M UTC')}")
            ax.set_xlabel("Longitude (E)")
            ax.set_ylabel("Latitude (N)")
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True, alpha=0.3)
        elif row == 2 and ("u_component_of_wind" in sample.nwp_variables and
                            "v_component_of_wind" in sample.nwp_variables):
            u_arr = sample.nwp_variables["u_component_of_wind"]
            v_arr = sample.nwp_variables["v_component_of_wind"]
            u2d = u_arr[lev_850_idx] if (u_arr.ndim == 3 and lev_850_idx is not None) \
                else u_arr if u_arr.ndim == 2 else u_arr[0]
            v2d = v_arr[lev_850_idx] if (v_arr.ndim == 3 and lev_850_idx is not None) \
                else v_arr if v_arr.ndim == 2 else v_arr[0]
            wspd = np.sqrt(u2d ** 2 + v2d ** 2)
            im = ax.pcolormesh(tgt_lon, tgt_lat, wspd,
                               cmap="viridis", shading="auto")
            plt.colorbar(im, ax=ax, label="m/s")
            # Quiver (subsample for clarity)
            step = max(1, len(tgt_lat) // 15)
            Q = ax.quiver(tgt_lon[::step], tgt_lat[::step],
                          u2d[::step, ::step], v2d[::step, ::step],
                          scale=200, width=0.003, alpha=0.7, color="white")
            ax.set_title(f"ERA5 Wind Speed @ 850 hPa\n"
                         f"{sample.nwp_time.strftime('%H:%M UTC')}")
            ax.set_xlabel("Longitude (E)")
            ax.set_ylabel("Latitude (N)")
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True, alpha=0.3)
        else:
            ax.axis("off")

    # --- Column 3: Geographic coverage + QC ---
    ax_cov = axes[0][2]
    ax_cov.set_facecolor("#d0e8f0")
    ax_cov.add_patch(Rectangle(
        (sample.lon_min, sample.lat_min),
        sample.lon_max - sample.lon_min,
        sample.lat_max - sample.lat_min,
        linewidth=2, edgecolor="navy", facecolor="steelblue", alpha=0.4,
        label="Prototype region"))
    ax_cov.set_xlim(60, 160)
    ax_cov.set_ylim(-10, 60)
    ax_cov.set_xlabel("Longitude (E)")
    ax_cov.set_ylabel("Latitude (N)")
    ax_cov.set_title("Geographic Coverage")
    ax_cov.legend(loc="lower right")
    ax_cov.grid(True, alpha=0.3)
    ax_cov.annotate("FY-4A nadir\n(104.7 E)", xy=(104.7, 0),
                    xytext=(104.7, -8), fontsize=8,
                    arrowprops=dict(arrowstyle="->", color="red"),
                    ha="center", color="red")

    # QC summary text
    ax_qc = axes[1][2]
    ax_qc.axis("off")
    qc_lines = [
        "QUALITY CONTROL SUMMARY",
        "=" * 30,
        f"Sample ID: {sample.sample_id}",
        "",
        f"SAT QC: {sample.sat_qc['overall_status']}",
    ]
    for ch, mf in sample.sat_missing_fraction.items():
        qc_lines.append(f"  {ch} missing: {mf*100:.1f}%")
    qc_lines += [
        "",
        f"NWP QC: {sample.nwp_qc['overall_status']}",
    ]
    for var, mf in sample.nwp_missing_fraction.items():
        qc_lines.append(f"  {var}: {mf*100:.2f}%")
    qc_lines += [
        "",
        f"Time diff: {sample.time_difference_minutes:.1f} min",
        f"Overall: {'VALID' if sample.overall_valid else 'INVALID'}",
    ]
    if sample.notes:
        qc_lines.append("")
        qc_lines.append("NOTES:")
        for note in sample.notes.split(" | "):
            qc_lines.append(f"  {note}")

    ax_qc.text(0.05, 0.95, "\n".join(qc_lines),
               transform=ax_qc.transAxes, fontsize=9,
               verticalalignment="top", fontfamily="monospace",
               bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

    # Missing data histogram
    ax_hist = axes[2][2] if n_rows > 2 else axes[0][2]
    ax_hist.axis("off")
    if n_rows > 2:
        ax_hist.axis("on")
        ch_names = list(sample.sat_missing_fraction.keys())
        miss_vals = [sample.sat_missing_fraction[c] * 100 for c in ch_names]
        colors = ["#e74c3c" if v > 20 else "#27ae60" for v in miss_vals]
        ax_hist.bar(ch_names, miss_vals, color=colors)
        ax_hist.axhline(y=30, color="red", linestyle="--", label="30% threshold")
        ax_hist.set_xlabel("Channel")
        ax_hist.set_ylabel("Missing (%)")
        ax_hist.set_title("Satellite Missing Data")
        ax_hist.legend()
        ax_hist.grid(True, alpha=0.3, axis="y")

    # Remaining panels
    for row in range(3, n_rows):
        for col in range(3):
            axes[row][col].axis("off")

    plt.tight_layout()

    if save_dir:
        fpath = os.path.join(save_dir, f"validation_{sample.sample_id}.png")
        plt.savefig(fpath, dpi=100, bbox_inches="tight")
        print(f"  Validation plot saved: {fpath}")

    plt.show()
    plt.close(fig)
    gc.collect()


# %%
# =============================================================================
# RUN STAGE 1: SINGLE PROOF-OF-CONCEPT SAMPLE
# =============================================================================

print("\n" + "=" * 70)
print("STAGE 1: SINGLE PAIRED SAMPLE (PROOF OF CONCEPT)")
print("=" * 70)

# Determine prototype source and time
if not CONFIG["fy4a_use_synthetic"] and agent.found_fy4a:
    fy4a_item = agent.found_fy4a[0]
    prototype_time = fy4a_item["start_time"]
    fy4a_source = fy4a_item["filepath"]
    print(f"Using REAL FY-4A file: {Path(fy4a_source).name}")
else:
    prototype_time = datetime.datetime(2023, 7, 15, 6, 0, 0)
    fy4a_source = prototype_time
    print(f"Using SYNTHETIC FY-4A data at {prototype_time}")

# Attempt CDS download if key is configured
era5_pl_file = None
if (CONFIG["cds_api_key"] != "YOUR_UID:YOUR_API_KEY" and HAS_CDSAPI):
    # Dynamically use the date from the satellite file we found (or synthetic prototype)
    y = f"{prototype_time.year:04d}"
    m = f"{prototype_time.month:02d}"
    d = f"{prototype_time.day:02d}"
    
    era5_pl_file = download_era5_pressure_levels(
        variables=CONFIG["nwp_variables"],
        pressure_levels=CONFIG["pressure_levels"],
        year=y, month=m, day=d,
        hours=CONFIG["prototype_hours"],
        lat_min=CONFIG["lat_min"], lat_max=CONFIG["lat_max"],
        lon_min=CONFIG["lon_min"], lon_max=CONFIG["lon_max"],
        output_dir=DIRS["raw_nwp"],
        api_key=CONFIG["cds_api_key"],
        api_url=CONFIG["cds_api_url"],
    )

# Determine whether to use synthetic NWP
use_synthetic_nwp = (era5_pl_file is None)
if use_synthetic_nwp:
    print("\n[INFO] Using SYNTHETIC ERA5 data (CDS API key not configured).")
    print("       To use real ERA5: set CONFIG['cds_api_key'] and rerun.")

# Inspect ERA5 file if downloaded
if era5_pl_file and check_file_valid(era5_pl_file)[0]:
    inspect_era5_file(era5_pl_file)

# Create the first paired sample
sample_001 = create_paired_sample(
    sample_id=prototype_time.strftime("%Y%m%d_%H%M_0001"),
    fy4a_source=fy4a_source,
    era5_filepath=era5_pl_file,
    target_time=prototype_time,
    config=CONFIG,
    use_synthetic_sat=CONFIG["fy4a_use_synthetic"],
    use_synthetic_nwp=use_synthetic_nwp,
)

if sample_001 is not None:
    print("\n[Stage 1] Sample created successfully.")
    validate_paired_sample(sample_001, save_dir=DIRS["plots"])
else:
    print("\n[Stage 1] FAILED to create sample. Check errors above.")


# %%
# =============================================================================
# STAGE 2: BUILD 10-100 PAIRED SAMPLES
# =============================================================================

print("\n" + "=" * 70)
print("STAGE 2: BUILDING MULTIPLE PAIRED SAMPLES (10-100)")
print("=" * 70)
print("Scientific rationale: We sample multiple times on the prototype day")
print("to demonstrate temporal coverage and assess variability across samples.")
print("Each sample uses an independent random seed so synthetic patterns differ.")
print()

# Build processing queue
stage2_tasks = []
if not CONFIG["fy4a_use_synthetic"] and agent.found_fy4a:
    print(f"Using {len(agent.found_fy4a)} real FY-4A files found by DataDiscoveryAgent.")
    for item in agent.found_fy4a[:20]:  # Cap at 20 for Kaggle memory limits
        stage2_tasks.append((item["start_time"], item["filepath"]))
else:
    print("Generating synthetic timestamps...")
    # 4 observations per day at 0000, 0600, 1200, 1800 UTC
    stage2_timestamps = [
        datetime.datetime(2023, 7, 15, h, 0, 0)
        for h in [0, 6, 12, 18]
    ]
    # Add additional days for more samples
    for day in [16, 17, 18, 19, 20]:
        for h in [0, 6, 12, 18]:
            stage2_timestamps.append(datetime.datetime(2023, 7, day, h, 0, 0))
    
    for ts in stage2_timestamps[:20]:
        stage2_tasks.append((ts, ts))

print(f"Generating {len(stage2_tasks)} paired samples ...")

all_samples: List[PairedSample] = []
if sample_001 is not None:
    all_samples.append(sample_001)

for i, (ts, f_source) in enumerate(stage2_tasks):
    # Skip if we already did this one in Stage 1
    if ts == prototype_time:
        continue

    sid = ts.strftime(f"%Y%m%d_%H%M_{i+2:04d}")
    print(f"\n[{i+1}/{len(stage2_tasks)}] {sid} @ {ts.isoformat()}")

    # Vary seed per sample so synthetic patterns are different
    sample_config = dict(CONFIG)
    sample_config["fy4a_synthetic_seed"] = CONFIG["fy4a_synthetic_seed"] + i

    try:
        smp = create_paired_sample(
            sample_id=sid,
            fy4a_source=f_source,
            era5_filepath=era5_pl_file,
            target_time=ts,
            config=sample_config,
            use_synthetic_sat=CONFIG["fy4a_use_synthetic"],
            use_synthetic_nwp=use_synthetic_nwp,
        )
        if smp is not None:
            all_samples.append(smp)

        # Explicit memory cleanup
        del smp
        gc.collect()

    except Exception as exc:
        log_error(sid, "stage2", "create_pair", str(exc))
        traceback.print_exc()

print(f"\n[Stage 2] Created {len(all_samples)} valid samples.")


# %%
# =============================================================================
# SECTION 14: DATASET STATISTICS
# =============================================================================

print("\n" + "=" * 70)
print("SECTION 14: DATASET STATISTICS")
print("=" * 70)

def compute_dataset_statistics(samples: List[PairedSample]) -> pd.DataFrame:
    rows = []
    for s in samples:
        row = {
            "sample_id": s.sample_id,
            "sat_time": s.sat_time,
            "nwp_time": s.nwp_time,
            "time_diff_min": s.time_difference_minutes,
            "overall_valid": s.overall_valid,
            "sat_is_synthetic": s.sat_is_synthetic,
            "nwp_is_synthetic": s.nwp_is_synthetic,
        }
        for ch, mf in s.sat_missing_fraction.items():
            row[f"sat_miss_{ch}"] = mf
        for var, mf in s.nwp_missing_fraction.items():
            row[f"nwp_miss_{var}"] = mf
        rows.append(row)
    return pd.DataFrame(rows)


stats_df = compute_dataset_statistics(all_samples)

print(f"\nTotal samples created  : {len(all_samples)}")
print(f"Valid samples          : {stats_df['overall_valid'].sum()}")
print(f"Invalid samples        : {(~stats_df['overall_valid']).sum()}")
print(f"Synthetic satellite    : {stats_df['sat_is_synthetic'].sum()}")
print(f"Synthetic NWP          : {stats_df['nwp_is_synthetic'].sum()}")
print(f"\nTime difference (min):")
print(f"  Mean  : {stats_df['time_diff_min'].mean():.2f}")
print(f"  Max   : {stats_df['time_diff_min'].max():.2f}")
print(f"  Min   : {stats_df['time_diff_min'].min():.2f}")

# Per-channel satellite missing statistics
sat_miss_cols = [c for c in stats_df.columns if c.startswith("sat_miss_")]
if sat_miss_cols:
    print(f"\nMean satellite missing fraction by channel:")
    for col in sat_miss_cols:
        ch = col.replace("sat_miss_", "")
        print(f"  {ch}: {stats_df[col].mean():.4f}")

nwp_miss_cols = [c for c in stats_df.columns if c.startswith("nwp_miss_")]
if nwp_miss_cols:
    print(f"\nMean NWP missing fraction by variable:")
    for col in nwp_miss_cols:
        var = col.replace("nwp_miss_", "")
        print(f"  {var}: {stats_df[col].mean():.6f}")


# %%
# =============================================================================
# SECTION 15: VISUALIZATIONS
# =============================================================================

print("\n" + "=" * 70)
print("SECTION 15: VISUALIZATIONS")
print("=" * 70)


def plot_time_difference_distribution(samples: List[PairedSample], save_dir: str):
    """
    Plot distribution of time differences between satellite and NWP.
    Scientific purpose: verify that temporal matching is within tolerance.
    """
    diffs = [s.time_difference_minutes for s in samples]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(diffs, bins=20, color="steelblue", edgecolor="white", alpha=0.8)
    ax.axvline(CONFIG["max_time_difference_minutes"], color="red",
               linestyle="--", label=f"Max allowed ({CONFIG['max_time_difference_minutes']} min)")
    ax.set_xlabel("Time Difference (minutes)")
    ax.set_ylabel("Number of Samples")
    ax.set_title("Temporal Matching: Satellite vs NWP Time Difference Distribution")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fpath = os.path.join(save_dir, "time_diff_distribution.png")
    plt.savefig(fpath, dpi=100, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"  Saved: {fpath}")


def plot_missing_data_summary(samples: List[PairedSample], save_dir: str):
    """
    Plot missing data fractions across all samples per channel.
    Scientific purpose: identify systematic data gaps.
    """
    channels = CONFIG["satellite_channels"]
    n_ch = len(channels)

    fig, axes = plt.subplots(1, n_ch, figsize=(5 * n_ch, 5), sharey=True)
    if n_ch == 1:
        axes = [axes]

    for i, ch in enumerate(channels):
        miss_vals = [s.sat_missing_fraction.get(ch, np.nan) * 100 for s in samples]
        axes[i].hist(miss_vals, bins=15, color="coral", edgecolor="white", alpha=0.8)
        axes[i].axvline(CONFIG["max_satellite_missing_fraction"] * 100,
                         color="red", linestyle="--", label="Rejection threshold")
        axes[i].set_title(f"FY-4A {ch}")
        axes[i].set_xlabel("Missing (%)")
        if i == 0:
            axes[i].set_ylabel("Samples")
        axes[i].legend(fontsize=8)
        axes[i].grid(True, alpha=0.3)

    fig.suptitle("Satellite Missing Data Distribution", fontsize=13)
    plt.tight_layout()
    fpath = os.path.join(save_dir, "missing_data_distribution.png")
    plt.savefig(fpath, dpi=100, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"  Saved: {fpath}")


def plot_sample_gallery(samples: List[PairedSample], n_show: int = 4,
                         save_dir: str = None):
    """
    Plot a gallery of paired sample thumbnails (satellite + NWP).
    Scientific purpose: quick visual QC of sample diversity.
    """
    n_show = min(n_show, len(samples))
    if n_show == 0:
        print("No samples to plot.")
        return

    fig, axes = plt.subplots(n_show, 4, figsize=(18, 4 * n_show))
    if n_show == 1:
        axes = axes[np.newaxis, :]

    for row, s in enumerate(samples[:n_show]):
        tgt_lat = s.target_lat
        tgt_lon = s.target_lon

        # Col 0: First satellite channel
        ax = axes[row][0]
        ch = list(s.sat_channels.keys())[0]
        arr = s.sat_channels[ch]
        im = ax.pcolormesh(tgt_lon, tgt_lat, arr, cmap="gray_r",
                           vmin=np.nanpercentile(arr, 2),
                           vmax=np.nanpercentile(arr, 98),
                           shading="auto")
        plt.colorbar(im, ax=ax, label="K")
        ax.set_title(f"{s.sample_id}\nFY-4A {ch}")
        ax.set_aspect("equal", adjustable="box")

        # Col 1: Temperature 850 hPa
        ax = axes[row][1]
        if "temperature" in s.nwp_variables:
            t_arr = s.nwp_variables["temperature"]
            lev_idx = 2 if t_arr.ndim == 3 else None  # 850 hPa (index 2)
            data2d = t_arr[lev_idx] if lev_idx is not None and t_arr.ndim == 3 \
                else t_arr if t_arr.ndim == 2 else t_arr[0]
            im = ax.pcolormesh(tgt_lon, tgt_lat, data2d, cmap="RdYlBu_r",
                               shading="auto")
            plt.colorbar(im, ax=ax, label="K")
            ax.set_title(f"ERA5 T @ 850 hPa\n{s.nwp_time.strftime('%Y-%m-%d %H UTC')}")
            ax.set_aspect("equal", adjustable="box")

        # Col 2: Humidity 850 hPa
        ax = axes[row][2]
        if "specific_humidity" in s.nwp_variables:
            q_arr = s.nwp_variables["specific_humidity"]
            data2d = q_arr[2] * 1000 if q_arr.ndim == 3 \
                else q_arr * 1000 if q_arr.ndim == 2 else q_arr[0] * 1000
            im = ax.pcolormesh(tgt_lon, tgt_lat, data2d, cmap="YlGnBu",
                               shading="auto")
            plt.colorbar(im, ax=ax, label="g/kg")
            ax.set_title(f"ERA5 q @ 850 hPa\n{s.nwp_time.strftime('%H UTC')}")
            ax.set_aspect("equal", adjustable="box")

        # Col 3: QC status
        ax = axes[row][3]
        ax.axis("off")
        status = "VALID" if s.overall_valid else "INVALID"
        color = "green" if s.overall_valid else "red"
        ax.text(0.5, 0.5, f"{status}\n\n"
                f"Time diff: {s.time_difference_minutes:.1f} min\n"
                f"SAT miss: {np.mean(list(s.sat_missing_fraction.values()))*100:.1f}%\n"
                f"NWP miss: {np.mean(list(s.nwp_missing_fraction.values()))*100:.2f}%\n"
                f"\n{'SYNTHETIC' if s.sat_is_synthetic else 'REAL DATA'}",
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=12, fontweight="bold", color=color,
                bbox=dict(boxstyle="round", facecolor="lightyellow"))

    plt.suptitle("Paired Sample Gallery", fontsize=14, fontweight="bold")
    plt.tight_layout()
    if save_dir:
        fpath = os.path.join(save_dir, "sample_gallery.png")
        plt.savefig(fpath, dpi=100, bbox_inches="tight")
        print(f"  Saved: {fpath}")
    plt.show()
    plt.close()
    gc.collect()


# Generate all plots
plot_time_difference_distribution(all_samples, DIRS["plots"])
plot_missing_data_summary(all_samples, DIRS["plots"])
plot_sample_gallery(all_samples, n_show=min(4, len(all_samples)),
                    save_dir=DIRS["plots"])


# %%
# =============================================================================
# SECTION 16: TRAIN / VALIDATION / TEST SPLIT
# =============================================================================
"""
Chronological Split
===================
Scientific rationale:
  Consecutive satellite images are highly correlated (atmospheric state
  changes slowly relative to the 6-hour interval). A random split would
  cause temporal leakage where validation images are similar to training images.

  Therefore we use a CHRONOLOGICAL split:
    Training  : earliest 60% of samples (by timestamp)
    Validation: next 20%
    Test      : latest 20%

  This is the standard approach in NWP-related ML (e.g., FourCastNet,
  Pangu-Weather, GraphCast all use 2017-2018 test, 2016 valid, earlier train).
"""

print("\n" + "=" * 70)
print("SECTION 16: TRAIN / VALIDATION / TEST SPLIT")
print("=" * 70)
print("Using CHRONOLOGICAL split to avoid temporal leakage.")
print()

if len(all_samples) < 3:
    print(f"[WARN] Only {len(all_samples)} samples -- cannot split meaningfully.")
    print("       All samples assigned to 'training'.")
    for s in all_samples:
        s.notes += " | SPLIT=train"
    split_stats = {"train": len(all_samples), "val": 0, "test": 0}
else:
    sorted_samples = sorted(all_samples, key=lambda s: s.sat_time)
    n = len(sorted_samples)
    n_train = int(n * 0.60)
    n_val = int(n * 0.20)
    n_test = n - n_train - n_val

    train_samples = sorted_samples[:n_train]
    val_samples   = sorted_samples[n_train:n_train + n_val]
    test_samples  = sorted_samples[n_train + n_val:]

    for s in train_samples:
        s.notes += " | SPLIT=train"
    for s in val_samples:
        s.notes += " | SPLIT=val"
    for s in test_samples:
        s.notes += " | SPLIT=test"

    split_stats = {"train": n_train, "val": n_val, "test": n_test}
    print(f"  Total samples  : {n}")
    print(f"  Training (60%) : {n_train}  "
          f"[{train_samples[0].sat_time.date()} - "
          f"{train_samples[-1].sat_time.date()}]")
    print(f"  Validation(20%): {n_val}  "
          f"[{val_samples[0].sat_time.date()} - "
          f"{val_samples[-1].sat_time.date()}]" if val_samples else "")
    print(f"  Test (20%)     : {n_test}  "
          f"[{test_samples[0].sat_time.date()} - "
          f"{test_samples[-1].sat_time.date()}]" if test_samples else "")


# %%
# =============================================================================
# SECTION 17: SAVE DATASET
# =============================================================================
"""
Storage Format: NetCDF4 (preferred) or NumPy NPZ (fallback)

NetCDF4 chosen because:
  1. CF-compliant: standard in atmospheric/oceanographic research
  2. Supports coordinate metadata (lat, lon, time, level)
  3. Readable by xarray, Python, R, MATLAB, NCO, CDO
  4. Supports compression (zlib, shuffle)
  5. Self-documenting via attributes
  6. Widely accepted by NWP journals for data sharing

Alternative: Zarr (better for cloud/parallel access, chosen for large datasets)
Alternative: NPZ (simplest, good for Kaggle; loses metadata richness)
"""

print("\n" + "=" * 70)
print("SECTION 17: SAVE DATASET")
print(f"Format: {CONFIG['output_format'].upper()}")
print("=" * 70)


def save_sample_netcdf(sample: PairedSample, output_dir: str) -> str:
    """
    Save one paired sample as a CF-compliant NetCDF4 file.

    File contains:
      - Satellite channels as (lat, lon) variables
      - NWP variables as (level, lat, lon) or (lat, lon) variables
      - Global attributes: timestamps, QC flags, provenance
    """
    fname = f"{sample.sample_id}.nc"
    fpath = os.path.join(output_dir, fname)

    import netCDF4 as nc4

    with nc4.Dataset(fpath, "w", format="NETCDF4") as ds:
        # Dimensions
        ds.createDimension("lat", len(sample.target_lat))
        ds.createDimension("lon", len(sample.target_lon))
        if sample.nwp_pressure_levels is not None:
            ds.createDimension("level", len(sample.nwp_pressure_levels))

        # Coordinate variables
        lat_var = ds.createVariable("lat", "f4", ("lat",))
        lat_var[:] = sample.target_lat
        lat_var.units = "degrees_north"
        lat_var.long_name = "Latitude"
        lat_var.axis = "Y"

        lon_var = ds.createVariable("lon", "f4", ("lon",))
        lon_var[:] = sample.target_lon
        lon_var.units = "degrees_east"
        lon_var.long_name = "Longitude"
        lon_var.axis = "X"

        if sample.nwp_pressure_levels is not None:
            lev_var = ds.createVariable("level", "f4", ("level",))
            lev_var[:] = sample.nwp_pressure_levels
            lev_var.units = "hPa"
            lev_var.long_name = "Pressure level"
            lev_var.positive = "down"
            lev_var.axis = "Z"

        # Satellite channels
        for ch, arr in sample.sat_channels.items():
            vname = f"fy4a_{ch}"
            v = ds.createVariable(vname, "f4", ("lat", "lon"),
                                   fill_value=np.float32(np.nan),
                                   zlib=True, complevel=4)
            v[:] = arr
            v.units = sample.sat_channel_units.get(ch, "unknown")
            v.long_name = f"FY-4A AGRI {ch} Brightness Temperature"
            v.satellite = "FY-4A"
            v.instrument = "AGRI"
            v.satellite_time = sample.sat_time.isoformat()
            v.missing_fraction = sample.sat_missing_fraction.get(ch, np.nan)
            v.is_synthetic = int(sample.sat_is_synthetic)

        # NWP variables
        for var, arr in sample.nwp_variables.items():
            if arr.ndim == 3 and sample.nwp_pressure_levels is not None:
                dims = ("level", "lat", "lon")
            else:
                dims = ("lat", "lon")
                arr = arr if arr.ndim == 2 else arr[0]

            vname = f"nwp_{var}"
            v = ds.createVariable(vname, "f4", dims,
                                   fill_value=np.float32(np.nan),
                                   zlib=True, complevel=4)
            v[:] = arr
            v.units = sample.nwp_variable_units.get(var, "unknown")
            v.long_name = f"ERA5 {var}"
            v.nwp_source = "ERA5 Reanalysis (ECMWF)"
            v.nwp_time = sample.nwp_time.isoformat()
            v.important_note = "REANALYSIS not operational NWP forecast"
            v.missing_fraction = sample.nwp_missing_fraction.get(var, np.nan)
            v.is_synthetic = int(sample.nwp_is_synthetic)

        # Global attributes
        ds.title = "FY-4A + ERA5 Paired Sample for Data Assimilation Research"
        ds.sample_id = sample.sample_id
        ds.satellite_time = sample.sat_time.isoformat()
        ds.nwp_time = sample.nwp_time.isoformat()
        ds.time_difference_minutes = sample.time_difference_minutes
        ds.lat_min = sample.lat_min
        ds.lat_max = sample.lat_max
        ds.lon_min = sample.lon_min
        ds.lon_max = sample.lon_max
        ds.satellite = "FY-4A"
        ds.instrument = "AGRI"
        ds.nwp_source = "ERA5"
        ds.nwp_note = ("ERA5 is REANALYSIS (4D-Var), not operational NWP. "
                        "FY-4A data may have been assimilated into ERA5.")
        ds.overall_valid = int(sample.overall_valid)
        ds.sat_qc_status = sample.sat_qc["overall_status"]
        ds.nwp_qc_status = sample.nwp_qc["overall_status"]
        ds.notes = sample.notes
        ds.conventions = "CF-1.8"
        ds.creation_date = datetime.datetime.utcnow().isoformat() + "Z"
        ds.random_seed = RANDOM_SEED
        ds.python_version = sys.version

    log_event("save_netcdf", "OK", f"Saved: {fname}")
    return fpath


def save_sample_numpy(sample: PairedSample, output_dir: str) -> str:
    """
    Fallback: save sample as compressed NumPy NPZ.
    Simpler than NetCDF but loses rich metadata encoding.
    """
    fname = f"{sample.sample_id}.npz"
    fpath = os.path.join(output_dir, fname)

    save_dict = {
        "target_lat": sample.target_lat,
        "target_lon": sample.target_lon,
    }
    for ch, arr in sample.sat_channels.items():
        save_dict[f"fy4a_{ch}"] = arr
    for var, arr in sample.nwp_variables.items():
        save_dict[f"nwp_{var}"] = arr
    if sample.nwp_pressure_levels is not None:
        save_dict["nwp_pressure_levels"] = sample.nwp_pressure_levels

    np.savez_compressed(fpath, **save_dict)
    log_event("save_numpy", "OK", f"Saved: {fname}")
    return fpath


# Save all samples
saved_files = []
save_errors = []

for s in all_samples:
    try:
        if CONFIG["output_format"] == "netcdf":
            try:
                fpath = save_sample_netcdf(s, DIRS["paired"])
            except Exception as nc_err:
                print(f"  [WARN] NetCDF save failed ({nc_err}); falling back to NPZ")
                fpath = save_sample_numpy(s, DIRS["paired"])
        else:
            fpath = save_sample_numpy(s, DIRS["paired"])

        saved_files.append(fpath)
    except Exception as exc:
        log_error(s.sample_id, "save", "save_sample", str(exc))
        save_errors.append(s.sample_id)

print(f"\n[Save] {len(saved_files)} samples saved, {len(save_errors)} errors")
if save_errors:
    print(f"  Failed: {save_errors}")


# %%
# =============================================================================
# SECTION 17b: METADATA MANIFEST (paired_samples.csv)
# =============================================================================

print("\nBuilding metadata manifest ...")

manifest_rows = []
for s in all_samples:
    split = "train"
    for note_part in s.notes.split(" | "):
        if note_part.startswith("SPLIT="):
            split = note_part.replace("SPLIT=", "")

    row = {
        "sample_id": s.sample_id,
        "satellite_file": f"{s.sample_id}.{'nc' if CONFIG['output_format'] == 'netcdf' else 'npz'}",
        "nwp_file": f"era5_{'synthetic' if s.nwp_is_synthetic else 'real'}",
        "satellite_time": s.sat_time.isoformat(),
        "nwp_time": s.nwp_time.isoformat(),
        "time_difference_minutes": f"{s.time_difference_minutes:.2f}",
        "lat_min": s.lat_min,
        "lat_max": s.lat_max,
        "lon_min": s.lon_min,
        "lon_max": s.lon_max,
        "satellite_channels": str(list(s.sat_channels.keys())),
        "nwp_variables": str(list(s.nwp_variables.keys())),
        "pressure_levels": str(list(s.nwp_pressure_levels.astype(int))
                               if s.nwp_pressure_levels is not None else []),
        "satellite_missing_fraction": f"{np.mean(list(s.sat_missing_fraction.values())):.4f}",
        "nwp_missing_fraction": f"{np.mean(list(s.nwp_missing_fraction.values())):.6f}",
        "quality_status": "VALID" if s.overall_valid else "INVALID",
        "sat_is_synthetic": s.sat_is_synthetic,
        "nwp_is_synthetic": s.nwp_is_synthetic,
        "split": split,
        "notes": s.notes,
    }
    manifest_rows.append(row)

manifest_df = pd.DataFrame(manifest_rows)
manifest_path = os.path.join(CONFIG["data_dir"], "paired_samples.csv")
manifest_df.to_csv(manifest_path, index=False)
print(f"Manifest saved: {manifest_path}")
print(f"  Columns: {list(manifest_df.columns)}")
print(f"  Rows   : {len(manifest_df)}")
print()
print(manifest_df[["sample_id", "satellite_time", "time_difference_minutes",
                     "quality_status", "split"]].to_string(index=False))


# %%
# =============================================================================
# SECTION 18: FINAL QC REPORT
# =============================================================================

print("\n" + "=" * 70)
print("SECTION 18: FINAL QC REPORT")
print("=" * 70)

total_sat_files = len(all_samples)
total_nwp_files = len(all_samples)  # 1:1 for prototype
total_pairs = len(all_samples)
valid_pairs = sum(1 for s in all_samples if s.overall_valid)
rejected_pairs = total_pairs - valid_pairs

rejection_reasons: Dict[str, int] = {}
for s in all_samples:
    if not s.overall_valid:
        for reason in s.sat_qc.get("reject_reasons", []):
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        for reason in s.nwp_qc.get("reject_reasons", []):
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

mean_sat_miss = np.mean([
    np.mean(list(s.sat_missing_fraction.values())) for s in all_samples
]) if all_samples else 0.0
mean_nwp_miss = np.mean([
    np.mean(list(s.nwp_missing_fraction.values())) for s in all_samples
]) if all_samples else 0.0
time_diffs = [s.time_difference_minutes for s in all_samples]

print(f"""
QC REPORT
=========
Total satellite files processed : {total_sat_files}
Total NWP files processed       : {total_nwp_files}
Potential pairs                 : {total_pairs}
Valid pairs                     : {valid_pairs}
Rejected pairs                  : {rejected_pairs}

Rejection reasons:
{chr(10).join(f"  {r}: {c}" for r, c in rejection_reasons.items()) or "  None"}

Data quality:
  Mean satellite missing fraction : {mean_sat_miss:.4f}
  Mean NWP missing fraction       : {mean_nwp_miss:.6f}

Time difference statistics:
  Mean  : {np.mean(time_diffs):.2f} min
  Std   : {np.std(time_diffs):.2f} min
  Min   : {np.min(time_diffs):.2f} min
  Max   : {np.max(time_diffs):.2f} min

Dataset split:
  Training   : {sum(1 for s in all_samples if 'SPLIT=train' in s.notes)}
  Validation : {sum(1 for s in all_samples if 'SPLIT=val' in s.notes)}
  Test       : {sum(1 for s in all_samples if 'SPLIT=test' in s.notes)}

Synthetic data:
  Synthetic satellite : {sum(1 for s in all_samples if s.sat_is_synthetic)}
  Synthetic NWP       : {sum(1 for s in all_samples if s.nwp_is_synthetic)}
  NOTE: Synthetic data is for pipeline validation only.

Output:
  Paired samples dir  : {DIRS['paired']}
  Manifest CSV        : {manifest_path}
  Error log           : see processing_errors.csv
""")

# Save QC report
qc_report = {
    "total_sat_files": total_sat_files,
    "total_nwp_files": total_nwp_files,
    "total_pairs": total_pairs,
    "valid_pairs": valid_pairs,
    "rejected_pairs": rejected_pairs,
    "rejection_reasons": rejection_reasons,
    "mean_sat_missing_fraction": float(mean_sat_miss),
    "mean_nwp_missing_fraction": float(mean_nwp_miss),
    "time_diff_mean_min": float(np.mean(time_diffs)) if time_diffs else 0.0,
    "time_diff_max_min": float(np.max(time_diffs)) if time_diffs else 0.0,
    "config": {k: str(v) for k, v in CONFIG.items()},
    "generated": datetime.datetime.utcnow().isoformat(),
}
qc_path = os.path.join(DIRS["reports"], "qc_report.json")
with open(qc_path, "w") as f:
    json.dump(qc_report, f, indent=2)
print(f"QC report saved: {qc_path}")

# Save error log
error_log_path = os.path.join(CONFIG["data_dir"], "processing_errors.csv")
if AGENT_ERRORS:
    pd.DataFrame(AGENT_ERRORS).to_csv(error_log_path, index=False)
else:
    pd.DataFrame(columns=["timestamp", "file", "stage", "step", "error"]
                 ).to_csv(error_log_path, index=False)
print(f"Error log saved: {error_log_path}")

# Final visualization: QC summary bar chart
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Pair status
labels = ["Valid", "Rejected"]
counts = [valid_pairs, rejected_pairs]
colors = ["#27ae60", "#e74c3c"]
ax1.bar(labels, counts, color=colors, edgecolor="white", linewidth=1.5)
ax1.set_title("Paired Sample QC Status")
ax1.set_ylabel("Number of Samples")
for i, (l, c) in enumerate(zip(labels, counts)):
    ax1.text(i, c + 0.1, str(c), ha="center", fontweight="bold")
ax1.grid(True, alpha=0.3, axis="y")

# Time difference distribution
if time_diffs:
    ax2.hist(time_diffs, bins=15, color="steelblue", edgecolor="white", alpha=0.8)
    ax2.axvline(CONFIG["max_time_difference_minutes"], color="red",
                linestyle="--", label=f"Threshold ({CONFIG['max_time_difference_minutes']} min)")
    ax2.set_xlabel("Time Difference (minutes)")
    ax2.set_ylabel("Count")
    ax2.set_title("Temporal Matching Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

plt.tight_layout()
fig_path = os.path.join(DIRS["plots"], "qc_summary.png")
plt.savefig(fig_path, dpi=100, bbox_inches="tight")
plt.show()
plt.close()
print(f"QC summary plot saved: {fig_path}")


# %%
# =============================================================================
# SECTION 19: EXAMPLE PAIRED SAMPLE
# =============================================================================

print("\n" + "=" * 70)
if all_samples:
    example = all_samples[0]
    print(f"""
==================================================
PAIRED SAMPLE
==================================================

Sample ID:
  {example.sample_id}

Satellite:
  FY-4A AGRI
  Channels: {list(example.sat_channels.keys())}
  Units: {list(example.sat_channel_units.values())}
  Grid: {len(example.target_lat)} lat x {len(example.target_lon)} lon

Satellite time:
  {example.sat_time.strftime('%Y-%m-%d %H:%M UTC')}

NWP time:
  {example.nwp_time.strftime('%Y-%m-%d %H:%M UTC')}

Time difference:
  {example.time_difference_minutes:.1f} minutes

Region:
  Latitude  : {example.lat_min}N -- {example.lat_max}N
  Longitude : {example.lon_min}E -- {example.lon_max}E

NWP source:
  ERA5 Reanalysis (ECMWF)
  *** REANALYSIS -- NOT operational NWP forecast ***

NWP variables:
  {list(example.nwp_variables.keys())}

Pressure levels:
  {list(example.nwp_pressure_levels.astype(int)) if example.nwp_pressure_levels is not None else 'N/A'} hPa

Satellite missing:
  {' | '.join(f"{ch}: {mf*100:.1f}%" for ch, mf in example.sat_missing_fraction.items())}

NWP missing:
  {' | '.join(f"{var}: {mf*100:.2f}%" for var, mf in example.nwp_missing_fraction.items())}

Synthetic data:
  Satellite: {example.sat_is_synthetic}
  NWP      : {example.nwp_is_synthetic}

Quality:
  Satellite QC : {example.sat_qc['overall_status']}
  NWP QC       : {example.nwp_qc['overall_status']}
  Overall      : {'VALID' if example.overall_valid else 'INVALID'}

Notes:
  {example.notes}

==================================================
""")
else:
    print("No samples available.")


# %%
# =============================================================================
# SECTION 20: LIMITATIONS AND SCALING
# =============================================================================

print("=" * 70)
print("SECTION 20: LIMITATIONS AND SCALING")
print("=" * 70)
print("""
CURRENT LIMITATIONS
===================

1. SYNTHETIC DATA (most important)
   - When CONFIG['fy4a_use_synthetic'] = True, all satellite data is synthetic.
   - Synthetic data validates the PIPELINE, not the science.
   - To use real data: obtain FY-4A HDF5 files from data.nsmc.org.cn
     and set CONFIG['fy4a_data_dir'] to the mounted Kaggle dataset path.
   - Real calibration coefficients must be read from the HDF5 Calibration
     group, not the simplified linear approximation used here.

2. ERA5 vs OPERATIONAL NWP
   - ERA5 is a REANALYSIS, not a forecast.
   - For real data assimilation experiments, use NCEP GFS or ECMWF HRES.
   - ERA5 may have already assimilated FY-4A data, creating circularity.
   - For clean experiments: use ERA5 from before 2018 (pre-FY-4A era).

3. CALIBRATION
   - Real FY-4A IR calibration requires reading the per-channel LUT from
     the Calibration group of the HDF5 file.
   - The simplified linear approximation here is for structural demonstration.

4. SPATIAL RESOLUTION MISMATCH
   - FY-4A native: ~4 km at nadir
   - ERA5 native: ~28 km (0.25 deg)
   - We aggregate satellite to NWP resolution, losing fine-scale information.
   - An intermediate common grid (0.05 deg) would retain more satellite detail
     but require NWP interpolation (with documented accuracy caveats).

5. TEMPORAL COVERAGE
   - Prototype covers one day (2023-07-15).
   - Full research dataset would require months-years of data.

SCALING GUIDE
=============

Stage 1 (this notebook): 1-20 samples -- Kaggle free tier
Stage 2: 100-1000 samples
  - Mount FY-4A Kaggle dataset (upload HDF files as Kaggle Dataset)
  - Use CDS API to download ERA5 for full month
  - Process in batches of 24 hours, releasing memory between batches

Stage 3: 10,000+ samples
  - Use cloud storage (GCS, S3) for data
  - Parallelize with Dask or multiprocessing
  - Use Zarr format for cloud-native I/O
  - Run on Kaggle GPU or cloud VM

Recommended next steps:
  1. Register at data.nsmc.org.cn for FY-4A access
  2. Register at cds.climate.copernicus.eu for ERA5 access
  3. Upload a test FY-4A HDF file as a Kaggle Dataset
  4. Set CONFIG['fy4a_use_synthetic'] = False
  5. Set CONFIG['cds_api_key'] in Kaggle Secrets
  6. Rerun notebook from Section 5 onwards
  7. Scale to larger date ranges once single-day pipeline is validated

COMPUTATIONAL RESOURCES ESTIMATE
=================================
  Per sample (0.25 deg grid, 20-45N, 100-135E):
    Grid size: ~101 lat x 141 lon = 14,241 cells
    Channels: 3 x 14,241 x 4 bytes = ~171 KB satellite
    NWP vars: 5 vars x 7 levels x 14,241 x 4 bytes = ~2 MB
    Total per sample: ~2.2 MB

  100 samples: ~220 MB RAM (manageable on Kaggle)
  1000 samples: ~2.2 GB RAM (needs chunked processing)
  10,000 samples: needs Zarr + chunked I/O + cloud storage

""")

print("=" * 70)
print("PIPELINE COMPLETE")
print("=" * 70)
print(f"  Samples created : {len(all_samples)}")
print(f"  Valid samples   : {sum(1 for s in all_samples if s.overall_valid)}")
print(f"  Output dir      : {CONFIG['data_dir']}")
print(f"  Manifest        : {manifest_path}")
print(f"  Error log       : {error_log_path}")
print(f"  QC report       : {qc_path}")
print(f"  Plots           : {DIRS['plots']}")
print()
print("To scale: set CONFIG['fy4a_use_synthetic'] = False,")
print("  add your CDS API key, mount FY-4A data, and rerun.")
print("=" * 70)
