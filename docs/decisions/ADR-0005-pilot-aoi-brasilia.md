# ADR-0005 — Pilot AOI definition (Brasília / Distrito Federal)

**Status:** Accepted  
**Date:** 2026-03-09  
**Decision owner:** Project team (validated with managers)

## Context
For the pilot, we must define an AOI that is strict and reproducible to avoid processing outside the intended region.

## Decision
We define the pilot AOI as the **Distrito Federal administrative boundary from OpenStreetMap (OSM)**.
- AOI file: `data/interim/aoi/brasilia_boundary.gpkg`
- Layer: `brasilia_boundary`

All pilot processing (GHSL clipping, settlement mask creation, favela mask generation) is limited to this AOI.

## QC evidence (AOI coverage)
Using the cleaned Brazil-wide favela polygons (`favelas_clean.gpkg`), we computed coverage:

- Total cleaned polygon parts (after explode): **12741**
- Polygons intersecting AOI: **72**
- Polygons fully within AOI: **68**
- Polygons intersecting but not fully within (cross boundary): **4**
- Polygons excluded (no intersection with AOI): **12669**

QC script:
- `src/qc/qc_aoi_coverage.py`
Output:
- `reports/qc/stats/aoi_coverage_brasilia.csv`

## Implications
- Pilot results represent **Distrito Federal (OSM boundary)**, not necessarily a broader “Brasília metro area”.
- Polygons outside AOI are intentionally excluded for pilot scope control.
- If later required, we can extend AOI (OSM boundary + buffer) or switch to IBGE official boundaries.