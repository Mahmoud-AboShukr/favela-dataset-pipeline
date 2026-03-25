from pathlib import Path
import numpy as np
import rasterio

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

def main():
    for city in CITIES:
        path = Path(f"data/interim/masks/{city}/{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_fillholes_5px.tif")

        if not path.exists():
            print(f"[MISSING] {path}")
            continue

        with rasterio.open(path) as src:
            arr = src.read(1)
            unique = np.unique(arr)
            kept = int((arr == 1).sum())
            print(
                f"{city}: crs={src.crs}, shape=({src.height}, {src.width}), "
                f"dtype={src.dtypes[0]}, unique={unique.tolist()}, kept_pixels={kept}"
            )

if __name__ == "__main__":
    main()