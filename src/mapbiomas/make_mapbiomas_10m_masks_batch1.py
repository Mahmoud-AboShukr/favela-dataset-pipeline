from pathlib import Path
import tempfile
import shutil

import numpy as np
import rasterio


RASTER_ROOT = Path("data/interim/mapbiomas_10m_clips")
MASK_ROOT = Path("data/interim/masks")

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

# Frozen Batch 1 logic
STRICT_VEGETATION_CLASSES = {3, 4, 5, 6, 11, 12, 49, 50}
BUILT_CLASSES = {24}


def save_uint8_mask(mask_array: np.ndarray, meta: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_meta = meta.copy()
    out_meta.update({
        "count": 1,
        "dtype": "uint8",
        "nodata": 0,
    })

    with tempfile.NamedTemporaryFile(
        suffix=".tif",
        delete=False,
        dir=str(out_path.parent)
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with rasterio.open(tmp_path, "w", **out_meta) as dst:
            dst.write(mask_array.astype(np.uint8), 1)
        shutil.move(str(tmp_path), str(out_path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def build_masks_for_city(city: str) -> None:
    raster_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    veg_out = MASK_ROOT / city / f"{city}_mapbiomas_10m_vegetation_mask_strict.tif"
    built_out = MASK_ROOT / city / f"{city}_mapbiomas_10m_built_mask.tif"

    if not raster_path.exists():
        raise FileNotFoundError(f"Raster clip not found: {raster_path}")

    print(f"\n=== {city} ===")
    print(f"Reading: {raster_path}")

    with rasterio.open(raster_path) as src:
        arr = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata

        valid = np.ones(arr.shape, dtype=bool)
        if nodata is not None:
            valid &= arr != nodata

        veg_mask = np.isin(arr, list(STRICT_VEGETATION_CLASSES)) & valid
        built_mask = np.isin(arr, list(BUILT_CLASSES)) & valid

        save_uint8_mask(veg_mask.astype(np.uint8), meta, veg_out)
        save_uint8_mask(built_mask.astype(np.uint8), meta, built_out)

        veg_pixels = int(veg_mask.sum())
        built_pixels = int(built_mask.sum())
        valid_pixels = int(valid.sum())

        veg_ratio = 100 * veg_pixels / valid_pixels if valid_pixels else 0.0
        built_ratio = 100 * built_pixels / valid_pixels if valid_pixels else 0.0

        print(f"Saved strict vegetation mask: {veg_out}")
        print(f"Saved built mask:             {built_out}")
        print(f"Valid pixels:                {valid_pixels}")
        print(f"Vegetation pixels:           {veg_pixels} ({veg_ratio:.4f}%)")
        print(f"Built pixels:                {built_pixels} ({built_ratio:.4f}%)")


def main():
    for city in CITIES:
        build_masks_for_city(city)

    print("\nDone.")


if __name__ == "__main__":
    main()