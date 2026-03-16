from pathlib import Path
import tempfile
import shutil

import geopandas as gpd
import rasterio
from rasterio.mask import mask


RAW_ROOT = Path("data/raw/mapbiomas")
AOI_PATH = Path("data/interim/aoi/brasilia_boundary.gpkg")
AOI_LAYER = "brasilia_boundary"
OUT_PATH = Path("data/interim/mapbiomas_clips/mapbiomas_brasilia_aoi_clip.tif")


def find_mapbiomas_raster() -> Path:
    candidates = sorted(RAW_ROOT.rglob("*.tif"))

    if not candidates:
        raise FileNotFoundError(
            f"No .tif files found under: {RAW_ROOT}"
        )

    # Prefer files that look like the annual coverage raster
    preferred = [
        p for p in candidates
        if "coverage" in p.name.lower() and "2024" in p.name.lower()
    ]

    if preferred:
        return preferred[0]

    return candidates[0]


def main():
    raw_raster = find_mapbiomas_raster()

    if not AOI_PATH.exists():
        raise FileNotFoundError(f"AOI file not found: {AOI_PATH}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Using raw raster: {raw_raster}")

    aoi = gpd.read_file(AOI_PATH, layer=AOI_LAYER)
    if aoi.empty:
        raise ValueError("AOI layer is empty.")

    with rasterio.open(raw_raster) as src:
        if src.crs is None:
            raise ValueError("Input raster has no CRS.")

        if aoi.crs != src.crs:
            aoi = aoi.to_crs(src.crs)

        geoms = [g for g in aoi.geometry if g is not None and not g.is_empty]
        if not geoms:
            raise ValueError("AOI geometry is empty after filtering.")

        clipped, transform = mask(
            src,
            geoms,
            crop=True,
            filled=True,
            nodata=src.nodata
        )

        meta = src.meta.copy()
        meta.update({
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": transform
        })

        with tempfile.NamedTemporaryFile(
            suffix=".tif",
            delete=False,
            dir=str(OUT_PATH.parent)
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with rasterio.open(tmp_path, "w", **meta) as dst:
                dst.write(clipped)
            shutil.move(str(tmp_path), str(OUT_PATH))
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    print(f"Saved AOI clip to: {OUT_PATH}")
    


if __name__ == "__main__":
    main()