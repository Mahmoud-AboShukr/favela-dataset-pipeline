#!/usr/bin/env python3
"""
Download WSF files listed inside a .meta4 Metalink file using normal HTTP requests.

This avoids aria2 range-header issues and large pre-allocation.

Usage:
    python src/final_pipeline/utils/download_wsf_from_meta4.py ^
        --meta4 south_america_wsf.meta4 ^
        --out-dir data/raw/wsf ^
        --max-files 20
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests


def parse_meta4(meta4_path: Path) -> list[str]:
    tree = ET.parse(meta4_path)
    root = tree.getroot()

    urls = []
    for elem in root.iter():
        tag = elem.tag.lower()
        if tag.endswith("url") and elem.text:
            urls.append(elem.text.strip())

    return urls


def filename_from_url(url: str) -> str:
    path = urlparse(url).path
    return os.path.basename(path)


def download_file(url: str, out_path: Path, chunk_size: int = 1024 * 1024) -> bool:
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")

    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()

            total = r.headers.get("Content-Length")
            total_mb = f"{int(total) / (1024 * 1024):.2f} MB" if total else "unknown size"

            print(f"Downloading: {out_path.name} ({total_mb})")

            with open(tmp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

        tmp_path.replace(out_path)
        print(f"Saved: {out_path}")
        return True

    except Exception as e:
        print(f"FAILED: {url}")
        print(f"Reason: {e}")
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta4", required=True, type=Path, help="Path to .meta4 file")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory")
    parser.add_argument("--max-files", type=int, default=None, help="Optional limit for testing")
    parser.add_argument("--sleep", type=float, default=0.5, help="Pause between files")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    urls = parse_meta4(args.meta4)
    if not urls:
        print("No URLs found in meta4 file.")
        sys.exit(1)

    print(f"Found {len(urls)} URLs in {args.meta4}")

    if args.max_files is not None:
        urls = urls[:args.max_files]
        print(f"Limiting to first {len(urls)} files")

    ok = 0
    fail = 0
    skip = 0

    for i, url in enumerate(urls, start=1):
        fname = filename_from_url(url)
        out_path = args.out_dir / fname

        print(f"\n[{i}/{len(urls)}] {fname}")

        if out_path.exists() and out_path.stat().st_size > 0:
            print("Already exists, skipping.")
            skip += 1
            continue

        success = download_file(url, out_path)
        if success:
            ok += 1
        else:
            fail += 1

        time.sleep(args.sleep)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Downloaded successfully: {ok}")
    print(f"Failed: {fail}")
    print(f"Skipped existing: {skip}")


if __name__ == "__main__":
    main()