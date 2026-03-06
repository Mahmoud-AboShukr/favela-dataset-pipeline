# Data Sources

This project combines official vector labels (favela polygons) with global built-up proxies (GHSL) and satellite imagery (Sentinel-1/2). The goal is to produce a refined, DL-ready segmentation dataset.

---

## 1. Favela polygons (Brazilian government dataset)

### Description
A national vector dataset of favela (informal settlement) boundaries provided as a shapefile. The dataset is used as the *starting point* for label generation.

### Format
- Shapefile bundle (`.shp`, `.shx`, `.dbf`, `.prj`, optionally `.cpg`)
- Loaded and processed using GeoPandas.

### Known issues (motivation for refinement)
- Some polygons include surrounding non-favela areas (e.g., vegetation or open land).
- MultiPolygon geometries occur (one record can contain multiple disconnected parts).
- Occasional invalid geometry (self-intersections, topology errors).

### Pipeline outputs
- Cleaned national layer:
  - `data/interim/polygons_clean/favelas_clean.gpkg`
- Pilot subset (Brasília):
  - `data/interim/polygons_clean/favelas_brasilia.gpkg`

---

## 2. GHSL built-up layer (label refinement proxy)

### Selected product and settings (confirmed decision)
We use GHSL built-up for label refinement with:
- Product: **GHS-BUILT**
- Epoch: **2018**
- Resolution: **10 m**
- Coordinate system: **WGS84 (EPSG:4326)**

### Why GHSL
GHSL provides an independent built-up proxy which helps reduce label noise in polygons by removing areas that are not supported as built-up.

### Pipeline outputs
- Raw GHSL tiles:
  - `data/raw/ghsl/`
- AOI clips (pilot/state):
  - `data/interim/ghsl_clips/`

---

## 3. Sentinel-2 imagery (optical)

### Purpose
Sentinel-2 provides multi-spectral optical imagery used as model input for segmentation.

### Expected usage (final dataset grid)
- Target resolution: **10 m**
- Typical 10 m bands: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)
- Optional 20 m bands: B11, B12 (SWIR) resampled to 10 m

### Raw and processed storage
- Raw exports:
  - `data/raw/sentinel/s2/`
- Aligned stacks / processed outputs:
  - `data/processed/...`

---

## 4. Sentinel-1 imagery (SAR)

### Purpose
Sentinel-1 SAR complements optical data (cloud-robust) and improves detection in complex urban contexts.

### Typical inputs
- Polarizations: VV, VH
- Derived features (optional): VV/VH ratio, texture features

### Raw and processed storage
- Raw exports:
  - `data/raw/sentinel/s1/`
- Aligned stacks / processed outputs:
  - `data/processed/...`

---

## 5. Pilot AOI and scaling
- **Pilot AOI:** Brasília (used to validate refinement logic and QC workflows).
- **Scaling:** processing organized **by Brazilian state**, with patches extracted at **512×512** pixels.

---

## 6. Provenance tracking (recommended)
For each dataset build, record:
- input dataset filenames/versions (polygons, GHSL, Sentinel)
- configuration file used (`config/config.yaml` and any `config/experiments/*.yaml`)
- code version/commit (once git is used)
- output paths and QC evidence

QC overlays and statistics should be stored in:
- `reports/qc/overlays/`
- `reports/qc/stats/`