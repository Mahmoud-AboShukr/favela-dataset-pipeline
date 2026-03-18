from pathlib import Path

# Cities included in Batch 2
CITIES = [
    "manaus",
    "belo_horizonte",
    "salvador",
]

# Paths
AOI_ROOT = Path("data/interim/aoi")
RASTER_ROOT = Path("data/interim/mapbiomas_10m_clips")
MASK_ROOT = Path("data/interim/masks")
POLY_ROOT = Path("data/processed/polygons")
QC_ROOT = Path("reports/qc/mapbiomas_10m")
BATCH_ROOT = QC_ROOT / "batch2"

# Refinement choice
REFINEMENT_VARIANT = "keep_uncertain"

# MapBiomas class logic
BUILT_CLASSES = {24}
STRICT_VEGETATION_CLASSES = {3, 4, 5, 6, 11, 12, 49, 50}

# Raster output nodata
OUT_NODATA = 255

# Class labels for reports
CLASS_LABELS = {
    0: "Unknown / 0",
    3: "Forest Formation",
    4: "Savanna Formation",
    5: "Mangrove",
    6: "Floodable Forest",
    11: "Wetland",
    12: "Grassland Formation",
    15: "Pasture",
    18: "Agriculture",
    19: "Temporary Crop",
    21: "Mosaic of Uses",
    23: "Beach, Dune and Sand Spot",
    24: "Urban Area",
    25: "Other Non Vegetated Areas",
    27: "Not Observed",
    29: "Rocky Outcrop",
    30: "Mining",
    31: "Aquaculture",
    33: "River, Lake and Ocean",
    36: "Perennial Crop",
    39: "Soybean",
    40: "Rice",
    41: "Other Temporary Crops",
    46: "Coffee",
    47: "Citrus",
    48: "Other Perennial Crops",
    49: "Wooded Sandbank Vegetation",
    50: "Herbaceous Sandbank Vegetation",
    62: "Cotton",
}

# Colors for quick overview figures
CLASS_COLORS = {
    0: "#000000",
    3: "#1b5e20",
    4: "#66bb6a",
    5: "#2e7d32",
    6: "#388e3c",
    11: "#26a69a",
    12: "#9ccc65",
    15: "#c0ca33",
    21: "#d4a373",
    24: "#d32f2f",
    25: "#8d6e63",
    33: "#42a5f5",
    49: "#81c784",
    50: "#aed581",
}
DEFAULT_COLOR = "#bdbdbd"