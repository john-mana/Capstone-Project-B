import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.ticker as mticker
import re
import folium

# --- Setup: Define paths relative to this script file ---
# This makes the script runnable from anywhere
script_dir = Path(__file__).parent

# Input files are in the same directory as the script
paths = {
    "ALA": script_dir / "ALA.csv",
    "iNaturalist": script_dir / "iNaturalist.csv",
    "Prototype": script_dir / "Prototype.csv",
}

# Output directory is also relative to the script's location
out_dir = script_dir / "experiment0_outputs"
out_dir.mkdir(exist_ok=True, parents=True)

print(f"Script running from: {script_dir}")
print(f"Output will be saved to: {out_dir}\n")

# --- Helper Functions ---

def count_decimals(value):
    """Count decimal places of a stringified number, preserving trailing zeros."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    if "." in s:
        frac = s.split(".")[1]
        frac = "".join([c for c in frac if c.isdigit()])
        return len(frac)
    return 0

def find_col(df, candidates):
    """Find a column name in df from a list of candidates (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None

def parse_year_from_date(s):
    """Extracts the four-digit year from a string."""
    if pd.isna(s):
        return np.nan
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y"):
        try:
            dt = datetime.strptime(s[:10], fmt)
            return dt.year
        except (ValueError, TypeError):
            continue
    m = re.search(r"(19|20)\d{2}", s)
    return int(m.group()) if m else np.nan

def tier_from_decimals(d):
    """Categorizes coordinate precision based on number of decimal places."""
    if pd.isna(d): return "unknown"
    d = int(d)
    if d <= 1: return "≈10–100 km (0–1 dp)"
    if d == 2: return "≈1–10 km (2 dp)"
    if d == 3: return "≈100–1000 m (3 dp)"
    if d == 4: return "≈10–100 m (4 dp)"
    if d == 5: return "≈1–10 m (5 dp)"
    if d >= 6: return "<1 m (6+ dp)"
    return "unknown"

# --- 1. Data Loading and Merging ---
loaded = {}
issues = []

for name, path in paths.items():
    if not path.exists():
        issues.append(f"{name} not found at {path}")
        continue
    try:
        df = pd.read_csv(path, dtype=str, low_memory=False)
        df["__source"] = name
        loaded[name] = df
    except Exception as e:
        issues.append(f"Failed to read {name}: {e}")

if issues:
    print("\n".join(["[READ ISSUE] " + m for m in issues]))

if not loaded:
    raise RuntimeError("No CSVs could be loaded. Check file paths and contents.")

df_all = pd.concat(loaded.values(), ignore_index=True)
print(f"Loaded a total of {len(df_all):,} rows from {len(loaded)} sources.")

# --- 2. Deduplication ---
df_all_raw = df_all.copy()
df_all = df_all.drop_duplicates()

key_cols = ["Scientific Name", "Decimal Latitude", "Decimal Longitude", "Event Date"]
missing = [c for c in key_cols if c not in df_all.columns]

if not missing:
    df_all = df_all.drop_duplicates(subset=key_cols).reset_index(drop=True)
else:
    print(f"Skipping key-field deduplication because columns are missing: {missing}")
    df_all = df_all.reset_index(drop=True)

print(f"Finished cleaning. Rows remaining: {len(df_all):,}\n")


# --- 3. Data Processing & Feature Engineering ---
lat_col = find_col(df_all, ["decimal latitude", "latitude", "lat", "decimalLatitude"])
lon_col = find_col(df_all, ["decimal longitude", "longitude", "lon", "decimalLongitude"])
date_col = find_col(df_all, ["date", "eventDate", "event date", "observationDate", "observed_on"])

if date_col:
    df_all["year"] = df_all[date_col].apply(parse_year_from_date)
else:
    df_all["year"] = np.nan

if lat_col and lon_col:
    dec_lat = df_all[lat_col].apply(count_decimals)
    dec_lon = df_all[lon_col].apply(count_decimals)
    df_all["decimals"] = pd.concat([dec_lat, dec_lon], axis=1).max(axis=1)
    print(f"Calculated decimals for {df_all['decimals'].notna().sum():,} rows")
else:
    df_all["decimals"] = np.nan
    print("No lat/lon columns found")

print(f"Rows with valid year: {df_all['year'].notna().sum():,}")
print(f"Rows with valid decimals: {df_all['decimals'].notna().sum():,}")

df_clean = df_all.dropna(subset=["year", "decimals"]).copy()
print(f"Rows after filtering: {len(df_clean):,}")

if len(df_clean) > 0:
    df_clean["year"] = df_clean["year"].astype(int)
    df_clean["decimals"] = df_clean["decimals"].astype(int)
df_clean["precision_tier"] = df_clean["decimals"].apply(tier_from_decimals)

print(f"Found {len(df_clean):,} usable rows with both year and coordinate data.\n")

# --- 4. Analysis and CSV Outputs ---
summary_overall = (
    df_clean.groupby(["__source", "year"])["decimals"]
    .median()
    .reset_index(name="median_decimals")
    .sort_values(["__source", "year"])
)

# Precision tier analysis
summary_tier_share = (
    df_clean.groupby(["__source", "precision_tier"])
    .size()
    .groupby(level=0, group_keys=False)
    .apply(lambda s: (s / s.sum()).round(3))
    .reset_index(name="share")
    .sort_values(["__source", "share"], ascending=[True, False])
)

# Save outputs
summary_overall_path = out_dir / "E0_median_decimals_by_year.csv"
summary_tier_path = out_dir / "E0_precision_tier_share.csv"
df_clean_path = out_dir / "E0_clean_records_sample.csv"

summary_overall.to_csv(summary_overall_path, index=False)
summary_tier_share.to_csv(summary_tier_path, index=False)
df_clean.sample(min(1000, len(df_clean))).to_csv(df_clean_path, index=False)

print(f"Saved yearly median summary to: {summary_overall_path}")
print(f"Saved precision tier share to: {summary_tier_path}")
print(f"Saved clean records sample to: {df_clean_path}")


# --- 5. Visualizations ---
print("Generating plots...")

# Combined Trend Plot (Basic)
plt.figure(figsize=(14, 8))
for src, g in summary_overall.groupby("__source"):
    plt.plot(g["year"], g["median_decimals"], marker="o", markersize=6, linewidth=2, label=src)
plt.xlabel("Year", fontsize=14)
plt.ylabel("Median decimal places (latitude/longitude)", fontsize=14)
plt.title("Time vs GPS Precision (Median decimals)", fontsize=16, weight="bold")
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(fontsize=12, frameon=True)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
plt.tight_layout()
plt.savefig(out_dir / "E0_trend_combined.png", dpi=300)
plt.close()

# Combined Trend Plot (Beautified)
plt.figure(figsize=(16, 10))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
for i, (src, g) in enumerate(summary_overall.groupby("__source")):
    plt.plot(g["year"], g["median_decimals"], marker="o", markersize=8, linewidth=3, 
             label=src, color=colors[i % len(colors)], alpha=0.8)
plt.xlabel("Year", fontsize=16, weight='bold')
plt.ylabel("Median decimal places (latitude/longitude)", fontsize=16, weight='bold')
plt.title("GPS Precision Evolution Over Time", fontsize=20, weight="bold", pad=20)
plt.grid(True, linestyle="--", alpha=0.7)
plt.legend(fontsize=14, frameon=True, shadow=True)
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)
plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
plt.tight_layout()
plt.savefig(out_dir / "E0_trend_combined_beautified.png", dpi=300)
plt.close()

# Individual source trend plots
for src in df_clean["__source"].unique():
    src_data = summary_overall[summary_overall["__source"] == src]
    if len(src_data) > 0:
        # Basic plot
        plt.figure(figsize=(12, 8))
        plt.plot(src_data["year"], src_data["median_decimals"], marker="o", markersize=6, linewidth=2)
        plt.xlabel("Year", fontsize=14)
        plt.ylabel("Median decimal places", fontsize=14)
        plt.title(f"GPS Precision Trend - {src}", fontsize=16, weight="bold")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        plt.tight_layout()
        plt.savefig(out_dir / f"E0_trend_{src}.png", dpi=300)
        plt.close()
        
        # Beautified plot
        plt.figure(figsize=(14, 10))
        plt.plot(src_data["year"], src_data["median_decimals"], marker="o", markersize=8, linewidth=3, color='#2ca02c')
        plt.xlabel("Year", fontsize=16, weight='bold')
        plt.ylabel("Median decimal places", fontsize=16, weight='bold')
        plt.title(f"GPS Precision Evolution - {src}", fontsize=20, weight="bold", pad=20)
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        plt.tight_layout()
        plt.savefig(out_dir / f"E0_trend_{src}_beautified.png", dpi=300)
        plt.close()

# Dot Plot (Basic)
sampled = df_clean.sample(min(10000, len(df_clean)), random_state=42).copy()
rng = np.random.default_rng(42)
sampled["_year_jitter"] = sampled["year"] + rng.normal(0, 0.05, size=len(sampled))
plt.figure(figsize=(10, 6))
plt.scatter(sampled["_year_jitter"], sampled["decimals"], s=10, alpha=0.5, color="red")
plt.xlabel("Year", fontsize=13)
plt.ylabel("Decimal places (max of lat/lon)", fontsize=13)
plt.title("Dot Plot of GPS Decimal Places over Time (sampled)", fontsize=15, weight="bold")
plt.grid(True, linestyle="--", alpha=0.6)
plt.xticks(fontsize=11)
plt.yticks(fontsize=11)
plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
plt.tight_layout()
plt.savefig(out_dir / "E0_dotplot_sampled.png", dpi=300)
plt.close()

# Dot Plot (Red version)
plt.figure(figsize=(12, 8))
plt.scatter(sampled["_year_jitter"], sampled["decimals"], s=15, alpha=0.6, color="#d62728")
plt.xlabel("Year", fontsize=14, weight='bold')
plt.ylabel("Decimal places (max of lat/lon)", fontsize=14, weight='bold')
plt.title("GPS Precision Distribution Over Time", fontsize=18, weight="bold")
plt.grid(True, linestyle="--", alpha=0.7)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
plt.tight_layout()
plt.savefig(out_dir / "E0_dotplot_sampled_red.png", dpi=300)
plt.close()

print("Plots saved successfully.\n")


# --- 6. Interactive Map ---
print("Generating interactive map...")
reserve_keyword = "Lansdowne"
dot_color = "#d86b1c"
circle_color = "#8fbc8f"
circle_opacity = 0.25
dot_radius = 3
max_points = 5000

# Ensure lat/lon columns exist before proceeding
lat_col = find_col(df_clean, ["decimal latitude", "latitude", "lat", "decimalLatitude"])
lon_col = find_col(df_clean, ["decimal longitude", "longitude", "lon", "decimalLongitude"])
reserve_col = find_col(df_clean, ["Reserve Name"])

if lat_col and lon_col:
    df_map = df_clean.copy()
    if reserve_col and reserve_keyword:
        df_map = df_map[df_map[reserve_col].str.contains(reserve_keyword, case=False, na=False)]

    df_map = df_map.dropna(subset=[lat_col, lon_col]).copy()
    
    if len(df_map) > max_points:
        df_map = df_map.sample(max_points, random_state=42)

    if not df_map.empty:
        center_lat = df_map[lat_col].astype(float).median()
        center_lon = df_map[lon_col].astype(float).median()

        # Calculate radius for circle
        lat_km = 111.0
        lon_km = 111.0 * np.cos(np.deg2rad(center_lat))
        d_km = np.sqrt(
            ((df_map[lat_col].astype(float) - center_lat) * lat_km) ** 2 +
            ((df_map[lon_col].astype(float) - center_lon) * lon_km) ** 2
        )
        radius_m = float(np.percentile(d_km, 95) * 2 * 1000)  # 95th percentile * 2, convert to meters
        radius_m = max(radius_m, 500)  # Minimum 500m radius

        m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="OpenStreetMap")

        # Add circle
        folium.Circle(
            location=[center_lat, center_lon],
            radius=radius_m,
            color=circle_color,
            fill=True,
            fill_color=circle_color,
            fill_opacity=circle_opacity,
            weight=1
        ).add_to(m)

        # Add markers
        for _, row in df_map.iterrows():
            folium.CircleMarker(
                location=[float(row[lat_col]), float(row[lon_col])],
                radius=dot_radius,
                color=dot_color,
                fill=True,
                fill_opacity=0.9,
                opacity=0.9
            ).add_to(m)

        # Add title
        title_html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 320px; z-index: 9999; 
                    background-color: rgba(255,255,255,0.9); padding: 6px 10px; 
                    border-radius: 6px; font-size: 14px;">
        <b>Observations — {reserve_keyword}</b><br>
        Points: {len(df_map):,} | Circle radius: {int(radius_m)} m
        </div>
        """
        m.get_root().html.add_child(folium.Element(title_html))

        html_path = out_dir / f"E0_map_{reserve_keyword.replace(' ','_')}.html"
        m.save(str(html_path))
        print(f"Map for '{reserve_keyword}' saved to: {html_path}")
    else:
        print(f"No data found for keyword '{reserve_keyword}' to create a map.")
else:
    print("Could not find latitude/longitude columns to generate map.")

print("\nAnalysis complete.")