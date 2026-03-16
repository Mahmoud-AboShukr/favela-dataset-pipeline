# MapBiomas Refinement

## Purpose

This page documents the pilot workflow for using **MapBiomas** as an auxiliary evidence source to refine official favela polygons in the Brasília study area.

The purpose of this pilot is to test whether **MapBiomas alone** can provide enough information to:

- identify vegetation that should be removed from noisy polygon margins,
- provide a useful anthropic or built-up proxy,
- and support conservative refinement without immediately depending on NDVI calculation or additional settlement layers.

This pilot is intended as an operational baseline experiment for the current stage of the project.

---

## Role in the project

The MapBiomas pilot is part of the broader label-refinement stage.

It is being evaluated as a practical alternative to a first refinement workflow based on directly computed vegetation indices from Sentinel-2. In the current project phase, this is useful because Sentinel-based NDVI computation can be complicated by cloud contamination, image selection, and preprocessing requirements.

MapBiomas is therefore being tested as a simpler initial source of:

- vegetation evidence,
- anthropic or urban support,
- and land-cover context for conservative polygon trimming.

At this stage, the main question is:

> Can MapBiomas alone provide a sufficiently robust first refinement baseline for Brasília?

---

## Why MapBiomas is being tested

MapBiomas was selected for the pilot because it may provide a practical way to identify non-settlement land cover without requiring immediate cloud-sensitive optical preprocessing.

The main motivations are:

- it provides ready-to-use thematic land-cover classes,
- it may help identify vegetation inside or around official polygons,
- it may also offer anthropic or urban classes that can help preserve plausible settlement areas,
- it is operationally simpler to test in the short term than a full NDVI-based workflow.

This makes it a good pilot candidate for answering whether a land-cover-based refinement approach is sufficient on its own.

---

## General refinement objective

The MapBiomas pilot does **not** aim to redraw favela polygons from scratch.

Instead, the objective is to:

- keep the official polygon as the main label source,
- remove clearly non-settlement vegetation where appropriate,
- preserve realistic built-up or anthropic portions of the polygon,
- and test whether a land-cover product can support conservative refinement.

The expected outcome is a cleaner polygon or raster mask that removes obvious vegetation-dominated areas without severely damaging settlement geometry.

---

## Inputs

The MapBiomas pilot takes as input:

- cleaned official favela polygons,
- the Brasília pilot AOI,
- one selected MapBiomas raster product for the same study area and year.

Depending on the exact dataset chosen, the MapBiomas raster may contain multiple land-cover classes relevant to refinement.

The pilot should document:

- the MapBiomas collection or product used,
- the year selected,
- the class legend,
- the raster resolution,
- and any clipping or reprojection steps required.

---

## Main idea

The central idea of the MapBiomas pilot is to transform land-cover classes into simpler refinement evidence layers.

In practice, the raster classes are grouped into three broad categories:

### 1. Vegetation-like classes
These are classes considered candidates for removal when they occur in suspicious parts of a polygon, especially near the boundary.

Examples may include:
- forest,
- shrub vegetation,
- grassland,
- other strongly vegetated cover types.

### 2. Anthropic or built-support classes
These are classes considered evidence that an area should probably be preserved rather than removed.

Examples may include:
- urban infrastructure,
- anthropic occupation,
- built-up or developed surfaces.

### 3. Uncertain or neutral classes
These are classes that do not provide sufficiently strong evidence either for removal or for preservation.

Such classes may be left unchanged in the first pilot version.

---

## Expected refinement logic

The MapBiomas pilot is intended to use a **conservative refinement logic**.

Rather than replacing the polygon geometry directly with land-cover classes, the preferred approach is:

1. start from the official polygon,
2. rasterize the polygon on the chosen analysis grid,
3. derive a vegetation mask from MapBiomas classes,
4. derive an anthropic or built-support mask from MapBiomas classes,
5. apply a conservative removal rule,
6. postprocess the output,
7. compare the refined result against the original.

The key principle is that **MapBiomas provides evidence**, not a complete replacement geometry.

---

## Conservative rule design

The first MapBiomas pilot should remain simple and interpretable.

A good first conservative rule is:

- preserve the polygon interior,
- allow edits mainly at the outer margin,
- remove areas classified as vegetation when they appear to be obvious non-settlement parts of the polygon,
- preserve areas classified as anthropic or urban support,
- leave uncertain classes unchanged.

This approach reduces the risk of over-trimming and keeps the experiment easy to interpret.

---

## Possible refinement variants

The pilot may compare more than one MapBiomas-based refinement rule.

### Variant A — vegetation-only trimming
- remove only vegetation-class pixels from editable parts of the polygon
- keep everything else unchanged

This is the simplest baseline.

### Variant B — vegetation removal with anthropic protection
- remove vegetation-class pixels
- explicitly preserve anthropic or urban-class pixels
- leave uncertain pixels unchanged

This is likely a better practical baseline if the class legend provides useful anthropic categories.

### Variant C — stricter conservative refinement
- remove vegetation only in a boundary band
- preserve the polygon core
- use anthropic classes as protective support

This is often the safest version for maintaining shape realism.

---

## Boundary-aware use

Because land-cover classes can be noisy or coarse, the MapBiomas pilot is better suited to **boundary-aware refinement** than to direct polygon replacement.

This means:

- the polygon interior should remain largely protected,
- the outer boundary should be the main editable zone,
- and class-based removal should be applied conservatively where there is strong evidence of vegetation.

This design is especially important because informal settlements may legitimately contain some internal vegetation, bare soil, or mixed land-cover patterns.

---

## Outputs

The MapBiomas pilot is expected to generate several outputs, such as:

- a Brasília-clipped MapBiomas raster,
- a binary vegetation mask,
- a binary anthropic or built-support mask,
- one or more refined raster masks,
- optionally refined vector polygons,
- QC plots or overlays for inspection.

These outputs should be stored in the same general refinement workflow structure used elsewhere in the project.

---

## Evaluation criteria

The pilot should assess whether MapBiomas alone is:

- sufficient as a standalone refinement source,
- partially useful but incomplete,
- or insufficient without support from another source such as GHSL or WSF.

Evaluation should combine both visual and simple quantitative checks.

### Visual checks
The refined output should be inspected against:

- the original polygon,
- the MapBiomas classes,
- any available high-level contextual imagery or overlays.

Key questions include:

- are obvious vegetation margins being removed?
- are realistic settlement regions being preserved?
- are polygon shapes still plausible?
- is the result too aggressive or too weak?

### Quantitative checks
Useful pilot metrics may include:

- total area before vs after refinement,
- number of polygons modified,
- percentage of area removed,
- proportion of removed pixels belonging to vegetation classes,
- comparison across two or more rule variants.

---

## Decision outcomes

At the end of the pilot, the method should support one of three conclusions:

### 1. Sufficient alone
MapBiomas can be used as the main initial refinement evidence source for Brasília and possibly later scaling.

### 2. Useful but incomplete
MapBiomas is good for vegetation removal, but another source is still needed for built-up protection or settlement support.

### 3. Insufficient alone
MapBiomas should be retained only as an auxiliary evidence source within a future multi-source fusion workflow.

---

## Limitations

The MapBiomas pilot has several limitations.

### Class ambiguity
Some land-cover classes may not separate settlement and vegetation cleanly enough at the polygon scale.

### Resolution and thematic granularity
The MapBiomas resolution and class taxonomy may not perfectly match the geometric detail needed for boundary refinement.

### Internal vegetation
Favela polygons may contain real vegetation inside valid settlement areas, so vegetation-like classes should not automatically imply removal everywhere.

### Boundary sensitivity
A direct class-based trim may damage polygon shape if applied too aggressively.

### Temporal mismatch
The selected MapBiomas year may not perfectly align with the date of the official polygon delineation or other auxiliary products.

For these reasons, the pilot is designed as a conservative experiment rather than a final fixed solution.

---

## Position relative to other methods

The MapBiomas pilot complements other methods in the project.

Compared with GHSL-based refinement:
- MapBiomas focuses more directly on land-cover interpretation,
- while GHSL focuses more directly on built-up evidence.

Compared with temporal GHSL analysis:
- MapBiomas is intended for direct refinement support,
- while temporal analysis is mainly diagnostic and interpretive.

Compared with future multi-source fusion:
- MapBiomas may eventually become one component in a combined rule set, especially for vegetation removal.

---

## Recommended use in the Brasília pilot

Within the Brasília pilot, MapBiomas should initially be used to answer a practical methodological question:

> can a land-cover-based source alone remove obvious vegetation from noisy favela polygons while preserving a plausible settlement footprint?

The first implementation should favor simplicity, interpretability, and conservative shape preservation over aggressive correction.

---

## Related files

This method is associated with:

- the cleaned polygon inputs in `data/interim/polygons_clean/`
- the Brasília AOI in `data/interim/aoi/`
- future MapBiomas clips and masks to be stored in `data/interim/`
- refinement scripts in `src/labels/` and/or future `src/mapbiomas/` utilities if added

Experiment-specific outputs and conclusions should be documented in:

- `experiments/`
- `status/`
- and relevant decision records.

---

## Related method pages

See also:

- [Label Refinement](label_refinement.md)
- [GHSL Refinement](ghsl_refinement.md)
- [Temporal Change Analysis](temporal_change_analysis.md)
- [Multi-source Fusion](multi_source_fusion.md)