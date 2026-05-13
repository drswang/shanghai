# Shanghai 1905 Flood Modeling Project

Hydrodynamic flood modeling and geospatial analysis project reconstructing the August 1905 Shanghai flood event. Analyzes rainfall, tidal influences, and water depths across 358 hourly timesteps with scenario comparisons.

## Tech Stack

- **Language**: Python 3.9+
- **Environment**: Jupyter Notebooks
- **Geospatial**: GeoPandas, Shapely, Pyproj
- **Data Processing**: Pandas, NumPy, xarray (NetCDF climate data)
- **Visualization**: Matplotlib, Contextily (basemaps), matplotlib_scalebar
- **Statistics**: SciPy (lognormal distribution fitting)
- **Animation**: FFMpegWriter, PillowWriter

## Project Structure

```
shanghai/
├── Untitled.ipynb              # Main analysis notebook (original experiments)
├── postproc_analysis.ipynb     # New experiments analysis notebook
├── 20Creanalysis.ipynb         # Historical climate reanalysis
├── update2/                    # Hydrodynamic model outputs (7.2 GB, original)
│   ├── ctrl/                   # Baseline scenario
│   ├── lowtide/                # Low tide scenario
│   ├── norain1/, norain2/      # No rainfall scenarios
│   └── nostone/                # No stone barriers scenario
├── postproc/                   # New hydrodynamic model outputs
│   ├── new_postproc1/          # proc 1 — ctrl (baseline)
│   ├── new_postproc2/          # proc 2 — no rain #2
│   ├── new_postproc3/          # proc 3 — no rain #1
│   └── new_postproc4/          # proc 4 — no rain #1 + #2
├── map/                        # Geographic data
│   └── 1910map/shape/          # Historical shapefiles
├── 市管河道/                    # Current river network shapefiles
└── *.csv                       # Tide, rainfall, and analysis data
```

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `update2/*/text/` | XYZ gridded water depth files (t1.xyz - t358.xyz per scenario, original) |
| `update2/*/figures/` | Pre-rendered PNG maps for each timestep (original) |
| `postproc/new_postproc{N}/infil_7_890_rain/text/` | New XYZ water depth files (t1.xyz - t358.xyz) |
| `postproc/new_postproc{N}/infil_7_890_rain/figures/` | New pre-rendered PNG maps |
| `map/1910map/shape/` | Historical 1910 boundaries (coastline, embankments, polders) |
| `市管河道/` | Current Shanghai river network shapefile |

### New postproc experiment folders

Each `new_postproc{N}` folder contains multiple experiment sub-folders; **always use `infil_7_890_rain`** for analysis.

| Folder | Label | Scenario | Notes |
|--------|-------|----------|-------|
| `new_postproc1/infil_7_890_rain/` | proc 1 | ctrl (baseline) | Confirmed matches old ctrl pattern |
| `new_postproc2/infil_7_890_rain/` | proc 2 | no rain #2 | Inferred from divergence timing (~Aug 27); **10 empty files t312–t321** (Sep 1 00:00–09:00) — needs re-delivery from model operator |
| `new_postproc3/infil_7_890_rain/` | proc 3 | no rain #1 | Inferred from divergence timing (~Aug 20–21); complete |
| `new_postproc4/infil_7_890_rain/` | proc 4 | no rain #1 + #2 | Inferred: matches proc 3 early, proc 2 late; complete |

## Running the Project

```bash
# Main flood analysis
jupyter notebook Untitled.ipynb

# Climate reanalysis
jupyter notebook 20Creanalysis.ipynb
```

**Dependencies** (conda/pip):
```
geopandas pandas numpy xarray matplotlib contextily shapely pyproj scipy ffmpeg
```

## Key Data Files

| File | Description |
|------|-------------|
| `wusongkou.csv` | Observed water levels Aug 19, 1905 |
| `Wusong_tide_modeling_19050801-19050916.csv` | Tide model data |
| `xujiahui_aug2031_daily_rain.csv` | 2031 rainfall projection |
| `river_mask.xyz` | River mask for analysis region |

## Geographic Parameters

- **Bounds**: lat (30.8, 31.5), lon (120.8, 121.5)
- **CRS**: EPSG:4326 (WGS84)
- **Timesteps**: 358 hours per scenario

## Model Scenarios

### Original (`update2/`)

| Scenario | Purpose |
|----------|---------|
| `ctrl` | Baseline reconstruction |
| `lowtide` | Low tide conditions |
| `norain1/2` | No rainfall variants |
| `nostone` | Without historical stone barriers |

### New (`postproc/`)

| Folder | Label | Scenario | Status |
|--------|-------|----------|--------|
| `new_postproc1` | proc 1 | ctrl | Complete |
| `new_postproc2` | proc 2 | no rain #2 | 10 empty files t312–t321 |
| `new_postproc3` | proc 3 | no rain #1 | Complete |
| `new_postproc4` | proc 4 | no rain #1 + #2 | Complete |

## Current Status (as of 2026-05-13)

### Completed
- All 4 proc scenarios delivered and file-checked (all `infil_7_890_rain` folders have 358 files except proc2 t312–t321)
- Scenario labels inferred from divergence timing analysis (needs operator confirmation)
- `Fig_norain1_comparison.png` — 4 rows (proc 1/2/3/4), 4 snapshot columns
- `Fig_Diff_new.png` — 3-panel difference maps: No Rain #1, No Rain #2, No Rain #1+2 vs ctrl
- `Fig_Overview_maps_new.png` — 2×2 ctrl (proc 1) snapshots at t49/t90/t275/t357

### Scenario characterization (based on flooded-area time series analysis)

| Label | Scenario | Diverges from ctrl | Character |
|-------|----------|--------------------|-----------|
| proc 1 | ctrl | — | reference |
| proc 2 | no rain #2 | ~Aug 27 04:00 | Identical to ctrl until Aug 27, then fewer wet cells; 10-hr data gap Sep 1 |
| proc 3 | no rain #1 | ~Aug 20–21 | ~300–450 fewer wet cells throughout, otherwise similar to ctrl |
| proc 4 | no rain #1+2 | ~Aug 20–21 | Matches proc 3 early, tracks proc 2 after Aug 27 |

Scenario labels are **inferred, not yet confirmed** by model operator. Proc 2 t312–t321 gap also needs re-delivery.

### Outstanding issues
- Confirm scenario labels for proc 2, 3, 4 with model operator
- Request re-delivery of proc 2 `infil_7_890_rain` t312–t321 (empty files)

## Output Products

### Original experiments (`update2/`)
- `Fig_Overview.pdf` — Composite analysis figure
- `Fig_Overview_maps.pdf` — Map series (4 ctrl snapshots)
- `Fig_Diff.pdf` — Scenario difference maps (norain1, norain2, lowtide, nostone)
- `Shanghai_1905_flood_movie.mp4` — Animated flood propagation

### New experiments (`postproc/`)
- `Fig_norain1_comparison.png` — 4×4 snapshot grid (proc 1–4 rows, 4 timestep columns)
- `Fig_Overview_maps_new.png` — 2×2 ctrl (proc 1) snapshots at t49/t90/t275/t357
- `Fig_Diff_new.png` — 3-panel difference maps: No Rain #1, No Rain #2, No Rain #1+2 vs ctrl
- `Fig_norain1_comparison.py` — script for comparison figure
- `Fig_Overview_maps_new.py` — script for ctrl overview maps
- `Fig_Diff_new.py` — script for difference maps

## External Data Dependencies

- GADM boundaries: `~/sandbox/data/borders/gadm36.shp`
- 20C precipitation reanalysis: `~/sandbox/data/20C_PRECIP/*.nc`

## Data Formats

| Format | Usage |
|--------|-------|
| XYZ | Gridded hydrodynamic model outputs (lon, lat, depth) |
| CSV | Tide data, rainfall, model summaries |
| Shapefile | Geographic boundaries, rivers |
| NetCDF | Climate reanalysis data |
