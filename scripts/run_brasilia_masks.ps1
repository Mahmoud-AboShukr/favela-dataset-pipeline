# scripts/run_brasilia_masks.ps1
# Run the core Brasأ­lia masks pipeline (edit paths if needed)

.\\venv\\Scripts\\Activate.ps1

# 1) Clean polygons (input shapefile path must be absolute)
# python .\\src\\labels\\subtask1_clean_polygons.py "C:\\full\\path\\to\\data\\raw\\favelas_shp\\favelas.shp"

# 2) Extract Brasأ­lia subset
python .\\src\\labels\\subtask1_extract_brasilia.py

# 3) Inspect GHSL (edit src/ghsl/inspect_ghsl.py TIF variable)
python .\\src\\ghsl\\inspect_ghsl.py

# 4) Clip GHSL to Brasأ­lia (auto-select tile overlap)
python .\\src\\ghsl\\clip_ghsl_auto_select.py

# 5) Generate refined mask (close QGIS to avoid file locks)
python .\\src\\labels\\subtask3_refine_brasilia_with_ghsl.py
