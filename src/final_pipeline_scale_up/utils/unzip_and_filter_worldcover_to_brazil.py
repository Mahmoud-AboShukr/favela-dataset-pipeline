from pathlib import Path
import zipfile
import shutil
import re

import geopandas as gpd
from shapely.geometry import box

WORLD_COVER_DIR = Path(r"data/raw/worldcover/brazil")
NOT_BRAZIL_DIR = Path(r"data/raw/worldcover_not_brazil")

MUNICIPALITIES_PATH = Path(
    r"data/raw/ibge/BR_Municipios_2024/BR_Municipios_2024.shp"
)

TILE_RE = re.compile(
    r"ESA_WorldCover_10m_2021_v200_([NS])(\d{2})([EW])(\d{3})_Map\.tif$",
    re.IGNORECASE,
)


def load_brazil_polygon() -> gpd.GeoDataFrame:
    print("Loading Brazil polygon from municipalities...")
    gdf = gpd.read_file(MUNICIPALITIES_PATH)

    if gdf.empty:
        raise RuntimeError("Municipalities layer is empty.")
    if gdf.crs is None:
        raise RuntimeError("Municipalities layer has no CRS.")

    gdf = gdf.to_crs("EPSG:4326")
    return gdf.dissolve()


def unzip_all_worldcover():
    zip_files = sorted(WORLD_COVER_DIR.glob("*.zip"))

    if not zip_files:
        print("No zip files found.")
        return

    print(f"Found {len(zip_files)} zip file(s) to extract.\n")

    for zip_path in zip_files:
        print(f"EXTRACT | {zip_path.name}")
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(WORLD_COVER_DIR)
        except Exception as e:
            print(f"FAILED  | {zip_path.name} -> {e}")


def parse_worldcover_tile_bounds(filename: str):
    m = TILE_RE.search(filename)
    if not m:
        return None

    lat_hem, lat_deg, lon_hem, lon_deg = m.groups()

    lat = int(lat_deg)
    lon = int(lon_deg)

    if lat_hem.upper() == "S":
        lat = -lat
    if lon_hem.upper() == "W":
        lon = -lon

    minx = lon
    miny = lat
    maxx = lon + 3
    maxy = lat + 3

    return box(minx, miny, maxx, maxy)


def move_file_flat(src: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.move(str(src), str(dst))
    return dst


def filter_to_brazil():
    NOT_BRAZIL_DIR.mkdir(parents=True, exist_ok=True)

    brazil = load_brazil_polygon()
    brazil_geom = brazil.geometry.iloc[0]

    map_files = sorted(WORLD_COVER_DIR.rglob("*_Map.tif"))
    input_quality_files = sorted(WORLD_COVER_DIR.rglob("*_InputQuality.tif"))

    if not map_files and not input_quality_files:
        print("No extracted WorldCover tif files found.")
        return

    keep_count = 0
    move_count = 0
    fail_count = 0
    kept_tile_keys = set()

    print("\nChecking MAP tiles against Brazil...\n")

    for tif_path in map_files:
        tile_geom = parse_worldcover_tile_bounds(tif_path.name)

        if tile_geom is None:
            print(f"FAILED | could not parse tile name: {tif_path}")
            fail_count += 1
            continue

        if tile_geom.intersects(brazil_geom):
            print(f"KEEP   | {tif_path}")
            keep_count += 1
            key = tif_path.name.replace("_Map.tif", "")
            kept_tile_keys.add(key)
        else:
            dst = move_file_flat(tif_path, NOT_BRAZIL_DIR)
            print(f"MOVE   | {tif_path} -> {dst}")
            move_count += 1

    print("\nChecking INPUTQUALITY files...\n")

    iq_keep = 0
    iq_move = 0
    iq_fail = 0

    for tif_path in input_quality_files:
        key = tif_path.name.replace("_InputQuality.tif", "")

        if key in kept_tile_keys:
            print(f"KEEP   | {tif_path}")
            iq_keep += 1
        else:
            dst = move_file_flat(tif_path, NOT_BRAZIL_DIR)
            print(f"MOVE   | {tif_path} -> {dst}")
            iq_move += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Map tiles kept (intersect Brazil): {keep_count}")
    print(f"Map tiles moved (not Brazil):      {move_count}")
    print(f"Map tiles failed:                  {fail_count}")
    print(f"InputQuality kept:                 {iq_keep}")
    print(f"InputQuality moved:                {iq_move}")
    print(f"InputQuality failed:               {iq_fail}")


def main():
    unzip_all_worldcover()
    print("\n" + "=" * 80 + "\n")
    filter_to_brazil()


if __name__ == "__main__":
    main()