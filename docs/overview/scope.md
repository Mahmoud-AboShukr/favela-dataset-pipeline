# Scope and Goals

## Purpose

This page defines the scope of the favela dataset pipeline and clarifies the main goals of the current project phase.

The project is focused on building a **deep-learning-ready dataset for favela detection and segmentation in Brazil**. The immediate work is centered on a **Brasília pilot**, which is used to design, test, and document the label-refinement workflow before broader scaling.

---

## Core project goal

The main objective is to construct a reproducible pipeline that can:

1. ingest official favela polygons,
2. clean and standardize those polygons,
3. refine noisy or overextended boundaries using auxiliary raster evidence,
4. generate binary masks suitable for machine learning,
5. align the labels with Sentinel-1 and Sentinel-2 imagery,
6. prepare the data for tiling, patch extraction, and later model development.

The project is therefore both:

- a **geospatial preprocessing pipeline**, and
- a **research workflow** for evaluating how best to refine noisy settlement labels.

---

## Immediate pilot scope

The current pilot scope is limited to **Brasília / Distrito Federal**.

This pilot is used to:

- validate the basic preprocessing workflow,
- test candidate refinement strategies,
- study the behavior of auxiliary raster products,
- produce QC outputs,
- and support methodological decisions before scaling.

The Brasília pilot is not the final target of the project. It is the controlled study area used to reduce complexity and make experimentation manageable.

---

## What is in scope

The current project scope includes:

### 1. Official polygon preparation
- ingesting the official favela polygons,
- fixing invalid geometries,
- exploding multipart features,
- assigning consistent identifiers,
- creating Brasília subsets for pilot work.

### 2. AOI preparation
- defining the Brasília pilot boundary,
- clipping and organizing inputs around the pilot AOI.

### 3. Auxiliary raster preparation
- preparing GHSL rasters,
- clipping rasters to the AOI,
- inspecting raster metadata and alignment,
- generating derived masks and supporting layers.

### 4. Label refinement experiments
- GHSL-based refinement baselines,
- GHSL temporal-change analysis,
- MapBiomas-based vegetation-removal experiments,
- future multi-source fusion if needed.

### 5. Raster mask generation
- creating binary masks from refined labels,
- producing intermediate debug masks,
- preparing outputs that can later be aligned with satellite imagery.

### 6. Documentation and QC
- documenting methods,
- recording decisions,
- tracking status notes,
- producing experiment summaries,
- preparing thesis-oriented drafts.

---

## What is out of scope for the current phase

The following items are part of the broader project vision but are **not yet the main focus** of the current pilot phase:

### 1. Full Brazil-scale execution
The project is not yet running refinement for all Brazilian states at production scale.

### 2. Final model training
The current work is focused on dataset construction and label quality, not yet on final deep-learning experiments.

### 3. Full national evaluation benchmark
The current pilot does not yet include a large manually validated benchmark across Brazil.

### 4. Permanent final refinement method
The project is still evaluating candidate refinement strategies. No single final method is yet locked for nationwide use.

### 5. Full Sentinel-driven refinement
Sentinel-1 and Sentinel-2 are part of the broader pipeline, but the current pilot is still focused mainly on upstream label-refinement experiments.

---

## Current methodological scope

At this stage, the project treats refinement as a **modular evidence-based problem**.

The official polygon is the starting point, and auxiliary sources are evaluated according to the role they can play, for example:

- built-up support,
- vegetation-removal evidence,
- temporal interpretation,
- or future multi-source fusion.

The current work is therefore focused less on “finding one perfect raster” and more on designing a defensible and scalable refinement workflow.

---

## Current goals for the Brasília pilot

The immediate goals of the Brasília pilot are:

1. establish a stable preprocessing workflow for the official polygons and AOI,
2. test whether GHSL can support conservative refinement,
3. evaluate whether temporal GHSL analysis adds useful interpretive context,
4. test whether MapBiomas alone can support vegetation-related refinement,
5. determine whether a single-source method is sufficient or whether fusion is required,
6. document the resulting methods clearly enough to support future scaling and thesis writing.

---

## Longer-term goals

Beyond the current pilot, the longer-term project goals are to:

- scale the workflow by Brazilian state,
- align refined labels with Sentinel-1 and Sentinel-2,
- generate a patch-based dataset,
- support segmentation and detection experiments,
- and create a reusable and well-documented research pipeline for informal-settlement mapping.

---

## Guiding principles

The project is currently guided by the following principles:

### Conservative refinement
Refinement should improve noisy polygons without aggressively redrawing them from scratch.

### Interpretability
Methods should remain understandable and auditable during the pilot stage.

### Modularity
Different evidence sources should be testable without forcing the whole pipeline to be rewritten.

### Reproducibility
Intermediate products, QC outputs, and decisions should be documented clearly.

### Scalability
Pilot choices should be made with future Brazil-scale processing in mind.

---

## Summary

In summary, the current scope is:

- a **Brasília-centered pilot**,
- focused on **polygon cleaning and label refinement**,
- supported by **auxiliary raster experiments**,
- documented as both a **pipeline implementation** and a **research workflow**,
- with the long-term aim of producing a scalable dataset for favela mapping in Brazil.