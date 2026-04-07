# MapBiomas-only Experiments

## Purpose

This page documents the phase of the project in which MapBiomas was used as the main or only semantic basis for label refinement.

These experiments were essential for understanding the strengths and limitations of land-cover-driven refinement and strongly influenced the final multi-source method.

---

## Why MapBiomas became important

After the limitations of hard settlement-mask refinement became clear, the project needed a richer semantic basis for deciding which parts of a favela polygon should be preserved or removed.

MapBiomas provided that basis because it allowed the workflow to distinguish:

- urban areas,
- uncertain non-vegetated areas,
- vegetation classes,
- water and other non-target classes.

This made it possible to reason about labels more explicitly than with a binary settlement mask alone.

---

## Main MapBiomas class logic

The main interpretation used in these experiments was:

- `24 = Urban Area` → built / keep
- `25 = Other Non Vegetated Areas` → uncertain
- vegetation classes such as forest, savanna, wetland, grassland, mangrove → remove candidates
- some water-related classes → optional hard remove

This class logic later became the conceptual core of the final pipeline.

---

## Main trade-off discovered

The MapBiomas-only experiments revealed a major trade-off:

### Remove uncertain pixels aggressively
This reduces vegetation spillover, but it can also remove real built-up favela edges.

### Keep uncertain pixels
This preserves the footprint better, but it often keeps too much vegetation or non-target spillover.

This trade-off became one of the central problems the later multi-source pipeline was designed to solve.

---

## Variants explored

During this phase, multiple variants were tested, including:

- 30 m MapBiomas experiments,
- 10 m MapBiomas experiments,
- no-ring refinement variants,
- keep-uncertain vs remove-uncertain policies,
- hole-filling post-processing,
- polygonization and dissolved-output comparisons.

These experiments helped clarify what could and could not be achieved using MapBiomas alone.

---

## Main lessons learned

The MapBiomas-only phase taught the project several important lessons:

1. semantic land-cover information is extremely valuable,
2. the built class should remain central,
3. uncertain classes need additional support,
4. vegetation suppression is necessary but can become too aggressive,
5. morphology and polygonization matter after pixel-level decisions.

---

## Relationship to the current pipeline

The current Brazil-scale workflow still depends heavily on MapBiomas, but no longer uses it alone.

The final operational method keeps MapBiomas as:

- the semantic base,
- the master raster grid,
- and the main source of class-based interpretation.

However, it supplements MapBiomas with:

- GHSL for built-up support,
- WorldCover for vegetation support.

In that sense, the MapBiomas-only phase provided the semantic foundation, while the final pipeline added support logic around it.

---

## Why it is now archived

These experiments are archived because they are no longer the active operational workflow.

They remain important because they explain:

- where the current class logic came from,
- why uncertain pixels cannot simply be kept or removed blindly,
- and why multi-source fusion became necessary.