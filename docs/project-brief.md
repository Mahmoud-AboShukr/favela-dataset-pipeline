# Project Brief

## Title

Brazil-scale Favela Polygon Refinement Pipeline

---

## Short description

This project develops a scalable geospatial pipeline to refine official favela polygons across Brazil into cleaner raster and polygon labels. The refined outputs are intended to reduce manual correction effort and serve as a stronger basis for later dataset construction and machine-learning workflows.

---

## Main objective

The main goal is to improve the quality of the national favela label layer by combining multiple raster sources rather than relying on a single support layer or a purely manual correction process.

The refined outputs should:

- preserve likely built-up favela areas,
- suppress vegetation spillover and other non-target regions,
- remain practical for manual review,
- and later support downstream satellite-image dataset creation.

---

## Long-term objective

The longer-term goal of the project is to build a deep-learning-ready dataset for favela detection and segmentation in Brazil.

This means the current label-refinement work is not the final destination by itself. Rather, it is the label-engineering stage that prepares the project for:

- satellite-image alignment,
- dataset extraction,
- model training,
- and later evaluation.

---

## Historical development

The project began with early pilot experiments focused on Brasília and GHSL-based refinement. These pilots were useful for establishing the initial pipeline structure, but they also revealed a key limitation: a hard settlement-mask refinement strategy can wrongly remove valid label regions when the support layer contains false negatives.

Later phases explored:

- MapBiomas-based refinement,
- Manaus as a difficult urban–vegetation pilot,
- multi-city MapBiomas 10 m experiments,
- and increasingly multi-source logic.

These stages eventually led to the current Brazil-scale chunked pipeline.

---

## Current active methodology

The current operational refinement workflow uses:

- favela polygons as the source label layer,
- MapBiomas 10 m as the semantic base and master grid,
- GHSL EMC-BUILT 2022 10 m as built-up support,
- ESA WorldCover 2021 v200 as vegetation support.

The final output remains polygon-based, but the refinement logic is raster-based.

The workflow is chunked so that Brazil can be processed as many local units rather than one monolithic raster task.

---

## Current pipeline structure

The active workflow is implemented under:

`src/final_pipeline_scale_up/`

and is organized into four stages:

1. `1_prepare_inputs.py`
2. `2_build_refined_mask.py`
3. `3_polygonize_and_qc.py`
4. `4_merge_brazil_polygons.py`

These stages respectively handle:

- data preparation and alignment,
- raster refinement,
- polygonization and QC,
- national polygon merging.

---

## Key methodological decisions

Several important decisions define the current project state:

### 1. Chunk-based national processing
Brazil is processed as many local chunks rather than one full-country raster pass.

### 2. Multi-source refinement
The pipeline combines semantic and support layers rather than relying on a single raster source.

### 3. Polygon-based final outputs
Even though the logic is raster-based, the final product remains polygon-oriented.

### 4. WSF excluded from the core rule
WSF was considered, but it is not part of the current active rule because of temporal-consistency concerns.

### 5. Archived pilots remain documented but are no longer active
Older Brasília, Manaus, and MapBiomas-only experiments remain part of the project history but are no longer the main workflow.

---

## Current project status

The Brazil-scale active pipeline has already been executed successfully across:

- **407 active chunks**

This means the project now has:

- chunk-level prepared inputs,
- chunk-level refined raster masks,
- chunk-level raw polygons,
- chunk-level dissolved polygons,
- chunk-level QC summaries,
- and national merged polygon outputs.

The pipeline is therefore operational at national scale.

---

## What has been achieved so far

The project has already achieved:

- early pilot development and lessons from Brasília,
- semantic refinement development through MapBiomas,
- multi-source design maturation through Manaus and multi-city experiments,
- national raw-data organization,
- full implementation of the scaled-up operational pipeline,
- national execution of all main stages,
- repository cleanup and archival separation of old experiments.

---

## What still remains

Before moving fully into the satellite-image phase, the following tasks still remain:

- representative visual validation in QGIS,
- national QC aggregation,
- chunk-boundary consistency review,
- optional industrial-area veto,
- final transition to satellite-image processing and dataset building.

---

## Intended audience

This project brief is intended for:

- project supervisors,
- collaborators,
- future contributors,
- and anyone needing a concise explanation of the project’s purpose and current status.

---

## One-paragraph summary

The project has evolved from early Brasília GHSL-based pilots into a working Brazil-scale chunked favela-refinement pipeline. The active workflow uses MapBiomas 10 m, GHSL 2022, and WorldCover 2021 to produce refined raster and polygon labels across Brazil. The current national run has already completed successfully over 407 active chunks, and the project is now transitioning from label-refinement engineering into validation, consolidation, and preparation for satellite-image dataset construction.