from pathlib import Path
import rasterio

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
    "belo_horizonte",
    "salvador",
    "manaus",
]


def main():
    for city in CITIES:
        path = Path(f"data/interim/mapbiomas_10m_clips/{city}/mapbiomas_10m_{city}_aoi_clip.tif")

        if not path.exists():
            print(f"[MISSING] {path}")
            continue

        with rasterio.open(path) as src:
            print(
                f"{city}: "
                f"crs={src.crs}, "
                f"width={src.width}, "
                f"height={src.height}, "
                f"count={src.count}, "
                f"dtype={src.dtypes[0]}"
            )


if __name__ == "__main__":
    main()