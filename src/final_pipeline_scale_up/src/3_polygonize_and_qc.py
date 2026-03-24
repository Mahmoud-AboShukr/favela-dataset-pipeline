"""
3_polygonize_and_qc.py

Purpose
-------
Convert the refined raster mask into polygon outputs and compute QC layers/metrics.

Main responsibilities
---------------------
1. Polygonize the cleaned refined mask.
2. Intersect / relate refined polygons to source favela polygons.
3. Dissolve results by source favela ID or another grouping rule.
4. Compute QC metrics.
5. Export review layers for manual inspection.

Why this stage matters
----------------------
The project's final usable output is polygon-based. Raster logic is only the
internal decision mechanism. The final deliverables must support:
- manual review,
- correction,
- comparison with original polygons,
- reporting.
"""

from pathlib import Path
import csv


# =============================================================================
# CONFIG
# =============================================================================

CITY_NAME = "manaus"

BASE_DIR = Path("data/processed/final_pipeline") / CITY_NAME
PREPARED_DIR = BASE_DIR / "prepared"
REFINED_DIR = BASE_DIR / "refined"
POLY_DIR = BASE_DIR / "polygonized"
POLY_DIR.mkdir(parents=True, exist_ok=True)

REFINED_MASK_PATH = REFINED_DIR / "refined_mask_clean.tif"
FAVELA_VECTOR_PATH = Path("data/interim/polygons_clean/favelas_clean.gpkg")


# =============================================================================
# HELPER PLACEHOLDERS
# =============================================================================

def read_raster(path):
    """
    Read raster and profile.
    """
    raise NotImplementedError


def polygonize_binary_raster(mask_path):
    """
    Polygonize the refined binary raster.

    Output:
        raw polygon GeoDataFrame
    """
    raise NotImplementedError


def load_favela_subset(favela_path, city_name):
    """
    Load the source favela polygons corresponding to the AOI/city.
    """
    raise NotImplementedError


def assign_source_ids(refined_gdf, source_favelas_gdf):
    """
    Link each refined polygon back to its source favela polygon.

    This can be done by:
    - spatial join,
    - max-overlap assignment,
    - centroid-in-polygon,
    depending on the desired rule.
    """
    raise NotImplementedError


def dissolve_by_source_id(refined_gdf):
    """
    Dissolve refined polygons by source favela ID.

    This gives the main final polygon layer for manual review.
    """
    raise NotImplementedError


def build_review_flags(refined_gdf, dissolved_gdf, source_gdf):
    """
    Create a review layer highlighting suspicious cases.

    Example flags:
    - very small refined polygon
    - large area loss
    - fragmented output
    - no refined result for a source favela
    """
    raise NotImplementedError


def compute_qc_metrics(source_gdf, raw_gdf, dissolved_gdf):
    """
    Compute QC metrics such as:
    - number of source polygons
    - number of raw refined polygons
    - number of dissolved refined polygons
    - total source area
    - total refined area
    - mean area change
    """
    raise NotImplementedError


def save_vector(gdf, output_path):
    """
    Save vector layer as GPKG.
    """
    raise NotImplementedError


def save_qc_csv(metrics_dict, output_path):
    """
    Save QC metrics to CSV.
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for k, v in metrics_dict.items():
            writer.writerow([k, v])


# =============================================================================
# MAIN PIPELINE LOGIC
# =============================================================================

def main():
    print("=" * 80)
    print("STAGE 3 — POLYGONIZE AND QC")
    print("=" * 80)

    # 1. Polygonize refined raster
    print("\n[1] Polygonizing refined raster...")
    refined_raw_gdf = polygonize_binary_raster(REFINED_MASK_PATH)

    # 2. Load source favela polygons
    print("\n[2] Loading source favela polygons...")
    source_favelas_gdf = load_favela_subset(FAVELA_VECTOR_PATH, CITY_NAME)

    # 3. Link refined polygons to source IDs
    print("\n[3] Assigning source favela IDs...")
    refined_raw_gdf = assign_source_ids(refined_raw_gdf, source_favelas_gdf)

    # 4. Dissolve by source favela ID
    print("\n[4] Dissolving refined polygons by source ID...")
    refined_dissolved_gdf = dissolve_by_source_id(refined_raw_gdf)

    # 5. Build review flags
    print("\n[5] Building review layer...")
    review_gdf = build_review_flags(
        refined_raw_gdf,
        refined_dissolved_gdf,
        source_favelas_gdf
    )

    # 6. Compute QC metrics
    print("\n[6] Computing QC metrics...")
    qc_metrics = compute_qc_metrics(
        source_favelas_gdf,
        refined_raw_gdf,
        refined_dissolved_gdf
    )

    # 7. Save outputs
    print("\n[7] Saving outputs...")
    save_vector(refined_raw_gdf, POLY_DIR / "refined_raw.gpkg")
    save_vector(refined_dissolved_gdf, POLY_DIR / "refined_dissolved.gpkg")
    save_vector(review_gdf, POLY_DIR / "review_flags.gpkg")
    save_qc_csv(qc_metrics, POLY_DIR / "qc_metrics.csv")

    print("\nQC summary:")
    for k, v in qc_metrics.items():
        print(f"  {k}: {v}")

    print("\nDone: stage 3 produced polygon outputs and QC artifacts.")


if __name__ == "__main__":
    main()