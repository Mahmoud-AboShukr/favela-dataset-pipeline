from pathlib import Path
import tempfile
import shutil

import numpy as np
import rasterio


IN_PATH = Path("data/interim/mapbiomas_10m_clips/mapbiomas_10m_brasilia_aoi_clip.tif")
OUT_PATH = Path("data/interim/masks/brasilia_mapbiomas_10m_vegetation_mask_strict.tif")

OUT_NODATA = 255

# Conservative vegetation classes only
STRICT_VEGETATION_CLASSES = {3, 5, 6, 49}


def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Input MapBiomas 10 m clip not found: {IN_PATH}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(IN_PATH) as src:
        arr = src.read(1)
        src_nodata = src.nodata

        valid_mask = np.ones(arr.shape, dtype=bool)
        if src_nodata is not None:
            valid_mask = arr != src_nodata

        veg_mask = np.full(arr.shape, OUT_NODATA, dtype=np.uint8)
        veg_mask[valid_mask] = 0
        veg_mask[valid_mask & np.isin(arr, list(STRICT_VEGETATION_CLASSES))] = 1

        meta = src.meta.copy()
        meta.update({
            "dtype": "uint8",
            "count": 1,
            "nodata": OUT_NODATA,
            "compress": "lzw"
        })

        with tempfile.NamedTemporaryFile(
            suffix=".tif",
            delete=False,
            dir=str(OUT_PATH.parent)
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with rasterio.open(tmp_path, "w", **meta) as dst:
                dst.write(veg_mask, 1)
            shutil.move(str(tmp_path), str(OUT_PATH))
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    valid_pixels = int(np.sum(veg_mask != OUT_NODATA))
    vegetation_pixels = int(np.sum(veg_mask == 1))
    non_vegetation_pixels = int(np.sum(veg_mask == 0))

    print(f"Saved strict 10 m vegetation mask to: {OUT_PATH}")
    print(f"Strict vegetation classes: {sorted(STRICT_VEGETATION_CLASSES)}")
    print(f"Valid pixels: {valid_pixels}")
    print(f"Vegetation pixels (1): {vegetation_pixels}")
    print(f"Non-vegetation pixels (0): {non_vegetation_pixels}")
    if valid_pixels > 0:
        print(f"Vegetation share: {vegetation_pixels / valid_pixels * 100:.2f}%")


if __name__ == "__main__":
    main()