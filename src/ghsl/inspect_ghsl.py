from pathlib import Path
import rasterio

GHSL_DIR = Path("data/raw/ghsl")  # folder containing GHSL .tif files

# Options:
# - None: auto-pick first tif in GHSL_DIR
# - "brasilia": search by substring in filename
# - "myfile.tif": exact filename inside GHSL_DIR
# - r"C:\...\file.tif": absolute path
TIF = "brasilia"


def resolve_tif(tif_setting: str | None) -> Path:
    if tif_setting is None:
        tifs = sorted(GHSL_DIR.glob("*.tif"))
        if not tifs:
            raise FileNotFoundError(f"No .tif found in {GHSL_DIR.resolve()}")
        return tifs[0]

    p = Path(tif_setting)

    # Absolute or relative path provided directly
    if p.suffix.lower() == ".tif" and p.exists():
        return p.resolve()

    # Filename provided (without path) like "file.tif"
    if p.suffix.lower() == ".tif":
        candidate = (GHSL_DIR / p.name)
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

        # Optional: inspect value range (small sample)
        band1 = src.read(1, masked=True)
        # masked arrays handle nodata safely
        print("Value min/max (band 1):", float(band1.min()), "/", float(band1.max()))


if __name__ == "__main__":
    main()