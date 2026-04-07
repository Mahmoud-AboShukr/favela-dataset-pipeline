# Run Brazil Pipeline

## Purpose

This page documents how to run the current active Brazil-scale favela refinement pipeline.

The workflow is implemented under:

`src/final_pipeline_scale_up/src`

and the outputs are written under:

`data/processed/final_pipeline_scale_up`

---

## Prerequisites

Before running the pipeline, make sure that:

- the Python environment is activated,
- the required geospatial packages are installed,
- the raw raster data are available in `data/raw/...`,
- the favela input layer is available,
- and the repository paths match the current expected structure.

---

## Main scripts

The active workflow is composed of:

1. `1_prepare_inputs.py`
2. `2_build_refined_mask.py`
3. `3_polygonize_and_qc.py`
4. `4_merge_brazil_polygons.py`

---

## Stage 1 — Prepare inputs

### Purpose
Prepare chunk-level aligned raster and vector inputs.

### Run on a few chunks first
```powershell
python src\final_pipeline_scale_up\src\1_prepare_inputs.py --limit 2
```

### Run one specific chunk
```powershell
python src\final_pipeline_scale_up\src\1_prepare_inputs.py --chunk-id chunk_000001
```

### Run all active chunks
```powershell
python src\final_pipeline_scale_up\src\1_prepare_inputs.py
```

### Overwrite existing prepared outputs
```powershell
python src\final_pipeline_scale_up\src\1_prepare_inputs.py --overwrite
```

### Save a log
```powershell
python src\final_pipeline_scale_up\src\1_prepare_inputs.py | Tee-Object -FilePath prepare_all_brazil_log.txt
```

### Main outputs
- `chunk_index.gpkg`
- per-chunk `prepared/` folders

---

## Stage 2 — Build refined mask

### Purpose
Apply the active raster refinement rule to each prepared chunk.

### Test on a few chunks first
```powershell
python src\final_pipeline_scale_up\src\2_build_refined_mask.py --limit 2
```

### Run one specific chunk
```powershell
python src\final_pipeline_scale_up\src\2_build_refined_mask.py --chunk-id chunk_000001
```

### Run all chunks
```powershell
python src\final_pipeline_scale_up\src\2_build_refined_mask.py
```

### Overwrite existing outputs
```powershell
python src\final_pipeline_scale_up\src\2_build_refined_mask.py --overwrite
```

### Save a log
```powershell
python src\final_pipeline_scale_up\src\2_build_refined_mask.py | Tee-Object -FilePath refine_all_brazil_log.txt
```

### Main outputs per chunk
- `refined/refined_mask.tif`
- `refined/refined_mask_clean.tif`
- `refined/pixel_summary.json`

---

## Stage 3 — Polygonize and QC

### Purpose
Polygonize the cleaned refined mask and compute basic QC summaries.

### Test on a few chunks first
```powershell
python src\final_pipeline_scale_up\src\3_polygonize_and_qc.py --limit 2
```

### Run one specific chunk
```powershell
python src\final_pipeline_scale_up\src\3_polygonize_and_qc.py --chunk-id chunk_000001
```

### Run all chunks
```powershell
python src\final_pipeline_scale_up\src\3_polygonize_and_qc.py
```

### Overwrite existing polygon outputs
```powershell
python src\final_pipeline_scale_up\src\3_polygonize_and_qc.py --overwrite
```

### Save a log
```powershell
python src\final_pipeline_scale_up\src\3_polygonize_and_qc.py | Tee-Object -FilePath polygonize_all_brazil_log.txt
```

### Main outputs per chunk
- `polygonized/refined_raw.gpkg`
- `polygonized/refined_dissolved.gpkg`
- `polygonized/qc_metrics.json`
- `polygonized/qc_metrics.csv`

---

## Stage 4 — Merge Brazil polygons

### Purpose
Merge chunk-level polygon outputs into Brazil-wide layers.

### Run merge
```powershell
python src\final_pipeline_scale_up\src\4_merge_brazil_polygons.py
```

### Merge only dissolved polygons
```powershell
python src\final_pipeline_scale_up\src\4_merge_brazil_polygons.py --skip-raw
```

### Merge only raw polygons
```powershell
python src\final_pipeline_scale_up\src\4_merge_brazil_polygons.py --skip-dissolved
```

### Main outputs
- `data/processed/final_pipeline_scale_up/brazil_refined_raw.gpkg`
- `data/processed/final_pipeline_scale_up/brazil_refined_dissolved.gpkg`

---

## Recommended execution order

For a full run, use the following order:

1. run Stage 1,
2. run Stage 2,
3. run Stage 3,
4. run Stage 4 merge.

---

## Recommended validation order

Before running the full country, it is recommended to:

1. test Stage 1 on 1–2 chunks,
2. test Stage 2 on 1–2 chunks,
3. test Stage 3 on 1–2 chunks,
4. inspect outputs in QGIS,
5. then launch all-Brazil runs.

---

## Current known behavior

The current workflow has already been run successfully at national scale across 407 active chunks.

The main remaining work after the pipeline run is:

- visual validation,
- QC aggregation,
- chunk-boundary review,
- and preparation for the satellite-image phase.
