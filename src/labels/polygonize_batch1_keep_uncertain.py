from pathlib import Path

import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape


CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

MASK_ROOT = Path("data/interim/masks")
OUT_ROOT = Path("data/processed/polygons")


def polygonize_one_city(city: str) -> None:
    in_path = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain.tif"
    raw_out = OUT_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_raw.gpkg"
    dissolved_out = OUT_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_dissolved.gpkg"

    if not in_path.exists():
        raise FileNotFoundError(f"Input raster not found: {in_path}")

    raw_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(in_path) as src:
        arr = src.read(1)
        transform = src.transform
        crs = src.crs

        # Keep only pixels == 1
        mask = arr == 1

        feats = []
        for geom, value in shapes(arr, mask=mask, transform=transform):
            if int(value) == 1:
                feats.append({
                    "geometry": shape(geom),
                    "value": 1
                })

    if not feats:
        raise ValueError(f"No kept polygons found for city: {city}")

    gdf = gpd.GeoDataFrame(feats, crs=crs)
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()

    # Save raw polygonized output
    gdf.to_file(raw_out, driver="GPKG")

    # Dissolve all kept pieces into multipart geometry
    dissolved = gdf.dissolve(by="value").reset_index(drop=True)
    dissolved["source"] = f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain"
    dissolved.to_file(dissolved_out, driver="GPKG")

    print(f"\n=== {city} ===")
    print(f"Input:          {in_path}")
    print(f"Raw output:     {raw_out}")
    print(f"Dissolved out:  {dissolved_out}")
    print(f"Raw pieces:     {len(gdf)}")
    print(f"Dissolved rows: {len(dissolved)}")


def main():
    for city in CITIES:
        polygonize_one_city(city)

    print("\nDone.")


if __name__ == "__main__":
    main()