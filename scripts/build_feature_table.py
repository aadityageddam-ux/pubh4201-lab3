"""Build the extra-credit samples x features x metadata table."""

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "processed" / "samples_regex_clean.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "samples_feature_table.csv"

REQUIRED_COLUMNS = {
    "sample_id",
    "glucose_value",
    "dob",
    "sex",
    "enrollment_site",
    "notes",
    "qc_flags",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a samples x features x metadata table."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Cleaned sample table not found: {args.input}")

    cleaned_data = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    missing_columns = REQUIRED_COLUMNS - set(cleaned_data.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise SystemExit(f"Input is missing required columns: {missing_list}")

    if cleaned_data["sample_id"].duplicated().any():
        duplicate_ids = cleaned_data.loc[
            cleaned_data["sample_id"].duplicated(keep=False),
            "sample_id",
        ].tolist()
        raise SystemExit(f"Duplicate sample IDs found: {duplicate_ids}")

    # Converting these columns checks their types without dropping missing values.
    parsed_glucose = pd.to_numeric(cleaned_data["glucose_value"], errors="coerce")
    invalid_glucose = (cleaned_data["glucose_value"] != "") & parsed_glucose.isna()
    if invalid_glucose.any():
        raise SystemExit("One or more cleaned glucose values are not numeric.")

    parsed_dates = pd.to_datetime(
        cleaned_data["dob"],
        format="%Y-%m-%d",
        errors="coerce",
    )
    invalid_dates = (cleaned_data["dob"] != "") & parsed_dates.isna()
    if invalid_dates.any():
        raise SystemExit("One or more cleaned dates are not valid ISO dates.")

    feature_table = pd.DataFrame(
        {
            "sample_id": cleaned_data["sample_id"],
            "glucose_mg_dl": parsed_glucose,
            "dob": parsed_dates.dt.strftime("%Y-%m-%d").fillna(""),
            "sex": cleaned_data["sex"],
            "enrollment_site": cleaned_data["enrollment_site"],
            "notes": cleaned_data["notes"],
            "qc_flags": cleaned_data["qc_flags"],
        }
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    feature_table.to_csv(args.output, index=False, na_rep="")

    missing_glucose = int(feature_table["glucose_mg_dl"].isna().sum())
    missing_sex = int((feature_table["sex"] == "").sum())
    extreme_values = int(
        feature_table["qc_flags"].str.contains(
            "extreme_glucose_after_conversion",
            regex=False,
        ).sum()
    )
    print(f"Built feature table with {len(feature_table)} samples.")
    print(f"Missing glucose values: {missing_glucose}")
    print(f"Missing sex values: {missing_sex}")
    print(f"Extreme converted glucose values flagged: {extreme_values}")
    print(f"Saved output to {args.output.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
