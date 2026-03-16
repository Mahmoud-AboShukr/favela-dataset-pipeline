# Status Note — 2026-03-13 — GHSL Temporal Change

## Objective

Today’s goal was to test whether comparing **two GHSL epochs over Brasília** could provide useful context for the polygon-refinement workflow.

The experiment was introduced to help answer whether mismatch between official favela polygons and GHSL support might be partly explained by:

- temporal urban growth,
- apparent loss,
- persistent built-up structure,
- or differences between GHSL products and epochs.

The temporal-change workflow was treated as a **diagnostic support experiment**, not as a direct label-generation method.

---

## Inputs used

The temporal comparison used the following GHSL rasters:

- `data/raw/ghsl/Brasilia_2018.tif`
- `data/raw/ghsl/Brasilia_2025.tif`

These rasters represent two different GHSL epochs for the Brasília study area.

Because the rasters differ in characteristics, the comparison required:

- metadata inspection,
- overlap verification,
- alignment to a common grid,
- and conversion to binary built-up masks before change computation.

---

## Work completed

The following steps were completed or prepared as part of the temporal-change workflow:

1. identified the two GHSL epoch rasters for Brasília,
2. confirmed that the analysis should be restricted to the Brasília pilot area,
3. prepared a comparison workflow to harmonize the rasters,
4. derived temporal categories for:
   - growth,
   - loss,
   - persistence,
5. generated experiment outputs in the temporal-change workspace,
6. clarified that the results should be interpreted as contextual built-up change rather than favela change.

---

## Outputs generated

The temporal-change experiment produced outputs in:

- `data/interim/temporal_change/`

Key outputs include:

- `growth_2018_to_2025.tif`
- `loss_2018_to_2025.tif`
- `persistence_2018_to_2025.tif`

Additional intermediate files may include:

- aligned or resampled versions of one epoch,
- binary built-up masks,
- and supporting debug rasters used during harmonization.

---

## Main observations

### 1. Temporal comparison is useful for interpretation
Comparing two GHSL epochs helps explain why a location may appear weakly supported in one raster but more strongly built-up in another.

### 2. Persistence is likely the most useful category
Persistent built-up support across epochs appears to be the most interpretable temporal signal for identifying stable urban structure.

### 3. Growth and loss require caution
Growth and loss maps may reflect real change, but they may also be influenced by:

- resolution mismatch,
- threshold sensitivity,
- resampling effects,
- or differences in product behavior.

### 4. Temporal change is not a direct refinement mask
The outputs are useful for diagnosing mismatch and understanding context, but they are not suitable as direct replacement labels for favela boundaries.

---

## Interpretation

At this stage, the temporal-change outputs are best interpreted as:

- **diagnostic evidence**
- **context for QC**
- **support for understanding disagreement between sources**

They should not be interpreted as:

- direct favela labels,
- exact settlement growth boundaries,
- or final refinement outputs.

The experiment strengthens understanding of the Brasília pilot, but does not by itself resolve the refinement problem.

---

## Limitations identified

The main limitations observed or expected in this experiment are:

- different raster resolutions between epochs,
- possible product inconsistency across GHSL versions,
- binary threshold sensitivity,
- temporal ambiguity between the two dates,
- and the fact that built-up change is not equivalent to favela change.

These limitations mean that temporal change should remain a supporting analysis layer rather than the main refinement source.

---

## Current conclusion

The current conclusion is that **GHSL temporal change is useful as a contextual and interpretive experiment**, especially for:

- diagnosing apparent GHSL false negatives,
- identifying stable built-up areas,
- and understanding urban evolution in the pilot area.

However, it is **not sufficient as a standalone polygon-refinement method**.

---

## Decision relevance

This status note supports the emerging methodological direction that:

- GHSL remains useful as built-up evidence,
- temporal GHSL outputs add interpretive value,
- and final refinement will likely require either:
  - a conservative single-source workflow, or
  - a future multi-source fusion strategy.

---

## Next actions

The recommended next steps are:

1. keep temporal GHSL analysis as a documented diagnostic method,
2. avoid treating temporal outputs as direct label truth,
3. continue the Brasília pilot with the **MapBiomas-only refinement experiment**,
4. later assess whether temporal persistence could contribute to a future fusion strategy.

---

## Related pages

- `methods/temporal_change_analysis.md`
- `experiments/2026-03-ghsl-temporal-change.md`
- `methods/ghsl_refinement.md`
- `methods/multi_source_fusion.md`