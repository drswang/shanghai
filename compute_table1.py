#!/usr/bin/env python3
"""
Compute Table 1 (flooded area + depth-change statistics) for the 1905 Shanghai
flood simulations.

Method is the ORIGINAL notebook method (Untitled.ipynb, cell 10), validated to
reproduce the published Table 1 exactly:
  - drop river cells (river_mask.xyz) and points east of the 1905 coastline
  - restrict to the Shanghai polygon (GADM), reproject to EPSG:3857
  - bin each field onto a common mesh with binned_statistic_2d
    (bins = 70*1.5 = 105, per-scenario bounding box)
  - depth-change diff = scenario - control on that mesh
  - areal %% = (# cells past threshold) / (# mesh cells inside Shanghai)
  - 95th-pct decrease/increase = percentile of the diff (5th/95th)
  - metrics evaluated at the post-typhoon timestep (t = 358)

Per the caption rule, 95th-pct values are reported only where the changed
area is >= 5%.

Run:  ~/anaconda3/bin/python compute_table1.py
Deps: geopandas>=1.0, shapely>=2, scipy, pandas, numpy  (conda base env)
"""
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Point, LineString
from scipy.stats import binned_statistic_2d
import warnings
warnings.filterwarnings("ignore")

# ── Config ──────────────────────────────────────────────────────────────────
BASE = "/Users/shuaiwang/sandbox/shanghai"
GADM = "/Users/shuaiwang/sandbox/data/borders/gadm36.shp"
SHAPE_DIR = f"{BASE}/map/1910map/shape"
RIVER_MASK = f"{BASE}/river_mask.xyz"
T = 358                       # post-typhoon timestep
AREA_THRESHOLD = 0.05         # omit 95th-pct where changed area < 5%

# Control first; each scenario is compared against the control.
# To add the forthcoming NEW neap-tide run, add e.g.:
#   "Neap tide": f"{BASE}/postproc/new_postproc6/infil_7_890_rain/text/t{T}.xyz"
NEW = f"{BASE}/postproc"
SCENARIOS = {
    "Control":      f"{NEW}/new_postproc1/infil_7_890_rain/text/t{T}.xyz",
    "No rain #1":   f"{NEW}/new_postproc3/infil_7_890_rain/text/t{T}.xyz",
    "No rain #2":   f"{NEW}/new_postproc2/infil_7_890_rain/text/t{T}.xyz",
    "No rain #1&2": f"{NEW}/new_postproc4/infil_7_890_rain/text/t{T}.xyz",
    "Neap tide":    f"{NEW}/new_postproc6/infil_7_890_rain/text/t{T}.xyz",  # new neap-tide run
    "No stone emb.": f"{NEW}/new_postproc5/infil_7_890_rain/text/t{T}.xyz",
}

# ── Static geometry (loaded once) ───────────────────────────────────────────
gadm = gpd.read_file(GADM)
sh = gadm[(gadm.NAME_0 == "China") & (gadm.NAME_2 == "Shanghai")].dissolve()
geom = sh.geometry.iloc[0]
if isinstance(geom, MultiPolygon):
    geom = max(geom.geoms, key=lambda p: p.area)
SHANGHAI = gpd.GeoDataFrame(geometry=[geom], crs=sh.crs).to_crs(3857)

river_df = pd.read_csv(RIVER_MASK, sep=r"\s+", header=None, names=["lon", "lat", "depth"])
RIVER_COORDS = set(zip(river_df["lon"], river_df["lat"]))

coast = gpd.read_file(f"{SHAPE_DIR}/海岸线.shp").to_crs(3857)
_cl = coast.geometry.union_all()
if _cl.geom_type == "MultiLineString":
    _cl = LineString(np.concatenate([np.array(g.coords) for g in _cl.geoms]))
_cc = np.array(_cl.coords)
_cc = _cc[np.argsort(_cc[:, 1])]
_ulat, _idx = np.unique(_cc[:, 1], return_index=True)
_COAST = dict(zip(_ulat, _cc[_idx, 0]))
_KX = np.array(list(_COAST.keys())); _KY = np.array(list(_COAST.values()))


def load(path):
    """Load an XYZ depth grid: drop river cells, keep inland of coastline, 3857."""
    df = pd.read_csv(path, sep=r"\s+", header=None, names=["lon", "lat", "depth"])
    df = df[~df[["lon", "lat"]].apply(tuple, axis=1).isin(RIVER_COORDS)]
    g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat),
                         crs="EPSG:4326").to_crs(3857)
    coast_x = np.interp(g.geometry.y, _KX, _KY)
    return g[g.geometry.x <= coast_x].copy()


def _mesh(gdf, edges=None):
    within = gpd.sjoin(gdf, SHANGHAI, how="inner", predicate="within")
    if edges is None:
        xr = [within.geometry.x.min(), within.geometry.x.max()]
        yr = [within.geometry.y.min(), within.geometry.y.max()]
        stat, xe, ye, _ = binned_statistic_2d(
            within.geometry.x, within.geometry.y, within["depth"],
            statistic="mean", bins=70 * 1.5, range=[xr, yr])
    else:
        stat, xe, ye, _ = binned_statistic_2d(
            within.geometry.x, within.geometry.y, within["depth"],
            statistic="mean", bins=edges)
    return np.nan_to_num(stat, nan=0), xe, ye


def _n_inside(xe, ye):
    xc = (xe[:-1] + xe[1:]) / 2; yc = (ye[:-1] + ye[1:]) / 2
    Xc, Yc = np.meshgrid(xc, yc)
    centers = gpd.GeoSeries([Point(x, y) for x, y in zip(Xc.ravel(), Yc.ravel())],
                            crs="EPSG:3857")
    return centers.within(SHANGHAI.geometry.iloc[0]).sum()


def flooded_pct(gdf):
    stat, xe, ye = _mesh(gdf)
    z = stat.T.ravel()
    return (z > 0.01).sum() / _n_inside(xe, ye) * 100


def change_stats(ctrl_gdf, scen_gdf):
    """Areal %% and 95th-pct of decrease/increase, scenario vs control."""
    stat_s, xe, ye = _mesh(scen_gdf)
    stat_c, _, _ = _mesh(ctrl_gdf, edges=[xe, ye])
    diff = (stat_s - stat_c).T.ravel()
    n = _n_inside(xe, ye)
    dec = diff < -0.01; inc = diff > 0.01
    return dict(
        dec_pct=dec.sum() / n * 100,
        inc_pct=inc.sum() / n * 100,
        p95_dec=abs(np.percentile(diff[dec], 5)) if dec.any() else 0.0,
        p95_inc=np.percentile(diff[inc], 95) if inc.any() else 0.0,
    )


def main():
    ctrl = load(SCENARIOS["Control"])
    cols = list(SCENARIOS)
    rows = {"Flooded area of Shanghai": {}, "Area with decreased depth": {},
            "95th-pct decrease (m)": {}, "Area with increased depth": {},
            "95th-pct increase (m)": {}}
    for name, path in SCENARIOS.items():
        g = ctrl if name == "Control" else load(path)
        rows["Flooded area of Shanghai"][name] = f"{flooded_pct(g):.0f}%"
        if name == "Control":
            for r in list(rows)[1:]:
                rows[r][name] = "---"
            continue
        s = change_stats(ctrl, g)
        rows["Area with decreased depth"][name] = f"{s['dec_pct']:.0f}%"
        rows["Area with increased depth"][name] = f"{s['inc_pct']:.0f}%"
        rows["95th-pct decrease (m)"][name] = (
            f"{s['p95_dec']:.2f}" if s["dec_pct"] >= AREA_THRESHOLD * 100 else "---")
        rows["95th-pct increase (m)"][name] = (
            f"{s['p95_inc']:.2f}" if s["inc_pct"] >= AREA_THRESHOLD * 100 else "---")
    df = pd.DataFrame(rows).T[cols]
    print(f"\nTable 1 (t = {T}; neap = new neap-tide run)\n")
    print(df.to_string())
    return df


if __name__ == "__main__":
    main()
