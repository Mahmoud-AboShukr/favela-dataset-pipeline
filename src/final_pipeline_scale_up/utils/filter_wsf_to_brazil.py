#!/usr/bin/env python3
"""
Filter WSF2019 tiles to Brazil.

Default behavior:
- keep tiles intersecting Brazil in data/raw/wsf/
- move tiles NOT intersecting Brazil to data/raw/wsf_not_brazil/

Safer than direct deletion. After verification, you can delete the quarantine folder.

Assumptions:
- WSF filenames look like: WSF2019_v1_-62_-4.tif
- each tile is 2 x 2 degrees
- lon/lat in filename correspond to lower-left tile corner
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------
WSF_DIR = Path("data/raw/wsf")
QUARANTINE_DIR = Path("data/raw/wsf_not_brazil")
MUNICIPALITIES_PATH = Path("data/raw/ibge/BR_Municipios_2024/BR_Municipios_2024.shp")

# ---------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------
DELETE_INSTEAD_OF_MOVE = False   # set True only if you really want permanent deletion
TILE_SIZE_DEG = 2

# Example: WSF2019_v1_-62_-4.tif
FILENAME_RE = re.compile(r"^WSF2019_v1_(-?\d+)_(-?\d+)\.tif$", re.IGNORECASE)


def parse_wsf_filename(filename: str):
    m = FILENAME_RE.match(filename)
    if not m:
        return None
    lon = int(m.group(1))
    lat = int(m.group(2))
    return lon, lat


def build_brazil_polygon(municipalities_path: Path):
    munis = gpd.read_file(municipalities_path)
    brazil = munis.dissolve().reset_index(drop=True)
    if brazil.crs is None:
        raise ValueError("Municipalities layer has no CRS.")
    return brazil.to_crs("EPSG:4326")


def tile_geom_from_filename(filename: str):
    parsed = parse_wsf_filename(filename)
    if parsed is None:
        return None
    lon, lat = parsed
    return box(lon, lat, lon + TILE_SIZE_DEG, lat + TILE_SIZE_DEG)


def main():
    if not WSF_DIR.exists():
        raise FileNotFoundError(f"WSF directory not found: {WSF_DIR}")
    if not MUNICIPALITIES_PATH.exists():
        raise FileNotFoundError(f"Municipalities shapefile not found: {MUNICIPALITIES_PATH}")

    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading Brazil polygon from municipalities...")
    brazil = build_brazil_polygon(MUNICIPALITIES_PATH)
    brazil_union = brazil.geometry.union_all()

    tif_paths = sorted(WSF_DIR.glob("WSF2019_v1_*.tif"))
    if not tif_paths:
        raise ValueError(f"No WSF tiles found in {WSF_DIR}")

    kept = []
    moved = []
    skipped = []

    for tif_path in tif_paths:
        geom = tile_geom_from_filename(tif_path.name)
        if geom is None:
            skipped.append(tif_path.name)
            continue

        intersects_brazil = geom.intersects(brazil_union)

        if intersects_brazil:
            kept.append(tif_path.name)
            print(f"KEEP  | {tif_path.name}")
        else:
            if DELETE_INSTEAD_OF_MOVE:
                tif_path.unlink()
                print(f"DELETE| {tif_path.name}")
            else:
                dst = QUARANTINE_DIR / tif_path.name
                shutil.move(str(tif_path), str(dst))
                print(f"MOVE  | {tif_path.name} -> {dst}")
            moved.append(tif_path.name)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tiles scanned: {len(tif_paths)}")
    print(f"Kept (intersect Brazil): {len(kept)}")
    print(f"{'Deleted' if DELETE_INSTEAD_OF_MOVE else 'Moved'} (not Brazil): {len(moved)}")
    print(f"Skipped (filename not parsed): {len(skipped)}")

    if skipped:
        print("\nSkipped files:")
        for name in skipped:
            print(f"  - {name}")


if __name__ == "__main__":
    main()