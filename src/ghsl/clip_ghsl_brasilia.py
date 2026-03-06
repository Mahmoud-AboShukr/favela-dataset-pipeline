from pathlib import Path

import rasterio
from rasterio.mask import mask
from shapely.geometry import box, mapping


# Same bbox you used earlier (WGS84 / EPSG:4326)
BRASILIA_BBOX = (-48.30, -16.10, -47.50, -15.50)  # (min_lon, min_lat, max_lon, max_lat)

IN_TIF = Path("data/raw/ghsl/brasilia.tif")  # <-- adjust if your filename differs
OUT_TIF = Path("data/interim/ghsl_clips/ghsl_brasilia_clip.tif")


def main():
    if not IN_TIF.exists():
        raise FileNotFoundError(f"Input GHSL file not found: {IN_TIF.resolve()}")

    OUT_TIF.parent.mkdir(parents=True, exist_ok=True)

    # Create bbox polygon (in EPSG:4326)
    bbox_geom = box(*BRASILIA_BBOX)
    bbox_geojson = [mapping(bbox_geom)]

    with rasterio.open(IN_TIF) as src:
        if src.crs is None:
            raise ValueError("GHSL raster has no CRS. Cannot clip safely.")

        # If GHSL is not EPSG:4326, we'd need to reproject bbox.
        # Your inspection shows EPSG:4326, so this is OK.
        if src.crs.to_string() != "EPSG:4326":
            raise ValueError(f"GHSL CRS is {src.crs}, expected EPSG:4326. Reprojection step needed.")

        clipped, clipped_transform = mask(
            src,
            bbox_geojson,
            crop=True,
            all_touched=False,  # change to True if you want more inclusive edge pixels
            filled=True
        )

        # Update metadata for output
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": clipped_transform,
            "compress": "deflate"  # smaller file
        })

    # Write clipped raster
    with rasterio.open(OUT_TIF, "w", **out_meta) as dst:
        dst.write(clipped)

    print("✅ Input:", IN_TIF)
    print("✅ Output:", OUT_TIF)
    print("✅ Output shape (bands, height, width):", clipped.shape)


if __name__ == "__main__":
    main()