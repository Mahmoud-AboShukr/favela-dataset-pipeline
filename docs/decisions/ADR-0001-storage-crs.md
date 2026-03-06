# ADR-0001 — Storage CRS and processing CRS strategy

**Status:** Accepted  
**Date:** 2026-03-06  
**Decision owner:** Project team (validated with managers)

## Context
We combine vector labels (favela polygons) with raster products (GHSL, Sentinel-1/2).  
CRS choices affect:
- reproducibility of vector/raster alignment,
- ease of tiling/indexing,
- correctness of distance/area computations,
- performance (reprojection cost).

We need a consistent policy that works for the Brasília pilot and scales to all Brazil (state-by-state processing).

## Decision
1) **Canonical storage CRS for vector data:**  
   - Store cleaned polygon layers in **WGS84 (EPSG:4326)** as the default “exchange/storage CRS”.

2) **Processing CRS rule (per raster grid):**  
   - For rasterization, clipping, resampling, and alignment, use the **reference raster’s CRS/grid** for the current task (e.g., GHSL WGS84 grid for label refinement; Sentinel grid for final dataset generation).

3) **Metric operations (distance/area thresholds):**  
   - Any operation that requires meters (area filtering, buffer distances, component-size filters expressed in m²) should be computed in an appropriate **projected CRS**, typically derived per region/state/tile (e.g., UTM zone), then results converted back to the working grid.

## Rationale
- **EPSG:4326** is universally interoperable (QGIS, web basemaps, many datasets) and simplifies indexing by lat/lon bounds.
- Raster pipelines naturally require a **single grid** (CRS + transform + resolution). Using the raster CRS as the processing CRS prevents misalignment.
- Metric thresholds in degrees are not meaningful; projected CRS ensures correct area/distance logic.

## Implications
- Clean polygons are saved in EPSG:4326 (e.g., `favelas_clean.gpkg`, `favelas_brasilia.gpkg`).
- Each subtask must explicitly define its **reference grid**:
  - GHSL refinement uses GHSL raster grid.
  - Sentinel dataset creation will use Sentinel-2 10 m grid (or an agreed master grid).
- Documentation must record the CRS used in each stage and any reprojection steps.

## Alternatives considered
1) **Store everything in EPSG:4674 (SIRGAS 2000)**  
   - Pros: matches Brazilian official datasets  
   - Cons: less universal than EPSG:4326; still does not solve metric operations without projection

2) **Store everything in a projected CRS (e.g., UTM)**  
   - Pros: metric computations are easy  
   - Cons: Brazil spans multiple UTM zones; complicated to keep one CRS for the whole country; harder for global indexing

3) **Always reproject rasters to EPSG:4326**  
   - Pros: single CRS everywhere  
   - Cons: resampling may distort pixel geometry and complicate use of original Sentinel products; unnecessary if we can align to the source raster grid

## Links / evidence
- Clean polygons output stored in EPSG:4326:
  - `data/interim/polygons_clean/favelas_clean.gpkg`
- CRS and bounds checks performed with:
  - `src/ghsl/inspect_ghsl.py`
- Alignment notes:
  - `docs/methods/tiling_and_alignment.md`