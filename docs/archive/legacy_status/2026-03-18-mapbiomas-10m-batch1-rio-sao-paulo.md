# Batch 1 status note — MapBiomas 10 m transfer test (Rio de Janeiro and São Paulo)

## Status
Completed

## Date
2026-03-18

## Objective
Evaluate whether the frozen Brasília 10 m MapBiomas refinement logic transfers to the first multicity benchmark pair:
- Rio de Janeiro
- São Paulo

The initial Batch 1 goal was to test transfer without city-specific tuning, using the Brasília 10 m workflow as the reference baseline.

---

## Frozen Brasília reference
- Preferred Brasília operational baseline:
  - 10 m MapBiomas
  - no-ring V2.2
  - fillholes_9px
  - dissolved output

For Batch 1, the core refinement logic remained aligned with the Brasília no-ring approach, but the preferred candidate was selected after side-by-side inspection of:
- remove-uncertain
- keep-uncertain

---

## Input preparation
### AOIs
Official municipality AOIs were extracted from IBGE municipal boundaries for:
- Rio de Janeiro
- São Paulo

### Favela subsets
City-specific favela subsets were extracted from the cleaned national favela layer.

Counts:
- Rio de Janeiro: 838 intersecting polygons
- São Paulo: 1439 intersecting polygons

### MapBiomas 10 m city clips
10 m MapBiomas was clipped to both city AOIs and validated successfully.

---

## Class composition inside original favela polygons

### Rio de Janeiro
Top classes inside favela polygons:
- Urban Area (24): 90.29%
- Mosaic of Uses (21): 6.01%
- Forest Formation (3): 1.89%
- Pasture (15): 0.75%

### São Paulo
Top classes inside favela polygons:
- Urban Area (24): 88.79%
- Class 0 / unknown: 5.17%
- Mosaic of Uses (21): 3.69%
- Forest Formation (3): 1.72%

### Interpretation
In both cities, Urban Area remained overwhelmingly dominant inside the favela polygons. This was a stronger urban signal than in the Brasília pilot, where the favela polygons had a more mixed class composition. This indicated that Batch 1 was suitable for transfer testing.

---

## Batch 1 mask logic
### Built classes
- Urban Area (24)

### Strict vegetation classes
- Forest Formation (3)
- Savanna Formation (4)
- Mangrove (5)
- Floodable Forest (6)
- Wetland (11)
- Grassland Formation (12)
- Wooded Sandbank Vegetation (49)
- Herbaceous Sandbank Vegetation (50)

### Mask summary
#### Rio de Janeiro
- Vegetation pixels: 3,806,346 (13.0942%)
- Built pixels: 6,219,815 (21.3968%)

#### São Paulo
- Vegetation pixels: 4,648,693 (12.4721%)
- Built pixels: 9,453,733 (25.3636%)

---

## Refinement variants tested
Two no-ring variants were considered:
- V2.1 keep-uncertain
- V2.2 remove-uncertain

A small fillholes_5px post-processing test was also run on the remove-uncertain output, but the effect was minimal:
- Rio: +121 pixels
- São Paulo: +56 pixels

This showed that the main decision factor was not hole filling but the treatment of uncertain pixels.

---

## Selected Batch 1 candidate
### Preferred candidate
- no-ring V2.1 keep-uncertain

### Reason
A quick visual comparison indicated that keeping uncertain pixels better preserved the settlement footprint and avoided overly aggressive trimming. The remove-uncertain variant appeared unnecessarily restrictive for Batch 1.

---

## Polygonization outputs

### Rio de Janeiro
- Raw refined pieces: 820
- Dissolved output rows: 1

### São Paulo
- Raw refined pieces: 1227
- Dissolved output rows: 1

The dissolved output was expected to contain one multipart feature per city because all retained pieces were dissolved together.

---

## QC summary for keep-uncertain candidate

### Rio de Janeiro
- Original polygon count: 838
- Raw piece count: 820
- Original kept pixels: 643,295
- Refined kept pixels: 628,682
- Removed pixels: 14,613
- Kept ratio: 97.7284%
- Removed ratio: 2.2716%
- Original vector area: 59,853,133.49 m²
- Refined vector area: 58,486,405.15 m²

### São Paulo
- Original polygon count: 1439
- Raw piece count: 1227
- Original kept pixels: 735,676
- Refined kept pixels: 722,867
- Removed pixels: 12,809
- Kept ratio: 98.2589%
- Removed ratio: 1.7411%
- Original vector area: 67,778,513.29 m²
- Refined vector area: 66,398,461.77 m²

---

## Interpretation of Batch 1 QC
The keep-uncertain candidate produced a conservative refinement in both cities. Removal rates were low:
- Rio: 2.27%
- São Paulo: 1.74%

This is much less aggressive than the Brasília 10 m preferred baseline. The result suggests that, in highly urban-dominated cities such as Rio and São Paulo, the no-ring logic transfers well and that retaining uncertain pixels is preferable to avoid unnecessary loss of settlement footprint.

---

## Visual assessment
### Rio de Janeiro
The overview output remained coherent at city scale and did not show obvious large-scale over-trimming. The main remaining point for local inspection is the urban–vegetation edge, especially where settlements are close to forested slopes or coastal vegetation.

### São Paulo
The overview output remained highly coherent and visually stable. The result supports the interpretation that São Paulo is an easier transfer case than Brasília because of the very strong urban dominance inside the favela polygons.

### General note
The citywide overview figures are useful for context but are too coarse to serve as the final visual proof of improvement. Local examples should still be exported for:
- one clear improvement case
- one case requiring review

---

## Batch 1 decision
### Decision
Proceed to Batch 2 using:
- the same class logic,
- the same no-ring refinement framework,
- and **keep-uncertain as the preferred operational variant**.

### Rationale
- Urban Area strongly dominates inside favela polygons in both cities.
- The refined outputs are visually coherent at city scale.
- The keep-uncertain candidate preserves the settlement footprint better than the remove-uncertain candidate.
- No evidence of large-scale transfer failure was observed in Batch 1.

---

## Next step
Run Batch 2 on:
- Belo Horizonte
- Salvador

using the same workflow and the keep-uncertain operational choice, while continuing to monitor:
- vegetation-edge trimming
- fragmentation
- city-specific morphology differences