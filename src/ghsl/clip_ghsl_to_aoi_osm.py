from pathlib import Path
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping

GHSL_DIR = Path("data/raw/ghsl")
AOI_GPKG = Path("data/interim/aoi/brasilia_boundary.gpkg")
AOI_LAYER = "brasilia_boundary"

OUT_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_full_clip.tif")

def intersects(a, b):
    # a, b: (minx, miny, maxx, maxy)
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])

def main():
    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)

    aoi = gpd.read_file(AOI_GPKG, layer=AOI_LAYER)
    if aoi.empty or aoi.crs is None:
        raise ValueError("AOI boundary is missing or CRS is not set.")

    # dissolve AOI into one geometry and standardize to EPSG:4326 for searching
    aoi_geom_wgs84 = aoi.to_crs("EPSG:4326").geometry.union_all()

    tifs = sorted(GHSL_DIR.glob("*.tif"))
    if not tifs:
        raise FileNotFoundError(f"No GHSL .tif files found in {GHSL_DIR.resolve()}")

    selected = None
    selected_crs = None

    # 1) auto-select a GHSL tile overlapping AOI
    for tif in tifs:
        with rasterio.open(tif) as src:
            if src.crs is None:
                continue

            aoi_r = gpd.GeoSeries([aoi_geom_wgs84], crs="EPSG:4326").to_crs(src.crs)
            geom = aoi_r.iloc[0]

            rb = src.bounds
            raster_bounds = (rb.left, rb.bottom, rb.right, rb.top)

            if intersects(geom.bounds, raster_bounds):
                selected = tif
                selected_crs = src.crs
                break

    if selected is None:
        raise ValueError("No GHSL tile overlaps the Brasília AOI. Download the correct tile(s).")

    # 2) clip selected tile to AOI
    with rasterio.open(selected) as src:
        aoi_r = gpd.GeoSeries([aoi_geom_wgs84], crs="EPSG:4326").to_crs(src.crs)
        geom = aoi_r.iloc[0]

        clipped, clipped_transform = mask(
            src,
            [mapping(geom)],
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

    print("✅ Selected GHSL tile:", selected)
    print("✅ AOI clip saved:", OUT_TIF)
    print("✅ Output shape:", clipped.shape)
    print("✅ CRS:", selected_crs)

if __name__ == "__main__":
    main()