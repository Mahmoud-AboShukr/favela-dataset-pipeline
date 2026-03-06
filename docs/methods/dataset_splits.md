# Dataset Splits (Train / Validation / Test)

This document defines the dataset split strategy to ensure a fair evaluation and avoid spatial leakage.

---

## 1. Why spatial splits are required
If we randomly split patches across the whole AOI, neighboring patches can end up in train and test sets, causing leakage:
- the model sees almost the same urban structures during training
- test performance becomes over-optimistic

Therefore, splits must be **spatially separated**.

---

## 2. Split strategy (confirmed direction)
### Scaling stage: split by state (preferred)
Since the pipeline is organized state-by-state, splits can be defined at the state level or within states using spatial blocks.

Two practical options:
1) **Hold-out states** (strongest leakage control)
- train on a subset of states
- validate/test on different states

2) **Spatial blocks within each state** (more balanced)
- divide each state into large spatial blocks
- assign blocks to train/val/test

---

## 3. Recommended ratios
Default:
- Train: 70%
- Validation: 15%
- Test: 15%

(Exact ratios can be adjusted based on state coverage and class prevalence.)

---

## 4. Implementation notes
- Keep split assignment in a single index table (CSV/Parquet) stored with dataset outputs.
- Each patch record should include:
  - state
  - bounds/centroid
  - split label (train/val/test)
  - acquisition metadata (dates, cloud stats)
- Avoid splitting by time if the goal is spatial generalization; time-based splits are a different evaluation scenario.

---

## 5. Reporting
Always report performance per split plus:
- performance by state
- performance by urban density group (if relevant)
- failure cases with QC overlays