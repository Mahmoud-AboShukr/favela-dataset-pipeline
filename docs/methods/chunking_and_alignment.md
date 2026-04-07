# Chunking and Alignment

## Purpose

This page explains why the current pipeline is chunked and how raster alignment is handled.

Chunking and alignment are fundamental to the current Brazil-scale workflow. Without them, the raster sources could not be combined safely and efficiently.

---

## Why chunking is necessary

The project operates at Brazil scale. Processing all rasters over the whole country in a single pass would create several problems:

- excessive memory use,
- unnecessarily large raster operations,
- difficulty rerunning failed processing,
- slower debugging,
- inefficient loading of tiles that do not intersect favela areas.

To avoid this, the pipeline uses a chunk-based strategy.

---

## Chunking strategy

The workflow:

1. loads the national favela polygon layer,
2. builds a regular chunk grid over the favela extent,
3. keeps only chunks that intersect favela polygons,
4. processes each active chunk independently.

This means the country is not processed as one monolithic raster operation, but as many smaller local operations.

---

## Practical benefits of chunking

Chunking provides:

- local tile selection,
- smaller raster windows,
- easier recovery from failures,
- easier testing on sample chunks,
- cleaner per-chunk outputs,
- and more scalable execution.

In the current national run, this strategy produced:

- **407 active chunks**

---

## Chunk contents

Each chunk becomes a self-contained local processing unit.

After Stage 1, each active chunk contains:

- local prepared rasters,
- local favela polygons,
- local chunk geometry,
- metadata describing the local inputs.

This makes later stages independent and easier to manage.

---

## Why alignment is necessary

The active raster sources do not naturally share the same CRS, tiling scheme, or raster grid.

This is especially important because:

- MapBiomas is used as a national thematic reference,
- GHSL is in a different CRS,
- WorldCover comes in tiled geographic coverage.

If these layers were used without harmonization, then:

- pixels would not correspond spatially,
- overlays would be inconsistent,
- the refinement logic would be unreliable.

---

## Active alignment principle

The current alignment strategy is:

- use **MapBiomas 10 m** as the master grid,
- align all other rasters to that grid within each chunk.

This means MapBiomas determines:

- the working raster extent per chunk,
- the raster shape,
- the affine transform,
- and the final pixel grid for Stage 2.

---

## Source-specific alignment behavior

### MapBiomas
MapBiomas is clipped to the local processing geometry and kept in its own grid as the reference.

### GHSL
GHSL is first clipped in its native form, then reprojected and aligned to the MapBiomas grid.

This is especially important because GHSL is in:

- `ESRI:54009`

and therefore cannot be combined directly with MapBiomas without reprojection.

### WorldCover
WorldCover is clipped and aligned to the MapBiomas grid using categorical-safe resampling.

---

## Resampling choices

The current logic uses different resampling behavior depending on source type.

### GHSL
GHSL is treated as a continuous or quasi-continuous support surface, so alignment uses a continuous-friendly resampling strategy.

### WorldCover
WorldCover is categorical, so alignment must preserve class identity. It is therefore aligned using a categorical-safe resampling strategy.

---

## Local processing geometry

Each chunk is not processed only as the exact grid cell itself.

Instead, the chunk geometry is buffered to define a local processing geometry. This helps avoid overly tight clipping and allows the local raster window to include the immediate context around the favela polygons.

---

## Favela rasterization

After the reference grid is established, the local favela polygons are rasterized onto the same MapBiomas-aligned grid.

This creates:

- `favela_mask.tif`

which later acts as the spatial constraint for refinement.

---

## Why this design matters

The current pipeline depends on pixel-wise logic. For example, Stage 2 compares:

- MapBiomas built/uncertain classes,
- GHSL support,
- WorldCover vegetation,
- favela-mask restriction.

This only works correctly if all layers are aligned to the same grid.

So alignment is not a technical detail; it is a central requirement of the method.

---

## Outputs created by alignment

After Stage 1, each chunk contains aligned local inputs:

- `mapbiomas.tif`
- `ghsl.tif`
- `worldcover.tif`
- `favela_mask.tif`

These become the inputs to the active refinement logic.

---

## Current status

The chunking and alignment workflow has already been executed successfully at national scale and produced prepared inputs for all 407 active chunks.