# src/labels/subtask1_extract_brasilia.py
from pathlib import Path
import geopandas as gpd

OSM_AOI_GPKG = Path("data/interim/aoi/brasilia_boundary.gpkg")
OSM_AOI_LAYER = "brasilia_boundary"

def main():
    in_path = Path("data/interim/polygons_clean/favelas_clean.gpkg")
    in_layer = "favelas_clean"

    out_path = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
    out_layer = "favelas_brasilia"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1) Read cleaned polygons
    gdf = gpd.read_file(in_path, layer=in_layer)
    if gdf.crs is None:
        raise ValueError("Input polygons CRS is missing.")
    gdf = gdf.to_crs("EPSG:4326")

    # 2) Read OSM AOI (required)
    if not OSM_AOI_GPKG.exists():
        raise FileNotFoundError(
            f"OSM AOI file not found: {OSM_AOI_GPKG}\n"
            "Generate it first (OSMnx) or place it in data/interim/aoi/."
        )

    aoi = gpd.read_file(OSM_AOI_GPKG, layer=OSM_AOI_LAYER)
    if aoi.empty:
        raise ValueError("OSM AOI layer is empty.")
    if aoi.crs is None:
        raise ValueError("OSM AOI CRS is missing.")
    aoi = aoi.to_crs("EPSG:4326")

    # 3) Keep only polygon geometries and dissolve into one AOI geometry
    aoi = aoi[aoi.geometry.notna() & ~aoi.geometry.is_empty].copy()
    aoi = aoi[aoi.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    if aoi.empty:
        raise ValueError("OSM AOI has no Polygon/MultiPolygon geometry.")
    aoi_geom = aoi.geometry.union_all()

    aoi_gdf = gpd.GeoDataFrame({"name": ["brasilia_osm_aoi"]}, geometry=[aoi_geom], crs="EPSG:4326")

    # 4) Clip favela polygons to AOI
    gdf_sub = gpd.clip(gdf, aoi_gdf)

    # 5) Save
    gdf_sub.to_file(out_path, layer=out_layer, driver="GPKG")

    print("✅ AOI source: OSM boundary (forced)")
    print(f"✅ Saved Brasília subset: {out_path} (layer={out_layer})")
    print(f"✅ Rows: {len(gdf_sub)}")

if __name__ == "__main__":
    main()