# Tiling and Alignment Strategy

This project is designed to scale to all Brazil while remaining reproducible and computationally feasible.

---

## 1. High-level strategy
We process data in two nested levels:

1) **Orchestration unit (scaling): Brazilian state**
- All acquisition and processing is organized state-by-state for manageability, parallelization, and reporting.

2) **Training sample unit: fixed-size patches**
- Within each state, we extract training samples as image/mask patches of:
  - **512 × 512 pixels**

---

## 2. Why “by state” processing
- Matches administrative reporting: progress and QC can be communicated per state.
- Facilitates parallel processing and incremental scaling after pilot validation.
- Makes storage organization simple (state-specific folders, logs, QC evidence).

---

## 3. Patch size
**Patch size:** 512×512 pixels

Interpretation depends on resolution:
- At 10 m: patch ≈ 5.12 km × 5.12 km
- At 20 m: patch ≈ 10.24 km × 10.24 km

We choose 512 because it provides sufficient spatial context while being GPU-friendly for segmentation.

---

## 4. “Master grid” (alignment target)
To ensure pixel-perfect alignment between imagery and masks, each processing run uses a **master grid** defined by:
- CRS
- transform (origin and pixel size)
- resolution
- extent

### Policy
- Store vectors in **EPSG:4326** (canonical storage CRS).
- For raster generation and alignment, use the **reference raster grid**:
  - GHSL grid during label refinement stage
  - Sentinel-2 10 m grid (final dataset) for model inputs and final masks

---

## 5. Alignment steps (conceptual)
For a given state (or pilot AOI):
1) Define AOI geometry (state boundary or bbox).
2) Clip GHSL tile(s) to AOI.
3) Clip/prepare Sentinel imagery for AOI.
4) Choose master grid (typically Sentinel-2 10 m).
5) Rasterize refined labels onto the master grid.
6) Verify alignment:
   - same CRS, shape, transform across all arrays.

---

## 6. Notes on CRS and metric operations
- EPSG:4326 is convenient for indexing and storage, but distances/areas are in degrees.
- Any metric threshold (area filters, buffer size) should be evaluated in a projected CRS (e.g., UTM), then mapped back to the master grid.

---

## 7. Outputs and indexing
Recommended outputs per state:
- `data/interim/tiles/` (tile grids / indexes if used)
- `data/interim/ghsl_clips/<state>.tif`
- `data/interim/masks/<state>_refined_mask.tif` (or per-tile masks)
- `data/processed/<state>/patches/`

Each patch should have metadata:
- state name/code
- patch coordinates/bounds
- acquisition date(s)
- cloud stats (S2)
- source filenames/versions