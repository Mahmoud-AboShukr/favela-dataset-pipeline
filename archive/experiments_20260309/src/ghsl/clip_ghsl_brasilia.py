from pathlib import Path

import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping


# Inputs
IN_TIF = Path("data/raw/ghsl/brasilia.tif")  # your 10m GHSL tile (ESRI:54009)
POLYGONS_GPKG = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
POLYGONS_LAYER = "favelas_brasilia"

# Output
OUT_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_clip.tif")

# Buffer in meters (raster CRS is meters in Mollweide). Adjust if you want larger context.
BUFFER_M = 2000  # 2 km


def main():
    if not IN_TIF.exists():
        raise FileNotFoundError(f"Input GHSL file not found: {IN_TIF.resolve()}")
    if not POLYGONS_GPKG.exists():
        raise FileNotFoundError(f"Brasília polygons file not found: {POLYGONS_GPKG.resolve()}")

    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)

    # Load polygons (stored in EPSG:4326)
    gdf = gpd.read_file(POLYGONS_GPKG, layer=POLYGONS_LAYER)
    if gdf.crs is None:
        raise ValueError("Brasília polygons CRS is missing.")
    if gdf.empty:
        raise ValueError("Brasília polygons layer is empty.")

    with rasterio.open(IN_TIF) as src:
        if src.crs is None:
            raise ValueError("GHSL raster has no CRS.")

        raster_crs = src.crs
        raster_bounds = src.bounds  # in raster CRS

        # Reproject polygons to raster CRS
        gdf_r = gdf.to_crs(raster_crs)

        # Union geometry and buffer (in meters)
        geom = gdf_r.unary_union
        geom_buf = geom.buffer(BUFFER_M)

        # Quick overlap check using bounds
        geom_bounds = geom_buf.bounds  # (minx, miny, maxx, maxy)

        def intersects(a, b):
            # a and b are (minx, miny, maxx, maxy)
            return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])

        if not intersects(geom_bounds, (raster_bounds.left, raster_bounds.bottom, raster_bounds.right, raster_bounds.top)):
            raise ValueError(
                "Input polygons (after reprojection) do not overlap the GHSL raster tile.\n"
                f"Raster bounds (raster CRS): {raster_bounds}\n"
                f"Buffered polygons bounds: {geom_bounds}\n\n"
                "This usually means the GHSL tile you downloaded does NOT cover Brasília.\n"
                "➡ Fix: download the correct GHSL 10m tile that contains Brasília."
            )

        # Clip raster by buffered geometry
        shapes = [mapping(geom_buf)]
        clipped, clipped_transform = mask(
            src,
            shapes=shapes,
            crop=True,
            all_touched=False,
            filled=True
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

    print("✅ Input:", IN_TIF)
    print("✅ Output:", OUT_TIF)
    print("✅ Raster CRS:", raster_crs)
    print("✅ Output shape (bands, height, width):", clipped.shape)


if __name__ == "__main__":
    main()