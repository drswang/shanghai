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
│   ├── new_postproc1/          # ctrl (baseline)
│   ├── new_postproc2/          # norain1 (no rain #1)
│   ├── new_postproc3/          # norain2 (no rain #2)
│   └── new_postproc4/          # no rain at all (new scenario)
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

| Folder | Scenario |
|--------|---------|
| `new_postproc1/infil_7_890_rain/` | ctrl (baseline) |
| `new_postproc2/infil_7_890_rain/` | norain1 (no rain #1) |
| `new_postproc3/infil_7_890_rain/` | norain2 (no rain #2) |
| `new_postproc4/infil_7_890_rain/` | no rain at all (new) |

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

| Scenario | Purpose |
|----------|---------|
| `new_postproc1` (ctrl) | Baseline reconstruction |
| `new_postproc2` (norain1) | No rain #1 |
| `new_postproc3` (norain2) | No rain #2 |
| `new_postproc4` (no rain at all) | Zero rainfall (new scenario) |

## Current Status (as of 2026-04-24)

### Completed
- `postproc_analysis.ipynb` created — adapts `Untitled.ipynb` for the 4 new postproc scenarios
- New `postproc/` directory structure documented

### Known data issue — postproc folders
MD5 comparison of all 8 simulations across `new_postproc1`–`4` revealed:

| Simulation | Folder 1 | Folders 2, 3, 4 |
|---|---|---|
| `7_890_rain` | unique | all three differ from each other |
| `890_rain` | unique | 2=3=4 (identical) |
| `890_rain_adjusted` | **missing** (no text folder) | 2=3=4 (identical) |
| `890_rain_average` | unique | 2=3=4 (identical) |
| `infil_7_890_rain` | unique | 2=3=4 (identical) |
| `infil_890_rain` | unique | 2=3=4 (identical) |
| `infil_890_rain_adjusted` | unique | 2=3=4 (identical) |
| `infil_890_rain_average` | unique | 2=3 identical; **4 missing** |

**Action needed**: For most simulations, folders 2/3/4 have identical data — the correct scenario outputs for norain1, norain2, and no-rain-at-all likely need to be copied/generated into those folders. Also fix the two missing text directories (`890_rain_adjusted` in folder 1; `infil_890_rain_average` in folder 4).

### Next steps
- Confirm correct model outputs are placed in `new_postproc2`–`4` (currently most sims are copies of the same data)
- Run `postproc_analysis.ipynb` once data is confirmed correct

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
