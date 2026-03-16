# ADR-0008 — MapBiomas Pilot Policy

- **Status:** Accepted
- **Date:** 2026-03-13
- **Deciders:** Project team / supervisors
- **Related pages:** `methods/mapbiomas_refinement.md`, `experiments/2026-03-mapbiomas-pilot.md`

---

## Context

The Brasília pilot is intended to identify a defensible and operational method for refining official favela polygons before scaling the workflow to larger regions of Brazil.

Earlier discussion considered using vegetation indices such as **NDVI** derived from Sentinel-2 imagery to detect vegetation inside or around the polygons. However, this would require additional processing steps, including:

- selecting suitable Sentinel-2 scenes,
- dealing with cloud and cloud-shadow contamination,
- ensuring temporal appropriateness,
- and adding a more complex optical preprocessing burden during the pilot stage.

At the same time, the project needed a practical way to test whether polygon refinement could focus on the removal of obvious vegetation or non-settlement margins while preserving plausible built-up settlement structure.

Because of this, the project team considered **MapBiomas** as an alternative pilot evidence source.

This raised the following policy question:

> should the project first test MapBiomas as a standalone refinement source before introducing more complex vegetation-index workflows or multi-source fusion?

---

## Decision

The project will adopt **MapBiomas as the first standalone pilot source for the current Brasília vegetation-removal experiment**.

This means that, for the current pilot phase:

- MapBiomas will be tested on its own as an auxiliary evidence source,
- NDVI-based vegetation detection from Sentinel-2 is **deferred** for now,
- and other auxiliary sources such as GHSL or WSF will only be introduced later if MapBiomas alone proves insufficient.

MapBiomas is therefore approved as the **current first-pass operational baseline** for vegetation-oriented refinement testing in Brasília.

---

## Rationale

This decision is based on the following considerations.

### 1. The immediate refinement problem is vegetation-related

A major current concern in the official polygons is the inclusion of vegetation or non-settlement margins. A land-cover product is therefore a natural candidate for the first pilot, because it may help identify areas that are inconsistent with the intended settlement label.

### 2. MapBiomas is operationally simpler than immediate NDVI preprocessing

Using NDVI would require extra work related to scene choice, cloud handling, and optical preprocessing. For the current pilot week, this would add unnecessary complexity before a simpler land-cover-based baseline has been tested.

### 3. MapBiomas provides directly interpretable class information

MapBiomas can be grouped into categories such as:

- vegetation-like classes,
- anthropic or built-support classes,
- uncertain classes.

This makes it suitable for a conservative and explainable pilot refinement workflow.

### 4. The project favors stepwise experimentation

The broader project strategy is to test whether a single source is sufficient before moving to more complex fusion approaches.

Testing MapBiomas first is consistent with that strategy:
- first evaluate standalone utility,
- then introduce GHSL, WSF, or other support sources only if needed.

### 5. The pilot remains conservative

This decision does **not** mean that MapBiomas replaces the official polygons directly. It is approved only as an **evidence source** for conservative refinement.

---

## Scope of the decision

This policy applies specifically to the **current Brasília pilot experiment**.

It governs:

- the first operational vegetation-removal pilot,
- the short-term experimental order of methods,
- and the documentation of the current refinement strategy.

It does **not** imply that:

- MapBiomas is permanently the final refinement solution,
- NDVI is rejected as a future option,
- or multi-source fusion will not be needed later.

---

## Consequences

### Positive consequences

- the pilot can move forward quickly with a practical land-cover source,
- the method remains interpretable and easy to explain,
- the project can test vegetation removal without immediate cloud-sensitive preprocessing,
- and the team gains evidence on whether a single-source land-cover approach is sufficient.

### Negative consequences

- MapBiomas may prove too coarse or too ambiguous for standalone refinement,
- the pilot may still require later support from GHSL or WSF,
- and deferring NDVI means that one potentially informative vegetation source is not evaluated immediately.

---

## Operational guidance

The following operational rules apply during the MapBiomas pilot.

### Allowed use of MapBiomas
MapBiomas may be used to:

- identify vegetation-like areas as candidate removable regions,
- identify anthropic or urban-support areas as protective evidence,
- support conservative raster-based refinement experiments,
- generate pilot masks and QC overlays.

### Required interpretation rule
MapBiomas must be used as **supporting evidence**, not as direct replacement geometry.

This means:

- the official polygon remains the backbone of the label,
- refinement should remain conservative,
- and uncertain classes should generally be handled cautiously.

### Deferred work
The following are explicitly deferred until after the standalone MapBiomas pilot is assessed:

- NDVI-based refinement using Sentinel-2,
- mandatory fusion with GHSL,
- mandatory fusion with WSF,
- more complex multi-source refinement logic.

---

## Decision outcomes expected from the pilot

The purpose of this policy is to enable a clear decision after the pilot. The MapBiomas experiment should support one of three outcomes:

### Outcome 1 — sufficient alone
MapBiomas is strong enough to serve as the first operational refinement baseline for Brasília.

### Outcome 2 — useful but incomplete
MapBiomas is useful for vegetation-related trimming, but another source is needed for built-up protection or settlement support.

### Outcome 3 — insufficient alone
MapBiomas is not strong enough as a standalone source and should be used only later as one component in a broader fusion workflow.

---

## Relationship to other methods

This decision places MapBiomas in the following methodological position:

- **current standalone pilot source** for vegetation-oriented refinement,
- distinct from **GHSL**, which remains the built-up baseline,
- distinct from **temporal GHSL**, which remains diagnostic,
- and potentially complementary to future multi-source fusion.

If MapBiomas alone proves insufficient, the most likely next methodological direction is:

- MapBiomas for vegetation-removal evidence,
- GHSL for built-up protection,
- with optional later inclusion of WSF or other auxiliary sources.

---

## Future review

This ADR should be revisited after the Brasília MapBiomas pilot has been executed and evaluated.

The decision may be updated if:

- MapBiomas proves clearly sufficient alone,
- MapBiomas proves clearly insufficient,
- or the project transitions to a documented multi-source fusion workflow.

Until that review, the active policy remains:

> test MapBiomas first as a standalone refinement source for the Brasília pilot, and defer NDVI-based refinement and mandatory fusion until the pilot result is known.