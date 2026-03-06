# Favela Dataset Pipeline (Brazil)
**Polygons → GHSL-refined Masks → Sentinel-1/2 Dataset**

This repository builds a Deep Learning–ready dataset for favela detection in Brazil by:

- ingesting the official Brazilian government favela polygons,
- refining them using GHSL (Global Human Settlement Layer) built-up evidence to remove vegetation / non-built-up areas,
- generating binary masks (**0 = non-favela**, **1 = favela**),
- aligning masks with Sentinel-2 (optical) and Sentinel-1 (SAR) imagery,
- exporting tile-based stacks and training patches for semantic segmentation.

We start with a **Brasília pilot**, then scale to **all Brazil** (organized **by state**) with **512×512** patches.

---

## Repository structure

```text
favela-dataset-pipeline/
├─ README.md
├─ pyproject.toml                 # or requirements.txt
├─ .gitignore
├─ config/
│  ├─ config.yaml                 # pipeline configuration
│  └─ secrets.env                 # optional (DO NOT commit)
├─ data/
│  ├─ raw/
│  │  ├─ favelas_shp/             # original shapefile bundle (shp/shx/dbf/prj/...)
│  │  ├─ ghsl/                    # GHSL rasters (tiles)
│  │  └─ sentinel/
│  │     ├─ s2/                   # raw S2 exports / SAFE / COGs
│  │     └─ s1/                   # raw S1 exports / SAFE / COGs
│  ├─ interim/
│  │  ├─ polygons_clean/          # cleaned polygons + Brasília subset
│  │  ├─ tiles/                   # tiling indexes (later)
│  │  ├─ ghsl_clips/              # clipped GHSL rasters (AOI/state)
│  │  └─ masks/                   # polygon masks + refined masks
│  └─ processed/
│     ├─ brasilia_pilot/          # pilot dataset outputs
│     └─ brazil_full/             # full-country outputs (later)
├─ notebooks/                     # exploration & QC only
├─ src/                           # pipeline code
├─ scripts/                       # helper run scripts
└─ reports/                       # QC overlays + notes
```

---

## Environment setup

### Option A — `requirements.txt`
Create a `requirements.txt` (example):

- geopandas  
- rasterio  
- shapely  
- numpy  
- pandas  
- pyproj  
- rtree  
- matplotlib  
- scikit-image  

Then:

```bash
python -m venv .venv
# Windows:
# .venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate
pip install -r requirements.txt
```

---

## Pipeline overview (current)

### Subtask 1 — Clean polygons ✅
- Input: government shapefile
- Output:
  - `data/interim/polygons_clean/favelas_clean.gpkg`
  - `data/interim/polygons_clean/favelas_clean_summary.csv`

Run:
```powershell
python .\src\labels\subtask1_clean_polygons.py "C:\full\path\to\data\raw\favelas_shp\favelas.shp"
```

### Brasília subset ✅
Output:
- `data/interim/polygons_clean/favelas_brasilia.gpkg`

Run:
```powershell
python .\src\labels\subtask1_extract_brasilia.py
```

### Subtask 2 — GHSL download + clip ✅
- GHSL chosen: **GHS-BUILT, Epoch 2018, 10 m, WGS84**
- Raw tile(s): `data/raw/ghsl/`
- Clip: `data/interim/ghsl_clips/ghsl_brasilia_clip.tif`

Inspect:
```powershell
python .\src\ghsl\inspect_ghsl.py
```

Clip:
```powershell
python .\src\ghsl\clip_ghsl_brasilia.py
```

### Subtask 3 — Refine labels using GHSL (next)
Expected outputs:
- `data/interim/masks/brasilia_polygon_mask.tif`
- `data/interim/masks/brasilia_refined_mask.tif`

---

## Notes
- Keep large data out of git: ignore `data/raw`, `data/interim`, `data/processed`.
- Use QGIS for QC overlays and store evidence under `reports/qc/overlays/`.
