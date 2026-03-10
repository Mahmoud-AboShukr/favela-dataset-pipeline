# ADR-0006 — Settlement mask definition from GHSL (pilot)

**Status:** Proposed (pilot tuning in progress)  
**Date:** 2026-03-09  

## Context
We need an AOI-wide settlement/built-up mask to constrain favela labels and reduce vegetation/non-built-up false positives.

## Decision (current pilot configuration)
We generate a binary settlement mask from GHSL built-up (GHS-BUILT, 2018, 10 m, ESRI:54009) by:
1) Valid pixels: ghsl != nodata (255)
2) Built-up: ghsl >= THRESHOLD
3) Morphology: closing(disk=CLOSE_RADIUS) → fill holes → remove small objects(min_size=MIN_PIXELS)

Current pilot parameters:
- THRESHOLD=5
- CLOSE_RADIUS=5
- MIN_PIXELS=50

## Evidence
Current built-up ratio on valid pixels after post-processing ≈ 0.10 (10%).

## Open issue
Visual QC indicates false negatives (missed settlement areas). A threshold sweep and pixel value probes will be conducted to decide whether to:
- lower threshold (e.g., 1–3),
- adjust morphology,
- or use an alternative GHSL layer (e.g., SMOD) as an auxiliary settlement definition.

## Consequences
Until resolved, the settlement mask should be treated as an *experimental prior* and not as a final authoritative settlement extent layer.