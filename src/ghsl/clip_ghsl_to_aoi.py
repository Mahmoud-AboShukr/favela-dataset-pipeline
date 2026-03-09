from pathlib import Path
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping

GHSL_DIR = Path("data/raw/ghsl")
AOI_GPKG = Path("data/interim/aoi/brasilia_aoi_from_favelas.gpkg")
AOI_LAYER = "brasilia_aoi"

OUT_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_aoi_clip.tif")

def intersects(a, b):
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])

def main():
    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)

    aoi = gpd.read_file(AOI_GPKG, layer=AOI_LAYER)
    if aoi.empty or aoi.crs is None:
        raise ValueError("AOI is missing or CRS not set.")
    aoi_geom_wgs84 = aoi.to_crs("EPSG:4326").geometry.union_all()

    tifs = sorted(GHSL_DIR.glob("*.tif"))
    if not tifs:
        raise FileNotFoundError(f"No GHSL tiles in {GHSL_DIR.resolve()}")

    selected = None
    for tif in tifs:
        with rasterio.open(tif) as src:
            if src.crs is None:
                continue
            aoi_r = gpd.GeoSeries([aoi_geom_wgs84], crs="EPSG:4326").to_crs(src.crs)
            rb = src.bounds
            if intersects(aoi_r.iloc[0].bounds, (rb.left, rb.bottom, rb.right, rb.top)):
                selected = tif
                break

    if selected is None:
        raise ValueError("No GHSL tile overlaps AOI. Download the correct tile(s).")

    with rasterio.open(selected) as src:
        aoi_r = gpd.GeoSeries([aoi_geom_wgs84], crs="EPSG:4326").to_crs(src.crs)
        clipped, clipped_transform = mask(src, [mapping(aoi_r.iloc[0])], crop=True, filled=True)

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

    print("✅ Selected:", selected)
    print("✅ AOI clip:", OUT_TIF)
    print("✅ Shape:", clipped.shape)
    print("✅ CRS:", out_meta.get("crs"))

if __name__ == "__main__":
    main()