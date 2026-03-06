# ADR-0002 — GHSL product selection for label refinement

**Status:** Accepted  
**Date:** 2026-03-06  
**Decision owner:** Project team (validated with managers)  

## Context
We refine official favela polygons by intersecting them with a GHSL-derived built-up layer to remove non-built-up regions (e.g., vegetation mistakenly included in polygons).  
We need a GHSL product that:
- is suitable as a built-up proxy for urban fabric,
- aligns well with Sentinel-2 scale (10 m),
- can be used consistently across Brazil.

## Decision
We will use **GHSL built-up** with the following settings:
- **Product:** `GHS-BUILT`
- **Epoch:** `2018`
- **Resolution:** `10 m`
- **Coordinate system:** `WGS84 (EPSG:4326)`

## Rationale
- `GHS-BUILT` directly supports the label refinement objective (built-up vs non-built-up).
- `10 m` resolution is closer to Sentinel-2 10 m bands and improves boundary refinement compared to coarse (e.g., 3 arcsec) products.
- `WGS84` simplifies integration with our current vector storage CRS and tiling/indexing workflows.
- `2018` provides consistent coverage for the pilot and is a stable baseline to start the refinement pipeline.

## Implications
- GHSL data downloads will be managed as **tiles** and clipped to AOIs (pilot/state) to keep processing efficient.
- Thresholding and postprocessing parameters (τ, min component size, etc.) must be documented and tuned using QC overlays.
- When we integrate Sentinel imagery, masks will be re-aligned to the final “master grid” (likely Sentinel-2 10 m grid) per AOI.

## Alternatives considered
1) **GHSL 3 arcsec products** (coarser)  
   - Pros: smaller files, quick download  
   - Cons: too coarse for boundary refinement; loses detail around informal settlements
2) **GHS-SMOD** (settlement classes)  
   - Pros: semantically meaningful classes  
   - Cons: class-based selection may be less direct than built-up for refinement; requires careful class mapping
3) **Later epochs / projections**  
   - Rejected for now to avoid mixing observation-based labels with projected layers.

## Links / evidence
- QC overlays will be stored under: `reports/qc/overlays/`
- Threshold sensitivity notes: `docs/methods/label_refinement.md`