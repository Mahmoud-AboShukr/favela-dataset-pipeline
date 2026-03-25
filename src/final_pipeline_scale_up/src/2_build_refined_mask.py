from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import rasterio
from scipy import ndimage as ndi


# =============================================================================
# CONFIG
# =============================================================================

OUTPUT_ROOT = Path("data/processed/final_pipeline_scale_up")

# MapBiomas classes
MAPBIOMAS_BUILT = {24}
MAPBIOMAS_UNCERTAIN = {25}
MAPBIOMAS_VEGETATION = {3, 4, 5, 6, 11, 12, 49, 50}
MAPBIOMAS_HARD_REMOVE = {31, 33}

# WorldCover 2021 classes commonly treated as vegetation / non-target
# 10 Tree cover
# 20 Shrubland
# 30 Grassland
# 90 Herbaceous wetland
# 95 Mangroves
# 100 Moss and lichen
WORLDCOVER_VEGETATION = {10, 20, 30, 90, 95, 100}

# Optional hard remove from WorldCover
# 80 Permanent water bodies
WORLDCOVER_HARD_REMOVE = {80}

# GHSL threshold
DEFAULT_GHSL_KEEP_THRESHOLD = 20.0

# Morphology
DEFAULT_MIN_OBJECT_PIXELS = 9
DEFAULT_MAX_HOLE_PIXELS = 9


# =============================================================================
# HELPERS
# =============================================================================

def log(msg: str) -> None:
    print(msg, flush=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_raster(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Raster not found: {path}")
    with rasterio.open(path) as src:
        arr = src.read(1)
        profile = src.profile.copy()
    return arr, profile


def write_raster(path: Path, arr: np.ndarray, profile: dict) -> None:
    ensure_dir(path.parent)
    out_profile = profile.copy()
    out_profile.update(
        {
            "count": 1,
            "dtype": str(arr.dtype),
            "compress": "deflate",
            "nodata": 0 if arr.dtype == np.uint8 else profile.get("nodata"),
        }
    )
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(arr, 1)


def list_chunk_dirs(output_root: Path) -> List[Path]:
    chunks_root = output_root / "chunks"
    if not chunks_root.exists():
        raise FileNotFoundError(f"Chunks folder not found: {chunks_root}")
    chunk_dirs = sorted([p for p in chunks_root.iterdir() if p.is_dir()])
    if not chunk_dirs:
        raise RuntimeError(f"No chunk folders found under: {chunks_root}")
    return chunk_dirs


def build_class_mask(arr: np.ndarray, classes: Iterable[int]) -> np.ndarray:
    classes = list(classes)
    if len(classes) == 0:
        return np.zeros(arr.shape, dtype=bool)
    return np.isin(arr, classes)


def get_valid_mask(arr: np.ndarray, nodata) -> np.ndarray:
    if nodata is None:
        return np.ones(arr.shape, dtype=bool)
    return arr != nodata


def build_ghsl_support_mask(
    ghsl: np.ndarray,
    ghsl_nodata,
    threshold: float,
) -> np.ndarray:
    valid = get_valid_mask(ghsl, ghsl_nodata)
    support = valid & (ghsl >= threshold)
    return support


def remove_small_objects(binary: np.ndarray, min_pixels: int) -> np.ndarray:
    if min_pixels <= 1:
        return binary.copy()

    structure = np.ones((3, 3), dtype=np.uint8)
    labels, n = ndi.label(binary, structure=structure)
    if n == 0:
        return binary.copy()

    counts = np.bincount(labels.ravel())
    keep = counts >= min_pixels
    keep[0] = False
    cleaned = keep[labels]
    return cleaned.astype(bool)


def fill_small_holes(binary: np.ndarray, max_hole_pixels: int) -> np.ndarray:
    if max_hole_pixels <= 0:
        return binary.copy()

    inv = ~binary
    structure = np.ones((3, 3), dtype=np.uint8)
    labels, n = ndi.label(inv, structure=structure)
    if n == 0:
        return binary.copy()

    # Find background components touching border; those are not holes
    border_labels = set()
    border_labels.update(np.unique(labels[0, :]).tolist())
    border_labels.update(np.unique(labels[-1, :]).tolist())
    border_labels.update(np.unique(labels[:, 0]).tolist())
    border_labels.update(np.unique(labels[:, -1]).tolist())

    counts = np.bincount(labels.ravel())
    fill = np.zeros_like(binary, dtype=bool)

    for lbl in range(1, n + 1):
        if lbl in border_labels:
            continue
        if counts[lbl] <= max_hole_pixels:
            fill |= labels == lbl

    return binary | fill


def compute_summary(masks: Dict[str, np.ndarray]) -> Dict[str, int]:
    return {k: int(v.sum()) for k, v in masks.items()}


def build_mapbiomas_masks(mapbiomas: np.ndarray) -> Dict[str, np.ndarray]:
    return {
        "core_built": build_class_mask(mapbiomas, MAPBIOMAS_BUILT),
        "uncertain": build_class_mask(mapbiomas, MAPBIOMAS_UNCERTAIN),
        "vegetation": build_class_mask(mapbiomas, MAPBIOMAS_VEGETATION),
        "hard_remove": build_class_mask(mapbiomas, MAPBIOMAS_HARD_REMOVE),
    }


def build_worldcover_masks(worldcover: np.ndarray) -> Dict[str, np.ndarray]:
    return {
        "wc_vegetation": build_class_mask(worldcover, WORLDCOVER_VEGETATION),
        "wc_hard_remove": build_class_mask(worldcover, WORLDCOVER_HARD_REMOVE),
    }


# =============================================================================
# ONE-CHUNK PROCESSING
# =============================================================================

def process_chunk(
    chunk_dir: Path,
    ghsl_threshold: float,
    min_object_pixels: int,
    max_hole_pixels: int,
    overwrite: bool = False,
) -> None:
    prepared_dir = chunk_dir / "prepared"
    refined_dir = chunk_dir / "refined"

    if not prepared_dir.exists():
        log(f"[SKIP] {chunk_dir.name}: missing prepared folder.")
        return

    ensure_dir(refined_dir)

    final_mask_path = refined_dir / "refined_mask_clean.tif"
    if final_mask_path.exists() and not overwrite:
        log(f"[SKIP] {chunk_dir.name}: refined outputs already exist.")
        return

    mapbiomas_path = prepared_dir / "mapbiomas.tif"
    ghsl_path = prepared_dir / "ghsl.tif"
    worldcover_path = prepared_dir / "worldcover.tif"
    favela_mask_path = prepared_dir / "favela_mask.tif"

    for p in [mapbiomas_path, ghsl_path, worldcover_path, favela_mask_path]:
        if not p.exists():
            raise FileNotFoundError(f"{chunk_dir.name}: missing required input {p}")

    log("=" * 80)
    log(f"[CHUNK] {chunk_dir.name}")
    log("=" * 80)

    mapbiomas, mb_profile = read_raster(mapbiomas_path)
    ghsl, ghsl_profile = read_raster(ghsl_path)
    worldcover, _ = read_raster(worldcover_path)
    favela_mask, _ = read_raster(favela_mask_path)

    # Basic shape check
    shape = mapbiomas.shape
    for name, arr in {
        "ghsl": ghsl,
        "worldcover": worldcover,
        "favela_mask": favela_mask,
    }.items():
        if arr.shape != shape:
            raise ValueError(
                f"{chunk_dir.name}: shape mismatch. "
                f"mapbiomas={shape}, {name}={arr.shape}"
            )

    log(f"[STEP] {chunk_dir.name}: building thematic masks...")
    mb_masks = build_mapbiomas_masks(mapbiomas)
    wc_masks = build_worldcover_masks(worldcover)

    inside_favela = favela_mask > 0
    ghsl_support = build_ghsl_support_mask(
        ghsl=ghsl,
        ghsl_nodata=ghsl_profile.get("nodata"),
        threshold=ghsl_threshold,
    )

    # Core logic
    # - always keep clear built
    # - allow uncertain only if GHSL supports
    # - remove vegetation / hard remove
    supported_uncertain = mb_masks["uncertain"] & ghsl_support
    candidate = (mb_masks["core_built"] | supported_uncertain) & inside_favela

    remove_mask = (
        mb_masks["vegetation"]
        | mb_masks["hard_remove"]
        | wc_masks["wc_vegetation"]
        | wc_masks["wc_hard_remove"]
    )

    refined_mask = candidate & (~remove_mask)

    log(f"[STEP] {chunk_dir.name}: morphological cleanup...")
    refined_mask_clean = remove_small_objects(refined_mask, min_object_pixels)
    refined_mask_clean = fill_small_holes(refined_mask_clean, max_hole_pixels)

    # Save outputs
    raw_out = refined_mask.astype(np.uint8)
    clean_out = refined_mask_clean.astype(np.uint8)

    write_raster(refined_dir / "refined_mask.tif", raw_out, mb_profile)
    write_raster(refined_dir / "refined_mask_clean.tif", clean_out, mb_profile)

    summary = compute_summary(
        {
            "inside_favela": inside_favela,
            "core_built": mb_masks["core_built"],
            "uncertain": mb_masks["uncertain"],
            "vegetation": mb_masks["vegetation"],
            "hard_remove": mb_masks["hard_remove"],
            "ghsl_support": ghsl_support,
            "wc_vegetation": wc_masks["wc_vegetation"],
            "wc_hard_remove": wc_masks["wc_hard_remove"],
            "supported_uncertain": supported_uncertain,
            "candidate": candidate,
            "refined_mask": refined_mask,
            "refined_mask_clean": refined_mask_clean,
        }
    )

    summary.update(
        {
            "chunk_id": chunk_dir.name,
            "ghsl_threshold": ghsl_threshold,
            "min_object_pixels": min_object_pixels,
            "max_hole_pixels": max_hole_pixels,
        }
    )

    with open(refined_dir / "pixel_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log(f"[DONE] {chunk_dir.name}: refined successfully.")


# =============================================================================
# MAIN
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Build refined raster masks for prepared Brazil-scale favela chunks."
    )
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--chunk-id", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")

    parser.add_argument("--ghsl-threshold", type=float, default=DEFAULT_GHSL_KEEP_THRESHOLD)
    parser.add_argument("--min-object-pixels", type=int, default=DEFAULT_MIN_OBJECT_PIXELS)
    parser.add_argument("--max-hole-pixels", type=int, default=DEFAULT_MAX_HOLE_PIXELS)

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
    log(f"[RUN] GHSL threshold: {args.ghsl_threshold}")
    log(f"[RUN] Min object pixels: {args.min_object_pixels}")
    log(f"[RUN] Max hole pixels: {args.max_hole_pixels}")

    for chunk_dir in chunk_dirs:
        process_chunk(
            chunk_dir=chunk_dir,
            ghsl_threshold=args.ghsl_threshold,
            min_object_pixels=args.min_object_pixels,
            max_hole_pixels=args.max_hole_pixels,
            overwrite=args.overwrite,
        )

    log("[DONE] Stage 2 completed.")


if __name__ == "__main__":
    main()