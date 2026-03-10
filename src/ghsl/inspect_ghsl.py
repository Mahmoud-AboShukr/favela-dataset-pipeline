from __future__ import annotations

from pathlib import Path
import numpy as np
import rasterio


# You can inspect either raw tiles or clipped rasters.
# Change this to "data/interim/ghsl_clips" when you want to inspect the AOI clip.
GHSL_DIR = Path("data/raw/ghsl")

# To inspect the AOI clipped file, set:
# GHSL_DIR = Path("data/interim/ghsl_clips")
# TIF = "ghsl_brasilia_aoi_clip.tif"

# Options:
# - None: auto-pick first tif in GHSL_DIR
# - "brasilia": search by substring in filename
# - "myfile.tif": exact filename inside GHSL_DIR
# - r"C:\...\file.tif": absolute path
TIF = "brasilia"

# Sampling settings for huge rasters (avoid reading the whole file)
SAMPLE_STEP = 8000   # every N pixels in x/y we take a sample window
SAMPLE_WIN = 512     # window size (pixels) to read at each sample location
MAX_SAMPLES = 200    # safety cap: stop after this many windows


def resolve_tif(tif_setting: str | None) -> Path:
    """
    Resolve a user-friendly TIF selector into an actual path.
    """
    if tif_setting is None:
        tifs = sorted(GHSL_DIR.glob("*.tif"))
        if not tifs:
            raise FileNotFoundError(f"No .tif found in {GHSL_DIR.resolve()}")
        return tifs[0].resolve()

    p = Path(tif_setting)

    # Absolute or relative path directly provided
    if p.suffix.lower() == ".tif" and p.exists():
        return p.resolve()

    # Filename provided (without path) like "file.tif"
    if p.suffix.lower() == ".tif":
        candidate = GHSL_DIR / p.name
        if candidate.exists():
            return candidate.resolve()
        raise FileNotFoundError(f"Could not find {candidate.resolve()}")

    # Substring search like "brasilia"
    matches = sorted([x for x in GHSL_DIR.glob("*.tif") if tif_setting.lower() in x.name.lower()])
    if not matches:
        available = [x.name for x in GHSL_DIR.glob("*.tif")]
        raise FileNotFoundError(
            f'No GHSL .tif matching "{tif_setting}" in {GHSL_DIR.resolve()}.\n'
            f"Available .tif files: {available}"
        )
    if len(matches) > 1:
        print(f'⚠ Multiple matches for "{tif_setting}". Using first:')
        for m in matches:
            print("   -", m.name)
    return matches[0].resolve()


def approx_minmax(src: rasterio.io.DatasetReader, band: int = 1) -> tuple[int | None, int | None]:
    """
    Approximate min/max by sampling small windows across the raster.
    This avoids reading the full raster (which can be huge).
    """
    nodata = src.nodata
    mins: list[int] = []
    maxs: list[int] = []

    samples = 0

    # sample a grid of windows across the raster
    for row in range(0, src.height, SAMPLE_STEP):
        for col in range(0, src.width, SAMPLE_STEP):
            if samples >= MAX_SAMPLES:
                break

            h = min(SAMPLE_WIN, src.height - row)
            w = min(SAMPLE_WIN, src.width - col)

            data = src.read(band, window=((row, row + h), (col, col + w)))

            # remove nodata if it exists
            if nodata is not None:
                data = data[data != nodata]

            if data.size == 0:
                continue

            mins.append(int(data.min()))
            maxs.append(int(data.max()))
            samples += 1

        if samples >= MAX_SAMPLES:
            break

    if not mins:
        return None, None

    return int(np.min(mins)), int(np.max(maxs))


def main():
    tif_path = resolve_tif(TIF)

    with rasterio.open(tif_path) as src:
        print("File:", tif_path)
        print("CRS:", src.crs)
        print("Resolution (pixel size):", src.res)
        print("Width x Height:", src.width, "x", src.height)
        print("Nodata:", src.nodata)
        print("Bounds:", src.bounds)
        print("Dtype:", src.dtypes)
        print("Count (bands):", src.count)

        # Value range without freezing:
        mn, mx = approx_minmax(src, band=1)
        print(f"Approx value min/max (band 1): {mn} / {mx}")
        print(f"(Computed from up to {MAX_SAMPLES} sampled windows of {SAMPLE_WIN}x{SAMPLE_WIN} pixels)")

        # If the raster is small enough, you *can* compute exact min/max safely:
        # Example threshold: <= 50 million pixels (~50MB for uint8)
        total_pixels = src.width * src.height
        if total_pixels <= 120_000_000:
            band1 = src.read(1, masked=True)
            print("Exact value min/max (band 1):", float(band1.min()), "/", float(band1.max()))
        else:
            print("Exact min/max skipped (raster is huge). Use the approximate values above.")


if __name__ == "__main__":
    main()