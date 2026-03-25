from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask


AOI_ROOT = Path("data/interim/aoi")
RASTER_ROOT = Path("data/interim/mapbiomas_10m_clips")
OUT_ROOT = Path("reports/qc/mapbiomas_10m")

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
    "belo_horizonte",
    "salvador",
    "manaus",
]

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


def inspect_one_city(city: str) -> None:
    raster_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    favela_path = AOI_ROOT / city / f"favelas_{city}.gpkg"
    out_dir = OUT_ROOT / city

    out_aoi_csv = out_dir / f"{city}_aoi_class_histogram.csv"
    out_favela_csv = out_dir / f"{city}_favela_polygon_class_histogram.csv"
    out_values_md = out_dir / f"{city}_unique_values.md"

    if not raster_path.exists():
        raise FileNotFoundError(f"Raster clip not found for {city}: {raster_path}")
    if not favela_path.exists():
        raise FileNotFoundError(f"Favela file not found for {city}: {favela_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {city} ===")
    print(f"Raster:  {raster_path}")
    print(f"Favelas: {favela_path}")

    with rasterio.open(raster_path) as src:
        arr = src.read(1)
        nodata = src.nodata

        aoi_df = summarize_values(arr, nodata)
        aoi_df.to_csv(out_aoi_csv, index=False)

        favela_gdf = gpd.read_file(favela_path)

        if favela_gdf.empty:
            raise ValueError(f"Favela layer is empty for city: {city}")

        if favela_gdf.crs is None:
            raise ValueError(f"Favela layer has no CRS for city: {city}")

        if favela_gdf.crs != src.crs:
            favela_gdf = favela_gdf.to_crs(src.crs)

        geoms = [g for g in favela_gdf.geometry if g is not None and not g.is_empty]
        if not geoms:
            raise ValueError(f"No valid favela geometries for city: {city}")

        favela_arr, _ = mask(
            src,
            geoms,
            crop=False,
            filled=False
        )

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

    print(f"Saved: {out_aoi_csv}")
    print(f"Saved: {out_favela_csv}")
    print(f"Saved: {out_values_md}")


def main():
    for city in CITIES:
        inspect_one_city(city)

    print("\nDone.")


if __name__ == "__main__":
    main()