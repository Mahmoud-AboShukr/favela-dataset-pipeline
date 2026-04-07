from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape


# =============================================================================
# PATHS / CONFIG
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / "data" / "processed" / "final_pipeline_2021"


# =============================================================================
# HELPERS
# =============================================================================

def log(msg: str) -> None:
    print(msg, flush=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def list_chunk_dirs(output_root: Path) -> List[Path]:
    chunks_root = output_root / "chunks"
    if not chunks_root.exists():
        raise FileNotFoundError(f"Chunks folder not found: {chunks_root}")
    chunk_dirs = sorted([p for p in chunks_root.iterdir() if p.is_dir()])
    if not chunk_dirs:
        raise RuntimeError(f"No chunk folders found under: {chunks_root}")
    return chunk_dirs


def read_raster(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Raster not found: {path}")
    with rasterio.open(path) as src:
        arr = src.read(1)
        profile = src.profile.copy()
    return arr, profile


def safe_unlink(path: Path) -> None:
    if path.exists():
        path.unlink()


def save_vector(gdf: gpd.GeoDataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    safe_unlink(path)
    gdf.to_file(path, driver="GPKG")


def polygonize_binary_mask(mask: np.ndarray, transform, crs) -> gpd.GeoDataFrame:
    mask = mask.astype(np.uint8)
    geoms = []
    values = []

    for geom, value in shapes(mask, mask=(mask == 1), transform=transform):
        if int(value) != 1:
            continue
        geoms.append(shape(geom))
        values.append(int(value))

    if not geoms:
        return gpd.GeoDataFrame({"value": []}, geometry=[], crs=crs)

    return gpd.GeoDataFrame({"value": values}, geometry=geoms, crs=crs)


def load_local_favelas(prepared_dir: Path) -> gpd.GeoDataFrame:
    path = prepared_dir / "favelas.gpkg"
    if not path.exists():
        raise FileNotFoundError(f"Missing local favela file: {path}")
    return gpd.read_file(path)


def load_chunk_geom(prepared_dir: Path) -> gpd.GeoDataFrame:
    path = prepared_dir / "chunk_geom.gpkg"
    if not path.exists():
        raise FileNotFoundError(f"Missing chunk geometry file: {path}")
    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError(f"Empty chunk geometry file: {path}")
    return gdf


def ensure_same_crs(target: gpd.GeoDataFrame, reference: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if target.empty:
        return target
    if target.crs is None:
        raise ValueError("Target GeoDataFrame has no CRS.")
    if reference.crs is None:
        raise ValueError("Reference GeoDataFrame has no CRS.")
    if str(target.crs) != str(reference.crs):
        return target.to_crs(reference.crs)
    return target


def add_area_m2(gdf: gpd.GeoDataFrame, col_name: str) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    if gdf.empty:
        gdf[col_name] = pd.Series(dtype="float64")
        return gdf
    gdf_m = gdf.to_crs("EPSG:3857")
    gdf[col_name] = gdf_m.geometry.area.astype(float)
    return gdf


def assign_source_ids_by_largest_overlap(
    refined_gdf: gpd.GeoDataFrame,
    source_favelas_gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    if refined_gdf.empty:
        refined_gdf = refined_gdf.copy()
        refined_gdf["source_id"] = pd.Series(dtype="object")
        return refined_gdf

    if source_favelas_gdf.empty:
        refined_gdf = refined_gdf.copy()
        refined_gdf["source_id"] = pd.Series(dtype="object")
        return refined_gdf

    refined = ensure_same_crs(refined_gdf, source_favelas_gdf).copy()
    sources = source_favelas_gdf.copy()

    if "source_id" not in sources.columns:
        sources["source_id"] = np.arange(1, len(sources) + 1)

    refined["raw_id"] = np.arange(1, len(refined) + 1)

    candidates = gpd.overlay(
        refined[["raw_id", "geometry"]],
        sources[["source_id", "geometry"]],
        how="intersection",
    )

    if candidates.empty:
        refined["source_id"] = pd.Series(dtype="object")
        return refined.drop(columns=["raw_id"])

    candidates = add_area_m2(candidates, "overlap_area_m2")

    best = (
        candidates.sort_values(["raw_id", "overlap_area_m2"], ascending=[True, False])
        .drop_duplicates(subset=["raw_id"])
        [["raw_id", "source_id"]]
    )

    refined = refined.merge(best, on="raw_id", how="left")
    refined = refined.drop(columns=["raw_id"])
    return refined


def dissolve_by_source_id(refined_raw_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if refined_raw_gdf.empty:
        return gpd.GeoDataFrame({"source_id": []}, geometry=[], crs=refined_raw_gdf.crs)

    gdf = refined_raw_gdf.copy()

    assigned = gdf[gdf["source_id"].notna()].copy()
    unassigned = gdf[gdf["source_id"].isna()].copy()

    parts = []

    if not assigned.empty:
        dissolved_assigned = assigned.dissolve(by="source_id", as_index=False)
        parts.append(dissolved_assigned[["source_id", "geometry"]].copy())

    if not unassigned.empty:
        unassigned = unassigned.reset_index(drop=True)
        unassigned["source_id"] = [f"unassigned_{i+1}" for i in range(len(unassigned))]
        parts.append(unassigned[["source_id", "geometry"]].copy())

    if not parts:
        return gpd.GeoDataFrame({"source_id": []}, geometry=[], crs=gdf.crs)

    dissolved = pd.concat(parts, ignore_index=True)
    return gpd.GeoDataFrame(dissolved, geometry="geometry", crs=gdf.crs)


def clip_to_chunk(gdf: gpd.GeoDataFrame, chunk_geom: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    gdf = ensure_same_crs(gdf, chunk_geom)
    return gpd.overlay(gdf, chunk_geom[["geometry"]], how="intersection")


def area_in_m2(gdf: gpd.GeoDataFrame) -> float:
    if gdf.empty:
        return 0.0
    gdf_m = gdf.to_crs("EPSG:3857")
    return float(gdf_m.geometry.area.sum())


def count_source_polygons_with_match(dissolved_gdf: gpd.GeoDataFrame) -> int:
    if dissolved_gdf.empty or "source_id" not in dissolved_gdf.columns:
        return 0
    src_ids = dissolved_gdf["source_id"].dropna().astype(str)
    src_ids = src_ids[~src_ids.str.startswith("unassigned_")]
    return int(src_ids.nunique())


def compute_qc_metrics(
    local_favelas_gdf: gpd.GeoDataFrame,
    refined_raw_gdf: gpd.GeoDataFrame,
    refined_dissolved_gdf: gpd.GeoDataFrame,
    chunk_id: str,
) -> Dict[str, float]:
    metrics = {
        "chunk_id": chunk_id,
        "source_polygon_count": int(len(local_favelas_gdf)),
        "refined_raw_polygon_count": int(len(refined_raw_gdf)),
        "refined_dissolved_polygon_count": int(len(refined_dissolved_gdf)),
        "matched_source_polygon_count": int(count_source_polygons_with_match(refined_dissolved_gdf)),
        "source_area_m2": area_in_m2(local_favelas_gdf),
        "refined_raw_area_m2": area_in_m2(refined_raw_gdf),
        "refined_dissolved_area_m2": area_in_m2(refined_dissolved_gdf),
    }

    if metrics["source_area_m2"] > 0:
        metrics["refined_vs_source_area_ratio"] = (
            metrics["refined_dissolved_area_m2"] / metrics["source_area_m2"]
        )
    else:
        metrics["refined_vs_source_area_ratio"] = 0.0

    return metrics


def save_qc_metrics_csv(metrics: Dict[str, float], path: Path) -> None:
    ensure_dir(path.parent)
    df = pd.DataFrame([{"metric": k, "value": v} for k, v in metrics.items()])
    df.to_csv(path, index=False)


# =============================================================================
# PROCESS ONE CHUNK
# =============================================================================

def process_chunk(chunk_dir: Path, overwrite: bool = False) -> None:
    prepared_dir = chunk_dir / "prepared"
    refined_dir = chunk_dir / "refined"
    polygonized_dir = chunk_dir / "polygonized"

    if not prepared_dir.exists():
        log(f"[SKIP] {chunk_dir.name}: missing prepared folder.")
        return
    if not refined_dir.exists():
        log(f"[SKIP] {chunk_dir.name}: missing refined folder.")
        return

    refined_mask_path = refined_dir / "refined_mask_clean.tif"
    if not refined_mask_path.exists():
        log(f"[SKIP] {chunk_dir.name}: missing refined_mask_clean.tif.")
        return

    ensure_dir(polygonized_dir)

    raw_out_path = polygonized_dir / "refined_raw.gpkg"
    dissolved_out_path = polygonized_dir / "refined_dissolved.gpkg"
    qc_json_path = polygonized_dir / "qc_metrics.json"
    qc_csv_path = polygonized_dir / "qc_metrics.csv"

    if raw_out_path.exists() and dissolved_out_path.exists() and qc_json_path.exists() and not overwrite:
        log(f"[SKIP] {chunk_dir.name}: polygonized outputs already exist.")
        return

    log("=" * 80)
    log(f"[CHUNK] {chunk_dir.name}")
    log("=" * 80)

    refined_mask, profile = read_raster(refined_mask_path)
    local_favelas = load_local_favelas(prepared_dir)
    chunk_geom = load_chunk_geom(prepared_dir)

    log(f"[STEP] {chunk_dir.name}: polygonizing refined mask...")
    refined_raw = polygonize_binary_mask(refined_mask, profile["transform"], profile["crs"])

    if refined_raw.empty:
        refined_raw = gpd.GeoDataFrame(
            {"value": [], "source_id": [], "raw_area_m2": []},
            geometry=[],
            crs=profile["crs"],
        )
        refined_dissolved = gpd.GeoDataFrame(
            {"source_id": []},
            geometry=[],
            crs=profile["crs"],
        )
    else:
        refined_raw = add_area_m2(refined_raw, "raw_area_m2")

        log(f"[STEP] {chunk_dir.name}: assigning source ids...")
        refined_raw = assign_source_ids_by_largest_overlap(refined_raw, local_favelas)

        log(f"[STEP] {chunk_dir.name}: dissolving by source id...")
        refined_dissolved = dissolve_by_source_id(refined_raw)

    log(f"[STEP] {chunk_dir.name}: clipping polygon outputs to chunk geometry...")
    refined_raw = clip_to_chunk(refined_raw, chunk_geom)
    refined_dissolved = clip_to_chunk(refined_dissolved, chunk_geom)

    log(f"[STEP] {chunk_dir.name}: computing QC metrics...")
    qc_metrics = compute_qc_metrics(
        local_favelas_gdf=local_favelas,
        refined_raw_gdf=refined_raw,
        refined_dissolved_gdf=refined_dissolved,
        chunk_id=chunk_dir.name,
    )

    log(f"[STEP] {chunk_dir.name}: saving outputs...")
    save_vector(refined_raw, raw_out_path)
    save_vector(refined_dissolved, dissolved_out_path)

    with open(qc_json_path, "w", encoding="utf-8") as f:
        json.dump(qc_metrics, f, indent=2)

    save_qc_metrics_csv(qc_metrics, qc_csv_path)

    log(f"[DONE] {chunk_dir.name}: polygonized successfully.")


# =============================================================================
# MAIN
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Polygonize refined chunk rasters and compute QC metrics (2021 pipeline)."
    )
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--chunk-id", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    chunk_dirs = list_chunk_dirs(args.output_root)

    if args.chunk_id is not None:
        chunk_dirs = [p for p in chunk_dirs if p.name == args.chunk_id]
        if not chunk_dirs:
            raise ValueError(f"Chunk not found: {args.chunk_id}")

    if args.limit is not None:
        chunk_dirs = chunk_dirs[:args.limit]

    log(f"[RUN] Chunks to process: {len(chunk_dirs)}")

    for chunk_dir in chunk_dirs:
        process_chunk(chunk_dir=chunk_dir, overwrite=args.overwrite)

    log("[DONE] Stage 3 completed.")


if __name__ == "__main__":
    main()