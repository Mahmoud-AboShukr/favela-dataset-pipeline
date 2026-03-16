from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import shapes, rasterize
from shapely.geometry import shape
import fiona


ORIGINAL_MASK_PATH = Path("data/interim/masks/brasilia_favela_original_mask.tif")
REFINED_MASK_PATH = Path("data/interim/masks/brasilia_favela_refined_mapbiomas_no_ring_v2_2_fillholes_4px.tif")

ORIGINAL_POLYGONS_PATH = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
ORIGINAL_POLYGONS_LAYER = None  # set if needed

OUT_DIR = Path("reports/qc")
OUT_CSV = OUT_DIR / "refinement_metrics_brasilia.csv"
OUT_MD = OUT_DIR / "refinement_metrics_brasilia.md"
OUT_PER_POLYGON_CSV = OUT_DIR / "refinement_per_polygon_brasilia.csv"

MASK_NODATA = 255
METRIC_CRS = "EPSG:31983"  # Brasília-safe projected CRS


def pick_layer_name(gpkg_path: Path):
    layers = fiona.listlayers(str(gpkg_path))
    if not layers:
        raise ValueError(f"No layers found inside GeoPackage: {gpkg_path}")
    if len(layers) == 1:
        return layers[0]

    preferred = [
        "favelas_brasilia",
        "favelas",
        "favela",
        "setores_subnormais",
        "subnormais",
        "brasilia",
    ]
    for keyword in preferred:
        for layer in layers:
            if keyword in layer.lower():
                return layer
    return layers[0]


def load_original_polygons() -> gpd.GeoDataFrame:
    if not ORIGINAL_POLYGONS_PATH.exists():
        raise FileNotFoundError(f"Original polygons file not found: {ORIGINAL_POLYGONS_PATH}")

    layer = ORIGINAL_POLYGONS_LAYER if ORIGINAL_POLYGONS_LAYER else pick_layer_name(ORIGINAL_POLYGONS_PATH)
    print(f"Using original polygon file: {ORIGINAL_POLYGONS_PATH}")
    print(f"Using original polygon layer: {layer}")

    gdf = gpd.read_file(ORIGINAL_POLYGONS_PATH, layer=layer) if layer else gpd.read_file(ORIGINAL_POLYGONS_PATH)

    if gdf.empty:
        raise ValueError("Original polygons layer is empty.")

    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()

    if gdf.empty:
        raise ValueError("No valid original geometries found.")

    if "orig_id" not in gdf.columns:
        gdf["orig_id"] = np.arange(len(gdf), dtype=int)

    return gdf


def polygon_count_from_mask(mask_bool: np.ndarray, transform) -> int:
    count = 0
    arr = mask_bool.astype("uint8")
    for geom, value in shapes(arr, mask=mask_bool, transform=transform, connectivity=8):
        if int(value) == 1:
            poly = shape(geom)
            if not poly.is_empty:
                count += 1
    return count


def main():
    if not ORIGINAL_MASK_PATH.exists():
        raise FileNotFoundError(f"Original mask not found: {ORIGINAL_MASK_PATH}")
    if not REFINED_MASK_PATH.exists():
        raise FileNotFoundError(f"Refined mask not found: {REFINED_MASK_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(ORIGINAL_MASK_PATH) as orig_src, rasterio.open(REFINED_MASK_PATH) as ref_src:
        if (
            orig_src.width != ref_src.width
            or orig_src.height != ref_src.height
            or orig_src.transform != ref_src.transform
            or orig_src.crs != ref_src.crs
        ):
            raise ValueError("Original and refined masks are not aligned.")

        orig_arr = orig_src.read(1)
        ref_arr = ref_src.read(1)

        nodata = orig_src.nodata if orig_src.nodata is not None else MASK_NODATA
        valid = orig_arr != nodata

        original = (orig_arr == 1) & valid
        refined = (ref_arr == 1) & valid

        removed = original & (~refined)
        unchanged_kept = original & refined

        original_px = int(original.sum())
        refined_px = int(refined.sum())
        removed_px = int(removed.sum())
        unchanged_px = int(unchanged_kept.sum())

        removed_ratio = (removed_px / original_px * 100) if original_px else 0.0
        kept_ratio = (refined_px / original_px * 100) if original_px else 0.0

        refined_piece_count = polygon_count_from_mask(refined, ref_src.transform)

        # Approximate raster-cell area in metric CRS
        # Use pixel center polygons transformed to metric? Simpler:
        # 30m MapBiomas cell approx 900 m². Keep both pixel and approx area.
        approx_pixel_area_m2 = 900.0
        original_area_m2 = original_px * approx_pixel_area_m2
        refined_area_m2 = refined_px * approx_pixel_area_m2
        removed_area_m2 = removed_px * approx_pixel_area_m2

        summary_df = pd.DataFrame([
            {"metric": "original_pixels", "value": original_px},
            {"metric": "refined_pixels", "value": refined_px},
            {"metric": "removed_pixels", "value": removed_px},
            {"metric": "unchanged_kept_pixels", "value": unchanged_px},
            {"metric": "kept_ratio_percent", "value": round(kept_ratio, 4)},
            {"metric": "removed_ratio_percent", "value": round(removed_ratio, 4)},
            {"metric": "original_area_m2_approx", "value": round(original_area_m2, 2)},
            {"metric": "refined_area_m2_approx", "value": round(refined_area_m2, 2)},
            {"metric": "removed_area_m2_approx", "value": round(removed_area_m2, 2)},
            {"metric": "refined_polygon_piece_count", "value": refined_piece_count},
        ])
        summary_df.to_csv(OUT_CSV, index=False)

        # Per-original-polygon change
        orig_gdf = load_original_polygons()
        if orig_gdf.crs is None:
            raise ValueError("Original polygons have no CRS.")
        if orig_gdf.crs != orig_src.crs:
            orig_gdf = orig_gdf.to_crs(orig_src.crs)

        pixel_records = []
        for _, row in orig_gdf.iterrows():
            geom = row.geometry
            orig_id = int(row["orig_id"])

            single_mask = rasterize(
                [(geom, 1)],
                out_shape=(orig_src.height, orig_src.width),
                transform=orig_src.transform,
                fill=0,
                dtype="uint8",
                all_touched=False
            ).astype(bool)

            single_mask = single_mask & valid

            orig_poly_px = int(np.sum(original & single_mask))
            ref_poly_px = int(np.sum(refined & single_mask))
            removed_poly_px = orig_poly_px - ref_poly_px
            removed_poly_ratio = (removed_poly_px / orig_poly_px * 100) if orig_poly_px else 0.0
            changed = removed_poly_px > 0

            pixel_records.append({
                "orig_id": orig_id,
                "original_pixels": orig_poly_px,
                "refined_pixels": ref_poly_px,
                "removed_pixels": removed_poly_px,
                "removed_ratio_percent": round(removed_poly_ratio, 4),
                "changed": bool(changed),
            })

        per_poly_df = pd.DataFrame(pixel_records).sort_values("orig_id").reset_index(drop=True)
        per_poly_df.to_csv(OUT_PER_POLYGON_CSV, index=False)

    changed_count = int(per_poly_df["changed"].sum())
    strongly_changed_count = int((per_poly_df["removed_ratio_percent"] >= 20).sum())

    md_lines = [
        "# Brasília refinement QC metrics",
        "",
        f"- Original mask: `{ORIGINAL_MASK_PATH.as_posix()}`",
        f"- Refined mask: `{REFINED_MASK_PATH.as_posix()}`",
        "",
        "## Global metrics",
        f"- Original kept pixels: {original_px}",
        f"- Refined kept pixels: {refined_px}",
        f"- Removed pixels: {removed_px}",
        f"- Kept ratio: {kept_ratio:.4f}%",
        f"- Removed ratio: {removed_ratio:.4f}%",
        f"- Approx. original area: {original_area_m2:.2f} m²",
        f"- Approx. refined area: {refined_area_m2:.2f} m²",
        f"- Approx. removed area: {removed_area_m2:.2f} m²",
        f"- Refined polygon piece count: {refined_piece_count}",
        "",
        "## Per-polygon change",
        f"- Number of original polygons: {len(per_poly_df)}",
        f"- Number of polygons changed: {changed_count}",
        f"- Number of polygons strongly changed (>= 20% removed): {strongly_changed_count}",
        "",
        "## Most changed polygons",
    ]

    top_changed = per_poly_df.sort_values("removed_ratio_percent", ascending=False).head(10)
    for _, r in top_changed.iterrows():
        md_lines.append(
            f"- orig_id={int(r['orig_id'])}: removed {int(r['removed_pixels'])} px "
            f"({r['removed_ratio_percent']}%)"
        )

    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    print(f"Saved: {OUT_PER_POLYGON_CSV}")
    print()
    print(f"Original pixels: {original_px}")
    print(f"Refined pixels: {refined_px}")
    print(f"Removed pixels: {removed_px}")
    print(f"Removed ratio: {removed_ratio:.4f}%")
    print(f"Changed polygons: {changed_count}")
    print(f"Strongly changed polygons (>=20% removed): {strongly_changed_count}")


if __name__ == "__main__":
    main()