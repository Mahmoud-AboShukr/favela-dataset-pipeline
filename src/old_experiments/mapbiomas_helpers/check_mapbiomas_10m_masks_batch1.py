from pathlib import Path
import numpy as np
import rasterio

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

def check_one(path: Path) -> None:
    if not path.exists():
        print(f"[MISSING] {path}")
        return

    with rasterio.open(path) as src:
        arr = src.read(1)
        unique = np.unique(arr)
        print(
            f"{path.name}: crs={src.crs}, shape=({src.height}, {src.width}), "
            f"dtype={src.dtypes[0]}, unique={unique.tolist()}"
        )

def main():
    for city in CITIES:
        print(f"\n=== {city} ===")
        veg = Path(f"data/interim/masks/{city}/{city}_mapbiomas_10m_vegetation_mask_strict.tif")
        built = Path(f"data/interim/masks/{city}/{city}_mapbiomas_10m_built_mask.tif")
        check_one(veg)
        check_one(built)

if __name__ == "__main__":
    main()