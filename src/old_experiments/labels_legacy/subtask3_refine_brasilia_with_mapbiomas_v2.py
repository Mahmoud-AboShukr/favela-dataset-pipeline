from pathlib import Path
import tempfile
import shutil

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import binary_erosion


MAPBIOMAS_PATH = Path("data/interim/mapbiomas_clips/mapbiomas_brasilia_aoi_clip.tif")
VEG_MASK_PATH = Path("data/interim/masks/brasilia_mapbiomas_vegetation_mask_strict.tif")
BUILT_MASK_PATH = Path("data/interim/masks/brasilia_mapbiomas_built_mask.tif")
FAVELA_PATH = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
FAVELA_LAYER = None  # set explicitly if needed

OUT_DIR = Path("data/interim/masks")

OUT_ORIGINAL = OUT_DIR / "brasilia_favela_original_mask.tif"
OUT_CORE = OUT_DIR / "brasilia_favela_core_mask_12px.tif"
OUT_RING = OUT_DIR / "brasilia_favela_ring_mask_12px.tif"
OUT_V21 = OUT_DIR / "brasilia_favela_refined_mapbiomas_v2_1_keep_uncertain_12px.tif"
OUT_V22 = OUT_DIR / "brasilia_favela_refined_mapbiomas_v2_2_remove_uncertain_12px.tif"

OUT_NODATA = 255
EROSION_PIXELS = 12


def save_uint8(mask_arr: np.ndarray, meta_template: dict, out_path: Path) -> None:
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
            dst.write(mask_arr, 1)
        shutil.move(str(tmp_path), str(out_path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def load_favelas() -> gpd.GeoDataFrame:
    if not FAVELA_PATH.exists():
        raise FileNotFoundError(f"Favela file not found: {FAVELA_PATH}")

    if FAVELA_LAYER:
        gdf = gpd.read_file(FAVELA_PATH, layer=FAVELA_LAYER)
    else:
        gdf = gpd.read_file(FAVELA_PATH)

    if gdf.empty:
        raise ValueError("Favela layer is empty.")

    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()

    if gdf.empty:
        raise ValueError("No valid favela geometries found.")

    return gdf


def rasterize_favelas(gdf: gpd.GeoDataFrame, ref_src) -> np.ndarray:
    if gdf.crs is None:
        raise ValueError("Favela layer has no CRS.")

    if gdf.crs != ref_src.crs:
        gdf = gdf.to_crs(ref_src.crs)

    shapes = ((geom, 1) for geom in gdf.geometry if geom is not None and not geom.is_empty)

    arr = rasterize(
        shapes=shapes,
        out_shape=(ref_src.height, ref_src.width),
        transform=ref_src.transform,
        fill=0,
        dtype="uint8",
        all_touched=False
    )

    return arr


def ensure_aligned(ref_src, other_src, name: str) -> None:
    if (
        ref_src.width != other_src.width
        or ref_src.height != other_src.height
        or ref_src.transform != other_src.transform
        or ref_src.crs != other_src.crs
    ):
        raise ValueError(f"{name} is not aligned with the reference MapBiomas raster.")


def main():
    if not MAPBIOMAS_PATH.exists():
        raise FileNotFoundError(f"Reference raster not found: {MAPBIOMAS_PATH}")
    if not VEG_MASK_PATH.exists():
        raise FileNotFoundError(f"Vegetation mask not found: {VEG_MASK_PATH}")
    if not BUILT_MASK_PATH.exists():
        raise FileNotFoundError(f"Built mask not found: {BUILT_MASK_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    favelas = load_favelas()

    with (
        rasterio.open(MAPBIOMAS_PATH) as ref_src,
        rasterio.open(VEG_MASK_PATH) as veg_src,
        rasterio.open(BUILT_MASK_PATH) as built_src
    ):
        ensure_aligned(ref_src, veg_src, "Vegetation mask")
        ensure_aligned(ref_src, built_src, "Built mask")

        ref_arr = ref_src.read(1)
        ref_nodata = ref_src.nodata

        valid = np.ones(ref_arr.shape, dtype=bool)
        if ref_nodata is not None:
            valid = ref_arr != ref_nodata

        veg = veg_src.read(1)
        built = built_src.read(1)

        veg_is_1 = veg == 1
        built_is_1 = built == 1

        original = rasterize_favelas(favelas, ref_src).astype(bool)
        original = original & valid

        core = binary_erosion(original, iterations=EROSION_PIXELS)
        ring = original & (~core)

        # V2.1: remove vegetation, keep built, keep uncertain
        v21 = original.copy()
        v21[ring & veg_is_1 & (~built_is_1)] = False

        # V2.2: keep only built in the ring; remove vegetation + uncertain
        v22 = original.copy()
        v22[ring & (~built_is_1)] = False

        def to_output(mask_bool: np.ndarray) -> np.ndarray:
            out = np.full(mask_bool.shape, OUT_NODATA, dtype=np.uint8)
            out[valid] = 0
            out[valid & mask_bool] = 1
            return out

        original_out = to_output(original)
        core_out = to_output(core)
        ring_out = to_output(ring)
        v21_out = to_output(v21)
        v22_out = to_output(v22)

        meta_template = ref_src.meta.copy()

    save_uint8(original_out, meta_template, OUT_ORIGINAL)
    save_uint8(core_out, meta_template, OUT_CORE)
    save_uint8(ring_out, meta_template, OUT_RING)
    save_uint8(v21_out, meta_template, OUT_V21)
    save_uint8(v22_out, meta_template, OUT_V22)

    original_px = int(np.sum(original))
    core_px = int(np.sum(core))
    ring_px = int(np.sum(ring))
    v21_px = int(np.sum(v21))
    v22_px = int(np.sum(v22))

    protected_ring_px = int(np.sum(ring & built_is_1))
    veg_ring_px = int(np.sum(ring & veg_is_1))
    uncertain_ring_px = int(np.sum(ring & (~veg_is_1) & (~built_is_1)))

    print(f"Saved: {OUT_ORIGINAL}")
    print(f"Saved: {OUT_CORE}")
    print(f"Saved: {OUT_RING}")
    print(f"Saved: {OUT_V21}")
    print(f"Saved: {OUT_V22}")
    print()
    print(f"Original favela pixels: {original_px}")
    print(f"Core pixels: {core_px}")
    print(f"Ring pixels: {ring_px}")
    print()
    print(f"Built-supported ring pixels: {protected_ring_px}")
    print(f"Vegetation ring pixels: {veg_ring_px}")
    print(f"Uncertain ring pixels: {uncertain_ring_px}")
    print()
    print(f"V2.1 kept favela pixels: {v21_px}")
    print(f"V2.2 kept favela pixels: {v22_px}")
    print(f"V2.1 removed pixels from original: {original_px - v21_px}")
    print(f"V2.2 removed pixels from original: {original_px - v22_px}")


if __name__ == "__main__":
    main()