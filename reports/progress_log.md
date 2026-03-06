# Progress Log — Favela Dataset Pipeline (Brazil)
**Project goal:** refine official favela polygons using GHSL built-up evidence to produce binary masks (0/1), then align these masks with Sentinel-1 and Sentinel-2 imagery to build a DL-ready dataset (pilot: Brasília → scale: Brazil).

---

## 0) Repository & workflow setup
We created a reproducible project structure separating:
- **raw inputs** (`data/raw`) from
- **intermediate artifacts** (`data/interim`) and
- **final dataset outputs** (`data/processed`)

Key idea: everything should be reproducible, and artifacts should be traceable from source → clean polygons → refined mask → patches.

---

## 1) Subtask 1 — Ingest & clean favela polygons (DONE ✅)

### Objective
Take the official government favela polygon shapefile and convert it into a clean, reliable vector layer suitable for downstream rasterization and spatial matching.

### Inputs
- Government shapefile bundle placed in:
  - `data/raw/favelas_shp/`
  - files: `.shp/.shx/.dbf/.prj/.cpg`

### Output files
- Clean polygons GeoPackage:
  - `data/interim/polygons_clean/favelas_clean.gpkg`
- Summary stats:
  - `data/interim/polygons_clean/favelas_clean_summary.csv`

### Script used
- `src/labels/subtask1_clean_polygons.py`

### What the cleaning script does
1) Reads the shapefile into a GeoDataFrame
2) Checks CRS exists (otherwise stops)
3) Reprojects to `EPSG:4326` (temporary storage CRS)
4) Drops empty geometries
5) Fixes invalid geometries (`make_valid` then fallback `buffer(0)`)
6) Handles MultiPolygons via `explode`
7) Creates robust IDs for traceability:
   - `source_id`: original feature id before explode
   - `part_index`: index of each piece after explode
   - `favela_id = source_id_part_index`: stable unique id per final polygon
8) Computes diagnostic area stats (projected to EPSG:3857 only for sanity checks)
9) Writes to `.gpkg`

### Key results (from run summary)
- **Input CRS:** EPSG:4674 (Brazil SIRGAS 2000)
- **Target CRS:** EPSG:4326
- **Loaded features:** 12,348
- **After explode:** 12,741 (expected increase from multipolygons)
- **Invalid geometries:** 1 → fixed to 0
- **favela_id duplicates:** 0

### Validation performed
- QGIS visual inspection of `favelas_clean.gpkg`
- Attribute table sanity checks (IDs present)
- Python inspection script checks (CRS, bounds, validity, duplicates)

---

## 2) Brasília pilot subset extraction (DONE ✅)

### Objective
Create a smaller subset of polygons around Brasília to speed up experimentation and avoid running whole-Brazil operations during early prototyping.

### Input
- `data/interim/polygons_clean/favelas_clean.gpkg` (layer: `favelas_clean`)

### Output
- `data/interim/polygons_clean/favelas_brasilia.gpkg` (layer: `favelas_brasilia`)

### Script
- `src/labels/subtask1_extract_brasilia.py`

### What it does
- Builds a rough Brasília bounding box in EPSG:4326
- Ensures the polygons are in EPSG:4326
- Uses `gpd.clip` to both select AND cut geometries to the bbox
- Writes the clipped subset to a new GeoPackage

### Result
- Extracted subset size: **105 polygons**

---

## 3) Subtask 2 — Acquire GHSL built-up raster + verify properties (DONE ✅)

### Objective
Download a GHSL raster tile that covers Brasília and inspect its metadata to ensure CRS, resolution, bounds, and value range are understood before using it for polygon refinement.

### Input
- GHSL tile downloaded to:
  - `data/raw/ghsl/brasilia.tif`

### Verification script
- `src/ghsl/inspect_ghsl.py`

### GHSL tile properties (observed)
- **CRS:** EPSG:4326
- **Resolution:** ~0.000833333° (≈ 3 arcsec, ~90m scale near Brasília)
- **Size:** 12000 × 12000 pixels
- **Bands:** 1
- **dtype:** uint16
- **nodata:** None
- **Value range:** 0 to ~8415
- **Bounds:** cover lon [-50, -40], lat [-20.9, -10.9] (Brasília is inside)

Interpretation:
- This is a coarse GHSL grid (3 arcsec), suitable for initial “built-up vs non-built-up” filtering, but not as fine as Sentinel-2 10m. It is still useful for pilot refinement logic and for removing gross vegetation / non-built-up errors.

---

## 4) GHSL clipping to Brasília bbox (DONE ✅)

### Objective
Clip the large GHSL tile to the same Brasília bbox used for polygons to make processing fast and local.

### Input
- `data/raw/ghsl/brasilia.tif`

### Output
- `data/interim/ghsl_clips/ghsl_brasilia_clip.tif`

### Script
- `src/ghsl/clip_ghsl_brasilia.py`

### Result
- Output raster shape: **(1, 721, 961)** (bands, height, width)

---

# Plan (next subtasks)

## Subtask 3 — Refine Brasília polygons using GHSL (NEXT 🔜)
**Goal:** remove non-built-up areas inside favela polygons using GHSL evidence and produce a binary raster mask (0/1).

**Approach (raster-based, preferred):**
1) Use GHSL clip raster as reference grid
2) Rasterize Brasília polygons onto that grid → `polygon_mask` (1 inside, 0 outside)
3) Threshold GHSL values into built-up mask: `builtup = (ghsl >= τ)`
4) Refined mask: `refined = polygon_mask AND builtup`
5) Post-process:
   - remove tiny components (min pixels)
   - optional hole fill / smoothing
6) Save:
   - `data/interim/masks/brasilia_polygon_mask.tif`
   - `data/interim/masks/brasilia_refined_mask.tif`
7) QC in QGIS: overlay refined mask on GHSL + basemap

## Subtask 4 — Define tiling scheme for Brasília (after Subtask 3 prototype)
**Goal:** convert the pilot to the true tile-by-tile architecture.

Deliverables:
- tile grid GeoJSON
- tile index (CSV)
- per-tile clipping of polygons and GHSL

## Subtask 5 — Sentinel-2 acquisition & preprocessing (pilot)
**Goal:** download/export S2 L2A bands, cloud filtering/compositing, align to master grid.

## Subtask 6 — Sentinel-1 preprocessing (pilot)
**Goal:** VV/VH preprocessing (calibration/terrain correction), align grid.

## Subtask 7/8 — Co-registration and patch export
**Goal:** produce DL-ready patches + metadata, with spatial train/val/test split.

## Subtask 9 — Quality control report
**Goal:** overlay samples, compute label stats and failure modes, tune thresholds and cleanup parameters.

## Subtask 10 — Automation for scaling to all Brazil
**Goal:** CLI-driven pipeline, caching, parallel tile processing, and reproducibility.

---