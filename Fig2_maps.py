#!/usr/bin/env python3
"""
Figure 2 — simulated water depth (control) at four stages:
  (a) after predecessor rain #1 (Aug 21),  (b) after predecessor rain #2 (Aug 28),
  (c) before typhoon impact (Sep 1),        (d) after typhoon impact (Sep 2).

Extracted verbatim from Untitled.ipynb (cell 8, the ax2-ax5 map panels of the
overview figure); tidied for standalone use: paths -> shuaiwang, rainfall/tide
(ax1) code removed, headless backend + savefig. The 5-panel gridspec is kept
(ax1 created empty then deleted) so the colorbar/layout match the manuscript.

Run:  ~/anaconda3/bin/python Fig2_maps.py   ->  Fig2_maps.{pdf,png}
Note: uses contextily basemap tiles (needs internet).
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import contextily as ctx
from shapely.geometry import MultiPolygon, LineString
from pyproj import Transformer
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

plt.rcParams.update({"font.size": 8})

# ── Paths ───────────────────────────────────────────────────────────────────
BASE = "/Users/shuaiwang/sandbox/shanghai"
shape_dir = f"{BASE}/map/1910map/shape"
gadm_path = "/Users/shuaiwang/sandbox/data/borders/gadm36.shp"
# NEW simulation control run (new_postproc1). Timesteps matched to the old
# figure snapshots (fig3a=t73, fig3b=t241, fig3c=t313, fig124a3d=t358).
NEWCTRL = f"{BASE}/postproc/new_postproc1/infil_7_890_rain/text"
depth_csv_path = f"{NEWCTRL}/t358.xyz"   # (d) after typhoon  (Sep 2)
xyz1_path = f"{NEWCTRL}/t73.xyz"         # (a) after rain #1  (Aug 22 00:00)
xyz2_path = f"{NEWCTRL}/t241.xyz"        # (b) after rain #2  (Aug 29 00:00)
xyz3_path = f"{NEWCTRL}/t313.xyz"        # (c) before typhoon (Sep 1)
river_mask_path = f"{BASE}/river_mask.xyz"
river_dir = f"{BASE}/市管河道/"

# ── Historical map layers ───────────────────────────────────────────────────
圩塘 = gpd.read_file(f"{shape_dir}/圩塘.shp")
海岸线 = gpd.read_file(f"{shape_dir}/海岸线.shp")
钦公塘 = gpd.read_file(f"{shape_dir}/钦公塘.shp")
雍正石塘 = gpd.read_file(f"{shape_dir}/雍正石塘.shp")
市管河道 = gpd.read_file(f"{river_dir}/市管河道.shp")
市管河道 = 市管河道.set_crs(epsg=4326, inplace=False)

# GADM -> Shanghai
gadm = gpd.read_file(gadm_path)
sh_parts = gadm[(gadm["NAME_0"] == "China") & (gadm["NAME_2"] == "Shanghai")]
sh_dissolved = sh_parts.dissolve()
geom = sh_dissolved.geometry.iloc[0]
if isinstance(geom, MultiPolygon):
    main_poly = max(geom.geoms, key=lambda p: p.area)
    shanghai_main = gpd.GeoDataFrame(geometry=[main_poly], crs=sh_dissolved.crs)
else:
    shanghai_main = sh_dissolved

# Inland border
other_regions = gadm[(gadm["NAME_0"] == "China") & (gadm["NAME_2"] != "Shanghai")]
china_other = other_regions.dissolve()
shanghai_boundary = gpd.GeoDataFrame(geometry=shanghai_main.boundary, crs=shanghai_main.crs)
china_other_boundary = gpd.GeoDataFrame(geometry=china_other.boundary, crs=china_other.crs)
inland_border = gpd.overlay(shanghai_boundary, china_other_boundary, how="intersection")

# ── Point data ──────────────────────────────────────────────────────────────
river_mask_df = pd.read_csv(river_mask_path, sep=r'\s+', header=None, names=["lon", "lat", "depth"])
river_coords = set(zip(river_mask_df["lon"], river_mask_df["lat"]))

depth_df = pd.read_csv(depth_csv_path, sep=r'\s+', header=None, names=["lon", "lat", "depth"])
depth_df = depth_df[~depth_df[["lon", "lat"]].apply(tuple, axis=1).isin(river_coords)]
depth_gdf = gpd.GeoDataFrame(depth_df, geometry=gpd.points_from_xy(depth_df.lon, depth_df.lat), crs="EPSG:4326")

xyz1_df = pd.read_csv(xyz1_path, sep=r'\s+', header=None, names=["lon", "lat", "depth"])
xyz1_df = xyz1_df[~xyz1_df[["lon", "lat"]].apply(tuple, axis=1).isin(river_coords)]
xyz1_gdf = gpd.GeoDataFrame(xyz1_df, geometry=gpd.points_from_xy(xyz1_df.lon, xyz1_df.lat), crs="EPSG:4326")

xyz2_df = pd.read_csv(xyz2_path, sep=r'\s+', header=None, names=["lon", "lat", "depth"])
xyz2_df = xyz2_df[~xyz2_df[["lon", "lat"]].apply(tuple, axis=1).isin(river_coords)]
xyz2_gdf = gpd.GeoDataFrame(xyz2_df, geometry=gpd.points_from_xy(xyz2_df.lon, xyz2_df.lat), crs="EPSG:4326")

xyz3_df = pd.read_csv(xyz3_path, sep=r'\s+', header=None, names=["lon", "lat", "depth"])
xyz3_df = xyz3_df[~xyz3_df[["lon", "lat"]].apply(tuple, axis=1).isin(river_coords)]
xyz3_gdf = gpd.GeoDataFrame(xyz3_df, geometry=gpd.points_from_xy(xyz3_df.lon, xyz3_df.lat), crs="EPSG:4326")

# Reproject to EPSG:3857
for layer in [圩塘, 海岸线, 钦公塘, 雍正石塘, 市管河道, shanghai_main, inland_border, depth_gdf, xyz1_gdf, xyz2_gdf, xyz3_gdf]:
    layer.to_crs(epsg=3857, inplace=True)

# ── Filter data east of the 1905 coastline ──────────────────────────────────
coastline_line = 海岸线.geometry.union_all()
if coastline_line.geom_type == 'MultiLineString':
    coastline_line = LineString(np.concatenate([np.array(geom.coords) for geom in coastline_line.geoms]))
coast_coords = np.array(coastline_line.coords)
coast_coords = coast_coords[np.argsort(coast_coords[:, 1])]
unique_lat, idx = np.unique(coast_coords[:, 1], return_index=True)
interp_func = dict(zip(unique_lat, coast_coords[idx, 0]))  # lat: lon


def clean_outsiders(test_gdf):
    depth_points = test_gdf.copy()
    x = depth_points.geometry.x
    y = depth_points.geometry.y
    depth_points["coast_x"] = np.interp(
        y, np.array(list(interp_func.keys())), np.array(list(interp_func.values())))
    return depth_points[x <= depth_points["coast_x"]].copy()


depth_gdf = clean_outsiders(depth_gdf)
xyz1_gdf = clean_outsiders(xyz1_gdf)
xyz2_gdf = clean_outsiders(xyz2_gdf)
xyz3_gdf = clean_outsiders(xyz3_gdf)

# ── Figure / gridspec (ax1 top kept empty then deleted; maps in rows 2-3) ────
fig = plt.figure(figsize=(7, 9), dpi=600)
gs = gridspec.GridSpec(nrows=4, ncols=2, height_ratios=[.85, 0.15, 1, 1], width_ratios=[1, 1])
ax1 = fig.add_subplot(gs[0, :])
ax2 = fig.add_subplot(gs[2, 0])
ax3 = fig.add_subplot(gs[2, 1])
ax4 = fig.add_subplot(gs[3, 0])
ax5 = fig.add_subplot(gs[3, 1])
gs.update(wspace=0.05, hspace=0.05)


# ── Colormap ────────────────────────────────────────────────────────────────
def shuai_colormap1():
    C1 = np.asarray([170, 219, 30]) / 255   # green
    C2 = np.asarray([2, 7, 93]) / 255       # dark blue
    C3 = np.asarray([0, 183, 235]) / 255    # cyan
    C6 = np.asarray([255, 0, 0]) / 255      # red
    C7 = np.asarray([255, 233, 0]) / 255    # yellow
    C8 = np.asarray([255, 240, 240]) / 255  # mistyrose
    C9 = np.asarray([240, 255, 255]) / 255  # azure
    CUTS = 10
    tmp1 = np.asarray([np.linspace(C1[0], C2[0], CUTS), np.linspace(C1[1], C2[1], CUTS), np.linspace(C1[2], C2[2], CUTS)]).transpose()[:-1]
    CUTS = 8
    tmp2 = np.asarray([np.linspace(C2[0], C3[0], CUTS), np.linspace(C2[1], C3[1], CUTS), np.linspace(C2[2], C3[2], CUTS)]).transpose()[:-1]
    CUTS = 4
    tmp4 = np.asarray([np.linspace(C3[0], C9[0], CUTS), np.linspace(C3[1], C9[1], CUTS), np.linspace(C3[2], C9[2], CUTS)]).transpose()
    colors_arr = np.concatenate([tmp1, tmp2, tmp4])
    cmap = mcolors.LinearSegmentedColormap.from_list('my_colormap', colors_arr)
    cmaplist = [cmap(i) for i in range(cmap.N)]
    cmap = mcolors.LinearSegmentedColormap.from_list('Custom cmap', cmaplist, cmap.N)
    return cmap.reversed()


cmap = shuai_colormap1()
norm = colors.Normalize(vmin=0, vmax=1.2)
bounds = np.arange(0, 1.2 + 0.1, 0.1)

# ── Map panels (ax2-ax5) ─────────────────────────────────────────────────────
for ax_tmp, data_tmp in [[ax2, xyz1_gdf], [ax3, xyz2_gdf], [ax4, xyz3_gdf], [ax5, depth_gdf]]:
    圩塘.plot(ax=ax_tmp, color='darkgoldenrod', edgecolor='none')
    钦公塘.plot(ax=ax_tmp, color='darkgoldenrod', edgecolor='none', lw=2)
    雍正石塘.plot(ax=ax_tmp, edgecolor='slategray', linewidth=3)
    海岸线.plot(ax=ax_tmp, edgecolor='black', linewidth=1, linestyle='dashed')
    inland_border.plot(ax=ax_tmp, edgecolor='black', linewidth=0.8)
    市管河道[市管河道["MC"].isin([
        "黄浦江", "苏州河", "蕴藻浜", "淀浦河", "太浦河", "拦路港", "斜塘", "横潦泾", "西泖河", "泖河", "竖潦泾"
    ])].plot(ax=ax_tmp, edgecolor='magenta', linewidth=1, facecolor='none', zorder=20, alpha=.5)

    ctx.add_basemap(ax_tmp, source=ctx.providers.CartoDB.PositronNoLabels, attribution=False)

    shanghai_main_tmp = shanghai_main.to_crs(epsg=3857)
    depth_within = gpd.sjoin(data_tmp, shanghai_main_tmp, how='inner', predicate='within')
    hb = ax_tmp.hexbin(depth_within.geometry.x, depth_within.geometry.y,
                       C=depth_within["depth"], reduce_C_function=np.mean,
                       gridsize=70, cmap=cmap, norm=norm, edgecolors='none')
    hb.set_antialiased(False)

# Shared colorbar (right side, spanning ax3 top to ax5 bottom)
cbar_ax = fig.add_axes([0.92, ax5.get_position().y0, 0.015, ax3.get_position().y1 - ax5.get_position().y0])
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, cax=cbar_ax, ticks=bounds, extend='max')
cbar.set_label("Water Depth (m)")

# ── Axes formatting (lat/lon ticks) ──────────────────────────────────────────
transformer_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
bounds4326 = shanghai_main.to_crs(epsg=4326).total_bounds
minx_3857, miny_3857 = transformer_to_3857.transform(bounds4326[0] - .05, bounds4326[1] - .05)
maxx_3857, maxy_3857 = transformer_to_3857.transform(bounds4326[2] + .05, bounds4326[3] + .05)

axes_grid = [ax2, ax3, ax4, ax5]
show_x = [False, False, True, True]   # only bottom row
show_y = [True, False, True, False]   # only left column
for i, ax in enumerate(axes_grid):
    x_deg_ticks = np.arange(np.floor(bounds4326[0] * 5) / 5, np.ceil(bounds4326[2] * 5) / 5 + 0.01, 0.4)
    y_deg_ticks = np.arange(np.floor(bounds4326[1] * 5) / 5, np.ceil(bounds4326[3] * 5) / 5 + 0.01, 0.4)
    x_ticks_merc = [transformer_to_3857.transform(x, bounds4326[1])[0] for x in x_deg_ticks]
    y_ticks_merc = [transformer_to_3857.transform(bounds4326[0], y)[1] for y in y_deg_ticks]
    x_labels = [f"{abs(round(x, 2))}°{'E' if x >= 0 else 'W'}" for x in x_deg_ticks]
    y_labels = [f"{abs(round(y, 2))}°{'N' if y >= 0 else 'S'}" for y in y_deg_ticks]
    ax.set_xticks(x_ticks_merc)
    ax.set_xticklabels([])
    ax.set_yticks(y_ticks_merc)
    ax.set_yticklabels([])
    if show_x[i]:
        ax.set_xticklabels(x_labels)
    if show_y[i]:
        ax.set_yticklabels(y_labels)
    ax.set_xlim(minx_3857, maxx_3857)
    ax.set_ylim(miny_3857, maxy_3857)

# Panel labels a-d
for ax, label in zip([ax2, ax3, ax4, ax5], ['a', 'b', 'c', 'd']):
    ax.text(0.01, 0.98, label, transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='top', ha='left')

# Top-right corner titles
map_titles = ["Predecessor\nRain #1", "Predecessor\nRain #2",
              "Before\nTyphoon Impact", "After\nTyphoon Impact"]
for ax, title in zip([ax2, ax3, ax4, ax5], map_titles):
    ax.text(0.99, 0.98, title, transform=ax.transAxes, fontsize=8, ha='right', va='top')

# Legend
legend_elements = [
    Line2D([0], [0], color='darkgoldenrod', linewidth=2, label='Earthen\nEmbankment'),
    Line2D([0], [0], color='slategray', linewidth=3, label='Stone\nEmbankment'),
    Line2D([0], [0], color='black', linestyle='dashed', linewidth=1, label='Coastline\nin 1905'),
    Line2D([0], [0], color='black', linewidth=0.8, label='Shanghai\nBorder'),
    Line2D([0], [0], color='magenta', linewidth=1, label='River')
]
fig.legend(handles=legend_elements, loc='lower center',
           bbox_to_anchor=(0.51, 0.035), ncol=5, fontsize=8, frameon=False)

# Delete the empty top panel so only the 2x2 maps remain
fig.delaxes(ax1)

fig.savefig(f"{BASE}/Fig2_maps.pdf", bbox_inches="tight")
fig.savefig(f"{BASE}/Fig2_maps.png", dpi=300, bbox_inches="tight")
print("Saved Fig2_maps.pdf / .png")
