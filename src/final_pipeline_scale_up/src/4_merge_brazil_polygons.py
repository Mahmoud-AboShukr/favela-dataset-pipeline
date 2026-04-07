from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import geopandas as gpd
import pandas as pd


# =============================================================================
# CONFIG
# =============================================================================

OUTPUT_ROOT = Path("data/processed/final_pipeline_scale_up")

RAW_FILENAME = "refined_raw.gpkg"
DISSOLVED_FILENAME = "refined_dissolved.gpkg"

OUT_RAW = OUTPUT_ROOT / "brazil_refined_raw.gpkg"
OUT_DISSOLVED = OUTPUT_ROOT / "brazil_refined_dissolved.gpkg"


# =============================================================================
# HELPERS
# =============================================================================

def log(msg: str) -> None:
    print(msg, flush=True)


def list_chunk_dirs(output_root: Path) -> List[Path]:
    chunks_root = output_root / "chunks"
    if not chunks_root.exists():
        raise FileNotFoundError(f"Chunks folder not found: {chunks_root}")
    chunk_dirs = sorted([p for p in chunks_root.iterdir() if p.is_dir()])
    if not chunk_dirs:
        raise RuntimeError(f"No chunk folders found under: {chunks_root}")
    return chunk_dirs


def safe_unlink(path: Path) -> None:
    if path.exists():
        path.unlink()


def read_gpkg(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    gdf = gpd.read_file(path)
    if gdf.empty:
        return gdf
    if gdf.crs is None:
        raise ValueError(f"GeoDataFrame has no CRS: {path}")
    return gdf


def ensure_same_crs(gdf: gpd.GeoDataFrame, target_crs) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    if str(gdf.crs) != str(target_crs):
        return gdf.to_crs(target_crs)
    return gdf


def add_chunk_id_if_missing(gdf: gpd.GeoDataFrame, chunk_id: str) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    if "chunk_id" not in gdf.columns:
        gdf["chunk_id"] = chunk_id
    else:
        gdf["chunk_id"] = gdf["chunk_id"].fillna(chunk_id)
    return gdf


def prefix_source_id(gdf: gpd.GeoDataFrame, chunk_id: str) -> gpd.GeoDataFrame:
    """
    Make source_id globally unique across chunks.
    """
    gdf = gdf.copy()
    if "source_id" in gdf.columns:
        gdf["source_id"] = gdf["source_id"].astype(str)
        gdf["source_id"] = gdf["source_id"].apply(
            lambda x: f"{chunk_id}__{x}" if x not in ["nan", "None", ""] else x
        )
    return gdf


def write_gpkg(gdf: gpd.GeoDataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_unlink(path)
    gdf.to_file(path, driver="GPKG")


# =============================================================================
# MERGE LOGIC
# =============================================================================

def collect_chunk_polygons(
    output_root: Path,
    filename: str,
    include_empty: bool = False,
) -> gpd.GeoDataFrame:
    chunk_dirs = list_chunk_dirs(output_root)

    collected = []
    target_crs = None
    found_files = 0
    missing_files = 0
    empty_files = 0

    for chunk_dir in chunk_dirs:
        poly_path = chunk_dir / "polygonized" / filename

        if not poly_path.exists():
            missing_files += 1
            log(f"[SKIP] {chunk_dir.name}: missing {filename}")
            continue

        found_files += 1
        gdf = read_gpkg(poly_path)

        if gdf.empty:
            empty_files += 1
            log(f"[INFO] {chunk_dir.name}: empty {filename}")
            if include_empty:
                gdf = add_chunk_id_if_missing(gdf, chunk_dir.name)
                collected.append(gdf)
            continue

        if target_crs is None:
            target_crs = gdf.crs

        gdf = ensure_same_crs(gdf, target_crs)
        gdf = add_chunk_id_if_missing(gdf, chunk_dir.name)
        gdf = prefix_source_id(gdf, chunk_dir.name)

        collected.append(gdf)
        log(f"[ADD] {chunk_dir.name}: {len(gdf)} features from {filename}")

    if not collected:
        if target_crs is None:
            target_crs = "EPSG:4326"
        result = gpd.GeoDataFrame(geometry=[], crs=target_crs)
    else:
        result = gpd.GeoDataFrame(
            pd.concat(collected, ignore_index=True),
            geometry="geometry",
            crs=target_crs,
        )

    log("-" * 80)
    log(f"[SUMMARY] file type: {filename}")
    log(f"[SUMMARY] chunk files found   : {found_files}")
    log(f"[SUMMARY] chunk files missing : {missing_files}")
    log(f"[SUMMARY] empty files         : {empty_files}")
    log(f"[SUMMARY] merged features     : {len(result)}")
    log("-" * 80)

    return result


# =============================================================================
# MAIN
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge chunk-level polygon outputs into one Brazil-wide GPKG."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=OUTPUT_ROOT,
        help="Root folder of final_pipeline_scale_up outputs.",
    )
    parser.add_argument(
        "--raw-filename",
        type=str,
        default=RAW_FILENAME,
        help="Chunk-level raw polygon filename.",
    )
    parser.add_argument(
        "--dissolved-filename",
        type=str,
        default=DISSOLVED_FILENAME,
        help="Chunk-level dissolved polygon filename.",
    )
    parser.add_argument(
        "--out-raw",
        type=Path,
        default=OUT_RAW,
        help="Brazil-wide output path for merged raw polygons.",
    )
    parser.add_argument(
        "--out-dissolved",
        type=Path,
        default=OUT_DISSOLVED,
        help="Brazil-wide output path for merged dissolved polygons.",
    )
    parser.add_argument(
        "--skip-raw",
        action="store_true",
        help="Skip merging raw polygons.",
    )
    parser.add_argument(
        "--skip-dissolved",
        action="store_true",
        help="Skip merging dissolved polygons.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.skip_raw:
        log("=" * 80)
        log("MERGING BRAZIL RAW POLYGONS")
        log("=" * 80)
        merged_raw = collect_chunk_polygons(args.output_root, args.raw_filename)
        write_gpkg(merged_raw, args.out_raw)
        log(f"[DONE] Wrote merged raw polygons: {args.out_raw}")
        log("")

    if not args.skip_dissolved:
        log("=" * 80)
        log("MERGING BRAZIL DISSOLVED POLYGONS")
        log("=" * 80)
        merged_dissolved = collect_chunk_polygons(args.output_root, args.dissolved_filename)
        write_gpkg(merged_dissolved, args.out_dissolved)
        log(f"[DONE] Wrote merged dissolved polygons: {args.out_dissolved}")
        log("")

    log("[DONE] Brazil-wide merge completed.")


if __name__ == "__main__":
    main()