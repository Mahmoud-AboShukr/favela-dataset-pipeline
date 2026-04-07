from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Download just one experiment month first
INPUT_MONTH_CSV = Path(
    "data/experiments/sentinel2_cloud/manaus/monthly_scene_lists/2022_08.csv"
)

OUT_DIR = Path("data/experiments/sentinel2_cloud/manaus/inputs/s2_products/2022_08")
REPORT_CSV = OUT_DIR / "download_report_2022_08.csv"

# Official CDSE endpoints
ODATA_PRODUCTS_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
DOWNLOAD_BASE_URL = "https://download.dataspace.copernicus.eu/odata/v1/Products"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

CLIENT_ID_ENV = "CDSE_CLIENT_ID"
CLIENT_SECRET_ENV = "CDSE_CLIENT_SECRET"

REQUEST_TIMEOUT = 120
CHUNK_SIZE = 1024 * 1024  # 1 MB

# Safety limit for the first run
# Set to None after the first successful test if you want the full month
MAX_DOWNLOADS: int | None = 3


# -----------------------------------------------------------------------------
# Auth
# -----------------------------------------------------------------------------

def get_oauth_session() -> OAuth2Session:
    client_id = os.getenv(CLIENT_ID_ENV)
    client_secret = os.getenv(CLIENT_SECRET_ENV)

    if not client_id or not client_secret:
        raise RuntimeError(
            f"Missing credentials. Please set {CLIENT_ID_ENV} and {CLIENT_SECRET_ENV}."
        )

    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)

    oauth.fetch_token(
        token_url=TOKEN_URL,
        client_secret=client_secret,
        include_client_id=True,
    )
    return oauth


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def escape_odata_string(value: str) -> str:
    return value.replace("'", "''")


def strip_safe_suffix(name: str) -> str:
    # STAC ids usually do not end with .SAFE, OData product Name usually does.
    return name[:-5] if name.endswith(".SAFE") else name


def resolve_product_by_scene_name(scene_name: str, session: requests.Session) -> dict[str, Any] | None:
    """
    Resolve a STAC scene id to an OData product by querying Name eq '<scene>.SAFE'
    and falling back to Name eq '<scene>'.
    """
    candidates = [f"{strip_safe_suffix(scene_name)}.SAFE", strip_safe_suffix(scene_name)]

    for candidate in candidates:
        safe_name = escape_odata_string(candidate)
        params = {
            "$filter": f"Name eq '{safe_name}'",
            "$top": 2,
            "$select": "Id,Name,Online,ContentLength,S3Path",
        }

        response = session.get(ODATA_PRODUCTS_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        payload = response.json()
        values = payload.get("value", [])
        if values:
            return values[0]

    return None


def download_product(product_id: str, out_path: Path, session: requests.Session) -> tuple[bool, str]:
    """
    Download product archive using the official OData product download endpoint.
    """
    url = f"{DOWNLOAD_BASE_URL}({product_id})/$value"

    with session.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        if response.status_code != 200:
            try:
                msg = response.text[:500]
            except Exception:
                msg = f"HTTP {response.status_code}"
            return False, msg

        with open(out_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

    return True, "downloaded"


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:
    print("=" * 80)
    print("DOWNLOAD SENTINEL-2 PRODUCTS FOR ONE EXPERIMENT MONTH")
    print("=" * 80)

    if not INPUT_MONTH_CSV.exists():
        raise FileNotFoundError(f"Input month CSV not found: {INPUT_MONTH_CSV}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_MONTH_CSV)
    if "id" not in df.columns:
        raise ValueError("Expected an 'id' column in the input CSV.")

    scene_names = df["id"].dropna().astype(str).tolist()

    if MAX_DOWNLOADS is not None:
        scene_names = scene_names[:MAX_DOWNLOADS]

    print(f"\nScenes to process: {len(scene_names)}")
    print(f"Output folder: {OUT_DIR}")

    print("\nRequesting OAuth token...")
    session = get_oauth_session()
    print("Token acquired.")

    report_rows: list[dict[str, Any]] = []

    for idx, scene_name in enumerate(scene_names, start=1):
        print("-" * 80)
        print(f"[{idx}/{len(scene_names)}] Resolving: {scene_name}")

        row: dict[str, Any] = {
            "scene_name": scene_name,
            "product_name": None,
            "product_id": None,
            "online": None,
            "content_length": None,
            "s3_path": None,
            "output_file": None,
            "status": None,
            "message": None,
        }

        try:
            product = resolve_product_by_scene_name(scene_name, session)

            if product is None:
                row["status"] = "not_found"
                row["message"] = "No matching OData product found"
                report_rows.append(row)
                print("  -> Not found in OData")
                continue

            product_id = product.get("Id")
            product_name = product.get("Name")
            online = product.get("Online")
            content_length = product.get("ContentLength")
            s3_path = product.get("S3Path")

            row["product_name"] = product_name
            row["product_id"] = product_id
            row["online"] = online
            row["content_length"] = content_length
            row["s3_path"] = s3_path

            if not product_id:
                row["status"] = "missing_product_id"
                row["message"] = "OData match returned no product Id"
                report_rows.append(row)
                print("  -> Missing product Id")
                continue

            if online is False:
                row["status"] = "offline"
                row["message"] = "Product offline"
                report_rows.append(row)
                print("  -> Offline, skipped")
                continue

            out_name = product_name if str(product_name).endswith(".SAFE") else f"{product_name}.zip"
            if not out_name.endswith(".zip") and not out_name.endswith(".SAFE"):
                out_name = f"{out_name}.zip"

            # Always download as zip-like file container
            if out_name.endswith(".SAFE"):
                out_name = out_name + ".zip"

            out_path = OUT_DIR / out_name
            row["output_file"] = str(out_path)

            if out_path.exists():
                row["status"] = "exists"
                row["message"] = "Already downloaded"
                report_rows.append(row)
                print("  -> Already exists, skipped")
                continue

            print(f"  -> Downloading to: {out_path.name}")
            ok, msg = download_product(product_id, out_path, session)

            row["status"] = "downloaded" if ok else "failed"
            row["message"] = msg
            report_rows.append(row)

            print(f"  -> {row['status']}: {msg}")
            time.sleep(1)

        except Exception as e:
            row["status"] = "error"
            row["message"] = str(e)
            report_rows.append(row)
            print(f"  -> error: {e}")

    report_df = pd.DataFrame(report_rows)
    report_df.to_csv(REPORT_CSV, index=False)

    print("\nSaved report:")
    print(f"  {REPORT_CSV}")

    if not report_df.empty and "status" in report_df.columns:
        print("\nStatus counts:")
        print(report_df["status"].value_counts(dropna=False).to_string())

    print("\nDone.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)