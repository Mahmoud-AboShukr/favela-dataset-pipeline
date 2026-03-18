from pathlib import Path
import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd


CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

AOI_ROOT = Path("data/interim/aoi")
MASK_ROOT = Path("data/interim/masks")
POLY_ROOT = Path("data/processed/polygons")
OUT_ROOT = Path("reports/qc/mapbiomas_10m")


def load_gdf(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError(f"Empty layer: {path}")
    return gdf


def area_m2(gdf: gpd.GeoDataFrame) -> float:
    # Use SIRGAS 2000 / Brazil Albers equal-area
    ea = gdf.to_crs("EPSG:5880")
    return float(ea.geometry.area.sum())


def qc_one_city(city: str) -> dict:
    orig_path = AOI_ROOT / city / f"favelas_{city}.gpkg"
    refined_mask_path = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain.tif"
    raw_poly_path = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_raw.gpkg"
    dissolved_path = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_dissolved.gpkg"

    orig_gdf = load_gdf(orig_path)
    raw_gdf = load_gdf(raw_poly_path)
    dissolved_gdf = load_gdf(dissolved_path)

    with rasterio.open(refined_mask_path) as src:
        arr = src.read(1)
        nodata = src.nodata
        valid = arr != nodata if nodata is not None else np.ones(arr.shape, dtype=bool)

        original_mask_path = MASK_ROOT / city / f"{city}_favela_original_mask_10m.tif"
        with rasterio.open(original_mask_path) as src_orig:
            orig_arr = src_orig.read(1)
            orig_nodata = src_orig.nodata
            orig_valid = orig_arr != orig_nodata if orig_nodata is not None else np.ones(orig_arr.shape, dtype=bool)

        original_kept_pixels = int(((orig_arr == 1) & orig_valid).sum())
        refined_kept_pixels = int(((arr == 1) & valid).sum())
        removed_pixels = original_kept_pixels - refined_kept_pixels
        kept_ratio = (refined_kept_pixels / original_kept_pixels * 100) if original_kept_pixels else 0.0
        removed_ratio = (removed_pixels / original_kept_pixels * 100) if original_kept_pixels else 0.0

        pixel_area_m2 = 100.0  # 10 m pixels

    original_area_m2 = area_m2(orig_gdf)
    raw_area_m2 = area_m2(raw_gdf)
    dissolved_area_m2 = area_m2(dissolved_gdf)

    row = {
        "city": city,
        "original_polygon_count": len(orig_gdf),
        "raw_piece_count": len(raw_gdf),
        "dissolved_row_count": len(dissolved_gdf),
        "original_kept_pixels": original_kept_pixels,
        "refined_kept_pixels": refined_kept_pixels,
        "removed_pixels": removed_pixels,
        "kept_ratio_percent": round(kept_ratio, 4),
        "removed_ratio_percent": round(removed_ratio, 4),
        "approx_original_area_m2_from_raster": original_kept_pixels * pixel_area_m2,
        "approx_refined_area_m2_from_raster": refined_kept_pixels * pixel_area_m2,
        "approx_removed_area_m2_from_raster": removed_pixels * pixel_area_m2,
        "original_vector_area_m2": round(original_area_m2, 2),
        "raw_vector_area_m2": round(raw_area_m2, 2),
        "dissolved_vector_area_m2": round(dissolved_area_m2, 2),
    }

    print(f"\n=== {city} ===")
    for k, v in row.items():
        if k != "city":
            print(f"{k}: {v}")

    return row


def main():
    rows = []
    for city in CITIES:
        rows.append(qc_one_city(city))

    out_dir = OUT_ROOT / "batch1"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / "batch1_keep_uncertain_qc_summary.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\nSaved summary: {out_csv}")


if __name__ == "__main__":
    main()