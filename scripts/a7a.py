import geopandas as gpd

gdf = gpd.read_file("data/interim/polygons_clean/favelas_clean.gpkg").to_crs("EPSG:4326")
print("bounds:", gdf.total_bounds)  # minx, miny, maxx, maxy