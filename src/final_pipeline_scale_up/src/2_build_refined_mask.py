"""
2_build_refined_mask.py

Purpose
-------
Build the refined raster favela mask by combining:
- MapBiomas
- WSF
- GHSL
- WorldCover

Main idea
---------
MapBiomas provides the thematic starting point.
WSF provides strict settlement confirmation.
GHSL provides broader built-up support.
WorldCover helps suppress vegetation spillover.

The output is a cleaned binary raster mask representing the refined favela
candidate footprint.
"""

from pathlib import Path
import json


# =============================================================================
# CONFIG
# =============================================================================

CITY_NAME = "manaus"

PREPARED_DIR = Path("data/processed/final_pipeline") / CITY_NAME / "prepared"
REFINED_DIR = Path("data/processed/final_pipeline") / CITY_NAME / "refined"
REFINED_DIR.mkdir(parents=True, exist_ok=True)

MAPBIOMAS_PATH = PREPARED_DIR / "mapbiomas_aoi.tif"
WSF_PATH = PREPARED_DIR / "wsf_aoi.tif"
GHSL_PATH = PREPARED_DIR / "ghsl_aoi.tif"
WORLDCOVER_PATH = PREPARED_DIR / "worldcover_aoi.tif"
FAVELA_MASK_PATH = PREPARED_DIR / "favela_raster_mask.tif"


# =============================================================================
# CLASS / THRESHOLD CONFIG
# =============================================================================

MAPBIOMAS_BUILT = {24}
MAPBIOMAS_UNCERTAIN = {25}
MAPBIOMAS_VEGETATION = {3, 4, 5, 6, 11, 12, 49, 50}
MAPBIOMAS_HARD_REMOVE = {31, 33}

GHSL_KEEP_THRESHOLD = 20
MIN_OBJECT_PIXELS = 9
FILL_HOLE_PIXELS = 9


# =============================================================================
# HELPER PLACEHOLDERS
# =============================================================================

def read_raster(path):
    """
    Read raster array + profile.
    """
    raise NotImplementedError


def save_raster(path, array, profile):
    """
    Save raster output.
    """
    raise NotImplementedError


def build_mapbiomas_masks(mapbiomas):
    """
    Build semantic masks from MapBiomas classes.

    Returns:
        core_built
        uncertain
        vegetation
        hard_remove
    """
    raise NotImplementedError


def build_wsf_support_mask(wsf):
    """
    Convert WSF to a boolean settlement support mask.

    Since WSF behaves like a strict settlement layer, this mask should be
    conservative and high-confidence.
    """
    raise NotImplementedError


def build_ghsl_support_mask(ghsl, threshold):
    """
    Convert GHSL built-up evidence into a boolean support mask using a threshold.
    """
    raise NotImplementedError


def build_worldcover_vegetation_mask(worldcover):
    """
    Build a vegetation-like mask from WorldCover classes.

    This is used mainly to suppress vegetation spillover near favela edges.
    """
    raise NotImplementedError


def remove_small_objects(binary_mask, min_pixels):
    """
    Remove tiny isolated components.
    """
    raise NotImplementedError


def fill_small_holes(binary_mask, max_hole_pixels):
    """
    Fill small holes inside the candidate mask.
    """
    raise NotImplementedError


def compute_pixel_summary(**masks):
    """
    Print / return pixel counts for debugging and QC.
    """
    summary = {}
    for name, arr in masks.items():
        summary[name] = int(arr.sum())
    return summary


# =============================================================================
# MAIN DECISION LOGIC
# =============================================================================

def main():
    print("=" * 80)
    print("STAGE 2 — BUILD REFINED MASK")
    print("=" * 80)

    # 1. Load prepared rasters
    print("\n[1] Reading prepared AOI rasters...")
    mapbiomas, profile = read_raster(MAPBIOMAS_PATH)
    wsf, _ = read_raster(WSF_PATH)
    ghsl, _ = read_raster(GHSL_PATH)
    worldcover, _ = read_raster(WORLDCOVER_PATH)
    favela_mask, _ = read_raster(FAVELA_MASK_PATH)

    # 2. Build base semantic masks
    print("\n[2] Building semantic masks from MapBiomas...")
    core_built, uncertain, vegetation, hard_remove = build_mapbiomas_masks(mapbiomas)

    # 3. Support masks from auxiliary data
    print("\n[3] Building support masks from WSF / GHSL / WorldCover...")
    wsf_support = build_wsf_support_mask(wsf)
    ghsl_support = build_ghsl_support_mask(ghsl, threshold=GHSL_KEEP_THRESHOLD)
    wc_vegetation = build_worldcover_vegetation_mask(worldcover)

    # 4. Restrict work to favela vicinity if desired
    # Depending on the final design, refinement may happen:
    # - only inside the original favela polygons,
    # - or slightly around them if later expansion is allowed.
    print("\n[4] Restricting candidate logic to favela mask...")
    inside_favela = favela_mask.astype(bool)

    # 5. Core keep logic
    # Philosophy:
    # - always keep clear MapBiomas built
    # - keep uncertain pixels only if settlement / built-up support exists
    # - remove strong vegetation
    print("\n[5] Applying core refinement logic...")

    supported_uncertain = uncertain & (wsf_support | ghsl_support)

    candidate = (core_built | supported_uncertain) & inside_favela

    # 6. Remove pixels likely to be vegetation / non-target
    vegetation_block = vegetation | wc_vegetation | hard_remove
    refined = candidate & (~vegetation_block)

    # 7. Morphological cleanup
    print("\n[6] Cleaning refined mask...")
    refined_clean = remove_small_objects(refined, MIN_OBJECT_PIXELS)
    refined_clean = fill_small_holes(refined_clean, FILL_HOLE_PIXELS)

    # 8. Save outputs
    print("\n[7] Saving refined rasters...")
    save_raster(REFINED_DIR / "refined_mask.tif", refined.astype("uint8"), profile)
    save_raster(REFINED_DIR / "refined_mask_clean.tif", refined_clean.astype("uint8"), profile)

    # 9. Save debug summary
    print("\n[8] Saving debug pixel summary...")
    summary = compute_pixel_summary(
        core_built=core_built,
        uncertain=uncertain,
        vegetation=vegetation,
        wsf_support=wsf_support,
        ghsl_support=ghsl_support,
        wc_vegetation=wc_vegetation,
        candidate=candidate,
        refined=refined,
        refined_clean=refined_clean,
    )

    with open(REFINED_DIR / "pixel_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nPixel summary:")
    for k, v in summary.items():
        print(f"  {k}: {v:,}")

    print("\nDone: stage 2 created the refined raster mask.")


if __name__ == "__main__":
    main()