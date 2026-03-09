from pathlib import Path
import osmnx as ox
import geopandas as gpd

OUT = Path("data/interim/aoi/brasilia_boundary.gpkg")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Try multiple names. Some return polygons, some return points.
QUERIES = [
    "Distrito Federal, Brazil",              # often a polygon boundary
    "Brasília, Distrito Federal, Brazil",    # sometimes not polygon
    "Brasilia, Distrito Federal, Brazil",    # without accent
]

def try_geocode(q: str) -> gpd.GeoDataFrame | None:
    try:
        gdf = ox.geocode_to_gdf(q)
        # Keep only polygon-ish geometries
        poly = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        if len(poly) == 0:
            return None
        return poly
    except Exception:
        return None

def main():
    for q in QUERIES:
        gdf = try_geocode(q)
        if gdf is not None:
            gdf = gdf.reset_index(drop=True)
            gdf.to_file(OUT, layer="brasilia_boundary", driver="GPKG")
            print(f"✅ Saved boundary from query: {q}")
            print("✅ Output:", OUT)
            return

    raise RuntimeError(
        "Could not get a (Multi)Polygon boundary from Nominatim for any query.\n"
        "Use Solution B (Overpass admin boundary query) instead."
    )

if __name__ == "__main__":
    main()