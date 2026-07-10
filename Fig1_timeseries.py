#!/usr/bin/env python3
"""
Figure 1 — time series of daily rainfall (Xujiahui) with 2-/5-yr return-period
lines, and modelled water level + astronomical tide at Wusongkou, Aug-Sep 1905.

Extracted verbatim from Untitled.ipynb (cell 1, the `ax1` panel of the overview
figure); only tidied for standalone use: paths -> shuaiwang, single-panel figure
instead of the 5-panel gridspec, map code removed, headless backend + savefig.

Run:  ~/anaconda3/bin/python Fig1_timeseries.py   ->  Fig1_timeseries.{pdf,png}
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

BASE = "/Users/shuaiwang/sandbox/shanghai"
rain_path = f"{BASE}/xujiahui_aug2031_daily_rain.csv"

# ── Load & preprocess rainfall ──────────────────────────────────────────────
rain = pd.read_csv(rain_path, sep=",")
rain["date"] = pd.to_datetime(dict(year=rain.Year, month=rain.Mon, day=rain.Day))
rain["daily_mm"] = rain["daily_acc_10thmm"] / 10.0
rain["md"] = rain["date"].dt.strftime("%m-%d")

# Subset for Aug 20 - Sept 5
mask = (rain["date"].dt.month == 8) & (rain["date"].dt.day >= 20) | (rain["date"].dt.month == 9) & (rain["date"].dt.day <= 5)
rain_subset = rain.loc[mask].copy()
ordered_days = sorted(rain_subset["md"].unique(), key=lambda x: pd.to_datetime("1900-" + x))
rain_subset["md"] = pd.Categorical(rain_subset["md"], categories=ordered_days, ordered=True)
rain_subset = rain_subset[rain_subset["md"].between("08-20", "09-02")]
ordered_days = sorted(rain_subset["md"].unique(), key=lambda x: pd.to_datetime("1900-" + x))

# Split 1905 from other years
rain_1905 = rain_subset[rain_subset["Year"] == 1905]
rain_clim = rain_subset[rain_subset["Year"] != 1905]

# ── Figure ──────────────────────────────────────────────────────────────────
plt.rcParams.update({"font.size": 8})
# match the manuscript figure dimensions (image2.pdf = 462.845 x 182.479 pt)
fig, ax1 = plt.subplots(figsize=(6.428, 2.534), dpi=600)

## ax1: Bar plot of 1905 rainfall with non-parametric return level shading

# Load and preprocess rainfall data
df = pd.read_csv(rain_path)

# Step 1: Annual maximum daily rainfall (for non-parametric estimation)
df["date"] = pd.to_datetime(dict(year=df.Year, month=df.Mon, day=df.Day))
df["daily_mm"] = df["daily_acc_10thmm"] / 10.0
df["year"] = df["date"].dt.year
annual_max = df.groupby("year")["daily_mm"].max().dropna().sort_values(ascending=False)
n_years = len(annual_max)
ranks = np.arange(1, n_years + 1)
empirical_return_periods = (n_years + 1) / ranks

# Step 2: Interpolate non-parametric return levels
target_T = [1, 2, 5]
return_levels = np.interp(target_T, np.sort(empirical_return_periods), np.sort(annual_max.values))
r1, r2, r5 = return_levels

# Step 3: Plot 1905 rainfall bars + shaded return level bands

# Prepare 1905 rainfall data
rain_1905_sorted = rain_1905.sort_values("md")
rain_1905_series = rain_1905_sorted.set_index("md").loc[ordered_days]["daily_mm"].values
x = pd.to_datetime(["1905-" + d for d in ordered_days])

# Colors
color_bar = "#1f77b4"
color_0_1 = 'none'
color_1_2 = "#c6dbef"     # Light blue
color_2_5 = "#6baed6"    # Medium blue
color_5plus = "#2171b5"  # Dark blue

# Horizontal lines for return levels
ax1.axhline(r2, color="#6baed6", linestyle="--", linewidth=2)
ax1.axhline(r5, color="#2171b5", linestyle="--", linewidth=2)
# Annotate return levels at Aug 19
ax1.text(pd.to_datetime("1905-08-18"), r2, "2-yr rainfall\nreturn period", color="#6baed6", fontsize=8, ha='center', va='bottom')
ax1.text(pd.to_datetime("1905-08-18"), r5 - 2, "5-yr rainfall\nreturn period", color="#2171b5", fontsize=8, ha='center', va='top')

# Bar plot
ax1.bar(x, rain_1905_series, color=color_bar, label="Rainfall")

# Formatting
ax1.set_ylim([0, 100])
ax1.tick_params(axis='y', colors=color_bar)
ax1.set_ylabel("Daily Rainfall (mm)", color=color_bar)
ax1.set_xlim(pd.to_datetime("1905-08-16"), pd.to_datetime("1905-09-03"))
# Customize x-ticks: show labels only from 08-20 to 09-03
tick_dates = pd.date_range("1905-08-20", "1905-09-03")
ax1.set_xticks(tick_dates)
ax1.set_xticklabels([d.strftime("%m/%d") for d in tick_dates], rotation=45)

# ── Tide / water level ──────────────────────────────────────────────────────
tide_df = pd.read_csv(f"{BASE}/wusongkou.csv")
tide_df.columns = tide_df.columns.str.strip()  # Remove any whitespace in headers


def fix_year(d):
    parts = d.split()
    date_parts = parts[0].split('/')
    if len(date_parts[2]) == 2:
        date_parts[2] = '19' + date_parts[2]
    return '/'.join(date_parts) + ' ' + parts[1]


# Apply to the date column
tide_df["fixed_date"] = tide_df["date and time"].apply(fix_year)

# Now safely parse as datetime
tide_df["datetime"] = pd.to_datetime(tide_df["fixed_date"], format="%m/%d/%Y %H:%M")
tide_df["depth_m"] = tide_df["water depth (points) (m)"]
tide_mask = (tide_df["datetime"] >= "1905-08-20") & (tide_df["datetime"] <= "1905-09-02 21:00")
tide_plot = tide_df.loc[tide_mask]

tide_df = pd.read_csv(f"{BASE}/Wusong_tide_modeling_19050801-19050916.csv")
tide_df.columns = tide_df.columns.str.strip()  # Remove any whitespace in headers

# Apply to the date column
tide_df["fixed_date"] = tide_df["date and time"].apply(fix_year)

# Now safely parse as datetime
tide_df["datetime"] = pd.to_datetime(tide_df["fixed_date"], format="%m/%d/%Y %H:%M")
tide_df["depth_m"] = tide_df["water depth (points) (m)"]
tide_mask = (tide_df["datetime"] >= "1905-08-20") & (tide_df["datetime"] <= "1905-09-02 21:00")
tide_plot_tide = tide_df.loc[tide_mask]

tide_plot_tide['depth_m'] += 2.4

# Plot tide on right y-axis
ax1_tide = ax1.twinx()
ax1_tide.plot(tide_plot["datetime"], tide_plot["depth_m"], color="#d62728", linewidth=2, label="Water Level")
ax1_tide.plot(tide_plot_tide["datetime"], tide_plot_tide["depth_m"], color="#FFD700", linewidth=.6, label="Tide Level")

ax1_tide.axhline(5.4, color="#ff7f0e", linestyle="--", linewidth=2)
ax1_tide.text(pd.to_datetime("1905-08-18"), 5.4, "10-yr water level\nreturn period", color="#ff7f0e", fontsize=8, ha='center', va='bottom')

ax1_tide.tick_params(axis='y', colors="#d62728")
ax1_tide.set_ylabel("Water Level (m)", color="#d62728")

ax1_tide.set_xticks(tide_plot["datetime"])
ax1_tide.set_xticklabels(tide_plot["datetime"], rotation=45)
ax1_tide.xaxis.set_major_locator(mdates.DayLocator())
ax1_tide.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax1_tide.set_ylim([0, 7])
ax1_tide.set_xlim(pd.to_datetime("1905-08-16"), pd.to_datetime("1905-09-03"))
# Customize x-ticks: show labels only from 08-20 to 09-03
tick_dates = pd.date_range("1905-08-20", "1905-09-02")
ax1_tide.set_xticks(tick_dates)
ax1_tide.set_xticklabels([d.strftime("%m/%d") for d in tick_dates], rotation=45)

# Combine legends from both axes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax1_tide.get_legend_handles_labels()

custom_handles = [
    Patch(facecolor=color_bar, edgecolor='none', label='Rainfall'),
    Line2D([0], [0], color="#d62728", lw=1.5, label='Water/Level')
]

ax1.legend(custom_handles, [h.get_label() for h in custom_handles], loc="lower left", handlelength=1.5, handleheight=1, frameon=False)

# Add annotation for Predecessor Rain #1
ax1.annotate("Predecessor\nRain #1",
             xy=(pd.to_datetime("1905-08-21"), 83.6), xycoords='data',
             xytext=(0, 5), textcoords='offset points',
             ha='center', va='bottom',
             arrowprops=dict(arrowstyle='-|>', facecolor='black', lw=0.8),
             fontsize=8, color='black')

# Add annotation for Predecessor Rain #2
ax1.annotate("Predecessor\nRain #2",
             xy=(pd.to_datetime("1905-08-28"), 83.6), xycoords='data',
             xytext=(0, 5), textcoords='offset points',
             ha='center', va='bottom',
             arrowprops=dict(arrowstyle='-|>', facecolor='black', lw=0.8),
             fontsize=8, color='black')

# Add annotation for Typhoon Impact (spanning 09-01 to 09-02)
ax1.annotate("Typhoon\nImpact",
             xy=(pd.to_datetime("1905-09-01 12:00"), 83.6), xycoords='data',
             xytext=(0, 5), textcoords='offset points',
             ha='center', va='bottom',
             arrowprops=dict(arrowstyle='-|>', facecolor='black', lw=0.8),
             fontsize=8, color='black')

fig.savefig(f"{BASE}/Fig1_timeseries.pdf", bbox_inches="tight")
fig.savefig(f"{BASE}/Fig1_timeseries.png", dpi=300, bbox_inches="tight")
print("Saved Fig1_timeseries.pdf / .png")
