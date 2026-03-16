# Chapter Draft — Discussion

## Introduction

This chapter discusses the methodological implications of the Brasília pilot experiments conducted for the favela dataset pipeline.

The project began with the objective of refining official favela polygons using auxiliary geospatial evidence in order to build a deep-learning-ready dataset for Brazil. Initially, the working assumption was that a built-up or settlement-related raster source such as **GHSL** might provide a sufficiently strong basis for polygon refinement. However, as the pilot evolved, it became clear that the refinement problem is more complex than a simple raster-vector intersection or thresholding task.

The main issue is that official favela polygons are not uniformly wrong, but **partially noisy**. In many cases, the relevant question is not “where is the settlement?” in a general sense, but rather “which parts of the official polygon are clearly inconsistent with the intended label?” This distinction changes the interpretation of the whole problem.

The Brasília pilot therefore gradually shifted from a search for a single refinement raster toward a broader **evidence-based refinement framework**, in which multiple data sources are evaluated according to the specific role they can play in a conservative correction workflow.

---

## From direct replacement to conservative refinement

One of the most important lessons from the pilot is that polygon refinement should be framed as a **conservative correction problem**, not as a full redelineation problem.

At first glance, it is tempting to assume that an external settlement mask could simply replace or strongly constrain the official polygons. However, the experiments showed that this assumption is too simplistic. Auxiliary raster products such as GHSL may provide useful built-up support, but they do not necessarily align with the true geometry of the official favela polygons in a way that permits direct substitution.

This is especially important in informal-settlement mapping, where the polygon interior may contain:

- heterogeneous built-up density,
- narrow vegetation patches,
- mixed anthropic and non-anthropic land cover,
- fragmented structures,
- and ambiguous margins.

As a result, a direct replacement strategy risks producing outputs that are:

- too sparse,
- overly fragmented,
- geometrically unrealistic,
- or disconnected from the original label intent.

The pilot therefore supports a different interpretation: the official polygon should remain the **backbone of the label**, while auxiliary data should be used to refine it conservatively, especially where the external evidence strongly suggests that some outer portions are inconsistent with the intended settlement extent.

---

## What the GHSL baseline revealed

The GHSL baseline played a central role in clarifying the problem.

GHSL was initially attractive because it offers a built-up or settlement-related representation that is directly relevant to the general question of urbanized land. As a baseline source, it provided several advantages:

- it is scalable,
- raster-based,
- methodologically relevant,
- and naturally connected to settlement-support estimation.

However, the pilot also revealed several limitations that reduced the suitability of GHSL as a standalone final refinement source.

### 1. Sparsity and threshold sensitivity

One key issue is that GHSL-derived support can become too sparse depending on the chosen threshold or product interpretation. When that happens, the resulting support mask may underrepresent plausible settlement areas and encourage over-aggressive trimming.

This is especially problematic if the refinement logic depends on a binary settlement-support mask. A small change in threshold may substantially alter the overlap between the mask and the official polygon, which suggests that the refinement result is not stable enough to rely on GHSL alone without careful contextual interpretation.

### 2. Built-up support is not equivalent to favela geometry

Another key lesson is that built-up support is not the same thing as favela identity. GHSL may indicate where built structure exists, but it does not specifically distinguish informal settlement from other urban land use. Therefore, even if GHSL is relevant, it cannot be interpreted as a direct favela truth layer.

### 3. Raster support alone is not enough

The pilot also showed that a useful refinement method requires more than built-up presence alone. Since the actual problem often involves removing vegetation or other non-settlement margins, a purely built-up-driven source may be informative but incomplete.

Taken together, these findings suggest that GHSL is valuable as a **baseline built-up evidence source**, but insufficient as a universal solution to the refinement problem.

---

## What the temporal GHSL experiment contributed

The temporal GHSL experiment made a different kind of contribution.

Unlike the baseline GHSL refinement workflow, the temporal-change experiment was not designed to provide a direct refinement mask. Instead, it served as a **diagnostic tool** that helped interpret disagreement between the official polygons and single-epoch GHSL support.

This experiment was important for at least three reasons.

### 1. It exposed the role of temporal mismatch

A weak overlap between a polygon and a GHSL layer does not automatically imply label error. It may also result from differences in time between the vector label, the raster epoch, or actual urban growth. Temporal comparison helps make this ambiguity visible.

### 2. It highlighted the value of persistence

Among the temporal outputs, persistent built-up areas across epochs appear to be the most interpretable and methodologically useful. They do not provide direct settlement truth, but they can increase confidence that some urbanized support is stable rather than incidental.

### 3. It reinforced the need for caution

The experiment also showed that temporal change is difficult to interpret cleanly when the underlying rasters differ in resolution, thresholding behavior, or product structure. Apparent growth or loss may reflect technical harmonization effects as much as real urban change.

This means that temporal GHSL outputs are best treated as **contextual evidence** rather than direct refinement truth. Their contribution is still important, because they improve diagnosis and interpretation, but they do not solve the core label-refinement problem on their own.

---

## Why vegetation removal became central

As the pilot progressed, it became clearer that the most immediate practical error in the polygons was often the inclusion of **vegetated or non-settlement margins** rather than the complete absence of built-up support.

This realization is methodologically significant.

It implies that a refinement source should not only indicate where urbanization exists, but also help identify where the official polygon likely extends into areas that are inconsistent with the intended label. In other words, the problem is partly a **negative identification problem**:

> which parts of the polygon should probably not be there?

This is one reason why a land-cover source such as MapBiomas became increasingly relevant. A source that can identify vegetation-like classes may be more directly aligned with the practical objective of removing obvious non-settlement areas than a source that only indicates built-up intensity.

This does not make built-up support irrelevant. On the contrary, built-up support remains necessary to avoid over-trimming. But it suggests that the problem may be better solved by combining:

- a source for vegetation-like evidence,
- and a source for built-up protection.

This insight strongly motivates the later move toward **multi-source fusion**.

---

## Why MapBiomas is promising, but not guaranteed to be sufficient

The MapBiomas pilot represents an important methodological shift because it tests whether a land-cover source can provide a simpler and more operational starting point for the refinement task.

This is promising for several reasons:

- it targets vegetation more directly,
- it avoids immediate reliance on cloud-sensitive NDVI preprocessing,
- and it introduces a class-based interpretation that is easier to explain in early pilot work.

However, several limitations remain.

### 1. Land-cover classes may still be too coarse

Even if vegetation classes are correctly identified, the spatial granularity may not always be sufficient for precise polygon-edge correction.

### 2. Real settlement areas may contain vegetation

A valid favela polygon may still include internal vegetation, mixed surfaces, or anthropic areas that are not strictly “urban” in a narrow land-cover sense. Therefore, vegetation-like classes cannot be interpreted as automatic removal everywhere.

### 3. Thematic interpretation is not perfect geometry

MapBiomas is semantically rich, but that does not mean it can be used as direct geometry truth. Like GHSL, it is most useful when interpreted conservatively and role-specifically.

The likely conclusion is that MapBiomas may be highly useful for **vegetation-related refinement**, but may still require a complementary built-up support source to avoid excessive removal.

---

## The case for role-based evidence

One of the strongest conclusions emerging from the pilot is that auxiliary sources should not be evaluated only by asking whether they are “good” or “bad.” Instead, they should be evaluated according to the **role** they can play.

This is a more precise and more useful way to frame the problem.

For example:

- GHSL is strong as **built-up support**
- temporal GHSL is useful as **contextual diagnosis**
- MapBiomas is promising as **vegetation-removal evidence**

These are not competing versions of the same signal. They are different signals with different methodological functions.

This role-based interpretation has an important implication: the final refinement workflow may be more robust if it is designed as a system in which each source contributes according to its specific strength, rather than trying to force one source to solve the entire problem alone.

---

## Why multi-source fusion is the logical next step

The experimental results so far suggest that **multi-source fusion** is likely to become the most defensible next methodological step if no single source proves sufficient alone.

The reason is not simply that “more data is better,” but that the sources appear to be **complementary**.

A plausible future configuration is:

- MapBiomas for vegetation-removal evidence,
- GHSL for built-up protection,
- temporal GHSL outputs for contextual confidence and interpretation.

Such a configuration would align naturally with the actual refinement problem:

- vegetation-like evidence proposes what might be removable,
- built-up evidence protects what should plausibly remain,
- temporal context explains uncertainty or disagreement.

This is a more nuanced design than direct replacement or direct thresholding, and it is much better aligned with the complexities of informal-settlement mapping.

At the same time, fusion should not be introduced too early. It adds:

- preprocessing complexity,
- alignment challenges,
- rule-design choices,
- and interpretive burden.

For that reason, the strategy of first testing single-source sufficiency in Brasília remains methodologically sound.

---

## Boundary-aware refinement as a strong design principle

Another important design principle emerging from the pilot is that refinement should likely be **boundary-aware**.

The experiments suggest that many of the most important errors occur at polygon margins rather than in the deep interior. This supports the idea of preserving the polygon core while allowing more flexible edits near the edge.

This principle has several advantages:

- it preserves shape realism,
- it reduces the chance of fragmenting the polygon,
- and it aligns with the intuition that many official delineation errors are marginal rather than total.

Boundary-aware refinement is therefore not just a technical convenience. It is increasingly supported by the empirical logic of the pilot and may become one of the central design principles of the final workflow.

---

## Limits of the current experimental stage

The current project stage also has important limitations that must be acknowledged honestly.

### 1. Single pilot area

Brasília is useful as a controlled sandbox, but it is only one urban context. Favela morphology and land-cover context may differ substantially across Brazil.

### 2. Limited external validation

At this stage, the evaluation is still based mainly on methodological reasoning, visual QC, and internal consistency rather than on a large hand-validated benchmark.

### 3. Product mismatch

The auxiliary raster sources differ in:

- time,
- semantics,
- resolution,
- and spatial behavior.

This makes comparison informative, but also methodologically difficult.

### 4. Intrinsic ambiguity of the target

The concept of a favela boundary is itself not always perfectly crisp at fine spatial scale. Some ambiguity is therefore structural, not merely technical.

These limitations do not invalidate the pilot. Rather, they clarify why conservative refinement and clear documentation are so important.

---

## Overall interpretation

Taken together, the pilot experiments support a broader methodological reinterpretation of the project.

The problem is not best understood as:

> find one raster source that matches the official polygons.

Instead, it is better understood as:

> design a conservative, interpretable, and scalable workflow that uses auxiliary evidence to remove clearly inconsistent polygon regions while preserving realistic settlement structure.

This is a more difficult problem, but it is also a more realistic and scientifically defensible one.

In that framing:

- GHSL remains important as a built-up baseline,
- temporal GHSL strengthens diagnosis and interpretation,
- MapBiomas becomes important for vegetation-related refinement,
- and multi-source fusion emerges as a likely future direction.

---

## Conclusion

The discussion of the Brasília pilot suggests that the refinement problem cannot be solved reliably by a single naive raster operation. Instead, it requires a careful balance between:

- preserving the official polygon,
- removing clearly wrong areas,
- interpreting multiple evidence sources according to their role,
- and maintaining geometric realism.

The current evidence supports a shift from a GHSL-only refinement narrative to a broader **modular refinement framework**.

This framework is built on four central ideas:

1. the official polygon remains the backbone of the label,
2. refinement should be conservative rather than reconstructive,
3. auxiliary sources should be used according to their strengths,
4. and multi-source fusion may ultimately provide the most robust solution.

This discussion therefore lays the foundation for the next stage of the project, in which the Brasília pilot will determine whether MapBiomas alone is sufficient or whether a fused vegetation-plus-built-up strategy is required.