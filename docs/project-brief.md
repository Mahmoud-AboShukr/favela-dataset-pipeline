# Project Brief — Favela Dataset Pipeline (Brazil)

## Goal
Build a Deep Learning–ready dataset for favela detection by:
1) cleaning the official Brazilian favela polygons,
2) refining labels using GHSL built-up evidence (remove vegetation / non-built-up areas),
3) generating binary masks (0 = non-favela, 1 = favela),
4) aligning masks with Sentinel-2 (optical) and Sentinel-1 (SAR) imagery.

We start with a **Brasília pilot** before scaling to all Brazil.

---

## Current status (as of today)
### Completed ✅
**Subtask 1 — Clean polygons (Brazil-wide)**
- Input CRS: EPSG:4674 (SIRGAS 2000)
- Stored CRS: EPSG:4326
- Loaded features: 12,348
- After multipolygon explode: 12,741
- Invalid geometries fixed: 1 → 0
- Unique IDs created: `source_id`, `part_index`, `favela_id` (no duplicates)

Outputs:
- `data/interim/polygons_clean/favelas_clean.gpkg`
- `data/interim/polygons_clean/favelas_clean_summary.csv`

**Brasília subset extraction**
- Created bbox subset of cleaned polygons
- Extracted: 105 polygons

Outputs:
- `data/interim/polygons_clean/favelas_brasilia.gpkg`

**Subtask 2 — GHSL acquisition + verification**
- Downloaded GHSL tile that covers Brasília
- Verified raster properties:
  - CRS: EPSG:4326
  - Resolution: ~0.000833333° (3 arcsec)
  - dtype: uint16
  - value range: 0..~8415

Output:
- `data/raw/ghsl/brasilia.tif`

**GHSL clip to Brasília bbox**
- Clipped GHSL tile for fast iteration

Output:
- `data/interim/ghsl_clips/ghsl_brasilia_clip.tif` (shape ~721×961)

---

### Notes / lessons learned (GHSL download)
- **Initial GHSL tile mismatch:** the first downloaded GHSL GeoTIFF did not overlap the Brasília bbox, which caused clipping to fail with: *“Input shapes do not overlap raster.”*
- **Fix applied:** downloaded the correct GHSL tile covering Brasília (lon ≈ -48, lat ≈ -16). Updated the clipping workflow to validate bbox–raster overlap before clipping.
- **Current GHSL files used:**
  - Full tile: `data/raw/ghsl/brasilia.tif` (EPSG:4326, ~3 arcsec, uint16, value range ~0..8415)
  - Brasília clip: `data/interim/ghsl_clips/ghsl_brasilia_clip.tif` (shape ~721×961)

## Next steps (planned)
### Next 🔜
**Subtask 3 — Refine Brasília polygons using GHSL**
- Rasterize Brasília polygons to GHSL grid
- Apply rule: `refined = polygon_mask AND (ghsl >= τ)`
- Postprocess (remove small blobs)
- Produce refined masks and QC overlays

### Subtask 3 (next) — Brasília label refinement prototype
- Rasterize Brasília polygons onto the GHSL clipped grid
- Apply refinement rule: `refined = polygon_mask AND (ghsl >= τ)`
- Postprocess: remove small connected components (min pixels), optional hole filling if needed
- QC in QGIS: overlay refined mask on GHSL and basemap; export 2–5 screenshots to `reports/qc/overlays/`

Deliverables:
- `data/interim/masks/brasilia_polygon_mask.tif`
- `data/interim/masks/brasilia_refined_mask.tif`
- QC overlays in `reports/qc/overlays/`

### Decisions confirmed with managers
- **GHSL for label refinement:** GHS-BUILT, Epoch 2018, 10 m, WGS84
- **Scaling strategy:** processing organized **by state**, with DL patch size **512×512**


### After Subtask 3
- Subtask 4: Brasília tiling system (tile index, per-tile processing)
- Subtask 5: Sentinel-2 acquisition & preprocessing
- Subtask 6: Sentinel-1 preprocessing
- Subtask 7/8: alignment + patch export
- Subtask 9: QC report + threshold sensitivity
- Subtask 10: scale to all Brazil

---

## Risks / uncertainties
- GHSL resolution (3 arcsec ~90 m) is coarse compared to Sentinel-2 10 m; refinement will remove gross errors but may not perfectly sharpen boundaries.
- Threshold selection (τ) needs tuning using QC overlays and pixel statistics.
- Final “master grid” CRS/resolution should follow Sentinel exports and supervisor guidance.

---

## Evidence / references
- Clean polygons summary CSV: `data/interim/polygons_clean/favelas_clean_summary.csv`
- GHSL inspection output: run `python src/ghsl/inspect_ghsl.py`