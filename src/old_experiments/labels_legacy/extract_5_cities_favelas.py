from pathlib import Path
import geopandas as gpd
import pandas as pd

# Input: cleaned national favela polygons
FAVELAS_INPUT = Path("data/interim/polygons_clean/favelas_clean.gpkg")

# AOI root
AOI_ROOT = Path("data/interim/aoi")

# Output summary table
SUMMARY_OUT = Path("reports/qc/mapbiomas_10m/city_favela_subset_summary.csv")

CITIES = [
    "rio_de_janeiro",
    "sao_paulo",
    "belo_horizonte",
    "salvador",
    "manaus",
]


def main():
    if not FAVELAS_INPUT.exists():
        raise FileNotFoundError(f"Favela layer not found: {FAVELAS_INPUT}")

    print(f"Reading favela layer: {FAVELAS_INPUT}")
    favelas = gpd.read_file(FAVELAS_INPUT)

    print("Favela CRS:", favelas.crs)
    print("Favela polygons:", len(favelas))

    summary_rows = []

    for city in CITIES:
        aoi_path = AOI_ROOT / city / f"{city}_aoi.gpkg"
        out_path = AOI_ROOT / city / f"favelas_{city}.gpkg"

        if not aoi_path.exists():
            raise FileNotFoundError(f"AOI not found for {city}: {aoi_path}")

        aoi = gpd.read_file(aoi_path)

        # Reproject favela layer if needed to match AOI CRS
        if favelas.crs != aoi.crs:
            favelas_city_crs = favelas.to_crs(aoi.crs)
        else:
            favelas_city_crs = favelas.copy()

        aoi_union = aoi.union_all()

        intersects_mask = favelas_city_crs.intersects(aoi_union)
        within_mask = favelas_city_crs.within(aoi_union)

        subset = favelas_city_crs[intersects_mask].copy()

        total_intersecting = int(intersects_mask.sum())
        fully_inside = int(within_mask.sum())
        boundary_crossing = total_intersecting - fully_inside

        if subset.empty:
            print(f"[WARNING] No favela polygons intersect AOI for {city}")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        subset.to_file(out_path, driver="GPKG")

        print(f"\nSaved {city}: {out_path}")
        print(f"  total intersecting: {total_intersecting}")
        print(f"  fully inside:       {fully_inside}")
        print(f"  boundary crossing:  {boundary_crossing}")

        summary_rows.append(
            {
                "city": city,
                "aoi_file": str(aoi_path),
                "favela_subset_file": str(out_path),
                "total_intersecting": total_intersecting,
                "fully_inside": fully_inside,
                "boundary_crossing": boundary_crossing,
                "crs": str(aoi.crs),
            }
        )

    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary_rows).to_csv(SUMMARY_OUT, index=False)
    print(f"\nSaved summary table: {SUMMARY_OUT}")


if __name__ == "__main__":
    main()