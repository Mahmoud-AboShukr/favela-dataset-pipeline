from pathlib import Path

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt


IN_GPKG = Path("data/interim/polygons_clean/favelas_clean.gpkg")
LAYER = "favelas_clean"

OUT_DIR = Path("reports/qc/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_MAP = OUT_DIR / "fig01_cleaned_polygons.png"
OUT_TABLE = OUT_DIR / "fig01_cleaned_polygons_attribute_preview.csv"

# How many rows to export from the attribute table preview
N_ROWS = 50


def main():
    if not IN_GPKG.exists():
        raise FileNotFoundError(f"Missing input: {IN_GPKG}")

    gdf = gpd.read_file(IN_GPKG, layer=LAYER)
    if gdf.empty:
        raise ValueError("Layer is empty.")

    # Ensure favela_id exists
    if "favela_id" not in gdf.columns:
        raise ValueError("favela_id column not found. Re-run subtask1_clean_polygons.py.")

    # --- 1) Export attribute table preview (CSV)
    cols_priority = [c for c in ["favela_id", "source_id", "part_index", "gov_id"] if c in gdf.columns]
    cols_rest = [c for c in gdf.columns if c not in cols_priority + ["geometry"]]
    cols = cols_priority + cols_rest

    preview = gdf[cols].head(N_ROWS).copy()
    preview.to_csv(OUT_TABLE, index=False)

    # --- 2) Export simple map figure (PNG)
    # Plot polygons quickly (no basemap)
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot polygons with stronger styling
    gdf.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=0.4)

    # Optional: add centroids as points so the distribution is obvious
    gdf_cent = gdf.copy()
    gdf_cent["geometry"] = gdf_cent.geometry.centroid
    gdf_cent.plot(ax=ax, markersize=1, alpha=0.6)

    ax.set_title("Cleaned favela polygons (EPSG:4326) — favelas_clean.gpkg")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    fig.savefig(OUT_MAP, dpi=250)

    print("✅ Saved map image:", OUT_MAP)
    print("✅ Saved attribute preview CSV:", OUT_TABLE)
    print(f"✅ Rows in preview: {min(N_ROWS, len(gdf))} / {len(gdf)} total")


if __name__ == "__main__":
    main()