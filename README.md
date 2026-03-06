# Favela Dataset Pipeline (Brazil) — Polygons → GHSL-refined Masks → Sentinel-1/2 Dataset

This repository builds a Deep Learning–ready dataset for favela detection in Brazil by:
1) ingesting the official Brazilian government favela polygons,
2) refining them using GHSL (Global Human Settlement Layer) evidence to remove vegetation / non-built-up areas,
3) generating binary masks (0 = non-favela, 1 = favela),
4) aligning the masks with Sentinel-2 (optical) and Sentinel-1 (SAR) imagery,
5) exporting tile-based stacks and training patches for semantic segmentation.

We start **tile-by-tile** with a **Brasília pilot** before scaling to all Brazil.

---

## Repository structure

favela-dataset-pipeline/
├─ README.md
├─ pyproject.toml # or requirements.txt
├─ .gitignore
├─ config/
│ ├─ config.yaml # pipeline configuration
│ └─ secrets.env # optional (DO NOT commit)
├─ data/
│ ├─ raw/
│ │ ├─ favelas_gov/ # original shapefile bundle
│ │ ├─ ghsl/ # GHSL rasters
│ │ └─ sentinel/
│ │ ├─ s2/ # raw S2 exports / SAFE / COGs
│ │ └─ s1/ # raw S1 exports / SAFE / COGs
│ ├─ interim/
│ │ ├─ polygons_clean/ # Subtask 1 output (clean polygons)
│ │ ├─ tiles/ # tile grid + tile index
│ │ ├─ ghsl_clips/ # per-tile GHSL windows
│ │ └─ masks/ # per-tile masks (pre/post refinement)
│ └─ processed/
│ ├─ brasilia_pilot/ # pilot dataset outputs
│ └─ brazil_full/ # full-country outputs (later)
├─ notebooks/ # exploration & QC notebooks only
├─ src/ # pipeline code (reusable + testable)
├─ scripts/ # helper run scripts
└─ reports/ # QC overlays + notes


---

## Environment setup

### Option A — requirements.txt
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
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt