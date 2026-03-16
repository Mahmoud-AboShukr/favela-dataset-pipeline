# MapBiomas Pilot — Brasília

## Objective

This experiment evaluates whether **MapBiomas alone** can provide enough land-cover evidence to support conservative refinement of official favela polygons in the Brasília pilot.

The main question is:

> Can MapBiomas be used as a standalone first-pass refinement source to remove obvious vegetation from noisy polygon margins while preserving plausible settlement geometry?

The experiment is intentionally framed as a **pilot baseline**, not as a final production solution.

---

## Motivation

The project initially considered using vegetation indices such as **NDVI** from Sentinel-2 to detect vegetation inside or around official polygons. However, in practice this would require additional preprocessing steps such as:

- selecting suitable Sentinel-2 scenes,
- dealing with clouds and cloud shadows,
- and ensuring that the imagery is appropriate for the pilot period.

Following discussion with supervisors, the decision was made to first test **MapBiomas** as a more operational land-cover source.

This experiment therefore asks whether MapBiomas can provide:

- enough vegetation evidence to remove obvious false-positive vegetated areas,
- enough anthropic or built-up evidence to preserve plausible settlement regions,
- and a sufficiently interpretable baseline before introducing additional sources such as GHSL or WSF.

---

## Study area

The experiment is limited to the **Brasília pilot AOI**.

This is the same pilot area used throughout the project for:

- official polygon subset extraction,
- GHSL clipping and settlement-mask generation,
- temporal GHSL experiments,
- and the initial refinement workflow.

Keeping the MapBiomas pilot within the same AOI allows direct comparison with existing methods and outputs.

---

## Inputs

The experiment takes as input:

- the cleaned official favela polygons for Brasília,
- the Brasília AOI,
- one selected MapBiomas raster for the same area and year.

The exact MapBiomas source should be documented clearly when the experiment is executed, including:

- collection or product name,
- selected year,
- raster resolution,
- class legend,
- clipping and reprojection steps if needed.

---

## Experimental question

The pilot is designed to answer three practical questions:

1. Can MapBiomas identify vegetation inside or around official polygons well enough to support trimming of obvious non-settlement areas?
2. Can MapBiomas also provide a useful anthropic or built-up proxy to protect plausible settlement regions?
3. If used alone, does MapBiomas preserve realistic polygon shapes, or does it over-trim or under-trim too often?

These questions are important because the pilot is evaluating **MapBiomas as a standalone evidence source**, not yet as part of a fused workflow.

---

## Method summary

The experiment follows a conservative refinement logic rather than direct polygon replacement.

The general workflow is:

1. clip MapBiomas to the Brasília pilot AOI,
2. inspect the class values and legend,
3. group classes into simplified evidence categories,
4. rasterize the official polygons on a compatible grid,
5. generate binary evidence masks from MapBiomas,
6. apply one or more conservative refinement rules,
7. postprocess the outputs,
8. compare the refined result against the original polygons.

This workflow is intended to remain simple and interpretable during the pilot phase.

---

## Class grouping strategy

A core part of the experiment is simplifying the MapBiomas legend into a small number of refinement-relevant categories.

### 1. Vegetation-like classes
These classes are treated as candidates for removal when they occur in suspicious parts of a polygon.

Examples may include:
- forest,
- shrubland,
- grassland,
- or other strongly vegetated land-cover classes.

### 2. Anthropic or built-support classes
These classes are treated as evidence that an area should be preserved.

Examples may include:
- urban infrastructure,
- anthropic occupation,
- developed land,
- or other classes interpreted as settlement-supporting.

### 3. Uncertain classes
These classes do not provide strong evidence either for removal or preservation.

In the first pilot version, these classes should usually be left unchanged.

The exact mapping between MapBiomas classes and these simplified groups should be documented once the selected product is fixed.

---

## Refinement logic

The experiment does **not** use MapBiomas to redraw the favela polygons completely.

Instead, the preferred logic is conservative:

- the official polygon remains the main geometry,
- MapBiomas provides evidence for trimming or preserving parts of that geometry,
- and the refinement is applied in a way that tries to preserve realistic shape.

The most natural first refinement rules are:

### Variant A — vegetation-only trimming
- remove only vegetation-class pixels from editable parts of the polygon,
- leave everything else unchanged.

### Variant B — vegetation trimming with anthropic protection
- remove vegetation-class pixels,
- preserve anthropic or urban-support pixels,
- leave uncertain classes unchanged.

### Variant C — boundary-aware trimming
- preserve the polygon interior,
- edit only an outer boundary band,
- remove boundary pixels only where vegetation evidence is strong,
- preserve boundary pixels where anthropic support exists.

This third version is likely to be the safest if shape preservation becomes a major concern.

---

## Why a conservative design is preferred

MapBiomas is useful because it provides semantic land-cover classes, but it also has limitations.

A direct polygon replacement approach would be risky because:

- land-cover classes may be too coarse,
- settlements may contain internal vegetation,
- anthropic surfaces may be mixed with bare soil or vegetation,
- and direct class clipping may produce unrealistic boundaries.

For these reasons, the experiment is designed as a **conservative evidence-based refinement**, not a hard class mask replacement.

---

## Expected outputs

The experiment is expected to produce:

- a Brasília-clipped MapBiomas raster,
- a binary vegetation mask,
- a binary anthropic or built-support mask,
- one or more refined raster masks,
- optionally refined vector polygons,
- and QC overlays for visual inspection.

These outputs should be stored within the interim data and QC structure used for the rest of the project.

---

## Evaluation criteria

The pilot will judge MapBiomas according to both visual and simple quantitative criteria.

### Visual evaluation

The refined results should be inspected against:

- the original polygons,
- the MapBiomas classes,
- any available contextual imagery,
- and the known urban structure of the pilot area.

Important visual questions include:

- are obvious vegetation margins removed?
- are plausible settlement regions preserved?
- are the refined boundaries still realistic?
- are there signs of over-trimming or under-trimming?

### Quantitative evaluation

Useful summary indicators may include:

- total polygon area before vs after refinement,
- number of polygons changed,
- percentage of removed area,
- proportion of removed pixels belonging to vegetation classes,
- comparison between multiple rule variants.

These metrics are not intended to replace visual interpretation, but to support consistent comparison.

---

## Possible outcomes

The experiment is designed to support one of three conclusions.

### Outcome 1 — Sufficient alone
MapBiomas provides enough useful evidence to serve as the main first-pass refinement source for the Brasília pilot.

### Outcome 2 — Useful but incomplete
MapBiomas is effective for vegetation removal, but insufficient for built-up protection or full settlement support on its own.

In this case, it should be combined later with a source such as GHSL or WSF.

### Outcome 3 — Insufficient alone
MapBiomas does not support reliable standalone refinement and should be used only as one component within a broader multi-source workflow.

---

## Main limitations

Several limitations must be kept in mind during interpretation.

### Class ambiguity
Some MapBiomas classes may not separate settlement and vegetation cleanly enough for reliable boundary correction.

### Resolution limitations
The spatial detail may be insufficient for precise polygon-edge editing in all cases.

### Internal vegetation
Real settlement polygons may contain vegetation, so vegetation-like classes should not automatically imply removal everywhere.

### Temporal mismatch
The chosen MapBiomas year may differ from the timing of the official polygon delineation or other auxiliary layers.

### Shape sensitivity
Even if vegetation is correctly detected, direct trimming may still damage polygon shape if the rule is too aggressive.

For these reasons, the pilot must prioritize interpretability and conservative refinement.

---

## Current expected interpretation

At the current stage of the project, the MapBiomas pilot is best viewed as a **practical standalone baseline test**.

Its purpose is not to prove that MapBiomas is the final solution, but to determine whether it can:

- simplify the vegetation-removal problem,
- reduce dependence on immediate NDVI preprocessing,
- and provide a useful first refinement signal before multi-source fusion is introduced.

---

## Next step

If MapBiomas proves useful but incomplete, the next logical extension is a **multi-source fusion experiment**, most likely involving:

- MapBiomas for vegetation removal,
- GHSL for built-up protection,
- and potentially temporal GHSL products for interpretation.

If MapBiomas proves sufficient alone in the pilot, it may become the first operational refinement baseline before broader scaling.

---

## Related method pages

See also:

- [MapBiomas Refinement](../methods/mapbiomas_refinement.md)
- [Label Refinement](../methods/label_refinement.md)
- [Data Sources](../methods/data_sources.md)
- [Multi-source Fusion](../methods/multi_source_fusion.md)