#!/usr/bin/env python3
"""
src/final_pipeline/3_polygonize_and_qc.py

Polygonize the refined Manaus raster outputs and compute polygon-level QC metrics
for manual review prioritization.

Inputs
------
Prepared:
- data/processed/final_pipeline/manaus/prepared/aoi_manaus.gpkg
- data/processed/final_pipeline/manaus/prepared/favela_polygons_manaus.gpkg
- data/processed/final_pipeline/manaus/prepared/favela_mask.tif

Refined:
- data/processed/final_pipeline/manaus/refined/favela_refined_final.tif
- data/processed/final_pipeline/manaus/refined/review_zones.tif
- data/processed/final_pipeline/manaus/refined/core_built.tif
- data/processed/final_pipeline/manaus/refined/uncertain_candidates.tif
- data/processed/final_pipeline/manaus/refined/uncertain_accepted.tif
- data/processed/final_pipeline/manaus/refined/uncertain_rejected.tif
- data/processed/final_pipeline/manaus/refined/wsf_support.tif
- data/processed/final_pipeline/manaus/refined/ghsl_support.tif
- data/processed/final_pipeline/manaus/refined/worldcover_vegetation_support.tif
- data/processed/final_pipeline/manaus/refined/settlement_support_combined.tif

Outputs
-------
data/processed/final_pipeline/manaus/polygonized/
- refined_polygons_raw.gpkg
- refined_polygons_dissolved.gpkg
- review_zones_polygons.gpkg
- favela_qc.gpkg
- favela_qc_metrics.csv
- city_qc_summary.json

Notes
-----
- The "raw" polygonized output is pixel-connected regions.
- The "dissolved" output merges all refined pieces belonging to the same source favela polygon.
- QC is computed per original favela polygon, because that is the most useful unit for manual review.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.ops import unary_union


# =============================================================================
# CONFIG
# =============================================================================

CITY = "manaus"

BASE_DIR = Path("data/processed/final_pipeline") / CITY
PREPARED_DIR = BASE_DIR / "prepared"
REFINED_DIR = BASE_DIR / "refined"
OUT_DIR = BASE_DIR / "polygonized"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AOI_PATH = PREPARED_DIR / "aoi_manaus.gpkg"
FAVELA_POLYGONS_PATH = PREPARED_DIR / "favela_polygons_manaus.gpkg"

FINAL_MASK_PATH = REFINED_DIR / "favela_refined_final.tif"
REVIEW_ZONES_PATH = REFINED_DIR / "review_zones.tif"
CORE_BUILT_PATH = REFINED_DIR / "core_built.tif"
UNCERTAIN_CANDIDATES_PATH = REFINED_DIR / "uncertain_candidates.tif"
UNCERTAIN_ACCEPTED_PATH = REFINED_DIR / "uncertain_accepted.tif"
UNCERTAIN_REJECTED_PATH = REFINED_DIR / "uncertain_rejected.tif"
WSF_SUPPORT_PATH = REFINED_DIR / "wsf_support.tif"
GHSL_SUPPORT_PATH = REFINED_DIR / "ghsl_support.tif"
WORLDCOVER_VEG_PATH = REFINED_DIR / "worldcover_vegetation_support.tif"
SETTLEMENT_SUPPORT_PATH = REFINED_DIR / "settlement_support_combined.tif"

RAW_POLYGONS_OUT = OUT_DIR / "refined_polygons_raw.gpkg"
DISSOLVED_POLYGONS_OUT = OUT_DIR / "refined_polygons_dissolved.gpkg"
REVIEW_POLYGONS_OUT = OUT_DIR / "review_zones_polygons.gpkg"
QC_GPKG_OUT = OUT_DIR / "favela_qc.gpkg"
QC_CSV_OUT = OUT_DIR / "favela_qc_metrics.csv"
CITY_SUMMARY_JSON_OUT = OUT_DIR / "city_qc_summary.json"

# Small sliver cleanup after polygonization
MIN_RAW_POLYGON_AREA_M2 = 100.0

# Review scoring thresholds
SHRINK_RATIO_HIGH = 0.60
SHRINK_RATIO_MED = 0.80
REMOVED_RATIO_HIGH = 0.20
REMOVED_RATIO_MED = 0.10
REVIEW_ZONE_RATIO_HIGH = 0.05
REVIEW_ZONE_RATIO_MED = 0.01
FRAGMENT_COUNT_HIGH = 4
FRAGMENT_COUNT_MED = 2

# Output CRS for area computation
# Use local projected CRS if you want, but for Brazil-wide simplicity SIRGAS 2000 / Brazil Mercator is common.
# EPSG:5880 is a Brazil Mercator CRS often used for area-ish work.
AREA_CRS = "EPSG:5880"


# =============================================================================
# HELPERS
# =============================================================================

def read_raster(path: Path):
    with rasterio.open(path) as src:
        arr = src.read(1)
        transform = src.transform
        crs = src.crs
        profile = src.profile.copy()
    return arr, transform, crs, profile


def polygonize_binary_mask(mask: np.ndarray, transform, crs, value_field: str = "value") -> gpd.GeoDataFrame:
    """
    Polygonize binary raster where 1 is foreground.
    """
    geoms = []
    vals = []

    mask_bool = mask.astype(np.uint8)
    for geom, val in shapes(mask_bool, mask=mask_bool == 1, transform=transform):
        if int(val) == 1:
            geoms.append(shape(geom))
            vals.append(1)

    if not geoms:
        return gpd.GeoDataFrame({value_field: []}, geometry=[], crs=crs)

    gdf = gpd.GeoDataFrame({value_field: vals}, geometry=geoms, crs=crs)
    return gdf


def explode_multipart(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if len(gdf) == 0:
        return gdf.copy()
    return gdf.explode(index_parts=False).reset_index(drop=True)


def ensure_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if len(gdf) == 0:
        return gdf.copy()
    gdf = gdf.copy()
    gdf["geometry"] = gdf.geometry.buffer(0)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()].copy()
    return gdf


def area_series_m2(gdf: gpd.GeoDataFrame) -> pd.Series:
    if len(gdf) == 0:
        return pd.Series(dtype=float)
    return gdf.to_crs(AREA_CRS).geometry.area


def area_m2_of_geom(geom, src_crs) -> float:
    if geom is None or geom.is_empty:
        return 0.0
    tmp = gpd.GeoSeries([geom], crs=src_crs).to_crs(AREA_CRS)
    return float(tmp.area.iloc[0])


def safe_ratio(num: float, den: float) -> float:
    if den == 0:
        return 0.0
    return float(num / den)


def count_fragments(geom) -> int:
    if geom is None or geom.is_empty:
        return 0
    if geom.geom_type == "Polygon":
        return 1
    if geom.geom_type == "MultiPolygon":
        return len(geom.geoms)
    return 0


def classify_priority(score: int) -> str:
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def add_review_score(row: pd.Series) -> int:
    score = 0

    if row["final_to_original_area_ratio"] < SHRINK_RATIO_HIGH:
        score += 2
    elif row["final_to_original_area_ratio"] < SHRINK_RATIO_MED:
        score += 1

    if row["removed_area_ratio"] > REMOVED_RATIO_HIGH:
        score += 2
    elif row["removed_area_ratio"] > REMOVED_RATIO_MED:
        score += 1

    if row["review_zone_area_ratio"] > REVIEW_ZONE_RATIO_HIGH:
        score += 2
    elif row["review_zone_area_ratio"] > REVIEW_ZONE_RATIO_MED:
        score += 1

    if row["fragment_count"] >= FRAGMENT_COUNT_HIGH:
        score += 2
    elif row["fragment_count"] >= FRAGMENT_COUNT_MED:
        score += 1

    return score


# =============================================================================
# RASTER-BASED PER-POLYGON METRICS
# =============================================================================

def zonal_sum_binary(arr: np.ndarray, geom, transform, crs) -> int:
    """
    Sum binary raster values inside a geometry.
    """
    if geom is None or geom.is_empty:
        return 0

    with rasterio.io.MemoryFile() as memfile:
        pass  # placeholder to keep structure simple if later expanded

    from rasterio.features import geometry_mask

    mask = ~geometry_mask(
        [geom],
        transform=transform,
        invert=False,
        out_shape=arr.shape,
        all_touched=False,
    )
    return int(arr[mask].sum())


def zonal_mean(arr: np.ndarray, geom, transform) -> float:
    from rasterio.features import geometry_mask

    if geom is None or geom.is_empty:
        return 0.0

    mask = ~geometry_mask(
        [geom],
        transform=transform,
        invert=False,
        out_shape=arr.shape,
        all_touched=False,
    )
    vals = arr[mask]
    if vals.size == 0:
        return 0.0
    return float(np.mean(vals))


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("LOADING INPUTS")
    print("=" * 80)

    favela_polys = gpd.read_file(FAVELA_POLYGONS_PATH)
    favela_polys = ensure_valid(favela_polys)

    final_mask, transform, raster_crs, profile = read_raster(FINAL_MASK_PATH)
    review_mask, _, _, _ = read_raster(REVIEW_ZONES_PATH)
    core_built, _, _, _ = read_raster(CORE_BUILT_PATH)
    uncertain_candidates, _, _, _ = read_raster(UNCERTAIN_CANDIDATES_PATH)
    uncertain_accepted, _, _, _ = read_raster(UNCERTAIN_ACCEPTED_PATH)
    uncertain_rejected, _, _, _ = read_raster(UNCERTAIN_REJECTED_PATH)
    wsf_support, _, _, _ = read_raster(WSF_SUPPORT_PATH)
    ghsl_support, _, _, _ = read_raster(GHSL_SUPPORT_PATH)
    wc_veg_support, _, _, _ = read_raster(WORLDCOVER_VEG_PATH)
    settlement_support, _, _, _ = read_raster(SETTLEMENT_SUPPORT_PATH)

    if favela_polys.crs != raster_crs:
        favela_polys = favela_polys.to_crs(raster_crs)

    print(f"Original favela polygons: {len(favela_polys)}")

    # stable source polygon id
    favela_polys = favela_polys.reset_index(drop=True).copy()
    favela_polys["favela_id"] = np.arange(1, len(favela_polys) + 1)

    # -------------------------------------------------------------------------
    # 1) Polygonize refined final raster
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("POLYGONIZING FINAL REFINED RASTER")
    print("=" * 80)

    raw_polys = polygonize_binary_mask((final_mask == 1).astype(np.uint8), transform, raster_crs, "mask_val")
    raw_polys = ensure_valid(raw_polys)
    raw_polys = explode_multipart(raw_polys)

    if len(raw_polys) > 0:
        raw_polys["area_m2"] = area_series_m2(raw_polys)
        raw_polys = raw_polys[raw_polys["area_m2"] >= MIN_RAW_POLYGON_AREA_M2].copy()
        raw_polys = raw_polys.reset_index(drop=True)
        raw_polys["raw_poly_id"] = np.arange(1, len(raw_polys) + 1)
    else:
        raw_polys["area_m2"] = []
        raw_polys["raw_poly_id"] = []

    print(f"Raw refined polygons: {len(raw_polys)}")
    raw_polys.to_file(RAW_POLYGONS_OUT, driver="GPKG")

    # -------------------------------------------------------------------------
    # 2) Polygonize review zones
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("POLYGONIZING REVIEW ZONES")
    print("=" * 80)

    review_polys = polygonize_binary_mask((review_mask == 1).astype(np.uint8), transform, raster_crs, "review_val")
    review_polys = ensure_valid(review_polys)
    review_polys = explode_multipart(review_polys)

    if len(review_polys) > 0:
        review_polys["area_m2"] = area_series_m2(review_polys)
        review_polys = review_polys[review_polys["area_m2"] >= MIN_RAW_POLYGON_AREA_M2].copy()
        review_polys = review_polys.reset_index(drop=True)
        review_polys["review_poly_id"] = np.arange(1, len(review_polys) + 1)
    else:
        review_polys["area_m2"] = []
        review_polys["review_poly_id"] = []

    print(f"Review polygons: {len(review_polys)}")
    review_polys.to_file(REVIEW_POLYGONS_OUT, driver="GPKG")

        # -------------------------------------------------------------------------
    # 3) Assign refined raw polygons to source favela polygons
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("ASSIGNING RAW REFINED POLYGONS TO SOURCE FAVELA POLYGONS")
    print("=" * 80)

    if len(raw_polys) > 0:
        raw_join = gpd.sjoin(
            raw_polys,
            favela_polys[["favela_id", "geometry"]],
            how="left",
            predicate="intersects",
        ).drop(columns=["index_right"], errors="ignore")

        # keep best match by largest intersection area
        if len(raw_join) > 0:
            raw_join = raw_join.copy()
            raw_join["intersect_area_m2"] = 0.0

            # build fast lookup for source geometries
            favela_geom_lookup = favela_polys.set_index("favela_id")["geometry"].to_dict()

            valid_rows = []

            for idx, row in raw_join.iterrows():
                g1 = row.geometry
                fid = row.get("favela_id", np.nan)

                # scalar-safe null handling
                if fid is None:
                    continue
                if isinstance(fid, (pd.Series, np.ndarray, list, tuple)):
                    continue
                if pd.isna(fid):
                    continue

                fid = int(fid)

                if fid not in favela_geom_lookup:
                    continue

                g2 = favela_geom_lookup[fid]
                inter_area = area_m2_of_geom(g1.intersection(g2), raster_crs)
                raw_join.at[idx, "intersect_area_m2"] = inter_area
                valid_rows.append(idx)

            if len(valid_rows) > 0:
                raw_join = raw_join.loc[valid_rows].copy()
                raw_join = raw_join.sort_values(
                    ["raw_poly_id", "intersect_area_m2"],
                    ascending=[True, False]
                )
                raw_join = raw_join.drop_duplicates(subset=["raw_poly_id"], keep="first").copy()
            else:
                raw_join = raw_polys.copy()
                raw_join["favela_id"] = np.nan
        else:
            raw_join = raw_polys.copy()
            raw_join["favela_id"] = np.nan
    else:
        raw_join = raw_polys.copy()
        raw_join["favela_id"] = np.nan

    # -------------------------------------------------------------------------
    # 4) Dissolve refined pieces by source favela polygon
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("DISSOLVING REFINED POLYGONS BY SOURCE FAVELA ID")
    print("=" * 80)

    if len(raw_join) > 0 and raw_join["favela_id"].notnull().any():
        dissolved = raw_join.dropna(subset=["favela_id"]).dissolve(by="favela_id", as_index=False)
        dissolved = ensure_valid(dissolved)
        dissolved = dissolved.reset_index(drop=True)
        dissolved["area_m2"] = area_series_m2(dissolved)
    else:
        dissolved = gpd.GeoDataFrame({"favela_id": []}, geometry=[], crs=raster_crs)

    print(f"Dissolved refined polygons: {len(dissolved)}")
    dissolved.to_file(DISSOLVED_POLYGONS_OUT, driver="GPKG")

    # -------------------------------------------------------------------------
    # 5) Build polygon-level QC table
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("COMPUTING POLYGON-LEVEL QC METRICS")
    print("=" * 80)

    favela_polys["original_area_m2"] = area_series_m2(favela_polys)

    dissolved_lookup = {}
    for _, row in dissolved.iterrows():
        dissolved_lookup[int(row["favela_id"])] = row.geometry

    review_lookup = {}
    if len(review_polys) > 0:
        review_join = gpd.overlay(
            review_polys[["review_poly_id", "geometry"]],
            favela_polys[["favela_id", "geometry"]],
            how="intersection"
        )
        if len(review_join) > 0:
            for fid, grp in review_join.groupby("favela_id"):
                review_lookup[int(fid)] = unary_union(list(grp.geometry))

    qc_rows = []

    for _, fav_row in favela_polys.iterrows():
        fid = int(fav_row["favela_id"])
        orig_geom = fav_row.geometry
        orig_area = float(fav_row["original_area_m2"])

        final_geom = dissolved_lookup.get(fid, None)
        if final_geom is None or final_geom.is_empty:
            final_area = 0.0
            removed_area = orig_area
            fragment_count = 0
        else:
            final_area = area_m2_of_geom(final_geom, raster_crs)
            removed_area = max(orig_area - final_area, 0.0)
            fragment_count = count_fragments(final_geom)

        review_geom = review_lookup.get(fid, None)
        review_area = area_m2_of_geom(review_geom, raster_crs) if review_geom is not None else 0.0

        # Raster zonal metrics inside original polygon
        core_pixels = zonal_sum_binary(core_built, orig_geom, transform, raster_crs)
        uncertain_pixels = zonal_sum_binary(uncertain_candidates, orig_geom, transform, raster_crs)
        accepted_pixels = zonal_sum_binary(uncertain_accepted, orig_geom, transform, raster_crs)
        rejected_pixels = zonal_sum_binary(uncertain_rejected, orig_geom, transform, raster_crs)
        wsf_pixels = zonal_sum_binary(wsf_support, orig_geom, transform, raster_crs)
        ghsl_pixels = zonal_sum_binary(ghsl_support, orig_geom, transform, raster_crs)
        wc_veg_pixels = zonal_sum_binary(wc_veg_support, orig_geom, transform, raster_crs)

        mean_settlement_support = zonal_mean(settlement_support, orig_geom, transform)

        row = {
            "favela_id": fid,
            "original_area_m2": orig_area,
            "final_area_m2": final_area,
            "removed_area_m2": removed_area,
            "final_to_original_area_ratio": safe_ratio(final_area, orig_area),
            "removed_area_ratio": safe_ratio(removed_area, orig_area),
            "review_zone_area_m2": review_area,
            "review_zone_area_ratio": safe_ratio(review_area, orig_area),
            "fragment_count": fragment_count,
            "core_built_pixels": core_pixels,
            "uncertain_candidate_pixels": uncertain_pixels,
            "uncertain_accepted_pixels": accepted_pixels,
            "uncertain_rejected_pixels": rejected_pixels,
            "wsf_support_pixels": wsf_pixels,
            "ghsl_support_pixels": ghsl_pixels,
            "worldcover_veg_pixels": wc_veg_pixels,
            "mean_settlement_support": mean_settlement_support,
        }

        qc_rows.append(row)

    qc_df = pd.DataFrame(qc_rows)

    qc_df["review_score"] = qc_df.apply(add_review_score, axis=1)
    qc_df["review_priority"] = qc_df["review_score"].apply(classify_priority)

    # Attach geometries for geopackage output:
    qc_gdf = favela_polys.merge(qc_df, on="favela_id", how="left")

    # Add final dissolved geometry as separate layer-friendly field via intersection status columns,
    # but keep original polygon geometry as the QC spatial reference.
    qc_gdf["has_refined_output"] = qc_gdf["final_area_m2"] > 0
    qc_gdf["needs_manual_review"] = qc_gdf["review_priority"].isin(["medium", "high"])

    # Save
    qc_gdf.to_file(QC_GPKG_OUT, driver="GPKG")
    qc_df.to_csv(QC_CSV_OUT, index=False)

    # -------------------------------------------------------------------------
    # 6) City summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("WRITING CITY SUMMARY")
    print("=" * 80)

    city_summary = {
        "city": CITY,
        "counts": {
            "original_favela_polygons": int(len(favela_polys)),
            "raw_refined_polygons": int(len(raw_polys)),
            "dissolved_refined_polygons": int(len(dissolved)),
            "review_polygons": int(len(review_polys)),
            "qc_low_priority": int((qc_df["review_priority"] == "low").sum()),
            "qc_medium_priority": int((qc_df["review_priority"] == "medium").sum()),
            "qc_high_priority": int((qc_df["review_priority"] == "high").sum()),
            "qc_needs_manual_review": int(qc_gdf["needs_manual_review"].sum()),
            "qc_no_refined_output": int((qc_df["final_area_m2"] == 0).sum()),
        },
        "areas_m2": {
            "original_total_area_m2": float(qc_df["original_area_m2"].sum()),
            "final_total_area_m2": float(qc_df["final_area_m2"].sum()),
            "removed_total_area_m2": float(qc_df["removed_area_m2"].sum()),
            "review_zone_total_area_m2": float(qc_df["review_zone_area_m2"].sum()),
        },
        "review_score_stats": {
            "mean_review_score": float(qc_df["review_score"].mean()) if len(qc_df) else 0.0,
            "max_review_score": int(qc_df["review_score"].max()) if len(qc_df) else 0,
        },
        "paths": {
            "raw_polygons": str(RAW_POLYGONS_OUT),
            "dissolved_polygons": str(DISSOLVED_POLYGONS_OUT),
            "review_polygons": str(REVIEW_POLYGONS_OUT),
            "qc_gpkg": str(QC_GPKG_OUT),
            "qc_csv": str(QC_CSV_OUT),
        }
    }

    with open(CITY_SUMMARY_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(city_summary, f, indent=2)

    print("Done.")
    print(f"Outputs written to: {OUT_DIR}")


if __name__ == "__main__":
    main()