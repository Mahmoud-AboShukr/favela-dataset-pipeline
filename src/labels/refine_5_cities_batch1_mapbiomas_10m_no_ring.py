from pathlib import Path
import tempfile
import shutil

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize


CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

RASTER_ROOT = Path("data/interim/mapbiomas_10m_clips")
MASK_ROOT = Path("data/interim/masks")
AOI_ROOT = Path("data/interim/aoi")

OUT_NODATA = 255


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


def load_favelas(city: str) -> gpd.GeoDataFrame:
    favela_path = AOI_ROOT / city / f"favelas_{city}.gpkg"

    if not favela_path.exists():
        raise FileNotFoundError(f"Favela file not found: {favela_path}")

    gdf = gpd.read_file(favela_path)

    if gdf.empty:
        raise ValueError(f"Favela layer is empty for city: {city}")

    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()

    if gdf.empty:
        raise ValueError(f"No valid favela geometries found for city: {city}")

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


def to_output(mask_bool: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = np.full(mask_bool.shape, OUT_NODATA, dtype=np.uint8)
    out[valid] = 0
    out[valid & mask_bool] = 1
    return out


def refine_one_city(city: str) -> None:
    mapbiomas_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    veg_mask_path = MASK_ROOT / city / f"{city}_mapbiomas_10m_vegetation_mask_strict.tif"
    built_mask_path = MASK_ROOT / city / f"{city}_mapbiomas_10m_built_mask.tif"

    out_original = MASK_ROOT / city / f"{city}_favela_original_mask_10m.tif"
    out_nr_v21 = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain.tif"
    out_nr_v22 = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_remove_uncertain.tif"

    if not mapbiomas_path.exists():
        raise FileNotFoundError(f"Reference raster not found: {mapbiomas_path}")
    if not veg_mask_path.exists():
        raise FileNotFoundError(f"Vegetation mask not found: {veg_mask_path}")
    if not built_mask_path.exists():
        raise FileNotFoundError(f"Built mask not found: {built_mask_path}")

    favelas = load_favelas(city)

    with (
        rasterio.open(mapbiomas_path) as ref_src,
        rasterio.open(veg_mask_path) as veg_src,
        rasterio.open(built_mask_path) as built_src
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

        nr_v21 = original.copy()
        nr_v21[original & veg_is_1 & (~built_is_1)] = False

        nr_v22 = original.copy()
        nr_v22[original & (~built_is_1)] = False

        original_out = to_output(original, valid)
        nr_v21_out = to_output(nr_v21, valid)
        nr_v22_out = to_output(nr_v22, valid)

        meta_template = ref_src.meta.copy()

    save_uint8(original_out, meta_template, out_original)
    save_uint8(nr_v21_out, meta_template, out_nr_v21)
    save_uint8(nr_v22_out, meta_template, out_nr_v22)

    original_px = int(np.sum(original))
    nr_v21_px = int(np.sum(nr_v21))
    nr_v22_px = int(np.sum(nr_v22))

    inside_built_px = int(np.sum(original & built_is_1))
    inside_veg_px = int(np.sum(original & veg_is_1))
    inside_uncertain_px = int(np.sum(original & (~veg_is_1) & (~built_is_1)))

    print(f"\n=== {city} ===")
    print(f"Saved: {out_original}")
    print(f"Saved: {out_nr_v21}")
    print(f"Saved: {out_nr_v22}")
    print()
    print(f"Original favela pixels: {original_px}")
    print(f"Inside-polygon built pixels: {inside_built_px}")
    print(f"Inside-polygon vegetation pixels: {inside_veg_px}")
    print(f"Inside-polygon uncertain pixels: {inside_uncertain_px}")
    print()
    print(f"No-ring V2.1 kept favela pixels: {nr_v21_px}")
    print(f"No-ring V2.2 kept favela pixels: {nr_v22_px}")
    print(f"No-ring V2.1 removed pixels from original: {original_px - nr_v21_px}")
    print(f"No-ring V2.2 removed pixels from original: {original_px - nr_v22_px}")


def main():
    for city in CITIES:
        refine_one_city(city)

    print("\nDone.")


if __name__ == "__main__":
    main()