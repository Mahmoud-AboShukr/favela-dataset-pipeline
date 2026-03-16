# ADR-0007 — Temporal Change Policy

- **Status:** Accepted
- **Date:** 2026-03-13
- **Deciders:** Project team / supervisors
- **Related pages:** `methods/temporal_change_analysis.md`, `experiments/2026-03-ghsl-temporal-change.md`

---

## Context

The Brasília pilot initially focused on refining official favela polygons using single-epoch auxiliary raster evidence, especially GHSL-based built-up or settlement-support products.

During this work, it became clear that disagreement between official polygons and a single GHSL layer could be caused by more than one factor, including:

- actual urban growth between different dates,
- differences between GHSL epochs or products,
- resolution mismatch,
- threshold sensitivity,
- or incomplete support in one epoch alone.

A temporal GHSL comparison workflow was therefore introduced to compare multiple epochs over Brasília and derive products such as:

- growth,
- loss,
- persistence,
- and supporting aligned binary masks.

This raised an important policy question:

> how should temporal-change outputs be used in the project?

---

## Decision

Temporal-change outputs derived from GHSL are adopted as **diagnostic and interpretive evidence only**.

They may be used to:

- help explain mismatch between official polygons and single-epoch GHSL support,
- identify areas of persistent built-up presence,
- support visual QC and exploratory analysis,
- and inform later methodological reasoning.

They must **not** be used as:

- direct replacement labels for favela polygons,
- standalone ground truth for refinement,
- or the sole basis for adding or removing polygon regions.

In other words, temporal GHSL products are part of the project’s **contextual analysis layer**, not its direct labeling truth.

---

## Rationale

This decision is based on the following considerations.

### 1. Built-up change is not equivalent to favela change

Temporal GHSL outputs indicate change in built-up support between epochs. They do not identify informal settlements specifically, and they do not directly encode favela boundaries.

A growth or persistence signal may indicate urbanization, but not necessarily favela extent.

### 2. Temporal comparison is methodologically useful

Despite this limitation, temporal GHSL analysis is still valuable because it helps interpret why single-epoch support may be incomplete or ambiguous.

This is especially useful in the Brasília pilot, where apparent disagreement may reflect data timing rather than simple polygon error.

### 3. Technical uncertainty remains significant

Temporal comparison across GHSL epochs may be affected by:

- raster alignment issues,
- differences in spatial resolution,
- product inconsistencies,
- and threshold sensitivity.

These factors make temporal outputs informative, but not reliable enough to be treated as direct label truth.

### 4. The project favors conservative refinement

The broader methodological direction of the project is to refine official polygons conservatively rather than replace them with auxiliary raster outputs.

Using temporal change as a direct labeling source would conflict with this principle.

---

## Consequences

### Positive consequences

- temporal GHSL analysis can still be documented and used meaningfully,
- the project gains a useful interpretive tool for explaining mismatch,
- persistent built-up areas may strengthen contextual confidence,
- and the refinement workflow remains methodologically conservative.

### Negative consequences

- temporal outputs cannot directly solve the refinement problem,
- additional refinement evidence is still required,
- and the temporal workflow remains supportive rather than decisive.

---

## Operational guidance

The following operational rules apply.

### Allowed uses
Temporal GHSL outputs may be used for:

- QGIS interpretation and visual overlays,
- experiment reporting,
- status notes and thesis discussion,
- identifying stable built-up context,
- motivating future fusion hypotheses.

### Disallowed uses
Temporal GHSL outputs should not be used for:

- direct polygon clipping,
- direct polygon replacement,
- automatic label generation without other supporting evidence,
- or as the sole justification for removing official polygon regions.

---

## Relationship to other methods

This decision places temporal GHSL analysis in a different methodological category from:

- **GHSL refinement**, which uses built-up evidence more directly,
- **MapBiomas refinement**, which is being tested for vegetation-related trimming,
- and **future multi-source fusion**, where temporal persistence may later contribute as a contextual confidence signal.

At the current stage, temporal change remains auxiliary rather than operational.

---

## Future review

This decision may be revisited later if:

- temporal products prove more stable than expected,
- a validated fusion framework is developed,
- or persistent built-up evidence is shown to improve multi-source refinement in a controlled and conservative way.

Until then, the policy remains:

> temporal GHSL change products are for interpretation and diagnosis, not direct label definition.