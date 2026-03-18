from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.lines import Line2D
from rasterio.plot import show


CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
]

AOI_ROOT = Path("data/interim/aoi")
RASTER_ROOT = Path("data/interim/mapbiomas_10m_clips")
POLY_ROOT = Path("data/processed/polygons")
OUT_ROOT = Path("reports/qc/mapbiomas_10m/batch1/figures")


CLASS_COLORS = {
    0: "#000000",
    3: "#1b5e20",
    4: "#66bb6a",
    5: "#2e7d32",
    6: "#388e3c",
    11: "#26a69a",
    12: "#9ccc65",
    15: "#c0ca33",
    21: "#d4a373",
    24: "#d32f2f",
    25: "#8d6e63",
    33: "#42a5f5",
    49: "#81c784",
    50: "#aed581",
}
DEFAULT_COLOR = "#bdbdbd"


def mapbiomas_to_rgb(arr: np.ndarray) -> np.ndarray:
    rgb = np.zeros((arr.shape[0], arr.shape[1], 3), dtype=np.uint8)
    for val in np.unique(arr):
        color = CLASS_COLORS.get(int(val), DEFAULT_COLOR).lstrip("#")
        rgb[arr == val] = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    return rgb


def plot_city(city: str) -> None:
    raster_path = RASTER_ROOT / city / f"mapbiomas_10m_{city}_aoi_clip.tif"
    orig_path = AOI_ROOT / city / f"favelas_{city}.gpkg"
    raw_path = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_raw.gpkg"
    dissolved_path = POLY_ROOT / city / f"{city}_favela_refined_mapbiomas_10m_no_ring_v2_1_keep_uncertain_dissolved.gpkg"

    out_city_dir = OUT_ROOT / city
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

    print(f"\n=== {city} ===")
    print(f"Saved: {out_dissolved}")
    print(f"Saved: {out_raw}")


def main():
    for city in CITIES:
        plot_city(city)
    print("\nDone.")


if __name__ == "__main__":
    main()