from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import fiona


MAPBIOMAS_PATH = Path("data/interim/mapbiomas_10m_clips/mapbiomas_10m_brasilia_aoi_clip.tif")

FAVELA_PATH = Path("data/interim/polygons_clean/favelas_brasilia.gpkg")
FAVELA_LAYER: Optional[str] = None  # leave None unless you know the exact layer

OUT_DIR = Path("reports/qc/mapbiomas_10m")
OUT_AOI_CSV = OUT_DIR / "mapbiomas_10m_brasilia_aoi_class_histogram.csv"
OUT_FAVELA_CSV = OUT_DIR / "mapbiomas_10m_favela_polygon_class_histogram.csv"
OUT_VALUES_MD = OUT_DIR / "mapbiomas_10m_unique_values.md"

# Keep this mapping for now. If the 10 m product uses different codes,
# the unknown ones will still appear as "Unknown" and we can update later.
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


def load_favela_layer() -> gpd.GeoDataFrame:
    if not FAVELA_PATH.exists():
        raise FileNotFoundError(f"Favela polygon file not found: {FAVELA_PATH}")

    layer_name = FAVELA_LAYER if FAVELA_LAYER else pick_layer_name(FAVELA_PATH)
    print(f"Using favela file: {FAVELA_PATH}")
    print(f"Using favela layer: {layer_name}")

    if layer_name is not None:
        gdf = gpd.read_file(FAVELA_PATH, layer=layer_name)
    else:
        gdf = gpd.read_file(FAVELA_PATH)

    if gdf.empty:
        raise ValueError("Favela polygon layer is empty.")

    if "geometry" not in gdf.columns:
        raise ValueError("Favela layer has no geometry column.")

    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty].copy()

    if gdf.empty:
        raise ValueError("No valid favela geometries found.")

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


def write_markdown_summary(
    out_path: Path,
    raster_path: Path,
    nodata,
    aoi_df: pd.DataFrame,
    favela_df: pd.DataFrame,
) -> None:
    unique_values = sorted(aoi_df["class_value"].tolist()) if not aoi_df.empty else []
    favela_values = sorted(favela_df["class_value"].tolist()) if not favela_df.empty else []

    lines = [
        "# MapBiomas 10 m unique values summary",
        "",
        f"- Input raster: `{raster_path.as_posix()}`",
        f"- Favela polygons: `{FAVELA_PATH.as_posix()}`",
        f"- Nodata: `{nodata}`",
        "",
        "## Unique values in Brasília AOI clip",
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
def summarize_masked_values(arr: np.ma.MaskedArray) -> pd.DataFrame:
    """Compute unique values, counts, and percentages from a masked array."""
    flat = arr.compressed()  # keeps only unmasked pixels

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

def main():
    if not MAPBIOMAS_PATH.exists():
        raise FileNotFoundError(f"MapBiomas 10 m clip not found: {MAPBIOMAS_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(MAPBIOMAS_PATH) as src:
        arr = src.read(1)
        nodata = src.nodata

        # AOI-wide histogram
        aoi_df = summarize_values(arr, nodata)
        aoi_df.to_csv(OUT_AOI_CSV, index=False)

        # Favela-only histogram
        favela_gdf = load_favela_layer()

        if favela_gdf.crs is None:
            raise ValueError("Favela layer has no CRS.")

        if favela_gdf.crs != src.crs:
            favela_gdf = favela_gdf.to_crs(src.crs)

        geoms = [g for g in favela_gdf.geometry if g is not None and not g.is_empty]
        if not geoms:
            raise ValueError("No valid favela geometries available for masking.")

        favela_arr, _ = mask(
            src,
            geoms,
            crop=False,
            filled=False
        )

        favela_df = summarize_masked_values(favela_arr[0])
        favela_df.to_csv(OUT_FAVELA_CSV, index=False)

        write_markdown_summary(
            out_path=OUT_VALUES_MD,
            raster_path=MAPBIOMAS_PATH,
            nodata=nodata,
            aoi_df=aoi_df,
            favela_df=favela_df,
        )

    print(f"Saved: {OUT_AOI_CSV}")
    print(f"Saved: {OUT_FAVELA_CSV}")
    print(f"Saved: {OUT_VALUES_MD}")


if __name__ == "__main__":
    main()