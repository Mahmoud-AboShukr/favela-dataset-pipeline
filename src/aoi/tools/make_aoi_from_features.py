from pathlib import Path
import geopandas as gpd

IN_GPKG = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
IN_LAYER = "favelas_brasilia"

OUT_GPKG = Path("data/interim/aoi/brasilia_aoi_from_favelas.gpkg")
OUT_LAYER = "brasilia_aoi"

BUFFER_M = 5000  # 5 km buffer (tune: 2–10 km depending on how broad you want)

def main():
    gdf = gpd.read_file(IN_GPKG, layer=IN_LAYER)

    # Work in a metric CRS for buffering (Web Mercator ok for buffer size; UTM is better but more complex)
    gdf_m = gdf.to_crs("EPSG:3857")
    geom = gdf_m.geometry.union_all().buffer(BUFFER_M)

    aoi = gpd.GeoDataFrame({"name": ["brasilia_aoi_from_favelas"]}, geometry=[geom], crs="EPSG:3857")
    aoi = aoi.to_crs("EPSG:4326")

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    aoi.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")

    print("✅ Saved AOI:", OUT_GPKG, "layer:", OUT_LAYER)

if __name__ == "__main__":
    main()