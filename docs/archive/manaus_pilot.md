# Manaus Pilot

## Purpose

This page documents the Manaus pilot phase, which was a major step between the early Brasília pilot and the final Brazil-scale pipeline.

Manaus was used as a more difficult test case because it contains strong urban–vegetation interaction, many polygons, and complex boundaries that stress any refinement method.

---

## Why Manaus was important

Manaus was chosen as a hard-case pilot because it contains:

- many favela polygons,
- dense vegetation around urban areas,
- complex built-up edges,
- and ambiguous peri-urban transitions.

Compared with Brasília, Manaus was a much better stress test for refinement logic because it forced the project to confront the central problem of urban-edge ambiguity.

---

## Main methodological shift in Manaus

The Manaus work marked a transition away from simple settlement-mask logic and toward a more flexible multi-source refinement strategy.

Instead of relying mainly on a settlement prior, the Manaus pilot explored how to combine:

- semantic land-cover information,
- built-up support,
- vegetation suppression,
- and later polygon-based review outputs.

This phase helped shape the logic that is now used in the national pipeline.

---

## Main data sources explored

The Manaus pilot contributed to the final choice of active sources by testing combinations involving:

- MapBiomas,
- GHSL,
- WorldCover,
- and initially WSF.

This phase was important because it showed that:

- land-cover semantics are essential,
- built-up support should be used as support rather than absolute truth,
- and vegetation suppression is a central requirement in difficult Brazilian urban contexts.

---

## Why Manaus was a strong pilot

A refinement method that looks acceptable in a simpler area may fail in Manaus because of:

- mixed urban and vegetated edges,
- non-trivial morphology,
- many small and irregular polygon structures,
- and visually complex context around target boundaries.

For that reason, Manaus became the best intermediate test case before scaling to Brazil.

---

## Outputs and lessons

The Manaus pilot helped establish the practical three-part structure that later became formalized in the national workflow:

1. prepare and align inputs,
2. build a refined raster mask,
3. polygonize and compute QC.

It also reinforced the importance of preserving:

- both raster outputs,
- and final polygon outputs.

This became a core design principle of the current pipeline.

---

## Main contribution of the Manaus phase

The key contribution of the Manaus pilot was that it transformed the project from:

- a settlement-mask refinement idea

into:

- a true multi-source label-refinement strategy.

In other words, Manaus was where the modern logic of the pipeline really took shape.

---

## Why it is now archived

The Manaus pilot is archived because its ideas have now been absorbed into the national pipeline.

It is no longer the main operational branch because:

- the same logic has been generalized,
- the workflow has been formalized into chunk-based Brazil-scale scripts,
- and the project now runs nationally rather than only on pilot cities.

The Manaus phase is therefore a methodological bridge between Brasília and the final operational system.