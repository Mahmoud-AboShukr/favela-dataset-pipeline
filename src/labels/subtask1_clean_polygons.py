from pathlib import Path

import pandas as pd
import geopandas as gpd


def _ensure_dir(p: str | Path) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)


def _make_valid(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Prefer geopandas' make_valid when available; fall back to buffer(0).
    """
    try:
        gdf["geometry"] = gdf.make_valid()
        return gdf
    except Exception:
        gdf["geometry"] = gdf["geometry"].buffer(0)
        return gdf


def clean_polygons(
    shp_path: str | Path,
    out_gpkg: str | Path,
    layer_name: str = "favelas_clean",
    target_crs: str = "EPSG:4326",
    id_field: str | None = None,  # optional: existing stable ID column in shapefile
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:

    shp_path = Path(shp_path).resolve()
    out_gpkg = Path(out_gpkg)
    _ensure_dir(out_gpkg)

    # --- Read
    gdf = gpd.read_file(shp_path)
    n0 = len(gdf)
    input_crs = str(gdf.crs)

    if gdf.crs is None:
        raise ValueError(
            "Input shapefile CRS is missing. "
            "Check the .prj file and set CRS explicitly before continuing."
        )

    # --- CRS standardization
    gdf = gdf.to_crs(target_crs)

    # --- Drop empty geometries
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    n1 = len(gdf)

    # --- Fix invalid geometries
    invalid_before = int((~gdf.is_valid).sum())
    if invalid_before > 0:
        gdf = _make_valid(gdf)
    invalid_after = int((~gdf.is_valid).sum())

    # --- Preserve original ID if available (optional)
    if id_field and id_field in gdf.columns:
        gdf["gov_id"] = gdf[id_field].astype(str)
    else:
        gdf["gov_id"] = None

    # --- Create stable "source_id" BEFORE explode (based on current row order)
    gdf = gdf.reset_index(drop=True)
    gdf["source_id"] = gdf.index.astype("int64")

    # --- Explode multipolygons into single polygons
    gdf = gdf.explode(index_parts=False)
    gdf = gdf.reset_index(drop=True)

    # Count after explode
    n2 = len(gdf)

    # --- Part index per original source_id (0,1,2,...)
    gdf["part_index"] = gdf.groupby("source_id").cumcount().astype("int64")

    # --- Unique ID per exploded geometry
    gdf["favela_id"] = gdf["source_id"].astype(str) + "_" + gdf["part_index"].astype(str)

    # --- Quick ID sanity checks
    dup_favela_id = int(gdf["favela_id"].duplicated().sum())
    if dup_favela_id != 0:
        raise ValueError(f"Unexpected duplicate favela_id count: {dup_favela_id}")

    # --- Area sanity stats (projected CRS for meters²; EPSG:3857 is ok for diagnostics)
    gdf_area = gdf.to_crs("EPSG:3857")
    areas = gdf_area.geometry.area

    summary = pd.DataFrame([{
        "input_path": str(shp_path),
        "input_crs": input_crs,
        "target_crs": target_crs,
        "n_loaded": n0,
        "n_after_drop_empty": n1,
        "n_after_explode": n2,
        "invalid_before": invalid_before,
        "invalid_after": invalid_after,
        "favela_id_duplicates": dup_favela_id,
        "area_m2_min": float(areas.min()) if len(areas) else None,
        "area_m2_median": float(areas.median()) if len(areas) else None,
        "area_m2_max": float(areas.max()) if len(areas) else None,
    }])

    # --- Save
    gdf.to_file(out_gpkg, layer=layer_name, driver="GPKG")

    return gdf, summary


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Subtask 1: Clean favela polygons shapefile -> GeoPackage")
    parser.add_argument("shp_path", type=str, help="Path to input .shp")
    parser.add_argument("--out", type=str, default="data/interim/polygons_clean/favelas_clean.gpkg")
    parser.add_argument("--layer", type=str, default="favelas_clean")
    parser.add_argument("--crs", type=str, default="EPSG:4326")
    parser.add_argument("--id-field", type=str, default=None, help="Existing stable ID column name (optional)")
    args = parser.parse_args()

    _, summary = clean_polygons(
        shp_path=args.shp_path,
        out_gpkg=args.out,
        layer_name=args.layer,
        target_crs=args.crs,
        id_field=args.id_field,
    )

    summary_path = Path(args.out).with_suffix("").as_posix() + "_summary.csv"
    Path(summary_path).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_path, index=False)

    print("✅ Saved cleaned polygons to:", args.out)
    print("✅ Saved summary to:", summary_path)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()