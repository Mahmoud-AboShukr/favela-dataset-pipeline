# Chapter Draft — Experiments

## Introduction

This chapter documents the main pilot experiments conducted to support the development of a deep-learning-ready favela dataset for Brazil.

The experiments are centered on a **Brasília pilot area**, which serves as a controlled study region for testing candidate label-refinement strategies before broader scaling. The purpose of these experiments is not only to produce intermediate outputs, but also to evaluate which auxiliary raster evidence sources are sufficiently reliable, interpretable, and operational for refining noisy official favela polygons.

The experiments are designed to answer a central methodological question:

> how can official favela polygons be refined conservatively, especially where they include vegetation or weakly supported margins, without damaging realistic settlement geometry?

To address this question, multiple experimental directions were explored, including:

- GHSL-based refinement using built-up or settlement-derived evidence,
- GHSL temporal-change analysis across multiple epochs,
- MapBiomas-based refinement using land-cover classes,
- and the future possibility of multi-source fusion if no single source proves sufficient alone.

---

## Experimental framework

The experiments follow a common design logic.

First, the official favela polygons are treated as the **primary label source**. The aim of the experiments is therefore not to redraw settlement boundaries from scratch, but rather to improve them conservatively through the use of auxiliary evidence.

Second, the **Brasília pilot AOI** is used as a shared spatial framework for all experiments. This ensures comparability between different refinement strategies and keeps the pilot manageable during iterative development.

Third, the experiments are evaluated not only by output generation, but also by interpretability. In the context of noisy official polygons, a refinement method is only useful if it can be explained, inspected visually, and defended methodologically.

For this reason, the experiments are compared using both:

- **visual quality control**, through overlay inspection in GIS and intermediate raster outputs,
- and **simple quantitative indicators**, such as area removed, polygons affected, and consistency with the intended refinement objective.

---

## Experiment 1 — GHSL-based refinement baseline

### Objective

The first experimental direction evaluated whether **GHSL** could serve as a primary auxiliary evidence source for refining official favela polygons.

The main idea was that GHSL provides built-up or settlement-related information which could help identify parts of the polygons that are likely consistent with urbanized settlement structure. This made it a natural baseline candidate for the Brasília pilot.

### Rationale

GHSL was initially attractive because it offers:

- broad spatial coverage,
- built-up relevance,
- compatibility with raster-based refinement workflows,
- and a direct connection to settlement-support estimation.

The expectation was that GHSL could be used to generate binary settlement-support masks that would then help identify which portions of the official polygons should plausibly be retained or trimmed.

### Method summary

The GHSL baseline workflow involved:

1. preparing and clipping the GHSL raster over the Brasília AOI,
2. inspecting the raster values and metadata,
3. applying threshold-based logic to derive settlement-support masks,
4. comparing those masks to rasterized official polygons,
5. evaluating whether the resulting support was sufficient for conservative refinement.

### Main observations

The GHSL baseline was useful in that it provided a direct source of built-up support and allowed threshold-based experiments. However, several limitations emerged:

- the settlement support could be too sparse depending on threshold choice,
- the outputs were sensitive to resolution and product characteristics,
- and direct use of GHSL masks risked producing unrealistic or fragmented polygon shapes.

These findings suggested that GHSL is valuable as a **baseline built-up evidence source**, but not necessarily sufficient as a standalone final refinement method.

### Interim conclusion

The GHSL baseline remains an important experiment because it established:

- a built-up-oriented reference method,
- a first raster-based refinement workflow,
- and a benchmark against which other evidence sources can be compared.

However, it also made clear that settlement-support rasters alone may not fully resolve the vegetation-removal problem.

---

## Experiment 2 — GHSL temporal-change analysis

### Objective

The second experimental direction evaluated whether comparing **multiple GHSL epochs** could provide useful contextual information for the Brasília pilot.

The aim was not to generate final favela labels from temporal change directly, but to assess whether built-up evolution across time could help explain mismatch between official polygons and single-epoch GHSL support.

### Rationale

A weak overlap between a polygon and a single GHSL raster does not necessarily imply that the polygon is incorrect. It may also reflect:

- temporal mismatch between data sources,
- urban growth between epochs,
- differences in product behavior,
- or limitations in the representation of built-up structure.

A temporal-change workflow was therefore introduced to help distinguish stable from unstable built-up support.

### Method summary

The temporal analysis compared two GHSL rasters for Brasília and generated:

- growth areas,
- loss areas,
- persistence areas,
- and supporting intermediate masks.

The comparison required alignment to a common grid and conversion of the rasters into binary built-up representations before change categories could be computed.

### Main observations

The temporal experiment was useful for interpretation, especially in highlighting that:

- persistent built-up areas may provide stronger contextual support than a single epoch alone,
- some apparent disagreement may be related to temporal or product differences rather than simple label error,
- and growth/loss maps require careful interpretation because they may also reflect resolution or threshold effects.

### Interim conclusion

GHSL temporal change proved useful as a **diagnostic experiment**, particularly for contextual understanding and QC. However, it was not sufficient as a standalone refinement method and is best treated as supporting evidence rather than direct label truth.

---

## Experiment 3 — MapBiomas pilot

### Objective

The third experimental direction evaluated whether **MapBiomas alone** could support conservative refinement of official favela polygons in Brasília.

The main question was whether a land-cover product could provide enough information to:

- identify vegetation that should be removed,
- preserve anthropic or built-up areas,
- and serve as a simpler first operational baseline than immediate NDVI-based processing.

### Rationale

Initially, vegetation removal was expected to rely on Sentinel-2-derived indices such as NDVI. However, the practical burden of selecting appropriate images, handling clouds, and ensuring preprocessing consistency made that path less suitable as the immediate pilot.

MapBiomas was therefore introduced as a more operational alternative, since it already provides land-cover classes that can be grouped into vegetation-like, anthropic, and uncertain categories.

### Method summary

The MapBiomas pilot was designed to:

1. clip a suitable MapBiomas raster to the Brasília AOI,
2. inspect its legend and class values,
3. group the classes into simplified refinement-relevant categories,
4. create binary vegetation and anthropic support masks,
5. apply conservative refinement rules to the official polygons,
6. compare the refined results with the originals.

### Expected strengths

MapBiomas is promising because it may support:

- direct vegetation-related interpretation,
- simpler first-pass operational testing,
- and a refinement logic more directly linked to the observed problem of vegetation inside or around noisy polygon margins.

### Expected limitations

At the same time, several limitations must be considered:

- land-cover classes may be too coarse for precise boundary editing,
- true settlement areas may contain internal vegetation,
- and direct land-cover-based clipping may distort polygon shape if used too aggressively.

### Interim conclusion

The MapBiomas pilot is a critical experiment because it tests whether a land-cover product alone can support a practical and conservative first-pass refinement baseline. Its outcome will determine whether the project can proceed with a single-source vegetation-removal strategy or whether multi-source fusion becomes necessary.

---

## Comparative interpretation of the experiments

Taken together, the experiments reveal that different evidence sources serve different methodological roles.

- **GHSL** is more directly useful as built-up support.
- **Temporal GHSL change** is more useful as contextual interpretation.
- **MapBiomas** is more directly useful for vegetation-related refinement logic.

This suggests that the refinement problem may not be best solved by a single universal source. Instead, the most promising direction may involve assigning different sources different roles within a conservative refinement workflow.

For example:

- a land-cover source may propose areas for vegetation removal,
- a built-up source may protect plausible settlement areas,
- temporal evidence may explain uncertainty or disagreement.

This interpretation motivates the future exploration of **multi-source fusion**.

---

## Experimental design principles learned from the pilot

Several general lessons emerge from these experiments.

### 1. Conservative refinement is preferable to redelineation
The official polygons are imperfect, but they still remain the most important starting point. Replacing them directly with sparse or coarse auxiliary masks is too risky.

### 2. Boundary-aware logic is important
The main errors often appear at polygon margins rather than across the entire polygon interior. This makes boundary-constrained editing an attractive strategy.

### 3. Interpretability matters
A refinement rule is more useful when it is understandable and inspectable, especially during the pilot phase.

### 4. Single-source sufficiency should be tested before fusion
It is methodologically cleaner to first evaluate whether one source is sufficient on its own before moving to more complex fusion logic.

### 5. Auxiliary evidence should be role-specific
Different layers are not interchangeable. Some are better suited for vegetation removal, others for built-up protection, and others for temporal interpretation.

---

## Limitations of the experimental stage

The experimental phase also has several limitations that should be acknowledged.

First, the Brasília pilot is only one study area. Results obtained there may not generalize immediately to all Brazilian urban contexts.

Second, the evaluation is currently focused on methodological and visual plausibility rather than on a large manually validated ground-truth benchmark.

Third, auxiliary raster products differ in resolution, time period, semantics, and spatial behavior, which complicates direct comparison.

Finally, the refinement problem itself is inherently ambiguous: a favela polygon may contain mixtures of roofs, bare soil, vegetation, and anthropic surfaces, so no single auxiliary source should be interpreted as perfect truth.

---

## Current overall conclusion

The experiments conducted so far suggest that the refinement problem is best approached as a **modular evidence-based task** rather than a single fixed raster operation.

The current findings support the following interpretation:

- GHSL is valuable as a built-up baseline,
- temporal GHSL change is valuable for diagnosis and contextual understanding,
- MapBiomas is promising for vegetation-related refinement,
- and a future multi-source strategy may be required if no single source proves sufficiently robust alone.

This experimental chapter therefore supports the broader methodological shift of the project from a purely GHSL-centered pilot to a comparative refinement framework.

---

## Next experimental direction

The next major step is to determine whether **MapBiomas alone** is sufficient for a first operational baseline in Brasília.

If not, the most likely next experiment will be a **multi-source fusion workflow**, for example:

- MapBiomas for vegetation removal,
- GHSL for built-up protection,
- and temporal GHSL outputs as contextual support.

This progression follows directly from the lessons learned in the current experimental phase.