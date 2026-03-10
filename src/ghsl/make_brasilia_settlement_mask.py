from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from skimage.morphology import remove_small_objects, binary_closing, disk
from scipy.ndimage import binary_fill_holes


# Inputs/Outputs
IN_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_aoi_clip.tif")
OUT_MASK = Path("data/interim/masks/brasilia_settlement_mask.tif")
OUT_MASK.parent.mkdir(parents=True, exist_ok=True)

# Parameters (tune with QC)
THRESHOLD = 1         # GHSL built-up values are ~0..100
CLOSE_RADIUS = 5      # pixels; 5px @10m ~ 50m gap filling
MIN_PIXELS = 200       # remove very tiny specks (50px @10m ≈ 5,000 m²)


def _safe_write(out_path: Path, meta: dict, arr_u8: np.ndarray) -> Path:
    """
    Write to a temp file then replace. Prevents crashes when output is locked (QGIS/OneDrive).
    If replace fails, the temp file is kept.
    """
    out_path = Path(out_path)
    tmp_path = out_path.with_name(out_path.stem + "_tmp.tif")

    with rasterio.open(tmp_path, "w", **meta) as dst:
        dst.write(arr_u8, 1)

    try:
        if out_path.exists():
            out_path.unlink()  # may fail if locked
        tmp_path.replace(out_path)
        return out_path
    except Exception as e:
        print(f"⚠ Could not overwrite {out_path} (likely locked). Kept: {tmp_path}")
        print(f"   Reason: {e}")
        return tmp_path


def _mask_stats(mask_bool: np.ndarray, valid_bool: np.ndarray) -> tuple[int, int, float]:
    """
    Returns (valid_pixels, pixels_on, ratio_on_valid).
    """
    valid_pixels = int(valid_bool.sum())
    pixels_on = int(mask_bool.sum())
    ratio = pixels_on / valid_pixels if valid_pixels else 0.0
    return valid_pixels, pixels_on, ratio


def main():
    if not IN_TIF.exists():
        raise FileNotFoundError(f"Input GHSL clip not found: {IN_TIF}")

    # 1) Read GHSL clip and metadata
    with rasterio.open(IN_TIF) as src:
        ghsl = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata

    # 2) Build validity mask (exclude nodata)
    valid = (ghsl != nodata) if nodata is not None else np.ones_like(ghsl, dtype=bool)

    # 3) Threshold to built-up (boolean)
    built = (ghsl >= THRESHOLD) & valid
    valid_pixels, pixels_on_raw, ratio_raw = _mask_stats(built, valid)

    # 4) Morphology to reduce patchiness
    # 4.1 closing connects nearby built-up pixels and fills small gaps
    built = binary_closing(built, footprint=disk(CLOSE_RADIUS))

    # 4.2 fill holes inside built-up blobs
    built = binary_fill_holes(built)

    # 4.3 remove tiny isolated components
    built = remove_small_objects(built, min_size=MIN_PIXELS)

    # Ensure outside-valid area stays False
    built = built & valid

    valid_pixels2, pixels_on_final, ratio_final = _mask_stats(built, valid)

    # 5) Write output as uint8 mask (0/1)
    mask_u8 = built.astype("uint8")

    out_meta = meta.copy()
    out_meta.update({
        "dtype": "uint8",
        "count": 1,
        "nodata": 0,
        "compress": "deflate",
    })

    saved_path = _safe_write(OUT_MASK, out_meta, mask_u8)

    # 6) Print QC stats
    print("✅ Saved settlement mask:", saved_path)
    print("Stats:")
    print("  input:", str(IN_TIF))
    print("  CRS:", out_meta.get("crs"))
    print("  THRESHOLD:", THRESHOLD)
    print("  CLOSE_RADIUS:", CLOSE_RADIUS)
    print("  MIN_PIXELS:", MIN_PIXELS)
    print("  valid_pixels:", valid_pixels)
    print("  pixels_on_raw:", pixels_on_raw)
    print("  ratio_raw_on_valid:", ratio_raw)
    print("  pixels_on_final:", pixels_on_final)
    print("  ratio_final_on_valid:", ratio_final)


if __name__ == "__main__":
    main()