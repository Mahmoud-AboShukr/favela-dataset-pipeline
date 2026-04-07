# Validate Outputs

## Purpose

This page describes how to validate the outputs of the Brazil-scale favela refinement pipeline after running the main stages.

The current pipeline produces outputs at two levels:

- chunk level
- Brazil-wide merged level

Validation at this stage is mainly focused on:

- spatial alignment,
- geometric consistency,
- expected refinement behavior,
- and practical usability of the resulting polygons.

---

## Validation philosophy

The pipeline has already been executed successfully at national scale, which means the engineering workflow is operational. However, successful execution is not by itself sufficient to validate label quality.

Validation must therefore check whether the outputs are:

- spatially aligned,
- semantically reasonable,
- not overly aggressive,
- not too permissive,
- and still useful as final refined labels.

---

## Main files to inspect

### Per chunk

For any representative chunk, the most important files are:

#### Prepared inputs
- `prepared/mapbiomas.tif`
- `prepared/ghsl.tif`
- `prepared/worldcover.tif`
- `prepared/favela_mask.tif`
- `prepared/favelas.gpkg`
- `prepared/chunk_geom.gpkg`

#### Refined rasters
- `refined/refined_mask.tif`
- `refined/refined_mask_clean.tif`

#### Polygon outputs
- `polygonized/refined_raw.gpkg`
- `polygonized/refined_dissolved.gpkg`

#### QC summaries
- `polygonized/qc_metrics.json`
- `polygonized/qc_metrics.csv`

---

## Recommended validation workflow in QGIS

### Step 1 — Open a representative chunk
Choose a chunk that is likely to be informative, for example:

- a dense urban chunk,
- a sparse chunk,
- a chunk with strong surrounding vegetation,
- or a chunk near raster tile boundaries.

### Step 2 — Load these layers in QGIS
Load the following for that chunk:

- `prepared/chunk_geom.gpkg`
- `prepared/favelas.gpkg`
- `prepared/mapbiomas.tif`
- `prepared/ghsl.tif`
- `prepared/worldcover.tif`
- `prepared/favela_mask.tif`
- `refined/refined_mask_clean.tif`
- `polygonized/refined_raw.gpkg`
- `polygonized/refined_dissolved.gpkg`

### Step 3 — Check geometric alignment
Confirm that:

- all rasters overlap the same local area,
- the favela polygons match the favela raster mask,
- the refined mask aligns with the prepared rasters,
- the polygon outputs align with the refined raster.

This checks whether Stage 1 alignment and later stages remained consistent.

---

## What to check visually

### 1. Preservation of likely built-up favela areas
Check whether clear built-up areas inside the original favela extent are still preserved in the refined output.

Questions to ask:

- Are obvious built-up zones still present?
- Did the refinement remove too much from dense favela interiors?
- Are urban edges still coherent?

### 2. Vegetation suppression
Check whether vegetation spillover has been reduced without over-pruning true target areas.

Questions to ask:

- Are obvious vegetation areas removed?
- Are green or wetland edges still incorrectly included?
- Is the result too aggressive in mixed urban-vegetation zones?

### 3. Behavior of uncertain areas
Since MapBiomas uncertain class 25 is only kept when supported by GHSL, inspect whether the uncertain edge behavior looks reasonable.

Questions to ask:

- Are uncertain built-up edges kept where they should be?
- Are uncertain areas removed where they should not remain?
- Does the GHSL support appear too strict or too permissive?

### 4. Morphological cleanup
Inspect whether the small-object removal and hole-filling are behaving well.

Questions to ask:

- Are small noisy fragments removed?
- Are important small structures being lost?
- Are holes filled appropriately without over-smoothing the output?

### 5. Polygonization quality
Inspect both raw and dissolved polygon outputs.

Questions to ask:

- Does `refined_raw.gpkg` follow the raster correctly?
- Does `refined_dissolved.gpkg` merge pieces sensibly?
- Are there obvious fragmentation problems?
- Are polygons clipped correctly to the chunk extent?

---

## Recommended sample strategy

Do not validate only one chunk.

A useful minimum sample is:

- 1 dense urban chunk
- 1 sparse chunk
- 1 vegetation-heavy chunk
- 1 chunk with multiple raster tiles
- 1 chunk near the edge of the national favela distribution

This gives a much more informative picture of whether the logic generalizes.

---

## QC files to inspect

Each chunk includes:

- `polygonized/qc_metrics.json`
- `polygonized/qc_metrics.csv`

The most useful fields are typically:

- source polygon count
- refined raw polygon count
- refined dissolved polygon count
- source area
- refined area
- refined-to-source area ratio

These help detect chunks where the refinement may be unusually aggressive or unusually permissive.

---

## Brazil-wide validation after merge

After running the Brazil merge step, inspect:

- `data/processed/final_pipeline_scale_up/brazil_refined_raw.gpkg`
- `data/processed/final_pipeline_scale_up/brazil_refined_dissolved.gpkg`

At this level, the most important remaining checks are:

- chunk-boundary duplication,
- overlap consistency,
- overall geometry validity,
- and readiness for downstream dataset construction.

---

## Signs that the refinement is working well

The output is behaving well when:

- obvious built-up areas are preserved,
- vegetation spillover is reduced,
- the refined footprint remains coherent,
- raw polygons follow the raster cleanly,
- dissolved polygons remain interpretable,
- and results are consistent across different urban contexts.

---

## Signs that parameter tuning may still be needed

Revisit the refinement parameters if you observe:

- large loss of valid built-up area,
- too much fragmentation,
- too much residual vegetation,
- over-dependence on GHSL support,
- or repeated chunk-boundary artifacts.

---

## Current project position

At this point, the engineering side of the refinement pipeline is complete. Validation is therefore the bridge between:

- completed national label refinement,
- and the next project phase of satellite-image processing and dataset construction.