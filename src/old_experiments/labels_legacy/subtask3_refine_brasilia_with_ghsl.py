from pathlib import Path

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from skimage.morphology import remove_small_objects

from skimage.morphology import binary_closing, disk, remove_small_objects
from scipy.ndimage import binary_fill_holes


# Inputs
POLYGONS_GPKG = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
POLYGONS_LAYER = "favelas_brasilia"
GHSL_CLIP_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_aoi_clip.tif")

# Outputs
OUT_DIR = Path("data/interim/masks")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_POLY_MASK = OUT_DIR / "brasilia_polygon_mask.tif"
OUT_REFINED = OUT_DIR / "brasilia_refined_mask.tif"

# Parameters (tune after QC)
GHSL_THRESHOLD = 20          # start here (values are 0..100)
MIN_COMPONENT_PIXELS = 100   # 100 pixels at 10m ≈ 10,000 m²
ALL_TOUCHED = False


def main():
    # 1) Open GHSL clip (defines grid)
    with rasterio.open(GHSL_CLIP_TIF) as src:
        meta = src.meta.copy()
        transform = src.transform
        crs = src.crs
        height, width = src.height, src.width
        ghsl = src.read(1)
        nodata = src.nodata

    if crs is None:
        raise ValueError("GHSL clip has no CRS.")

    # 2) Load polygons and reproject to GHSL CRS
    gdf = gpd.read_file(POLYGONS_GPKG, layer=POLYGONS_LAYER)
    if gdf.crs is None:
        raise ValueError("Polygons CRS missing.")
    if gdf.crs != crs:
        gdf = gdf.to_crs(crs)

    geoms = [geom for geom in gdf.geometry if geom is not None and not geom.is_empty]
    if not geoms:
        raise ValueError("No geometries found in Brasília polygons layer.")

    # 3) Rasterize polygons -> polygon mask
    poly_mask = rasterize(
        [(geom, 1) for geom in geoms],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype="uint8",
        all_touched=ALL_TOUCHED,
    )

    mask_meta = meta.copy()
    mask_meta.update({"dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"})

    with rasterio.open(OUT_POLY_MASK, "w", **mask_meta) as dst:
        dst.write(poly_mask, 1)

    # 4) Build-up mask with nodata handling
    if nodata is not None:
        valid = ghsl != nodata
    else:
        valid = np.ones_like(ghsl, dtype=bool)

    builtup = (ghsl >= GHSL_THRESHOLD) & valid

    # 5) Refine
    refined = (poly_mask == 1) & builtup
    
    # Fill gaps and holes inside settlement regions within polygons
    refined = binary_closing(refined, footprint=disk(3))   # radius 3 pixels = 30m (tune 2–5)
    refined = binary_fill_holes(refined)                   # fills internal holes
    refined = remove_small_objects(refined, min_size=200)  # remove tiny leftover specks


    # 6) Cleanup small blobs
    refined_clean = remove_small_objects(refined, min_size=MIN_COMPONENT_PIXELS)
    refined_u8 = refined_clean.astype("uint8")

    with rasterio.open(OUT_REFINED, "w", **mask_meta) as dst:
        dst.write(refined_u8, 1)

    # 7) Stats
    poly_pixels = int(poly_mask.sum())
    refined_pixels = int(refined_u8.sum())
    ratio = float(refined_pixels / poly_pixels) if poly_pixels > 0 else 0.0

    print("✅ Saved polygon mask:", OUT_POLY_MASK)
    print("✅ Saved refined mask:", OUT_REFINED)
    print("Stats:")
    print("  CRS:", crs)
    print("  GHSL_THRESHOLD:", GHSL_THRESHOLD)
    print("  MIN_COMPONENT_PIXELS:", MIN_COMPONENT_PIXELS)
    print("  ALL_TOUCHED:", ALL_TOUCHED)
    print("  polygon pixels:", poly_pixels)
    print("  refined pixels:", refined_pixels)
    print("  refined/polygon ratio:", ratio)


if __name__ == "__main__":
    main()