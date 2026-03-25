from pathlib import Path
import numpy as np
import rasterio
from skimage.morphology import remove_small_objects, binary_closing, disk
from scipy.ndimage import binary_fill_holes

IN_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_aoi_clip.tif")
OUT_DIR = Path("data/interim/masks/sweeps")
OUT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLDS = [0,1, 3, 5, 8]
CLOSE_RADIUS = 5
MIN_PIXELS = 50

def main():
    with rasterio.open(IN_TIF) as src:
        ghsl = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata

    valid = (ghsl != nodata) if nodata is not None else np.ones_like(ghsl, dtype=bool)

    for t in THRESHOLDS:
        built = (ghsl >= t) & valid
        built = binary_closing(built, footprint=disk(CLOSE_RADIUS))
        built = binary_fill_holes(built)
        built = remove_small_objects(built, min_size=MIN_PIXELS)
        built = built & valid

        mask_u8 = built.astype("uint8")

        out_meta = meta.copy()
        out_meta.update({"dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"})

        out_path = OUT_DIR / f"brasilia_settlement_t{t}.tif"
        with rasterio.open(out_path, "w", **out_meta) as dst:
            dst.write(mask_u8, 1)

        valid_pixels = int(valid.sum())
        pixels_on = int(mask_u8.sum())
        ratio = pixels_on / valid_pixels if valid_pixels else 0.0

        print(f"t={t}: pixels_on={pixels_on} ratio_on_valid={ratio:.4f} saved={out_path}")

if __name__ == "__main__":
    main()