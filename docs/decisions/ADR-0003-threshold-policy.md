# ADR-0003 — Thresholding and postprocessing policy for GHSL-based label refinement

**Status:** Accepted  
**Date:** 2026-03-06  
**Decision owner:** Project team (validated with managers)

## Context
Official favela polygons may include non-favela regions (vegetation, open ground).  
We refine these labels using GHSL built-up evidence by applying a threshold rule and morphological cleanup.

However, GHSL products differ in:
- resolution (10 m vs coarser grids),
- value encoding (binary, percentage, scaled intensity, built-up surface),
- nodata handling.

We need a repeatable policy to select and justify thresholds and cleanup parameters, starting from the Brasília pilot and scaling state-by-state.

## Decision
### 1) Core refinement rule
For each processing unit (pilot AOI or state tile):
1) Rasterize polygons onto the reference grid → `P(x)` (0/1)
2) Convert GHSL to built-up mask using a threshold τ → `B(x)`
3) Produce refined mask:
- **`Y(x) = P(x) AND B(x)`**

### 2) Threshold selection strategy (τ)
We will choose τ using a **QC-driven procedure**:
- Start with an initial τ (low value) and generate a refined mask.
- Inspect overlays in QGIS (mask over GHSL + basemap/Sentinel preview).
- Record:
  - polygon pixels vs refined pixels,
  - qualitative outcomes (over-removal vs under-removal),
  - a small set of representative locations.
- Evaluate a small candidate set of thresholds and select the one that best removes clear non-built-up areas while preserving settlement fabric.

We will document the chosen τ **per GHSL product** (and if needed per region/state), along with evidence images and statistics.

### 3) Postprocessing policy
We will apply morphological cleanup to reduce noise:
- **Remove small connected components** below a minimum pixel size:
  - parameter: `min_component_pixels`
- Optional (only if QC shows benefit):
  - hole filling (small holes)
  - edge smoothing

Cleanup parameters must be logged alongside τ.

## Rationale
- GHSL value ranges are product-specific; thresholding must be empirical and justified by QC.
- A fixed global τ may not generalize perfectly across all Brazilian contexts; the policy allows controlled regional tuning while keeping decisions documented.
- Small-object removal prevents tiny noisy islands from becoming training labels.

## Implications
- Every refinement run should produce:
  - raw polygon mask,
  - refined mask,
  - pixel statistics,
  - 2–5 QC overlay screenshots saved in `reports/qc/overlays/`.
- Threshold and postprocessing parameters must be recorded in:
  - `docs/methods/label_refinement.md`
  - and optionally in `config/experiments/exp_*.yaml` for reproducibility.

## Alternatives considered
1) **No thresholding (use polygons only)**  
   - Rejected: known label noise (vegetation/open areas included)

2) **Vector-based intersection (convert GHSL to polygons and intersect)**  
   - Rejected for scaling: geometry explosion, slower, more fragile

3) **Single global τ without QC**  
   - Rejected: risk of systematic bias (over/under removal) and poor reproducibility justification in thesis

## Links / evidence
- Refinement method specification:
  - `docs/methods/label_refinement.md`
- QC evidence storage:
  - `reports/qc/overlays/`
- Scripts (pilot):
  - `src/ghsl/clip_ghsl_brasilia.py`
  - `src/labels/subtask3_refine_brasilia_with_ghsl.py` (planned/used in pilot)