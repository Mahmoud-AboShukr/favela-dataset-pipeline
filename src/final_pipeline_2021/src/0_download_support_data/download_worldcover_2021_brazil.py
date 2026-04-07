from pathlib import Path
import math
import requests
import geopandas as gpd
from shapely.geometry import box

# ---------------------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------------------

# Put here a Brazil boundary file you already have.
# Best option: a Brazil country polygon in EPSG:4326 or anything reprojectable.

BRAZIL_BOUNDARY = Path("data/raw/ibge/BR_Municipios_2024/BR_Municipios_2024.shp")

# Output folder for Brazil-only WorldCover tiles
OUT_DIR = Path("data/raw/worldcover_2021/brazil_tiles")

# ESA WorldCover 2021 v200 S3 public URL prefix
BASE_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map"

# If True, only print the tiles and URLs without downloading
DRY_RUN = False

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def floor_to_3(x: float) -> int:
    return math.floor(x / 3) * 3

def ceil_to_3(x: float) -> int:
    return math.ceil(x / 3) * 3

def format_lat(lat: int) -> str:
    hemi = "N" if lat >= 0 else "S"
    return f"{hemi}{abs(lat):02d}"

def format_lon(lon: int) -> str:
    hemi = "E" if lon >= 0 else "W"
    return f"{hemi}{abs(lon):03d}"

def tile_name(lat0: int, lon0: int) -> str:
    # WorldCover naming uses the lower-left corner of the 3x3 tile
    return f"{format_lat(lat0)}{format_lon(lon0)}"

def tile_filename(tile: str) -> str:
    return f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"

def tile_url(tile: str) -> str:
    return f"{BASE_URL}/{tile_filename(tile)}"

def iter_worldcover_tiles(bounds):
    minx, miny, maxx, maxy = bounds

    lon_start = floor_to_3(minx)
    lon_end = ceil_to_3(maxx)
    lat_start = floor_to_3(miny)
    lat_end = ceil_to_3(maxy)

    for lat0 in range(lat_start, lat_end, 3):
        for lon0 in range(lon_start, lon_end, 3):
            yield lat0, lon0, box(lon0, lat0, lon0 + 3, lat0 + 3)

def download_file(url: str, out_path: Path, chunk_size: int = 1024 * 1024):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = 0
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)
    return total

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    if not BRAZIL_BOUNDARY.exists():
        raise FileNotFoundError(
            f"Boundary file not found: {BRAZIL_BOUNDARY}\n"
            "Create or point this to a Brazil country boundary first."
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Reading Brazil boundary: {BRAZIL_BOUNDARY}")
    gdf = gpd.read_file(BRAZIL_BOUNDARY)

    if gdf.empty:
        raise ValueError("Boundary file is empty.")

    if gdf.crs is None:
        raise ValueError("Boundary file has no CRS. Please assign one first.")

    gdf = gdf.to_crs("EPSG:4326")
    geom = gdf.unary_union
    bounds = geom.bounds

    print(f"[INFO] Brazil bounds (EPSG:4326): {bounds}")

    selected_tiles = []

    for lat0, lon0, tile_geom in iter_worldcover_tiles(bounds):
        if tile_geom.intersects(geom):
            tname = tile_name(lat0, lon0)
            selected_tiles.append((tname, lat0, lon0))

    selected_tiles = sorted(selected_tiles, key=lambda x: (x[1], x[2]))

    print(f"[INFO] Intersecting WorldCover tiles: {len(selected_tiles)}")

    tile_list_path = OUT_DIR / "brazil_worldcover_2021_tiles.txt"
    with open(tile_list_path, "w", encoding="utf-8") as f:
        for tname, _, _ in selected_tiles:
            f.write(f"{tname}\n")

    print(f"[INFO] Tile list written to: {tile_list_path}")

    for tname, _, _ in selected_tiles:
        fname = tile_filename(tname)
        url = tile_url(tname)
        out_path = OUT_DIR / fname

        if out_path.exists():
            print(f"[SKIP] {fname} already exists")
            continue

        if DRY_RUN:
            print(f"[DRY ] {url}")
            continue

        try:
            print(f"[DOWN ] {fname}")
            size = download_file(url, out_path)
            print(f"[ OK  ] {fname} ({size / (1024**2):.1f} MB)")
        except Exception as e:
            print(f"[FAIL ] {fname} -> {e}")

    print("[DONE]")

if __name__ == "__main__":
    main()