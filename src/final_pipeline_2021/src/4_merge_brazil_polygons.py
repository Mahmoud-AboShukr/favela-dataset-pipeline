from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import pandas as pd


# =============================================================================
# PATHS / CONFIG
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / "data" / "processed" / "final_pipeline_2021"

RAW_MERGED_NAME = "brazil_refined_raw_merged.gpkg"
DISSOLVED_MERGED_NAME = "brazil_refined_dissolved_merged.gpkg"


# =============================================================================
# HELPERS
# =============================================================================

def log(msg: str) -> None:
    print(msg, flush=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def safe_unlink(path: Path) -> None:
    if path.exists():
        path.unlink()


def list_chunk_dirs(output_root: Path) -> List[Path]:
    chunks_root = output_root / "chunks"
    if not chunks_root.exists():
        raise FileNotFoundError(f"Chunks folder not found: {chunks_root}")

    chunk_dirs = sorted([p for p in chunks_root.iterdir() if p.is_dir()])
    if not chunk_dirs:
        raise RuntimeError(f"No chunk folders found under: {chunks_root}")

    return chunk_dirs


def read_vector(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Vector file not found: {path}")
    return gpd.read_file(path)


def standardize_crs(gdf: gpd.GeoDataFrame, target_crs) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf.set_crs(target_crs, allow_override=True) if gdf.crs is None else gdf.to_crs(target_crs)
    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS.")
    if str(gdf.crs) != str(target_crs):
        return gdf.to_crs(target_crs)
    return gdf


def add_chunk_context(
    gdf: gpd.GeoDataFrame,
    chunk_id: str,
    id_col_hint: str | None = None,
) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["chunk_id"] = chunk_id

    # Make source_id globally unique across chunks if present
    if "source_id" in gdf.columns:
        gdf["source_id_local"] = gdf["source_id"].astype(str)
        gdf["source_id"] = gdf["chunk_id"].astype(str) + "__" + gdf["source_id_local"]

    # Create globally unique raw id if helpful
    if id_col_hint is not None and id_col_hint in gdf.columns:
        gdf[f"{id_col_hint}_local"] = gdf[id_col_hint].astype(str)
        gdf[id_col_hint] = gdf["chunk_id"].astype(str) + "__" + gdf[f"{id_col_hint}_local"]

    return gdf


def collect_chunk_outputs(
    chunk_dirs: List[Path],
) -> Tuple[List[gpd.GeoDataFrame], List[gpd.GeoDataFrame]]:
    raw_parts: List[gpd.GeoDataFrame] = []
    dissolved_parts: List[gpd.GeoDataFrame] = []

    for chunk_dir in chunk_dirs:
        polygonized_dir = chunk_dir / "polygonized"
        raw_path = polygonized_dir / "refined_raw.gpkg"
        dissolved_path = polygonized_dir / "refined_dissolved.gpkg"

        if not raw_path.exists():
            log(f"[WARN] {chunk_dir.name}: missing {raw_path.name}, skipping raw.")
        else:
            raw_gdf = read_vector(raw_path)
            raw_gdf = add_chunk_context(raw_gdf, chunk_dir.name, id_col_hint="raw_id")
            raw_parts.append(raw_gdf)

        if not dissolved_path.exists():
            log(f"[WARN] {chunk_dir.name}: missing {dissolved_path.name}, skipping dissolved.")
        else:
            dissolved_gdf = read_vector(dissolved_path)
            dissolved_gdf = add_chunk_context(dissolved_gdf, chunk_dir.name)
            dissolved_parts.append(dissolved_gdf)

    return raw_parts, dissolved_parts


def concat_geodataframes(parts: List[gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    if not parts:
        return gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs=None)

    target_crs = parts[0].crs
    aligned = [standardize_crs(gdf, target_crs) for gdf in parts]

    merged = pd.concat(aligned, ignore_index=True, sort=False)
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=target_crs)
    return merged


def save_vector(gdf: gpd.GeoDataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    safe_unlink(path)
    gdf.to_file(path, driver="GPKG")


def summarize_merge(gdf: gpd.GeoDataFrame, name: str) -> None:
    if gdf.empty:
        log(f"[SUMMARY] {name}: empty")
        return

    log(f"[SUMMARY] {name}:")
    log(f"  rows: {len(gdf)}")
    log(f"  crs: {gdf.crs}")
    log(f"  columns: {list(gdf.columns)}")


# =============================================================================
# MAIN
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge all chunk-level polygon outputs into Brazil-wide layers (2021 pipeline)."
    )
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    chunk_dirs = list_chunk_dirs(args.output_root)
    log(f"[RUN] Chunk folders found: {len(chunk_dirs)}")

    raw_out = args.output_root / RAW_MERGED_NAME
    dissolved_out = args.output_root / DISSOLVED_MERGED_NAME

    if raw_out.exists() and dissolved_out.exists() and not args.overwrite:
        log("[SKIP] Merged outputs already exist. Use --overwrite to replace them.")
        return

    log("[STEP] Collecting chunk-level polygon outputs...")
    raw_parts, dissolved_parts = collect_chunk_outputs(chunk_dirs)

    log(f"[INFO] Raw chunk layers collected: {len(raw_parts)}")
    log(f"[INFO] Dissolved chunk layers collected: {len(dissolved_parts)}")

    log("[STEP] Merging raw layers...")
    merged_raw = concat_geodataframes(raw_parts)

    log("[STEP] Merging dissolved layers...")
    merged_dissolved = concat_geodataframes(dissolved_parts)

    summarize_merge(merged_raw, "merged_raw")
    summarize_merge(merged_dissolved, "merged_dissolved")

    log("[STEP] Saving merged outputs...")
    save_vector(merged_raw, raw_out)
    save_vector(merged_dissolved, dissolved_out)

    log(f"[DONE] Saved raw merged layer: {raw_out}")
    log(f"[DONE] Saved dissolved merged layer: {dissolved_out}")
    log("[DONE] Stage 4 completed.")


if __name__ == "__main__":
    main()