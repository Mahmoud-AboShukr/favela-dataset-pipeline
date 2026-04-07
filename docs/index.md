# Favela Dataset Pipeline

## Overview

This project develops a Brazil-scale pipeline for refining official favela polygons into cleaner raster and polygon labels for later dataset construction and machine-learning use.

The project began with earlier pilot experiments, especially a Brasília GHSL-based pilot and later Manaus and MapBiomas experiments. It has now evolved into a working national chunked pipeline that processes the favela layer across Brazil using multiple raster sources and produces both refined raster masks and refined polygon outputs.

The long-term objective is to build a robust, deep-learning-ready favela dataset that can later be aligned with satellite imagery such as Sentinel-1 and Sentinel-2.

---

## Current active workflow

The current active workflow is the Brazil-scale chunked pipeline located under:

`src/final_pipeline_scale_up/`

This is the main operational workflow of the project.

It uses:

- favela polygons as the source labels,
- MapBiomas 10 m as the semantic base and master grid,
- GHSL 2022 as built-up support,
- WorldCover 2021 as vegetation support.

The final outputs remain polygon-based, but the decision process is raster-based.

---

## Current pipeline stages

The active pipeline consists of four main stages:

1. **Prepare inputs**  
   Build chunk-level aligned raster and vector inputs.

2. **Build refined mask**  
   Apply the active multi-source refinement rule.

3. **Polygonize and QC**  
   Convert refined raster masks to polygon outputs and compute basic quality-control summaries.

4. **Merge Brazil polygons**  
   Merge chunk-level polygon outputs into Brazil-wide layers.

---

## Current project status

The national-scale label-refinement pipeline has already been executed successfully across:

- **407 active chunks**

The project now has:

- chunk-level prepared inputs,
- chunk-level refined raster masks,
- chunk-level raw polygons,
- chunk-level dissolved polygons,
- chunk-level QC files,
- Brazil-wide merged polygon outputs.

The pipeline is therefore no longer only experimental; it is now operational at Brazil scale.

---

## Why this project matters

Official favela polygons are useful but can contain noise, coarse boundaries, or label spillover. Refining these polygons helps reduce manual correction effort and improves the quality of labels that will later be used for dataset construction and model development.

The project is designed to preserve:

- methodological traceability,
- scalable execution,
- and final polygon-based outputs that remain practical for review and correction.

---

## Documentation structure

This documentation is organized around four main perspectives:

### Project
High-level project context, status, and repository organization.

### Methods
The current active Brazil-scale pipeline and its methodological logic.

### Runbook
Practical instructions for running and validating the pipeline.

### Archive
Older pilot and experiment phases that informed the current design but are no longer the main workflow.

---

## Current transition point

The core refinement pipeline is now in place. The project is at the transition between:

- national label refinement,
- and the next phase of satellite-image processing and dataset construction.

The immediate next tasks are:

- validate representative outputs,
- aggregate QC nationally,
- review chunk-boundary consistency,
- and prepare for satellite-image alignment.

---

## Recommended starting pages

If you are new to the project, the best reading order is:

1. **Project Brief**
2. **Current Pipeline**
3. **Run Brazil Pipeline**
4. **Brazil Pipeline Completed (March 2026)**
5. **Archive pages** for historical context if needed

---

## Short summary

This repository now contains a working Brazil-scale favela-refinement pipeline that combines semantic and built-up support layers to produce refined raster and polygon labels, with the next project phase focused on validation and satellite-image integration.