#!/usr/bin/env python3
"""
Script to restructure Untitled_NCities.ipynb with:
1. Data processing cell (shared data loading)
2. Wusongkou extraction cell (extract water levels from model grids)
3. Map configuration cell (shared map setup)
4. Figure 1-4 cells (simplified, using pre-processed data)
"""

import json
import uuid

# Load original notebook
with open("/Users/shwang/sandbox/shanghai/Untitled_NCities.ipynb", "r") as f:
    nb = json.load(f)

# Keep header markdown cell
header_cell = nb["cells"][0]

# Rest of cells (after the 4 figure cells)
rest_cells = nb["cells"][5:]

def make_code_cell(source, cell_id=None):
    """Create a code cell."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id or str(uuid.uuid4())[:8],
        "metadata": {},
        "outputs": [],
        "source": source.split("\n")
    }

def make_markdown_cell(source, cell_id=None):
    """Create a markdown cell."""
    return {
        "cell_type": "markdown",
        "id": cell_id or str(uuid.uuid4())[:8],
        "metadata": {},
        "source": source.split("\n")
    }

# ============================================================================
# CELL 1: DATA PROCESSING
# ============================================================================
data_processing_source = '''"""
Data Processing Cell - Load all shared data for Figures 1-4
============================================================
This cell loads:
- Geographic data (GADM boundaries, historical shapefiles)
- Rainfall data
- Tide data (observed and astronomical)
- River masks
- Flood depth data from all scenarios (ctrl, lowtide, norain1, norain2)
- Computes max depth, duration, and area time series for all scenarios
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib_scalebar.scalebar import ScaleBar
from shapely.geometry import MultiPolygon, LineString
import contextily as ctx
from pyproj import Transformer
import os
import matplotlib as mpl
mpl.rcParams.update({'font.size': 8})

# ============================================================================
# PATHS
# ============================================================================
base_dir = "/Users/shwang/sandbox/shanghai"
rain_path = f"{base_dir}/xujiahui_aug2031_daily_rain.csv"
wusong_obs_path = f"{base_dir}/wusongkou.csv"
wusong_tide_path = f"{base_dir}/Wusong_tide_modeling_19050801-19050916.csv"
river_mask_path = f"{base_dir}/river_mask.xyz"
river_dir = f"{base_dir}/市管河道"
shape_dir = f"{base_dir}/map/1910map/shape"
gadm_path = os.path.expanduser("~/sandbox/data/borders/gadm36.shp")

# Scenario directories
scenario_dirs = {
    "ctrl": f"{base_dir}/update2/ctrl/text",
    "lowtide": f"{base_dir}/update2/lowtide/text",
    "norain1": f"{base_dir}/update2/norain1/text",
    "norain2": f"{base_dir}/update2/norain2/text"
}

# Simulation parameters
SIM_START = pd.Timestamp("1905-08-19 01:00:00")
N_TIMESTEPS = 358
DEPTH_THRESHOLD = 0.3  # meters for inundation
CELL_AREA_KM2 = 0.01  # ~100m x 100m grid

# Pre-surge timestamp: 1905-08-28 12:00
PRE_SURGE_TIME = pd.Timestamp("1905-08-28 12:00:00")
PRE_SURGE_TIMESTEP = int((PRE_SURGE_TIME - SIM_START).total_seconds() / 3600) + 1
print(f"Pre-surge timestep: {PRE_SURGE_TIMESTEP} (corresponds to {PRE_SURGE_TIME})")

# ============================================================================
# LOAD RAINFALL DATA
# ============================================================================
print("\\nLoading rainfall data...")
rain = pd.read_csv(rain_path, sep=",")
rain["date"] = pd.to_datetime(dict(year=rain.Year, month=rain.Mon, day=rain.Day))
rain["daily_mm"] = rain["daily_acc_10thmm"] / 10.0
rain["md"] = rain["date"].dt.strftime("%m-%d")

# Subset for Aug 20 – Sept 5
mask = (rain["date"].dt.month == 8) & (rain["date"].dt.day >= 20) | (rain["date"].dt.month == 9) & (rain["date"].dt.day <= 5)
rain_subset = rain.loc[mask].copy()
ordered_days = sorted(rain_subset["md"].unique(), key=lambda x: pd.to_datetime("1900-" + x))
rain_subset["md"] = pd.Categorical(rain_subset["md"], categories=ordered_days, ordered=True)
rain_subset = rain_subset[rain_subset["md"].between("08-20", "09-02")]
ordered_days = sorted(rain_subset["md"].unique(), key=lambda x: pd.to_datetime("1900-" + x))

# Split 1905 from other years
rain_1905 = rain_subset[rain_subset["Year"] == 1905]

# Annual max for return period estimation
df_rain = pd.read_csv(rain_path)
df_rain["date"] = pd.to_datetime(dict(year=df_rain.Year, month=df_rain.Mon, day=df_rain.Day))
df_rain["daily_mm"] = df_rain["daily_acc_10thmm"] / 10.0
df_rain["year"] = df_rain["date"].dt.year
annual_max = df_rain.groupby("year")["daily_mm"].max().dropna().sort_values(ascending=False)
n_years = len(annual_max)
ranks = np.arange(1, n_years + 1)
empirical_return_periods = (n_years + 1) / ranks

# Interpolate non-parametric return levels
target_T = [1, 2, 5]
return_levels = np.interp(target_T, np.sort(empirical_return_periods), np.sort(annual_max.values))
R1_LEVEL, R2_LEVEL, R5_LEVEL = return_levels
print(f"  Return levels: 1-yr={R1_LEVEL:.1f}mm, 2-yr={R2_LEVEL:.1f}mm, 5-yr={R5_LEVEL:.1f}mm")

# ============================================================================
# LOAD TIDE / WATER LEVEL DATA (Observed and Astronomical)
# ============================================================================
print("\\nLoading tide data...")

def fix_year(d):
    """Fix 2-digit year to 4-digit (1905)"""
    parts = d.split()
    date_parts = parts[0].split('/')
    if len(date_parts[2]) == 2:
        date_parts[2] = '19' + date_parts[2]
    return '/'.join(date_parts) + ' ' + parts[1]

# Observed water levels (wusongkou.csv)
tide_obs = pd.read_csv(wusong_obs_path)
tide_obs.columns = tide_obs.columns.str.strip()
tide_obs["fixed_date"] = tide_obs["date and time"].apply(fix_year)
tide_obs["datetime"] = pd.to_datetime(tide_obs["fixed_date"], format="%m/%d/%Y %H:%M")
tide_obs["depth_m"] = tide_obs["water depth (points) (m)"]

# Modeled astronomical tide (pure tide, no surge)
tide_astro = pd.read_csv(wusong_tide_path)
tide_astro.columns = tide_astro.columns.str.strip()
tide_astro["fixed_date"] = tide_astro["date and time"].apply(fix_year)
tide_astro["datetime"] = pd.to_datetime(tide_astro["fixed_date"], format="%m/%d/%Y %H:%M")
tide_astro["depth_m"] = tide_astro["water depth (points) (m)"] + 2.4  # Adjust to same datum

print(f"  Observed tide: {len(tide_obs)} records")
print(f"  Astronomical tide: {len(tide_astro)} records")

# ============================================================================
# LOAD GEOGRAPHIC DATA
# ============================================================================
print("\\nLoading geographic data...")

gadm = gpd.read_file(gadm_path)
sh_parts = gadm[(gadm["NAME_0"] == "China") & (gadm["NAME_2"] == "Shanghai")]
sh_dissolved = sh_parts.dissolve()
geom = sh_dissolved.geometry.iloc[0]
if isinstance(geom, MultiPolygon):
    main_poly = max(geom.geoms, key=lambda p: p.area)
    shanghai_main = gpd.GeoDataFrame(geometry=[main_poly], crs=sh_dissolved.crs)
else:
    shanghai_main = sh_dissolved

other_regions = gadm[(gadm["NAME_0"] == "China") & (gadm["NAME_2"] != "Shanghai")]
china_other = other_regions.dissolve()
shanghai_boundary = gpd.GeoDataFrame(geometry=shanghai_main.boundary, crs=shanghai_main.crs)
china_other_boundary = gpd.GeoDataFrame(geometry=china_other.boundary, crs=china_other.crs)
inland_border = gpd.overlay(shanghai_boundary, china_other_boundary, how="intersection")

# Historical shapefiles
海岸线 = gpd.read_file(f"{shape_dir}/海岸线.shp")
圩塘 = gpd.read_file(f"{shape_dir}/圩塘.shp")
钦公塘 = gpd.read_file(f"{shape_dir}/钦公塘.shp")
雍正石塘 = gpd.read_file(f"{shape_dir}/雍正石塘.shp")

# Load river mask
river_mask_df = pd.read_csv(river_mask_path, sep=r"\\s+", header=None, names=["lon", "lat", "depth"])
river_coords = set(zip(river_mask_df["lon"], river_mask_df["lat"]))

# Load 市管河道 shapefile
市管河道 = gpd.read_file(f"{river_dir}/市管河道.shp")
if 市管河道.crs is None:
    市管河道 = 市管河道.set_crs("EPSG:4326")

print(f"  Shanghai boundary loaded")
print(f"  Historical shapefiles loaded (海岸线, 圩塘, 钦公塘, 雍正石塘)")
print(f"  River mask: {len(river_coords)} cells")

# ============================================================================
# HELPER FUNCTIONS FOR DATA LOADING
# ============================================================================
def load_xyz_data(fpath):
    """Load XYZ file and remove river grid cells."""
    df = pd.read_csv(fpath, sep=r"\\s+", header=None, names=["lon", "lat", "depth"])
    df = df[~df[["lon", "lat"]].apply(tuple, axis=1).isin(river_coords)]
    return df

def create_gdf(df, value_col="depth"):
    """Create GeoDataFrame from DataFrame with lon/lat columns."""
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.lon, df.lat),
        crs="EPSG:4326"
    )
    return gdf

def remove_river_points(gdf, river_gdf, buffer_m=50):
    """Remove points that fall within river polygons (with buffer)."""
    gdf_proj = gdf.to_crs(epsg=3857)
    river_proj = river_gdf.to_crs(epsg=3857)
    river_buffered = river_proj.geometry.buffer(buffer_m).union_all()
    mask = ~gdf_proj.geometry.within(river_buffered)
    result = gdf.loc[mask].copy()
    return result

# ============================================================================
# PROCESS ALL SCENARIOS - COMPUTE MAX DEPTH, DURATION, AREA TIME SERIES
# ============================================================================
print("\\n" + "="*60)
print("PROCESSING FLOOD DATA FOR ALL SCENARIOS")
print("="*60)

# Storage for all scenario data
scenario_data = {}

for scenario_name, xyz_dir in scenario_dirs.items():
    print(f"\\n--- Processing {scenario_name} ---")

    # Initialize storage
    max_depth_dict = {}
    hours_above_dict = {}
    hours_above_presurge_dict = {}  # Duration up to pre-surge only
    area_timeseries = []

    for t in range(1, N_TIMESTEPS + 1):
        if t % 50 == 0:
            print(f"  Timestep {t}/{N_TIMESTEPS}...")

        fpath = os.path.join(xyz_dir, f"t{t}.xyz")
        df_t = load_xyz_data(fpath)

        # Count inundated cells for area time series
        inundated = df_t["depth"] >= DEPTH_THRESHOLD
        n_inundated = inundated.sum()
        area_km2 = n_inundated * CELL_AREA_KM2

        current_time = SIM_START + pd.Timedelta(hours=t-1)
        area_timeseries.append({
            "timestep": t,
            "datetime": current_time,
            "area_km2": area_km2,
            "n_cells": n_inundated
        })

        # Update max depth and duration for each cell
        for _, row in df_t.iterrows():
            coord_key = (row["lon"], row["lat"])

            # Max depth
            if coord_key in max_depth_dict:
                max_depth_dict[coord_key] = max(max_depth_dict[coord_key], row["depth"])
            else:
                max_depth_dict[coord_key] = row["depth"]

            # Duration (hours above threshold)
            if row["depth"] >= DEPTH_THRESHOLD:
                hours_above_dict[coord_key] = hours_above_dict.get(coord_key, 0) + 1
                # Pre-surge duration
                if t <= PRE_SURGE_TIMESTEP:
                    hours_above_presurge_dict[coord_key] = hours_above_presurge_dict.get(coord_key, 0) + 1

    # Convert to DataFrames and GeoDataFrames
    max_depth_df = pd.DataFrame([
        {"lon": k[0], "lat": k[1], "max_depth": v}
        for k, v in max_depth_dict.items()
    ])
    max_depth_gdf = create_gdf(max_depth_df, "max_depth")
    max_depth_gdf = remove_river_points(max_depth_gdf, 市管河道)

    duration_df = pd.DataFrame([
        {"lon": k[0], "lat": k[1], "hours_above": v}
        for k, v in hours_above_dict.items()
    ])
    if len(duration_df) > 0:
        duration_gdf = create_gdf(duration_df, "hours_above")
        duration_gdf = remove_river_points(duration_gdf, 市管河道)
    else:
        duration_gdf = None

    duration_presurge_df = pd.DataFrame([
        {"lon": k[0], "lat": k[1], "hours_above": v}
        for k, v in hours_above_presurge_dict.items()
    ])
    if len(duration_presurge_df) > 0:
        duration_presurge_gdf = create_gdf(duration_presurge_df, "hours_above")
        duration_presurge_gdf = remove_river_points(duration_presurge_gdf, 市管河道)
    else:
        duration_presurge_gdf = None

    area_ts_df = pd.DataFrame(area_timeseries)

    # Load pre-surge snapshot
    presurge_fpath = os.path.join(xyz_dir, f"t{PRE_SURGE_TIMESTEP}.xyz")
    presurge_df = load_xyz_data(presurge_fpath)
    presurge_gdf = create_gdf(presurge_df)
    presurge_gdf = remove_river_points(presurge_gdf, 市管河道)

    # Compute pre-surge metrics
    inundated_mask = presurge_gdf["depth"] >= DEPTH_THRESHOLD
    n_inundated = inundated_mask.sum()
    inundated_area_km2 = n_inundated * CELL_AREA_KM2
    cell_area_m2 = CELL_AREA_KM2 * 1e6
    stored_water_m3 = (presurge_gdf.loc[inundated_mask, "depth"] * cell_area_m2).sum()
    stored_water_million_m3 = stored_water_m3 / 1e6

    # Store all data
    scenario_data[scenario_name] = {
        "max_depth_gdf": max_depth_gdf,
        "duration_gdf": duration_gdf,
        "duration_presurge_gdf": duration_presurge_gdf,
        "area_ts_df": area_ts_df,
        "presurge_gdf": presurge_gdf,
        "presurge_metrics": {
            "inundated_area_km2": inundated_area_km2,
            "stored_water_million_m3": stored_water_million_m3,
            "n_cells_inundated": n_inundated
        }
    }

    print(f"  Max depth cells: {len(max_depth_gdf)}")
    print(f"  Duration cells: {len(duration_gdf) if duration_gdf is not None else 0}")
    print(f"  Peak inundated area: {area_ts_df['area_km2'].max():.1f} km²")
    print(f"  Pre-surge inundated area: {inundated_area_km2:.1f} km²")

print("\\n" + "="*60)
print("DATA PROCESSING COMPLETE")
print("="*60)
'''

# ============================================================================
# CELL 2: WUSONGKOU EXTRACTION
# ============================================================================
wusongkou_extraction_source = '''"""
Wusongkou Station Water Level Extraction
=========================================
Extract simulated water levels at the nearest model grid point to Wusongkou station
for all scenarios (ctrl, lowtide, norain1, norain2).

Wusongkou station coordinates: Latitude 31.383333, Longitude 121.516667
Nearest model grid point: lon=121.515557, lat=31.389006
"""

# Wusongkou station coordinates
WUSONG_STATION_LON = 121.516667
WUSONG_STATION_LAT = 31.383333

# Find nearest grid point
print("Finding nearest grid point to Wusongkou station...")
print(f"  Station coordinates: ({WUSONG_STATION_LAT}°N, {WUSONG_STATION_LON}°E)")

# Use first timestep of ctrl to find nearest point
first_file = os.path.join(scenario_dirs["ctrl"], "t1.xyz")
grid_df = pd.read_csv(first_file, sep=r"\\s+", header=None, names=["lon", "lat", "depth"])

# Calculate distance to station for each grid point
grid_df["dist"] = np.sqrt((grid_df["lon"] - WUSONG_STATION_LON)**2 +
                          (grid_df["lat"] - WUSONG_STATION_LAT)**2)
nearest_idx = grid_df["dist"].idxmin()
NEAREST_LON = grid_df.loc[nearest_idx, "lon"]
NEAREST_LAT = grid_df.loc[nearest_idx, "lat"]
nearest_dist_deg = grid_df.loc[nearest_idx, "dist"]
nearest_dist_km = nearest_dist_deg * 111  # approximate km

print(f"  Nearest grid point: ({NEAREST_LAT:.6f}°N, {NEAREST_LON:.6f}°E)")
print(f"  Distance: {nearest_dist_deg:.6f}° (~{nearest_dist_km:.2f} km)")

# ============================================================================
# EXTRACT WATER LEVELS FOR ALL SCENARIOS
# ============================================================================
print("\\nExtracting water levels from model grid for all scenarios...")

wusong_simulated = {}

for scenario_name, xyz_dir in scenario_dirs.items():
    print(f"  Processing {scenario_name}...")

    water_levels = []

    for t in range(1, N_TIMESTEPS + 1):
        fpath = os.path.join(xyz_dir, f"t{t}.xyz")
        df_t = pd.read_csv(fpath, sep=r"\\s+", header=None, names=["lon", "lat", "depth"])

        # Find the row with nearest coordinates
        mask = (np.abs(df_t["lon"] - NEAREST_LON) < 0.0001) & (np.abs(df_t["lat"] - NEAREST_LAT) < 0.0001)
        if mask.sum() > 0:
            depth = df_t.loc[mask, "depth"].values[0]
        else:
            # Fallback: find minimum distance
            df_t["dist"] = np.sqrt((df_t["lon"] - NEAREST_LON)**2 + (df_t["lat"] - NEAREST_LAT)**2)
            depth = df_t.loc[df_t["dist"].idxmin(), "depth"]

        current_time = SIM_START + pd.Timedelta(hours=t-1)
        water_levels.append({
            "timestep": t,
            "datetime": current_time,
            "water_depth_m": depth
        })

    wusong_df = pd.DataFrame(water_levels)
    wusong_simulated[scenario_name] = wusong_df

    # Save to CSV
    output_path = f"{base_dir}/wusongkou_simulated_{scenario_name}.csv"
    wusong_df.to_csv(output_path, index=False)
    print(f"    Saved: {output_path}")
    print(f"    Water level range: {wusong_df['water_depth_m'].min():.2f} - {wusong_df['water_depth_m'].max():.2f} m")

print("\\nWusongkou extraction complete!")
print("\\nFiles created:")
for scenario_name in scenario_dirs.keys():
    print(f"  - wusongkou_simulated_{scenario_name}.csv")
'''

# ============================================================================
# CELL 3: MAP CONFIGURATION
# ============================================================================
map_config_source = '''"""
Map Configuration Cell - Shared setup for all figure maps
==========================================================
This cell sets up:
- CRS transformations
- Coastal filtering function
- Map plotting helper functions
- Custom colormaps
- Legend elements
"""

# ============================================================================
# TRANSFORM GEOGRAPHIC LAYERS TO WEB MERCATOR
# ============================================================================
print("Transforming layers to Web Mercator (EPSG:3857)...")

# Transform base layers
for layer in [圩塘, 海岸线, 钦公塘, 雍正石塘, shanghai_main, inland_border]:
    layer.to_crs(epsg=3857, inplace=True)

# Transform scenario data
for scenario_name in scenario_data.keys():
    data = scenario_data[scenario_name]
    if data["max_depth_gdf"] is not None:
        scenario_data[scenario_name]["max_depth_gdf"] = data["max_depth_gdf"].to_crs(epsg=3857)
    if data["duration_gdf"] is not None:
        scenario_data[scenario_name]["duration_gdf"] = data["duration_gdf"].to_crs(epsg=3857)
    if data["duration_presurge_gdf"] is not None:
        scenario_data[scenario_name]["duration_presurge_gdf"] = data["duration_presurge_gdf"].to_crs(epsg=3857)
    if data["presurge_gdf"] is not None:
        scenario_data[scenario_name]["presurge_gdf"] = data["presurge_gdf"].to_crs(epsg=3857)

# ============================================================================
# COASTAL FILTERING SETUP
# ============================================================================
print("Setting up coastal filtering...")

coastline_line = 海岸线.geometry.union_all()
if coastline_line.geom_type == 'MultiLineString':
    coastline_line = LineString(np.concatenate([np.array(g.coords) for g in coastline_line.geoms]))
coast_coords = np.array(coastline_line.coords)
coast_coords = coast_coords[np.argsort(coast_coords[:, 1])]
unique_lat, idx = np.unique(coast_coords[:, 1], return_index=True)
COAST_INTERP_FUNC = dict(zip(unique_lat, coast_coords[idx, 0]))

def clean_outsiders(test_gdf):
    """Filter out points east of 1905 coastline."""
    depth_points = test_gdf.copy()
    x = depth_points.geometry.x
    y = depth_points.geometry.y
    depth_points["coast_x"] = np.interp(
        y, np.array(list(COAST_INTERP_FUNC.keys())), np.array(list(COAST_INTERP_FUNC.values()))
    )
    return depth_points[x <= depth_points["coast_x"]].copy()

# Apply coastal filtering to all scenario data
print("Applying coastal filtering to all scenarios...")
for scenario_name in scenario_data.keys():
    data = scenario_data[scenario_name]
    if data["max_depth_gdf"] is not None:
        scenario_data[scenario_name]["max_depth_gdf"] = clean_outsiders(data["max_depth_gdf"])
    if data["duration_gdf"] is not None:
        scenario_data[scenario_name]["duration_gdf"] = clean_outsiders(data["duration_gdf"])
    if data["duration_presurge_gdf"] is not None:
        scenario_data[scenario_name]["duration_presurge_gdf"] = clean_outsiders(data["duration_presurge_gdf"])
    if data["presurge_gdf"] is not None:
        scenario_data[scenario_name]["presurge_gdf"] = clean_outsiders(data["presurge_gdf"])

# ============================================================================
# MAP EXTENT AND AXIS SETUP
# ============================================================================
transformer_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
bounds4326 = shanghai_main.to_crs(epsg=4326).total_bounds
MINX_3857, MINY_3857 = transformer_to_3857.transform(bounds4326[0]-.05, bounds4326[1]-.05)
MAXX_3857, MAXY_3857 = transformer_to_3857.transform(bounds4326[2]+.05, bounds4326[3]+.05)

x_deg_ticks = np.arange(np.floor(bounds4326[0]*5)/5, np.ceil(bounds4326[2]*5)/5 + 0.01, 0.4)
y_deg_ticks = np.arange(np.floor(bounds4326[1]*5)/5, np.ceil(bounds4326[3]*5)/5 + 0.01, 0.4)
X_TICKS_MERC = [transformer_to_3857.transform(x, bounds4326[1])[0] for x in x_deg_ticks]
Y_TICKS_MERC = [transformer_to_3857.transform(bounds4326[0], y)[1] for y in y_deg_ticks]
X_LABELS = [f"{abs(round(x,2))}°E" for x in x_deg_ticks]
Y_LABELS = [f"{abs(round(y,2))}°N" for y in y_deg_ticks]

shanghai_main_3857 = shanghai_main.to_crs(epsg=3857)

# ============================================================================
# CUSTOM COLORMAPS
# ============================================================================
def shuai_colormap1():
    """Custom blue-green colormap for flood depth."""
    C1 = np.asarray([170,219,30])/255
    C2 = np.asarray([2,7,93])/255
    C3 = np.asarray([0,183,235])/255
    C9 = np.asarray([240, 255, 255])/255
    CUTS = 10
    tmp1 = np.asarray([np.linspace(C1[0],C2[0],CUTS),np.linspace(C1[1],C2[1],CUTS),np.linspace(C1[2],C2[2],CUTS)]).transpose()[:-1]
    CUTS = 8
    tmp2 = np.asarray([np.linspace(C2[0],C3[0],CUTS),np.linspace(C2[1],C3[1],CUTS),np.linspace(C2[2],C3[2],CUTS)]).transpose()[:-1]
    CUTS = 4
    tmp4 = np.asarray([np.linspace(C3[0],C9[0],CUTS),np.linspace(C3[1],C9[1],CUTS),np.linspace(C3[2],C9[2],CUTS)]).transpose()
    colors_arr = np.concatenate([tmp1, tmp2, tmp4])
    cmap = mcolors.LinearSegmentedColormap.from_list('my_colormap', colors_arr)
    return cmap.reversed()

CMAP_DEPTH = shuai_colormap1()
CMAP_DURATION = plt.cm.YlOrRd
CMAP_DIFF = plt.cm.RdBu_r

# ============================================================================
# MAP PLOTTING HELPER FUNCTIONS
# ============================================================================
def setup_map_ax(ax):
    """Set up map axis with historical features and basemap."""
    圩塘.plot(ax=ax, color='darkgoldenrod', edgecolor='none')
    钦公塘.plot(ax=ax, color='darkgoldenrod', edgecolor='none', lw=2)
    雍正石塘.plot(ax=ax, edgecolor='slategray', linewidth=3)
    海岸线.plot(ax=ax, edgecolor='black', linewidth=1, linestyle='dashed')
    inland_border.plot(ax=ax, edgecolor='black', linewidth=0.8)
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels, attribution=False)
    ax.set_xlim(MINX_3857, MAXX_3857)
    ax.set_ylim(MINY_3857, MAXY_3857)
    ax.set_xticks(X_TICKS_MERC)
    ax.set_xticklabels(X_LABELS)
    ax.set_yticks(Y_TICKS_MERC)
    ax.set_yticklabels(Y_LABELS)

def plot_hexbin_map(ax, gdf, value_col, cmap, norm, gridsize=70):
    """Plot hexbin map and return hexbin object."""
    # Filter within Shanghai
    gdf_within = gpd.sjoin(gdf, shanghai_main_3857, how='inner', predicate='within')
    hb = ax.hexbin(gdf_within.geometry.x, gdf_within.geometry.y,
                   C=gdf_within[value_col], reduce_C_function=np.mean,
                   gridsize=gridsize, cmap=cmap, norm=norm, edgecolors='none')
    hb.set_antialiased(False)
    return hb

# Legend elements for all maps
LEGEND_ELEMENTS = [
    Line2D([0], [0], color='darkgoldenrod', linewidth=2, label='Earthen Embankment'),
    Line2D([0], [0], color='slategray', linewidth=3, label='Stone Embankment'),
    Line2D([0], [0], color='black', linestyle='dashed', linewidth=1, label='Coastline (1905)'),
    Line2D([0], [0], color='black', linewidth=0.8, label='Shanghai Border'),
]

print("\\nMap configuration complete!")
print(f"  Map extent: {bounds4326[0]:.2f}°E - {bounds4326[2]:.2f}°E, {bounds4326[1]:.2f}°N - {bounds4326[3]:.2f}°N")
'''

# ============================================================================
# CELL 4: FIGURE 1
# ============================================================================
figure1_source = '''"""
Figure 1: Shanghai 1905 Flood Event Overview (Nature Cities)
=============================================================
- Fig. 1A: Hazard trajectory panel (rainfall + boundary water level)
- Fig. 1B: Control maximum depth map (TRUE max across all 358 timesteps)
- Fig. 1C: Depth exceedance curve (CCDF) and threshold area statistics

Uses pre-processed data from data processing cell.
Uses simulated water level from wusongkou_simulated_ctrl.csv for Fig. 1A.
Uses astronomical tide from Wusong_tide_modeling file for comparison.
"""

# ============================================================================
# LOAD SIMULATED WATER LEVEL FOR CONTROL
# ============================================================================
wusong_sim_ctrl = wusong_simulated["ctrl"].copy()

# ============================================================================
# FIGURE 1: THREE-PANEL COMPOSITE
# ============================================================================
fig = plt.figure(figsize=(10, 12), dpi=150)

# Layout: Top row = 1A (wide), Bottom row = 1B (map) + 1C (exceedance)
gs = gridspec.GridSpec(2, 2, height_ratios=[0.8, 1.2], width_ratios=[1, 1],
                       hspace=0.25, wspace=0.25)

ax1 = fig.add_subplot(gs[0, :])   # 1A: time series (spans full width)
ax_map = fig.add_subplot(gs[1, 0])  # 1B: max depth map
ax_exc = fig.add_subplot(gs[1, 1])  # 1C: exceedance curves

# ============================================================================
# PANEL 1A: HAZARD TRAJECTORY
# ============================================================================
color_bar = "#1f77b4"

# Prepare 1905 rainfall data
rain_1905_sorted = rain_1905.sort_values("md")
rain_1905_series = rain_1905_sorted.set_index("md").loc[ordered_days]["daily_mm"].values
x = pd.to_datetime(["1905-" + d for d in ordered_days])

# Horizontal lines for return levels
ax1.axhline(R2_LEVEL, color="#6baed6", linestyle="--", linewidth=2)
ax1.axhline(R5_LEVEL, color="#2171b5", linestyle="--", linewidth=2)
ax1.text(pd.to_datetime("1905-08-18"), R2_LEVEL, "2-yr rainfall\\nreturn period", color="#6baed6", fontsize=8, ha='center', va='bottom')
ax1.text(pd.to_datetime("1905-08-18"), R5_LEVEL-2, "5-yr rainfall\\nreturn period", color="#2171b5", fontsize=8, ha='center', va='top')

# Bar plot
ax1.bar(x, rain_1905_series, color=color_bar, label="Rainfall")

# Formatting
ax1.set_ylim([0, 100])
ax1.tick_params(axis='y', colors=color_bar)
ax1.set_ylabel("Daily Rainfall (mm)", color=color_bar)
ax1.set_xlim(pd.to_datetime("1905-08-16"), pd.to_datetime("1905-09-03"))
tick_dates = pd.date_range("1905-08-20", "1905-09-03")
ax1.set_xticks(tick_dates)
ax1.set_xticklabels([d.strftime("%m/%d") for d in tick_dates], rotation=45)

# Plot simulated water level on right y-axis
ax1_tide = ax1.twinx()

# Filter to plot window
plot_mask = (wusong_sim_ctrl["datetime"] >= "1905-08-20") & (wusong_sim_ctrl["datetime"] <= "1905-09-02 21:00")
wusong_plot = wusong_sim_ctrl.loc[plot_mask]

ax1_tide.plot(wusong_plot["datetime"], wusong_plot["water_depth_m"], color="#d62728", linewidth=2, label="Simulated Water Level (Control)")

# Also plot astronomical tide for reference
tide_mask = (tide_astro["datetime"] >= "1905-08-20") & (tide_astro["datetime"] <= "1905-09-02 21:00")
tide_plot = tide_astro.loc[tide_mask].copy()
ax1_tide.plot(tide_plot["datetime"], tide_plot["depth_m"], color="#FFD700", linewidth=.6, label="Astronomical Tide")

ax1_tide.axhline(5.4, color="#ff7f0e", linestyle="--", linewidth=2)
ax1_tide.text(pd.to_datetime("1905-08-18"), 5.4, "10-yr water level\\nreturn period", color="#ff7f0e", fontsize=8, ha='center', va='bottom')

ax1_tide.tick_params(axis='y', colors="#d62728")
ax1_tide.set_ylabel("Water Level (m)", color="#d62728")
ax1_tide.xaxis.set_major_locator(mdates.DayLocator())
ax1_tide.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax1_tide.set_ylim([0, 7])
ax1_tide.set_xlim(pd.to_datetime("1905-08-16"), pd.to_datetime("1905-09-03"))
tick_dates2 = pd.date_range("1905-08-20", "1905-09-02")
ax1_tide.set_xticks(tick_dates2)
ax1_tide.set_xticklabels([d.strftime("%m/%d") for d in tick_dates2], rotation=45)

# Legend
custom_handles = [
    Patch(facecolor=color_bar, edgecolor='none', label='Rainfall'),
    Line2D([0], [0], color="#d62728", lw=1.5, label='Simulated Water Level'),
    Line2D([0], [0], color="#FFD700", lw=1, label='Astronomical Tide')
]
ax1.legend(custom_handles, [h.get_label() for h in custom_handles], loc="lower left", handlelength=1.5, handleheight=1, frameon=False)

# Event annotations
ax1.annotate("Predecessor\\nRain #1",
             xy=(pd.to_datetime("1905-08-21"), 83.6), xycoords='data',
             xytext=(0, 5), textcoords='offset points',
             ha='center', va='bottom',
             arrowprops=dict(arrowstyle='-|>', facecolor='black', lw=0.8),
             fontsize=8, color='black')

ax1.annotate("Predecessor\\nRain #2",
             xy=(pd.to_datetime("1905-08-28"), 83.6), xycoords='data',
             xytext=(0, 5), textcoords='offset points',
             ha='center', va='bottom',
             arrowprops=dict(arrowstyle='-|>', facecolor='black', lw=0.8),
             fontsize=8, color='black')

ax1.annotate("Typhoon\\nImpact",
             xy=(pd.to_datetime("1905-09-01 12:00"), 83.6), xycoords='data',
             xytext=(0, 5), textcoords='offset points',
             ha='center', va='bottom',
             arrowprops=dict(arrowstyle='-|>', facecolor='black', lw=0.8),
             fontsize=8, color='black')

ax1.set_title("A. Hazard drivers: rainfall and boundary water level (August 1905)",
              fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 1B: CONTROL MAXIMUM DEPTH MAP
# ============================================================================
setup_map_ax(ax_map)
norm = mcolors.Normalize(vmin=0, vmax=2.0)

depth_gdf = scenario_data["ctrl"]["max_depth_gdf"]
hb = plot_hexbin_map(ax_map, depth_gdf, "max_depth", CMAP_DEPTH, norm)

# Colorbar
cbar = plt.colorbar(hb, ax=ax_map, orientation="vertical", shrink=0.7, pad=0.02, extend='max')
cbar.set_label("Maximum Water Depth (m)", fontsize=9)

# Legend
ax_map.legend(handles=LEGEND_ELEMENTS, loc='lower center', ncol=2, fontsize=7,
              frameon=True, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

ax_map.set_title("B. Maximum flood depth (control scenario, all timesteps)", fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 1C: DEPTH EXCEEDANCE CURVE (CCDF) + THRESHOLD AREAS
# ============================================================================
depths = depth_gdf["max_depth"].values
depths_positive = depths[depths > 0.01]

# Calculate exceedance curve (CCDF)
sorted_depths = np.sort(depths_positive)[::-1]
n = len(sorted_depths)
exceedance_prob = np.arange(1, n + 1) / n

# Convert to area
total_flooded_area = n * CELL_AREA_KM2
area_exceeded = exceedance_prob * total_flooded_area

# Plot exceedance curve
ax_exc.plot(sorted_depths, area_exceeded, color="#2c7fb8", linewidth=2)
ax_exc.fill_between(sorted_depths, area_exceeded, alpha=0.3, color="#2c7fb8")

# Mark depth thresholds
thresholds = [0.3, 0.5, 1.0]
colors_th = ["#fdae61", "#f46d43", "#d73027"]
labels_th = [">0.3 m (wading)", ">0.5 m (dangerous)", ">1.0 m (severe)"]

for i, (th, col, lab) in enumerate(zip(thresholds, colors_th, labels_th)):
    area_above = np.sum(depths_positive >= th) * CELL_AREA_KM2
    ax_exc.axvline(th, color=col, linestyle="--", linewidth=1.5, alpha=0.8)
    ax_exc.scatter([th], [area_above], color=col, s=80, zorder=5, edgecolor="black")
    ax_exc.annotate(f"{lab}\\n{area_above:.0f} km²",
                    xy=(th, area_above),
                    xytext=(th + 0.15, area_above + total_flooded_area * 0.08),
                    fontsize=8, color=col,
                    arrowprops=dict(arrowstyle="->", color=col, lw=0.8))

ax_exc.set_xlabel("Maximum flood depth (m)", fontsize=10)
ax_exc.set_ylabel("Flooded area exceeding depth (km²)", fontsize=10)
ax_exc.set_xlim(0, 2.0)
ax_exc.set_ylim(0, total_flooded_area * 1.1)
ax_exc.grid(True, alpha=0.3)

# Summary statistics
stats_text = (
    f"Total flooded area: {total_flooded_area:.0f} km²\\n"
    f"Mean max depth: {np.mean(depths_positive):.2f} m\\n"
    f"Max depth: {np.max(depths_positive):.2f} m\\n"
    f"Median max depth: {np.median(depths_positive):.2f} m"
)
ax_exc.text(0.95, 0.95, stats_text, transform=ax_exc.transAxes, fontsize=9,
            verticalalignment="top", horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

ax_exc.set_title("C. Depth exceedance curve & threshold areas", fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# FINAL ADJUSTMENTS
# ============================================================================
plt.suptitle("Figure 1: Shanghai 1905 Flood Event Overview", fontsize=12, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])

# Save figure
fig.savefig(f"{base_dir}/Fig1_Overview_NCities.pdf", dpi=300, bbox_inches="tight")
fig.savefig(f"{base_dir}/Fig1_Overview_NCities.png", dpi=300, bbox_inches="tight")

plt.show()

print("\\nFigure 1 saved to:")
print(f"  - {base_dir}/Fig1_Overview_NCities.pdf")
print(f"  - {base_dir}/Fig1_Overview_NCities.png")
'''

# ============================================================================
# CELL 5: FIGURE 2
# ============================================================================
figure2_source = '''"""
Figure 2: Flood Persistence - The Urban Signature of Failure
=============================================================
- Fig. 2A: Map of hours with depth > 0.3 m (Control scenario)
- Fig. 2B: Time series of area inundated > 0.3 m (city inundation curve)
- Fig. 2C: Snapshot just before storm tide arrival (preconditioning state)
- Fig. 2D: Distribution of flood duration

Uses pre-processed data from data processing cell.
"""

# ============================================================================
# FIGURE 2: FOUR-PANEL COMPOSITE
# ============================================================================
fig = plt.figure(figsize=(12, 10), dpi=150)

# Layout: Top row = 2A (map) + 2B (timeseries), Bottom row = 2C (pre-surge map) + 2D (histogram)
gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1],
                       hspace=0.25, wspace=0.25)

ax_duration = fig.add_subplot(gs[0, 0])   # 2A: duration map
ax_timeseries = fig.add_subplot(gs[0, 1]) # 2B: area timeseries
ax_presurge = fig.add_subplot(gs[1, 0])   # 2C: pre-surge snapshot
ax_histogram = fig.add_subplot(gs[1, 1])  # 2D: duration histogram

# ============================================================================
# PANEL 2A: MAP OF HOURS > 0.3 m (DURATION MAP)
# ============================================================================
setup_map_ax(ax_duration)

norm_duration = mcolors.Normalize(vmin=0, vmax=200)
duration_gdf = scenario_data["ctrl"]["duration_gdf"]
hb_dur = plot_hexbin_map(ax_duration, duration_gdf, "hours_above", CMAP_DURATION, norm_duration)

cbar_dur = plt.colorbar(hb_dur, ax=ax_duration, orientation="vertical", shrink=0.7, pad=0.02, extend='max')
cbar_dur.set_label(f"Hours with depth > {DEPTH_THRESHOLD} m", fontsize=9)

ax_duration.legend(handles=LEGEND_ELEMENTS, loc='lower center', ncol=2, fontsize=7,
                   frameon=True, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

ax_duration.set_title(f"A. Flood duration: hours with depth > {DEPTH_THRESHOLD} m",
                      fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 2B: TIME SERIES OF INUNDATED AREA
# ============================================================================
area_ts_df = scenario_data["ctrl"]["area_ts_df"]

ax_timeseries.fill_between(area_ts_df["datetime"], area_ts_df["area_km2"],
                           alpha=0.3, color="#2c7fb8")
ax_timeseries.plot(area_ts_df["datetime"], area_ts_df["area_km2"],
                   color="#2c7fb8", linewidth=1.5)

# Mark key events
event_dates = [
    (pd.Timestamp("1905-08-21 12:00"), "Predecessor\\nRain #1", "green"),
    (pd.Timestamp("1905-08-28 12:00"), "Predecessor\\nRain #2", "orange"),
    (pd.Timestamp("1905-09-01 12:00"), "Typhoon\\nSurge", "red"),
]

for event_time, label, color in event_dates:
    ax_timeseries.axvline(event_time, color=color, linestyle="--", linewidth=1, alpha=0.7)
    y_pos = area_ts_df["area_km2"].max() * 0.95
    ax_timeseries.text(event_time, y_pos, label, color=color, fontsize=8,
                       ha='center', va='top', rotation=0)

# Mark pre-surge snapshot
ax_timeseries.axvline(PRE_SURGE_TIME, color="purple", linestyle=":", linewidth=2)
ax_timeseries.text(PRE_SURGE_TIME, area_ts_df["area_km2"].max() * 0.5,
                   "Pre-surge\\nsnapshot", color="purple", fontsize=8, ha='right', va='center')

ax_timeseries.set_xlabel("Date (1905)", fontsize=10)
ax_timeseries.set_ylabel(f"Area with depth > {DEPTH_THRESHOLD} m (km²)", fontsize=10)
ax_timeseries.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax_timeseries.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
plt.setp(ax_timeseries.xaxis.get_majorticklabels(), rotation=45, ha='right')
ax_timeseries.set_xlim(area_ts_df["datetime"].min(), area_ts_df["datetime"].max())
ax_timeseries.set_ylim(0, area_ts_df["area_km2"].max() * 1.1)
ax_timeseries.grid(True, alpha=0.3)

# Add statistics
peak_area = area_ts_df["area_km2"].max()
peak_time = area_ts_df.loc[area_ts_df["area_km2"].idxmax(), "datetime"]
mean_area = area_ts_df["area_km2"].mean()

stats_text = (
    f"Peak area: {peak_area:.0f} km²\\n"
    f"Peak time: {peak_time.strftime('%m/%d %H:00')}\\n"
    f"Mean area: {mean_area:.0f} km²"
)
ax_timeseries.text(0.02, 0.98, stats_text, transform=ax_timeseries.transAxes, fontsize=9,
                   verticalalignment="top", horizontalalignment="left",
                   bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

ax_timeseries.set_title(f"B. City inundation curve: area > {DEPTH_THRESHOLD} m over time",
                        fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 2C: PRE-SURGE SNAPSHOT
# ============================================================================
setup_map_ax(ax_presurge)

norm_depth = mcolors.Normalize(vmin=0, vmax=2.0)
presurge_gdf = scenario_data["ctrl"]["presurge_gdf"]
hb_presurge = plot_hexbin_map(ax_presurge, presurge_gdf, "depth", CMAP_DEPTH, norm_depth)

cbar_presurge = plt.colorbar(hb_presurge, ax=ax_presurge, orientation="vertical", shrink=0.7, pad=0.02, extend='max')
cbar_presurge.set_label("Water Depth (m)", fontsize=9)

ax_presurge.legend(handles=LEGEND_ELEMENTS, loc='lower center', ncol=2, fontsize=7,
                   frameon=True, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

presurge_flooded = scenario_data["ctrl"]["presurge_metrics"]["inundated_area_km2"]
ax_presurge.set_title(f"C. Pre-surge state ({PRE_SURGE_TIME.strftime('%b %d %H:00')}): {presurge_flooded:.0f} km² flooded",
                      fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 2D: DURATION HISTOGRAM
# ============================================================================
duration_values = duration_gdf["hours_above"].values
ax_histogram.hist(duration_values, bins=30, color="#2c7fb8", alpha=0.7, edgecolor="black")
ax_histogram.set_xlabel("Hours with depth > 0.3 m", fontsize=10)
ax_histogram.set_ylabel("Number of grid cells", fontsize=10)
ax_histogram.set_title("D. Distribution of flood duration", fontsize=10, fontweight="bold", loc="left")
ax_histogram.grid(True, alpha=0.3)

# Add statistics
median_dur = np.median(duration_values)
mean_dur = np.mean(duration_values)
max_dur = np.max(duration_values)

stats_text_dur = (
    f"Median: {median_dur:.0f} hours\\n"
    f"Mean: {mean_dur:.0f} hours\\n"
    f"Max: {max_dur:.0f} hours\\n"
    f"Cells affected: {len(duration_values)}"
)
ax_histogram.text(0.95, 0.95, stats_text_dur, transform=ax_histogram.transAxes, fontsize=9,
                  verticalalignment="top", horizontalalignment="right",
                  bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

# ============================================================================
# FINAL ADJUSTMENTS
# ============================================================================
plt.suptitle("Figure 2: Flood Persistence - Duration and Preconditioning",
             fontsize=12, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])

# Save figure
fig.savefig(f"{base_dir}/Fig2_Persistence_NCities.pdf", dpi=300, bbox_inches="tight")
fig.savefig(f"{base_dir}/Fig2_Persistence_NCities.png", dpi=300, bbox_inches="tight")

plt.show()

print("\\nFigure 2 saved to:")
print(f"  - {base_dir}/Fig2_Persistence_NCities.pdf")
print(f"  - {base_dir}/Fig2_Persistence_NCities.png")
'''

# ============================================================================
# CELL 6: FIGURE 3
# ============================================================================
figure3_source = '''"""
Figure 3: Asymmetric Preconditioning from Multi-day Sequencing (Nature Cities)
==============================================================================
- Fig. 3A: Bar chart of pre-surge inundated area and stored-water proxy for Control, No-Rain-1, No-Rain-2
- Fig. 3B: Difference map (No-Rain-2 minus Control) for flood duration with depth > 0.3m (time 0 to pre-surge)
- Fig. 3C: Difference map (No-Rain-2 minus Control) for flood depth at pre-surge timestamp

Uses pre-processed data from data processing cell.
"""

# ============================================================================
# COMPUTE DIFFERENCE MAPS (No-Rain-2 minus Control)
# ============================================================================
print("Computing difference maps (No-Rain-2 minus Control)...")

# Duration difference (pre-surge)
ctrl_dur = scenario_data["ctrl"]["duration_presurge_gdf"].copy()
norain2_dur = scenario_data["norain2"]["duration_presurge_gdf"].copy()

ctrl_dur["coord_key"] = list(zip(ctrl_dur.geometry.x, ctrl_dur.geometry.y))
norain2_dur["coord_key"] = list(zip(norain2_dur.geometry.x, norain2_dur.geometry.y))

dur_merged = norain2_dur.merge(
    ctrl_dur[["coord_key", "hours_above"]],
    on="coord_key",
    how="outer",
    suffixes=("_norain2", "_ctrl")
)
dur_merged["hours_above_norain2"] = dur_merged["hours_above_norain2"].fillna(0)
dur_merged["hours_above_ctrl"] = dur_merged["hours_above_ctrl"].fillna(0)
dur_merged["duration_diff"] = dur_merged["hours_above_norain2"] - dur_merged["hours_above_ctrl"]

dur_merged_gdf = gpd.GeoDataFrame(dur_merged, geometry="geometry", crs=norain2_dur.crs)

# Depth difference at pre-surge
ctrl_presurge = scenario_data["ctrl"]["presurge_gdf"].copy()
norain2_presurge = scenario_data["norain2"]["presurge_gdf"].copy()

ctrl_presurge["coord_key"] = list(zip(ctrl_presurge.geometry.x, ctrl_presurge.geometry.y))
norain2_presurge["coord_key"] = list(zip(norain2_presurge.geometry.x, norain2_presurge.geometry.y))

depth_merged = norain2_presurge.merge(
    ctrl_presurge[["coord_key", "depth"]],
    on="coord_key",
    how="outer",
    suffixes=("_norain2", "_ctrl")
)
depth_merged["depth_norain2"] = depth_merged["depth_norain2"].fillna(0)
depth_merged["depth_ctrl"] = depth_merged["depth_ctrl"].fillna(0)
depth_merged["depth_diff"] = depth_merged["depth_norain2"] - depth_merged["depth_ctrl"]

depth_merged_gdf = gpd.GeoDataFrame(depth_merged, geometry="geometry", crs=norain2_presurge.crs)

print(f"Duration difference range: {dur_merged['duration_diff'].min():.0f} to {dur_merged['duration_diff'].max():.0f} hours")
print(f"Depth difference range: {depth_merged['depth_diff'].min():.2f} to {depth_merged['depth_diff'].max():.2f} m")

# ============================================================================
# FIGURE 3: THREE-PANEL COMPOSITE
# ============================================================================
fig = plt.figure(figsize=(12, 10), dpi=150)

gs = gridspec.GridSpec(2, 2, height_ratios=[0.7, 1.2], width_ratios=[1, 1],
                       hspace=0.30, wspace=0.25)

ax_bar = fig.add_subplot(gs[0, :])      # 3A: bar chart (spans full width)
ax_dur_diff = fig.add_subplot(gs[1, 0])  # 3B: duration difference map
ax_depth_diff = fig.add_subplot(gs[1, 1]) # 3C: depth difference map

# ============================================================================
# PANEL 3A: BAR CHART OF PRE-SURGE METRICS
# ============================================================================
scenario_names = ["ctrl", "norain1", "norain2"]
display_names = ["Control", "No-Rain-1", "No-Rain-2"]

inundated_areas = [scenario_data[s]["presurge_metrics"]["inundated_area_km2"] for s in scenario_names]
stored_waters = [scenario_data[s]["presurge_metrics"]["stored_water_million_m3"] for s in scenario_names]

x = np.arange(len(display_names))
width = 0.35

ax_bar2 = ax_bar.twinx()

bars1 = ax_bar.bar(x - width/2, inundated_areas, width, label='Inundated Area (km²)',
                   color='steelblue', alpha=0.8)
bars2 = ax_bar2.bar(x + width/2, stored_waters, width, label='Stored Water (million m³)',
                    color='coral', alpha=0.8)

ax_bar.set_ylabel('Inundated Area (km²)', color='steelblue', fontsize=10)
ax_bar2.set_ylabel('Stored Water (million m³)', color='coral', fontsize=10)
ax_bar.tick_params(axis='y', labelcolor='steelblue')
ax_bar2.tick_params(axis='y', labelcolor='coral')

ax_bar.set_xticks(x)
ax_bar.set_xticklabels(display_names, fontsize=10)
ax_bar.set_xlabel('Scenario', fontsize=10)

for bar, val in zip(bars1, inundated_areas):
    ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{val:.0f}', ha='center', va='bottom', fontsize=9, color='steelblue')

for bar, val in zip(bars2, stored_waters):
    ax_bar2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f'{val:.1f}', ha='center', va='bottom', fontsize=9, color='coral')

lines1, labels1 = ax_bar.get_legend_handles_labels()
lines2, labels2 = ax_bar2.get_legend_handles_labels()
ax_bar.legend(lines1 + lines2, labels1 + labels2, loc='upper right', frameon=True)

ax_bar.set_title(f"A. Pre-surge preconditioning metrics at {PRE_SURGE_TIME.strftime('%Y-%m-%d %H:%M')}",
                 fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 3B: DURATION DIFFERENCE MAP
# ============================================================================
setup_map_ax(ax_dur_diff)

max_abs_dur = max(abs(dur_merged["duration_diff"].min()), abs(dur_merged["duration_diff"].max()))
if max_abs_dur == 0:
    max_abs_dur = 1
norm_dur = mcolors.TwoSlopeNorm(vmin=-max_abs_dur, vcenter=0, vmax=max_abs_dur)

hb_dur = plot_hexbin_map(ax_dur_diff, dur_merged_gdf, "duration_diff", CMAP_DIFF, norm_dur)

cbar_dur = plt.colorbar(hb_dur, ax=ax_dur_diff, orientation="vertical", shrink=0.7, pad=0.02, extend='both')
cbar_dur.set_label(f"Duration difference (hours, depth > {DEPTH_THRESHOLD} m)", fontsize=9)

ax_dur_diff.legend(handles=LEGEND_ELEMENTS, loc='lower center', ncol=2, fontsize=7,
                   frameon=True, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

ax_dur_diff.set_title(f"B. Duration difference (No-Rain-2 − Control)\\nt=0 to {PRE_SURGE_TIME.strftime('%m-%d %H:%M')}",
                      fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 3C: DEPTH DIFFERENCE MAP AT PRE-SURGE
# ============================================================================
setup_map_ax(ax_depth_diff)

max_abs_depth = max(abs(depth_merged["depth_diff"].min()), abs(depth_merged["depth_diff"].max()))
if max_abs_depth == 0:
    max_abs_depth = 0.1
norm_depth = mcolors.TwoSlopeNorm(vmin=-max_abs_depth, vcenter=0, vmax=max_abs_depth)

hb_depth = plot_hexbin_map(ax_depth_diff, depth_merged_gdf, "depth_diff", CMAP_DIFF, norm_depth)

cbar_depth = plt.colorbar(hb_depth, ax=ax_depth_diff, orientation="vertical", shrink=0.7, pad=0.02, extend='both')
cbar_depth.set_label("Depth difference (m)", fontsize=9)

ax_depth_diff.legend(handles=LEGEND_ELEMENTS, loc='lower center', ncol=2, fontsize=7,
                     frameon=True, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

ax_depth_diff.set_title(f"C. Depth difference at pre-surge\\n({PRE_SURGE_TIME.strftime('%Y-%m-%d %H:%M')})",
                        fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# FINAL ADJUSTMENTS
# ============================================================================
plt.suptitle("Figure 3: Asymmetric Preconditioning from Multi-day Sequencing",
             fontsize=12, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])

fig.savefig(f"{base_dir}/Fig3_Preconditioning_NCities.pdf", dpi=300, bbox_inches="tight")
fig.savefig(f"{base_dir}/Fig3_Preconditioning_NCities.png", dpi=300, bbox_inches="tight")

plt.show()

print("\\n" + "="*60)
print("SUMMARY OF RESULTS")
print("="*60)
for i, scenario_name in enumerate(scenario_names):
    m = scenario_data[scenario_name]["presurge_metrics"]
    print(f"\\n{display_names[i]}:")
    print(f"  Inundated area (>{DEPTH_THRESHOLD}m): {m['inundated_area_km2']:.1f} km²")
    print(f"  Stored water: {m['stored_water_million_m3']:.2f} million m³")

print(f"\\nDifference (No-Rain-2 - Control):")
print(f"  Inundated area: {scenario_data['norain2']['presurge_metrics']['inundated_area_km2'] - scenario_data['ctrl']['presurge_metrics']['inundated_area_km2']:.1f} km²")
print(f"  Stored water: {scenario_data['norain2']['presurge_metrics']['stored_water_million_m3'] - scenario_data['ctrl']['presurge_metrics']['stored_water_million_m3']:.2f} million m³")

print("\\nFigure 3 saved to:")
print(f"  - {base_dir}/Fig3_Preconditioning_NCities.pdf")
print(f"  - {base_dir}/Fig3_Preconditioning_NCities.png")
'''

# ============================================================================
# CELL 7: FIGURE 4
# ============================================================================
figure4_source = '''"""
Figure 4: Tide-locking as a Drainage Failure Mode (Nature Cities)
=================================================================
- Fig. 4A: Water-level time series showing spring vs neap tide relative to interior stages
- Fig. 4B: Control vs Neap-Tide (lowtide) inundation area time series and recession comparison
- Fig. 4C: Neap-Tide minus Control duration difference map

Uses pre-processed data from data processing cell.
Uses simulated water level from wusongkou_simulated files for Fig. 4A.
Uses astronomical tide from Wusong_tide_modeling file for neap tide reference.
"""

# Interior outfall stage (representative threshold for tide-locking)
INTERIOR_OUTFALL_STAGE = 3.0  # meters

# ============================================================================
# COMPUTE TIDE-LOCKING INDEX
# ============================================================================
print("Computing Tide-Locking Index...")

# Load simulated water levels for control and lowtide (neap)
wusong_ctrl = wusong_simulated["ctrl"].copy()
wusong_neap = wusong_simulated["lowtide"].copy()

# Filter to simulation period
sim_end = SIM_START + pd.Timedelta(hours=N_TIMESTEPS-1)

# Hours above outfall stage
hours_above_outfall_ctrl = (wusong_ctrl["water_depth_m"] >= INTERIOR_OUTFALL_STAGE).sum()
hours_above_outfall_neap = (wusong_neap["water_depth_m"] >= INTERIOR_OUTFALL_STAGE).sum()

tide_lock_fraction_ctrl = hours_above_outfall_ctrl / len(wusong_ctrl) if len(wusong_ctrl) > 0 else 0
tide_lock_fraction_neap = hours_above_outfall_neap / len(wusong_neap) if len(wusong_neap) > 0 else 0

print(f"Tide-locking fraction (Control): {tide_lock_fraction_ctrl:.2%} ({hours_above_outfall_ctrl} hours)")
print(f"Tide-locking fraction (Neap-Tide): {tide_lock_fraction_neap:.2%} ({hours_above_outfall_neap} hours)")

# Head difference integral
head_diff_ctrl = np.maximum(0, wusong_ctrl["water_depth_m"].values - INTERIOR_OUTFALL_STAGE)
head_diff_neap = np.maximum(0, wusong_neap["water_depth_m"].values - INTERIOR_OUTFALL_STAGE)

integral_ctrl = np.sum(head_diff_ctrl)  # meter-hours
integral_neap = np.sum(head_diff_neap)

print(f"Head difference integral (Control): {integral_ctrl:.1f} m·h")
print(f"Head difference integral (Neap-Tide): {integral_neap:.1f} m·h")

# ============================================================================
# COMPUTE DIFFERENCE MAP (Neap-Tide minus Control)
# ============================================================================
print("\\nComputing duration difference map...")

ctrl_dur = scenario_data["ctrl"]["duration_gdf"].copy()
neap_dur = scenario_data["lowtide"]["duration_gdf"].copy()

ctrl_dur["coord_key"] = list(zip(ctrl_dur.geometry.x, ctrl_dur.geometry.y))
neap_dur["coord_key"] = list(zip(neap_dur.geometry.x, neap_dur.geometry.y))

dur_merged = neap_dur.merge(
    ctrl_dur[["coord_key", "hours_above"]],
    on="coord_key",
    how="outer",
    suffixes=("_neap", "_ctrl")
)
dur_merged["hours_above_neap"] = dur_merged["hours_above_neap"].fillna(0)
dur_merged["hours_above_ctrl"] = dur_merged["hours_above_ctrl"].fillna(0)
dur_merged["duration_diff"] = dur_merged["hours_above_neap"] - dur_merged["hours_above_ctrl"]

dur_merged_gdf = gpd.GeoDataFrame(dur_merged, geometry="geometry", crs=neap_dur.crs)

print(f"Duration difference range: {dur_merged['duration_diff'].min():.0f} to {dur_merged['duration_diff'].max():.0f} hours")

# ============================================================================
# RECESSION ANALYSIS
# ============================================================================
print("\\nAnalyzing recession curves...")

ctrl_ts = scenario_data["ctrl"]["area_ts_df"]
neap_ts = scenario_data["lowtide"]["area_ts_df"]

ctrl_peak_idx = ctrl_ts["area_km2"].idxmax()
neap_peak_idx = neap_ts["area_km2"].idxmax()

ctrl_peak_time = ctrl_ts.loc[ctrl_peak_idx, "datetime"]
neap_peak_time = neap_ts.loc[neap_peak_idx, "datetime"]
ctrl_peak_area = ctrl_ts.loc[ctrl_peak_idx, "area_km2"]
neap_peak_area = neap_ts.loc[neap_peak_idx, "area_km2"]

print(f"Control peak: {ctrl_peak_area:.1f} km² at {ctrl_peak_time}")
print(f"Neap-Tide peak: {neap_peak_area:.1f} km² at {neap_peak_time}")

# ============================================================================
# FIGURE 4: THREE-PANEL COMPOSITE
# ============================================================================
fig = plt.figure(figsize=(12, 10), dpi=150)

gs = gridspec.GridSpec(2, 2, height_ratios=[0.8, 1.2], width_ratios=[1, 1],
                       hspace=0.30, wspace=0.25)

ax_tide = fig.add_subplot(gs[0, 0])      # 4A: tide time series
ax_recession = fig.add_subplot(gs[0, 1]) # 4B: recession curves
ax_map = fig.add_subplot(gs[1, :])       # 4C: difference map (full width)

# ============================================================================
# PANEL 4A: WATER LEVEL TIME SERIES
# ============================================================================
plot_start = pd.Timestamp("1905-08-28")
plot_end = pd.Timestamp("1905-09-05")

ctrl_plot = wusong_ctrl[(wusong_ctrl["datetime"] >= plot_start) & (wusong_ctrl["datetime"] <= plot_end)]
neap_plot = wusong_neap[(wusong_neap["datetime"] >= plot_start) & (wusong_neap["datetime"] <= plot_end)]

ax_tide.plot(ctrl_plot["datetime"], ctrl_plot["water_depth_m"],
             color="#d62728", linewidth=1.5, label="Control (Simulated)")
ax_tide.plot(neap_plot["datetime"], neap_plot["water_depth_m"],
             color="#1f77b4", linewidth=1.5, label="Neap-Tide (Simulated)")

# Interior outfall threshold
ax_tide.axhline(INTERIOR_OUTFALL_STAGE, color="green", linestyle="--", linewidth=1.5,
                label=f"Outfall Stage ({INTERIOR_OUTFALL_STAGE} m)")

# Shade tide-locked periods (control above threshold)
for i in range(len(ctrl_plot) - 1):
    if ctrl_plot.iloc[i]["water_depth_m"] >= INTERIOR_OUTFALL_STAGE:
        ax_tide.axvspan(ctrl_plot.iloc[i]["datetime"],
                       ctrl_plot.iloc[i+1]["datetime"],
                       alpha=0.2, color="red")

ax_tide.set_xlabel("Date (1905)", fontsize=10)
ax_tide.set_ylabel("Simulated Water Level (m)", fontsize=10)
ax_tide.set_xlim(plot_start, plot_end)
ax_tide.set_ylim(0, ctrl_plot["water_depth_m"].max() * 1.1)

ax_tide.xaxis.set_major_locator(mdates.DayLocator())
ax_tide.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax_tide.tick_params(axis='x', rotation=45)

ax_tide.legend(loc='upper left', fontsize=8, frameon=True)
ax_tide.grid(True, alpha=0.3)

# Add tide-locking index annotation
tide_lock_text = (f"Tide-Lock Index:\\n"
                  f"Control: {tide_lock_fraction_ctrl:.0%}\\n"
                  f"Neap-Tide: {tide_lock_fraction_neap:.0%}")
ax_tide.text(0.98, 0.98, tide_lock_text, transform=ax_tide.transAxes, fontsize=8,
             verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

ax_tide.set_title("A. Simulated water level at Wusongkou: Control vs Neap-Tide",
                  fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 4B: INUNDATION AREA AND RECESSION CURVES
# ============================================================================
ax_recession.plot(ctrl_ts["datetime"], ctrl_ts["area_km2"],
                  color="#d62728", linewidth=1.5, label="Control")
ax_recession.plot(neap_ts["datetime"], neap_ts["area_km2"],
                  color="#1f77b4", linewidth=1.5, label="Neap-Tide Scenario")

# Mark peaks
ax_recession.scatter([ctrl_peak_time], [ctrl_peak_area], color="#d62728", s=80,
                     zorder=5, edgecolor='black', marker='o')
ax_recession.scatter([neap_peak_time], [neap_peak_area], color="#1f77b4", s=80,
                     zorder=5, edgecolor='black', marker='o')

# Mark typhoon arrival
typhoon_time = pd.Timestamp("1905-09-01 12:00")
ax_recession.axvline(typhoon_time, color="purple", linestyle=":", linewidth=1.5)
ax_recession.text(typhoon_time, ax_recession.get_ylim()[1]*0.95, "Typhoon\\nSurge",
                  color="purple", fontsize=8, ha='center', va='top')

ax_recession.set_xlabel("Date (1905)", fontsize=10)
ax_recession.set_ylabel(f"Inundated Area > {DEPTH_THRESHOLD} m (km²)", fontsize=10)
ax_recession.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax_recession.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax_recession.tick_params(axis='x', rotation=45)

ax_recession.legend(loc='upper left', fontsize=8, frameon=True)
ax_recession.grid(True, alpha=0.3)

# Summary statistics
diff_peak = ctrl_peak_area - neap_peak_area
stats_text = (f"Peak difference: {diff_peak:.0f} km²\\n"
              f"Control peak: {ctrl_peak_area:.0f} km²\\n"
              f"Neap peak: {neap_peak_area:.0f} km²")
ax_recession.text(0.98, 0.60, stats_text, transform=ax_recession.transAxes, fontsize=8,
                  verticalalignment='top', horizontalalignment='right',
                  bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

ax_recession.set_title("B. Inundated area time series: Control vs Neap-Tide",
                       fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# PANEL 4C: DURATION DIFFERENCE MAP
# ============================================================================
setup_map_ax(ax_map)

max_abs_dur = max(abs(dur_merged["duration_diff"].min()), abs(dur_merged["duration_diff"].max()))
if max_abs_dur == 0:
    max_abs_dur = 1
norm_dur = mcolors.TwoSlopeNorm(vmin=-max_abs_dur, vcenter=0, vmax=max_abs_dur)

hb = plot_hexbin_map(ax_map, dur_merged_gdf, "duration_diff", CMAP_DIFF, norm_dur)

cbar = plt.colorbar(hb, ax=ax_map, orientation="vertical", shrink=0.7, pad=0.02, extend='both')
cbar.set_label(f"Duration difference (hours, depth > {DEPTH_THRESHOLD} m)", fontsize=9)

ax_map.legend(handles=LEGEND_ELEMENTS, loc='lower center', ncol=4, fontsize=7,
              frameon=True, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

ax_map.set_title("C. Duration difference map (Neap-Tide − Control): Red = longer flooding under neap tide",
                 fontsize=10, fontweight="bold", loc="left")

# ============================================================================
# FINAL ADJUSTMENTS
# ============================================================================
plt.suptitle("Figure 4: Tide-locking as a Drainage Failure Mode",
             fontsize=12, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])

fig.savefig(f"{base_dir}/Fig4_TideLocking_NCities.pdf", dpi=300, bbox_inches="tight")
fig.savefig(f"{base_dir}/Fig4_TideLocking_NCities.png", dpi=300, bbox_inches="tight")

plt.show()

# ============================================================================
# SUMMARY
# ============================================================================
print("\\n" + "="*60)
print("SUMMARY: TIDE-LOCKING ANALYSIS")
print("="*60)
print(f"\\nTide-Locking Index (hours above {INTERIOR_OUTFALL_STAGE}m outfall):")
print(f"  Control: {tide_lock_fraction_ctrl:.1%} ({hours_above_outfall_ctrl} hours)")
print(f"  Neap-Tide: {tide_lock_fraction_neap:.1%} ({hours_above_outfall_neap} hours)")
print(f"\\nHead difference integral:")
print(f"  Control: {integral_ctrl:.1f} m·h")
print(f"  Neap-Tide: {integral_neap:.1f} m·h")
print(f"\\nPeak inundation:")
print(f"  Control: {ctrl_peak_area:.0f} km² at {ctrl_peak_time}")
print(f"  Neap-Tide: {neap_peak_area:.0f} km² at {neap_peak_time}")
print(f"  Difference: {diff_peak:.0f} km²")

print("\\nFigure 4 saved to:")
print(f"  - {base_dir}/Fig4_TideLocking_NCities.pdf")
print(f"  - {base_dir}/Fig4_TideLocking_NCities.png")
'''

# ============================================================================
# BUILD NEW NOTEBOOK
# ============================================================================
# Create new cells list
new_cells = [
    header_cell,
    make_code_cell(data_processing_source, "data-processing"),
    make_code_cell(wusongkou_extraction_source, "wusongkou-extraction"),
    make_code_cell(map_config_source, "map-config"),
    make_code_cell(figure1_source, "figure1"),
    make_code_cell(figure2_source, "figure2"),
    make_code_cell(figure3_source, "figure3"),
    make_code_cell(figure4_source, "figure4"),
]

# Add rest of cells from original notebook
new_cells.extend(rest_cells)

# Create new notebook
new_nb = {
    "nbformat": nb["nbformat"],
    "nbformat_minor": nb["nbformat_minor"],
    "metadata": nb["metadata"],
    "cells": new_cells
}

# Fix source format - should be list of strings with newlines
def fix_source(cells):
    for cell in cells:
        if isinstance(cell.get("source"), list):
            # Ensure each line ends with newline except last
            new_source = []
            for i, line in enumerate(cell["source"]):
                if not line.endswith("\n") and i < len(cell["source"]) - 1:
                    new_source.append(line + "\n")
                else:
                    new_source.append(line)
            cell["source"] = new_source
    return cells

new_nb["cells"] = fix_source(new_nb["cells"])

# Save new notebook
output_path = "/Users/shwang/sandbox/shanghai/Untitled_NCities.ipynb"
with open(output_path, "w") as f:
    json.dump(new_nb, f, indent=1)

print(f"Restructured notebook saved to: {output_path}")
print(f"Total cells: {len(new_nb['cells'])}")
print("\nNew cell structure:")
for i, cell in enumerate(new_nb["cells"][:8]):
    cell_type = cell["cell_type"]
    cell_id = cell.get("id", "no-id")
    preview = "".join(cell["source"][:1])[:50] if cell["source"] else "(empty)"
    print(f"  {i}: [{cell_type}] {cell_id} - {preview}...")
