from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape


IN_MASK = Path("data/interim/masks/brasilia_favela_refined_mapbiomas_no_ring_v2_2_fillholes_4px.tif")

OUT_DIR = Path("data/interim/refined_labels_mapbiomas")
OUT_GPKG = OUT_DIR / "brasilia_favela_refined_mapbiomas_no_ring_v2_2_fillholes_4px.gpkg"
OUT_DISSOLVED_GPKG = OUT_DIR / "brasilia_favela_refined_mapbiomas_no_ring_v2_2_fillholes_4px_dissolved.gpkg"

OUT_LAYER = "refined_mapbiomas"
OUT_DISSOLVED_LAYER = "refined_mapbiomas_dissolved"

MIN_POLYGON_PIXELS = 2  # raise later if you want to drop tiny pieces


def main():
    if not IN_MASK.exists():
        raise FileNotFoundError(f"Input mask not found: {IN_MASK}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(IN_MASK) as src:
        arr = src.read(1)
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

        valid = np.ones(arr.shape, dtype=bool)
        if nodata is not None:
            valid = arr != nodata

        foreground = (arr == 1) & valid

        results = []
        for geom, value in shapes(
            arr.astype("uint8"),
            mask=foreground,
            transform=transform,
            connectivity=8
        ):
            if int(value) != 1:
                continue

            poly = shape(geom)
            if poly.is_empty:
                continue

            results.append({
                "value": 1,
                "geometry": poly
            })

    if not results:
        raise ValueError("No foreground polygons were extracted from the refined mask.")

    gdf = gpd.GeoDataFrame(results, crs=crs)

    # Area in pixels, approximated from geometry count after raster polygonization is not direct,
    # so compute metric area too.
    metric_crs = "EPSG:31983"
    gdf_metric = gdf.to_crs(metric_crs)
    gdf["area_m2"] = gdf_metric.area

    # Optional tiny-piece filter using area threshold derived from pixel size
    with rasterio.open(IN_MASK) as src:
        px_x, px_y = src.res
    # Approximate pixel area in degrees is not meaningful, so use metric area threshold.
    # 30m raster pixel ~ 900 m². Keep threshold configurable by pixel count.
    min_area_m2 = MIN_POLYGON_PIXELS * 900.0
    gdf = gdf[gdf["area_m2"] >= min_area_m2].copy()

    if gdf.empty:
        raise ValueError("All polygons were filtered out. Lower MIN_POLYGON_PIXELS.")

    gdf["poly_id"] = np.arange(len(gdf), dtype=int)

    # Save raw polygonized output
    gdf.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")

    # Dissolve all foreground into multipart geometry
    dissolved = gdf.dissolve()
    dissolved = dissolved.reset_index(drop=True)
    dissolved["dissolve_id"] = 1

    dissolved_metric = dissolved.to_crs(metric_crs)
    dissolved["area_m2"] = dissolved_metric.area

    dissolved.to_file(OUT_DISSOLVED_GPKG, layer=OUT_DISSOLVED_LAYER, driver="GPKG")

    print(f"Saved polygonized output: {OUT_GPKG}")
    print(f"Saved dissolved output: {OUT_DISSOLVED_GPKG}")
    print(f"Number of polygon pieces: {len(gdf)}")
    print(f"Dissolved features: {len(dissolved)}")
    print(f"Total area (m²): {gdf['area_m2'].sum():.2f}")


if __name__ == "__main__":
    main()