"""
2×2 difference figure using new postproc simulations (bottom-right empty).
  a: proc3 (No Rain #1) − proc1 (CTRL)
  b: proc2 (No Rain #2) − proc1 (CTRL)
  c: proc4 (No Rain #1+2) − proc1 (CTRL)
Timestep: t357 (Sep 02 20:00, After Typhoon Impact)
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import pandas as pd
from shapely.geometry import MultiPolygon, LineString
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import numpy as np
import matplotlib as mpl
from scipy.stats import binned_statistic_2d
from pyproj import Transformer
from matplotlib.lines import Line2D

mpl.rcParams.update({'font.size': 8})

# ── Paths ──────────────────────────────────────────────────────────────────
BASE      = "/Users/shwang/sandbox/shanghai"
SHAPE_DIR = f"{BASE}/map/1910map/shape"
GADM_PATH = "/Users/shwang/sandbox/data/borders/gadm36.shp"
RIVER_DIR = f"{BASE}/市管河道/"
RIVER_MASK = f"{BASE}/river_mask.xyz"
T = 357

CTRL_PATH      = f"{BASE}/postproc/new_postproc1/infil_7_890_rain/text/t{T}.xyz"
NORAIN1_PATH   = f"{BASE}/postproc/new_postproc3/infil_7_890_rain/text/t{T}.xyz"  # proc3
NORAIN2_PATH   = f"{BASE}/postproc/new_postproc2/infil_7_890_rain/text/t{T}.xyz"  # proc2
NORAIN12_PATH  = f"{BASE}/postproc/new_postproc4/infil_7_890_rain/text/t{T}.xyz"  # proc4

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

# ── Coastline filter ───────────────────────────────────────────────────────
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

def load_xyz(path):
    df  = pd.read_csv(path, sep=r"\s+", header=None, names=["lon", "lat", "depth"])
    df  = df[~df[["lon", "lat"]].apply(tuple, axis=1).isin(river_coords)]
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
    gdf = gdf.to_crs(epsg=3857)
    return clean_outsiders(gdf)

print("Loading simulation data…")
ctrl_gdf     = load_xyz(CTRL_PATH)
norain1_gdf  = load_xyz(NORAIN1_PATH)
norain2_gdf  = load_xyz(NORAIN2_PATH)
norain12_gdf = load_xyz(NORAIN12_PATH)

# ── Colormap ───────────────────────────────────────────────────────────────
def shuai_colormap2():
    C1 = np.array([170, 219,  30]) / 255
    C2 = np.array([  2,   7,  93]) / 255
    C3 = np.array([  0, 183, 235]) / 255
    C6 = np.array([255,   0,   0]) / 255
    C7 = np.array([255, 233,   0]) / 255
    C8 = np.array([255, 240, 240]) / 255
    C9 = np.array([240, 255, 255]) / 255
    tmp1 = np.array([[np.linspace(C1[k], C2[k], 10)[i] for k in range(3)] for i in range(9)])
    tmp2 = np.array([[np.linspace(C2[k], C3[k],  8)[i] for k in range(3)] for i in range(7)])
    tmp4 = np.array([[np.linspace(C3[k], C9[k],  5)[i] for k in range(3)] for i in range(5)])
    tmp5 = np.array([[np.linspace(C8[k], C6[k], 10)[i] for k in range(3)] for i in range(9)])
    tmp6 = np.array([[np.linspace(C6[k], C7[k], 11)[i] for k in range(3)] for i in range(11)])
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "shuai2", np.concatenate([tmp1, tmp2, tmp4, tmp5, tmp6])
    )
    return cmap.reversed()

cmap   = shuai_colormap2()
norm   = mcolors.Normalize(vmin=-0.5, vmax=0.5)
bounds = np.arange(-0.5, 0.5 + 0.1, 0.1)

# ── Map extent & ticks ─────────────────────────────────────────────────────
bounds4326          = shanghai_main.to_crs(epsg=4326).total_bounds
transformer_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
minx, miny = transformer_to_3857.transform(bounds4326[0] - .05, bounds4326[1] - .05)
maxx, maxy = transformer_to_3857.transform(bounds4326[2] + .05, bounds4326[3] + .05)

x_deg_ticks  = np.arange(np.floor(bounds4326[0] * 5) / 5, np.ceil(bounds4326[2] * 5) / 5 + 0.01, 0.4)
y_deg_ticks  = np.arange(np.floor(bounds4326[1] * 5) / 5, np.ceil(bounds4326[3] * 5) / 5 + 0.01, 0.4)
x_ticks_merc = [transformer_to_3857.transform(x, bounds4326[1])[0] for x in x_deg_ticks]
y_ticks_merc = [transformer_to_3857.transform(bounds4326[0], y)[1] for y in y_deg_ticks]
x_labels     = [f"{abs(round(x, 2))}°E" for x in x_deg_ticks]
y_labels     = [f"{abs(round(y, 2))}°N" for y in y_deg_ticks]

RIVERS_TO_SHOW    = ["黄浦江", "苏州河", "蕴藻浜", "淀浦河", "太浦河",
                      "拦路港", "斜塘", "横潦泾", "西泖河", "泖河", "竖潦泾"]
shanghai_main_3857 = shanghai_main.to_crs(epsg=3857)

# ── Figure ─────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(7, 7))
gs  = gridspec.GridSpec(2, 2)
gs.update(wspace=0.05, hspace=0.08)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, 0])
# gs[1, 1] intentionally left empty

ctrl_within = gpd.sjoin(ctrl_gdf, shanghai_main_3857, how="inner", predicate="within")

panels = [
    (ax1, norain1_gdf,  "No Rain #1 − CTRL",   "a", True,  True),
    (ax2, norain2_gdf,  "No Rain #2 − CTRL",   "b", True,  False),
    (ax3, norain12_gdf, "No Rain #1+2 − CTRL", "c", False, True),
]

for ax, scen_gdf, title, label, show_x, show_y in panels:
    print(f"  Plotting {title}…")
    圩塘.plot(ax=ax, color="darkgoldenrod", edgecolor="none")
    钦公塘.plot(ax=ax, color="darkgoldenrod", edgecolor="none", lw=2)
    雍正石塘.plot(ax=ax, edgecolor="slategray", linewidth=3)
    海岸线.plot(ax=ax, edgecolor="black", linewidth=1, linestyle="dashed")
    inland_border.plot(ax=ax, edgecolor="black", linewidth=0.8)
    市管河道[市管河道["MC"].isin(RIVERS_TO_SHOW)].plot(
        ax=ax, edgecolor="magenta", linewidth=1, facecolor="none", zorder=20, alpha=0.5
    )
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels, attribution=False)

    scen_within = gpd.sjoin(scen_gdf, shanghai_main_3857, how="inner", predicate="within")

    x_all   = np.concatenate([scen_within.geometry.x.values, ctrl_within.geometry.x.values])
    y_all   = np.concatenate([scen_within.geometry.y.values, ctrl_within.geometry.y.values])
    x_range = [x_all.min(), x_all.max()]
    y_range = [y_all.min(), y_all.max()]

    gridsize = 70
    stat_s, xedges, yedges, _ = binned_statistic_2d(
        scen_within.geometry.x, scen_within.geometry.y, scen_within["depth"],
        statistic="mean", bins=int(gridsize * 1.5), range=[x_range, y_range]
    )
    stat_c, _, _, _ = binned_statistic_2d(
        ctrl_within.geometry.x, ctrl_within.geometry.y, ctrl_within["depth"],
        statistic="mean", bins=[xedges, yedges]
    )
    diff = np.nan_to_num(stat_s, nan=0) - np.nan_to_num(stat_c, nan=0)

    x_centers = (xedges[:-1] + xedges[1:]) / 2
    y_centers = (yedges[:-1] + yedges[1:]) / 2
    Xc, Yc   = np.meshgrid(x_centers, y_centers)
    x_flat, y_flat, z_flat = Xc.ravel(), Yc.ravel(), diff.T.ravel()
    mask = abs(z_flat) > 0.01

    hb = ax.hexbin(
        x_flat[mask], y_flat[mask], C=z_flat[mask],
        gridsize=gridsize, cmap=cmap, norm=norm,
        reduce_C_function=np.mean, edgecolors="none"
    )
    hb.set_rasterized(True)

    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_xticks(x_ticks_merc)
    ax.set_yticks(y_ticks_merc)
    ax.set_xticklabels(x_labels if show_x else [], fontsize=7)
    ax.set_yticklabels(y_labels if show_y else [], fontsize=7)
    if show_x:
        ax.tick_params(axis="x", rotation=45)

    ax.text(0.01, 0.98, label, transform=ax.transAxes,
            fontsize=10, fontweight="bold", va="top", ha="left")
    ax.text(0.99, 0.98, title, transform=ax.transAxes,
            fontsize=8, ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, ec="none"))

# ── Colorbar ──────────────────────────────────────────────────────────────
cbar_ax = fig.add_axes([0.92, ax3.get_position().y0, 0.015,
                         ax1.get_position().y1 - ax3.get_position().y0])
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, cax=cbar_ax, ticks=bounds, extend="both")
cbar.set_label("Change in Water Depth (m)", fontsize=8)

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

out = f"{BASE}/Fig_Diff_new.png"
fig.savefig(out, format="png", dpi=200, bbox_inches="tight")
print(f"Saved: {out}")
plt.close(fig)
