from pathlib import Path
import shutil

SRC = Path(r"data/raw/worldcover/brazil")
DST = Path(r"data/raw/worldcover/brazil_map_tiles")

DST.mkdir(parents=True, exist_ok=True)

files = sorted(SRC.rglob("*_Map.tif"))

count = 0
for f in files:
    dst = DST / f.name
    if not dst.exists():
        shutil.copy2(f, dst)
        print(f"COPY | {f} -> {dst}")
        count += 1

print(f"\nDone. Copied {count} map tiles to {DST}")