# Project Brief — Favela Dataset Pipeline (Brazil)

## Project goal

Build a deep-learning-ready dataset for **favela detection and segmentation in Brazil** by:

1. ingesting and cleaning the official Brazilian favela polygons,
2. refining noisy or overextended labels using auxiliary raster evidence,
3. generating binary masks (`0 = non-favela`, `1 = favela`),
4. aligning refined labels with **Sentinel-2** (optical) and **Sentinel-1** (SAR) imagery,
5. preparing the data for later tiling, patch extraction, and machine learning workflows.

The work starts with a **Brasília pilot** before scaling to the rest of Brazil.

---

## Project framing

The project is now structured as a **modular label-refinement framework** rather than a single fixed refinement workflow.

The official polygons remain the primary label source, and multiple auxiliary raster products are being evaluated to determine how best to:

- remove obvious non-settlement areas such as vegetation,
- preserve realistic settlement geometry,
- avoid over-trimming true built-up areas,
- and build a refinement strategy that can scale later to all Brazil.

The current refinement evidence sources under evaluation include:

- **GHSL built-up / settlement-derived layers**
- **GHSL temporal change products**
- **MapBiomas land-cover evidence**
- potential later fusion with **WSF** or other built-up support layers

---

## Current status

### Completed

#### Subtask 1 — Clean polygons (Brazil-wide)
- Input CRS: `EPSG:4674` (SIRGAS 2000)
- Stored CRS: `EPSG:4326`
- Loaded features: `12,348`
- After multipolygon explode: `12,741`
- Invalid geometries fixed: `1 → 0`
- Unique IDs created: `source_id`, `part_index`, `favela_id` (no duplicates)

Outputs:
- `data/interim/polygons_clean/favelas_clean.gpkg`
- `data/interim/polygons_clean/favelas_clean_summary.csv`

#### Brasília subset extraction
- Created a Brasília-area subset from cleaned polygons
- Extracted subset for pilot experimentation

Output:
- `data/interim/polygons_clean/favelas_brasilia.gpkg`

#### Pilot AOI definition (Brasília / Distrito Federal)
- Pilot AOI is defined as the **Distrito Federal administrative boundary from OSM**
- AOI file:
  - `data/interim/aoi/brasilia_boundary.gpkg`

QC coverage (cleaned polygons → AOI):
- Total cleaned polygon parts: **12741**
- Intersect AOI: **72**
- Within AOI: **68**
- Cross boundary: **4**
- Excluded: **12669**

QC script:
- `src/qc/qc_aoi_coverage.py`

QC output:
- `reports/qc/stats/aoi_coverage_brasilia.csv`

---

## GHSL preparation work

### Subtask 2 — GHSL acquisition and verification
- Downloaded the GHSL tile covering Brasília
- Verified raster properties
- Prepared a clipped raster for faster pilot experimentation

Output:
- `data/raw/ghsl/brasilia.tif`

### GHSL clip to Brasília bbox
Output:
- `data/interim/ghsl_clips/ghsl_brasilia_clip.tif`

### Notes / lessons learned
- An initial GHSL tile mismatch caused clipping failure because the downloaded raster did not overlap the Brasília bbox.
- The workflow was updated to validate bbox–raster overlap before clipping.
- The corrected GHSL tile is now stored and used consistently for Brasília experiments.

---

## Experimental work in progress

The Brasília pilot now includes multiple experimental directions rather than a single refinement rule.

### 1. GHSL-based refinement experiments
Initial refinement work explored the use of GHSL built-up evidence to trim official polygons and generate refined binary masks.

This remains an important baseline, but the project no longer assumes that GHSL alone will be the final refinement source.

### 2. GHSL temporal change analysis
A temporal experiment has been introduced to compare multiple GHSL epochs and generate change products such as:

- growth,
- loss,
- persistence,
- and supporting resampled masks.

The purpose of this experiment is to assess whether temporal built-up change can help explain polygon mismatch, identify evolving urban areas, and support refinement interpretation.

### 3. MapBiomas-only pilot
Following discussion with supervisors, a new pilot experiment is being introduced to test whether **MapBiomas alone** can provide sufficient evidence for:

- vegetation removal,
- anthropic / built-up support,
- and conservative polygon refinement in Brasília.

This pilot is motivated by the practical difficulty of relying immediately on NDVI from Sentinel-2, especially under cloud contamination.

The main question is:

> Can MapBiomas alone provide a sufficiently robust first refinement baseline before introducing GHSL, WSF, or other auxiliary products?

---

## Current methodological direction

The working assumption is now:

- the **official favela polygon** remains the backbone of the label,
- refinement should be **conservative**,
- and changes should focus primarily on removing **obvious non-settlement margins**, especially vegetation.

Rather than fully redrawing polygons from sparse external masks, the project is increasingly oriented toward:

- boundary-aware refinement,
- multi-source comparison,
- and evidence-based removal rules.

This is especially important in informal-settlement mapping, where:
- polygon interiors may contain vegetation,
- built-up patterns may be fragmented,
- and coarse or sparse settlement products may distort geometry if used too aggressively.

---

## Current active questions

The Brasília pilot is currently focused on the following questions:

1. Can **GHSL** provide useful built-up evidence for polygon refinement despite resolution and sparsity limitations?
2. Can **GHSL temporal change** help interpret settlement evolution or diagnose apparent false negatives?
3. Can **MapBiomas alone** remove vegetation and provide useful anthropic support without requiring immediate NDVI computation?
4. If a single source is insufficient, what is the best multi-source combination for refinement?

---

## Confirmed decisions

### Confirmed with managers
- **Pilot AOI:** Brasília / Distrito Federal
- **Scaling strategy:** processing organized **by state**
- **Patch size for downstream DL workflows:** `512 × 512`

### Previously confirmed GHSL direction
- GHSL was initially selected as the main refinement evidence source for the pilot baseline.
- This is now being treated as a **baseline experiment**, not necessarily the final exclusive refinement source.

### Current experimental decision
- This week’s pilot will test **MapBiomas as a standalone refinement evidence source**
- NDVI-based vegetation detection is deferred for now because of the added complexity of cloud-sensitive Sentinel-2 preprocessing

---

## Near-term plan

### This week — Brasília pilot with MapBiomas
The immediate objective is to test whether MapBiomas can be used on its own to:

- identify vegetation inside or around favela polygons,
- provide built-up / anthropic support,
- and support conservative polygon refinement without additional sources.

Planned outputs include:
- a Brasília-clipped MapBiomas raster,
- a vegetation mask,
- an anthropic / built-up support mask,
- one or more refined pilot masks,
- visual QC examples,
- and a conclusion on whether MapBiomas alone is sufficient.

### Parallel documentation work
The documentation is being expanded to support:
- methods pages,
- experiment pages,
- dated status notes,
- ADRs,
- and thesis-writing drafts.

This is needed because the project now includes several parallel experiments and evolving methodological choices.

---

## Next pipeline stages

After the current Brasília refinement pilot, the broader pipeline remains:

1. finalize a defensible refinement strategy,
2. establish the tiling system,
3. acquire and preprocess Sentinel-2 imagery,
4. preprocess Sentinel-1 imagery,
5. align labels and imagery,
6. export machine-learning-ready patches,
7. run QC and sensitivity analysis,
8. scale the workflow to all Brazil.

---

## Risks and uncertainties

- Some auxiliary raster products may be too coarse or too sparse to support reliable boundary refinement on their own.
- Different data sources may disagree in mixed urban or peri-urban areas.
- Vegetation removal is easier to motivate conceptually than to implement conservatively without damaging true settlement boundaries.
- Thresholds, class groupings, and postprocessing choices will require pilot validation.
- The final master grid, target CRS, and raster alignment policy will need to remain consistent with later Sentinel-based export.

---

## Evidence and references

Primary evidence currently includes:
- `data/interim/polygons_clean/favelas_clean_summary.csv`
- `data/interim/polygons_clean/favelas_brasilia.gpkg`
- `data/interim/aoi/brasilia_boundary.gpkg`
- `data/raw/ghsl/brasilia.tif`
- `data/interim/ghsl_clips/ghsl_brasilia_clip.tif`

Supporting QC and scripts include:
- `src/qc/qc_aoi_coverage.py`
- `reports/qc/stats/aoi_coverage_brasilia.csv`

Additional experiment-specific evidence should be documented in:
- `docs/experiments/`
- `docs/status/`
- and the corresponding method pages as they are added.