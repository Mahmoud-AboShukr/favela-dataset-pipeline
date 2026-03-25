from pathlib import Path
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping

GHSL_DIR = Path("data/raw/ghsl")
AOI_GPKG = Path("data/interim/aoi/brasilia_boundary.gpkg")
AOI_LAYER = "brasilia_boundary"

OUT_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_aoi_clip.tif")


def intersects(a, b):
    # a, b: (minx, miny, maxx, maxy)
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


def main():
    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)

    # 1) Read AOI and dissolve into one geometry (in EPSG:4326)
    aoi = gpd.read_file(AOI_GPKG, layer=AOI_LAYER)
    if aoi.empty or aoi.crs is None:
        raise ValueError("AOI boundary is missing or CRS is not set.")
    aoi_geom_wgs84 = aoi.to_crs("EPSG:4326").geometry.union_all()

    # 2) Find ALL GHSL tiles that overlap AOI (by bbox test)
    tifs = sorted(GHSL_DIR.glob("*.tif"))
    if not tifs:
        raise FileNotFoundError(f"No GHSL .tif files found in {GHSL_DIR.resolve()}")

    selected = []
    for tif in tifs:
        with rasterio.open(tif) as src:
            if src.crs is None:
                continue
            aoi_r = gpd.GeoSeries([aoi_geom_wgs84], crs="EPSG:4326").to_crs(src.crs)
            geom = aoi_r.iloc[0]
            rb = src.bounds
            raster_bounds = (rb.left, rb.bottom, rb.right, rb.top)
            if intersects(geom.bounds, raster_bounds):
                selected.append(tif)

    if not selected:
        raise ValueError("No GHSL tile overlaps the Brasília AOI. Download the correct tile(s).")

    print("✅ Selected tiles:")
    for s in selected:
        print("   -", s)

    # 3) If only one tile, clip directly (memory-safe)
    if len(selected) == 1:
        selected_tif = selected[0]
        with rasterio.open(selected_tif) as src:
            aoi_r = gpd.GeoSeries([aoi_geom_wgs84], crs="EPSG:4326").to_crs(src.crs)
            geom = aoi_r.iloc[0]

            clipped, clipped_transform = mask(
                src,
                [mapping(geom)],
                crop=True,
                all_touched=False,
                filled=True,
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

        print("✅ AOI GHSL clip saved:", OUT_TIF)
        print("✅ Output shape:", clipped.shape)
        print("✅ CRS:", out_meta.get("crs"))
        return

    # 4) If multiple tiles, do NOT merge in-memory (too big).
    # For now, fail with an explicit message (we can implement a disk-based mosaic later).
    raise RuntimeError(
        f"AOI overlaps {len(selected)} GHSL tiles. In-memory merge would be too large.\n"
        "Next step: implement disk-based mosaic (VRT or windowed merge)."
    )


if __name__ == "__main__":
    main()