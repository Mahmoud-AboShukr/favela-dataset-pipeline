from pathlib import Path
import tempfile
import shutil

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.lines import Line2D
from rasterio.features import rasterize, shapes
from rasterio.mask import mask
from rasterio.plot import show
from shapely.geometry import shape

from batch2_config import (
    AOI_ROOT,
    BATCH_ROOT,
    BUILT_CLASSES,
    CITIES,
    CLASS_COLORS,
    CLASS_LABELS,
    DEFAULT_COLOR,
    MASK_ROOT,
    OUT_NODATA,
    POLY_ROOT,
    QC_ROOT,
    RASTER_ROOT,
    REFINEMENT_VARIANT,
    STRICT_VEGETATION_CLASSES,
)


def save_uint8(arr: np.ndarray, meta_template: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta = meta_template.copy()
    meta.update({
        "dtype": "uint8",
        "count": 1,
        "nodata": OUT_NODATA,
        "compress": "lzw",
    })

    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False, dir=str(out_path.parent)) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with rasterio.open(tmp_path, "w", **meta) as dst:
            dst.write(arr, 1)
        shutil.move(str(tmp_path), str(out_path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def load_gdf(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError(f"Empty layer: {path}")
    return gdf


def summarize_values(arr: np.ndarray, nodata) -> pd.DataFrame:
    flat = arr.reshape(-1)
    if nodata is not None:
        flat = flat[flat != nodata]

    if flat.size == 0:
        return pd.DataFrame(columns=["class_value", "pixel_count", "percent", "class_label"])

    unique, counts = np.unique(flat, return_counts=True)
    df = pd.DataFrame({
        "class_value": unique.astype(int),
        "pixel_count": counts.astype(int),
    })
    total = int(df["pixel_count"].sum())
    df["percent"] = (df["pixel_count"] / total * 100).round(4)
    df["class_label"] = df["class_value"].map(CLASS_LABELS).fillna("Unknown")
    df = df.sort_values(["pixel_count", "class_value"], ascending=[False, True]).reset_index(drop=True)
    return df


def summarize_masked_values(arr: np.ma.MaskedArray) -> pd.DataFrame:
    flat = arr.compressed()

    if flat.size == 0:
        return pd.DataFrame(columns=["class_value", "pixel_count", "percent", "class_label"])

    unique, counts = np.unique(flat, return_counts=True)
    df = pd.DataFrame({
        "class_value": unique.astype(int),
        "pixel_count": counts.astype(int),
    })
    total = int(df["pixel_count"].sum())
    df["percent"] = (df["pixel_count"] / total * 100).round(4)
    df["class_label"] = df["class_value"].map(CLASS_LABELS).fillna("Unknown")
    df = df.sort_values(["pixel_count", "class_value"], ascending=[False, True]).reset_index(drop=True)
    return df


def write_markdown_summary(
    out_path: Path,
    city: str,
    raster_path: Path,
    favela_path: Path,
    nodata,
    aoi_df: pd.DataFrame,
    favela_df: pd.DataFrame,
) -> None:
    unique_values = sorted(aoi_df["class_value"].tolist()) if not aoi_df.empty else []
    favela_values = sorted(favela_df["class_value"].tolist()) if not favela_df.empty else []

    lines = [
        f"# MapBiomas 10 m unique values summary — {city}",
        "",
        f"- Input raster: `{raster_path.as_posix()}`",
        f"- Favela polygons: `{favela_path.as_posix()}`",
        f"- Nodata: `{nodata}`",
        "",
        "## Unique values in AOI clip",
        ", ".join(map(str, unique_values)) if unique_values else "None",
        "",
        "## Unique values inside favela polygons",
        ", ".join(map(str, favela_values)) if favela_values else "None",
        "",
        "## Top classes in AOI",
    ]

    if aoi_df.empty:
        lines.append("- No valid AOI pixels found.")
    else:
        for _, row in aoi_df.head(20).iterrows():
            lines.append(
                f"- {int(row['class_value'])}: {row['class_label']} "
                f"({int(row['pixel_count'])} px, {row['percent']}%)"
            )

    lines.extend(["", "## Top classes inside favela polygons"])
    if favela_df.empty:
        lines.append("- No valid favela-overlap pixels found.")
    else:
        for _, row in favela_df.head(20).iterrows():
            lines.append(
                f"- {int(row['class_value'])}: {row['class_label']} "
                f"({int(row['pixel_count'])} px, {row['percent']}%)"
            )

    out_path.write_text("\n".join(lines), encoding="utf-8")


def inspect_classes(city: str) -> pd.DataFrame:
    raster_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    favela_path = AOI_ROOT / city / f"favelas_{city}.gpkg"
    out_dir = QC_ROOT / city
    out_dir.mkdir(parents=True, exist_ok=True)

    out_aoi_csv = out_dir / f"{city}_aoi_class_histogram.csv"
    out_favela_csv = out_dir / f"{city}_favela_polygon_class_histogram.csv"
    out_values_md = out_dir / f"{city}_unique_values.md"

    with rasterio.open(raster_path) as src:
        arr = src.read(1)
        nodata = src.nodata
        aoi_df = summarize_values(arr, nodata)
        aoi_df.to_csv(out_aoi_csv, index=False)

        favela_gdf = gpd.read_file(favela_path)
        if favela_gdf.crs != src.crs:
            favela_gdf = favela_gdf.to_crs(src.crs)

        geoms = [g for g in favela_gdf.geometry if g is not None and not g.is_empty]
        favela_arr, _ = mask(src, geoms, crop=False, filled=False)
        favela_df = summarize_masked_values(favela_arr[0])
        favela_df.to_csv(out_favela_csv, index=False)

        write_markdown_summary(
            out_path=out_values_md,
            city=city,
            raster_path=raster_path,
            favela_path=favela_path,
            nodata=nodata,
            aoi_df=aoi_df,
            favela_df=favela_df,
        )

    return favela_df


def build_masks(city: str) -> None:
    raster_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    veg_out = MASK_ROOT / city / f"{city}_mapbiomas_10m_vegetation_mask_strict.tif"
    built_out = MASK_ROOT / city / f"{city}_mapbiomas_10m_built_mask.tif"

    with rasterio.open(raster_path) as src:
        arr = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodata

        valid = np.ones(arr.shape, dtype=bool)
        if nodata is not None:
            valid &= arr != nodata

        veg_mask = np.isin(arr, list(STRICT_VEGETATION_CLASSES)) & valid
        built_mask = np.isin(arr, list(BUILT_CLASSES)) & valid

        save_uint8(veg_mask.astype(np.uint8), meta, veg_out)
        save_uint8(built_mask.astype(np.uint8), meta, built_out)


def ensure_aligned(ref_src, other_src, name: str) -> None:
    if (
        ref_src.width != other_src.width
        or ref_src.height != other_src.height
        or ref_src.transform != other_src.transform
        or ref_src.crs != other_src.crs
    ):
        raise ValueError(f"{name} is not aligned with the reference raster.")


def rasterize_favelas(gdf: gpd.GeoDataFrame, ref_src) -> np.ndarray:
    if gdf.crs != ref_src.crs:
        gdf = gdf.to_crs(ref_src.crs)

    shapes_iter = ((geom, 1) for geom in gdf.geometry if geom is not None and not geom.is_empty)

    arr = rasterize(
        shapes=shapes_iter,
        out_shape=(ref_src.height, ref_src.width),
        transform=ref_src.transform,
        fill=0,
        dtype="uint8",
        all_touched=False,
    )
    return arr


def to_output(mask_bool: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = np.full(mask_bool.shape, OUT_NODATA, dtype=np.uint8)
    out[valid] = 0
    out[valid & mask_bool] = 1
    return out


def refine_keep_uncertain(city: str) -> None:
    mapbiomas_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    veg_mask_path = MASK_ROOT / city / f"{city}_mapbiomas_10m_vegetation_mask_strict.tif"
    built_mask_path = MASK_ROOT / city / f"{city}_mapbiomas_10m_built_mask.tif"
    favela_path = AOI_ROOT / city / f"favelas_{city}.gpkg"

    out_original = MASK_ROOT / city / f"{city}_favela_original_mask_10m.tif"
    out_keep = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain.tif"
    out_remove = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_2_remove_uncertain.tif"

    favelas = load_gdf(favela_path)

    with (
        rasterio.open(mapbiomas_path) as ref_src,
        rasterio.open(veg_mask_path) as veg_src,
        rasterio.open(built_mask_path) as built_src,
    ):
        ensure_aligned(ref_src, veg_src, "Vegetation mask")
        ensure_aligned(ref_src, built_src, "Built mask")

        ref_arr = ref_src.read(1)
        ref_nodata = ref_src.nodata
        valid = np.ones(ref_arr.shape, dtype=bool)
        if ref_nodata is not None:
            valid &= ref_arr != ref_nodata

        veg = veg_src.read(1) == 1
        built = built_src.read(1) == 1

        original = rasterize_favelas(favelas, ref_src).astype(bool)
        original = original & valid

        keep_uncertain = original.copy()
        keep_uncertain[original & veg & (~built)] = False

        remove_uncertain = original.copy()
        remove_uncertain[original & (~built)] = False

        meta_template = ref_src.meta.copy()

    save_uint8(to_output(original, valid), meta_template, out_original)
    save_uint8(to_output(keep_uncertain, valid), meta_template, out_keep)
    save_uint8(to_output(remove_uncertain, valid), meta_template, out_remove)


def polygonize_keep_uncertain(city: str) -> None:
    in_path = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain.tif"
    raw_out = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_raw.gpkg"
    dissolved_out = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_dissolved.gpkg"

    raw_out.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(in_path) as src:
        arr = src.read(1)
        feats = []
        for geom, value in shapes(arr, mask=(arr == 1), transform=src.transform):
            if int(value) == 1:
                feats.append({"geometry": shape(geom), "value": 1})
        crs = src.crs

    if not feats:
        raise ValueError(f"No kept polygons found for city: {city}")

    gdf = gpd.GeoDataFrame(feats, crs=crs)
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
    gdf.to_file(raw_out, driver="GPKG")

    dissolved = gdf.dissolve(by="value").reset_index(drop=True)
    dissolved["source"] = f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain"
    dissolved.to_file(dissolved_out, driver="GPKG")


def area_m2(gdf: gpd.GeoDataFrame) -> float:
    ea = gdf.to_crs("EPSG:5880")
    return float(ea.geometry.area.sum())


def qc_keep_uncertain(city: str) -> dict:
    orig_path = AOI_ROOT / city / f"favelas_{city}.gpkg"
    original_mask_path = MASK_ROOT / city / f"{city}_favela_original_mask_10m.tif"
    refined_mask_path = MASK_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain.tif"
    raw_poly_path = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_raw.gpkg"
    dissolved_path = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_dissolved.gpkg"

    orig_gdf = load_gdf(orig_path)
    raw_gdf = load_gdf(raw_poly_path)
    dissolved_gdf = load_gdf(dissolved_path)

    with rasterio.open(original_mask_path) as src_orig:
        orig_arr = src_orig.read(1)
        orig_nodata = src_orig.nodata
        orig_valid = orig_arr != orig_nodata if orig_nodata is not None else np.ones(orig_arr.shape, dtype=bool)

    with rasterio.open(refined_mask_path) as src_ref:
        ref_arr = src_ref.read(1)
        ref_nodata = src_ref.nodata
        ref_valid = ref_arr != ref_nodata if ref_nodata is not None else np.ones(ref_arr.shape, dtype=bool)

    original_kept_pixels = int(((orig_arr == 1) & orig_valid).sum())
    refined_kept_pixels = int(((ref_arr == 1) & ref_valid).sum())
    removed_pixels = original_kept_pixels - refined_kept_pixels
    kept_ratio = (refined_kept_pixels / original_kept_pixels * 100) if original_kept_pixels else 0.0
    removed_ratio = (removed_pixels / original_kept_pixels * 100) if original_kept_pixels else 0.0

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
        "approx_original_area_m2_from_raster": original_kept_pixels * 100.0,
        "approx_refined_area_m2_from_raster": refined_kept_pixels * 100.0,
        "approx_removed_area_m2_from_raster": removed_pixels * 100.0,
        "original_vector_area_m2": round(area_m2(orig_gdf), 2),
        "raw_vector_area_m2": round(area_m2(raw_gdf), 2),
        "dissolved_vector_area_m2": round(area_m2(dissolved_gdf), 2),
    }
    return row


def mapbiomas_to_rgb(arr: np.ndarray) -> np.ndarray:
    rgb = np.zeros((arr.shape[0], arr.shape[1], 3), dtype=np.uint8)
    for val in np.unique(arr):
        color = CLASS_COLORS.get(int(val), DEFAULT_COLOR).lstrip("#")
        rgb[arr == val] = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
    return rgb


def make_overview_figure(city: str) -> None:
    raster_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    orig_path = AOI_ROOT / city / f"favelas_{city}.gpkg"
    raw_path = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_raw.gpkg"
    dissolved_path = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_dissolved.gpkg"

    out_city_dir = BATCH_ROOT / "figures" / city
    out_city_dir.mkdir(parents=True, exist_ok=True)

    out_dissolved = out_city_dir / f"{city}_overview_original_vs_dissolved.png"
    out_raw = out_city_dir / f"{city}_overview_original_vs_raw.png"

    orig = gpd.read_file(orig_path)
    raw = gpd.read_file(raw_path)
    dissolved = gpd.read_file(dissolved_path)

    with rasterio.open(raster_path) as src:
        arr = src.read(1)
        rgb = mapbiomas_to_rgb(arr)

        if orig.crs != src.crs:
            orig = orig.to_crs(src.crs)
        if raw.crs != src.crs:
            raw = raw.to_crs(src.crs)
        if dissolved.crs != src.crs:
            dissolved = dissolved.to_crs(src.crs)

        legend_handles_raw = [
            Line2D([0], [0], color="black", lw=1.2, label="Original favela polygons"),
            Line2D([0], [0], color="cyan", lw=1.0, label="Raw refined pieces (keep-uncertain)"),
        ]
        legend_handles_dissolved = [
            Line2D([0], [0], color="black", lw=1.2, label="Original favela polygons"),
            Line2D([0], [0], color="yellow", lw=1.2, label="Dissolved refined output (keep-uncertain)"),
        ]

        fig, ax = plt.subplots(figsize=(12, 12))
        show(rgb.transpose(2, 0, 1), transform=src.transform, ax=ax)
        orig.boundary.plot(ax=ax, color="black", linewidth=0.5)
        dissolved.boundary.plot(ax=ax, color="yellow", linewidth=0.8)
        ax.set_title(f"{city} — Original vs dissolved keep-uncertain output")
        ax.set_axis_off()
        ax.legend(handles=legend_handles_dissolved, loc="lower left", framealpha=0.9)
        plt.tight_layout()
        plt.savefig(out_dissolved, dpi=220, bbox_inches="tight")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(12, 12))
        show(rgb.transpose(2, 0, 1), transform=src.transform, ax=ax)
        orig.boundary.plot(ax=ax, color="black", linewidth=0.5)
        raw.boundary.plot(ax=ax, color="cyan", linewidth=0.4)
        ax.set_title(f"{city} — Original vs raw keep-uncertain output")
        ax.set_axis_off()
        ax.legend(handles=legend_handles_raw, loc="lower left", framealpha=0.9)
        plt.tight_layout()
        plt.savefig(out_raw, dpi=220, bbox_inches="tight")
        plt.close(fig)


def run_city(city: str) -> dict:
    print(f"\n{'=' * 80}")
    print(f"RUNNING BATCH 2 PIPELINE FOR: {city}")
    print(f"{'=' * 80}")

    favela_df = inspect_classes(city)
    print("\nTop classes inside favela polygons:")
    print(favela_df.head(10).to_string(index=False))

    build_masks(city)
    print("Masks built.")

    refine_keep_uncertain(city)
    print("Refinement complete.")

    polygonize_keep_uncertain(city)
    print("Polygonization complete.")

    qc_row = qc_keep_uncertain(city)
    print("QC complete.")

    make_overview_figure(city)
    print("Overview figures complete.")

    return qc_row


def main():
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)

    qc_rows = []
    for city in CITIES:
        qc_rows.append(run_city(city))

    out_csv = BATCH_ROOT / "batch2_keep_uncertain_qc_summary.csv"
    pd.DataFrame(qc_rows).to_csv(out_csv, index=False)
    print(f"\nSaved batch summary: {out_csv}")
    print("\nDone.")


if __name__ == "__main__":
    main()