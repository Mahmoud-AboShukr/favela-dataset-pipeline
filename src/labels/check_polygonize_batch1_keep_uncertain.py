from pathlib import Path
import geopandas as gpd

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

def check_one(path: Path) -> None:
    if not path.exists():
        print(f"[MISSING] {path}")
        return

    gdf = gpd.read_file(path)
    print(
        f"{path.name}: rows={len(gdf)}, crs={gdf.crs}, valid={gdf.is_valid.all()}"
    )

def main():
    for city in CITIES:
        print(f"\n=== {city} ===")
        raw_path = Path(
            f"data/processed/polygons/{city}/{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_raw.gpkg"
        )
        dissolved_path = Path(
            f"data/processed/polygons/{city}/{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_dissolved.gpkg"
        )
        check_one(raw_path)
        check_one(dissolved_path)

if __name__ == "__main__":
    main()