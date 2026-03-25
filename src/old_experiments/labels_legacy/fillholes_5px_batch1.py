from pathlib import Path
import tempfile
import shutil

import numpy as np
import rasterio
from scipy import ndimage


CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

MASK_ROOT = Path("data/interim/masks")
OUT_NODATA = 255
MAX_HOLE_SIZE = 5  # fill connected zero-components up to 5 pixels


def save_uint8(arr: np.ndarray, meta_template: dict, out_path: Path) -> None:
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


def fill_small_holes(binary_mask: np.ndarray, max_hole_size: int) -> tuple[np.ndarray, int]:
    """
    binary_mask: True where favela is kept, False otherwise.
    Fill interior connected False-components up to max_hole_size pixels.
    """
    holes = ~binary_mask

    # Label connected False regions
    structure = ndimage.generate_binary_structure(2, 1)  # 4-connectivity
    labeled, num = ndimage.label(holes, structure=structure)

    if num == 0:
        return binary_mask.copy(), 0

    # Regions touching image border are not interior holes
    border_labels = set(np.unique(np.concatenate([
        labeled[0, :],
        labeled[-1, :],
        labeled[:, 0],
        labeled[:, -1],
    ])))
    border_labels.discard(0)

    counts = np.bincount(labeled.ravel())
    filled = binary_mask.copy()
    holes_filled = 0

    for label_id in range(1, num + 1):
        if label_id in border_labels:
            continue

        size = counts[label_id]
        if size <= max_hole_size:
            filled[labeled == label_id] = True
            holes_filled += 1

    return filled, holes_filled


def to_output(mask_bool: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = np.full(mask_bool.shape, OUT_NODATA, dtype=np.uint8)
    out[valid] = 0
    out[valid & mask_bool] = 1
    return out


def process_city(city: str) -> None:
    in_path = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_remove_uncertain.tif"
    out_path = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_fillholes_5px.tif"

    if not in_path.exists():
        raise FileNotFoundError(f"Input refined mask not found: {in_path}")

    with rasterio.open(in_path) as src:
        arr = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata

        valid = arr != nodata if nodata is not None else np.ones(arr.shape, dtype=bool)
        kept = (arr == 1) & valid

        filled_kept, holes_filled = fill_small_holes(kept, MAX_HOLE_SIZE)
        out_arr = to_output(filled_kept, valid)

        original_kept = int(kept.sum())
        filled_kept_px = int(filled_kept.sum())
        added_px = filled_kept_px - original_kept

    save_uint8(out_arr, meta, out_path)

    print(f"\n=== {city} ===")
    print(f"Input:  {in_path}")
    print(f"Output: {out_path}")
    print(f"Original kept pixels: {original_kept}")
    print(f"Filled kept pixels:   {filled_kept_px}")
    print(f"Added pixels:         {added_px}")
    print(f"Holes filled:         {holes_filled}")


def main():
    for city in CITIES:
        process_city(city)

    print("\nDone.")


if __name__ == "__main__":
    main()