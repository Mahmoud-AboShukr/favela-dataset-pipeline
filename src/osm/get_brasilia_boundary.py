# src/osm/get_brasilia_boundary.py
from pathlib import Path
import osmnx as ox
import geopandas as gpd

OUT = Path("data/interim/aoi/brasilia_boundary.gpkg")
OUT.parent.mkdir(parents=True, exist_ok=True)

LAYER = "brasilia_boundary"

CANDIDATES = [
    "Distrito Federal, Brazil",
    "Brasília, Distrito Federal, Brazil",
    "Brasilia, Distrito Federal, Brazil",
]

def main():
    last_err = None
    for q in CANDIDATES:
        try:
            gdf = ox.geocode_to_gdf(q)
            gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
            if gdf.empty:
                raise ValueError("Result is not polygon/multipolygon.")
            # keep only a few columns
            keep = [c for c in ["display_name", "class", "type"] if c in gdf.columns]
            gdf = gdf[keep + ["geometry"]].copy()

            gdf.to_file(OUT, layer=LAYER, driver="GPKG")
            print(f"✅ Saved OSM AOI from query: {q}")
            print("✅ Output:", OUT)
            return
        except Exception as e:
            last_err = e

    raise RuntimeError(f"Could not produce polygon AOI from OSM queries. Last error: {last_err}")

if __name__ == "__main__":
    main()