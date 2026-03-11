from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from skimage.morphology import remove_small_objects, binary_closing, disk
from scipy.ndimage import binary_fill_holes


# =========================
# Inputs / Outputs
# =========================
IN_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_aoi_clip.tif")

OUT_DIR = Path("data/interim/masks/test_brasilia")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FINAL = OUT_DIR / "brasilia_settlement_mask.tif"
OUT_VALID = OUT_DIR / "debug_01_valid_mask.tif"
OUT_RAW = OUT_DIR / "debug_02_raw_threshold_mask.tif"
OUT_CLOSE = OUT_DIR / "debug_03_after_closing.tif"
OUT_FILL = OUT_DIR / "debug_04_after_fill_holes.tif"
OUT_SMALL = OUT_DIR / "debug_05_after_remove_small.tif"


# =========================
# Parameters
# =========================
# Use recall-friendly defaults first while diagnosing false negatives.
THRESHOLD = 1       # minimum GHSL built-up value to consider as settlement
CLOSE_RADIUS = 7    # stronger gap filling than 5 px to reconnect fragmented areas
MIN_PIXELS = 50     # keep smaller true settlement fragments while debugging

# If True, save each intermediate stage as a GeoTIFF for QGIS inspection.
SAVE_DEBUG_STAGES = True


def _safe_write(out_path: Path, meta: dict, arr: np.ndarray) -> Path:
    """
    Write to a temp file then replace the target if possible.
    Prevents crashes when output is locked (e.g. by QGIS / OneDrive).
    """
    out_path = Path(out_path)
    tmp_path = out_path.with_name(out_path.stem + "_tmp.tif")

    with rasterio.open(tmp_path, "w", **meta) as dst:
        dst.write(arr, 1)

    try:
        if out_path.exists():
            out_path.unlink()
        tmp_path.replace(out_path)
        return out_path
    except Exception as e:
        print(f"⚠ Could not overwrite {out_path}. Kept temp file: {tmp_path}")
        print(f"   Reason: {e}")
        return tmp_path


def _mask_stats(mask_bool: np.ndarray, valid_bool: np.ndarray) -> tuple[int, int, float]:
    """
    Returns:
        valid_pixels: number of valid raster pixels
        pixels_on: number of True pixels in the mask
        ratio_on_valid: pixels_on / valid_pixels
    """
    valid_pixels = int(valid_bool.sum())
    pixels_on = int(mask_bool.sum())
    ratio_on_valid = pixels_on / valid_pixels if valid_pixels else 0.0
    return valid_pixels, pixels_on, ratio_on_valid


def _print_stage_stats(stage_name: str, mask_bool: np.ndarray, valid_bool: np.ndarray) -> None:
    valid_pixels, pixels_on, ratio = _mask_stats(mask_bool, valid_bool)
    print(f"  [{stage_name}]")
    print(f"    valid_pixels: {valid_pixels}")
    print(f"    pixels_on: {pixels_on}")
    print(f"    ratio_on_valid: {ratio:.6f}")


def _write_bool_mask(out_path: Path, base_meta: dict, mask_bool: np.ndarray) -> Path:
    """
    Save boolean mask as uint8 GeoTIFF:
    0 = background / invalid
    1 = mask on
    """
    out_meta = base_meta.copy()
    out_meta.update(
        {
            "dtype": "uint8",
            "count": 1,
            "nodata": 0,
            "compress": "deflate",
        }
    )
    arr_u8 = mask_bool.astype("uint8")
    return _safe_write(out_path, out_meta, arr_u8)


def main():
    if not IN_TIF.exists():
        raise FileNotFoundError(f"Input GHSL clip not found: {IN_TIF}")

    # 1) Read GHSL clip and metadata
    with rasterio.open(IN_TIF) as src:
        ghsl = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata
        transform = src.transform

    # Approximate pixel size for reporting area
    pixel_width = abs(transform.a)
    pixel_height = abs(transform.e)
    pixel_area_m2 = pixel_width * pixel_height

    # 2) Build validity mask (exclude nodata)
    if nodata is not None:
        valid = ghsl != nodata
    else:
        valid = np.ones_like(ghsl, dtype=bool)

    # Save validity mask for debugging
    if SAVE_DEBUG_STAGES:
        _write_bool_mask(OUT_VALID, meta, valid)

    # 3) Raw threshold mask
    raw = (ghsl >= THRESHOLD) & valid

    # 4) Closing: connect nearby fragments / fill narrow gaps
    after_closing = binary_closing(raw, footprint=disk(CLOSE_RADIUS))

    # Keep only valid area after morphology
    after_closing = after_closing & valid

    # 5) Fill holes inside connected blobs
    after_fill = binary_fill_holes(after_closing)

    # Keep only valid area after fill
    after_fill = after_fill & valid

    # 6) Remove tiny isolated components
    final_mask = remove_small_objects(after_fill, min_size=MIN_PIXELS)

    # Ensure outside-valid area stays False
    final_mask = final_mask & valid

    # 7) Save all intermediate stages
    if SAVE_DEBUG_STAGES:
        _write_bool_mask(OUT_RAW, meta, raw)
        _write_bool_mask(OUT_CLOSE, meta, after_closing)
        _write_bool_mask(OUT_FILL, meta, after_fill)
        _write_bool_mask(OUT_SMALL, meta, final_mask)

    saved_final = _write_bool_mask(OUT_FINAL, meta, final_mask)

    # 8) Print parameter summary
    print("✅ Saved final settlement mask:", saved_final)
    print("Parameters:")
    print(f"  input: {IN_TIF}")
    print(f"  CRS: {meta.get('crs')}")
    print(f"  nodata: {nodata}")
    print(f"  THRESHOLD: {THRESHOLD}")
    print(f"  CLOSE_RADIUS: {CLOSE_RADIUS} px")
    print(f"  MIN_PIXELS: {MIN_PIXELS}")
    print(f"  pixel_size: {pixel_width:.3f} x {pixel_height:.3f}")
    print(f"  pixel_area_m2: {pixel_area_m2:.3f}")
    print(f"  MIN_PIXELS_area_m2: {MIN_PIXELS * pixel_area_m2:.3f}")

    # 9) Print stats per stage
    print("Stage stats:")
    _print_stage_stats("valid_mask", valid, valid)
    _print_stage_stats("raw_threshold", raw, valid)
    _print_stage_stats("after_closing", after_closing, valid)
    _print_stage_stats("after_fill_holes", after_fill, valid)
    _print_stage_stats("final_after_remove_small", final_mask, valid)

    if SAVE_DEBUG_STAGES:
        print("Debug outputs:")
        print(f"  valid mask: {OUT_VALID}")
        print(f"  raw threshold mask: {OUT_RAW}")
        print(f"  after closing: {OUT_CLOSE}")
        print(f"  after fill holes: {OUT_FILL}")
        print(f"  final after remove_small_objects: {OUT_SMALL}")


if __name__ == "__main__":
    main()