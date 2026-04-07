# Polygonization and QC

## Purpose

This page describes Stage 3 of the active Brazil-scale pipeline.

The purpose of this stage is to convert the cleaned refined raster into polygon outputs and compute basic per-chunk QC summaries.

This stage is important because the project deliberately preserves polygon outputs as a final usable product for review, comparison, and later downstream dataset construction.

---

## Why polygonization is needed

Although the refinement logic itself is raster-based, the final working format of the project is still polygon-oriented.

This is useful because:

- manual inspection is easier in vector form,
- correction workflows are easier with polygons,
- geometry-based QC is easier,
- later merging and dataset preparation are easier to organize.

---

## Inputs to Stage 3

For each chunk, Stage 3 reads:

- `refined/refined_mask_clean.tif`
- `prepared/favelas.gpkg`
- `prepared/chunk_geom.gpkg`

These provide:

- the cleaned refined binary mask,
- the source favela polygons,
- and the spatial boundary of the chunk.

---

## Main operations

### 1. Polygonize the refined mask
The cleaned binary raster is polygonized so that all connected foreground regions become vector geometries.

This produces the first vector version of the refined output.

### 2. Generate raw polygons
The polygonized output is stored as:

- `refined_raw.gpkg`

This is the direct vector version of the refined raster mask.

### 3. Assign source IDs
Each raw polygon is assigned to the source favela polygon with which it has the largest overlap.

This step links the refined polygons back to their original source polygons.

### 4. Dissolve by source polygon
After source assignment, the raw polygons are dissolved by source identifier.

This creates a cleaner per-source refined output:

- `refined_dissolved.gpkg`

### 5. Clip to chunk geometry
The polygon outputs are clipped to the chunk boundary as a final safety step.

### 6. Compute QC metrics
Basic per-chunk QC metrics are computed and saved.

---

## Outputs per chunk

Each chunk receives a `polygonized/` folder containing:

- `refined_raw.gpkg`
- `refined_dissolved.gpkg`
- `qc_metrics.json`
- `qc_metrics.csv`

---

## Raw vs dissolved outputs

### Raw polygons
The raw output is the direct polygonization of the refined raster.

It is useful because:

- it preserves the detailed connected components,
- it reflects the raster result more directly,
- it is useful for debugging and detailed inspection.

### Dissolved polygons
The dissolved output merges raw polygons by their assigned source polygon ID.

It is useful because:

- it is closer to the final intended label structure,
- it is easier to inspect,
- it is easier to compare to the source favela layer,
- it reduces fragmentation at the review stage.

Both outputs are intentionally preserved.

---

## Source assignment logic

The current source assignment strategy is overlap-based.

For each raw polygon:

- intersect it with source favela polygons,
- compute overlap area,
- assign the raw polygon to the source polygon with the largest overlap.

This is a practical and interpretable linking strategy for the current workflow.

---

## QC logic

The current Stage 3 does not generate a suspicious-flag layer.

Instead, it computes simple quantitative summaries such as:

- source polygon count,
- refined raw polygon count,
- refined dissolved polygon count,
- source area,
- refined area,
- refined-to-source area ratio.

This provides a lightweight QC layer without introducing a separate review-flag system.

---

## Area computation note

Area-based operations should not be computed directly in a geographic CRS.

The Stage 3 implementation was corrected so that overlap and area calculations use a projected CRS when necessary. This avoids misleading area values and removes warnings associated with area computation in latitude/longitude space.

---

## Bug encountered during development

During the first test of Stage 3, the script failed during clipping because it attempted to select fields from the chunk geometry layer that did not exist there.

This was fixed by simplifying the clipping operation so that clipping uses only the chunk geometry itself.

This fix was important because it made the national Stage 3 run stable.

---

## National execution status

After the fix, Stage 3 completed successfully across all 407 active chunks.

This confirms that:

- the refined raster masks were valid for polygonization,
- source assignment worked across the country,
- dissolved outputs could be generated consistently,
- and chunk-level QC summaries were produced successfully.

---

## Relationship to Stage 4 merge

Stage 3 remains chunk-based.

After all chunks are polygonized, Stage 4 merges chunk-level polygon outputs into Brazil-wide layers:

- `brazil_refined_raw.gpkg`
- `brazil_refined_dissolved.gpkg`

At that point, chunk-boundary consistency and possible deduplication become a later national-level concern.

---

## Why Stage 3 matters

Stage 3 is the bridge between:

- raster refinement logic,
- and final vector products that can be validated, reviewed, merged, and later aligned with imagery workflows.

It is therefore a central transition stage in the current project.