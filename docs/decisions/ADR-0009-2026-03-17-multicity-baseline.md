# ADR — Frozen baseline for multicity MapBiomas transfer test

## Status
Accepted

## Date
2026-03-17

## Objective
Freeze the exact Brasília refinement baseline before scaling the pipeline to 5 cities, so that transferability is evaluated against a stable reference rather than a changing workflow.

## Reference city
Brasília

## Study area
- City: Brasília
- Favela polygons used: `data/interim/polygons_clean/favelas_brasilia.gpkg`
- Number of original polygons: 72

---

## Baseline A — 30 m MapBiomas pilot (proof of concept)

### Frozen input
- Clipped raster: `data/interim/mapbiomas_clips/mapbiomas_brasilia_aoi_clip.tif`
- Strict vegetation mask: `data/interim/masks/brasilia_mapbiomas_vegetation_mask_strict.tif`
- Built mask: `data/interim/masks/brasilia_mapbiomas_built_mask.tif`

### Class composition inside original favela polygons
- Urban Area (24): 40,927 px (73.8235%)
- Savanna Formation (4): 5,761 px (10.3916%)
- Forest Formation (3): 3,961 px (7.1448%)
- Pasture (15): 2,343 px (4.2263%)
- Mosaic of Uses (21): 2,007 px (3.6202%)

### Frozen refinement logic
- Method: `no-ring V2.2 + fillholes_4px`
- Refined mask: `data/interim/masks/brasilia_favela_refined_mapbiomas_no_ring_v2_2_fillholes_4px.tif`

### Frozen QC metrics
- Original kept pixels: 55,439
- Refined kept pixels: 41,148
- Removed pixels: 14,293
- Kept ratio: 74.2221%
- Removed ratio: 25.7815%
- Approx. original area: 49,895,100 m²
- Approx. refined area: 37,033,200 m²
- Approx. removed area: 12,863,700 m²
- Refined polygon piece count: 86
- Changed polygons: 58 / 72
- Strongly changed polygons (>= 20% removed): 37 / 72

### Interpretation
- The 30 m run established that MapBiomas can act as a valid refinement source.
- The result was visually strong but somewhat aggressive near vegetation edges.
- This run serves as the proof-of-concept baseline before moving to 10 m.

---

## Baseline B — 10 m MapBiomas pilot (current preferred baseline)

### Frozen input
- Clipped raster: `data/interim/mapbiomas_10m_clips/mapbiomas_10m_brasilia_aoi_clip.tif`
- Strict vegetation mask: `data/interim/masks/brasilia_mapbiomas_10m_vegetation_mask_strict.tif`
- Built mask: `data/interim/masks/brasilia_mapbiomas_10m_built_mask.tif`

### Class composition inside original favela polygons
- Urban Area (24): 346,671 px (69.4918%)
- Forest Formation (3): 39,035 px (7.8247%)
- Savanna Formation (4): 35,977 px (7.2118%)
- Pasture (15): 33,684 px (6.7521%)
- Other Non Vegetated Areas (25): 32,212 px (6.4570%)

### Frozen refinement logic
- Method: `no-ring V2.2 + fillholes_9px`
- Final vector candidate for review: dissolved 10 m refined output

### Frozen QC metrics
- Original kept pixels: 498,866
- Refined kept pixels: 346,803
- Removed pixels: 152,063
- Kept ratio: 69.5183%
- Removed ratio: 30.4817%
- Approx. original area: 49,886,600 m²
- Approx. refined area: 34,680,300 m²
- Approx. removed area: 15,206,300 m²
- Refined polygon piece count: 153
- Changed polygons: 64 / 72
- Strongly changed polygons (>= 20% removed): 37 / 72

### Interpretation
- The 10 m run is the current preferred Brasília baseline.
- It is slightly more aggressive quantitatively than the 30 m run, but visually it preserves the settlement footprint more faithfully and reduces coarse boundary errors.
- The dissolved 10 m output is the best candidate currently available for review and for multicity transfer testing.

---

## Baseline decision

For scale-up, the recommended Brasília reference baseline is:

- **Preferred operational baseline:** 10 m MapBiomas, `no-ring V2.2`, `fillholes_9px`, dissolved output
- **Reference proof-of-concept baseline:** 30 m MapBiomas, `no-ring V2.2`, `fillholes_4px`

This preserves both:
1. the original proof-of-concept result at 30 m, and
2. the current preferred operational baseline at 10 m.

---

## Transfer-testing rule
For the first multicity experiment:
- the 10 m Brasília baseline is the frozen operational reference,
- all target cities must use the same logic unchanged,
- no city-specific tuning is allowed in the first pass,
- any later change must be documented as a new decision after the multicity comparison.

## Consequences
- The first multicity benchmark measures transferability, not local optimization.
- Any later adjustment to vegetation masking, built support, hole filling, or dissolve logic must be tested as a controlled modification against this frozen baseline.
- City-by-city results must be compared against the frozen Brasília 10 m reference.