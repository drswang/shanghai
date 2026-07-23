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
│   ├── new_postproc4/          # proc 4 — no rain #1 + #2
│   ├── new_postproc5/          # proc 5 — stone → earth dike
│   └── new_postproc6/          # proc 6 — neap tide
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
| `new_postproc2/infil_7_890_rain/` | proc 2 | no rain #2 | Confirmed: diverges ~Aug 27 (late); t312–t321 gap now filled, complete |
| `new_postproc3/infil_7_890_rain/` | proc 3 | no rain #1 | Confirmed: diverges ~Aug 20 (early); complete |
| `new_postproc4/infil_7_890_rain/` | proc 4 | no rain #1 + #2 | Confirmed via superposition (proc2+proc3-ctrl≈proc4, resid≈13 cells); complete |
| `new_postproc5/infil_7_890_rain/` | proc 5 | stone → earth dike | Confirmed: recovers to ≈ctrl by Sep 2, not a rain scenario; complete |

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
| `new_postproc2` | proc 2 | no rain #2 | Complete (t312–t321 gap filled) |
| `new_postproc3` | proc 3 | no rain #1 | Complete |
| `new_postproc4` | proc 4 | no rain #1 + #2 | Complete |
| `new_postproc5` | proc 5 | stone → earth dike | Complete |
| `new_postproc6` | proc 6 | neap tide | Complete (delivered 2026-07-23) |

## Current Status (as of 2026-07-09)

### Completed
- All 5 proc scenarios delivered and file-checked — every `infil_7_890_rain` folder has 358 non-empty files (proc 2 t312–t321 gap now filled)
- **Scenario labels confirmed by data analysis** (wet-cell divergence timing + superposition test); proc→scenario mapping settled
- `Fig_norain1_comparison.png` — 5 rows in logical order (ctrl, no rain #1, no rain #2, no rain #1&2, stone→earth dike), 4 snapshot columns
- `Fig_Diff_new.png` — 3-panel difference maps: No Rain #1, No Rain #2, No Rain #1+2 vs ctrl
- `Fig_Overview_maps_new.png` — 2×2 ctrl (proc 1) snapshots at t49/t90/t275/t357
- Local figure environment set up on this machine (`~/anaconda3/bin/python` + GADM); GitHub remote switched to SSH

### Scenario characterization (confirmed via wet-cell time series; t1 ≈ Aug 19 00:00)

| Label | Scenario | Diverges from ctrl | Character |
|-------|----------|--------------------|-----------|
| proc 1 | ctrl | — | reference |
| proc 2 | no rain #2 | ~Aug 27 04:00 (t197) | Identical to ctrl until Aug 27, then fewer wet cells (end Δ ≈ −2675) |
| proc 3 | no rain #1 | ~Aug 20 (t24) | Early divergence, effect fades by Sep 2 (end Δ ≈ −423) |
| proc 4 | no rain #1+2 | ~Aug 20 (t24) | Deepest deficit; equals proc2+proc3 effect (superposition resid ≈ 13 cells) |
| proc 5 | stone → earth dike | ~Aug 20 (t24) | Diverges then recovers to ≈ctrl by Sep 2 (end Δ ≈ −137); structural, not rain |

Labels are **data-confirmed**. They match the earlier timing inference and are the opposite of naive folder-order reading of the scenario list.

### Outstanding issues
- (none blocking) — scenario labels resolved; all files complete

## Output Products

### Original experiments (`update2/`)
- `Fig_Overview.pdf` — Composite analysis figure
- `Fig_Overview_maps.pdf` — Map series (4 ctrl snapshots)
- `Fig_Diff.pdf` — Scenario difference maps (norain1, norain2, lowtide, nostone)
- `Shanghai_1905_flood_movie.mp4` — Animated flood propagation

### New experiments (`postproc/`)
- `Fig_norain1_comparison.png` — 5×4 snapshot grid (rows: ctrl, no rain #1, no rain #2, no rain #1&2, stone→earth dike; 4 timestep columns)
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
