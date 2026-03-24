from pathlib import Path
import tempfile
import shutil

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize, shapes
from shapely.geometry import shape


CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
    "belo_horizonte",
    "salvador",
    "manaus",
]

RASTER_ROOT = Path("data/interim/mapbiomas_10m_clips")
MASK_ROOT = Path("data/interim/masks")
AOI_ROOT = Path("data/interim/aoi")
POLY_ROOT = Path("data/processed/polygons")

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

    shapes_iter = ((geom, 1) for geom in gdf.geometry if geom is not None and not geom.is_empty)

    arr = rasterize(
        shapes=shapes_iter,
        out_shape=(ref_src.height, ref_src.width),
        transform=ref_src.transform,
        fill=0,
        dtype="uint8",
        all_touched=False,
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


def polygonize_mask_raster(in_path: Path, raw_out: Path, dissolved_out: Path, source_name: str) -> tuple[int, int]:
    raw_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(in_path) as src:
        arr = src.read(1)
        feats = []

        for geom, value in shapes(arr, mask=(arr == 1), transform=src.transform):
            if int(value) == 1:
                feats.append({
                    "geometry": shape(geom),
                    "value": 1,
                })

        crs = src.crs

    if not feats:
        raise ValueError(f"No kept polygons found in raster: {in_path}")

    gdf = gpd.GeoDataFrame(feats, crs=crs)
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
    gdf.to_file(raw_out, driver="GPKG")

    dissolved = gdf.dissolve(by="value").reset_index(drop=True)
    dissolved["source"] = source_name
    dissolved.to_file(dissolved_out, driver="GPKG")

    return len(gdf), len(dissolved)


def refine_one_city(city: str) -> None:
    mapbiomas_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    veg_mask_path = MASK_ROOT / city / f"{city}_mapbiomas_10m_vegetation_mask_strict.tif"
    built_mask_path = MASK_ROOT / city / f"{city}_mapbiomas_10m_built_mask.tif"

    out_original = MASK_ROOT / city / f"{city}_favela_original_mask_10m.tif"
    out_keep = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain.tif"
    out_remove = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_remove_uncertain.tif"

    keep_raw_out = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_raw.gpkg"
    keep_dissolved_out = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_dissolved.gpkg"

    remove_raw_out = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_remove_uncertain_raw.gpkg"
    remove_dissolved_out = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_remove_uncertain_dissolved.gpkg"

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
        rasterio.open(built_mask_path) as built_src,
    ):
        ensure_aligned(ref_src, veg_src, "Vegetation mask")
        ensure_aligned(ref_src, built_src, "Built mask")

        ref_arr = ref_src.read(1)
        ref_nodata = ref_src.nodata

        valid = np.ones(ref_arr.shape, dtype=bool)
        if ref_nodata is not None:
            valid &= ref_arr != ref_nodata

        veg_is_1 = veg_src.read(1) == 1
        built_is_1 = built_src.read(1) == 1

        original = rasterize_favelas(favelas, ref_src).astype(bool)
        original = original & valid

        keep_uncertain = original.copy()
        keep_uncertain[original & veg_is_1 & (~built_is_1)] = False

        remove_uncertain = original.copy()
        remove_uncertain[original & (~built_is_1)] = False

        original_out = to_output(original, valid)
        keep_out = to_output(keep_uncertain, valid)
        remove_out = to_output(remove_uncertain, valid)

        meta_template = ref_src.meta.copy()

    save_uint8(original_out, meta_template, out_original)
    save_uint8(keep_out, meta_template, out_keep)
    save_uint8(remove_out, meta_template, out_remove)

    keep_raw_count, keep_dissolved_count = polygonize_mask_raster(
        in_path=out_keep,
        raw_out=keep_raw_out,
        dissolved_out=keep_dissolved_out,
        source_name=f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain",
    )

    remove_raw_count, remove_dissolved_count = polygonize_mask_raster(
        in_path=out_remove,
        raw_out=remove_raw_out,
        dissolved_out=remove_dissolved_out,
        source_name=f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_remove_uncertain",
    )

    original_px = int(np.sum(original))
    keep_px = int(np.sum(keep_uncertain))
    remove_px = int(np.sum(remove_uncertain))

    inside_built_px = int(np.sum(original & built_is_1))
    inside_veg_px = int(np.sum(original & veg_is_1))
    inside_uncertain_px = int(np.sum(original & (~veg_is_1) & (~built_is_1)))

    print(f"\n=== {city} ===")
    print(f"Saved original mask:         {out_original}")
    print(f"Saved keep-uncertain mask:   {out_keep}")
    print(f"Saved remove-uncertain mask: {out_remove}")
    print()
    print(f"Original favela pixels:        {original_px}")
    print(f"Inside-polygon built pixels:  {inside_built_px}")
    print(f"Inside-polygon vegetation px: {inside_veg_px}")
    print(f"Inside-polygon uncertain px:  {inside_uncertain_px}")
    print()
    print(f"Keep-uncertain kept pixels:   {keep_px}")
    print(f"Remove-uncertain kept pixels: {remove_px}")
    print(f"Keep-uncertain removed px:    {original_px - keep_px}")
    print(f"Remove-uncertain removed px:  {original_px - remove_px}")
    print()
    print(f"Keep-uncertain raw pieces:    {keep_raw_count}")
    print(f"Keep-uncertain dissolved:     {keep_dissolved_count}")
    print(f"Remove-uncertain raw pieces:  {remove_raw_count}")
    print(f"Remove-uncertain dissolved:   {remove_dissolved_count}")


def main() -> None:
    for city in CITIES:
        refine_one_city(city)

    print("\nDone.")


if __name__ == "__main__":
    main()