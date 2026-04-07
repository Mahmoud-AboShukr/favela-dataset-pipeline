# Satellite Processing Plan

## Purpose

This page describes the planned transition from label refinement to satellite-image processing.

At this stage of the project, the Brazil-scale label-refinement pipeline is operational. The next major phase is to connect the refined labels to satellite imagery so that a downstream machine-learning-ready dataset can be constructed.

---

## Current project position

The project has already completed the main label-refinement implementation phase.

The current workflow can now:

- prepare chunk-level aligned inputs,
- generate chunk-level refined raster masks,
- generate chunk-level raw and dissolved polygon outputs,
- and merge chunk-level outputs into Brazil-wide polygon layers.

This means the project now has refined labels that can become the basis for image-aligned dataset construction.

---

## Why satellite processing comes next

The long-term objective of the project is not only to refine polygons, but to build a dataset that can be used for model training and evaluation.

That requires:

- refined labels,
- imagery aligned to those labels,
- a reproducible extraction strategy,
- and well-documented preprocessing.

The label-refinement phase therefore acts as a preparatory stage for the imagery phase.

---

## Main goals of the satellite phase

The next phase should aim to:

1. define the satellite sources to be used,
2. align refined labels with imagery,
3. extract image tiles or patches,
4. define dataset splits,
5. document preprocessing choices,
6. prepare the final machine-learning-ready dataset structure.

---

## Candidate imagery sources

The main intended sources are:

### Sentinel-2
Useful for optical information, land-cover context, and visible built-environment patterns.

### Sentinel-1
Useful for radar-based urban texture and robustness under cloud conditions.

The final dataset may use one or both depending on the downstream modelling strategy.

---

## What must be done before full image extraction

Before large-scale satellite extraction begins, the following label-side tasks should be completed:

### 1. Visual validation
Representative refined outputs should be checked in QGIS.

### 2. QC aggregation
Chunk-level QC should be combined into a national summary.

### 3. Chunk-boundary consistency
Potential duplication or overlap effects at chunk boundaries should be reviewed after the national merge.

### 4. Optional post-processing
If needed, industrial-area veto logic using OSM can still be added before finalizing labels.

---

## Planned imagery workflow

A practical imagery workflow would likely include:

1. choose the imagery product and time range,
2. define the spatial extraction strategy,
3. decide on patch size and resolution,
4. clip or tile imagery according to the refined labels,
5. associate polygons or masks with image tiles,
6. build train/validation/test splits,
7. document preprocessing and metadata.

---

## Important alignment consideration

The refined labels are polygon-based in their final form, even though they were produced through raster logic.

This means the satellite phase must define carefully:

- whether polygons are rasterized again for model training,
- whether patch-level targets are derived from polygons directly,
- and how label/imagery alignment is handled reproducibly.

---

## What should be documented during the satellite phase

As the project moves into imagery, documentation should clearly record:

- source products,
- temporal choices,
- reprojection strategy,
- tiling and extraction rules,
- patch-generation logic,
- band selection,
- quality filtering,
- and final dataset organization.

---

## Recommended immediate next steps

The most sensible next sequence is:

1. validate a representative sample of refined labels,
2. aggregate QC and inspect the national merged outputs,
3. finalize the refined label product,
4. then begin imagery extraction and preprocessing documentation.

---

## Long-term relationship to the project

The satellite phase is the point where the current label-refinement work becomes a true dataset-building workflow.

In other words:

- the current pipeline produces refined labels,
- the next phase turns those labels into image-aligned training data.

This marks the transition from geospatial refinement engineering to downstream dataset construction for machine learning.