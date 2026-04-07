# Current Brazil-Scale Favela Refinement Pipeline

## Purpose

The current active workflow is a Brazil-scale chunked pipeline designed to refine the national favela polygon layer into cleaner raster and polygon labels. The goal is to reduce expensive manual correction while preserving a final polygon-based output suitable for validation, review, and later downstream dataset construction.

This page describes the **current operational pipeline**, not the earlier archived Brasília or Manaus pilot workflows.

---

## High-level goal

The objective of the refinement stage is to improve the geometric quality of official favela polygons by combining multiple raster sources rather than relying on a single settlement or land-cover layer.

The final output remains polygon-based, but the decision process is raster-based.

The pipeline is designed to:

- preserve likely built-up favela areas,
- suppress vegetation spillover,
- keep uncertain edge pixels only when supported,
- and produce both raster and polygon outputs.

---

## Core active data sources

The current active pipeline uses the following sources:

### 1. Favela polygons
These are the main input vector labels to be refined.

### 2. MapBiomas 10 m
MapBiomas is the semantic base layer and the master grid used for alignment.

Its main roles are:

- provide the main built-up class,
- identify uncertain non-vegetated areas,
- identify vegetation classes,
- and define the reference raster grid.

### 3. GHSL EMC-BUILT 2022 10 m
GHSL is used as built-up support, especially for uncertain pixels that should only be kept when built-up evidence is present.

### 4. ESA WorldCover 2021 v200
WorldCover is used mainly as vegetation support to help suppress vegetation spillover.

---

## Source intentionally excluded from the core rule

### WSF
WSF was considered during pipeline design, but it is not part of the current core decision rule.

The main reason is temporal consistency. Since the active refinement logic is oriented around more recent label support, using an older settlement source as a mandatory keep condition would risk suppressing valid newer built-up favela extent.

WSF may still be used later for comparison or ablation, but not as a core support condition in the current operational pipeline.

---

## Why the pipeline is chunked

The workflow does not process Brazil in one single raster pass.

Instead, it:

1. loads the national favela layer,
2. builds a regular chunk grid over the favela extent,
3. keeps only chunks that intersect favela polygons,
4. processes each chunk independently.

This design was chosen because a single Brazil-wide raster pass would be unnecessarily heavy, harder to debug, and harder to rerun selectively.

Chunking allows:

- local raster loading only where needed,
- cleaner debugging,
- easier reruns,
- and scalable execution across the country.

In the current national run, the pipeline produced **407 active chunks**.

---

## Pipeline stages

The active workflow is implemented under:

`src/final_pipeline_scale_up/src`

and consists of four main stages:

1. `1_prepare_inputs.py`
2. `2_build_refined_mask.py`
3. `3_polygonize_and_qc.py`
4. `4_merge_brazil_polygons.py`

---

## Stage 1 — Prepare inputs

### Purpose
Prepare harmonized per-chunk raster and vector inputs.

### Main operations
For each active chunk, the script:

- selects the local favela subset,
- finds intersecting raster tiles,
- clips MapBiomas, GHSL, and WorldCover to the local processing geometry,
- keeps MapBiomas as the master grid,
- aligns GHSL and WorldCover to the MapBiomas grid,
- rasterizes local favela polygons.

### Outputs
Each chunk receives:

- `prepared/mapbiomas.tif`
- `prepared/ghsl.tif`
- `prepared/worldcover.tif`
- `prepared/favela_mask.tif`
- `prepared/favelas.gpkg`
- `prepared/chunk_geom.gpkg`
- `prepared/metadata.json`

---

## Stage 2 — Build refined mask

### Purpose
Apply the raster refinement rule.

### Core logic
For each chunk, the script:

- keeps MapBiomas class 24 (`Urban Area`),
- treats class 25 (`Other Non Vegetated Areas`) as uncertain,
- keeps uncertain pixels only when GHSL support is above threshold,
- removes vegetation classes from MapBiomas,
- removes vegetation and water-like classes from WorldCover,
- restricts the result to the favela mask,
- removes very small isolated objects,
- fills very small holes.

### Main parameters used in the national run
- GHSL threshold = `20.0`
- minimum object size = `9` pixels
- maximum hole-fill size = `9` pixels

### Outputs
Each chunk receives:

- `refined/refined_mask.tif`
- `refined/refined_mask_clean.tif`
- `refined/pixel_summary.json`

---

## Stage 3 — Polygonize and QC

### Purpose
Convert the cleaned refined raster into polygon outputs and compute basic QC summaries.

### Main operations
For each chunk, the script:

- polygonizes the cleaned refined mask,
- generates raw polygons,
- assigns each raw polygon to the source favela polygon with the largest overlap,
- dissolves polygons by source ID,
- clips outputs to the chunk geometry,
- computes simple QC metrics.

### Outputs
Each chunk receives:

- `polygonized/refined_raw.gpkg`
- `polygonized/refined_dissolved.gpkg`
- `polygonized/qc_metrics.json`
- `polygonized/qc_metrics.csv`

---

## Stage 4 — Merge Brazil polygons

### Purpose
Merge chunk-level polygon outputs into Brazil-wide outputs.

### Outputs
The merged outputs are:

- `data/processed/final_pipeline_scale_up/brazil_refined_raw.gpkg`
- `data/processed/final_pipeline_scale_up/brazil_refined_dissolved.gpkg`

This stage concatenates chunk-level outputs into national layers. At this point, chunk-boundary deduplication is a later refinement task rather than part of the first merge step.

---

## Output philosophy

The pipeline intentionally preserves both:

### Raster outputs
These preserve the exact per-pixel refinement result and are useful for debugging and reproducibility.

### Polygon outputs
These remain the main final deliverable because manual review and later label correction are easier in polygon form.

---

## Current strengths

The current pipeline has the following strengths:

- modular structure,
- chunk-based national scalability,
- semantic control through MapBiomas,
- built-up support from GHSL 2022,
- vegetation suppression through WorldCover,
- preservation of both raster and polygon outputs,
- clear end-to-end national execution.

---

## Current limitations

The pipeline is operational, but several tasks remain:

- representative visual validation in QGIS,
- national QC aggregation across chunks,
- chunk-boundary consistency checks,
- optional industrial-area veto using OSM,
- preparation for satellite-image processing.

---

## Current status

The active Brazil-scale run has already completed:

- Stage 1 on all active chunks,
- Stage 2 on all active chunks,
- Stage 3 on all active chunks,

with a total of **407 processed chunks**.

The pipeline is therefore now operational at national scale and serves as the main refinement workflow for the project.