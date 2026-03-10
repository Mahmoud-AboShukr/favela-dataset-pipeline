from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from skimage.morphology import binary_closing, disk, remove_small_objects
from scipy.ndimage import binary_fill_holes

POLYGONS_GPKG = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
POLYGONS_LAYER = "favelas_brasilia"

GRID_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_aoi_clip.tif")
SETTLEMENT_TIF = Path("data/interim/masks/brasilia_settlement_mask.tif")

OUT_DIR = Path("data/interim/masks")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_POLY = OUT_DIR / "brasilia_polygon_mask.tif"
OUT_REFINED = OUT_DIR / "brasilia_favela_refined_mask.tif"

ALL_TOUCHED = True
CLOSE_RADIUS = 3
MIN_COMPONENT_PIXELS = 200
FILL_HOLES = True


def safe_write(out_path: Path, meta: dict, arr_u8: np.ndarray) -> Path:
    tmp = out_path.with_name(out_path.stem + "_tmp.tif")
    with rasterio.open(tmp, "w", **meta) as dst:
        dst.write(arr_u8, 1)
    try:
        if out_path.exists():
            out_path.unlink()
        tmp.replace(out_path)
        return out_path
    except Exception as e:
        print(f"⚠ Could not overwrite {out_path} (locked). Kept: {tmp}\n   {e}")
        return tmp


def main():
    # grid defines CRS/transform/shape
    with rasterio.open(GRID_TIF) as grid:
        meta = grid.meta.copy()
        crs = grid.crs
        transform = grid.transform
        height, width = grid.height, grid.width

    # settlement mask must match the grid
    with rasterio.open(SETTLEMENT_TIF) as s:
        settlement = s.read(1).astype(bool)
        if (s.height, s.width) != (height, width):
            raise ValueError("Settlement mask grid does not match GHSL clip grid.")
        if s.crs != crs:
            raise ValueError("Settlement mask CRS does not match GHSL clip CRS.")

    # polygons -> raster CRS
    gdf = gpd.read_file(POLYGONS_GPKG, layer=POLYGONS_LAYER)
    if gdf.crs is None:
        raise ValueError("Polygons CRS missing.")
    gdf = gdf.to_crs(crs)
    geoms = [g for g in gdf.geometry if g is not None and not g.is_empty]
    if not geoms:
        raise ValueError("No geometries to rasterize.")

    # polygon mask
    poly = rasterize(
        [(g, 1) for g in geoms],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype="uint8",
        all_touched=ALL_TOUCHED,
    ).astype(bool)

    # refine
    refined = poly & settlement

    # cleanup
    refined = binary_closing(refined, footprint=disk(CLOSE_RADIUS))
    if FILL_HOLES:
        refined = binary_fill_holes(refined)
    refined = remove_small_objects(refined, min_size=MIN_COMPONENT_PIXELS)

    out_meta = meta.copy()
    out_meta.update({"dtype": "uint8", "count": 1, "nodata": 0, "compress": "deflate"})

    saved_poly = safe_write(OUT_POLY, out_meta, poly.astype("uint8"))
    saved_ref = safe_write(OUT_REFINED, out_meta, refined.astype("uint8"))

    poly_px = int(poly.sum())
    ref_px = int(refined.sum())
    ratio = ref_px / poly_px if poly_px else 0.0

    print("✅ Saved polygon mask:", saved_poly)
    print("✅ Saved refined favela mask:", saved_ref)
    print("Stats:")
    print("  ALL_TOUCHED:", ALL_TOUCHED)
    print("  CLOSE_RADIUS:", CLOSE_RADIUS)
    print("  MIN_COMPONENT_PIXELS:", MIN_COMPONENT_PIXELS)
    print("  polygon_pixels:", poly_px)
    print("  refined_pixels:", ref_px)
    print("  refined/polygon:", ratio)


if __name__ == "__main__":
    main()