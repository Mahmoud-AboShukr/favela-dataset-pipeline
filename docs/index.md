# Favela Dataset Pipeline

This site documents the pipeline for building a deep-learning-ready dataset for **favela detection and segmentation in Brazil**.

The project starts from official favela polygons and develops methods to:
- refine noisy boundaries,
- remove obvious non-settlement areas such as vegetation,
- align labels with **Sentinel-1** and **Sentinel-2** imagery,
- and prepare data for downstream machine learning experiments.

The current work is centered on a **Brasília pilot**, used to test refinement strategies before scaling to larger regions of Brazil.

## Current focus

The main topics currently covered in this documentation are:

- official polygon cleaning and refinement,
- **GHSL-based** built-up and settlement analysis,
- **GHSL temporal change** experiments,
- **MapBiomas-based** vegetation-removal and built-up support experiments,
- preparation of refined masks for later Sentinel-aligned dataset generation.

## Navigate the documentation

### Project overview
General context, scope, and repository organization.

- [Project Brief](project-brief.md)
- [Runbook](runbook.md)
- [Scope and Goals](overview/scope.md)
- [Pipeline Status](overview/pipeline-status.md)

### Methods
Reusable methodological components of the pipeline.

- [Data Sources](methods/data_sources.md)
- [Label Refinement](methods/label_refinement.md)
- [Temporal Change Analysis](methods/temporal_change_analysis.md)
- [MapBiomas Refinement](methods/mapbiomas_refinement.md)

### Experiments
Pilot studies and comparative analyses carried out on Brasília.

- [Experiments Overview](experiments/index.md)

### Decisions
Architecture and methodology decisions recorded as ADRs.

- [Decisions](decisions/ADR-0001-storage-crs.md)

### Thesis draft
Working research-writing material derived from the implemented methods and experiments.

- [Methods Chapter Draft](thesis/chapter_methods_draft.md)

## Active experiments

The current active experiments are:

- **GHSL settlement-mask refinement pilot**
- **GHSL temporal change analysis**
- **MapBiomas-only pilot for vegetation removal and settlement-support inference**

## Project goal

The long-term objective is to produce a scalable and consistent dataset for informal-settlement mapping in Brazil by:

1. ingesting official favela polygons,
2. refining noisy or overextended boundaries,
3. generating reliable binary masks,
4. aligning the labels with Sentinel-1 and Sentinel-2 imagery,
5. preparing patch-based data for machine learning workflows.