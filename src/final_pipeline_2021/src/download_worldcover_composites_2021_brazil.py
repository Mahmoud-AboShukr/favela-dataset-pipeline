from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import geopandas as gpd
import requests
from tqdm import tqdm


from pathlib import Path

def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "data").exists() and (candidate / "src").exists():
            return candidate
    raise RuntimeError("Could not locate repo root containing both 'data' and 'src' folders.")

REPO_ROOT = find_repo_root(Path(__file__).parent)

DEFAULT_BRAZIL_BOUNDARY = (
    REPO_ROOT / "data" / "raw" / "ibge" / "BR_Municipios_2024" / "BR_Municipios_2024.shp"
)
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "raw" / "worldcover_composites_2021_brazil"

GRID_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/esa_worldcover_grid_composites.fgb"
HTTP_TIMEOUT = 120


def log(msg: str) -> None:
    print(msg, flush=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download ESA WorldCover 2021 Sentinel-1 / Sentinel-2 annual composites for Brazil."
    )
    parser.add_argument(
        "--brazil-boundary",
        type=Path,
        default=DEFAULT_BRAZIL_BOUNDARY,
        help="Path to Brazil boundary shapefile/GPKG.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Output folder.",
    )
    parser.add_argument(
        "--products",
        nargs="+",
        default=["s1", "s2_tcc"],
        choices=["s1", "s2_tcc", "s2_swir", "s2_ndvi"],
        help=(
            "Products to download. "
            "Default downloads Sentinel-1 annual composite and Sentinel-2 true-color/RGBNIR composite."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list files that would be downloaded.",
    )
    return parser.parse_args()


def load_brazil_geometry(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Brazil boundary not found: {path}")

    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError(f"Boundary file is empty: {path}")
    if gdf.crs is None:
        raise ValueError(f"Boundary file has no CRS: {path}")

    gdf = gdf.to_crs("EPSG:4326")
    geom = gdf.union_all()
    return geom


def load_grid() -> gpd.GeoDataFrame:
    log(f"[LOAD] Reading product grid: {GRID_URL}")
    grid = gpd.read_file(GRID_URL)
    if grid.empty:
        raise ValueError("WorldCover composites grid is empty.")
    if grid.crs is None:
        raise ValueError("WorldCover composites grid has no CRS.")
    grid = grid.to_crs("EPSG:4326")
    return grid


def discover_candidate_columns(grid: gpd.GeoDataFrame) -> list[str]:
    cols: list[str] = []
    for col in grid.columns:
        if col == "geometry":
            continue
        series = grid[col].dropna()
        if series.empty:
            continue
        text = " ".join(series.astype(str).head(50).tolist()).lower()
        if (
            "esa-worldcover-s1" in text
            or "esa-worldcover-s2" in text
            or ".tif" in text
            or "s3://" in text
            or "http://" in text
            or "https://" in text
        ):
            cols.append(col)
    return cols


def row_has_year_2021(row) -> bool:
    for val in row:
        if val is None:
            continue
        sval = str(val).strip()
        if sval == "2021":
            return True
    return False


def classify_product(text: str) -> str | None:
    t = text.upper()

    if "2021" not in t:
        return None

    if "ESA-WORLDCOVER-S1" in t or "GAMMA0" in t or "_S1_" in t:
        return "s1"

    if "ESA-WORLDCOVER-S2" in t or "_S2_" in t:
        if "SWIR" in t or "B11" in t or "B12" in t:
            return "s2_swir"
        if "NDVI" in t:
            return "s2_ndvi"
        if "TCC" in t or "RGBNIR" in t or "B02" in t or "B03" in t or "B04" in t or "B08" in t:
            return "s2_tcc"

    return None


def s3_to_https(url: str) -> str:
    if not url.startswith("s3://"):
        return url

    parsed = urlparse(url)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return f"https://{bucket}.s3.eu-central-1.amazonaws.com/{key}"


def looks_like_downloadable_tif(text: str) -> bool:
    t = text.lower()
    return (".tif" in t or ".tiff" in t) and (
        t.startswith("s3://") or t.startswith("http://") or t.startswith("https://")
    )


def iter_candidate_urls(row, candidate_cols: Iterable[str]):
    for col in candidate_cols:
        val = row.get(col)
        if val is None:
            continue
        sval = str(val).strip()
        if not sval:
            continue
        if looks_like_downloadable_tif(sval):
            yield col, sval


def collect_downloads(
    grid_subset: gpd.GeoDataFrame,
    wanted_products: set[str],
) -> list[dict]:
    candidate_cols = discover_candidate_columns(grid_subset)
    log(f"[INFO] Candidate URL/path columns: {candidate_cols}")

    rows: list[dict] = []
    seen: set[str] = set()

    for _, row in grid_subset.iterrows():
        row_year_ok = row_has_year_2021(row)

        for source_col, raw_url in iter_candidate_urls(row, candidate_cols):
            product = classify_product(raw_url)

            if product is None and row_year_ok:
                upper = raw_url.upper()
                if "ESA-WORLDCOVER-S1" in upper:
                    product = "s1"
                elif "ESA-WORLDCOVER-S2" in upper and "SWIR" in upper:
                    product = "s2_swir"
                elif "ESA-WORLDCOVER-S2" in upper and "NDVI" in upper:
                    product = "s2_ndvi"
                elif "ESA-WORLDCOVER-S2" in upper:
                    product = "s2_tcc"

            if product is None or product not in wanted_products:
                continue

            http_url = s3_to_https(raw_url)

            if http_url in seen:
                continue
            seen.add(http_url)

            filename = Path(urlparse(http_url).path).name
            rows.append(
                {
                    "product": product,
                    "source_column": source_col,
                    "url": http_url,
                    "filename": filename,
                }
            )

    rows = sorted(rows, key=lambda x: (x["product"], x["filename"]))
    return rows


def download_file(url: str, out_path: Path, overwrite: bool) -> None:
    if out_path.exists() and not overwrite:
        return

    ensure_dir(out_path.parent)
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")

    with requests.get(url, stream=True, timeout=HTTP_TIMEOUT) as r:
        r.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    tmp_path.replace(out_path)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_root)

    log("[STEP] Loading Brazil boundary...")
    brazil_geom = load_brazil_geometry(args.brazil_boundary)

    log("[STEP] Loading WorldCover composites grid...")
    grid = load_grid()

    log("[STEP] Intersecting grid with Brazil...")
    grid_subset = grid[grid.intersects(brazil_geom)].copy()
    if grid_subset.empty:
        raise RuntimeError("No WorldCover composite tiles intersect Brazil.")

    log(f"[INFO] Intersecting 1x1-degree tiles: {len(grid_subset)}")

    wanted_products = set(args.products)

    log("[STEP] Collecting 2021 S1/S2 download URLs...")
    downloads = collect_downloads(grid_subset, wanted_products=wanted_products)

    if not downloads:
        raise RuntimeError(
            "No matching downloads found. "
            "Inspect the grid columns and adjust the product detection rules if needed."
        )

    manifest_path = args.output_root / "download_manifest_2021_brazil.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(downloads, f, indent=2)

    by_product: dict[str, int] = {}
    for item in downloads:
        by_product[item["product"]] = by_product.get(item["product"], 0) + 1

    log(f"[INFO] Products requested: {sorted(wanted_products)}")
    log(f"[INFO] Download counts by product: {by_product}")
    log(f"[INFO] Manifest written to: {manifest_path}")

    if args.dry_run:
        log("[DRY RUN] No files downloaded.")
        return

    log("[STEP] Downloading files...")
    for item in tqdm(downloads, desc="Downloading", unit="file"):
        product_dir = args.output_root / item["product"]
        out_path = product_dir / item["filename"]
        download_file(item["url"], out_path, overwrite=args.overwrite)

    log("[DONE] Download complete.")


if __name__ == "__main__":
    main()