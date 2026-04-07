# Data Sources

## Purpose

This page documents the main data sources used by the current Brazil-scale favela refinement pipeline.

The project combines vector labels and multiple raster products in order to refine the national favela layer into cleaner raster and polygon outputs.

This page focuses on the **current active pipeline**, not the older archived pilot-only workflows.

---

## Overview

The active refinement workflow uses the following core inputs:

1. favela polygons,
2. MapBiomas 10 m,
3. GHSL EMC-BUILT 2022 10 m,
4. ESA WorldCover 2021 v200.

A fifth source is planned for later post-processing:

5. OSM industrial / factory polygons.

---

## 1. Favela polygons

### Role
The favela polygons are the main target labels to be refined.

They define:

- the starting polygon footprint,
- the spatial extent of the label-refinement problem,
- and the vector basis for the final output.

### Usage in the pipeline
The polygons are used to:

- define the chunked processing extent,
- generate per-chunk local favela subsets,
- rasterize a favela mask on the working grid,
- and later assign refined polygons back to source polygons.

### Output relationship
Although the refinement logic itself is raster-based, the final project remains polygon-oriented, so these source polygons remain central throughout the workflow.

---

## 2. MapBiomas 10 m

### Role
MapBiomas is the semantic base layer of the current active pipeline.

It is used as:

- the main land-cover / land-use interpretation source,
- the master thematic layer,
- and the master grid for raster alignment.

### Why it matters
MapBiomas provides explicit semantic classes that help distinguish:

- urban built-up areas,
- uncertain non-vegetated areas,
- vegetation,
- water and other non-target classes.

This makes it the main source of semantic control in the refinement logic.

### Main class usage
The current pipeline interprets MapBiomas classes approximately as follows:

#### Main keep class
- `24 = Urban Area`

#### Uncertain class
- `25 = Other Non Vegetated Areas`

#### Vegetation classes used as removal support
- `3 = Forest Formation`
- `4 = Savanna Formation`
- `5 = Mangrove`
- `6 = Floodable Forest`
- `11 = Wetland`
- `12 = Grassland`
- `49 = Wooded Sandbank Vegetation`
- `50 = Herbaceous Sandbank Vegetation`

#### Hard-remove classes
- `31 = Aquaculture`
- `33 = Water`

### Operational role
In the current pipeline, MapBiomas is not just a source of classes. It also defines the working raster geometry for each chunk.

---

## 3. GHSL EMC-BUILT 2022 10 m

### Role
GHSL is used as built-up support.

It helps identify whether uncertain pixels are likely to belong to built-up favela structures rather than to surrounding non-target areas.

### Why it matters
The project learned early that land-cover semantics alone are not enough. Some uncertain pixels need additional support before they can be kept.

GHSL provides that support.

### Current interpretation
The current pipeline uses GHSL as a built-up evidence surface and thresholds it to create a support mask.

In the current national run, the active threshold was:

- `GHSL >= 20.0`

### CRS note
A key practical detail is that GHSL uses a different CRS from the other main sources.

This is why Stage 1 must explicitly reproject and align GHSL to the MapBiomas grid.

### Current status
GHSL is part of the active core rule and is one of the main reasons the final method is stronger than the older MapBiomas-only variants.

---

## 4. ESA WorldCover 2021 v200

### Role
WorldCover is used mainly as vegetation support.

Its main job is to help suppress vegetation spillover in and around favela edges.

### Why it matters
The project repeatedly observed that edge ambiguity is one of the central problems in label refinement. WorldCover provides an additional vegetation-oriented signal that complements MapBiomas vegetation classes.

### Typical classes used
The current pipeline uses WorldCover mainly to identify vegetation-like and water-like areas such as:

- tree cover,
- shrubland,
- grassland,
- wetlands,
- mangroves,
- permanent water bodies.

### Operational role
WorldCover is aligned to the MapBiomas grid during Stage 1 and then used in Stage 2 to remove likely non-target pixels.

---

## 5. OSM industrial / factory polygons

### Role
This source is planned for later post-processing.

Its purpose is to remove industrial or non-residential built-up areas that may still survive the raster refinement logic.

### Why it is needed
Even if an area is built-up, it is not necessarily a favela. Industrial and factory zones are a good example of built-up non-target land that may need explicit masking.

### Current status
OSM industrial/factory masking is not yet part of the active operational pipeline, but it remains part of the planned next refinement stage.

---

## Source intentionally excluded from the core rule

## WSF

### Historical role
WSF was considered as a settlement-confirmation source during the design of the multi-source pipeline.

### Why it is not active now
It is currently excluded from the core rule because of temporal-consistency concerns relative to the current refinement context.

Using an older settlement source as a mandatory support layer could suppress valid more recent built-up favela extent.

### Current status
WSF is not part of the active pipeline logic, but it may later be used for comparison or ablation experiments.

---

## Why multiple sources are needed

No single source is sufficient on its own.

### Favela polygons alone
They provide the target footprint but can contain geometry and boundary noise.

### MapBiomas alone
It provides strong semantics but creates a trade-off between keeping uncertain built-up edges and suppressing vegetation spillover.

### GHSL alone
It provides built-up support but is not enough to drive the full semantic decision process.

### WorldCover alone
It helps identify vegetation but is not sufficient as a standalone refinement source.

The current active method therefore depends on combining these sources rather than trusting any one source blindly.

---

## Current active source combination

The current operational pipeline uses:

- favela polygons as the target vector input,
- MapBiomas 10 m as the semantic base and master grid,
- GHSL 2022 as built-up support,
- WorldCover 2021 as vegetation support.

This is the active source combination used in the national-scale run.

---

## Relationship to the project phases

These sources belong to the label-refinement phase of the project.

Once the labels are sufficiently validated, the next phase will connect them to satellite-image processing and dataset construction.