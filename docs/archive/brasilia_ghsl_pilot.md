# Brasília GHSL Pilot

## Purpose

This page documents the original Brasília GHSL-based pilot that served as the starting point of the favela-refinement project.

Although this pilot is no longer the active workflow, it remains methodologically important because it revealed the main weakness of hard settlement-mask refinement and motivated the later move toward a multi-source strategy.

---

## Historical context

At the beginning of the project, the main idea was to refine official favela polygons by intersecting them with a built-up or settlement-support layer.

Brasília was chosen as an early pilot because it provided:

- a manageable first area of study,
- a relatively controlled urban context,
- and a practical setting for testing raster-based label refinement.

The early workflow used:

- cleaned official favela polygons,
- a Brasília AOI extracted from OSM,
- GHSL built-up data,
- and a derived settlement mask.

---

## Main workflow steps

The original Brasília pilot roughly followed these steps:

1. clean the favela polygon layer,
2. extract a Brasília AOI,
3. clip GHSL to the AOI,
4. derive a settlement mask from the GHSL built-up product,
5. intersect the favela polygons with that settlement support,
6. generate refined raster and polygon outputs.

This early workflow was relatively simple compared with the current Brazil-scale pipeline.

---

## Main data source

The key raster source was GHSL.

It was used to derive a settlement-support layer intended to indicate where built-up surface existed and where favela polygons should be retained.

At that stage, the methodological assumption was that favela polygons should mostly coincide with settlement-like built-up regions.

---

## What the pilot revealed

The main lesson from the Brasília pilot was that a settlement mask can introduce false negatives.

This means:

- some areas that visually or semantically appear to belong to the target polygon
- may not be marked as settlement by the support layer.

When the refinement logic is too strict, those false negatives propagate directly into the refined label.

In practice, this means that a rule such as:

- keep polygon pixels only if they overlap settlement support

can wrongly remove valid favela areas.

---

## Why this mattered

This was the first major methodological warning in the project.

It showed that:

- the support layer is not perfect,
- hard logical intersection is too brittle,
- and refinement must tolerate uncertainty more intelligently.

This insight directly influenced later work by encouraging:

- softer support logic,
- class-based semantic filtering,
- and eventually multi-source fusion.

---

## Relationship to later work

The Brasília GHSL pilot should be seen as the conceptual origin of the project, not as a failed experiment.

It provided three important contributions:

1. it validated the general idea of raster-assisted label refinement,
2. it exposed the danger of hard settlement-mask logic,
3. it created the initial framework that later evolved into the current multi-source chunked pipeline.

---

## Why it is now archived

This workflow is no longer the main project line because:

- it relied too heavily on one support source,
- it was too sensitive to false negatives,
- it was designed for a pilot AOI rather than country-scale operation,
- and later experiments showed that semantic land-cover information and multi-source support provide a stronger basis for refinement.

The current Brazil-scale pipeline therefore preserves the lesson of the Brasília pilot, but not its exact operational logic.