from pathlib import Path
import shutil
import zipfile

import geopandas as gpd
import rasterio
from shapely.geometry import box


# =============================================================================
# PATHS
# =============================================================================

GHSL_ZIP_DIR = Path("data/raw/ghsl/south_america")
NON_BRAZIL_DIR = Path("data/raw/ghsl_not_brazil")

# Adjust only if your IBGE path is different
BRAZIL_MUNICIPALITIES = Path("data/raw/ibge/BR_Municipios_2024/BR_Municipios_2024.shp")


# =============================================================================
# HELPERS
# =============================================================================

def load_brazil_polygon_from_municipalities(shp_path: Path) -> gpd.GeoDataFrame:
    """
    Load municipalities shapefile and dissolve it into one Brazil polygon.
    """
    if not shp_path.exists():
        raise FileNotFoundError(f"Brazil municipalities shapefile not found: {shp_path}")

    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        raise ValueError("Municipalities shapefile is empty.")

    if gdf.crs is None:
        raise ValueError("Municipalities shapefile has no CRS.")

    brazil = gdf.dissolve()
    brazil = brazil[["geometry"]].reset_index(drop=True)
    return brazil


def find_tif_inside_zip(zip_path: Path) -> str:
    """
    Return the internal path of the first .tif/.tiff file inside the zip.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        tif_members = [
            name for name in zf.namelist()
            if name.lower().endswith(".tif") or name.lower().endswith(".tiff")
        ]

    if not tif_members:
        raise ValueError(f"No .tif found inside zip: {zip_path}")

    if len(tif_members) > 1:
        print(f"WARNING | Multiple TIFFs in {zip_path.name}, using: {tif_members[0]}")

    return tif_members[0]


def get_raster_bbox_from_zip(zip_path: Path) -> gpd.GeoDataFrame:
    """
    Open the TIFF inside the zip using GDAL's /vsizip/ virtual path and
    return its bounding box as a GeoDataFrame in the raster CRS.
    """
    tif_inside_zip = find_tif_inside_zip(zip_path)

    vsi_path = f"/vsizip/{zip_path.resolve().as_posix()}/{tif_inside_zip}"

    with rasterio.open(vsi_path) as src:
        bounds = src.bounds
        crs = src.crs

    if crs is None:
        raise ValueError(f"Raster inside zip has no CRS: {zip_path}")

    geom = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
    return gpd.GeoDataFrame({"geometry": [geom]}, crs=crs)


def zip_intersects_brazil(zip_path: Path, brazil_gdf: gpd.GeoDataFrame) -> bool:
    """
    Check whether the raster tile inside the zip intersects Brazil.
    """
    tile_gdf = get_raster_bbox_from_zip(zip_path)
    brazil_in_tile_crs = brazil_gdf.to_crs(tile_gdf.crs)

    return tile_gdf.intersects(brazil_in_tile_crs.geometry.iloc[0]).iloc[0]


# =============================================================================
# MAIN
# =============================================================================

def main():
    if not GHSL_ZIP_DIR.exists():
        raise FileNotFoundError(f"GHSL zip directory not found: {GHSL_ZIP_DIR}")

    NON_BRAZIL_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading Brazil polygon from municipalities...")
    brazil = load_brazil_polygon_from_municipalities(BRAZIL_MUNICIPALITIES)

    zip_files = sorted(GHSL_ZIP_DIR.glob("*.zip"))
    if not zip_files:
        print(f"No .zip files found in {GHSL_ZIP_DIR}")
        return

    kept = 0
    moved = 0
    failed = 0

    for zip_path in zip_files:
        try:
            if zip_intersects_brazil(zip_path, brazil):
                print(f"KEEP  | {zip_path.name}")
                kept += 1
            else:
                dst = NON_BRAZIL_DIR / zip_path.name
                print(f"MOVE  | {zip_path.name} -> {dst}")
                shutil.move(str(zip_path), str(dst))
                moved += 1

        except Exception as e:
            print(f"ERROR | {zip_path.name} | {e}")
            failed += 1

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total zip tiles scanned: {len(zip_files)}")
    print(f"Kept (intersect Brazil): {kept}")
    print(f"Moved (not Brazil): {moved}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    main()