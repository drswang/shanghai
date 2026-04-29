# AGENTS.md — Shanghai 1905 Flood Modeling (Codex instructions)

Hydrodynamic flood modeling and geospatial analysis of the August 1905 Shanghai flood. Work happens in Jupyter notebooks against large hydrodynamic outputs and GIS layers.

## Quick layout
```
shanghai/
├── Untitled_NCities.ipynb      # Active flood analysis/figures
├── Untitled.ipynb, 20Creanalysis.ipynb, Untitled-Copy1.ipynb
├── update2/                    # Hydrodynamic outputs (large)
│   ├── ctrl/, lowtide/, norain1/, norain2/, nostone/
│   │   ├── text/               # t1.xyz–t358.xyz grids (lon,lat,depth)
│   │   └── figures/            # Per-timestep PNGs
├── map/                        # Historical map assets (1910, redrawn)
├── 市管河道/                    # Current river network shapefile set
├── *.csv, *.xyz                # Tide/rain inputs, masks
└── Figures/media               # Fig*_*.pdf/png, movies
```

## Running
- Launch notebooks: `jupyter notebook Untitled_NCities.ipynb` (main) or `20Creanalysis.ipynb` (climate).
- Dependencies (conda/pip): `geopandas pandas numpy xarray matplotlib contextily shapely pyproj scipy ffmpeg matplotlib_scalebar pillow`.
- External data referenced: `~/sandbox/data/borders/gadm36.shp`, `~/sandbox/data/20C_PRECIP/*.nc`.

## Scenarios & data
- Scenarios: `ctrl` (baseline), `lowtide`, `norain1`, `norain2`, `nostone`.
- Each scenario has 358 hourly timesteps (`t1.xyz` … `t358.xyz` in `update2/*/text/`); figures mirror the timesteps.
- Key inputs: `wusongkou.csv`, `Wusong_tide_modeling_19050801-19050916.csv`, `xujiahui_aug2031_daily_rain.csv`, `river_mask.xyz`.
- CRS defaults to EPSG:4326; map reprojections often to EPSG:3857.

## Known gotchas
- GeoPandas `to_crs` has no `inplace`; use `layer = layer.to_crs(epsg=3857)` style.
- Large data in `update2/` and media files—avoid copying/duplicating.
- Chinese path names (`市管河道/`, `地图重绘/`) are expected; keep encoding intact.

## Outputs
- Figures: `Fig1_Overview_NCities.*`, `Fig2_Persistence_NCities.*`, `Fig_Overview*.pdf/svg`, `Fig_Diff.*`.
- Animations: `Shanghai_1905_flood_movie.mp4`, `Shanghai_1905_timeseries_map_movie.mp4`.

## Workflow tips
- Use `rg` for searching; notebooks hold code + outputs.
- Keep edits ASCII unless touching existing Chinese-named assets.
- If summarizing notebooks, note sections, data sources, and outputs rather than dumping cells.
