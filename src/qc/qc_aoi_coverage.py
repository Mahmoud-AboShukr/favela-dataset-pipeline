from pathlib import Path
import pandas as pd
import geopandas as gpd

AOI_GPKG = Path("data/interim/aoi/brasilia_boundary.gpkg")
AOI_LAYER = "brasilia_boundary"

CLEAN_GPKG = Path("data/interim/polygons_clean/favelas_clean.gpkg")
CLEAN_LAYER = "favelas_clean"

OUT_CSV = Path("reports/qc/stats/aoi_coverage_brasilia.csv")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

def main():
    aoi = gpd.read_file(AOI_GPKG, layer=AOI_LAYER).to_crs("EPSG:4326")
    gdf = gpd.read_file(CLEAN_GPKG, layer=CLEAN_LAYER).to_crs("EPSG:4326")

    A = aoi.geometry.union_all()

    n_total = len(gdf)
    n_intersect = int(gdf.intersects(A).sum())
    n_within = int(gdf.within(A).sum())
    n_excluded = n_total - n_intersect
    n_intersect_not_within = n_intersect - n_within  # polygons crossing the boundary

    row = {
        "aoi_name": "Distrito Federal (OSM)",
        "n_total_clean": n_total,
        "n_intersect_aoi": n_intersect,
        "n_within_aoi": n_within,
        "n_excluded": n_excluded,
        "n_intersect_not_within": n_intersect_not_within,
    }

    df = pd.DataFrame([row])
    df.to_csv(OUT_CSV, index=False)

    print("✅ AOI coverage QC saved:", OUT_CSV)
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()