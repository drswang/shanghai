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
│   ├── new_postproc2/          # proc 2 — scenario TBC
│   ├── new_postproc3/          # proc 3 — scenario TBC
│   └── new_postproc4/          # proc 4 — not yet delivered
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
| `new_postproc2/infil_7_890_rain/` | proc 2 | TBC | Unusual: ~40% flooded area but 3.7m mean depth vs ~2m for others; low correlation with old ctrl (r=0.79) |
| `new_postproc3/infil_7_890_rain/` | proc 3 | TBC | Floods like proc 1 in extent and depth; scenario label not yet confirmed |
| `new_postproc4/infil_7_890_rain/` | proc 4 | TBC | Not yet delivered |

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

| Folder | Label | Purpose |
|--------|-------|---------|
| `new_postproc1` | proc 1 | Baseline reconstruction (confirmed) |
| `new_postproc2` | proc 2 | Scenario TBC — unusual behavior (see notes above) |
| `new_postproc3` | proc 3 | Scenario TBC — floods similarly to proc 1 |
| `new_postproc4` | proc 4 | Not yet delivered |

## Current Status (as of 2026-05-03)

### Completed
- `postproc_analysis.ipynb` created — adapts `Untitled.ipynb` for the new postproc scenarios
- proc1, proc2, proc3 (`infil_7_890_rain`) all delivered with unique data (verified by MD5)
- `Fig_norain1_comparison.png` updated: 3 rows (proc 1/2/3), snapshot times shown in panels

### Scenario characterization (based on flooded-area time series analysis)

| Label | Mean wet cells | Mean depth (wet) | Correlation vs old ctrl | Character |
|-------|---------------|-----------------|------------------------|-----------|
| old ctrl | 58,460 | 2.01 m | — | reference |
| old norain1 | 57,847 | 2.02 m | r=0.9997 | near-identical to ctrl |
| old norain2 | 57,332 | 2.02 m | r=0.9986 | near-identical to ctrl |
| proc 1 | 56,607 | 2.06 m | r=0.9984 | matches old ctrl well |
| proc 2 | 22,791 | 3.73 m | r=0.7907 | **anomalous** — far less area, much deeper |
| proc 3 | 56,012 | 2.07 m | r=0.9975 | floods like proc 1 |

Proc 2 and proc 3 scenario labels (norain1, norain2, etc.) are **not yet confirmed** — need verification from model operator.

### Next steps
- Confirm scenario labels for proc 2 and proc 3
- Wait for proc 4 delivery
- Run `postproc_analysis.ipynb` once all scenarios confirmed

## Output Products

- `Fig_Overview.pdf` - Composite analysis figure
- `Fig_Overview_maps.pdf` - Map series
- `Fig_Diff.pdf` - Scenario difference analysis
- `Shanghai_1905_flood_movie.mp4` - Animated flood propagation (original)
- `Fig_postproc_flooded_area.pdf` - Flooded area time series, new experiments (planned)
- `Fig_postproc_diff.pdf` - Scenario differences vs new ctrl (planned)
- `Shanghai_1905_flood_movie_new_ctrl.mp4` - Animation for new ctrl (planned)

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
