from pathlib import Path
import tempfile
import shutil

import numpy as np
import rasterio
from scipy import ndimage


IN_PATH = Path("data/interim/masks/brasilia_favela_refined_mapbiomas_10m_no_ring_v2_2_remove_uncertain.tif")
OUT_PATH = Path("data/interim/masks/brasilia_favela_refined_mapbiomas_10m_no_ring_v2_2_fillholes_9px.tif")

OUT_NODATA = 255
MAX_HOLE_SIZE = 9


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

    for label_id in range(1, num + 1):
        comp = labeled == label_id
        size = int(comp.sum())

        if size > max_hole_size:
            continue

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

        filled = fill_small_holes(mask_bool, max_hole_size=MAX_HOLE_SIZE)
        out_arr = to_output(filled, valid)

        meta_template = src.meta.copy()

    save_mask(out_arr, meta_template, OUT_PATH)

    original_px = int(mask_bool.sum())
    filled_px = int(filled.sum())

    print(f"Saved: {OUT_PATH}")
    print(f"Original kept pixels: {original_px}")
    print(f"After filling <= {MAX_HOLE_SIZE}px holes: {filled_px}")
    print(f"Pixels added: {filled_px - original_px}")


if __name__ == "__main__":
    main()