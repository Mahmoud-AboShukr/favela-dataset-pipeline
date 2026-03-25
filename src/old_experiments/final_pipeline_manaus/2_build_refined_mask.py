#!/usr/bin/env python3
"""
src/final_pipeline/2_build_refined_mask.py

Build a refined favela raster mask for Manaus by combining:
- MapBiomas 10 m (base built / vegetation / uncertain candidate logic)
- WSF 2019 (strict settlement confirmation; binarized 255->1, 0->0)
- GHSL EMC-BUILT (broader built-up support)
- ESA WorldCover 2021 (vegetation support)
- Favela raster mask (limit processing to favela footprint)

Outputs are written to:
data/processed/final_pipeline/manaus/refined/

Main idea
---------
1. Derive MapBiomas-based:
   - core_built
   - vegetation_clear
   - uncertain_candidates
2. Build support layers:
   - wsf_support
   - ghsl_support
   - settlement_support_combined
   - worldcover_vegetation_support
3. Accept uncertain pixels only when they:
   - lie inside favela_mask
   - are connected to the built core
   - have enough settlement support
   - are not strongly vegetation-like
4. Write intermediates + final mask.

IMPORTANT
---------
You MUST review the MapBiomas class lists below against your actual product legend.
The defaults are intentionally conservative placeholders.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import rasterio
from rasterio.enums import Resampling
from scipy import ndimage as ndi


# =============================================================================
# CONFIG
# =============================================================================

CITY = "manaus"

BASE_DIR = Path("data/processed/final_pipeline") / CITY
PREPARED_DIR = BASE_DIR / "prepared"
OUT_DIR = BASE_DIR / "refined"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MAPBIOMAS_PATH = PREPARED_DIR / "mapbiomas_10m_manaus.tif"
WSF_PATH = PREPARED_DIR / "wsf_manaus.tif"
GHSL_PATH = PREPARED_DIR / "ghsl_manaus.tif"
WORLDCOVER_PATH = PREPARED_DIR / "worldcover_manaus.tif"
FAVELA_MASK_PATH = PREPARED_DIR / "favela_mask.tif"

# -----------------------------
# REVIEW THESE CLASS SETS
# -----------------------------
# These are placeholders and should be adapted to the actual MapBiomas 10 m product used.
# The script prints unique values to help inspection.
MAPBIOMAS_BUILT_CLASSES = {
    24,  # urban infrastructure / urban area in many legends
}

MAPBIOMAS_VEGETATION_CLASSES = {
    1,   # forest / natural vegetation (placeholder)
    3,   # forest formation (placeholder)
    4,   # savanna formation (placeholder)
    5,   # mangrove / woody veg (placeholder)
    6,   # flooded forest / wet veg (placeholder)
    49,  # wooded sandbank vegetation in some legends (placeholder)
    10,  # grassland (placeholder)
    11,  # wetland (placeholder)
    12,  # shrubland / non-forest natural formation (placeholder)
    13,  # other natural non-forest (placeholder)
}

# Optional: water if you want to force-reject it
MAPBIOMAS_WATER_CLASSES = {
    33,  # water (common in some legends)
}

# WorldCover v200 classes
WORLDCOVER_VEGETATION_CLASSES = {
    10,  # Tree cover
    20,  # Shrubland
    30,  # Grassland
    40,  # Cropland
    90,  # Herbaceous wetland
    95,  # Mangroves
    100, # Moss and lichen
}
WORLDCOVER_WATER_CLASSES = {80}
WORLDCOVER_BUILT_CLASS = 50

# GHSL support threshold:
# start conservative but not too strict; adjust after inspecting value distribution.
GHSL_BUILT_THRESHOLD = 10

# Support rules
MIN_SETTLEMENT_SUPPORT_TO_ACCEPT = 1   # 0,1,2 where 2 means WSF+GHSL
REJECT_IF_STRONG_VEGETATION = True
USE_WORLDCOVER_BUILT_AS_EXTRA_SUPPORT = True

# Connectivity rule:
# uncertain pixels are accepted only if connected to a dilated core.
CORE_CONNECTIVITY_DILATION_ITERS = 2   # 10 m pixels -> 20 m reach
MORPH_OPEN_ITERS = 0
MORPH_CLOSE_ITERS = 1
MIN_COMPONENT_PIXELS = 4

# Review zones:
# ambiguous areas = uncertain + connected + some conflict
WRITE_REVIEW_ZONES = True

NODATA_OUT = 0


# =============================================================================
# IO HELPERS
# =============================================================================

def read_raster(path: Path) -> Tuple[np.ndarray, Dict]:
    with rasterio.open(path) as src:
        arr = src.read(1)
        profile = src.profile.copy()
    return arr, profile


def write_u8(path: Path, arr: np.ndarray, profile: Dict) -> None:
    out_profile = profile.copy()
    out_profile.update(
        dtype=rasterio.uint8,
        count=1,
        compress="lzw",
        nodata=NODATA_OUT,
    )
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(arr.astype(np.uint8), 1)


def write_u16(path: Path, arr: np.ndarray, profile: Dict) -> None:
    out_profile = profile.copy()
    out_profile.update(
        dtype=rasterio.uint16,
        count=1,
        compress="lzw",
        nodata=0,
    )
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(arr.astype(np.uint16), 1)


def check_same_grid(profiles: Dict[str, Dict]) -> None:
    keys = list(profiles.keys())
    ref = profiles[keys[0]]
    for k in keys[1:]:
        p = profiles[k]
        assert p["crs"] == ref["crs"], f"CRS mismatch: {k}"
        assert p["width"] == ref["width"], f"Width mismatch: {k}"
        assert p["height"] == ref["height"], f"Height mismatch: {k}"
        assert p["transform"] == ref["transform"], f"Transform mismatch: {k}"


# =============================================================================
# MASK HELPERS
# =============================================================================

def to_binary(arr: np.ndarray) -> np.ndarray:
    return (arr > 0).astype(np.uint8)


def remove_small_components(mask: np.ndarray, min_pixels: int) -> np.ndarray:
    if min_pixels <= 1:
        return mask.astype(np.uint8)

    labeled, num = ndi.label(mask)
    if num == 0:
        return mask.astype(np.uint8)

    counts = np.bincount(labeled.ravel())
    keep = counts >= min_pixels
    keep[0] = False
    out = keep[labeled]
    return out.astype(np.uint8)


def binary_open_close(mask: np.ndarray, open_iters: int = 0, close_iters: int = 0) -> np.ndarray:
    s = ndi.generate_binary_structure(2, 2)
    out = mask.astype(bool)

    if open_iters > 0:
        out = ndi.binary_opening(out, structure=s, iterations=open_iters)
    if close_iters > 0:
        out = ndi.binary_closing(out, structure=s, iterations=close_iters)

    return out.astype(np.uint8)


def dilate(mask: np.ndarray, iters: int) -> np.ndarray:
    if iters <= 0:
        return mask.astype(np.uint8)
    s = ndi.generate_binary_structure(2, 2)
    return ndi.binary_dilation(mask.astype(bool), structure=s, iterations=iters).astype(np.uint8)


def connected_to_core(candidates: np.ndarray, core: np.ndarray) -> np.ndarray:
    """
    Keep only candidate pixels that belong to components touching the core.
    """
    cand = candidates.astype(bool)
    core_bool = core.astype(bool)

    labeled, num = ndi.label(cand)
    if num == 0:
        return np.zeros_like(candidates, dtype=np.uint8)

    touching_labels = np.unique(labeled[core_bool & cand])
    touching_labels = touching_labels[touching_labels != 0]
    if len(touching_labels) == 0:
        return np.zeros_like(candidates, dtype=np.uint8)

    keep = np.isin(labeled, touching_labels)
    return keep.astype(np.uint8)


# =============================================================================
# MAIN LOGIC
# =============================================================================

def main() -> None:
    print("=" * 80)
    print("LOADING PREPARED INPUTS")
    print("=" * 80)

    mapb, mapb_profile = read_raster(MAPBIOMAS_PATH)
    wsf, wsf_profile = read_raster(WSF_PATH)
    ghsl, ghsl_profile = read_raster(GHSL_PATH)
    wc, wc_profile = read_raster(WORLDCOVER_PATH)
    favela_mask, favela_profile = read_raster(FAVELA_MASK_PATH)

    check_same_grid({
        "mapbiomas": mapb_profile,
        "wsf": wsf_profile,
        "ghsl": ghsl_profile,
        "worldcover": wc_profile,
        "favela_mask": favela_profile,
    })

    favela_mask_bin = to_binary(favela_mask)

    print(f"MapBiomas unique sample: {np.unique(mapb)[:50]}")
    print(f"WSF unique values: {np.unique(wsf)}")
    print(f"GHSL min/max: {np.nanmin(ghsl)} / {np.nanmax(ghsl)}")
    print(f"WorldCover unique values: {np.unique(wc)}")

    print("\n" + "=" * 80)
    print("DERIVING MAPBIOMAS MASKS")
    print("=" * 80)

    core_built = np.isin(mapb, list(MAPBIOMAS_BUILT_CLASSES)).astype(np.uint8)
    vegetation_clear = np.isin(mapb, list(MAPBIOMAS_VEGETATION_CLASSES)).astype(np.uint8)
    water_clear = np.isin(mapb, list(MAPBIOMAS_WATER_CLASSES)).astype(np.uint8)

    # uncertain = inside favela footprint but not clear built and not clear vegetation/water
    uncertain_candidates = (
        (favela_mask_bin == 1) &
        (core_built == 0) &
        (vegetation_clear == 0) &
        (water_clear == 0)
    ).astype(np.uint8)

    # restrict core to favela footprint for conservative behavior
    core_built = ((core_built == 1) & (favela_mask_bin == 1)).astype(np.uint8)

    print(f"core_built pixels: {int(core_built.sum())}")
    print(f"uncertain_candidates pixels: {int(uncertain_candidates.sum())}")
    print(f"vegetation_clear pixels: {int(vegetation_clear.sum())}")

    print("\n" + "=" * 80)
    print("DERIVING SUPPORT LAYERS")
    print("=" * 80)

    # WSF: MUST be binarized explicitly
    wsf_support = (wsf == 255).astype(np.uint8)

    # GHSL support
    # nodata handling: if ghsl was clipped/reprojected cleanly, nodata should already be managed
    ghsl_support = (ghsl >= GHSL_BUILT_THRESHOLD).astype(np.uint8)

    # WorldCover vegetation
    worldcover_vegetation_support = np.isin(wc, list(WORLDCOVER_VEGETATION_CLASSES)).astype(np.uint8)
    worldcover_water_support = np.isin(wc, list(WORLDCOVER_WATER_CLASSES)).astype(np.uint8)
    worldcover_built_support = (wc == WORLDCOVER_BUILT_CLASS).astype(np.uint8)

    settlement_support_combined = (wsf_support + ghsl_support).astype(np.uint8)

    if USE_WORLDCOVER_BUILT_AS_EXTRA_SUPPORT:
        settlement_support_combined = np.clip(
            settlement_support_combined + worldcover_built_support,
            0,
            2
        ).astype(np.uint8)

    print(f"wsf_support pixels: {int(wsf_support.sum())}")
    print(f"ghsl_support pixels: {int(ghsl_support.sum())}")
    print(f"worldcover_vegetation_support pixels: {int(worldcover_vegetation_support.sum())}")

    print("\n" + "=" * 80)
    print("APPLYING CONNECTIVITY + SUPPORT RULES")
    print("=" * 80)

    core_for_connectivity = dilate(core_built, CORE_CONNECTIVITY_DILATION_ITERS)
    connected_uncertain = connected_to_core(uncertain_candidates, core_for_connectivity)

    support_ok = (settlement_support_combined >= MIN_SETTLEMENT_SUPPORT_TO_ACCEPT).astype(np.uint8)

    strong_vegetation = (
        (vegetation_clear == 1) |
        (worldcover_vegetation_support == 1) |
        (worldcover_water_support == 1) |
        (water_clear == 1)
    ).astype(np.uint8)

    uncertain_accepted = (
        (uncertain_candidates == 1) &
        (connected_uncertain == 1) &
        (support_ok == 1)
    )

    if REJECT_IF_STRONG_VEGETATION:
        uncertain_accepted = uncertain_accepted & (strong_vegetation == 0)

    uncertain_accepted = uncertain_accepted.astype(np.uint8)
    uncertain_accepted = binary_open_close(
        uncertain_accepted,
        open_iters=MORPH_OPEN_ITERS,
        close_iters=MORPH_CLOSE_ITERS
    )
    uncertain_accepted = remove_small_components(uncertain_accepted, MIN_COMPONENT_PIXELS)

    uncertain_rejected = (
        (uncertain_candidates == 1) &
        (uncertain_accepted == 0)
    ).astype(np.uint8)

    # Optional review zones:
    # connected uncertain pixels that have some settlement support but are also vegetation-like
    if WRITE_REVIEW_ZONES:
        review_zones = (
            (uncertain_candidates == 1) &
            (connected_uncertain == 1) &
            (settlement_support_combined >= 1) &
            (strong_vegetation == 1)
        ).astype(np.uint8)
    else:
        review_zones = np.zeros_like(uncertain_candidates, dtype=np.uint8)

    favela_refined_final = (
        (core_built == 1) | (uncertain_accepted == 1)
    ).astype(np.uint8)

    # Final restriction to original favela footprint
    favela_refined_final = (
        (favela_refined_final == 1) &
        (favela_mask_bin == 1)
    ).astype(np.uint8)

    print(f"connected_uncertain pixels: {int(connected_uncertain.sum())}")
    print(f"uncertain_accepted pixels: {int(uncertain_accepted.sum())}")
    print(f"uncertain_rejected pixels: {int(uncertain_rejected.sum())}")
    print(f"review_zones pixels: {int(review_zones.sum())}")
    print(f"favela_refined_final pixels: {int(favela_refined_final.sum())}")

    print("\n" + "=" * 80)
    print("WRITING OUTPUTS")
    print("=" * 80)

    write_u8(OUT_DIR / "core_built.tif", core_built, mapb_profile)
    write_u8(OUT_DIR / "vegetation_clear_mapbiomas.tif", vegetation_clear, mapb_profile)
    write_u8(OUT_DIR / "uncertain_candidates.tif", uncertain_candidates, mapb_profile)
    write_u8(OUT_DIR / "wsf_support.tif", wsf_support, mapb_profile)
    write_u8(OUT_DIR / "ghsl_support.tif", ghsl_support, mapb_profile)
    write_u8(OUT_DIR / "worldcover_vegetation_support.tif", worldcover_vegetation_support, mapb_profile)
    write_u8(OUT_DIR / "settlement_support_combined.tif", settlement_support_combined, mapb_profile)
    write_u8(OUT_DIR / "connected_uncertain.tif", connected_uncertain, mapb_profile)
    write_u8(OUT_DIR / "uncertain_accepted.tif", uncertain_accepted, mapb_profile)
    write_u8(OUT_DIR / "uncertain_rejected.tif", uncertain_rejected, mapb_profile)
    write_u8(OUT_DIR / "review_zones.tif", review_zones, mapb_profile)
    write_u8(OUT_DIR / "favela_refined_final.tif", favela_refined_final, mapb_profile)

    pixel_area_m2 = abs(mapb_profile["transform"].a * mapb_profile["transform"].e)
    summary = {
        "city": CITY,
        "inputs": {
            "mapbiomas": str(MAPBIOMAS_PATH),
            "wsf": str(WSF_PATH),
            "ghsl": str(GHSL_PATH),
            "worldcover": str(WORLDCOVER_PATH),
            "favela_mask": str(FAVELA_MASK_PATH),
        },
        "parameters": {
            "mapbiomas_built_classes": sorted(list(MAPBIOMAS_BUILT_CLASSES)),
            "mapbiomas_vegetation_classes": sorted(list(MAPBIOMAS_VEGETATION_CLASSES)),
            "mapbiomas_water_classes": sorted(list(MAPBIOMAS_WATER_CLASSES)),
            "worldcover_vegetation_classes": sorted(list(WORLDCOVER_VEGETATION_CLASSES)),
            "worldcover_water_classes": sorted(list(WORLDCOVER_WATER_CLASSES)),
            "worldcover_built_class": WORLDCOVER_BUILT_CLASS,
            "ghsl_built_threshold": GHSL_BUILT_THRESHOLD,
            "min_settlement_support_to_accept": MIN_SETTLEMENT_SUPPORT_TO_ACCEPT,
            "core_connectivity_dilation_iters": CORE_CONNECTIVITY_DILATION_ITERS,
            "morph_open_iters": MORPH_OPEN_ITERS,
            "morph_close_iters": MORPH_CLOSE_ITERS,
            "min_component_pixels": MIN_COMPONENT_PIXELS,
            "reject_if_strong_vegetation": REJECT_IF_STRONG_VEGETATION,
            "use_worldcover_built_as_extra_support": USE_WORLDCOVER_BUILT_AS_EXTRA_SUPPORT,
        },
        "counts": {
            "favela_mask_pixels": int(favela_mask_bin.sum()),
            "core_built_pixels": int(core_built.sum()),
            "uncertain_candidates_pixels": int(uncertain_candidates.sum()),
            "connected_uncertain_pixels": int(connected_uncertain.sum()),
            "uncertain_accepted_pixels": int(uncertain_accepted.sum()),
            "uncertain_rejected_pixels": int(uncertain_rejected.sum()),
            "review_zones_pixels": int(review_zones.sum()),
            "final_refined_pixels": int(favela_refined_final.sum()),
        },
        "areas_m2": {
            "favela_mask_area_m2": float(favela_mask_bin.sum() * pixel_area_m2),
            "core_built_area_m2": float(core_built.sum() * pixel_area_m2),
            "uncertain_candidates_area_m2": float(uncertain_candidates.sum() * pixel_area_m2),
            "uncertain_accepted_area_m2": float(uncertain_accepted.sum() * pixel_area_m2),
            "uncertain_rejected_area_m2": float(uncertain_rejected.sum() * pixel_area_m2),
            "review_zones_area_m2": float(review_zones.sum() * pixel_area_m2),
            "final_refined_area_m2": float(favela_refined_final.sum() * pixel_area_m2),
        }
    }

    with open(OUT_DIR / "refined_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nDone.")
    print(f"Outputs written to: {OUT_DIR}")


if __name__ == "__main__":
    main()