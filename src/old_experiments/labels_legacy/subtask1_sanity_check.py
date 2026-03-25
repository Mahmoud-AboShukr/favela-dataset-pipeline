import geopandas as gpd

gdf = gpd.read_file("data/interim/polygons_clean/favelas_clean.gpkg", layer="favelas_clean")

print("CRS:", gdf.crs)
print("Rows:", len(gdf))
print("Valid geometries:", gdf.is_valid.mean())
print("Bounds (minx, miny, maxx, maxy):", gdf.total_bounds)

# Basic ID checks
print("favela_id missing:", gdf["favela_id"].isna().sum())
print("favela_id duplicates:", gdf["favela_id"].duplicated().sum())