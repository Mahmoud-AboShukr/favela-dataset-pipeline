# 2026-03-09 — Brasília Pilot: GHSL settlement mask (status & issues)

## What we built today (pipeline state)
**Goal:** Produce a city-wide (AOI-wide) built-up/settlement mask from GHSL to support later favela label refinement.

### AOI definition (pilot)
- AOI source: **OSM administrative boundary (Distrito Federal)**
- File: `data/interim/aoi/brasilia_boundary.gpkg` (layer: `brasilia_boundary`)
- AOI generation script: `src/osm/get_brasilia_boundary.py`

### Favela polygons (pilot)
- Cleaned polygons: `data/interim/polygons_clean/favelas_clean.gpkg`
- Brasília subset (clipped to AOI): `data/interim/polygons_clean/favelas_brasilia.gpkg`
- Extraction script: `src/labels/subtask1_extract_brasilia.py`

### GHSL (pilot)
- Raw tile used: `data/raw/ghsl/Brasilia.tif` (10 m, ESRI:54009, nodata=255, values 0..100)
- AOI-clipped GHSL: `data/interim/ghsl_clips/ghsl_brasilia_aoi_clip.tif`
- Clipping script: `src/ghsl/clip_ghsl_to_aoi_osm.py`
- Inspection script: `src/ghsl/inspect_ghsl.py`

### Settlement mask (pilot)
- Output mask: `data/interim/masks/brasilia_settlement_mask.tif`
- Script: `src/ghsl/make_brasilia_settlement_mask.py`
- Current parameters:
  - THRESHOLD = 5
  - CLOSE_RADIUS = 5
  - MIN_PIXELS = 50

## QC results (current)
- GHSL clip: CRS ESRI:54009, resolution 10 m, nodata 255.
- Settlement mask is binary (uint8) with unique values {0,1}.
- Built-up coverage (on valid pixels):
  - valid_pixels: 58,146,865
  - pixels_on_raw: 4,309,217 (ratio 0.0741)
  - pixels_on_final: 5,790,039 (ratio 0.0996)
  - Interpretation: morphology expands/connects built-up (~7.4% → ~10.0%).

## Issue observed (to resolve later)
**Observation:** Visual QC suggests some settlement/urban areas remain unmasked (false negatives), even with THRESHOLD=5 and smoothing.
**Hypotheses:**
1) GHSL built-up values in some settlement areas are < 5 (threshold too strict for our definition of “settlement extent”).
2) GHSL built-up at 10 m is patchy for certain urban textures; may require different GHSL product or additional post-processing.
3) Some areas may be nodata (255), which cannot be recovered through thresholding.

## Next steps (planned)
1) Value probe at missed locations (QGIS identify tool):
   - check whether missed pixels are nodata (255) or low-value (<5).
2) Threshold sweep experiment:
   - generate masks for thresholds {1, 3, 5, 8} with fixed morphology.
   - compare coverage ratios + visual overlays.
3) Consider GHSL SMOD (settlement model) as an alternative/auxiliary layer if built-up remains insufficient.
4) Once settlement mask is acceptable:
   - Subtask 3: refine favela masks = polygon_mask AND settlement_mask, then hole-fill/closing inside polygons.