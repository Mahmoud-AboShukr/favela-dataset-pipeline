# Runbook — How to run this project (Windows / PowerShell)

This runbook lists the exact commands to reproduce the pipeline steps and where outputs are written.  
It is written for **Windows + PowerShell** (your current setup).

---

## 0) Folder conventions (important)

- `data/raw/` = original downloads (do not edit)
- `data/interim/` = intermediate artifacts you can rebuild
- `data/processed/` = final DL-ready dataset outputs
- `src/` = pipeline code (scripts)
- `docs/` = documentation content (MkDocs source)
- `reports/` = QC evidence (overlays, stats, milestone notes)

---

## 1) One-time setup

### 1.1 Create and activate a virtual environment
From the repo root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 1.2 Install Python dependencies

Core geospatial + processing:
```powershell
pip install geopandas rasterio shapely pandas numpy scikit-image
```

Docs tooling (MkDocs):
```powershell
pip install mkdocs==1.6.1 mkdocs-material==9.7.4 pymdown-extensions
```

(If your environment is already installed, you can skip this.)

---

## 2) Documentation workflow (MkDocs)

### 2.1 Serve docs locally (auto-reload)
```powershell
mkdocs serve
```

Open in your browser:
- `http://127.0.0.1:8000/`

**How you use this daily**
- keep `mkdocs serve` running in a terminal
- edit files in `docs/`
- refresh happens automatically

### 2.2 Build a static site (for sharing)
```powershell
mkdocs build
```

This produces a `site/` folder. You can:
- zip `site/` and send it, or
- upload `site/` to OneDrive and share a link

Managers open:
- `site/index.html`

---

## 3) Subtask 1 — Clean government polygons (Brazil-wide)

### 3.1 Inputs
Place the **entire shapefile bundle** in:
- `data/raw/favelas_shp/`

The set must share the same base filename and include at least:
- `.shp` (geometry)
- `.shx` (index)
- `.dbf` (attributes)
- `.prj` (CRS)

Example:
```
data/raw/favelas_shp/
  favelas.shp
  favelas.shx
  favelas.dbf
  favelas.prj
  favelas.cpg   (optional)
```

### 3.2 Run cleaning
Use an **absolute path** on Windows/OneDrive (this avoids file-not-found issues):

```powershell
python .\src\labels\subtask1_clean_polygons.py "C:\Users\acer\OneDrive\Desktop\UMR_espace_dev\favela-dataset-pipeline\data\raw\favelas_shp\favelas.shp"
```

### 3.3 Outputs
- `data/interim/polygons_clean/favelas_clean.gpkg`
- `data/interim/polygons_clean/favelas_clean_summary.csv`

### 3.4 Quick validation (recommended)
- Open `favelas_clean.gpkg` in QGIS and “Zoom to layer”
- Check attribute table has `favela_id`
- Ensure polygons roughly align with basemap (OSM)

---

## 4) Brasília subset extraction (pilot AOI)

### 4.1 Run
```powershell
python .\src\labels\subtask1_extract_brasilia.py
```

### 4.2 Output
- `data/interim/polygons_clean/favelas_brasilia.gpkg` (layer: `favelas_brasilia`)

### 4.3 Quick validation (recommended)
Load `favelas_brasilia.gpkg` in QGIS and confirm it contains only Brasília-area polygons.

---

## 5) Subtask 2 — GHSL download + verification + clipping (Brasília pilot)

### 5.1 Download GHSL tile
Download the GHSL GeoTIFF tile that **covers Brasília** and place it in:
- `data/raw/ghsl/`

Example:
- `data/raw/ghsl/brasilia.tif`

### 5.2 Inspect GHSL metadata (CRS, resolution, bounds, value range)
Edit `src/ghsl/inspect_ghsl.py` and set:
- `TIF = "brasilia"` (substring search) OR
- `TIF = "brasilia.tif"` (exact filename)

Run:
```powershell
python .\src\ghsl\inspect_ghsl.py
```

Confirm:
- CRS is `EPSG:4326` (or note the CRS if different)
- Bounds cover Brasília (lon ~ -48, lat ~ -16)
- Value range makes sense (not just 0/1)

### 5.3 Clip GHSL to Brasília bbox
Ensure `src/ghsl/clip_ghsl_brasilia.py` points to the correct input file:
- `IN_TIF = Path("data/raw/ghsl/brasilia.tif")`

Run:
```powershell
python .\src\ghsl\clip_ghsl_brasilia.py
```

Output:
- `data/interim/ghsl_clips/ghsl_brasilia_clip.tif`

**If you see:** `Input shapes do not overlap raster`  
➡ You downloaded the wrong GHSL tile. Download the correct one (tile bounds must contain Brasília) and retry.

---

## 6) Subtask 3 — Refine Brasília polygons using GHSL (pilot)

### 6.1 Goal
Create a refined binary mask (0/1) by intersecting:
- the rasterized favela polygons mask
- the GHSL built-up evidence via a threshold

Core rule:
- `refined = polygon_mask AND (ghsl >= τ)`

### 6.2 Inputs
- Polygons (Brasília subset):
  - `data/interim/polygons_clean/favelas_brasilia.gpkg`
- GHSL clip:
  - `data/interim/ghsl_clips/ghsl_brasilia_clip.tif`

### 6.3 Run (after creating the script)
Create the script:
- `src/labels/subtask3_refine_brasilia_with_ghsl.py`

Run:
```powershell
python .\src\labels\subtask3_refine_brasilia_with_ghsl.py
```

### 6.4 Outputs
- `data/interim/masks/brasilia_polygon_mask.tif`
- `data/interim/masks/brasilia_refined_mask.tif`

### 6.5 QC in QGIS (required)
Load and overlay in QGIS:
- `data/interim/ghsl_clips/ghsl_brasilia_clip.tif`
- `data/interim/masks/brasilia_polygon_mask.tif`
- `data/interim/masks/brasilia_refined_mask.tif`

What to check:
- refined mask should be **smaller** than polygon mask (vegetation/non-built-up removed)
- it should not disappear completely (threshold too strict)

Save 2–5 screenshots to:
- `reports/qc/overlays/`

Record pixel stats printed by the script and note the chosen threshold τ in:
- `docs/methods/label_refinement.md`

---

## 7) Common Windows issues (fast fixes)

### 7.1 GeoPandas / rasterio “file not found” while file exists
- Use **absolute paths** (OneDrive + GDAL sometimes fails with relative paths).

### 7.2 Shapefile errors: missing .shx/.dbf/.prj
- Ensure all shapefile sidecar files exist and share the same base filename.

### 7.3 GHSL clip fails with overlap error
- Check GHSL bounds from `inspect_ghsl.py`
- Download the correct tile covering Brasília

---

## 8) What comes next (after Subtask 3)
- Subtask 4: define Brasília tiling scheme (tile grid + tile index)
- Subtask 5: Sentinel-2 acquisition + preprocessing
- Subtask 6: Sentinel-1 preprocessing
- Subtask 7/8: co-registration + patch export
- Subtask 9: QC report + threshold sensitivity analysis
- Subtask 10: scale to all Brazil (parallel tile processing)
