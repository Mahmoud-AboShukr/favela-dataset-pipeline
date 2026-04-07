# Refinement Logic

## Purpose

This page documents the active decision logic used in Stage 2 of the Brazil-scale favela refinement pipeline.

The goal of this logic is to improve the geometric quality of favela labels by combining semantic land-cover information, built-up support, and vegetation suppression.

The output of this stage is a refined binary raster mask.

---

## General principle

The refinement logic is designed to follow this principle:

- keep clearly built-up pixels,
- allow uncertain pixels only when supported,
- remove vegetation-like pixels,
- restrict the result to the favela footprint,
- and clean the result morphologically.

This means the pipeline is conservative in structure, but not purely based on a hard settlement prior.

---

## Active source roles

### MapBiomas 10 m
MapBiomas provides the semantic starting point.

Its roles are:

- identify built-up pixels,
- identify uncertain non-vegetated pixels,
- identify vegetation,
- identify optional hard-removal classes,
- define the master grid.

### GHSL EMC-BUILT 2022 10 m
GHSL provides built-up support.

Its main role is to support uncertain pixels that should only remain if built-up evidence is present.

### ESA WorldCover 2021 v200
WorldCover provides vegetation support.

Its role is to help suppress vegetation spillover that may otherwise remain around favela edges.

---

## WSF status

WSF is not part of the current core rule.

It was considered during development, but it is currently excluded from the active logic because of temporal-consistency concerns relative to the target refinement context.

---

## MapBiomas class interpretation

The current logic uses the following interpretation:

### Built class
- `24 = Urban Area`

This is the main keep class.

### Uncertain class
- `25 = Other Non Vegetated Areas`

This class is not automatically kept. It is treated as uncertain and only retained when supported by GHSL.

### Vegetation removal classes
The current vegetation mask includes:

- `3 = Forest Formation`
- `4 = Savanna Formation`
- `5 = Mangrove`
- `6 = Floodable Forest`
- `11 = Wetland`
- `12 = Grassland`
- `49 = Wooded Sandbank Vegetation`
- `50 = Herbaceous Sandbank Vegetation`

### Optional hard-remove classes
The current logic also treats the following as hard removal:

- `31 = Aquaculture`
- `33 = Water`

---

## WorldCover class interpretation

The current logic uses WorldCover mainly as a vegetation suppression source.

### Vegetation-like classes
These are treated as vegetation support:

- `10 = Tree cover`
- `20 = Shrubland`
- `30 = Grassland`
- `90 = Herbaceous wetland`
- `95 = Mangroves`
- `100 = Moss and lichen`

### Hard-remove class
- `80 = Permanent water bodies`

---

## GHSL support threshold

GHSL is converted into a support mask using a threshold.

In the current national run, the threshold was:

- `GHSL >= 20.0`

This means uncertain MapBiomas pixels are only retained if the corresponding GHSL built-up evidence is at least 20.

---

## Active decision rule

The current rule can be summarized as follows:

### Step 1 — Build semantic masks
From MapBiomas, build:

- `core_built`
- `uncertain`
- `vegetation`
- `hard_remove`

From WorldCover, build:

- `wc_vegetation`
- `wc_hard_remove`

From GHSL, build:

- `ghsl_support`

### Step 2 — Restrict to the favela footprint
The logic is constrained by the favela raster mask. This means the refinement is performed inside the favela footprint rather than as open expansion into surrounding territory.

### Step 3 — Keep built-up pixels
All `core_built` pixels are retained.

### Step 4 — Keep uncertain pixels only with support
Uncertain pixels are only retained when GHSL support is present.

Conceptually:

`uncertain AND ghsl_support`

### Step 5 — Form the candidate mask
The candidate mask becomes:

`core_built OR supported_uncertain`

still restricted to the favela mask.

### Step 6 — Remove non-target pixels
Pixels are removed if they belong to:

- MapBiomas vegetation classes,
- MapBiomas hard-remove classes,
- WorldCover vegetation classes,
- WorldCover hard-remove classes.

### Step 7 — Apply morphology
The result is cleaned using:

- small-object removal
- small-hole filling

---

## Current morphology parameters

The national run used:

- minimum object size = `9` pixels
- maximum hole fill size = `9` pixels

These parameters were chosen as a moderate cleanup rather than a strong geometric smoothing.

---

## Why this logic was chosen

This logic is the result of earlier experimentation.

The earlier pilots showed that:

- hard settlement-based logic can remove true positives,
- MapBiomas-only logic can either over-prune or keep vegetation spillover,
- a multi-source rule gives a better balance.

The current rule therefore aims to:

- preserve high-confidence urban pixels,
- keep uncertain edge pixels only with built-up support,
- suppress vegetation using both MapBiomas and WorldCover,
- and preserve the final footprint as a controlled refinement rather than an unconstrained expansion.

---

## Strengths of the current rule

The current logic has several advantages:

- semantically interpretable,
- based on explicit classes and support masks,
- temporally more consistent than a WSF-dependent rule,
- scalable to the full country,
- relatively easy to tune.

---

## Current limitations

The logic also has limitations:

- GHSL threshold choice still influences edge preservation strongly,
- vegetation suppression may still be too strong or too weak in some local contexts,
- chunk-boundary effects are not solved inside Stage 2,
- and the current rule does not yet use industrial-area masking.

---

## What may be tuned later

Potential later refinements include:

- tuning the GHSL threshold,
- changing morphology parameters,
- class-specific regional adjustments,
- introducing OSM industrial/factory veto logic,
- or testing optional WSF use as a comparison rather than a required support layer.

---

## Current status

This logic has already been run successfully across all 407 active chunks of the current Brazil-scale pipeline.