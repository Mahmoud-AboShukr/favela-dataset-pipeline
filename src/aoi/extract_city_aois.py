from pathlib import Path
import geopandas as gpd

# ============================================================
# INPUT: exact path to the downloaded IBGE shapefile
# IMPORTANT: replace the .shp filename below with the real one
# found inside data/raw/ibge/BR_Municipios_2024/
# ============================================================
INPUT = Path(r"data/raw/ibge/BR_Municipios_2024/BR_Municipios_2024.shp")

# Output root
AOI_ROOT = Path("data/interim/aoi")

# Target cities and IBGE municipality codes
TARGETS = {
    "rio_de_janeiro": "3304557",
    "sao_paulo": "3550308",
    "belo_horizonte": "3106200",
    "salvador": "2927408",
    "manaus": "1302603",
}

def main():
    print(f"Reading: {INPUT}")

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Input shapefile not found: {INPUT}\n"
            "Please check the .shp filename inside data/raw/ibge/BR_Municipios_2024/"
        )

    gdf = gpd.read_file(INPUT)

    print("\nColumns found:")
    print(list(gdf.columns))
    print("\nCRS:", gdf.crs)
    print("Rows:", len(gdf))

    # Try to detect municipality code column automatically
    candidate_code_cols = [
        "CD_MUN",
        "CD_GEOCMU",
        "GEOCODIGO",
        "codigo_ibge",
        "code_muni",
        "cod_municip",
    ]

    code_col = None
    for col in candidate_code_cols:
        if col in gdf.columns:
            code_col = col
            break

    if code_col is None:
        raise ValueError(
            "Could not find municipality code column automatically.\n"
            f"Available columns: {list(gdf.columns)}"
        )

    print("\nUsing municipality code column:", code_col)

    # Ensure output directories exist
    for city in TARGETS:
        (AOI_ROOT / city).mkdir(parents=True, exist_ok=True)

    # Extract and save each city AOI
    for city, code in TARGETS.items():
        aoi = gdf[gdf[code_col].astype(str) == code].copy()

        if aoi.empty:
            raise ValueError(f"No municipality found for {city} with code {code}")

        out_path = AOI_ROOT / city / f"{city}_aoi.gpkg"
        aoi.to_file(out_path, driver="GPKG")
        print(f"Saved {city}: {out_path}")

    print("\nDone.")

if __name__ == "__main__":
    main()