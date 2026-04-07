# Temporal Change Analysis

## Purpose

This page documents the temporal-change workflow used to compare multiple **GHSL epochs** over the Brasília pilot area.

The purpose of this analysis is **not** to produce the final refinement mask directly. Instead, it is used as an **auxiliary diagnostic method** to help answer questions such as:

- has the built-up footprint changed between two GHSL epochs?
- can apparent polygon mismatch be partly explained by temporal urban growth or loss?
- can temporal persistence help distinguish stable built-up areas from recent or uncertain changes?

This method is therefore used mainly for **interpretation, debugging, and contextual support** during the pilot stage.

---

## Role in the project

The temporal-change workflow supports the broader label-refinement pipeline by providing additional context for understanding spatial disagreement between:

- official favela polygons,
- GHSL-derived settlement evidence,
- and other candidate refinement products.

In particular, temporal change analysis can help identify whether an apparent false negative in one GHSL layer may be related to:

- settlement growth after an earlier epoch,
- lower built-up intensity in one period,
- or a mismatch caused by product resolution and temporal coverage.

At the current stage of the project, temporal-change outputs are treated as **supporting evidence**, not as direct replacement labels.

---

## Inputs

The workflow currently compares two GHSL rasters for Brasília:

- `data/raw/ghsl/Brasilia_2018.tif`
- `data/raw/ghsl/Brasilia_2025.tif`

These rasters represent different GHSL epochs and may differ in:

- spatial resolution,
- coverage,
- product characteristics,
- and built-up representation.

Because of this, temporal comparison requires harmonization before change maps can be interpreted safely.

---

## Main outputs

The workflow generates a set of intermediate and final rasters inside a temporal-change working directory.

Typical outputs include:

- **growth** — areas that appear built-up in the later epoch but not in the earlier epoch
- **loss** — areas that appear built-up in the earlier epoch but not in the later epoch
- **persistence** — areas that appear built-up in both epochs
- supporting binary masks and resampled intermediate rasters used during harmonization

These outputs are useful for visual QC, interpretation of settlement evolution, and comparison against official polygons.

---

## Conceptual definitions

Let:

- **Epoch A** = earlier GHSL raster
- **Epoch B** = later GHSL raster

After binarization and alignment:

- **Growth** = pixels that are non-built in Epoch A and built in Epoch B
- **Loss** = pixels that are built in Epoch A and non-built in Epoch B
- **Persistence** = pixels that are built in both Epoch A and Epoch B

These categories should be interpreted carefully, especially when the two rasters differ in resolution or product design.

---

## Method overview

The temporal-change workflow follows these general steps:

1. load the two GHSL rasters,
2. inspect metadata and confirm extent overlap,
3. align both rasters to a comparable grid,
4. convert each raster into a built-up binary representation,
5. compare the aligned binary masks pixel by pixel,
6. export growth, loss, and persistence rasters,
7. inspect the results visually and use them as contextual evidence.

This is a diagnostic workflow rather than a final labeling workflow.

---

## Step 1 — Input inspection

Before comparing the two epochs, the following properties must be checked:

- CRS
- spatial extent
- resolution
- nodata value
- raster dimensions
- valid data overlap

This step is essential because a temporal comparison is only meaningful when the rasters overlap spatially and can be brought onto a common analysis grid.

---

## Step 2 — Harmonization and alignment

Temporal GHSL comparison may involve rasters with different spatial resolutions or grid definitions.

To make comparison possible, the two rasters must be harmonized by:

- choosing a reference grid,
- reprojecting if necessary,
- resampling one raster to match the other,
- and ensuring that both outputs share the same shape, transform, and extent.

This harmonization step is one of the most important parts of the workflow, because poor alignment can create artificial change.

---

## Step 3 — Binary built-up masks

Once the rasters are aligned, each epoch is converted into a binary built-up mask.

Conceptually:

- `1` = built-up or settlement-supporting pixel
- `0` = non-built pixel

The exact thresholding or class-conversion logic depends on the GHSL product used.

This binary conversion is necessary because the temporal analysis focuses on **change in built-up presence**, not on the full continuous value distribution.

---

## Step 4 — Change computation

After binary masks have been created for both epochs, temporal change is computed using logical comparison.

Conceptually:

- **growth** = built in later epoch only
- **loss** = built in earlier epoch only
- **persistence** = built in both epochs

These outputs are written as separate rasters for inspection and later comparison.

---

## Step 5 — Visual and contextual interpretation

The change outputs are then inspected in relation to:

- official favela polygons,
- current GHSL refinement masks,
- known built-up areas,
- and other candidate evidence layers.

This step is critical, because temporal change should not be interpreted mechanically. Some apparent changes may reflect:

- real urban growth,
- product differences,
- resolution mismatch,
- thresholding effects,
- or raster alignment artifacts.

---

## How this method supports refinement

Temporal GHSL analysis is currently used in the project for three main purposes:

### 1. Diagnosing apparent false negatives
If a polygon overlaps an area that is not strongly supported by one GHSL epoch, temporal comparison can show whether the area appears more built-up in another epoch.

### 2. Identifying stable built-up zones
Persistent built-up areas across epochs may provide stronger support for stable settlement presence.

### 3. Understanding evolving urban context
Growth patterns can help interpret whether settlement expansion or urban change may explain disagreement between official polygons and auxiliary evidence.

---

## Current interpretation policy

At the current pilot stage, temporal-change outputs should be treated as:

- **diagnostic evidence**
- **interpretive context**
- **support for QC and analysis**

They should **not** be treated as direct ground truth for favela boundaries.

The temporal products are useful for understanding spatial patterns, but they do not by themselves determine whether a given polygon region should be kept or removed.

---

## Limitations

Temporal GHSL analysis has several important limitations.

### Resolution mismatch
If the two epochs differ strongly in resolution, apparent change may partly reflect resampling effects rather than true land-cover change.

### Product differences
Different GHSL products or epochs may not behave identically, even if both are interpreted as built-up evidence.

### Threshold sensitivity
Binary built-up masks depend on thresholding or value interpretation, which can affect downstream growth/loss results.

### Temporal ambiguity
A change between epochs indicates difference, but not necessarily the exact timing or cause of the change.

### Not settlement-specific
Built-up persistence or growth does not automatically mean informal settlement growth. It only indicates change in built-up evidence.

For these reasons, temporal-change outputs must always be interpreted alongside the broader refinement workflow.

---

## Recommended use in the Brasília pilot

Within the Brasília pilot, temporal-change analysis is most useful for:

- explaining spatial mismatch between GHSL outputs and polygons,
- identifying areas of stable built-up support,
- and documenting why a single GHSL epoch may be insufficient for interpretation.

It is best used as a **supporting experiment** alongside:
- GHSL refinement experiments,
- MapBiomas-based vegetation analysis,
- and later multi-source fusion if required.

---

## Related files

This method is associated with:

- raw GHSL epoch rasters in `data/raw/ghsl/`
- temporal outputs in `data/interim/temporal_change/`
- the temporal comparison script in `scripts/temporal_change_analysis.py`

Exact filenames and experiment-specific conclusions should be documented in:

- `experiments/`
- `status/`
- and the corresponding decision records where relevant.

---

## Related method pages

See also:

- [Label Refinement](label_refinement.md)
- [GHSL Refinement](../archive/legacy_methods/ghsl_refinement_legacy.md)
- [MapBiomas Refinement](../archive/legacy_methods/mapbiomas_refinement_legacy.md)
- [Multi-source Fusion](multi_source_fusion.md)
