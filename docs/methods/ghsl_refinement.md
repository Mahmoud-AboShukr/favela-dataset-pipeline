# GHSL Refinement

## Purpose

This page documents how **GHSL** is used as an auxiliary evidence source to support the refinement of official favela polygons in the Brasília pilot.

The purpose of GHSL-based refinement is to test whether built-up or settlement-related raster evidence can help:

- identify parts of polygons that are plausibly urbanized,
- support the generation of binary settlement masks,
- and provide a baseline refinement strategy before moving to more complex or multi-source approaches.

GHSL-based refinement is currently treated as an important **baseline method**, not necessarily the final exclusive refinement solution.

---

## Role in the project

GHSL is one of the main auxiliary data families currently used in the refinement stage.

Within the project, GHSL serves three related roles:

1. **Built-up evidence**  
   It provides a proxy for urbanized or structurally occupied areas inside and around the official polygons.

2. **Settlement-mask generation**  
   It supports the creation of binary masks derived from thresholding or class conversion.

3. **Baseline refinement experiment**  
   It provides a first operational refinement strategy against which other sources, such as MapBiomas, can later be compared.

GHSL is therefore central to the early Brasília pilot, even though the project now allows for multiple refinement evidence sources.

---

## Why GHSL was chosen initially

GHSL was selected as an early refinement source because it offers a large-scale and standardized representation of built-up or settlement-related information.

This made it a strong candidate for the first pilot because:

- it is available over the study area,
- it is directly relevant to settlement presence,
- it is compatible with raster-based mask generation,
- and it can be aligned with a later geospatial machine learning workflow.

In the initial project framing, GHSL was expected to serve as the main raster evidence for refining noisy official polygons.

The project has since become more modular, but GHSL remains the main built-up baseline.

---

## General refinement objective

The GHSL-based workflow does **not** aim to redraw favela polygons from scratch.

Instead, the objective is to:

- begin with the cleaned official polygon as the main label source,
- use GHSL to estimate built-up support inside or around the polygon,
- generate raster evidence that can be compared with the polygon extent,
- and produce refined masks conservatively.

This means GHSL is used as **supporting evidence**, not as a direct replacement geometry.

---

## Inputs

The GHSL refinement workflow typically takes as input:

- cleaned official favela polygons,
- the Brasília pilot AOI,
- one or more GHSL rasters covering the same area.

Depending on the experiment, these GHSL inputs may represent:

- built-up fraction or built-up support,
- settlement-related masks,
- or multiple epochs used for comparison.

The exact product and epoch should be documented clearly for each experiment.

---

## Main GHSL preparation steps

Before refinement, the GHSL raster must be prepared for the Brasília pilot.

Typical preparation includes:

1. identifying the correct raster tile for the study area,
2. checking CRS, resolution, extent, and nodata,
3. confirming overlap with the Brasília AOI,
4. clipping the raster to the area of interest,
5. saving the clipped version for repeated experiments.

This preparation step is essential because an incorrect tile or extent mismatch can invalidate the downstream refinement workflow.

---

## GHSL-derived evidence types

Within the project, GHSL can support refinement in more than one way.

### 1. Continuous built-up support

Some GHSL products provide continuous or quasi-continuous values that indicate the degree of built-up presence.

These can be used to:

- inspect built-up intensity,
- test thresholds,
- and generate candidate built-up masks.

### 2. Binary settlement masks

A GHSL-based binary mask can be created by applying thresholding or class-conversion rules.

Conceptually:

- `1` = likely built-up or settlement-supporting pixel
- `0` = non-built pixel

This binary representation is easier to use in mask refinement experiments.

### 3. Temporal comparison support

When multiple GHSL epochs are available, GHSL can also be used to derive growth, loss, and persistence products.

These are documented separately under the temporal-change method page.

---

## Settlement-mask generation

A common use of GHSL in the project is to generate a binary settlement-support mask for Brasília.

The general idea is:

1. start from a clipped GHSL raster,
2. interpret its values as built-up evidence,
3. apply one or more thresholds,
4. export a binary raster mask for later refinement tests.

This step is useful because it converts the raw GHSL product into a form that can be directly compared with the rasterized official polygons.

However, this process is sensitive to:

- threshold selection,
- product type,
- resolution,
- and local urban morphology.

---

## Thresholding strategy

A major part of the GHSL pilot is the evaluation of thresholded settlement masks.

The workflow may test multiple thresholds to determine how strict or permissive the built-up support should be.

### Why thresholding matters

If the threshold is too strict:
- true settlement areas may be missed,
- the mask becomes sparse,
- and polygon refinement may become too destructive.

If the threshold is too permissive:
- non-settlement areas may be included,
- the mask may become too broad,
- and the refinement loses precision.

For this reason, GHSL threshold sweeps are useful during the pilot stage.

---

## Relationship to polygon refinement

Once a GHSL-derived mask has been created, it can be compared to the rasterized official polygon in different ways.

Possible uses include:

- identifying where the polygon overlaps built-up support,
- measuring the amount of polygon area not supported by GHSL,
- testing whether unsupported boundary areas should be trimmed,
- or using GHSL only as a protective layer in a more conservative rule.

In practice, GHSL is best used carefully because a direct polygon intersection with a sparse GHSL mask can produce unrealistic shapes.

---

## Conservative use of GHSL

The project increasingly treats GHSL as a source of **supportive evidence** rather than a complete geometric solution.

A conservative way to use GHSL is to:

- preserve the official polygon as the main label,
- use GHSL to support keeping plausible built-up regions,
- avoid fully replacing the polygon with the GHSL mask,
- and use additional logic or postprocessing where necessary.

This is particularly important in informal-settlement mapping because:

- settlement patterns may be fragmented,
- built-up density may be heterogeneous,
- and sparse GHSL support does not necessarily imply that a polygon region is incorrect.

---

## Postprocessing

After generating a GHSL-derived binary mask or refinement candidate, postprocessing may be applied to improve usability.

Typical postprocessing may include:

- removing very small isolated regions,
- filling small holes,
- smoothing or cleaning noisy edges,
- converting raster results back into vector form where needed.

The exact postprocessing settings may vary between experiments and should be documented alongside the relevant outputs.

---

## Evaluation in the Brasília pilot

The GHSL refinement workflow is evaluated using both visual and simple quantitative checks.

### Visual evaluation

Typical visual QC includes comparison between:

- original polygons,
- GHSL rasters,
- thresholded settlement masks,
- refined raster outputs,
- and later contextual overlays where useful.

### Quantitative evaluation

Simple checks may include:

- polygon area before and after refinement,
- overlap between GHSL masks and polygon masks,
- sensitivity to threshold selection,
- and comparison across rule variants.

The goal is not only to produce a mask, but to understand how robust GHSL is as a refinement source.

---

## Strengths of GHSL in this project

GHSL offers several advantages:

- it is directly related to built-up presence,
- it supports raster-based refinement workflows,
- it provides a scalable evidence source,
- it is suitable for threshold experiments,
- and it integrates naturally into a geospatial ML pipeline.

These strengths make it an important baseline source even if it is not sufficient alone.

---

## Limitations

GHSL also has several important limitations in this project.

### Sparsity
Some GHSL-derived masks may be too sparse to preserve realistic polygon geometry if used directly.

### Threshold sensitivity
The result can change significantly depending on the chosen threshold.

### Resolution constraints
Some products or epochs may be too coarse for accurate boundary refinement.

### Mixed urban morphology
Informal settlements may contain a mix of built-up, bare soil, vegetation, and irregular structures that are not fully captured by GHSL.

### Not a direct favela label
GHSL indicates built-up or settlement support, not favela identity specifically.

Because of these limitations, GHSL is best treated as a baseline refinement source or a component of a broader multi-source workflow.

---

## Position relative to other methods

Compared with MapBiomas:
- GHSL is more directly related to built-up evidence,
- while MapBiomas is more directly useful for land-cover and vegetation interpretation.

Compared with temporal GHSL analysis:
- GHSL refinement uses one or more GHSL layers directly for candidate mask generation,
- while temporal analysis focuses on change interpretation across epochs.

Compared with future multi-source fusion:
- GHSL may serve as the built-up support component in a combined refinement strategy.

---

## Recommended use in the Brasília pilot

Within the Brasília pilot, GHSL should be used as:

- the main built-up baseline,
- a source for settlement-mask experiments,
- a reference point for comparing alternative evidence sources,
- and a diagnostic tool for understanding where polygons align or disagree with built-up evidence.

The most useful question for the pilot is not simply:

> can GHSL produce a mask?

but rather:

> how well can GHSL support conservative refinement of official polygons without damaging realistic settlement geometry?

---

## Related files

This method is associated with:

- raw GHSL rasters in `data/raw/ghsl/`
- clipped GHSL rasters in `data/interim/ghsl_clips/`
- generated masks in `data/interim/masks/`
- threshold sweeps and debug masks in related interim folders
- GHSL scripts in `src/ghsl/`
- label refinement scripts in `src/labels/`

Experiment-specific outputs and conclusions should be documented in:

- `experiments/`
- `status/`
- and relevant decision records.

---

## Related method pages

See also:

- [Label Refinement](label_refinement.md)
- [Data Sources](data_sources.md)
- [Temporal Change Analysis](temporal_change_analysis.md)
- [MapBiomas Refinement](mapbiomas_refinement.md)
- [Multi-source Fusion](multi_source_fusion.md)