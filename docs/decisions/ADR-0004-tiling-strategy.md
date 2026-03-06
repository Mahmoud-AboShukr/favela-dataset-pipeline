# ADR-0004 — Tiling strategy for pilot and scaling

**Status:** Accepted  
**Date:** 2026-03-06  
**Decision owner:** Project team (validated with managers)  

## Context
To scale dataset generation across Brazil, we need a tiling strategy that:
- supports efficient processing and parallelization,
- aligns with how we will manage data by administrative regions,
- produces DL-ready patches consistently.

## Decision
We will tile processing **by Brazilian state** as the primary unit of orchestration, and generate DL patches of:
- **Patch size:** `512 × 512` pixels

(“State” here defines the unit for batching downloads, indexing, and outputs; patching is performed within each state.)

## Rationale
- State-level partitioning is practical for managing compute and storage and matches management needs (“progress by state”).
- It enables parallel processing (state-by-state) and incremental scaling after the Brasília pilot.
- `512×512` is a common patch size for semantic segmentation; large enough to include context while remaining feasible for GPU training.

## Implications
- The pipeline will maintain a state index and produce outputs grouped by state (raw/interim/processed).
- Train/val/test splits should be **spatial** and respect state boundaries to reduce leakage.
- Patch size interacts with resolution:
  - at 10 m resolution, 512×512 ≈ 5.12 km × 5.12 km per patch.

## Alternatives considered
1) **Fixed global lat/lon grid**  
   - Pros: simple universal indexing  
   - Cons: does not align with administrative reporting; variable ground distance by latitude
2) **UTM/equal-area projected tiles**  
   - Pros: consistent area per tile  
   - Cons: more complex CRS handling across zones in Brazil
3) **Smaller patches (256×256)**  
   - Pros: faster training, smaller I/O  
   - Cons: less context; may increase label noise sensitivity

## Links / evidence
- Tiling implementation notes: `docs/methods/tiling_and_alignment.md`
- Patch export: `src/dataset/make_patches.py` (planned)