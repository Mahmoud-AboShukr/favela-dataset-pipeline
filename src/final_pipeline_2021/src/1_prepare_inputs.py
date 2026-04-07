from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask, rasterize
from rasterio.merge import merge
from rasterio.warp import reproject, transform_bounds, transform_geom
from shapely.geometry import box, mapping


# =============================================================================
# PATHS / CONFIG
# =============================================================================

# This file lives at:
# repo_root / src / final_pipeline_2021 / src / 1_prepare_inputs.py
REPO_ROOT = Path(__file__).resolve().parents[3]

WORKING_CRS = "EPSG:4326"

FAVELA_PATH = REPO_ROOT / "data" / "raw" / "favelas_shp" / "favelas.shp"
MAPBIOMAS_ROOT = REPO_ROOT / "data" / "raw" / "mapbiomas" / "mapbiomas_10m_2021.tif"
GHSL_ROOT = REPO_ROOT / "data" / "raw" / "ghsl" / "brazil_unzipped"
WORLDCOVER_ROOT = REPO_ROOT / "data" / "raw" / "worldcover_2021" / "brazil_tiles"

OUTPUT_ROOT = REPO_ROOT / "data" / "processed" / "final_pipeline_2021"

DEFAULT_CHUNK_SIZE_DEG = 0.5
DEFAULT_BUFFER_DEG = 0.02


# =============================================================================
# HELPERS
# =============================================================================

def log(msg: str) -> None:
    print(msg, flush=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def list_tifs(path: Path) -> List[Path]:
    """
    Return tif files from either:
    - a single tif file path
    - or a directory recursively containing tif files
    """
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if path.is_file():
        if path.suffix.lower() not in {".tif", ".tiff"}:
            raise ValueError(f"Expected a tif/tiff file, got: {path}")
        return [path]

    tifs = sorted(
        [
            p for p in path.rglob("*")
            if p.is_file() and p.suffix.lower() in {".tif", ".tiff"}
        ]
    )
    if not tifs:
        raise FileNotFoundError(f"No .tif files found under: {path}")
    return tifs


def default_nodata(dtype_str: str):
    dtype = np.dtype(dtype_str)
    if np.issubdtype(dtype, np.floating):
        return -9999.0
    if np.issubdtype(dtype, np.unsignedinteger):
        return np.iinfo(dtype).max
    if np.issubdtype(dtype, np.signedinteger):
        return np.iinfo(dtype).min
    return 0


def safe_write_gpkg(gdf: gpd.GeoDataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    if path.exists():
        path.unlink()
    gdf.to_file(path, driver="GPKG")


# =============================================================================
# LOAD FAVELAS
# =============================================================================

def load_favelas(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Favela file not found: {path}")

    log(f"[LOAD] Reading favelas: {path}")
    gdf = gpd.read_file(path)

    if gdf.empty:
        raise ValueError("Favela file is empty.")

    gdf = gdf[gdf.geometry.notnull()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()

    if gdf.crs is None:
        raise ValueError("Favela file has no CRS.")

    if str(gdf.crs) != WORKING_CRS:
        gdf = gdf.to_crs(WORKING_CRS)

    gdf = gdf.explode(index_parts=False).reset_index(drop=True)

    if "source_id" not in gdf.columns:
        gdf["source_id"] = np.arange(1, len(gdf) + 1)

    return gdf


# =============================================================================
# CHUNKING
# =============================================================================

def build_chunk_index(
    favelas: gpd.GeoDataFrame,
    chunk_size_deg: float,
    buffer_deg: float,
) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = favelas.total_bounds

    minx -= buffer_deg
    miny -= buffer_deg
    maxx += buffer_deg
    maxy += buffer_deg

    xs = np.arange(
        math.floor(minx / chunk_size_deg) * chunk_size_deg,
        math.ceil(maxx / chunk_size_deg) * chunk_size_deg,
        chunk_size_deg,
    )
    ys = np.arange(
        math.floor(miny / chunk_size_deg) * chunk_size_deg,
        math.ceil(maxy / chunk_size_deg) * chunk_size_deg,
        chunk_size_deg,
    )

    cells = []
    for x in xs:
        for y in ys:
            cells.append(box(x, y, x + chunk_size_deg, y + chunk_size_deg))

    grid = gpd.GeoDataFrame({"geometry": cells}, crs=WORKING_CRS)

    joined = gpd.sjoin(
        grid,
        favelas[["geometry"]],
        how="inner",
        predicate="intersects",
    )

    keep_idx = np.unique(joined.index.to_numpy())
    grid = grid.iloc[keep_idx].copy().reset_index(drop=True)

    grid["chunk_id"] = [f"chunk_{i:06d}" for i in range(1, len(grid) + 1)]
    grid["buffer_deg"] = buffer_deg
    grid["chunk_size_deg"] = chunk_size_deg

    return grid[["chunk_id", "chunk_size_deg", "buffer_deg", "geometry"]]


def subset_favelas_for_chunk(
    favelas: gpd.GeoDataFrame,
    chunk_geom,
    buffer_deg: float,
) -> Tuple[gpd.GeoDataFrame, object]:
    processing_geom = chunk_geom.buffer(buffer_deg)
    local = favelas[favelas.intersects(processing_geom)].copy().reset_index(drop=True)
    return local, processing_geom


# =============================================================================
# RASTER INDEXING
# =============================================================================

def raster_bounds_wgs84(path: Path):
    with rasterio.open(path) as src:
        bounds_wgs84 = transform_bounds(
            src.crs,
            WORKING_CRS,
            *src.bounds,
            densify_pts=21,
        )
    return box(*bounds_wgs84)


def build_raster_index(root: Path, source_name: str) -> gpd.GeoDataFrame:
    tif_paths = list_tifs(root)
    log(f"[INDEX] {source_name}: found {len(tif_paths)} tif file(s) under {root}")

    rows = []
    for p in tif_paths:
        try:
            with rasterio.open(p) as src:
                rows.append(
                    {
                        "source": source_name,
                        "path": str(p),
                        "crs": str(src.crs),
                        "width": src.width,
                        "height": src.height,
                        "count": src.count,
                        "dtype": src.dtypes[0],
                        "nodata": src.nodata,
                        "res_x": src.res[0],
                        "res_y": src.res[1],
                        "geometry": raster_bounds_wgs84(p),
                    }
                )
        except Exception as e:
            log(f"[WARN] Failed indexing {p}: {e}")

    if not rows:
        raise RuntimeError(f"No readable rasters found for {source_name} under {root}")

    return gpd.GeoDataFrame(rows, crs=WORKING_CRS)


def select_tiles(raster_index: gpd.GeoDataFrame, geom_wgs84) -> List[Path]:
    hits = raster_index[raster_index.intersects(geom_wgs84)].copy()
    return [Path(p) for p in hits["path"].tolist()]


# =============================================================================
# RASTER PREPARATION
# =============================================================================

def mosaic_clip_native(
    tile_paths: List[Path],
    target_geom_wgs84,
):
    if not tile_paths:
        raise ValueError("No raster tiles supplied.")

    datasets = [rasterio.open(p) for p in tile_paths]
    try:
        first = datasets[0]
        src_crs = first.crs
        src_dtype = first.dtypes[0]
        src_nodata = first.nodata
        if src_nodata is None:
            src_nodata = default_nodata(src_dtype)

        for ds in datasets[1:]:
            if ds.crs != src_crs:
                raise ValueError(f"Mixed CRS within source tiles: {src_crs} vs {ds.crs}")

        geom_src = transform_geom(
            WORKING_CRS,
            src_crs,
            mapping(target_geom_wgs84),
            precision=6,
        )

        geom_bounds = (
            gpd.GeoSeries([target_geom_wgs84], crs=WORKING_CRS)
            .to_crs(src_crs)
            .total_bounds
        )

        mosaic, transform = merge(
            datasets,
            bounds=tuple(geom_bounds),
            nodata=src_nodata,
        )

        arr = mosaic[0]

        valid_mask = geometry_mask(
            [geom_src],
            out_shape=arr.shape,
            transform=transform,
            invert=True,
        )

        arr = np.where(valid_mask, arr, src_nodata).astype(src_dtype)

        profile = first.profile.copy()
        profile.update(
            {
                "height": arr.shape[0],
                "width": arr.shape[1],
                "transform": transform,
                "count": 1,
                "nodata": src_nodata,
                "dtype": str(arr.dtype),
                "compress": "deflate",
            }
        )

        return arr, profile

    finally:
        for ds in datasets:
            ds.close()


def reproject_to_reference(
    src_array: np.ndarray,
    src_profile: dict,
    ref_profile: dict,
    resampling: Resampling,
):
    src_nodata = src_profile.get("nodata")
    if src_nodata is None:
        src_nodata = default_nodata(src_profile["dtype"])

    dst_dtype = np.dtype(src_profile["dtype"])
    dst = np.full(
        (ref_profile["height"], ref_profile["width"]),
        fill_value=src_nodata,
        dtype=dst_dtype,
    )

    reproject(
        source=src_array,
        destination=dst,
        src_transform=src_profile["transform"],
        src_crs=src_profile["crs"],
        src_nodata=src_nodata,
        dst_transform=ref_profile["transform"],
        dst_crs=ref_profile["crs"],
        dst_nodata=src_nodata,
        resampling=resampling,
    )

    out_profile = ref_profile.copy()
    out_profile.update(
        {
            "count": 1,
            "dtype": str(dst.dtype),
            "nodata": src_nodata,
            "compress": "deflate",
        }
    )

    return dst, out_profile


def rasterize_favelas(local_favelas: gpd.GeoDataFrame, ref_profile: dict):
    if local_favelas.empty:
        mask = np.zeros((ref_profile["height"], ref_profile["width"]), dtype=np.uint8)
    else:
        local_ref = local_favelas.to_crs(ref_profile["crs"])
        shapes = [(geom, 1) for geom in local_ref.geometry if geom is not None and not geom.is_empty]

        mask = rasterize(
            shapes=shapes,
            out_shape=(ref_profile["height"], ref_profile["width"]),
            transform=ref_profile["transform"],
            fill=0,
            default_value=1,
            dtype="uint8",
        )

    mask_profile = ref_profile.copy()
    mask_profile.update(
        {
            "count": 1,
            "dtype": "uint8",
            "nodata": 0,
            "compress": "deflate",
        }
    )
    return mask, mask_profile


def write_raster(path: Path, arr: np.ndarray, profile: dict) -> None:
    ensure_dir(path.parent)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)


# =============================================================================
# PROCESS ONE CHUNK
# =============================================================================

def prepare_chunk(
    chunk_row: pd.Series,
    favelas: gpd.GeoDataFrame,
    mb_index: gpd.GeoDataFrame,
    ghsl_index: gpd.GeoDataFrame,
    wc_index: gpd.GeoDataFrame,
    output_root: Path,
    overwrite: bool = False,
):
    chunk_id = chunk_row["chunk_id"]
    chunk_geom = chunk_row.geometry
    buffer_deg = float(chunk_row["buffer_deg"])

    local_favelas, processing_geom = subset_favelas_for_chunk(
        favelas,
        chunk_geom,
        buffer_deg,
    )

    if local_favelas.empty:
        log(f"[SKIP] {chunk_id}: no local favelas.")
        return

    chunk_dir = output_root / "chunks" / chunk_id / "prepared"
    ensure_dir(chunk_dir)

    metadata_path = chunk_dir / "metadata.json"
    if metadata_path.exists() and not overwrite:
        log(f"[SKIP] {chunk_id}: already exists.")
        return

    log("=" * 80)
    log(f"[CHUNK] {chunk_id}")
    log("=" * 80)

    mb_tiles = select_tiles(mb_index, processing_geom)
    ghsl_tiles = select_tiles(ghsl_index, processing_geom)
    wc_tiles = select_tiles(wc_index, processing_geom)

    if not mb_tiles:
        raise RuntimeError(f"{chunk_id}: no MapBiomas tiles found.")
    if not ghsl_tiles:
        raise RuntimeError(f"{chunk_id}: no GHSL tiles found.")
    if not wc_tiles:
        raise RuntimeError(f"{chunk_id}: no WorldCover tiles found.")

    log(f"[INFO] {chunk_id}: local favela polygons = {len(local_favelas)}")
    log(f"[INFO] {chunk_id}: MapBiomas tiles = {len(mb_tiles)}")
    log(f"[INFO] {chunk_id}: GHSL tiles = {len(ghsl_tiles)}")
    log(f"[INFO] {chunk_id}: WorldCover tiles = {len(wc_tiles)}")

    # MapBiomas master grid
    log(f"[STEP] {chunk_id}: preparing MapBiomas...")
    mb_arr, mb_profile = mosaic_clip_native(mb_tiles, processing_geom)
    write_raster(chunk_dir / "mapbiomas.tif", mb_arr, mb_profile)

    # GHSL aligned to MapBiomas grid
    log(f"[STEP] {chunk_id}: preparing GHSL...")
    ghsl_arr_native, ghsl_profile_native = mosaic_clip_native(ghsl_tiles, processing_geom)
    ghsl_arr, ghsl_profile = reproject_to_reference(
        ghsl_arr_native,
        ghsl_profile_native,
        mb_profile,
        Resampling.bilinear,
    )
    write_raster(chunk_dir / "ghsl.tif", ghsl_arr, ghsl_profile)

    # WorldCover aligned to MapBiomas grid
    log(f"[STEP] {chunk_id}: preparing WorldCover...")
    wc_arr_native, wc_profile_native = mosaic_clip_native(wc_tiles, processing_geom)
    wc_arr, wc_profile = reproject_to_reference(
        wc_arr_native,
        wc_profile_native,
        mb_profile,
        Resampling.nearest,
    )
    write_raster(chunk_dir / "worldcover.tif", wc_arr, wc_profile)

    # Favela raster mask
    log(f"[STEP] {chunk_id}: rasterizing favela polygons...")
    fav_mask, fav_mask_profile = rasterize_favelas(local_favelas, mb_profile)
    write_raster(chunk_dir / "favela_mask.tif", fav_mask, fav_mask_profile)

    # Save vectors
    safe_write_gpkg(local_favelas, chunk_dir / "favelas.gpkg")
    safe_write_gpkg(
        gpd.GeoDataFrame(
            {"chunk_id": [chunk_id], "geometry": [processing_geom]},
            crs=WORKING_CRS,
        ),
        chunk_dir / "chunk_geom.gpkg",
    )

    metadata = {
        "chunk_id": chunk_id,
        "favela_count": int(len(local_favelas)),
        "buffer_deg": buffer_deg,
        "master_grid_source": "MapBiomas 10m 2021",
        "sources": {
            "mapbiomas_tiles": [str(p) for p in mb_tiles],
            "ghsl_tiles": [str(p) for p in ghsl_tiles],
            "worldcover_tiles": [str(p) for p in wc_tiles],
        },
        "outputs": {
            "mapbiomas": str(chunk_dir / "mapbiomas.tif"),
            "ghsl": str(chunk_dir / "ghsl.tif"),
            "worldcover": str(chunk_dir / "worldcover.tif"),
            "favela_mask": str(chunk_dir / "favela_mask.tif"),
            "favelas": str(chunk_dir / "favelas.gpkg"),
            "chunk_geom": str(chunk_dir / "chunk_geom.gpkg"),
        },
        "notes": [
            "MapBiomas 2021 is the master grid.",
            "GHSL 2022 aligned with bilinear resampling.",
            "WorldCover 2021 aligned with nearest resampling.",
            "Favela polygons rasterized on the MapBiomas grid.",
        ],
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    log(f"[DONE] {chunk_id}: prepared successfully.")


# =============================================================================
# MAIN
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare inputs for Brazil-scale favela refinement (2021 pipeline)."
    )
    parser.add_argument("--favela-path", type=Path, default=FAVELA_PATH)
    parser.add_argument("--mapbiomas-root", type=Path, default=MAPBIOMAS_ROOT)
    parser.add_argument("--ghsl-root", type=Path, default=GHSL_ROOT)
    parser.add_argument("--worldcover-root", type=Path, default=WORLDCOVER_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)

    parser.add_argument("--chunk-size-deg", type=float, default=DEFAULT_CHUNK_SIZE_DEG)
    parser.add_argument("--buffer-deg", type=float, default=DEFAULT_BUFFER_DEG)

    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--chunk-id", type=str, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_dir(args.output_root)

    favelas = load_favelas(args.favela_path)

    log("[CHUNKS] Building chunk index...")
    chunk_index = build_chunk_index(
        favelas,
        args.chunk_size_deg,
        args.buffer_deg,
    )

    if args.chunk_id is not None:
        chunk_index = chunk_index[chunk_index["chunk_id"] == args.chunk_id].copy()
        if chunk_index.empty:
            raise ValueError(f"Chunk not found: {args.chunk_id}")

    if args.limit is not None:
        chunk_index = chunk_index.head(args.limit).copy()

    chunk_index_path = args.output_root / "chunk_index.gpkg"
    safe_write_gpkg(chunk_index, chunk_index_path)
    log(f"[CHUNKS] Saved chunk index: {chunk_index_path}")
    log(f"[CHUNKS] Active chunks this run: {len(chunk_index)}")

    mb_index = build_raster_index(args.mapbiomas_root, "mapbiomas")
    ghsl_index = build_raster_index(args.ghsl_root, "ghsl")
    wc_index = build_raster_index(args.worldcover_root, "worldcover")

    safe_write_gpkg(mb_index, args.output_root / "mapbiomas_tile_index.gpkg")
    safe_write_gpkg(ghsl_index, args.output_root / "ghsl_tile_index.gpkg")
    safe_write_gpkg(wc_index, args.output_root / "worldcover_tile_index.gpkg")

    for _, row in chunk_index.iterrows():
        prepare_chunk(
            row,
            favelas,
            mb_index,
            ghsl_index,
            wc_index,
            args.output_root,
            overwrite=args.overwrite,
        )

    log("[DONE] Stage 1 completed.")


if __name__ == "__main__":
    main()