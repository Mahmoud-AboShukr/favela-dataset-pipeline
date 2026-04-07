from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pystac_client import Client
from shapely.geometry import shape


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

STAC_URL = "https://stac.dataspace.copernicus.eu/v1/"
COLLECTION = "sentinel-2-l2a"

# Try the AOI paths that actually exist in your repo tree.
AOI_CANDIDATE_PATHS = [
    Path("data/old_experiments_data/interim/aoi/manaus/manaus_aoi.gpkg"),
    Path("data/old_experiments_data/processed/final_pipeline/manaus/prepared/aoi_manaus.gpkg"),
]

AOI_LAYER = None  # keep None unless you know a specific layer name is required

DATE_START = "2022-01-01"
DATE_END = "2022-12-31"
MAX_CLOUD = 40.0

OUT_DIR = Path("data/interim/imagery/sentinel2/manaus")
OUT_CSV = OUT_DIR / "s2_2022_search_results.csv"
OUT_GEOJSON = OUT_DIR / "s2_2022_search_results.geojson"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def pick_existing_aoi_path(candidates: list[Path]) -> Path:
    """
    Return the first AOI path that exists.
    """
    for path in candidates:
        if path.exists():
            return path
    checked = "\n".join(f"  - {p}" for p in candidates)
    raise FileNotFoundError(
        "No AOI file was found. Checked these paths:\n"
        f"{checked}"
    )


def load_aoi_geometry(aoi_path: Path, layer: str | None = None) -> dict[str, Any]:
    """
    Load the AOI geometry from a vector file and return a single GeoJSON geometry
    in EPSG:4326 for STAC intersects search.
    """
    gdf = gpd.read_file(aoi_path, layer=layer)

    if gdf.empty:
        raise ValueError(f"AOI file is empty: {aoi_path}")

    if gdf.crs is None:
        raise ValueError(f"AOI file has no CRS: {aoi_path}")

    gdf = gdf.to_crs("EPSG:4326")

    # Dissolve to one geometry for a simple STAC query
    try:
        geom = gdf.union_all()
    except Exception:
        geom = gdf.unary_union

    return json.loads(gpd.GeoSeries([geom], crs="EPSG:4326").to_json())["features"][0]["geometry"]


def extract_item_record(item) -> dict[str, Any]:
    """
    Extract the main fields we want from one STAC item.
    """
    props = item.properties or {}

    instruments = props.get("instruments")
    if isinstance(instruments, list):
        instruments = ",".join(instruments)

    return {
        "id": item.id,
        "collection": item.collection_id,
        "datetime": props.get("datetime"),
        "start_datetime": props.get("start_datetime"),
        "end_datetime": props.get("end_datetime"),
        "platform": props.get("platform"),
        "instruments": instruments,
        "eo_cloud_cover": props.get("eo:cloud_cover"),
        "s2_product_type": props.get("s2:product_type"),
        "sat_orbit_state": props.get("sat:orbit_state"),
        "proj_epsg": props.get("proj:epsg"),
        "geometry": item.geometry,
    }


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    print("=" * 80)
    print("SENTINEL-2 SEARCH FOR MANAUS (2022)")
    print("=" * 80)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    aoi_path = pick_existing_aoi_path(AOI_CANDIDATE_PATHS)
    print(f"\nUsing AOI file: {aoi_path}")

    geometry = load_aoi_geometry(aoi_path, AOI_LAYER)

    print(f"Opening STAC catalog: {STAC_URL}")
    catalog = Client.open(STAC_URL)

    print("\nSearching STAC items...")
    search = catalog.search(
        collections=[COLLECTION],
        intersects=geometry,
        datetime=f"{DATE_START}/{DATE_END}",
        query={
            "eo:cloud_cover": {"lte": MAX_CLOUD}
        },
    )

    items = list(search.items())
    print(f"Found {len(items)} matching Sentinel-2 L2A items.")

    if not items:
        print("No items found. Check AOI, dates, collection name, or cloud threshold.")
        return

    records = [extract_item_record(item) for item in items]
    df = pd.DataFrame(records)

    # Sort by date then cloud cover
    sort_cols = [c for c in ["datetime", "eo_cloud_cover"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=True, na_position="last")

    # Save CSV without geometry column
    csv_df = df.drop(columns=["geometry"], errors="ignore")
    csv_df.to_csv(OUT_CSV, index=False)

    # Save GeoJSON with scene footprints
    footprint_geoms = [shape(rec["geometry"]) for rec in records if rec.get("geometry") is not None]
    geo_df = gpd.GeoDataFrame(
        df.drop(columns=["geometry"], errors="ignore").copy(),
        geometry=footprint_geoms,
        crs="EPSG:4326",
    )
    geo_df.to_file(OUT_GEOJSON, driver="GeoJSON")

    print("\nSaved:")
    print(f"  CSV:     {OUT_CSV}")
    print(f"  GeoJSON: {OUT_GEOJSON}")

    print("\nSample rows:")
    preview_cols = [
        c for c in
        ["id", "datetime", "eo_cloud_cover", "platform", "s2_product_type", "proj_epsg"]
        if c in csv_df.columns
    ]
    print(csv_df[preview_cols].head(10).to_string(index=False))

    print("\nDone.")


if __name__ == "__main__":
    main()