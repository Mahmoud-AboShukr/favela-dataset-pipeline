# Multicity Scale-Up Plan — 10 m MapBiomas Favela Refinement

## Objective
Test whether the current Brasília 10 m MapBiomas refinement pipeline transfers across 5 Brazilian cities with different vegetation context, urban texture, terrain, and settlement morphology.

## Target cities
- [ ] Rio de Janeiro
- [ ] São Paulo
- [ ] Belo Horizonte
- [ ] Salvador
- [ ] Manaus

---

## Phase 0 — Freeze the baseline before scaling

### Task 0.1 — Freeze the exact Brasília baseline
- [x] Record exact input product name
- [x] Record year used
- [x] Record class mapping used in the current pipeline
- [x] Record strict vegetation mask classes
- [x] Record built mask classes
- [x] Record refinement version used (`no-ring V2.2`)
- [x] Record hole-filling rule and threshold
- [x] Record polygonization settings
- [x] Record dissolve settings
- [x] Record QC metrics currently used
- [x] Save all of the above in a baseline decision note

**Deliverable**
- [x] `docs/decisions/ADR-0009-2026-03-17-multicity-baseline.md`

### Task 0.2 — Define evaluation criteria before running cities
- [x] Define what counts as **good transfer**
- [x] Define what counts as **acceptable with issues**
- [x] Define what counts as **failure**
- [x] Define visual criteria for over-trimming
- [x] Define acceptable removed-ratio range
- [x] Define how to flag full polygon loss
- [x] Define how to flag strong fragmentation

**Deliverable**
- [ ] Add evaluation criteria to the baseline note or a separate QC note

---

## Phase 1 — Prepare the multicity framework

### Task 1.1 — Create city-specific folder structure
- [ ] Create AOI folder per city
- [ ] Create MapBiomas clip folder per city
- [ ] Create masks folder per city
- [ ] Create refined raster folder per city
- [ ] Create polygon output folder per city
- [ ] Create QC/report folder per city

**Suggested structure**
- [ ] `data/interim/aoi/<city>/`
- [ ] `data/interim/mapbiomas_10m_clips/<city>/`
- [ ] `data/interim/masks/<city>/`
- [ ] `data/interim/refined_labels_mapbiomas_10m/<city>/`
- [ ] `data/processed/polygons/<city>/`
- [ ] `reports/qc/mapbiomas_10m/<city>/`

### Task 1.2 — Standardize city naming
- [ ] Use `rio_de_janeiro`
- [ ] Use `sao_paulo`
- [ ] Use `belo_horizonte`
- [ ] Use `salvador`
- [ ] Use `manaus`
- [ ] Ensure naming is consistent in paths, scripts, configs, and reports

### Task 1.3 — Parameterize the pipeline by city
- [ ] Replace Brasília-specific hardcoded paths
- [ ] Add `--city` argument
- [ ] Add `--aoi` argument
- [ ] Add `--favela-polygons` argument
- [ ] Add `--input-raster` argument
- [ ] Add `--output-dir` argument
- [ ] Add optional `--config` argument
- [ ] Test one dry run using Brasília inputs through the generalized runner

**Deliverable**
- [ ] `scripts/run_mapbiomas_10m_city.py`

### Task 1.4 — Create reusable note templates
- [ ] Create city status note template
- [ ] Create multicity comparison note template
- [ ] Create QC summary table template

**Deliverables**
- [ ] `docs/templates/city-status-template.md`
- [ ] `docs/templates/multicity-comparison-template.md`

---

## Phase 2 — Prepare city inputs

### Task 2.1 — Define AOIs
For each city:
- [ ] Obtain municipal AOI
- [ ] Save AOI source
- [ ] Check geometry validity
- [ ] Check CRS
- [ ] Save final AOI file

### Task 2.2 — Subset favela polygons
For each city:
- [ ] Intersect national favela polygons with AOI
- [ ] Export per-city polygon layer
- [ ] Count total intersecting polygons
- [ ] Count polygons fully inside AOI
- [ ] Count polygons crossing AOI boundary

### Task 2.3 — Prepare raster inputs
For each city:
- [ ] Clip 10 m MapBiomas raster to AOI
- [ ] Verify resolution
- [ ] Verify CRS alignment
- [ ] Verify coverage completeness
- [ ] Save clipped raster

### Task 2.4 — Record input note
For each city:
- [ ] Record AOI source
- [ ] Record polygon file
- [ ] Record raster product
- [ ] Record raster year
- [ ] Record CRS
- [ ] Record file paths

**Deliverable per city**
- [ ] `docs/status/YYYY-MM-DD-mapbiomas-10m-<city>-inputs.md`

---

## Phase 3 — Run the frozen baseline unchanged

For each city:

### Task 3.1 — Inspect classes inside favela polygons
- [ ] Compute class histogram inside polygons
- [ ] Identify dominant classes
- [ ] Check whether urban class dominates

### Task 3.2 — Build masks
- [ ] Build strict vegetation mask
- [ ] Build built mask
- [ ] Export masks

### Task 3.3 — Run refinement
- [ ] Run no-ring V2.2 refinement unchanged
- [ ] Export refined raster

### Task 3.4 — Apply post-processing
- [ ] Apply hole filling
- [ ] Polygonize output
- [ ] Dissolve output
- [ ] Export final candidate polygons

### Task 3.5 — Compute QC metrics
- [ ] Total input polygons
- [ ] Total input area
- [ ] Total refined area
- [ ] Refined/input area ratio
- [ ] Removed ratio
- [ ] Number of changed polygons
- [ ] Number of strongly changed polygons
- [ ] Number of fully lost polygons
- [ ] Number of connected components before/after
- [ ] Final dissolved polygon count

### Task 3.6 — Produce visual QC
- [ ] Example of selected refined output over imagery
- [ ] Example where 10 m clearly improves over raw result
- [ ] Example still requiring local review

**Deliverable per city**
- [ ] `docs/status/YYYY-MM-DD-mapbiomas-10m-<city>.md`

---

## Phase 4 — Failure mode review

For each city:
- [ ] Check over-trimming near vegetation
- [ ] Check urban false negatives
- [ ] Check confusion with bare soil
- [ ] Check confusion with industrial or port areas
- [ ] Check fragmentation
- [ ] Check excessive hole filling
- [ ] Check AOI boundary artifacts

**Deliverable per city**
- [ ] Add failure mode summary to city note

---

## Phase 5 — Batch execution order

### Batch 1
- [ ] Rio de Janeiro
- [ ] São Paulo

**Checkpoint**
- [ ] Compare Rio vs São Paulo
- [ ] Decide whether baseline transfers sufficiently
- [ ] Decide whether one global adjustment is needed before Batch 2

### Batch 2
- [ ] Belo Horizonte
- [ ] Salvador

### Batch 3
- [ ] Manaus

---

## Phase 6 — Multicity comparison

### Task 6.1 — Build comparison table
- [ ] Compile QC metrics for all 5 cities
- [ ] Compile failure modes for all 5 cities
- [ ] Compile visual assessment for all 5 cities

### Task 6.2 — Rank transfer quality
For each city:
- [ ] Good transfer
- [ ] Acceptable with issues
- [ ] Weak transfer

### Task 6.3 — Identify systematic issues
- [ ] Pipeline-level failures
- [ ] City-specific failures
- [ ] Product/class-scheme limitations

**Deliverable**
- [ ] `docs/status/YYYY-MM-DD-mapbiomas-10m-multicity-comparison.md`

---

## Phase 7 — Controlled adjustment only after transfer test

### Task 7.1 — Propose one global adjustment at a time
Possible examples:
- [ ] Increase hole-filling threshold
- [ ] Revise strict vegetation class set
- [ ] Revise built support logic

### Task 7.2 — Re-test only on representative cities first
- [ ] Rio de Janeiro
- [ ] São Paulo
- [ ] Manaus

### Task 7.3 — Accept or reject adjustment
- [ ] Keep adjustment only if it improves transfer overall
- [ ] Reject adjustment if it only helps one city but harms others

---

## Minimum deliverables
- [ ] Frozen baseline note
- [ ] City runner script
- [ ] Input note for each city
- [ ] Status note for each city
- [ ] Multicity comparison note
- [ ] QC figures for each city

---

## Immediate next step
- [ ] Start with **Step 1: Freeze the exact Brasília baseline**