# src/labels/subtask1_extract_brasilia.py

from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


# Rough Brasília bbox (WGS84). Adjust later if needed.
# Format: (min_lon, min_lat, max_lon, max_lat)
BRASILIA_BBOX = (-48.30, -16.10, -47.50, -15.50)


def main():
    in_path = Path("data/interim/polygons_clean/favelas_clean.gpkg")
    in_layer = "favelas_clean"

    out_path = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
    out_layer = "favelas_brasilia"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1) Read cleaned polygons
    gdf = gpd.read_file(in_path, layer=in_layer)

    # 2) Ensure CRS is EPSG:4326 (bbox is in WGS84 lon/lat)
    if gdf.crs is None:
        raise ValueError("Input layer has no CRS. Please check your cleaned polygons file.")
    if gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    # 3) Build a bbox polygon GeoDataFrame (for clip operations)
    bbox_geom = box(*BRASILIA_BBOX)
    bbox_gdf = gpd.GeoDataFrame(
        {"name": ["brasilia_bbox"]},
        geometry=[bbox_geom],
        crs="EPSG:4326",
    )

    # 4) Clip polygons to bbox (cuts parts outside the AOI)
    # This also implicitly selects only intersecting geometries.
    gdf_sub = gpd.clip(gdf, bbox_gdf)

    # 5) Save subset
    gdf_sub.to_file(out_path, layer=out_layer, driver="GPKG")

    print(f"✅ Saved Brasília subset: {out_path}")
    print(f"✅ Layer: {out_layer}")
    print(f"✅ Rows: {len(gdf_sub)}")


if __name__ == "__main__":
    main()