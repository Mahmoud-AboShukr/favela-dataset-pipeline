from pathlib import Path
import numpy as np
import rasterio
from skimage.morphology import remove_small_objects, binary_closing, disk

IN_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_full_clip.tif")
OUT_MASK = Path("data/interim/masks/brasilia_settlement_mask.tif")
OUT_MASK.parent.mkdir(parents=True, exist_ok=True)

# Start parameters (we will tune with QC)
THRESHOLD = 10        # try 5–15 first (GHSL is 0..100)
MIN_PIXELS = 200      # 200 px @10m => 20,000 m² (remove tiny specks)
CLOSE_RADIUS = 2      # fill small gaps (~20m)

def main():
    with rasterio.open(IN_TIF) as src:
        ghsl = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata

    valid = (ghsl != nodata) if nodata is not None else np.ones_like(ghsl, dtype=bool)
    built = (ghsl >= THRESHOLD) & valid

    # Reduce holes / patchiness
    built = binary_closing(built, footprint=disk(CLOSE_RADIUS))
    built = remove_small_objects(built, min_size=MIN_PIXELS)

    mask_u8 = built.astype("uint8")

    meta.update({"dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"})
    with rasterio.open(OUT_MASK, "w", **meta) as dst:
        dst.write(mask_u8, 1)

    print("✅ Saved settlement mask:", OUT_MASK)
    print("Stats:")
    print("  threshold:", THRESHOLD)
    print("  min_pixels:", MIN_PIXELS)
    print("  close_radius:", CLOSE_RADIUS)
    print("  pixels_on:", int(mask_u8.sum()))

if __name__ == "__main__":
    main()