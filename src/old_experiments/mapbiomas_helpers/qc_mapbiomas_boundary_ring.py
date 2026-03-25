from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.errors import WindowError
from shapely.geometry import box
import fiona
import matplotlib.pyplot as plt


MAPBIOMAS_PATH = Path("data/interim/mapbiomas_clips/mapbiomas_brasilia_aoi_clip.tif")
FAVELA_PATH = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
FAVELA_LAYER: Optional[str] = None  # set explicitly if needed

OUT_DIR = Path("reports/qc/mapbiomas_ring_qc")
FIG_DIR = OUT_DIR / "figures"

OUT_PER_POLYGON_CSV = OUT_DIR / "mapbiomas_ring_per_polygon.csv"
OUT_GLOBAL_CSV = OUT_DIR / "mapbiomas_ring_global_summary.csv"
OUT_MD = OUT_DIR / "mapbiomas_ring_summary.md"

RING_WIDTH_M = 120.0
METRIC_CRS = "EPSG:31983"

VEGETATION_CLASSES = {3, 4, 5, 6, 11, 12, 49, 50}
KEEP_CLASSES = {24}
WATER_CLASSES = {31, 33}

CLASS_LABELS = {
    3: "Forest Formation",
    4: "Savanna Formation",
    5: "Mangrove",
    6: "Floodable Forest",
    11: "Wetland",
    12: "Grassland Formation",
    15: "Pasture",
    18: "Agriculture",
    19: "Temporary Crop",
    21: "Mosaic of Uses",
    23: "Beach, Dune and Sand Spot",
    24: "Urban Area",
    25: "Other Non Vegetated Areas",
    27: "Not Observed",
    29: "Rocky Outcrop",
    30: "Mining",
    31: "Aquaculture",
    33: "River, Lake and Ocean",
    36: "Perennial Crop",
    39: "Soybean",
    40: "Rice",
    41: "Other Temporary Crops",
    46: "Coffee",
    47: "Citrus",
    48: "Other Perennial Crops",
    49: "Wooded Sandbank Vegetation",
    50: "Herbaceous Sandbank Vegetation",
    62: "Cotton",
}


def pick_layer_name(gpkg_path: Path) -> Optional[str]:
    layers = fiona.listlayers(str(gpkg_path))
    if not layers:
        raise ValueError(f"No layers found inside GeoPackage: {gpkg_path}")
    if len(layers) == 1:
        return layers[0]

    preferred_keywords = [
        "favelas_brasilia",
        "favelas",
        "favela",
        "setores_subnormais",
        "subnormais",
        "brasilia",
    ]
    for keyword in preferred_keywords:
        for layer in layers:
            if keyword in layer.lower():
                return layer
    return layers[0]


def load_favelas() -> gpd.GeoDataFrame:
    if not FAVELA_PATH.exists():
        raise FileNotFoundError(f"Favela polygon file not found: {FAVELA_PATH}")

    layer_name = FAVELA_LAYER if FAVELA_LAYER else pick_layer_name(FAVELA_PATH)
    print(f"Using favela file: {FAVELA_PATH}")
    print(f"Using favela layer: {layer_name}")

    gdf = gpd.read_file(FAVELA_PATH, layer=layer_name) if layer_name else gpd.read_file(FAVELA_PATH)

    if gdf.empty:
        raise ValueError("Favela polygon layer is empty.")
    if "geometry" not in gdf.columns:
        raise ValueError("Favela layer has no geometry column.")

    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()
    if gdf.empty:
        raise ValueError("No valid favela geometries found.")

    if "favela_id" not in gdf.columns:
        gdf["favela_id"] = np.arange(len(gdf), dtype=int)

    return gdf


def summarize_array(arr: np.ndarray, nodata) -> pd.DataFrame:
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


def compute_zone_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "valid_px": 0,
            "urban_px": 0,
            "vegetation_px": 0,
            "water_px": 0,
            "uncertain_px": 0,
            "urban_pct": 0.0,
            "vegetation_pct": 0.0,
            "water_pct": 0.0,
            "uncertain_pct": 0.0,
            "top_class_value": None,
            "top_class_label": None,
        }

    valid_px = int(df["pixel_count"].sum())
    urban_px = int(df.loc[df["class_value"].isin(KEEP_CLASSES), "pixel_count"].sum())
    vegetation_px = int(df.loc[df["class_value"].isin(VEGETATION_CLASSES), "pixel_count"].sum())
    water_px = int(df.loc[df["class_value"].isin(WATER_CLASSES), "pixel_count"].sum())
    uncertain_px = valid_px - urban_px - vegetation_px - water_px

    top = df.iloc[0]

    return {
        "valid_px": valid_px,
        "urban_px": urban_px,
        "vegetation_px": vegetation_px,
        "water_px": water_px,
        "uncertain_px": uncertain_px,
        "urban_pct": round(urban_px / valid_px * 100, 4) if valid_px else 0.0,
        "vegetation_pct": round(vegetation_px / valid_px * 100, 4) if valid_px else 0.0,
        "water_pct": round(water_px / valid_px * 100, 4) if valid_px else 0.0,
        "uncertain_pct": round(uncertain_px / valid_px * 100, 4) if valid_px else 0.0,
        "top_class_value": int(top["class_value"]) if pd.notna(top["class_value"]) else None,
        "top_class_label": str(top["class_label"]) if pd.notna(top["class_label"]) else None,
    }


def make_core_and_ring(gdf: gpd.GeoDataFrame, ring_width_m: float) -> gpd.GeoDataFrame:
    gdf_metric = gdf.to_crs(METRIC_CRS).copy()

    core_geoms = []
    ring_geoms = []
    core_exists = []

    for geom in gdf_metric.geometry:
        if geom is None or geom.is_empty:
            core_geoms.append(None)
            ring_geoms.append(None)
            core_exists.append(False)
            continue

        inner = geom.buffer(-ring_width_m)

        if inner.is_empty:
            core_geoms.append(None)
            ring_geoms.append(geom)
            core_exists.append(False)
        else:
            core_geoms.append(inner)
            ring_geoms.append(geom.difference(inner))
            core_exists.append(True)

    gdf_metric["core_geom"] = core_geoms
    gdf_metric["ring_geom"] = ring_geoms
    gdf_metric["core_exists"] = core_exists

    return gdf_metric.to_crs(gdf.crs)


def filter_to_raster_extent(gdf: gpd.GeoDataFrame, src) -> gpd.GeoDataFrame:
    raster_bounds_geom = box(*src.bounds)
    keep = gdf.geometry.intersects(raster_bounds_geom)
    filtered = gdf.loc[keep].copy()

    dropped = int((~keep).sum())
    if dropped > 0:
        print(f"Dropped {dropped} polygons that do not intersect the clipped raster extent.")

    if filtered.empty:
        raise ValueError("No favela polygons intersect the clipped raster extent.")

    return filtered


def extract_zone_array(src, geom, nodata):
    if geom is None or geom.is_empty:
        return None

    try:
        arr, _ = mask(
            src,
            [geom],
            crop=True,
            filled=True,
            nodata=nodata
        )
        return arr[0]
    except (ValueError, WindowError):
        return None


def aggregate_global(rows: pd.DataFrame) -> pd.DataFrame:
    zone_cols = ["full", "core", "ring"]
    records = []

    for zone in zone_cols:
        valid_px = int(rows[f"{zone}_valid_px"].sum())
        urban_px = int(rows[f"{zone}_urban_px"].sum())
        vegetation_px = int(rows[f"{zone}_vegetation_px"].sum())
        water_px = int(rows[f"{zone}_water_px"].sum())
        uncertain_px = int(rows[f"{zone}_uncertain_px"].sum())

        records.append({
            "zone": zone,
            "valid_px": valid_px,
            "urban_px": urban_px,
            "vegetation_px": vegetation_px,
            "water_px": water_px,
            "uncertain_px": uncertain_px,
            "urban_pct": round(urban_px / valid_px * 100, 4) if valid_px else 0.0,
            "vegetation_pct": round(vegetation_px / valid_px * 100, 4) if valid_px else 0.0,
            "water_pct": round(water_px / valid_px * 100, 4) if valid_px else 0.0,
            "uncertain_pct": round(uncertain_px / valid_px * 100, 4) if valid_px else 0.0,
        })

    return pd.DataFrame(records)


def save_figures(global_df: pd.DataFrame, per_polygon_df: pd.DataFrame):
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    zones = global_df["zone"].tolist()
    urban = global_df["urban_pct"].tolist()
    veg = global_df["vegetation_pct"].tolist()
    uncertain = global_df["uncertain_pct"].tolist()
    water = global_df["water_pct"].tolist()

    plt.figure(figsize=(8, 5))
    plt.bar(zones, urban, label="Urban")
    plt.bar(zones, veg, bottom=urban, label="Vegetation")
    bottom2 = np.array(urban) + np.array(veg)
    plt.bar(zones, uncertain, bottom=bottom2, label="Uncertain")
    bottom3 = bottom2 + np.array(uncertain)
    plt.bar(zones, water, bottom=bottom3, label="Water")
    plt.ylabel("Percent of valid pixels")
    plt.title("MapBiomas class composition by polygon zone")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "mapbiomas_zone_composition.png", dpi=200)
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.scatter(
        per_polygon_df["core_vegetation_pct"],
        per_polygon_df["ring_vegetation_pct"],
        alpha=0.7
    )
    lim = max(
        float(per_polygon_df["core_vegetation_pct"].max()),
        float(per_polygon_df["ring_vegetation_pct"].max()),
        1.0
    )
    plt.plot([0, lim], [0, lim], linestyle="--")
    plt.xlabel("Core vegetation %")
    plt.ylabel("Ring vegetation %")
    plt.title("Vegetation share: ring vs core by polygon")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "mapbiomas_ring_vs_core_vegetation.png", dpi=200)
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.scatter(
        per_polygon_df["core_urban_pct"],
        per_polygon_df["ring_urban_pct"],
        alpha=0.7
    )
    lim = max(
        float(per_polygon_df["core_urban_pct"].max()),
        float(per_polygon_df["ring_urban_pct"].max()),
        1.0
    )
    plt.plot([0, lim], [0, lim], linestyle="--")
    plt.xlabel("Core urban %")
    plt.ylabel("Ring urban %")
    plt.title("Urban share: ring vs core by polygon")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "mapbiomas_ring_vs_core_urban.png", dpi=200)
    plt.close()


def write_markdown_summary(global_df: pd.DataFrame, per_polygon_df: pd.DataFrame):
    full_row = global_df.loc[global_df["zone"] == "full"].iloc[0]
    core_row = global_df.loc[global_df["zone"] == "core"].iloc[0]
    ring_row = global_df.loc[global_df["zone"] == "ring"].iloc[0]

    veg_higher_in_ring = int((per_polygon_df["ring_vegetation_pct"] > per_polygon_df["core_vegetation_pct"]).sum())
    urban_higher_in_core = int((per_polygon_df["core_urban_pct"] > per_polygon_df["ring_urban_pct"]).sum())
    total_polygons = int(len(per_polygon_df))
    core_existing = int(per_polygon_df["core_exists"].sum())

    high_risk = per_polygon_df[
        (per_polygon_df["ring_vegetation_pct"] < per_polygon_df["core_vegetation_pct"]) &
        (per_polygon_df["ring_urban_pct"] < 50)
    ].sort_values("ring_urban_pct").head(10)

    lines = [
        "# MapBiomas boundary-ring QC summary",
        "",
        f"- Input raster: `{MAPBIOMAS_PATH.as_posix()}`",
        f"- Favela polygons: `{FAVELA_PATH.as_posix()}`",
        f"- Ring width: `{RING_WIDTH_M} m`",
        f"- Number of polygons inspected: `{total_polygons}`",
        "",
        "## Global zone composition",
        f"- Full polygons: urban {full_row['urban_pct']}%, vegetation {full_row['vegetation_pct']}%, uncertain {full_row['uncertain_pct']}%, water {full_row['water_pct']}%",
        f"- Core: urban {core_row['urban_pct']}%, vegetation {core_row['vegetation_pct']}%, uncertain {core_row['uncertain_pct']}%, water {core_row['water_pct']}%",
        f"- Ring: urban {ring_row['urban_pct']}%, vegetation {ring_row['vegetation_pct']}%, uncertain {ring_row['uncertain_pct']}%, water {ring_row['water_pct']}%",
        "",
        "## Spatial QC signals",
        f"- Polygons where ring vegetation > core vegetation: {veg_higher_in_ring} / {total_polygons}",
        f"- Polygons where core urban > ring urban: {urban_higher_in_core} / {total_polygons}",
        "",
        "## Interpretation",
        "A conservative boundary-only refinement is more plausible if vegetation is systematically stronger in the ring and urban support is systematically stronger in the core.",
        "",
        "## High-risk polygons to inspect manually",
        f"- Polygons with non-empty core after 120 m inward buffer: {core_existing} / {total_polygons}",
    ]

    if high_risk.empty:
        lines.append("- None flagged by the current heuristic.")
    else:
        for _, row in high_risk.iterrows():
            lines.append(
                f"- favela_id={row['favela_id']}: core urban {row['core_urban_pct']}%, "
                f"ring urban {row['ring_urban_pct']}%, core vegetation {row['core_vegetation_pct']}%, "
                f"ring vegetation {row['ring_vegetation_pct']}%"
            )

    lines.extend([
        "",
        "## Generated figures",
        "- `figures/mapbiomas_zone_composition.png`",
        "- `figures/mapbiomas_ring_vs_core_vegetation.png`",
        "- `figures/mapbiomas_ring_vs_core_urban.png`",
    ])

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    if not MAPBIOMAS_PATH.exists():
        raise FileNotFoundError(f"MapBiomas clip not found: {MAPBIOMAS_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    favelas = load_favelas()
    favelas = make_core_and_ring(favelas, RING_WIDTH_M)

    rows = []

    with rasterio.open(MAPBIOMAS_PATH) as src:
        nodata = src.nodata

        if favelas.crs is None:
            raise ValueError("Favela polygons have no CRS.")

        if favelas.crs != src.crs:
            favelas = favelas.to_crs(src.crs)

        favelas = filter_to_raster_extent(favelas, src)

        skipped = 0

        for idx, row in favelas.iterrows():
            favela_id = row["favela_id"]
            full_geom = row.geometry
            core_geom = row["core_geom"]
            ring_geom = row["ring_geom"]

            full_arr = extract_zone_array(src, full_geom, nodata)
            if full_arr is None:
                skipped += 1
                continue

            core_arr = extract_zone_array(src, core_geom, nodata)
            ring_arr = extract_zone_array(src, ring_geom, nodata)

            full_df = summarize_array(full_arr, nodata)
            core_df = summarize_array(core_arr, nodata) if core_arr is not None else pd.DataFrame()
            ring_df = summarize_array(ring_arr, nodata) if ring_arr is not None else pd.DataFrame()

            full_metrics = compute_zone_metrics(full_df)
            core_metrics = compute_zone_metrics(core_df)
            ring_metrics = compute_zone_metrics(ring_df)

            rows.append({
                "favela_id": favela_id,
                "polygon_index": idx,
                "core_exists": bool(row["core_exists"]),
                **{f"full_{k}": v for k, v in full_metrics.items()},
                **{f"core_{k}": v for k, v in core_metrics.items()},
                **{f"ring_{k}": v for k, v in ring_metrics.items()},
            })

    if skipped > 0:
        print(f"Skipped {skipped} polygons with no raster overlap after per-geometry masking.")

    if not rows:
        raise ValueError("No overlapping polygons remained after raster-overlap filtering.")

    per_polygon_df = pd.DataFrame(rows).sort_values("favela_id").reset_index(drop=True)
    global_df = aggregate_global(per_polygon_df)

    per_polygon_df.to_csv(OUT_PER_POLYGON_CSV, index=False)
    global_df.to_csv(OUT_GLOBAL_CSV, index=False)

    save_figures(global_df, per_polygon_df)
    write_markdown_summary(global_df, per_polygon_df)

    print(f"Saved: {OUT_PER_POLYGON_CSV}")
    print(f"Saved: {OUT_GLOBAL_CSV}")
    print(f"Saved: {OUT_MD}")
    print(f"Saved figures in: {FIG_DIR}")


if __name__ == "__main__":
    main()