# Pipeline Status

## Purpose

This page summarizes the current status of the favela dataset pipeline.

It is intended to provide a quick view of:

- what has already been completed,
- what is currently in progress,
- what is planned next,
- and where the main methodological uncertainty still lies.

The project is currently centered on a **Brasília pilot** before broader scaling to Brazil.

---

## Current overall status

The project has moved beyond initial repository setup and data ingestion and is now in an active **pilot experimentation phase**.

At this point, the pipeline includes:

- cleaned official polygons,
- a defined Brasília AOI,
- GHSL preparation and settlement-mask experiments,
- GHSL temporal-change analysis,
- MapBiomas pilot planning,
- and expanding documentation for methods, experiments, decisions, and thesis drafting.

In other words, the project is no longer only setting up the workflow; it is actively testing candidate refinement strategies.

---

## Completed components

### 1. Official polygon cleaning
Completed work includes:

- loading the official favela polygons,
- fixing invalid geometries,
- exploding multipart geometries,
- creating unique identifiers,
- exporting cleaned polygon outputs.

This established the base vector labels used by all later stages.

### 2. Brasília pilot subset
A Brasília subset has been extracted from the cleaned polygon dataset.

This subset acts as the main study area for current experimentation.

### 3. AOI preparation
The Brasília / Distrito Federal AOI has been defined and integrated into the workflow.

This provides a consistent pilot boundary for clipping and analysis.

### 4. GHSL preparation
Initial GHSL work has been completed, including:

- acquisition of a valid GHSL raster for the Brasília area,
- metadata inspection,
- clipping to the pilot AOI,
- and settlement-mask preparation experiments.

### 5. Basic documentation foundation
The documentation site has already been structured into:

- overview pages,
- methods pages,
- experiment pages,
- decisions,
- status notes,
- and thesis draft sections.

This is important because the project is increasingly research-oriented as well as operational.

---

## In-progress components

### 1. Refinement strategy evaluation
The main area currently in progress is the evaluation of how official polygons should be refined.

This includes:

- GHSL-based built-up support experiments,
- interpretation of sparse settlement masks,
- and comparison of possible refinement logics.

### 2. GHSL temporal-change analysis
A temporal experiment comparing GHSL epochs has been introduced.

This work is currently being treated as:

- diagnostic,
- interpretive,
- and supportive of refinement reasoning rather than direct label generation.

### 3. MapBiomas pilot
A new pilot direction has been defined in which MapBiomas will be tested as a standalone source for:

- vegetation-removal evidence,
- anthropic or built-support inference,
- and conservative refinement in Brasília.

This is one of the main active short-term priorities.

### 4. Documentation expansion
The docs are being expanded to better reflect:

- multiple experiments,
- evolving methodological decisions,
- and thesis-oriented project writing.

This includes filling the new pages under methods, experiments, status, and ADRs.

---

## Current methodological position

The current pipeline is best described as a **modular refinement framework under active evaluation**.

The project is no longer assuming that one source, such as GHSL alone, will necessarily be sufficient. Instead, the current position is:

- official polygons remain the backbone of the labels,
- refinement should be conservative,
- different evidence sources are being tested according to their role,
- and the final strategy may become multi-source if needed.

This is one of the most important developments in the current project stage.

---

## Main active experiments

The main active experiment tracks are:

### GHSL settlement-mask refinement
Used as the initial built-up baseline for comparing polygons and raster support.

### GHSL temporal change
Used to understand built-up persistence, growth, and loss across epochs, mainly for diagnosis and interpretation.

### MapBiomas pilot
Used to test whether vegetation-related refinement can be performed with a standalone land-cover source before adding GHSL, WSF, or NDVI-based workflows.

---

## Main open questions

The project is currently trying to answer the following questions:

1. Is GHSL sufficient as a standalone built-up refinement source?
2. How should sparse or threshold-sensitive settlement support be interpreted?
3. Can GHSL temporal change improve understanding of mismatch without being misused as direct truth?
4. Can MapBiomas alone remove vegetation conservatively enough to be useful?
5. If no single source is sufficient, what is the most defensible fusion strategy?

These questions define the current research stage of the project.

---

## Next planned steps

The most immediate next steps are:

### 1. Complete the MapBiomas pilot
This includes:

- selecting the MapBiomas dataset and year,
- clipping it to Brasília,
- defining vegetation / anthropic / uncertain class groupings,
- generating masks,
- testing conservative refinement rules,
- and assessing whether MapBiomas is sufficient alone.

### 2. Continue method and experiment documentation
The documentation should continue to be updated so that the current repo state is fully reflected in:

- methods,
- experiments,
- status notes,
- ADRs,
- and thesis drafts.

### 3. Decide whether multi-source fusion is needed
If MapBiomas alone is not sufficient, the next likely direction is to test a combined strategy, most likely using:

- MapBiomas for vegetation removal,
- GHSL for built-up protection,
- and temporal GHSL outputs for context.

### 4. Prepare for downstream dataset stages
Once the refinement direction is clearer, the project can proceed more confidently to:

- alignment with Sentinel imagery,
- tiling,
- patch extraction,
- and later ML dataset construction.

---

## Current risks and uncertainties

The main uncertainties at this stage are:

- whether any single auxiliary source is sufficient alone,
- how much threshold sensitivity affects GHSL-based outputs,
- whether MapBiomas is semantically useful enough for conservative refinement,
- how much temporal mismatch affects interpretation,
- and how to preserve realistic polygon geometry during trimming.

These are expected pilot-stage uncertainties and are part of the reason the project is being documented so carefully.

---

## Practical summary

### Completed
- official polygon cleaning
- Brasília subset creation
- AOI preparation
- GHSL raster preparation
- initial GHSL settlement-mask experimentation
- documentation restructuring

### In progress
- refinement strategy comparison
- GHSL temporal-change interpretation
- MapBiomas pilot setup and planning
- method / experiment / ADR documentation

### Next
- execute and assess the MapBiomas pilot
- decide whether single-source refinement is enough
- move to fusion if necessary
- then continue toward Sentinel alignment and dataset generation

---

## Status interpretation

The project is in a strong intermediate phase:

- the base pipeline exists,
- the pilot AOI is established,
- the main uncertainty is now methodological rather than infrastructural,
- and the current work is focused on choosing the most defensible refinement strategy before scaling further.

This is a productive stage because it shifts the project from setup into evidence-based decision making.