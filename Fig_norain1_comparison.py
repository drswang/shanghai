"""
5 rows × 4 columns comparison.
  Row 1: proc 1  (new_postproc1/infil_7_890_rain)
  Row 2: proc 2  (new_postproc2/infil_7_890_rain)
  Row 3: proc 3  (new_postproc3/infil_7_890_rain)
  Row 4: proc 4  (new_postproc4/infil_7_890_rain)
  Row 5: proc 5  — no stone  (new_postproc5/infil_7_890_rain)

Timesteps (verified against original fig files by depth correlation):
  t49  → Predecessor Rain #1  (Aug 21 00:00)
  t90  → Predecessor Rain #2  (Aug 22 17:00)
  t275 → Before Typhoon Impact (Aug 30 10:00)
  t357 → After Typhoon Impact  (Sep 02 20:00)
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from shapely.geometry import MultiPolygon, LineString
from pyproj import Transformer
import contextily as ctx
import matplotlib as mpl

mpl.rcParams.update({"font.size": 8})

# ── Paths ──────────────────────────────────────────────────────────────────
BASE       = "/Users/shuaiwang/sandbox/shanghai"
SHAPE_DIR  = f"{BASE}/map/1910map/shape"
GADM_PATH  = "/Users/shuaiwang/sandbox/data/borders/gadm36.shp"
RIVER_DIR  = f"{BASE}/市管河道/"
RIVER_MASK = f"{BASE}/river_mask.xyz"

SCENARIOS = [
    (f"{BASE}/postproc/new_postproc1/infil_7_890_rain/text", "proc 1"),
    (f"{BASE}/postproc/new_postproc2/infil_7_890_rain/text", "proc 2"),
    (f"{BASE}/postproc/new_postproc3/infil_7_890_rain/text", "proc 3"),
    (f"{BASE}/postproc/new_postproc4/infil_7_890_rain/text", "proc 4"),
    (f"{BASE}/postproc/new_postproc5/infil_7_890_rain/text", "proc 5\n(no stone)"),
]

TIMESTEPS   = [49, 90, 275, 357]
COL_TITLES  = ["Predecessor\nRain #1", "Predecessor\nRain #2",
               "Before\nTyphoon Impact", "After\nTyphoon Impact"]
SNAP_TIMES  = ["Aug 21 00:00", "Aug 22 17:00", "Aug 30 10:00", "Sep 02 20:00"]
PANEL_LABELS = ["b", "c", "d", "e"]

# ── Static layers ──────────────────────────────────────────────────────────
print("Loading static layers…")
圩塘     = gpd.read_file(f"{SHAPE_DIR}/圩塘.shp")
海岸线   = gpd.read_file(f"{SHAPE_DIR}/海岸线.shp")
钦公塘   = gpd.read_file(f"{SHAPE_DIR}/钦公塘.shp")
雍正石塘 = gpd.read_file(f"{SHAPE_DIR}/雍正石塘.shp")
市管河道 = gpd.read_file(f"{RIVER_DIR}/市管河道.shp").set_crs(epsg=4326, inplace=False)

gadm         = gpd.read_file(GADM_PATH)
sh_parts     = gadm[(gadm["NAME_0"] == "China") & (gadm["NAME_2"] == "Shanghai")]
sh_dissolved = sh_parts.dissolve()
geom         = sh_dissolved.geometry.iloc[0]
if isinstance(geom, MultiPolygon):
    main_poly     = max(geom.geoms, key=lambda p: p.area)
    shanghai_main = gpd.GeoDataFrame(geometry=[main_poly], crs=sh_dissolved.crs)
else:
    shanghai_main = sh_dissolved

other_regions        = gadm[(gadm["NAME_0"] == "China") & (gadm["NAME_2"] != "Shanghai")]
china_other          = other_regions.dissolve()
shanghai_boundary    = gpd.GeoDataFrame(geometry=shanghai_main.boundary, crs=shanghai_main.crs)
china_other_boundary = gpd.GeoDataFrame(geometry=china_other.boundary, crs=china_other.crs)
inland_border        = gpd.overlay(shanghai_boundary, china_other_boundary, how="intersection")

river_mask_df = pd.read_csv(RIVER_MASK, sep=r"\s+", header=None, names=["lon", "lat", "depth"])
river_coords  = set(zip(river_mask_df["lon"], river_mask_df["lat"]))

for layer in [圩塘, 海岸线, 钦公塘, 雍正石塘, 市管河道, shanghai_main, inland_border]:
    layer.to_crs(epsg=3857, inplace=True)

# ── Coastline inland filter ─────────────────────────────────────────────────
coastline_line = 海岸线.geometry.union_all()
if coastline_line.geom_type == "MultiLineString":
    coastline_line = LineString(
        np.concatenate([np.array(g.coords) for g in coastline_line.geoms])
    )
coast_coords = np.array(coastline_line.coords)
coast_coords = coast_coords[np.argsort(coast_coords[:, 1])]
unique_lat, idx = np.unique(coast_coords[:, 1], return_index=True)
interp_func = dict(zip(unique_lat, coast_coords[idx, 0]))

def clean_outsiders(gdf):
    pts = gdf.copy()
    pts["coast_x"] = np.interp(
        pts.geometry.y,
        np.array(list(interp_func.keys())),
        np.array(list(interp_func.values()))
    )
    return pts[pts.geometry.x <= pts["coast_x"]].copy()

def load_timestep(text_dir, t):
    path = os.path.join(text_dir, f"t{t}.xyz")
    df   = pd.read_csv(path, sep=r"\s+", header=None, names=["lon", "lat", "depth"])
    df   = df[~df[["lon", "lat"]].apply(tuple, axis=1).isin(river_coords)]
    gdf  = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
    gdf  = gdf.to_crs(epsg=3857)
    return clean_outsiders(gdf)

# ── Colormap ───────────────────────────────────────────────────────────────
def shuai_colormap1():
    C1 = np.array([170, 219,  30]) / 255
    C2 = np.array([  2,   7,  93]) / 255
    C3 = np.array([  0, 183, 235]) / 255
    C9 = np.array([240, 255, 255]) / 255
    tmp1 = np.array([[np.linspace(C1[k], C2[k], 10)[i] for k in range(3)] for i in range(9)])
    tmp2 = np.array([[np.linspace(C2[k], C3[k],  8)[i] for k in range(3)] for i in range(7)])
    tmp4 = np.array([[np.linspace(C3[k], C9[k],  4)[i] for k in range(3)] for i in range(4)])
    cmap = mcolors.LinearSegmentedColormap.from_list("shuai", np.concatenate([tmp1, tmp2, tmp4]))
    return cmap.reversed()

cmap   = shuai_colormap1()
norm   = mcolors.Normalize(vmin=0, vmax=1.2)
bounds = np.arange(0, 1.3, 0.1)

# ── Map extent & ticks ─────────────────────────────────────────────────────
bounds4326          = shanghai_main.to_crs(epsg=4326).total_bounds
transformer_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
minx, miny = transformer_to_3857.transform(bounds4326[0] - .05, bounds4326[1] - .05)
maxx, maxy = transformer_to_3857.transform(bounds4326[2] + .05, bounds4326[3] + .05)

x_deg_ticks  = np.arange(np.floor(bounds4326[0]*5)/5, np.ceil(bounds4326[2]*5)/5 + 0.01, 0.4)
y_deg_ticks  = np.arange(np.floor(bounds4326[1]*5)/5, np.ceil(bounds4326[3]*5)/5 + 0.01, 0.4)
x_ticks_merc = [transformer_to_3857.transform(x, bounds4326[1])[0] for x in x_deg_ticks]
y_ticks_merc = [transformer_to_3857.transform(bounds4326[0], y)[1] for y in y_deg_ticks]
x_labels     = [f"{abs(round(x,2))}°E" for x in x_deg_ticks]
y_labels     = [f"{abs(round(y,2))}°N" for y in y_deg_ticks]

RIVERS_TO_SHOW    = ["黄浦江", "苏州河", "蕴藻浜", "淀浦河", "太浦河",
                      "拦路港", "斜塘", "横潦泾", "西泖河", "泖河", "竖潦泾"]
shanghai_main_3857 = shanghai_main.to_crs(epsg=3857)

# ── Figure ────────────────────────────────────────────────────────────────
n_rows = len(SCENARIOS)
fig, axes = plt.subplots(n_rows, 4, figsize=(14, n_rows * 3.5), dpi=300)
fig.subplots_adjust(wspace=0.05, hspace=0.08)

for row_idx, (text_dir, row_label) in enumerate(SCENARIOS):
    for col_idx, (t, col_title) in enumerate(zip(TIMESTEPS, COL_TITLES)):
        ax = axes[row_idx, col_idx]
        print(f"  {row_label}, t={t}…")

        gdf = load_timestep(text_dir, t)

        圩塘.plot(ax=ax, color="darkgoldenrod", edgecolor="none")
        钦公塘.plot(ax=ax, color="darkgoldenrod", edgecolor="none", lw=2)
        雍正石塘.plot(ax=ax, edgecolor="slategray", linewidth=3)
        海岸线.plot(ax=ax, edgecolor="black", linewidth=1, linestyle="dashed")
        inland_border.plot(ax=ax, edgecolor="black", linewidth=0.8)
        市管河道[市管河道["MC"].isin(RIVERS_TO_SHOW)].plot(
            ax=ax, edgecolor="magenta", linewidth=1, facecolor="none", zorder=20, alpha=0.5
        )
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels, attribution=False)

        depth_within = gpd.sjoin(gdf, shanghai_main_3857, how="inner", predicate="within")
        hb = ax.hexbin(
            depth_within.geometry.x, depth_within.geometry.y,
            C=depth_within["depth"], reduce_C_function=np.mean,
            gridsize=70, cmap=cmap, norm=norm, edgecolors="none", linewidths=0
        )
        hb.set_rasterized(True)

        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)
        ax.set_xticks(x_ticks_merc)
        ax.set_yticks(y_ticks_merc)
        ax.set_xticklabels([])
        ax.set_yticklabels([])

        if row_idx == n_rows - 1:
            ax.set_xticklabels(x_labels, fontsize=7)
            ax.tick_params(axis="x", rotation=45)
        if col_idx == 0:
            ax.set_yticklabels(y_labels, fontsize=7)
            ax.set_ylabel(row_label, fontsize=9, labelpad=6)

        ax.text(0.01, 0.98, PANEL_LABELS[col_idx], transform=ax.transAxes,
                fontsize=10, fontweight="bold", va="top", ha="left")
        ax.text(0.99, 0.98, SNAP_TIMES[col_idx], transform=ax.transAxes,
                fontsize=7, va="top", ha="right",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, ec="none"))

        if row_idx == 0:
            ax.set_title(col_title, fontsize=8, pad=4)

# ── Colorbar ──────────────────────────────────────────────────────────────
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar_ax = fig.add_axes([0.92, 0.06, 0.015, 0.88])
cbar = fig.colorbar(sm, cax=cbar_ax, ticks=bounds, extend="max")
cbar.set_label("Water Depth (m)", fontsize=8)

# ── Legend ────────────────────────────────────────────────────────────────
legend_elements = [
    Line2D([0], [0], color="darkgoldenrod", linewidth=2, label="Earthen Embankment"),
    Line2D([0], [0], color="slategray",     linewidth=3, label="Stone Embankment"),
    Line2D([0], [0], color="black", linestyle="dashed", linewidth=1, label="Coastline (1905)"),
    Line2D([0], [0], color="black",   linewidth=0.8, label="Shanghai Border"),
    Line2D([0], [0], color="magenta", linewidth=1,   label="River"),
]
fig.legend(handles=legend_elements, loc="lower center",
           bbox_to_anchor=(0.46, 0.01), ncol=5, fontsize=8, frameon=False)

out = f"{BASE}/Fig_norain1_comparison.png"
fig.savefig(out, format="png", bbox_inches="tight")
print(f"Saved: {out}")
plt.close(fig)
