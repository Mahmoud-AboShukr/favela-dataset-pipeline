# Data Sources

## Purpose

This page documents the main data sources used in the favela dataset pipeline.

The project combines:

- official vector labels,
- auxiliary raster products used for refinement,
- later Sentinel imagery used for dataset construction,
- and internally derived intermediate products used for analysis and quality control.

The current work is centered on a **Brasília pilot**, but the longer-term objective is to build a scalable pipeline for all Brazil.

---

## Data-source roles in the pipeline

The data sources in the project do not all serve the same role.

At a high level, they can be grouped into four categories:

1. **Primary label sources**  
   Official vector data that define the initial favela polygons.

2. **Auxiliary refinement sources**  
   Raster products used to identify built-up, vegetated, anthropic, or changing areas that may help refine noisy polygon boundaries.

3. **Target imagery sources**  
   Sentinel imagery used later for alignment, patch extraction, and deep-learning-ready dataset generation.

4. **Derived internal products**  
   Intermediate rasters, masks, and QC layers generated inside the project from the above inputs.

---

## 1. Primary label source

### Official Brazilian favela polygons

The project begins with official favela polygons provided as vector data.

These polygons are the primary label source and remain the backbone of the annotation workflow. They are cleaned, standardized, and subsetted before refinement.

Typical issues addressed during preprocessing include:

- invalid geometries,
- multipart features,
- duplicate or missing identifiers,
- subset extraction for the Brasília pilot.

### Role in the pipeline

The official polygons are used to:

- define the initial candidate settlement extent,
- generate binary raster masks,
- provide the baseline geometry for refinement,
- and support later alignment with satellite imagery.

### Important note

The project does **not** currently aim to replace these official polygons entirely. Instead, it aims to **refine them conservatively** using auxiliary evidence.

---

## 2. Auxiliary refinement sources

Auxiliary refinement sources are raster layers used to help determine which parts of a polygon should likely be:

- preserved,
- trimmed,
- or interpreted with caution.

These sources are especially important because the official polygons may contain vegetation, broad margins, or mixed land-cover types.

### 2.1 GHSL

The **Global Human Settlement Layer (GHSL)** is one of the main auxiliary data families used in the project.

GHSL products provide built-up or settlement-related information that can be used to estimate whether an area is likely urbanized or structurally occupied.

### Current role

GHSL is currently used for:

- built-up evidence,
- settlement-mask experiments,
- threshold-based pilot refinement,
- and temporal comparison across multiple epochs.

### Why GHSL is useful

GHSL is attractive because it provides a large-scale and standardized way to estimate built-up presence, which is relevant to settlement refinement.

### Current limitations

Depending on the product and epoch, GHSL may be:

- sparse,
- resolution-limited,
- threshold-sensitive,
- or insufficient as a standalone final refinement source.

For this reason, GHSL is currently treated as an important **baseline evidence source**, not automatically the final solution.

---

### 2.2 GHSL temporal derivatives

In addition to single-epoch GHSL layers, the project also derives **temporal-change products** by comparing multiple GHSL epochs over Brasília.

These internal derivatives include outputs such as:

- growth,
- loss,
- persistence,
- and supporting harmonized binary masks.

### Role in the pipeline

These temporal layers are used mainly for:

- interpretation,
- diagnosis of spatial mismatch,
- and contextual understanding of built-up evolution.

They are **not** currently treated as direct label truth.

### Why they matter

Temporal change can help explain why a location appears weakly supported in one epoch but more strongly built-up in another.

---

### 2.3 MapBiomas

**MapBiomas** is being tested as a new pilot refinement source for Brasília.

MapBiomas provides thematic land-cover information that may be used to identify:

- vegetation-like areas,
- anthropic or urban-support areas,
- and uncertain land-cover zones.

### Current role

MapBiomas is being evaluated as a possible standalone pilot source for:

- vegetation removal,
- anthropic or built-up support inference,
- and conservative polygon refinement.

### Why MapBiomas is useful

It offers a practical alternative to immediately computing vegetation indices from Sentinel-2, especially when cloud contamination and optical preprocessing make a fast pilot more difficult.

### Key question

The current pilot is designed to answer:

> Can MapBiomas alone provide enough evidence to refine official favela polygons conservatively in Brasília?

---

### 2.4 Future auxiliary sources

The project may later include additional auxiliary evidence sources if no single product proves sufficient alone.

Potential examples include:

- **WSF (World Settlement Footprint)** for binary settlement support,
- directly computed **NDVI** or other optical indices from Sentinel-2,
- additional built-up or land-cover products if needed.

These are currently considered future or optional extensions rather than fixed core inputs.

---

## 3. Target imagery sources

The final dataset is intended to be aligned with Sentinel imagery for downstream machine learning.

### 3.1 Sentinel-2

**Sentinel-2** provides optical multispectral imagery.

### Role in the pipeline

Sentinel-2 is intended to support:

- later image-label alignment,
- optical patch extraction,
- visual interpretation,
- and potentially vegetation-related analysis such as NDVI.

### Current project status

Sentinel-2 is part of the planned downstream data-generation workflow, but direct NDVI-based refinement is currently deferred in the Brasília pilot in favor of first testing MapBiomas.

---

### 3.2 Sentinel-1

**Sentinel-1** provides synthetic aperture radar (SAR) imagery.

### Role in the pipeline

Sentinel-1 is intended to support:

- later image-label alignment,
- SAR-based deep learning experiments,
- and multimodal dataset construction together with Sentinel-2.

### Current project status

Sentinel-1 preprocessing is part of the broader pipeline, but the current refinement work still happens upstream of the final imagery-aligned dataset stage.

---

## 4. Derived internal products

The project also creates many intermediate products derived from the above sources.

These are not external raw datasets, but they are important working data layers.

Examples include:

- cleaned polygons,
- AOI subsets,
- clipped GHSL rasters,
- settlement masks,
- threshold-sweep outputs,
- refined raster masks,
- refined vector polygons,
- temporal change maps,
- QC overlays and statistics.

### Role in the pipeline

These derived products make the workflow reproducible and allow each pilot step to be inspected independently.

They are especially important for:

- debugging,
- visual comparison,
- threshold experiments,
- and documenting methodological decisions.

---

## Source categories by function

Another useful way to think about the project’s data sources is by function.

### Geometry source
- official favela polygons

### Built-up support
- GHSL
- potentially WSF or future built-up products

### Vegetation or land-cover support
- MapBiomas
- potentially later NDVI from Sentinel-2

### Temporal context
- GHSL temporal derivatives

### Final imagery for dataset creation
- Sentinel-2
- Sentinel-1

This distinction is important because different sources answer different questions in the refinement workflow.

---

## Current data-source strategy

The current strategy in the Brasília pilot is:

1. use the official polygons as the base labels,
2. evaluate auxiliary evidence sources one at a time where possible,
3. keep refinement conservative and interpretable,
4. determine whether one source is sufficient alone,
5. move to multi-source fusion only if necessary.

In practical terms:

- GHSL remains the main built-up baseline,
- temporal GHSL products provide contextual interpretation,
- MapBiomas is now being tested as a standalone land-cover refinement source,
- Sentinel-based vegetation-index workflows remain possible but are not the first pilot path.

---

## Selection principles

When choosing a data source for refinement, the project prioritizes:

- interpretability,
- operational simplicity,
- spatial relevance to the polygon-noise problem,
- compatibility with the later raster grid and dataset workflow,
- and the ability to preserve realistic settlement geometry.

A source is more valuable if it helps remove obvious false-positive areas without introducing major shape distortion or large uncertainty.

---

## Known challenges across sources

Several issues affect data-source use in this project:

- temporal mismatch between products,
- differences in resolution,
- class or threshold ambiguity,
- mixed pixels near urban boundaries,
- sparse or coarse settlement evidence,
- disagreement between built-up and vegetation indicators.

These challenges are one reason why the project is being developed through pilot experiments rather than assuming that a single product is always sufficient.

---

## Related method pages

See also:

- [Label Refinement](label_refinement.md)
- [GHSL Refinement](ghsl_refinement.md)
- [Temporal Change Analysis](temporal_change_analysis.md)
- [MapBiomas Refinement](mapbiomas_refinement.md)
- [Multi-source Fusion](multi_source_fusion.md)
- [Preprocessing S1](preprocessing_s1.md)
- [Preprocessing S2](preprocessing_s2.md)
- [Tiling and Alignment](tiling_and_alignment.md)