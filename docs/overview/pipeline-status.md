# Pipeline Status

## Purpose

This page summarizes the current status of the favela-refinement pipeline.

It is intended as a practical status snapshot of what has been completed, what is active, and what remains to be done before the next project phase.

---

## Current active workflow

The active workflow is the Brazil-scale chunked refinement pipeline located under:

`src/final_pipeline_scale_up/`

This is the current main implementation of the project.

It has replaced the older pilot-centric workflows as the main operational line.

---

## What has already been completed

## 1. Historical pilot phases completed
The project has already gone through several important earlier phases:

- Brasília GHSL pilot,
- MapBiomas-only experiments,
- Manaus pilot,
- multi-city MapBiomas 10 m experiments.

These are now archived conceptually and structurally, but their lessons were absorbed into the current workflow.

---

## 2. Brazil-scale raw data preparation completed
The required Brazil-scale raw inputs were collected and organized for the active pipeline, including:

- MapBiomas,
- GHSL,
- WorldCover,
- favela polygons.

The raw-data organization is now sufficient for the active refinement workflow.

---

## 3. Stage 1 completed
`1_prepare_inputs.py` was implemented and executed successfully at national scale.

This stage:

- built the chunk structure,
- aligned raster inputs,
- prepared per-chunk data,
- and rasterized the local favela masks.

---

## 4. Stage 2 completed
`2_build_refined_mask.py` was implemented and executed successfully at national scale.

This stage:

- applied the active refinement logic,
- created per-chunk refined raster masks,
- and saved per-chunk raster summaries.

---

## 5. Stage 3 completed
`3_polygonize_and_qc.py` was implemented and executed successfully at national scale.

This stage:

- polygonized refined chunk masks,
- generated raw and dissolved polygon outputs,
- and produced per-chunk QC metrics.

---

## 6. Stage 4 completed
`4_merge_brazil_polygons.py` was added to merge chunk-level polygon outputs into Brazil-wide layers.

This stage produces national raw and dissolved polygon outputs.

---

## Current national execution state

The current pipeline has already run successfully over:

- **407 active chunks**

This means the engineering workflow is now operational at Brazil scale.

---

## Current active outputs

The main current outputs are:

### Per chunk
- prepared aligned rasters and vectors
- refined raster masks
- raw polygon outputs
- dissolved polygon outputs
- QC summaries

### National merged outputs
- Brazil-wide raw polygons
- Brazil-wide dissolved polygons

---

## Current methodological position

The active operational refinement logic uses:

- MapBiomas 10 m as semantic base and master grid,
- GHSL 2022 as built-up support,
- WorldCover 2021 as vegetation support.

The project currently does **not** use WSF in the core rule.

This was an explicit methodological decision based on temporal-consistency concerns.

---

## What is considered finished

At this point, the following can be considered completed for the current project phase:

- national pipeline design,
- chunk-based processing structure,
- active multi-source raster refinement logic,
- polygonization workflow,
- Brazil-scale execution,
- repository cleanup and archival separation,
- main documentation restructuring.

---

## What is not fully finished yet

Several important tasks still remain:

### 1. Visual validation
Representative chunk outputs still need systematic visual inspection in QGIS.

### 2. National QC aggregation
Per-chunk QC should be aggregated into one Brazil-wide summary.

### 3. Boundary consistency checks
Chunk-boundary overlap or duplication effects should be reviewed after the national merge.

### 4. Optional industrial-area veto
OSM industrial/factory masking remains a planned enhancement.

### 5. Satellite-image integration
The next major project phase is still to come.

---

## Current project transition point

The project is now at the transition between:

- label-refinement engineering,
- and satellite-image processing / dataset construction.

This means the core refinement implementation is done, and the next phase should focus on:

- validating the labels,
- consolidating the national outputs,
- and connecting the labels to imagery.

---

## Current status in one sentence

The Brazil-scale favela refinement pipeline is now operational, documented, and structurally cleaned, and the project is ready to move into validation and satellite-image preparation.