from __future__ import annotations

import time
from typing import List, Tuple

import ee


PROJECT = "ninth-matter-490811-f1"

# Expanded favela-extent bounds you already computed
MIN_LON = -73.7
MIN_LAT = -33.1
MAX_LON = -33.8
MAX_LAT = 3.9

FOLDER = "dynamic_world_2021_fast"
YEAR_START = "2021-01-01"
YEAR_END = "2022-01-01"
SCALE = 10
MAX_PIXELS = 1e13


def make_quadrants(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> List[Tuple[str, ee.Geometry]]:
    mid_lon = (min_lon + max_lon) / 2.0
    mid_lat = (min_lat + max_lat) / 2.0

    return [
        ("q0", ee.Geometry.Rectangle([min_lon, min_lat, mid_lon, mid_lat], None, False)),
        ("q1", ee.Geometry.Rectangle([mid_lon, min_lat, max_lon, mid_lat], None, False)),
        ("q2", ee.Geometry.Rectangle([min_lon, mid_lat, mid_lon, max_lat], None, False)),
        ("q3", ee.Geometry.Rectangle([mid_lon, mid_lat, max_lon, max_lat], None, False)),
    ]


def build_dw_collection(region: ee.Geometry) -> ee.ImageCollection:
    return (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterDate(YEAR_START, YEAR_END)
        .filterBounds(region)
    )


def make_exports(tile_id: str, region: ee.Geometry) -> Tuple[ee.batch.Task, ee.batch.Task]:
    dw = build_dw_collection(region)

    built_mean = (
        dw.select("built")
        .mean()
        .clip(region)
        .rename("built_mean")
    )

    built_p90 = (
        dw.select("built")
        .reduce(ee.Reducer.percentile([90]))
        .clip(region)
        .rename("built_p90")
    )

    mean_task = ee.batch.Export.image.toDrive(
        image=built_mean,
        description=f"dw_built_mean_2021_{tile_id}",
        folder=FOLDER,
        fileNamePrefix=f"dw_built_mean_2021_{tile_id}",
        region=region.coordinates().getInfo(),
        scale=SCALE,
        maxPixels=MAX_PIXELS,
        fileFormat="GeoTIFF",
    )

    p90_task = ee.batch.Export.image.toDrive(
        image=built_p90,
        description=f"dw_built_p90_2021_{tile_id}",
        folder=FOLDER,
        fileNamePrefix=f"dw_built_p90_2021_{tile_id}",
        region=region.coordinates().getInfo(),
        scale=SCALE,
        maxPixels=MAX_PIXELS,
        fileFormat="GeoTIFF",
    )

    return mean_task, p90_task


def main() -> None:
    ee.Initialize(project=PROJECT)

    full_region = ee.Geometry.Rectangle([MIN_LON, MIN_LAT, MAX_LON, MAX_LAT], None, False)
    quadrants = make_quadrants(MIN_LON, MIN_LAT, MAX_LON, MAX_LAT)

    print(f"[INFO] Project: {PROJECT}")
    print(f"[INFO] Folder: {FOLDER}")
    print(f"[INFO] Full region: {full_region.getInfo()['coordinates']}")
    print(f"[INFO] Number of quadrants: {len(quadrants)}")

    tasks: List[ee.batch.Task] = []

    for tile_id, region in quadrants:
        mean_task, p90_task = make_exports(tile_id, region)
        mean_task.start()
        p90_task.start()

        tasks.extend([mean_task, p90_task])

        print(f"[START] dw_built_mean_2021_{tile_id}")
        print(f"[START] dw_built_p90_2021_{tile_id}")

        # Small pause so requests are not all fired at once
        time.sleep(2)

    print("\n[INFO] Started tasks:")
    for task in tasks:
        print(f"  - {task.id}")

    print("\n[INFO] Monitor task status with the Earth Engine CLI or in Google Drive.")
    print(f"[INFO] Output Drive folder: {FOLDER}")


if __name__ == "__main__":
    main()