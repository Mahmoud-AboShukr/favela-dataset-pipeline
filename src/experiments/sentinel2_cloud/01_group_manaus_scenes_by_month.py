from __future__ import annotations

from pathlib import Path

import pandas as pd


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

INPUT_CSV = Path("data/interim/imagery/sentinel2/manaus/s2_2022_search_results.csv")
OUT_DIR = Path("data/experiments/sentinel2_cloud/manaus/monthly_scene_lists")

EXPECTED_YEAR = 2022

# Set True if you want a deduplicated monthly file by scene id
DROP_DUPLICATES_BY_ID = True


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def month_label(dt: pd.Timestamp) -> str:
    """Return a YYYY_MM label for a datetime."""
    return f"{dt.year}_{dt.month:02d}"


def ensure_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in input CSV: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:
    print("=" * 80)
    print("GROUP MANAUS SENTINEL-2 SCENES BY MONTH")
    print("=" * 80)

    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nReading: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)

    ensure_required_columns(df, ["id", "datetime"])

    print(f"Rows read: {len(df):,}")

    # Parse datetime
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")

    bad_dt = df["datetime"].isna().sum()
    if bad_dt > 0:
        print(f"Warning: {bad_dt} rows have invalid datetime and will be dropped.")
        df = df.dropna(subset=["datetime"]).copy()

    # Keep only the expected year, just to be safe
    df = df[df["datetime"].dt.year == EXPECTED_YEAR].copy()

    if df.empty:
        raise ValueError(f"No rows remain after filtering to year {EXPECTED_YEAR}.")

    # Optional deduplication
    if DROP_DUPLICATES_BY_ID:
        before = len(df)
        df = df.drop_duplicates(subset=["id"]).copy()
        after = len(df)
        print(f"Dropped duplicate ids: {before - after}")

    # Add useful columns
    df["year"] = df["datetime"].dt.year
    df["month"] = df["datetime"].dt.month
    df["month_label"] = df["datetime"].apply(month_label)
    df["date"] = df["datetime"].dt.strftime("%Y-%m-%d")

    # Sort for readability
    sort_cols = [c for c in ["datetime", "eo_cloud_cover", "id"] if c in df.columns]
    df = df.sort_values(sort_cols, ascending=True, na_position="last").copy()

    # Save one CSV per month
    month_counts = []

    for month_label_value, month_df in df.groupby("month_label", sort=True):
        out_csv = OUT_DIR / f"{month_label_value}.csv"
        month_df.to_csv(out_csv, index=False)

        month_counts.append(
            {
                "month_label": month_label_value,
                "num_rows": len(month_df),
                "num_unique_dates": month_df["date"].nunique(),
                "num_unique_scene_ids": month_df["id"].nunique(),
                "min_cloud_cover": month_df["eo_cloud_cover"].min() if "eo_cloud_cover" in month_df.columns else None,
                "max_cloud_cover": month_df["eo_cloud_cover"].max() if "eo_cloud_cover" in month_df.columns else None,
                "mean_cloud_cover": month_df["eo_cloud_cover"].mean() if "eo_cloud_cover" in month_df.columns else None,
            }
        )

    # Save summary CSV
    summary_df = pd.DataFrame(month_counts).sort_values("month_label")
    summary_csv = OUT_DIR / "monthly_summary.csv"
    summary_df.to_csv(summary_csv, index=False)

    print("\nMonthly files written:")
    for _, row in summary_df.iterrows():
        print(
            f"  {row['month_label']}: "
            f"{int(row['num_rows'])} rows | "
            f"{int(row['num_unique_dates'])} unique dates"
        )

    print(f"\nSummary saved: {summary_csv}")

    # Optional: suggest a good month to start with
    suggested = summary_df.sort_values(
        by=["num_unique_dates", "num_rows"],
        ascending=[False, False]
    ).head(3)

    print("\nSuggested months to start experimenting with:")
    for _, row in suggested.iterrows():
        print(
            f"  {row['month_label']} | "
            f"{int(row['num_unique_dates'])} unique dates | "
            f"{int(row['num_rows'])} rows | "
            f"mean cloud cover: "
            f"{row['mean_cloud_cover']:.2f}" if pd.notna(row["mean_cloud_cover"]) else "n/a"
        )

    print("\nDone.")


if __name__ == "__main__":
    main()