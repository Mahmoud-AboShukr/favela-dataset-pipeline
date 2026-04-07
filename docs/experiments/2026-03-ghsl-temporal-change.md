# GHSL Temporal Change — Brasília Pilot

## Objective

This experiment evaluates whether **temporal comparison between two GHSL epochs** can provide useful contextual information for the Brasília pilot.

The main goal is **not** to generate final refined favela labels directly from temporal change. Instead, the experiment is intended to answer the following questions:

- can temporal GHSL comparison explain some mismatch between official polygons and single-epoch GHSL support?
- can persistent built-up areas provide stronger confidence than a single epoch alone?
- can growth or loss patterns help interpret apparent false negatives or ambiguous polygon boundaries?

This experiment is therefore treated as a **diagnostic and interpretive study** within the broader label-refinement workflow.

---

## Motivation

During the Brasília pilot, single-epoch GHSL evidence may appear too sparse or insufficient in some areas. A possible explanation is that:

- the official polygons and GHSL layers do not perfectly align in time,
- urban growth may have occurred between epochs,
- or differences in resolution and product behavior may affect local support.

To better understand this, a temporal change workflow was introduced to compare two GHSL rasters and derive spatial categories such as:

- growth,
- loss,
- persistence,
- and supporting binary masks.

The experiment helps determine whether temporal context adds useful interpretive value even if it is not directly used as the final refinement mask.

---

## Study area

The experiment is limited to the **Brasília pilot area**.

This is the same pilot AOI used for:

- official polygon subset extraction,
- GHSL clipping,
- settlement-mask experiments,
- and later MapBiomas testing.

Using the same pilot area ensures that temporal-change results can be compared directly with the existing refinement workflow.

---

## Inputs

The experiment compares two GHSL rasters for Brasília:

- `data/raw/ghsl/Brasilia_2018.tif`
- `data/raw/ghsl/Brasilia_2025.tif`

These rasters represent different GHSL epochs and may differ in:

- spatial resolution,
- built-up representation,
- product characteristics,
- and value interpretation.

Because of these differences, direct comparison is not meaningful without harmonization.

---

## Method summary

The temporal-change workflow follows these main steps:

1. load both GHSL rasters,
2. inspect CRS, extent, resolution, and nodata,
3. confirm valid spatial overlap,
4. harmonize the rasters onto a common analysis grid,
5. convert both epochs into binary built-up masks,
6. compute temporal change categories,
7. export intermediate and final outputs for inspection.

This workflow was implemented to support interpretation, not to replace the main refinement logic.

---

## Harmonization step

A key issue in this experiment is that the two GHSL rasters may not share the same:

- spatial resolution,
- raster grid,
- or shape.

To make comparison possible, one raster must be aligned to a chosen reference grid. This harmonization step includes:

- matching extent,
- matching transform,
- matching dimensions,
- and resampling where needed.

This is one of the most important parts of the experiment, because poor alignment can create artificial change patterns that do not reflect real built-up evolution.

---

## Binary change logic

After alignment, each GHSL raster is converted into a binary built-up mask.

Conceptually:

- `1` = built-up or settlement-supporting
- `0` = non-built

The temporal categories are then defined as follows:

### Growth
Pixels that are non-built in the earlier epoch and built in the later epoch.

### Loss
Pixels that are built in the earlier epoch and non-built in the later epoch.

### Persistence
Pixels that are built in both epochs.

These outputs are intended to show differences in built-up support over time, not to classify favela boundaries directly.

---

## Outputs

The experiment generates intermediate and final outputs in the temporal-change working area.

Typical outputs include:

- aligned or resampled raster intermediates,
- binary built-up masks for each epoch,
- `growth_2018_to_2025.tif`
- `loss_2018_to_2025.tif`
- `persistence_2018_to_2025.tif`

These outputs can then be inspected in QGIS and compared against:

- the official favela polygons,
- GHSL settlement masks,
- and later other evidence sources.

---

## Interpretation goals

The experiment is intended to support three kinds of interpretation.

### 1. Explaining disagreement with single-epoch GHSL
If a favela polygon is weakly supported by one epoch, temporal comparison may show whether built-up support appears stronger in another epoch.

### 2. Identifying stable built-up support
Persistent built-up areas across epochs may be more trustworthy than isolated support in only one raster.

### 3. Understanding urban evolution
Growth patterns may help explain why some peripheral or recently developed areas are poorly captured by a single GHSL snapshot.

---

## What this experiment does not do

This experiment does **not** aim to:

- produce the final refined favela mask,
- identify informal settlement directly,
- or replace the official polygons.

Built-up change is not the same as favela change. The outputs are therefore interpretive and contextual rather than definitive labels.

---

## Main limitations

Several limitations must be kept in mind when interpreting the results.

### Resolution mismatch
If the two epochs have different spatial resolutions, some apparent change may result from resampling rather than real urban transformation.

### Product inconsistency
Different GHSL products or epochs may behave differently even if both are treated as built-up evidence.

### Threshold sensitivity
The binary masks depend on how built-up support is defined, which can influence downstream growth/loss maps.

### Temporal ambiguity
A difference between epochs indicates change between two dates, but not the exact timing or cause of the change.

### Not settlement-specific
The outputs indicate built-up difference, not specifically favela formation, removal, or boundary correction.

For these reasons, the temporal outputs should always be interpreted together with the broader refinement workflow.

---

## Current conclusion

At the current stage of the Brasília pilot, GHSL temporal change is best treated as:

- a **diagnostic experiment**,
- a **supporting interpretation tool**,
- and a way to understand why single-epoch GHSL support may appear incomplete or inconsistent.

It is useful for analysis and QC, but not sufficient on its own as a polygon-refinement method.

---

## Next step

The next methodological question is whether temporal GHSL outputs should remain purely interpretive, or whether they can later contribute to a broader **multi-source fusion strategy** alongside:

- GHSL built-up support,
- MapBiomas vegetation evidence,
- and possibly other future auxiliary layers.

For now, the temporal-change experiment mainly strengthens the understanding of the Brasília pilot rather than directly modifying the labels.

---

## Related method pages

See also:

- [Temporal Change Analysis](../archive/legacy_methods/temporal_change_analysis_legacy.md)
- [Label Refinement](../methods/label_refinement.md)
- [GHSL Refinement](../archive/legacy_methods/ghsl_refinement_legacy.md)
- [Multi-source Fusion](../methods/multi_source_fusion.md)
