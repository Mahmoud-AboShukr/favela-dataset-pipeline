from pathlib import Path
import tempfile
import shutil

import geopandas as gpd
import rasterio
from rasterio.mask import mask


RAW_ROOT = Path("data/raw/mapbiomas")
AOI_ROOT = Path("data/interim/aoi")
OUT_ROOT = Path("data/interim/mapbiomas_10m_clips")

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
    "belo_horizonte",
    "salvador",
    "manaus",
]


def find_mapbiomas_raster() -> Path:
    candidates = sorted(RAW_ROOT.rglob("*.tif"))

    if not candidates:
        raise FileNotFoundError(f"No .tif files found under: {RAW_ROOT.resolve()}")

    preferred = [p for p in candidates if "10m" in p.name.lower()]

    if preferred:
        return preferred[0]

    raise FileNotFoundError(
        f"Could not find a 10 m MapBiomas raster under: {RAW_ROOT.resolve()}"
    )


def clip_one_city(raw_raster: Path, city: str) -> None:
    aoi_path = AOI_ROOT / city / f"{city}_aoi.gpkg"
    out_dir = OUT_ROOT / city
    out_path = out_dir / f"mapbiomas_10m_{city}_aoi_clip.tif"

    if not aoi_path.exists():
        raise FileNotFoundError(f"AOI file not found for {city}: {aoi_path.resolve()}")

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {city} ===")
    print(f"AOI: {aoi_path}")
    print(f"Output: {out_path}")

    aoi = gpd.read_file(aoi_path)
    if aoi.empty:
        raise ValueError(f"AOI is empty for city: {city}")

    with rasterio.open(raw_raster) as src:
        if src.crs is None:
            raise ValueError("Input raster has no CRS.")

        if aoi.crs != src.crs:
            aoi = aoi.to_crs(src.crs)

        geoms = [g for g in aoi.geometry if g is not None and not g.is_empty]
        if not geoms:
            raise ValueError(f"AOI geometry is empty after filtering for city: {city}")

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
            dir=str(out_dir)
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with rasterio.open(tmp_path, "w", **meta) as dst:
                dst.write(clipped)
            shutil.move(str(tmp_path), str(out_path))
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    print(f"Saved AOI clip to: {out_path}")


def main():
    if not RAW_ROOT.exists():
        raise FileNotFoundError(f"Raw mapbiomas folder not found: {RAW_ROOT.resolve()}")

    raw_raster = find_mapbiomas_raster()
    print(f"Using raw raster: {raw_raster}")

    for city in CITIES:
        clip_one_city(raw_raster, city)

    print("\nDone.")


if __name__ == "__main__":
    main()