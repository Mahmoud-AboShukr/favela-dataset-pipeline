from pathlib import Path
import zipfile

# Resolve paths relative to the repository root
REPO_ROOT = Path(__file__).resolve().parents[3]
INPUT_DIR = REPO_ROOT / "data" / "raw" / "ghsl" / "brazil"
OUTPUT_DIR = REPO_ROOT / "data" / "raw" / "ghsl" / "brazil_unzipped"

def main():
    print("=" * 80)
    print("UNZIP GHSL BRAZIL")
    print("=" * 80)
    print(f"Script location : {Path(__file__).resolve()}")
    print(f"Repo root       : {REPO_ROOT}")
    print(f"Input folder    : {INPUT_DIR}")
    print(f"Output folder   : {OUTPUT_DIR}")
    print()

    if not INPUT_DIR.exists():
        print(f"ERROR: input folder does not exist:\n{INPUT_DIR}")
        return

    zip_files = sorted(INPUT_DIR.glob("*.zip"))
    print(f"Found {len(zip_files)} zip files in input folder.\n")

    if not zip_files:
        print("No zip files found. Check that the files are really in data/raw/ghsl/brazil/")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    extracted = 0
    skipped = 0
    failed = 0

    for zip_path in zip_files:
        out_subdir = OUTPUT_DIR / zip_path.stem

        if out_subdir.exists() and any(out_subdir.iterdir()):
            print(f"SKIP  | {zip_path.name} -> already extracted")
            skipped += 1
            continue

        out_subdir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(out_subdir)
            print(f"UNZIP | {zip_path.name} -> {out_subdir}")
            extracted += 1
        except Exception as e:
            print(f"FAIL  | {zip_path.name} -> {e}")
            failed += 1

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total zip files: {len(zip_files)}")
    print(f"Extracted      : {extracted}")
    print(f"Skipped        : {skipped}")
    print(f"Failed         : {failed}")

if __name__ == "__main__":
    main()