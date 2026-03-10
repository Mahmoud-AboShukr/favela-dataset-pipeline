from pathlib import Path

import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping

GHSL_DIR = Path("data/raw/ghsl")
POLYGONS_GPKG = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
POLYGONS_LAYER = "favelas_brasilia"
OUT_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_clip.tif")

BUFFER_M = 2000  # 2 km buffer in raster CRS (meters)

def intersects(a, b):
    # a, b: (minx, miny, maxx, maxy)
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])

def main():
    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(POLYGONS_GPKG, layer=POLYGONS_LAYER)
    if gdf.crs is None or gdf.empty:
        raise ValueError("Brasília polygons CRS missing or layer empty.")

    tifs = sorted(GHSL_DIR.glob("*.tif"))
    if not tifs:
        raise FileNotFoundError(f"No .tif found in {GHSL_DIR.resolve()}")

    selected = None
    selected_info = None

    for tif in tifs:
        with rasterio.open(tif) as src:
            if src.crs is None:
                continue
            gdf_r = gdf.to_crs(src.crs)

            # use union_all() to avoid the unary_union deprecation warning
            geom = gdf_r.geometry.union_all()
            geom_buf = geom.buffer(BUFFER_M)

            poly_bounds = geom_buf.bounds
            rb = src.bounds
            raster_bounds = (rb.left, rb.bottom, rb.right, rb.top)

            if intersects(poly_bounds, raster_bounds):
                selected = tif
                selected_info = (src.crs, raster_bounds, poly_bounds)
                break

    if selected is None:
        raise ValueError(
            "No GHSL tile in data/raw/ghsl overlaps Brasília polygons.\n"
            "➡ Download the correct 10m GHSL tile(s) around Brasília and try again."
        )

    # Clip using selected tile
    with rasterio.open(selected) as src:
        gdf_r = gdf.to_crs(src.crs)
        geom = gdf_r.geometry.union_all().buffer(BUFFER_M)
        clipped, clipped_transform = mask(
            src, [mapping(geom)], crop=True, all_touched=False, filled=True
        )

        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": clipped_transform,
            "compress": "deflate",
        })
        if src.nodata is not None:
            out_meta["nodata"] = src.nodata

    with rasterio.open(OUT_TIF, "w", **out_meta) as dst:
        dst.write(clipped)

    print("✅ Selected tile:", selected)
    print("✅ Output:", OUT_TIF)
    print("✅ Output shape (bands, height, width):", clipped.shape)
    print("✅ CRS:", selected_info[0])

if __name__ == "__main__":
    main()