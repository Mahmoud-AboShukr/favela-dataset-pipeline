# Thesis Draft — Methods Chapter (Draft)

> This is a living draft that will be refined as the pipeline stabilizes and experiments are completed.

---

## 1. Problem definition
This work addresses the creation of a high-quality training dataset for automatic detection and segmentation of informal settlements (favelas) in Brazil using multi-source geospatial data. A key challenge is that available polygon labels contain noise, including regions not belonging to informal settlements (e.g., vegetation or open ground included inside polygon boundaries). Such label noise can degrade deep learning model performance and reduce generalization.

---

## 2. Data sources

### 2.1 Favela polygons
We use an official Brazilian government polygon dataset representing favela boundaries. The dataset is provided as a shapefile and contains both single polygons and multipolygon geometries. The dataset’s original CRS is EPSG:4674 (SIRGAS 2000). The polygons serve as initial labels but require refinement to reduce noise.

### 2.2 GHSL built-up layer
To refine labels, we use the Global Human Settlement Layer (GHSL) built-up product. GHSL provides an independent built-up proxy derived from remote sensing and related sources. Based on project decisions, we select:
- GHSL product: GHS-BUILT
- epoch: 2018
- resolution: 10 m
- coordinate reference: WGS84 (EPSG:4326)

### 2.3 Sentinel imagery
The final model inputs will include:
- Sentinel-2 optical imagery (L2A surface reflectance), primarily 10 m bands (B02, B03, B04, B08), with optional SWIR bands resampled to 10 m.
- Sentinel-1 SAR imagery (VV, VH) after standard preprocessing (calibration, terrain correction), resampled to the master grid.

---

## 3. Data cleaning and preprocessing

### 3.1 Polygon cleaning
The polygon dataset is cleaned to ensure robust downstream rasterization and spatial operations. Cleaning includes:
- CRS validation and conversion to a canonical storage CRS (EPSG:4326).
- removal of empty geometries,
- repair of invalid geometries,
- splitting multipolygons into single polygons,
- generation of stable identifiers for traceability:
  - `source_id` for original features,
  - `part_index` for exploded parts,
  - `favela_id = source_id_part_index` as a unique id per final polygon.

### 3.2 AOI strategy and scaling plan
We begin with a pilot region centered on Brasília to validate the workflow and to tune label refinement parameters. For scaling across Brazil, processing is organized by Brazilian state, enabling parallelization and incremental dataset construction.

---

## 4. Label refinement methodology

### 4.1 Motivation
Polygon labels may include non-built-up areas that are unlikely to represent informal settlement fabric. We refine labels by intersecting the polygon-based mask with a GHSL-based built-up mask.

### 4.2 Rasterization and refinement rule
For a given AOI:
1) polygons are rasterized onto a reference grid to produce a binary polygon mask `P(x)`,
2) GHSL values are converted into a built-up mask `B(x)` using a threshold τ,
3) the refined label is computed as:

`Y(x) = P(x) AND B(x)`

where `Y(x)` is the final binary label mask.

### 4.3 Threshold selection and postprocessing
Because GHSL encoding is product-specific, τ is selected using a QC-driven procedure:
- generate masks for candidate thresholds,
- visually inspect overlays in QGIS,
- quantify retained pixel fraction and spatial patterns,
- select τ balancing noise removal and label preservation.

Morphological cleanup removes small connected components below a minimum pixel threshold. Optional hole filling and smoothing may be applied if supported by QC evidence.

---

## 5. Tiling, alignment, and patch extraction

### 5.1 Master grid alignment
To ensure pixel-level alignment between labels and imagery, the final dataset is aligned to a master grid, planned to be Sentinel-2 10 m grid. All masks are resampled/rasterized to this grid using nearest-neighbor resampling.

### 5.2 Patch extraction
Training samples are extracted as fixed-size patches of 512×512 pixels. At 10 m resolution, each patch corresponds to approximately 5.12 km × 5.12 km. Patches are stored with metadata including AOI/state, acquisition dates, and quality indicators (e.g., cloud cover).

---

## 6. Dataset splitting and evaluation protocol
To avoid spatial leakage, train/validation/test splits must be spatially separated. Splits are defined either:
- by holding out states entirely for validation/testing, or
- by dividing each state into large spatial blocks assigned to different splits.

Performance is reported for each split and stratified by state and settlement density where relevant.

---

## 7. Reproducibility and provenance
All processing is parameterized via configuration files and documented decision records. Each dataset build records:
- input dataset filenames/versions,
- configuration used,
- outputs produced,
- QC evidence (overlay images and statistics).

This enables reproducibility and supports transparent reporting of methodological choices.

---

## 8. Limitations (initial)
- GHSL may misclassify built-up patterns depending on settlement type and sensor limitations.
- Threshold selection introduces a hyperparameter which must be justified through sensitivity analysis.
- SAR preprocessing choices (e.g., speckle filtering) can affect edge sharpness and must be validated.

> This section will be expanded once experiments and quantitative results are available.