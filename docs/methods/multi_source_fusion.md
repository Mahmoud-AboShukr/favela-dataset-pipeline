# Multi-source Fusion

## Purpose

This page describes the future-oriented strategy of combining multiple auxiliary evidence sources to refine official favela polygons more robustly than would be possible with any single source alone.

The motivation for multi-source fusion is simple:

- one source may be good at identifying vegetation,
- another may be better at indicating built-up support,
- another may help explain temporal mismatch,
- and combining them conservatively may produce better refinement results.

At the current stage of the project, multi-source fusion is a **planned methodological direction**, not yet the main operational baseline.

---

## Why fusion may be needed

The Brasília pilot is designed to test whether a single source can support conservative refinement on its own.

However, different data sources answer different questions:

- **MapBiomas** is useful for land-cover interpretation and vegetation-like classes,
- **GHSL** is useful for built-up or settlement-support evidence,
- **GHSL temporal derivatives** are useful for contextual interpretation of change,
- **WSF** or other future products may provide additional binary settlement support.

Because these sources are complementary, a fused method may be more reliable than a single-source approach.

---

## General idea

Multi-source fusion means combining several evidence layers into a single refinement decision process.

In this project, the general principle is:

- keep the **official polygon** as the backbone of the label,
- use different sources for different roles,
- and apply conservative rules that avoid aggressive geometric distortion.

The objective is not to build a perfect automatic truth mask, but to create a refinement workflow that is:

- interpretable,
- robust,
- conservative,
- and scalable.

---

## Source roles

A useful way to organize fusion is by assigning each source a specific role.

### 1. Geometry backbone
The official favela polygon remains the initial geometry to be refined.

### 2. Vegetation-removal evidence
A source that helps identify clearly non-settlement vegetated areas.

Examples:
- MapBiomas vegetation-related classes
- future NDVI or vegetation indices from Sentinel-2

### 3. Built-up protection evidence
A source that helps prevent valid settlement regions from being removed.

Examples:
- GHSL built-up support
- GHSL settlement masks
- future WSF support

### 4. Temporal context
A source that helps interpret disagreement across time.

Examples:
- GHSL growth/loss/persistence outputs

This role-based view is important because different layers should not all be treated as if they provide the same kind of evidence.

---

## Core fusion principle

The project’s preferred fusion logic is **asymmetric** rather than symmetric.

That means:

- vegetation-like evidence may suggest an area is removable,
- built-up evidence may protect an area from removal,
- temporal evidence may help interpret uncertainty,
- but no single layer should automatically replace the official polygon by itself.

A good conservative rule is therefore:

> remove only when non-settlement evidence is strong and protective built-up evidence is weak or absent.

This is safer than direct intersection or direct replacement approaches.

---

## Why conservative fusion is preferred

Conservative fusion is important because informal-settlement polygons may contain:

- internal vegetation,
- mixed land-cover types,
- fragmented built-up patterns,
- ambiguous margins,
- and temporal mismatch between vector labels and raster products.

If fusion is too aggressive, the result may:

- remove true settlement areas,
- fragment polygons,
- or produce unrealistic shapes.

For this reason, the project favors a workflow in which multiple sources improve the decision process without overriding the polygon too strongly.

---

## Example fusion patterns

Several fusion patterns are relevant to the project.

### Pattern 1 — MapBiomas + GHSL

This is currently the most natural fusion candidate.

A possible interpretation is:

- **MapBiomas** provides vegetation-removal evidence,
- **GHSL** provides built-up protection,
- the polygon is preserved unless vegetation evidence is strong and GHSL support is weak.

This combination is attractive because the two sources play complementary roles.

---

### Pattern 2 — MapBiomas + WSF

A future alternative may be:

- **MapBiomas** for vegetation detection,
- **WSF** for binary settlement support.

This could be useful if WSF is available and sufficiently informative for the area, especially as a high-confidence settlement-support layer.

---

### Pattern 3 — GHSL + temporal GHSL derivatives

Another pattern is to combine:

- one GHSL layer as current built-up evidence,
- temporal persistence as stronger support for stable built-up areas,
- and growth/loss patterns as contextual indicators.

This is more diagnostic than operational at present, but it may help define confidence rules.

---

### Pattern 4 — full multi-source fusion

In a more advanced version, the workflow could combine:

- official polygons,
- MapBiomas,
- GHSL,
- temporal GHSL context,
- and possibly WSF or Sentinel-derived indices.

This would allow different types of evidence to contribute to a more nuanced refinement rule.

---

## Conceptual fusion logic

A practical fusion workflow may follow this logic:

1. start from the official polygon,
2. rasterize the polygon on a common analysis grid,
3. generate evidence masks from each source,
4. assign each mask a role,
5. combine them using conservative decision rules,
6. postprocess the refined mask,
7. evaluate the result against QC criteria.

The exact fusion rule can vary, but the central design remains the same:
- one source proposes removal,
- another protects built-up areas,
- uncertainty is handled conservatively.

---

## Example rule families

### Rule family A — vegetation removal with built-up protection

A region is removed only if:

- vegetation evidence is strong,
- built-up protection is weak or absent,
- and the region lies in a suspicious part of the polygon, often near the boundary.

This is likely to be the most important fusion family in the current project.

---

### Rule family B — boundary-constrained fusion

The same logic as above, but edits are allowed only in an editable boundary band.

This version is especially useful when the priority is shape preservation.

A typical rule may be:

- preserve polygon core,
- evaluate only the outer ring,
- remove outer-ring pixels only if vegetation evidence is strong and built-up support is absent.

---

### Rule family C — score-based fusion

Instead of hard rules, each pixel or region can be assigned a score based on:

- vegetation evidence,
- built-up evidence,
- temporal persistence,
- distance to boundary,
- and connectivity to the polygon interior.

The final decision is then based on a threshold applied to the combined score.

This is flexible and systematic, but more complex and harder to interpret than a simple rule-based baseline.

---

## Common analysis grid

Any fused method requires a common spatial framework.

This means that all sources used in a fusion rule must be:

- clipped to the same AOI,
- reprojected as needed,
- aligned to the same raster grid,
- and interpreted at compatible resolution.

Without this step, apparent disagreement between sources may reflect technical misalignment rather than meaningful land-cover difference.

---

## Quality control for fusion

A fused result should be evaluated using the same principles as other refinement outputs.

### Visual QC
Inspect:

- original polygon,
- fused refined mask,
- each evidence source separately,
- and the areas that were removed or preserved.

### Quantitative QC
Useful metrics include:

- polygon area before and after refinement,
- overlap with built-up support,
- amount of vegetation removed,
- number of polygons strongly changed,
- comparison between fused and single-source variants.

Fusion should only be considered beneficial if it improves refinement quality without creating new shape or interpretation problems.

---

## Decision criteria

A multi-source fusion approach becomes justified when:

- no single source performs sufficiently well on its own,
- one source is clearly strong for vegetation but weak for built-up support,
- another source is clearly useful as a protective constraint,
- and the combination produces a more stable and interpretable result.

This means the project should move to fusion only after the single-source pilots have been tested and compared.

---

## Position in the project timeline

At the current stage of the project:

- GHSL is still a key baseline,
- MapBiomas is being tested as a standalone pilot,
- temporal GHSL analysis is being used diagnostically,
- multi-source fusion remains the next logical stage if a single-source method proves insufficient.

In other words, fusion is a **planned next step**, not the current default.

---

## Limitations

Multi-source fusion also introduces new challenges.

### Increased complexity
More sources mean more preprocessing, more alignment work, and more design decisions.

### Conflicting evidence
Different layers may disagree spatially, making rule design more difficult.

### Parameter tuning
Fusion rules may require thresholds, class mappings, weights, or boundary settings.

### Harder interpretation
A fused system is often less transparent than a simple single-source baseline.

For these reasons, fusion should be introduced gradually and documented carefully.

---

## Recommended future direction

If the Brasília pilot shows that no single source is sufficient alone, the most promising next step is likely:

### MapBiomas + GHSL
where:

- MapBiomas provides vegetation-removal evidence,
- GHSL provides built-up protection,
- refinement is restricted to conservative edits,
- and the official polygon remains the backbone.

This is currently the most natural and interpretable multi-source strategy for the project.

---

## Related method pages

See also:

- [Label Refinement](label_refinement.md)
- [Data Sources](data_sources.md)
- [GHSL Refinement](ghsl_refinement.md)
- [Temporal Change Analysis](temporal_change_analysis.md)
- [MapBiomas Refinement](mapbiomas_refinement.md)