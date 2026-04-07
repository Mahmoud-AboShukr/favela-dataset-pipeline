# Multi-city MapBiomas 10m Experiments

## Purpose

This page documents the multi-city MapBiomas 10 m experiment phase that was used to test whether the refinement logic generalized beyond a single city.

This stage was important because it moved the project from local experimentation toward broader methodological confidence.

---

## Why multi-city testing was needed

A refinement strategy that works in only one urban context is not sufficient for a national dataset.

The project therefore tested MapBiomas 10 m logic across multiple cities to see whether the same rules could generalize across:

- different urban forms,
- different vegetation contexts,
- different polygon densities,
- and different edge behaviors.

---

## Typical cities involved

This phase included cities such as:

- Rio de Janeiro,
- São Paulo,
- Belo Horizonte,
- Salvador,
- Manaus.

These cities were chosen because they span different Brazilian urban and environmental contexts.

---

## Main logic tested

The multi-city work focused mainly on MapBiomas-based refinement logic, especially:

- no-ring strategies,
- class 24 keep logic,
- class 25 uncertain logic,
- vegetation suppression,
- keep-uncertain vs remove-uncertain comparisons,
- hole-filling variants,
- raw vs dissolved polygonization outputs.

---

## Why 10 m mattered

Moving to the 10 m product was important because it offered finer spatial detail than earlier lower-resolution experiments.

This was especially useful for:

- urban edges,
- smaller structures,
- and more precise geometry in dense urban areas.

---

## Main results of this phase

This phase showed that:

- the MapBiomas semantic logic was meaningful across multiple cities,
- but the same trade-off still remained:
  - keep uncertain → more complete but noisier,
  - remove uncertain → cleaner but more aggressive.

So the multi-city tests increased confidence in the semantic structure of the method, while also confirming the need for additional support layers.

---

## Main methodological contribution

The multi-city phase was critical because it showed that the project should not think only in terms of one pilot city.

It supported the idea that the final pipeline should:

- scale across multiple local contexts,
- remain modular,
- and later operate at national level through chunk-based processing.

In this sense, the multi-city phase helped prepare the conceptual transition to the Brazil-scale pipeline.

---

## Why it is now archived

This phase is archived because it was still based mainly on MapBiomas-only logic and city-by-city experimentation.

Its key ideas survive in the active workflow, but the operational method has now moved beyond it by using:

- chunk-based national execution,
- built-up support from GHSL,
- vegetation support from WorldCover,
- and final national-scale processing scripts.