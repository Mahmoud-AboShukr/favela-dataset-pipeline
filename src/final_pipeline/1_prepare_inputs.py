from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Iterable, Optional

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.windows import Window
from rasterio.warp import reproject
from shapely.geometry import box


# ============================================================================
# CONFIG
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUT_DIR = PROJECT_ROOT / "data" / "processed" / "final_pipeline" / "manaus" / "prepared"

# --- Raster inputs ---
MAPBIOMAS_PATH = RAW_DIR / "mapbiomas" / "mapbiomas_10m.tif"

WSF_PATHS = [
    RAW_DIR / "wsf" / "WSF2019_v1_-62_-4.tif",
    RAW_DIR / "wsf" / "WSF2019_v1_-60_-4.tif",
]

GHSL_PATHS = [
    RAW_DIR / "ghsl" / "manus" / "ghsl_emc_built_2022_10m_1.tif",
    RAW_DIR / "ghsl" / "manus" / "ghsl_emc_built_2022_10m_2.tif",
]

WORLDCOVER_PATHS = [
    RAW_DIR / "worldcover" / "ESA_WorldCover_10m_2021_v200_S06W060_Map.tif",
    RAW_DIR / "worldcover" / "ESA_WorldCover_10m_2021_v200_S03W060_Map.tif",
    RAW_DIR / "worldcover" / "ESA_WorldCover_10m_2021_v200_S03W063_Map.tif",
    RAW_DIR / "worldcover" / "ESA_WorldCover_10m_2021_v200_S06W063_Map.tif",
]

# --- Vector inputs ---
AOI_VECTOR_PATH = RAW_DIR / "ibge" / "BR_Municipios_2024" / "BR_Municipios_2024.shp"
FAVELA_VECTOR_PATH = RAW_DIR / "favelas_shp" / "favelas.shp"

# Adjust only if needed
AOI_FILTER_FIELD = "NM_MUN"
AOI_FILTER_VALUE = "Manaus"
AOI_SECONDARY_FILTER_FIELD = "SIGLA_UF"
AOI_SECONDARY_FILTER_VALUE = "AM"

DEFAULT_NODATA_INT = 0
DEFAULT_NODATA_FLOAT = -9999.0

CLEAN_OUTPUT_DIR = False
SAMPLE_SIZE = 2048

# WSF uses 255 = settlement, 0 = no settlement
WSF_SETTLEMENT_VALUE = 255
WSF_NON_SETTLEMENT_VALUE = 0


# ============================================================================
# HELPERS
# ============================================================================

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def maybe_clean_dir(path: Path) -> None:
    if CLEAN_OUTPUT_DIR and path.exists():
        shutil.rmtree(path)
    ensure_dir(path)


def file_must_exist(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")


def files_must_exist(paths: Iterable[Path]) -> None:
    for p in paths:
        file_must_exist(p)


def print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def raster_summary(path: Path, max_unique: int = 20, sample_size: int = SAMPLE_SIZE) -> dict:
    with rasterio.open(path) as src:
        summary = {
            "path": str(path),
            "crs": src.crs.to_string() if src.crs else None,
            "bounds": tuple(round(v, 3) for v in src.bounds),
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": src.dtypes[0] if src.count > 0 else None,
            "nodata": src.nodata,
            "res": tuple(round(v, 8) for v in src.res),
            "transform": tuple(round(v, 8) for v in src.transform[:6]),
        }

        if src.count > 0:
            sample_w = min(sample_size, src.width)
            sample_h = min(sample_size, src.height)
            col_off = max(0, (src.width - sample_w) // 2)
            row_off = max(0, (src.height - sample_h) // 2)
            window = Window(col_off, row_off, sample_w, sample_h)

            arr = src.read(1, window=window, masked=True)

            if arr.count() > 0:
                compressed = arr.compressed()
                unique = np.unique(compressed)
                summary["sample_min"] = float(compressed.min())
                summary["sample_max"] = float(compressed.max())
                summary["unique_sample"] = unique[:max_unique].tolist()
                summary["unique_count_in_sample"] = int(unique.size)
            else:
                summary["sample_min"] = None
                summary["sample_max"] = None
                summary["unique_sample"] = []
                summary["unique_count_in_sample"] = 0

            summary["sample_window"] = {
                "row_off": int(row_off),
                "col_off": int(col_off),
                "width": int(sample_w),
                "height": int(sample_h),
            }

    return summary


def print_raster_summary(path: Path, label: str) -> None:
    s = raster_summary(path)
    print(f"\n[{label}]")
    for k, v in s.items():
        print(f"  {k}: {v}")


def binary_raster_overview(path: Path, step: int = 50) -> dict:
    """
    Coarse overview for binary/categorical rasters without loading full-res arrays.
    """
    with rasterio.open(path) as src:
        arr = src.read(1)[::step, ::step]
        unique, counts = np.unique(arr, return_counts=True)
        total = counts.sum()

        stats = {}
        for u, c in zip(unique.tolist(), counts.tolist()):
            stats[int(u)] = {
                "count": int(c),
                "fraction": float(c / total),
            }
        return stats


def print_binary_overview(path: Path, label: str, step: int = 50) -> None:
    overview = binary_raster_overview(path, step=step)
    print(f"\n[{label}]")
    for val, info in overview.items():
        print(f"  value {val}: count={info['count']}, fraction={info['fraction']:.4f}")


def vector_summary(gdf: gpd.GeoDataFrame, label: str) -> None:
    print(f"\n[{label}]")
    print(f"  rows: {len(gdf)}")
    print(f"  crs: {gdf.crs}")
    print(f"  total_bounds: {tuple(round(float(v), 3) for v in gdf.total_bounds)}")
    print(f"  geometry_types: {gdf.geom_type.value_counts().to_dict()}")
    print(f"  invalid_geometries: {int((~gdf.is_valid).sum())}")
    print(f"  empty_geometries: {int(gdf.geometry.is_empty.sum())}")


def safe_make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf = gdf[gdf.geometry.notnull()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    if (~gdf.is_valid).any():
        gdf["geometry"] = gdf.buffer(0)
    gdf = gdf[gdf.geometry.notnull()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    return gdf


def load_and_filter_aoi(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    gdf = safe_make_valid(gdf)

    if len(gdf) == 0:
        raise ValueError(f"AOI file is empty: {path}")

    if len(gdf) == 1:
        return gdf

    if AOI_FILTER_FIELD not in gdf.columns:
        raise ValueError(
            f"AOI_FILTER_FIELD '{AOI_FILTER_FIELD}' not found in AOI file columns: {list(gdf.columns)}"
        )

    filtered = gdf[gdf[AOI_FILTER_FIELD].astype(str).str.lower() == AOI_FILTER_VALUE.lower()].copy()

    if len(filtered) > 1 and AOI_SECONDARY_FILTER_FIELD and AOI_SECONDARY_FILTER_FIELD in filtered.columns:
        filtered2 = filtered[
            filtered[AOI_SECONDARY_FILTER_FIELD].astype(str).str.upper()
            == str(AOI_SECONDARY_FILTER_VALUE).upper()
        ].copy()
        if len(filtered2) > 0:
            filtered = filtered2

    if len(filtered) == 0:
        raise ValueError(
            f"Could not find AOI for {AOI_FILTER_VALUE}. "
            f"Check AOI_FILTER_FIELD / AOI_SECONDARY_FILTER_FIELD."
        )

    filtered = filtered.dissolve().reset_index(drop=True)
    filtered = safe_make_valid(filtered)
    return filtered


def load_and_filter_favelas(path: Path, aoi_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    fav = gpd.read_file(path)
    fav = safe_make_valid(fav)

    if fav.crs != aoi_gdf.crs:
        fav = fav.to_crs(aoi_gdf.crs)

    fav = fav[fav.intersects(aoi_gdf.geometry.iloc[0])].copy()
    fav = safe_make_valid(fav)

    if len(fav) == 0:
        raise ValueError("No favela polygons intersect the Manaus AOI.")

    return fav


def bounds_as_gdf(bounds, crs) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(geometry=[box(*bounds)], crs=crs)


def check_intersection(raster_path: Path, aoi_gdf: gpd.GeoDataFrame, label: str) -> None:
    with rasterio.open(raster_path) as src:
        rb = bounds_as_gdf(src.bounds, src.crs)
        aoi_in_src = aoi_gdf.to_crs(src.crs)
        intersects = bool(rb.intersects(aoi_in_src.geometry.iloc[0]).iloc[0])
        print(f"[INTERSECTION CHECK] {label}: {intersects}")
        if not intersects:
            raise ValueError(f"{label} does not intersect the Manaus AOI.")


def save_json(obj: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def clip_raster_to_geom(raster_path: Path, geom_gdf: gpd.GeoDataFrame, out_path: Path) -> Path:
    with rasterio.open(raster_path) as src:
        geom = geom_gdf
        if geom.crs != src.crs:
            geom = geom.to_crs(src.crs)

        shapes = [geom.geometry.iloc[0].__geo_interface__]
        out_image, out_transform = mask(src, shapes, crop=True)
        out_meta = src.meta.copy()
        out_meta.update(
            {
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "count": out_image.shape[0],
            }
        )

        with rasterio.open(out_path, "w", **out_meta) as dst:
            dst.write(out_image)

    return out_path


def clip_many_rasters_to_geom(
    raster_paths: list[Path],
    geom_gdf: gpd.GeoDataFrame,
    out_dir: Path,
    prefix: str,
) -> list[Path]:
    ensure_dir(out_dir)
    clipped_paths = []

    for i, raster_path in enumerate(raster_paths, start=1):
        out_path = out_dir / f"{prefix}_{i}_clip.tif"
        clip_raster_to_geom(raster_path, geom_gdf, out_path)
        clipped_paths.append(out_path)

    return clipped_paths


def mosaic_rasters(input_paths: list[Path], out_path: Path, method: str = "first") -> Path:
    srcs = [rasterio.open(p) for p in input_paths]
    try:
        mosaic_arr, mosaic_transform = merge(srcs, method=method)
        meta = srcs[0].meta.copy()
        meta.update(
            {
                "height": mosaic_arr.shape[1],
                "width": mosaic_arr.shape[2],
                "transform": mosaic_transform,
                "count": mosaic_arr.shape[0],
            }
        )
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(mosaic_arr)
    finally:
        for s in srcs:
            s.close()

    return out_path


def reproject_match(
    src_path: Path,
    ref_path: Path,
    out_path: Path,
    resampling: Resampling,
    dst_nodata: Optional[float] = None,
) -> Path:
    with rasterio.open(ref_path) as ref, rasterio.open(src_path) as src:
        src_dtype = src.dtypes[0]

        if "float" in src_dtype:
            nodata_value = DEFAULT_NODATA_FLOAT if dst_nodata is None else dst_nodata
        else:
            nodata_value = DEFAULT_NODATA_INT if dst_nodata is None else dst_nodata

        dst_meta = ref.meta.copy()
        dst_meta.update(
            {
                "count": src.count,
                "dtype": src_dtype,
                "nodata": nodata_value,
            }
        )

        with rasterio.open(out_path, "w", **dst_meta) as dst:
            for bidx in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, bidx),
                    destination=rasterio.band(dst, bidx),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src.nodata,
                    dst_transform=ref.transform,
                    dst_crs=ref.crs,
                    dst_nodata=nodata_value,
                    resampling=resampling,
                )

    return out_path


def rasterize_favelas_to_match(
    favela_gdf: gpd.GeoDataFrame,
    ref_path: Path,
    out_path: Path,
    burn_value: int = 1,
    nodata_value: int = 0,
) -> Path:
    with rasterio.open(ref_path) as ref:
        fav = favela_gdf
        if fav.crs != ref.crs:
            fav = fav.to_crs(ref.crs)

        shapes = ((geom, burn_value) for geom in fav.geometry if geom is not None and not geom.is_empty)

        arr = rasterize(
            shapes=shapes,
            out_shape=(ref.height, ref.width),
            transform=ref.transform,
            fill=nodata_value,
            dtype="uint8",
            all_touched=False,
        )

        meta = ref.meta.copy()
        meta.update({"count": 1, "dtype": "uint8", "nodata": nodata_value})

        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(arr, 1)

    return out_path


def verify_same_grid(paths: list[Path]) -> pd.DataFrame:
    rows = []
    for p in paths:
        with rasterio.open(p) as src:
            rows.append(
                {
                    "path": str(p),
                    "crs": src.crs.to_string() if src.crs else None,
                    "width": src.width,
                    "height": src.height,
                    "transform": tuple(round(v, 8) for v in src.transform[:6]),
                    "res": tuple(round(v, 8) for v in src.res),
                    "bounds": tuple(round(v, 3) for v in src.bounds),
                }
            )
    return pd.DataFrame(rows)


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    print_header("CHECKING RAW INPUT FILES")
    file_must_exist(MAPBIOMAS_PATH)
    files_must_exist(WSF_PATHS)
    files_must_exist(GHSL_PATHS)
    files_must_exist(WORLDCOVER_PATHS)
    file_must_exist(AOI_VECTOR_PATH)
    file_must_exist(FAVELA_VECTOR_PATH)

    maybe_clean_dir(OUT_DIR)

    # ------------------------------------------------------------------
    # 1) Load vectors
    # ------------------------------------------------------------------
    print_header("LOADING AND FILTERING VECTORS")
    aoi = load_and_filter_aoi(AOI_VECTOR_PATH)
    aoi = safe_make_valid(aoi)

    favelas = load_and_filter_favelas(FAVELA_VECTOR_PATH, aoi)
    favelas = safe_make_valid(favelas)

    vector_summary(aoi, "AOI (Manaus)")
    vector_summary(favelas, "Favela polygons filtered to Manaus")

    aoi_out = OUT_DIR / "aoi_manaus.gpkg"
    fav_out = OUT_DIR / "favela_polygons_manaus.gpkg"
    aoi.to_file(aoi_out, driver="GPKG")
    favelas.to_file(fav_out, driver="GPKG")

    # ------------------------------------------------------------------
    # 2) Inspect raw rasters
    # ------------------------------------------------------------------
    print_header("INSPECTING RAW RASTERS")
    print_raster_summary(MAPBIOMAS_PATH, "MapBiomas raw")
    for p in WSF_PATHS:
        print_raster_summary(p, f"WSF raw: {p.name}")
    for p in GHSL_PATHS:
        print_raster_summary(p, f"GHSL raw: {p.name}")
    for p in WORLDCOVER_PATHS:
        print_raster_summary(p, f"WorldCover raw: {p.name}")

    check_intersection(MAPBIOMAS_PATH, aoi, "MapBiomas")
    for p in WSF_PATHS:
        check_intersection(p, aoi, f"WSF tile: {p.name}")
    for p in GHSL_PATHS:
        check_intersection(p, aoi, f"GHSL tile: {p.name}")
    for p in WORLDCOVER_PATHS:
        check_intersection(p, aoi, f"WorldCover tile: {p.name}")

    # ------------------------------------------------------------------
    # 3) Clip MapBiomas first -> master grid
    # ------------------------------------------------------------------
    print_header("CLIPPING MAPBIOMAS TO MANAUS AOI")
    mapbiomas_clip = OUT_DIR / "mapbiomas_10m_manaus.tif"
    clip_raster_to_geom(MAPBIOMAS_PATH, aoi, mapbiomas_clip)
    print_raster_summary(mapbiomas_clip, "MapBiomas clipped")

    # ------------------------------------------------------------------
    # 4) Clip WSF / GHSL / WorldCover tiles individually first
    # ------------------------------------------------------------------
    print_header("CLIPPING WSF, GHSL, AND WORLDCOVER TILES INDIVIDUALLY TO MANAUS AOI")
    tmp_tiles_dir = OUT_DIR / "_tmp_tiles"
    ensure_dir(tmp_tiles_dir)

    wsf_clipped_tiles = clip_many_rasters_to_geom(
        raster_paths=WSF_PATHS,
        geom_gdf=aoi,
        out_dir=tmp_tiles_dir,
        prefix="wsf",
    )

    ghsl_clipped_tiles = clip_many_rasters_to_geom(
        raster_paths=GHSL_PATHS,
        geom_gdf=aoi,
        out_dir=tmp_tiles_dir,
        prefix="ghsl",
    )

    worldcover_clipped_tiles = clip_many_rasters_to_geom(
        raster_paths=WORLDCOVER_PATHS,
        geom_gdf=aoi,
        out_dir=tmp_tiles_dir,
        prefix="worldcover",
    )

    for p in wsf_clipped_tiles:
        print_raster_summary(p, f"WSF clipped tile: {p.name}")

    for p in ghsl_clipped_tiles:
        print_raster_summary(p, f"GHSL clipped tile: {p.name}")

    for p in worldcover_clipped_tiles:
        print_raster_summary(p, f"WorldCover clipped tile: {p.name}")

    # ------------------------------------------------------------------
    # 5) Mosaic only the clipped pieces
    # ------------------------------------------------------------------
    print_header("MOSAICKING CLIPPED WSF, GHSL, AND WORLDCOVER TILES")
    wsf_clip = OUT_DIR / "_tmp_wsf_clip.tif"
    ghsl_clip = OUT_DIR / "_tmp_ghsl_clip.tif"
    worldcover_clip = OUT_DIR / "_tmp_worldcover_clip.tif"

    mosaic_rasters(wsf_clipped_tiles, wsf_clip)
    mosaic_rasters(ghsl_clipped_tiles, ghsl_clip)
    mosaic_rasters(worldcover_clipped_tiles, worldcover_clip)

    print_raster_summary(wsf_clip, "WSF clipped mosaic")
    print_raster_summary(ghsl_clip, "GHSL clipped mosaic")
    print_raster_summary(worldcover_clip, "WorldCover clipped mosaic")

    # Useful WSF diagnostic
    print_binary_overview(wsf_clip, "WSF clipped mosaic coarse overview", step=50)

    # ------------------------------------------------------------------
    # 6) Reproject / align all rasters to MapBiomas grid
    # ------------------------------------------------------------------
    print_header("REPROJECTING AND ALIGNING TO MAPBIOMAS GRID")

    wsf_aligned = OUT_DIR / "wsf_manaus.tif"
    ghsl_aligned = OUT_DIR / "ghsl_manaus.tif"
    worldcover_aligned = OUT_DIR / "worldcover_manaus.tif"

    reproject_match(
        src_path=wsf_clip,
        ref_path=mapbiomas_clip,
        out_path=wsf_aligned,
        resampling=Resampling.nearest,
        dst_nodata=DEFAULT_NODATA_INT,
    )

    reproject_match(
        src_path=ghsl_clip,
        ref_path=mapbiomas_clip,
        out_path=ghsl_aligned,
        resampling=Resampling.nearest,
        dst_nodata=DEFAULT_NODATA_INT,
    )

    reproject_match(
        src_path=worldcover_clip,
        ref_path=mapbiomas_clip,
        out_path=worldcover_aligned,
        resampling=Resampling.nearest,
        dst_nodata=DEFAULT_NODATA_INT,
    )

    print_raster_summary(wsf_aligned, "WSF aligned")
    print_binary_overview(wsf_aligned, "WSF aligned coarse overview", step=50)

    print_raster_summary(ghsl_aligned, "GHSL aligned")
    print_raster_summary(worldcover_aligned, "WorldCover aligned")

    # ------------------------------------------------------------------
    # 7) Rasterize favelas to match grid
    # ------------------------------------------------------------------
    print_header("RASTERIZING FAVELA POLYGONS TO MAPBIOMAS GRID")
    favela_mask_out = OUT_DIR / "favela_mask.tif"
    rasterize_favelas_to_match(favelas, mapbiomas_clip, favela_mask_out)
    print_raster_summary(favela_mask_out, "Favela mask")

    # ------------------------------------------------------------------
    # 8) Verify same grid
    # ------------------------------------------------------------------
    print_header("VERIFYING PREPARED GRID CONSISTENCY")
    prepared_rasters = [
        mapbiomas_clip,
        wsf_aligned,
        ghsl_aligned,
        worldcover_aligned,
        favela_mask_out,
    ]
    grid_df = verify_same_grid(prepared_rasters)
    print(grid_df.to_string(index=False))

    grid_csv = OUT_DIR / "prepared_grid_check.csv"
    grid_df.to_csv(grid_csv, index=False)

    # ------------------------------------------------------------------
    # 9) Save metadata
    # ------------------------------------------------------------------
    print_header("SAVING METADATA SUMMARY")
    metadata = {
        "aoi_vector": str(aoi_out),
        "favela_vector": str(fav_out),
        "prepared_outputs": {
            "mapbiomas": str(mapbiomas_clip),
            "wsf": str(wsf_aligned),
            "ghsl": str(ghsl_aligned),
            "worldcover": str(worldcover_aligned),
            "favela_mask": str(favela_mask_out),
        },
        "raw_inputs": {
            "mapbiomas": str(MAPBIOMAS_PATH),
            "wsf_tiles": [str(p) for p in WSF_PATHS],
            "ghsl_tiles": [str(p) for p in GHSL_PATHS],
            "worldcover_tiles": [str(p) for p in WORLDCOVER_PATHS],
            "aoi_vector": str(AOI_VECTOR_PATH),
            "favela_vector": str(FAVELA_VECTOR_PATH),
        },
        "notes": {
            "master_grid": "clipped MapBiomas raster",
            "worldcover_inputquality_used": False,
            "wsf_mosaicked_after_clip": True,
            "ghsl_mosaicked_after_clip": True,
            "worldcover_mosaicked_after_clip": True,
            "wsf_settlement_value": WSF_SETTLEMENT_VALUE,
            "wsf_non_settlement_value": WSF_NON_SETTLEMENT_VALUE,
        },
    }
    save_json(metadata, OUT_DIR / "prepared_metadata.json")

    print("\nPrepared outputs written to:")
    for p in prepared_rasters + [aoi_out, fav_out, grid_csv, OUT_DIR / "prepared_metadata.json"]:
        print(f"  - {p}")

    print_header("DONE")


if __name__ == "__main__":
    main()