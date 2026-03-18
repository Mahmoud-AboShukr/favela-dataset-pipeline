from pathlib import Path
import geopandas as gpd

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
    "belo_horizonte",
    "salvador",
    "manaus",
]

def main():
    for city in CITIES:
        path = Path(f"data/interim/aoi/{city}/{city}_aoi.gpkg")

        if not path.exists():
            print(f"[MISSING] {path}")
            continue

        gdf = gpd.read_file(path)
        print(
            f"{city}: rows={len(gdf)}, crs={gdf.crs}, valid={gdf.is_valid.all()}"
        )

if __name__ == "__main__":
    main()