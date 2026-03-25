from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIG
# =============================================================================

# Start with True. Review the plan/output first.
DRY_RUN = False

# If False, script will refuse to overwrite existing destinations.
OVERWRITE = False

# If True, also move root-level temporary logs / tree files to old_experiments_data/logs
MOVE_TEMP_LOGS = True

REPO_ROOT = Path(".").resolve()
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = LOG_DIR / f"tidy_project_archive_{TIMESTAMP}.log"


# =============================================================================
# MOVE PLAN
# =============================================================================

@dataclass
class MoveItem:
    src: str
    dst: str
    reason: str


MOVE_PLAN = [
    # -------------------------------------------------------------------------
    # CODE: old top-level active/pilot pipelines -> archive
    # -------------------------------------------------------------------------
    MoveItem(
        src="src/final_pipeline",
        dst="src/old_experiments/final_pipeline_manaus",
        reason="Older pre-scale-up final pipeline / Manaus-oriented workflow",
    ),
    MoveItem(
        src="src/ghsl",
        dst="src/old_experiments/ghsl_brasilia",
        reason="Older GHSL-focused Brasília pipeline/helpers",
    ),
    MoveItem(
        src="src/labels",
        dst="src/old_experiments/labels_legacy",
        reason="Legacy label scripts from earlier experiments",
    ),
    MoveItem(
        src="src/mapbiomas",
        dst="src/old_experiments/mapbiomas_helpers",
        reason="Older MapBiomas helper code outside current main pipeline",
    ),

    # -------------------------------------------------------------------------
    # CODE: explicit experiments tree -> archive under old_experiments/experiments
    # -------------------------------------------------------------------------
    MoveItem(
        src="src/experiments/ghsl",
        dst="src/old_experiments/experiments/ghsl",
        reason="Archived GHSL experiments",
    ),
    MoveItem(
        src="src/experiments/mapbiomas_10m_brasilia",
        dst="src/old_experiments/experiments/mapbiomas_10m_brasilia",
        reason="Archived Brasília MapBiomas 10 m experiments",
    ),
    MoveItem(
        src="src/experiments/mapbiomas_10m_multicity",
        dst="src/old_experiments/experiments/mapbiomas_10m_multicity",
        reason="Archived multi-city MapBiomas 10 m experiments",
    ),
    MoveItem(
        src="src/experiments/mapbiomas_30m",
        dst="src/old_experiments/experiments/mapbiomas_30m",
        reason="Archived MapBiomas 30 m experiments",
    ),

    # -------------------------------------------------------------------------
    # DATA: archive older interim experiment outputs
    # -------------------------------------------------------------------------
    MoveItem(
        src="data/interim/aoi",
        dst="data/old_experiments_data/interim/aoi",
        reason="Older city/pilot AOI files",
    ),
    MoveItem(
        src="data/interim/ghsl",
        dst="data/old_experiments_data/interim/ghsl",
        reason="Older GHSL interim outputs",
    ),
    MoveItem(
        src="data/interim/ghsl_clips",
        dst="data/old_experiments_data/interim/ghsl_clips",
        reason="Older GHSL clipping outputs",
    ),
    MoveItem(
        src="data/interim/mapbiomas_10m",
        dst="data/old_experiments_data/interim/mapbiomas_10m",
        reason="Older MapBiomas 10 m interim outputs",
    ),
    MoveItem(
        src="data/interim/mapbiomas_10m_clips",
        dst="data/old_experiments_data/interim/mapbiomas_10m_clips",
        reason="Older MapBiomas 10 m clipped outputs",
    ),
    MoveItem(
        src="data/interim/mapbiomas_30m",
        dst="data/old_experiments_data/interim/mapbiomas_30m",
        reason="Older MapBiomas 30 m interim outputs",
    ),
    MoveItem(
        src="data/interim/mapbiomas_clips",
        dst="data/old_experiments_data/interim/mapbiomas_clips",
        reason="Older MapBiomas clip outputs",
    ),
    MoveItem(
        src="data/interim/masks",
        dst="data/old_experiments_data/interim/masks",
        reason="Older mask outputs from experiments",
    ),
    MoveItem(
        src="data/interim/refined_labels_mapbiomas",
        dst="data/old_experiments_data/interim/refined_labels_mapbiomas",
        reason="Older refined labels from MapBiomas pipeline",
    ),
    MoveItem(
        src="data/interim/refined_labels_mapbiomas_10m",
        dst="data/old_experiments_data/interim/refined_labels_mapbiomas_10m",
        reason="Older refined labels from MapBiomas 10 m pipeline",
    ),
    MoveItem(
        src="data/interim/temporal_change",
        dst="data/old_experiments_data/interim/temporal_change",
        reason="Older temporal-change experiment data",
    ),

    # -------------------------------------------------------------------------
    # DATA: older processed outputs -> archive
    # -------------------------------------------------------------------------
    MoveItem(
        src="data/processed/final_pipeline",
        dst="data/old_experiments_data/processed/final_pipeline",
        reason="Older final_pipeline outputs before scale-up",
    ),
]

TEMP_ITEMS = [
    MoveItem(
        src="cache",
        dst="data/old_experiments_data/logs/cache",
        reason="Temporary cache",
    ),
    MoveItem(
        src="data_raw_tree.txt",
        dst="data/old_experiments_data/logs/data_raw_tree.txt",
        reason="Temporary tree output",
    ),
    MoveItem(
        src="prepared_output_tree.txt",
        dst="data/old_experiments_data/logs/prepared_output_tree.txt",
        reason="Temporary tree output",
    ),
    MoveItem(
        src="prepare_all_brazil_log.txt",
        dst="data/old_experiments_data/logs/prepare_all_brazil_log.txt",
        reason="Temporary pipeline run log",
    ),
    MoveItem(
        src="refine_all_brazil_log.txt",
        dst="data/old_experiments_data/logs/refine_all_brazil_log.txt",
        reason="Temporary pipeline run log",
    ),
    MoveItem(
        src="polygonize_all_brazil_log.txt",
        dst="data/old_experiments_data/logs/polygonize_all_brazil_log.txt",
        reason="Temporary pipeline run log",
    ),
    MoveItem(
        src="project_tree.txt",
        dst="data/old_experiments_data/logs/project_tree.txt",
        reason="Temporary project tree export",
    ),
]

if MOVE_TEMP_LOGS:
    MOVE_PLAN += TEMP_ITEMS


# =============================================================================
# HELPERS
# =============================================================================

def write_log(message: str) -> None:
    print(message, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def exists_any(path: Path) -> bool:
    return path.exists()


def move_path(src: Path, dst: Path, overwrite: bool) -> None:
    if not src.exists():
        write_log(f"[SKIP] Missing: {src}")
        return

    if dst.exists():
        if not overwrite:
            write_log(f"[SKIP] Destination exists: {dst}")
            return

        write_log(f"[REMOVE] Existing destination: {dst}")
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()

    ensure_parent(dst)
    shutil.move(str(src), str(dst))
    write_log(f"[MOVED] {src} -> {dst}")


def validate_main_pipeline_paths() -> None:
    critical_paths = [
        REPO_ROOT / "src/final_pipeline_scale_up",
        REPO_ROOT / "data/processed/final_pipeline_scale_up",
        REPO_ROOT / "data/raw",
    ]

    for p in critical_paths:
        if not p.exists():
            write_log(f"[WARN] Expected active path not found: {p}")
        else:
            write_log(f"[OK] Active path preserved: {p}")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    write_log("=" * 80)
    write_log("PROJECT TIDY / ARCHIVE SCRIPT")
    write_log("=" * 80)
    write_log(f"Repo root : {REPO_ROOT}")
    write_log(f"Dry run   : {DRY_RUN}")
    write_log(f"Overwrite : {OVERWRITE}")
    write_log(f"Log file  : {LOG_PATH}")
    write_log("")

    validate_main_pipeline_paths()
    write_log("")

    write_log("Planned moves:")
    for item in MOVE_PLAN:
        write_log(f"  - {item.src} -> {item.dst}")
        write_log(f"    reason: {item.reason}")
    write_log("")

    if DRY_RUN:
        write_log("[INFO] Dry run only. No files were moved.")
        return

    for item in MOVE_PLAN:
        src = REPO_ROOT / item.src
        dst = REPO_ROOT / item.dst
        write_log("-" * 80)
        write_log(f"[ACTION] {item.reason}")
        move_path(src, dst, overwrite=OVERWRITE)

    write_log("")
    write_log("[DONE] Archive cleanup completed.")


if __name__ == "__main__":
    main()
