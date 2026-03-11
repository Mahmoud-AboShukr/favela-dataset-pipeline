from __future__ import annotations

from pathlib import Path

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling
from shapely.geometry import mapping


# =========================
# Paths
# =========================
GHSL_2018 = Path("data/raw/ghsl/Brasilia_2018.tif")
GHSL_2025 = Path("data/raw/ghsl/Brasilia_2025.tif")

AOI_GPKG = Path("data/interim/aoi/brasilia_boundary.gpkg")
AOI_LAYER = "brasilia_boundary"

OUT_DIR = Path("data/interim/temporal_change")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_2018_CLIP = OUT_DIR / "ghsl_2018_brasilia_clip.tif"
OUT_2025_CLIP = OUT_DIR / "ghsl_2025_brasilia_clip.tif"

OUT_MASK_2018 = OUT_DIR / "mask_2018_10m.tif"
OUT_MASK_2025 = OUT_DIR / "mask_2025_100m.tif"

OUT_2018_ON_2025_FRAC = OUT_DIR / "mask_2018_on_2025grid_fraction.tif"
OUT_2018_ON_2025_BIN = OUT_DIR / "mask_2018_on_2025grid_binary.tif"

OUT_GROWTH = OUT_DIR / "growth_2018_to_2025.tif"
OUT_PERSIST = OUT_DIR / "persistence_2018_to_2025.tif"
OUT_LOSS = OUT_DIR / "loss_2018_to_2025.tif"


# =========================
# Parameters
# =========================
THRESHOLD_2018 = 1
THRESHOLD_2025 = 1

# A 2025 100 m cell is considered "already built-up in 2018"
# if at least this fraction of its area was built-up in the 2018 10 m mask.
FRACTION_THRESHOLD = 0.10  # start with 10%, can also test 0.20 or 0.25


def _safe_write(out_path: Path, meta: dict, arr: np.ndarray) -> Path:
    """
    Write to temp file then replace if possible.
    """
    out_path = Path(out_path)
    tmp_path = out_path.with_name(out_path.stem + "_tmp.tif")

    with rasterio.open(tmp_path, "w", **meta) as dst:
        if arr.ndim == 2:
            dst.write(arr, 1)
        elif arr.ndim == 3:
            dst.write(arr)
        else:
            raise ValueError(f"Unsupported array ndim: {arr.ndim}")

    try:
        if out_path.exists():
            out_path.unlink()
        tmp_path.replace(out_path)
        return out_path
    except Exception as e:
        print(f"⚠ Could not overwrite {out_path}. Kept temp file: {tmp_path}")
        print(f"   Reason: {e}")
        return tmp_path


def _read_aoi_geometry(aoi_path: Path, layer: str):
    aoi = gpd.read_file(aoi_path, layer=layer)
    if aoi.empty:
        raise ValueError("AOI file is empty.")
    if aoi.crs is None:
        raise ValueError("AOI CRS is missing.")
    return aoi.geometry.union_all() if hasattr(aoi.geometry, "union_all") else aoi.unary_union, aoi.crs


def _clip_raster_to_aoi(in_tif: Path, aoi_geom, aoi_crs, out_tif: Path) -> Path:
    with rasterio.open(in_tif) as src:
        if src.crs is None:
            raise ValueError(f"Raster CRS is missing: {in_tif}")

        aoi_proj = gpd.GeoSeries([aoi_geom], crs=aoi_crs).to_crs(src.crs)
        geom_proj = aoi_proj.iloc[0]

        clipped, clipped_transform = mask(
            src,
            [mapping(geom_proj)],
            crop=True,
            all_touched=False,
            filled=True,
        )

        out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": clipped_transform,
                "compress": "deflate",
            }
        )

        if src.nodata is not None:
            out_meta["nodata"] = src.nodata

    saved = _safe_write(out_tif, out_meta, clipped)
    print(f"✅ Saved clip: {saved}")
    return saved


def _build_binary_mask(clip_tif: Path, threshold: float, out_tif: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(clip_tif) as src:
        arr = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata

    if nodata is not None:
        valid = arr != nodata
    else:
        valid = np.ones_like(arr, dtype=bool)

    mask_bool = (arr >= threshold) & valid

    out_meta = meta.copy()
    out_meta.update(
        {
            "dtype": "uint8",
            "count": 1,
            "nodata": 0,
            "compress": "deflate",
        }
    )

    _safe_write(out_tif, out_meta, mask_bool.astype("uint8"))
    print(f"✅ Saved binary mask: {out_tif}")

    return mask_bool, meta


def _aggregate_2018_mask_to_2025_grid(
    mask_2018_bool: np.ndarray,
    meta_2018: dict,
    ref_2025_tif: Path,
    out_frac_tif: Path,
    out_bin_tif: Path,
    fraction_threshold: float,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Reproject / aggregate 2018 binary mask (10 m) to the 2025 100 m grid.
    Uses average resampling so output values are fractions in [0, 1].
    """
    with rasterio.open(ref_2025_tif) as ref:
        dst_crs = ref.crs
        dst_transform = ref.transform
        dst_height = ref.height
        dst_width = ref.width
        ref_meta = ref.meta.copy()
        ref_nodata = ref.nodata

    src_arr = mask_2018_bool.astype("float32")
    dst_frac = np.zeros((dst_height, dst_width), dtype="float32")

    reproject(
        source=src_arr,
        destination=dst_frac,
        src_transform=meta_2018["transform"],
        src_crs=meta_2018["crs"],
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.average,
        src_nodata=0,
        dst_nodata=0,
    )

    # Build valid mask for 2025 reference grid
    with rasterio.open(ref_2025_tif) as ref:
        ref_arr = ref.read(1)
        if ref_nodata is not None:
            valid_2025 = ref_arr != ref_nodata
        else:
            valid_2025 = np.ones_like(ref_arr, dtype=bool)

    dst_frac = np.where(valid_2025, dst_frac, 0.0)
    dst_bin = (dst_frac >= fraction_threshold) & valid_2025

    frac_meta = ref_meta.copy()
    frac_meta.update(
        {
            "dtype": "float32",
            "count": 1,
            "nodata": 0.0,
            "compress": "deflate",
        }
    )

    bin_meta = ref_meta.copy()
    bin_meta.update(
        {
            "dtype": "uint8",
            "count": 1,
            "nodata": 0,
            "compress": "deflate",
        }
    )

    _safe_write(out_frac_tif, frac_meta, dst_frac.astype("float32"))
    _safe_write(out_bin_tif, bin_meta, dst_bin.astype("uint8"))

    print(f"✅ Saved 2018 fraction on 2025 grid: {out_frac_tif}")
    print(f"✅ Saved 2018 binary on 2025 grid: {out_bin_tif}")

    return dst_frac, dst_bin, ref_meta


def _save_bool_raster(out_tif: Path, ref_meta: dict, arr_bool: np.ndarray) -> Path:
    out_meta = ref_meta.copy()
    out_meta.update(
        {
            "dtype": "uint8",
            "count": 1,
            "nodata": 0,
            "compress": "deflate",
        }
    )
    return _safe_write(out_tif, out_meta, arr_bool.astype("uint8"))


def _print_stats(name: str, arr_bool: np.ndarray):
    on_pixels = int(arr_bool.sum())
    total = int(arr_bool.size)
    ratio = on_pixels / total if total else 0.0
    print(f"  {name}: pixels_on={on_pixels}, total={total}, ratio={ratio:.6f}")


def main():
    # 1) Check inputs
    for p in [GHSL_2018, GHSL_2025, AOI_GPKG]:
        if not p.exists():
            raise FileNotFoundError(f"Missing input: {p}")

    # 2) Read AOI once
    aoi_geom, aoi_crs = _read_aoi_geometry(AOI_GPKG, AOI_LAYER)

    # 3) Clip both rasters to AOI
    clip_2018 = _clip_raster_to_aoi(GHSL_2018, aoi_geom, aoi_crs, OUT_2018_CLIP)
    clip_2025 = _clip_raster_to_aoi(GHSL_2025, aoi_geom, aoi_crs, OUT_2025_CLIP)

    # 4) Build binary masks
    mask_2018_bool, meta_2018 = _build_binary_mask(clip_2018, THRESHOLD_2018, OUT_MASK_2018)
    mask_2025_bool, _ = _build_binary_mask(clip_2025, THRESHOLD_2025, OUT_MASK_2025)

    # 5) Aggregate 2018 mask to 2025 grid using average resampling
    _, mask_2018_on_2025_bool, ref_2025_meta = _aggregate_2018_mask_to_2025_grid(
        mask_2018_bool=mask_2018_bool,
        meta_2018=meta_2018,
        ref_2025_tif=clip_2025,
        out_frac_tif=OUT_2018_ON_2025_FRAC,
        out_bin_tif=OUT_2018_ON_2025_BIN,
        fraction_threshold=FRACTION_THRESHOLD,
    )

    # 6) Temporal change masks on the 2025 grid
    growth = mask_2025_bool & (~mask_2018_on_2025_bool)
    persistence = mask_2025_bool & mask_2018_on_2025_bool
    loss = (~mask_2025_bool) & mask_2018_on_2025_bool

    _save_bool_raster(OUT_GROWTH, ref_2025_meta, growth)
    _save_bool_raster(OUT_PERSIST, ref_2025_meta, persistence)
    _save_bool_raster(OUT_LOSS, ref_2025_meta, loss)

    # 7) Print summary
    print("\n✅ Temporal change products saved.")
    print(f"  {OUT_GROWTH}")
    print(f"  {OUT_PERSIST}")
    print(f"  {OUT_LOSS}")

    print("\nParameters:")
    print(f"  THRESHOLD_2018: {THRESHOLD_2018}")
    print(f"  THRESHOLD_2025: {THRESHOLD_2025}")
    print(f"  FRACTION_THRESHOLD: {FRACTION_THRESHOLD}")

    print("\nStats on 2025 grid:")
    _print_stats("mask_2025", mask_2025_bool)
    _print_stats("mask_2018_on_2025grid", mask_2018_on_2025_bool)
    _print_stats("growth_2018_to_2025", growth)
    _print_stats("persistence_2018_to_2025", persistence)
    _print_stats("loss_2018_to_2025", loss)


if __name__ == "__main__":
    main()