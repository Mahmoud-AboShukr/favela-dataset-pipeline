from pathlib import Path
import tempfile
import shutil

import numpy as np
import rasterio
from scipy import ndimage


IN_PATH = Path("data/interim/masks/brasilia_favela_refined_mapbiomas_no_ring_v2_2_remove_uncertain.tif")
OUT_PATH_1PX = Path("data/interim/masks/brasilia_favela_refined_mapbiomas_no_ring_v2_2_fillholes_1px.tif")
OUT_PATH_4PX = Path("data/interim/masks/brasilia_favela_refined_mapbiomas_no_ring_v2_2_fillholes_4px.tif")

OUT_NODATA = 255


def fill_small_holes(mask_bool: np.ndarray, max_hole_size: int) -> np.ndarray:
    """
    Fill background holes fully enclosed by foreground if their size
    is <= max_hole_size pixels.
    """
    background = ~mask_bool

    labeled, num = ndimage.label(background)
    if num == 0:
        return mask_bool.copy()

    filled = mask_bool.copy()

    h, w = mask_bool.shape

    for label_id in range(1, num + 1):
        comp = labeled == label_id
        size = int(comp.sum())

        # Skip large holes
        if size > max_hole_size:
            continue

        # Check whether this background component touches image border
        touches_border = (
            comp[0, :].any() or comp[-1, :].any() or
            comp[:, 0].any() or comp[:, -1].any()
        )

        # Only fill enclosed holes, not outside background
        if not touches_border:
            filled[comp] = True

    return filled


def to_output(mask_bool: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = np.full(mask_bool.shape, OUT_NODATA, dtype=np.uint8)
    out[valid] = 0
    out[valid & mask_bool] = 1
    return out


def save_mask(arr: np.ndarray, meta_template: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    meta = meta_template.copy()
    meta.update({
        "dtype": "uint8",
        "count": 1,
        "nodata": OUT_NODATA,
        "compress": "lzw",
    })

    with tempfile.NamedTemporaryFile(
        suffix=".tif",
        delete=False,
        dir=str(out_path.parent)
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with rasterio.open(tmp_path, "w", **meta) as dst:
            dst.write(arr, 1)
        shutil.move(str(tmp_path), str(out_path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Input refined mask not found: {IN_PATH}")

    with rasterio.open(IN_PATH) as src:
        arr = src.read(1)
        nodata = src.nodata

        valid = np.ones(arr.shape, dtype=bool)
        if nodata is not None:
            valid = arr != nodata

        mask_bool = (arr == 1) & valid

        filled_1 = fill_small_holes(mask_bool, max_hole_size=1)
        filled_4 = fill_small_holes(mask_bool, max_hole_size=4)

        out_1 = to_output(filled_1, valid)
        out_4 = to_output(filled_4, valid)

        meta_template = src.meta.copy()

    save_mask(out_1, meta_template, OUT_PATH_1PX)
    save_mask(out_4, meta_template, OUT_PATH_4PX)

    original_px = int(mask_bool.sum())
    filled_1_px = int(filled_1.sum())
    filled_4_px = int(filled_4.sum())

    print(f"Saved: {OUT_PATH_1PX}")
    print(f"Saved: {OUT_PATH_4PX}")
    print()
    print(f"Original kept pixels: {original_px}")
    print(f"After filling <=1px holes: {filled_1_px}  (+{filled_1_px - original_px})")
    print(f"After filling <=4px holes: {filled_4_px}  (+{filled_4_px - original_px})")


if __name__ == "__main__":
    main()