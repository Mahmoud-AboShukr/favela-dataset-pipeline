# Repository Structure

## Purpose

This page explains the current repository organization after the shift to the Brazil-scale chunked pipeline.

The repository now distinguishes between:

- the active main pipeline,
- archived older experiment code,
- active raw data,
- active processed outputs,
- and archived older experiment data.

---

## High-level structure

At a high level, the repository is organized around:

- `src/` for code,
- `data/` for raw, interim, processed, and archived experiment data,
- `docs/` for MkDocs documentation,
- `scripts/` for project utilities.

---

## Active main pipeline

The current active label-refinement workflow is under:

`src/final_pipeline_scale_up/`

This is the main operational pipeline and should be treated as the current production workflow for label refinement.

Its main scripts are:

- `1_prepare_inputs.py`
- `2_build_refined_mask.py`
- `3_polygonize_and_qc.py`
- `4_merge_brazil_polygons.py`

---

## Archived code

Older pilot and experimental code has been moved under:

`src/old_experiments/`

This keeps the repository cleaner while preserving the project history.

Examples of archived code groups include:

- earlier Manaus-oriented final pipeline code,
- Brasília GHSL pilot code,
- legacy label-refinement scripts,
- MapBiomas helper and pilot code.

This archived code remains useful for project history and methodological traceability, but it is no longer the main active workflow.

---

## Data structure

## Raw data

Active raw inputs remain under:

`data/raw/`

This includes source datasets such as:

- favela shapefiles,
- MapBiomas,
- GHSL,
- WorldCover,
- and other raw sources required by the active pipeline.

These are kept in place because the current pipeline still depends on them directly.

---

## Active processed outputs

The active processed outputs of the current main pipeline are under:

`data/processed/final_pipeline_scale_up/`

This folder contains:

- chunk index outputs,
- per-chunk prepared data,
- per-chunk refined rasters,
- per-chunk polygonized outputs,
- and Brazil-wide merged polygon outputs.

This is the main output location of the current operational workflow.

---

## Archived experiment data

Older experimental and pilot outputs have been moved under:

`data/old_experiments_data/`

This keeps the active data tree cleaner and separates the historical results from the current operational outputs.

Archived experiment data may include:

- older AOI subsets,
- earlier GHSL interim products,
- MapBiomas pilot outputs,
- older refined labels,
- earlier processed pilot results,
- logs and tree exports.

---

## Interim data

The `data/interim/` area should now remain focused only on data that are still active or still needed by the current pipeline.

In practice, the current active workflow relies much less on broad interim structures than the earlier pilots, because the national chunked pipeline writes most of its main outputs directly into the processed scale-up structure.

---

## Documentation

Project documentation is kept under:

`docs/`

The documentation now distinguishes clearly between:

- the active Brazil-scale pipeline,
- archived older experiments,
- current runbooks,
- and next-phase planning.

---

## Scripts

Utility and maintenance scripts are stored under:

`scripts/`

For example, repository-cleanup or archive-management utilities belong here.

---

## Why the repository was reorganized

The repository had become difficult to navigate because older pilots, intermediate experiments, and current pipeline code were mixed together.

The reorganization was performed so that:

- the scaled-up Brazil pipeline is clearly the main workflow,
- older code is preserved but archived,
- active outputs are easy to identify,
- and the project is easier to maintain before moving into the satellite-image phase.

---

## Main principle for future work

Future label-refinement development should happen primarily inside:

`src/final_pipeline_scale_up/`

and future active outputs should be written under:

`data/processed/final_pipeline_scale_up/`

Older experiment folders should remain archival unless there is a specific reason to reactivate them.

---

## Practical reading of the repository today

A new contributor should interpret the repository as follows:

- if you want the current pipeline, go to `src/final_pipeline_scale_up/`
- if you want older history, go to `src/old_experiments/`
- if you want current outputs, go to `data/processed/final_pipeline_scale_up/`
- if you want archived old outputs, go to `data/old_experiments_data/`
- if you want documentation, go to `docs/`

This is now the intended project organization.