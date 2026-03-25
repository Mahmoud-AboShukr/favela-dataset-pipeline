#!/usr/bin/env python3
"""
src/final_pipeline/4_refine_with_osm_industrial.py

Post-process final refined favela polygons by subtracting OSM industrial/factory
areas downloaded with OSMnx.

Intended use
------------
Run this AFTER:
- 1_prepare_inputs.py
- 2_build_refined_mask.py
- 3_polygonize_and_qc.py

Inputs
------
Prepared:
- data/processed/final_pipeline/manaus/prepared/aoi_manaus.gpkg

Polygonized:
- data/processed/final_pipeline/manaus/polygonized/refined_polygons_dissolved.gpkg

Outputs
-------
data/processed/final_pipeline/manaus/osm_refined/
- osm_industrial_raw.gpkg
- osm_industrial_union.gpkg
- refined_polygons_minus_osm_industrial.gpkg
- industrial_overlap_review.gpkg
- osm_refine_summary.json

Notes
-----
- This script is conservative: it removes only clearly industrial / factory-like
  OSM features by default.
- It is meant to remove industrial and factory areas mistakenly retained as
  residential/favela polygons.
- Because OSM quality varies spatially, the overlap layer is also exported for
  manual checking in QGIS.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import osmnx as ox
from shapely.ops import unary_union

# =============================================================================
# CONFIG
# =============================================================================

CITY = "manaus"

BASE_DIR = Path("data/processed/final_pipeline") / CITY
PREPARED_DIR = BASE_DIR / "prepared"
POLYGONIZED_DIR = BASE_DIR / "polygonized"
OUT_DIR = BASE_DIR / "osm_refined"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AOI_PATH = PREPARED_DIR / "aoi_manaus.gpkg"
REFINED_DISSOLVED_PATH = POLYGONIZED_DIR / "refined_polygons_dissolved.gpkg"

OSM_RAW_OUT = OUT_DIR / "osm_industrial_raw.gpkg"
OSM_UNION_OUT = OUT_DIR / "osm_industrial_union.gpkg"
REFINED_MINUS_OSM_OUT = OUT_DIR / "refined_polygons_minus_osm_industrial.gpkg"
OVERLAP_REVIEW_OUT = OUT_DIR / "industrial_overlap_review.gpkg"
SUMMARY_JSON_OUT = OUT_DIR / "osm_refine_summary.json"

# Output CRS for area calculations
AREA_CRS = "EPSG:5880"

# Conservative industrial/factory tags
# OSMnx features_from_polygon accepts a dict of tags. If a tag value is a list,
# it returns features matching any of those values for that key.
OSM_TAGS = {
    "landuse": [
        "industrial",
        "factory",
        "port",
        "logistics",
        "depot",
    ],
    "building": [
        "industrial",
        "warehouse",
        "factory",
        "manufacture",
        "depot",
    ],
    "industrial": True,
    "man_made": [
        "works",
        "storage_tank",
    ],
}

# Optional filtering logic
MIN_OSM_FEATURE_AREA_M2 = 100.0
MIN_OVERLAP_AREA_M2 = 50.0

# Keep the original favela_id if present
SOURCE_ID_FIELD = "favela_id"


# =============================================================================
# HELPERS
# =============================================================================

def ensure_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if len(gdf) == 0:
        return gdf.copy()
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(0)
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
    return gdf


def to_area_crs(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("Input GeoDataFrame has no CRS.")
    return gdf.to_crs(AREA_CRS)


def add_area_m2(gdf: gpd.GeoDataFrame, field: str = "area_m2") -> gpd.GeoDataFrame:
    if len(gdf) == 0:
        gdf = gdf.copy()
        gdf[field] = []
        return gdf
    gdf = gdf.copy()
    gdf[field] = to_area_crs(gdf).geometry.area
    return gdf


def safe_union(gdf: gpd.GeoDataFrame):
    if len(gdf) == 0:
        return None
    return unary_union(list(gdf.geometry))


def difference_with_union(gdf: gpd.GeoDataFrame, union_geom) -> gpd.GeoDataFrame:
    if union_geom is None or union_geom.is_empty:
        return gdf.copy()
    out = gdf.copy()
    out["geometry"] = out.geometry.apply(lambda geom: geom.difference(union_geom))
    out = ensure_valid(out)
    return out


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("LOADING INPUTS")
    print("=" * 80)

    aoi = gpd.read_file(AOI_PATH)
    refined = gpd.read_file(REFINED_DISSOLVED_PATH)

    aoi = ensure_valid(aoi)
    refined = ensure_valid(refined)

    if len(aoi) == 0:
        raise ValueError("AOI layer is empty.")
    if len(refined) == 0:
        raise ValueError("Refined dissolved polygon layer is empty.")

    if refined.crs != aoi.crs:
        refined = refined.to_crs(aoi.crs)

    aoi_union = unary_union(list(aoi.geometry))

    print(f"AOI polygons: {len(aoi)}")
    print(f"Refined dissolved polygons: {len(refined)}")

    # -------------------------------------------------------------------------
    # 1) Download OSM industrial/factory features
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("DOWNLOADING OSM INDUSTRIAL FEATURES WITH OSMNX")
    print("=" * 80)

    # OSMnx features_from_polygon downloads OSM geospatial features from the AOI polygon.
    osm_features = ox.features_from_polygon(aoi_union, tags=OSM_TAGS)

    if osm_features is None or len(osm_features) == 0:
        print("No OSM industrial features found in AOI.")

        empty = gpd.GeoDataFrame(geometry=[], crs=aoi.crs)
        empty.to_file(OSM_RAW_OUT, driver="GPKG")
        empty.to_file(OSM_UNION_OUT, driver="GPKG")
        refined.to_file(REFINED_MINUS_OSM_OUT, driver="GPKG")
        empty.to_file(OVERLAP_REVIEW_OUT, driver="GPKG")

        summary = {
            "city": CITY,
            "osm_features_found": 0,
            "refined_input_polygons": int(len(refined)),
            "refined_output_polygons": int(len(refined)),
            "removed_overlap_area_m2": 0.0,
        }
        with open(SUMMARY_JSON_OUT, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print("Done.")
        return

    osm_features = gpd.GeoDataFrame(osm_features, geometry="geometry", crs=osm_features.crs)
    osm_features = ensure_valid(osm_features)

    # Keep only polygonal geometries
    osm_features = osm_features[
        osm_features.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
    ].copy()

    # Reproject to AOI CRS if needed
    if osm_features.crs != aoi.crs:
        osm_features = osm_features.to_crs(aoi.crs)

    # Add area and remove very tiny features
    osm_features = add_area_m2(osm_features, "osm_area_m2")
    osm_features = osm_features[osm_features["osm_area_m2"] >= MIN_OSM_FEATURE_AREA_M2].copy()
    osm_features = osm_features.reset_index(drop=True)

    print(f"OSM industrial-like polygon features kept: {len(osm_features)}")

    # Save raw OSM features
    osm_features.to_file(OSM_RAW_OUT, driver="GPKG")

    # -------------------------------------------------------------------------
    # 2) Union OSM industrial features
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("BUILDING UNION OF OSM INDUSTRIAL FEATURES")
    print("=" * 80)

    osm_union_geom = safe_union(osm_features)

    if osm_union_geom is None or osm_union_geom.is_empty:
        print("OSM union is empty after filtering.")
        refined.to_file(REFINED_MINUS_OSM_OUT, driver="GPKG")

        empty = gpd.GeoDataFrame(geometry=[], crs=aoi.crs)
        empty.to_file(OSM_UNION_OUT, driver="GPKG")
        empty.to_file(OVERLAP_REVIEW_OUT, driver="GPKG")

        summary = {
            "city": CITY,
            "osm_features_found": int(len(osm_features)),
            "refined_input_polygons": int(len(refined)),
            "refined_output_polygons": int(len(refined)),
            "removed_overlap_area_m2": 0.0,
        }
        with open(SUMMARY_JSON_OUT, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print("Done.")
        return

    osm_union_gdf = gpd.GeoDataFrame(
        {"feature_type": ["osm_industrial_union"]},
        geometry=[osm_union_geom],
        crs=aoi.crs,
    )
    osm_union_gdf = add_area_m2(osm_union_gdf, "area_m2")
    osm_union_gdf.to_file(OSM_UNION_OUT, driver="GPKG")

    # -------------------------------------------------------------------------
    # 3) Compute overlap review layer
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("COMPUTING INDUSTRIAL OVERLAP REVIEW LAYER")
    print("=" * 80)

    overlap = gpd.overlay(
        refined[[c for c in refined.columns if c != "geometry"] + ["geometry"]],
        osm_features[[c for c in osm_features.columns if c != "geometry"] + ["geometry"]],
        how="intersection",
    )

    overlap = ensure_valid(overlap)
    overlap = add_area_m2(overlap, "overlap_area_m2")
    overlap = overlap[overlap["overlap_area_m2"] >= MIN_OVERLAP_AREA_M2].copy()
    overlap = overlap.reset_index(drop=True)

    print(f"Refined/industrial overlap polygons: {len(overlap)}")
    overlap.to_file(OVERLAP_REVIEW_OUT, driver="GPKG")

    # -------------------------------------------------------------------------
    # 4) Subtract OSM industrial union from refined polygons
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SUBTRACTING OSM INDUSTRIAL AREAS FROM REFINED POLYGONS")
    print("=" * 80)

    refined_before = add_area_m2(refined, "area_before_m2")

    refined_minus = difference_with_union(refined, osm_union_geom)
    refined_minus = refined_minus.explode(index_parts=False).reset_index(drop=True)
    refined_minus = ensure_valid(refined_minus)
    refined_minus = add_area_m2(refined_minus, "area_after_m2")

    # remove empty / tiny leftovers
    refined_minus = refined_minus[refined_minus["area_after_m2"] > 0].copy()
    refined_minus = refined_minus.reset_index(drop=True)

    # If original favela_id existed, preserve it. If not, create one.
    if SOURCE_ID_FIELD not in refined_minus.columns:
        refined_minus[SOURCE_ID_FIELD] = range(1, len(refined_minus) + 1)

    # area removed per polygon (best effort merge by source id if present)
    if SOURCE_ID_FIELD in refined_before.columns and SOURCE_ID_FIELD in refined_minus.columns:
        before_tbl = refined_before[[SOURCE_ID_FIELD, "area_before_m2"]].copy()
        after_tbl = (
            refined_minus.groupby(SOURCE_ID_FIELD, as_index=False)["area_after_m2"]
            .sum()
        )
        refined_minus = refined_minus.merge(before_tbl, on=SOURCE_ID_FIELD, how="left")
        refined_minus = refined_minus.merge(after_tbl, on=SOURCE_ID_FIELD, how="left", suffixes=("", "_sum"))
        refined_minus["removed_area_m2"] = (
            refined_minus["area_before_m2"] - refined_minus["area_after_m2_sum"]
        ).clip(lower=0)
        refined_minus["removed_ratio"] = (
            refined_minus["removed_area_m2"] / refined_minus["area_before_m2"]
        ).fillna(0)
        refined_minus = refined_minus.drop(columns=["area_after_m2_sum"], errors="ignore")
    else:
        refined_minus["removed_area_m2"] = None
        refined_minus["removed_ratio"] = None

    print(f"Refined polygons after OSM subtraction: {len(refined_minus)}")
    refined_minus.to_file(REFINED_MINUS_OSM_OUT, driver="GPKG")

    # -------------------------------------------------------------------------
    # 5) Summary
    # -------------------------------------------------------------------------
    removed_overlap_area_m2 = float(overlap["overlap_area_m2"].sum()) if len(overlap) else 0.0
    total_before_m2 = float(refined_before["area_before_m2"].sum()) if len(refined_before) else 0.0
    total_after_m2 = float(refined_minus["area_after_m2"].sum()) if len(refined_minus) else 0.0

    summary = {
        "city": CITY,
        "osm_features_found": int(len(osm_features)),
        "osm_union_area_m2": float(osm_union_gdf["area_m2"].sum()) if len(osm_union_gdf) else 0.0,
        "refined_input_polygons": int(len(refined)),
        "refined_output_polygons": int(len(refined_minus)),
        "industrial_overlap_polygons": int(len(overlap)),
        "removed_overlap_area_m2": removed_overlap_area_m2,
        "total_refined_area_before_m2": total_before_m2,
        "total_refined_area_after_m2": total_after_m2,
        "total_removed_area_m2": max(total_before_m2 - total_after_m2, 0.0),
        "paths": {
            "osm_raw": str(OSM_RAW_OUT),
            "osm_union": str(OSM_UNION_OUT),
            "refined_minus_osm": str(REFINED_MINUS_OSM_OUT),
            "overlap_review": str(OVERLAP_REVIEW_OUT),
        },
    }

    with open(SUMMARY_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nDone.")
    print(f"Outputs written to: {OUT_DIR}")


if __name__ == "__main__":
    main()