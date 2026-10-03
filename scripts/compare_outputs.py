"""Compare the regex and AI-assisted Lab 3 output tables."""

import argparse
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def text_value(value: object) -> str:
    """Return a consistent text value while keeping missing cells blank."""
    if value is None or pd.isna(value):
        return ""
    return str(value)


def numeric_values_match(left: str, right: str, tolerance: float = 0.0) -> bool:
    if left == "" and right == "":
        return True
    if left == "" or right == "":
        return False
    try:
        difference = abs(Decimal(left) - Decimal(right))
        return difference <= Decimal(str(tolerance))
    except InvalidOperation:
        return False


def semantic_match(field: str, regex_value: str, ai_value: str) -> bool:
    """Compare the underlying meaning while still keeping exact differences."""
    if field in {"sample_id", "sequence_id"}:
        regex_digits = re.sub(r"\D", "", regex_value)
        ai_digits = re.sub(r"\D", "", ai_value)
        return bool(regex_digits) and regex_digits == ai_digits

    if field == "glucose_value":
        # A tenth of a mg/dL covers the two approved conversion constants.
        return numeric_values_match(regex_value, ai_value, tolerance=0.1)

    if field in {"declared_length", "observed_length"}:
        return numeric_values_match(regex_value, ai_value)

    if field == "notes":
        regex_words = re.sub(r"[^a-z0-9]", "", regex_value.lower())
        ai_words = re.sub(r"[^a-z0-9]", "", ai_value.lower())
        return regex_words == ai_words

    return regex_value == ai_value


def compare_dataset(
    regex_path: Path,
    ai_path: Path,
    key_column: str,
    raw_id_column: str,
    fields: list[str],
    dataset_name: str,
) -> pd.DataFrame:
    """Build one long comparison table for a pair of cleaned outputs."""
    regex_data = pd.read_csv(regex_path, dtype=str, keep_default_na=False)
    ai_data = pd.read_csv(ai_path, dtype=str, keep_default_na=False)

    for label, data in (("regex", regex_data), ("AI", ai_data)):
        if key_column not in data.columns:
            raise ValueError(f"{label} output is missing key column: {key_column}")
        if data[key_column].duplicated().any():
            raise ValueError(f"{label} output has duplicate keys in {key_column}")

    if set(regex_data[key_column]) != set(ai_data[key_column]):
        raise ValueError(f"The {dataset_name} outputs do not contain the same records.")

    merged = regex_data.merge(
        ai_data,
        on=key_column,
        suffixes=("_regex", "_ai"),
        validate="one_to_one",
    ).sort_values(key_column, key=lambda column: column.astype(int))

    raw_regex_column = f"{raw_id_column}_regex"
    raw_ai_column = f"{raw_id_column}_ai"
    if not (merged[raw_regex_column] == merged[raw_ai_column]).all():
        raise ValueError(f"The {dataset_name} raw identifiers do not align.")

    comparison_rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        for field in fields:
            regex_value = text_value(row[f"{field}_regex"])
            ai_value = text_value(row[f"{field}_ai"])
            exact = regex_value == ai_value

            comparison_rows.append(
                {
                    "dataset": dataset_name,
                    "source_record": row[key_column],
                    "record_id_raw": row[raw_regex_column],
                    "field": field,
                    "regex_value": regex_value,
                    "ai_value": ai_value,
                    "exact_match": exact,
                    "semantic_match": semantic_match(
                        field,
                        regex_value,
                        ai_value,
                    ),
                    "regex_qc_flags": row["qc_flags_regex"],
                    "ai_qc_flags": row["qc_flags_ai"],
                }
            )

    return pd.DataFrame(comparison_rows)


def summarize_comparisons(comparisons: pd.DataFrame) -> pd.DataFrame:
    """Count exact and semantic agreements for each dataset and field."""
    summary_rows: list[dict[str, object]] = []
    grouped = comparisons.groupby(["dataset", "field"], sort=False)

    for (dataset, field), group in grouped:
        compared = len(group)
        exact_agreements = int(group["exact_match"].sum())
        semantic_agreements = int(group["semantic_match"].sum())
        summary_rows.append(
            {
                "dataset": dataset,
                "field": field,
                "records_compared": compared,
                "exact_agreements": exact_agreements,
                "exact_disagreements": compared - exact_agreements,
                "semantic_agreements": semantic_agreements,
                "semantic_disagreements": compared - semantic_agreements,
            }
        )

    return pd.DataFrame(summary_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare regex and AI-assisted Lab 3 outputs."
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=DEFAULT_PROCESSED_DIR,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    processed_dir = args.processed_dir

    required_files = [
        "samples_regex_clean.csv",
        "samples_ai_clean.csv",
        "sequences_regex_clean.csv",
        "sequences_ai_clean.csv",
    ]
    missing_files = [
        filename
        for filename in required_files
        if not (processed_dir / filename).exists()
    ]
    if missing_files:
        missing_list = ", ".join(missing_files)
        raise SystemExit(f"Missing required comparison files: {missing_list}")

    try:
        sample_comparison = compare_dataset(
            processed_dir / "samples_regex_clean.csv",
            processed_dir / "samples_ai_clean.csv",
            key_column="source_row",
            raw_id_column="sample_id_raw",
            fields=[
                "sample_id",
                "patient_name",
                "dob",
                "sex",
                "enrollment_site",
                "glucose_value",
                "glucose_unit",
                "notes",
            ],
            dataset_name="samples",
        )
        sequence_comparison = compare_dataset(
            processed_dir / "sequences_regex_clean.csv",
            processed_dir / "sequences_ai_clean.csv",
            key_column="source_record",
            raw_id_column="sequence_id_raw",
            fields=[
                "sequence_id",
                "organism",
                "gene",
                "declared_length",
                "observed_length",
                "note",
                "sequence",
            ],
            dataset_name="sequences",
        )
    except ValueError as error:
        raise SystemExit(f"Comparison failed: {error}") from error

    all_comparisons = pd.concat(
        [sample_comparison, sequence_comparison],
        ignore_index=True,
    )
    summary = summarize_comparisons(all_comparisons)

    sample_comparison.to_csv(
        processed_dir / "samples_comparison.csv",
        index=False,
    )
    sequence_comparison.to_csv(
        processed_dir / "sequences_comparison.csv",
        index=False,
    )
    summary.to_csv(
        processed_dir / "comparison_summary.csv",
        index=False,
    )

    exact_disagreements = int((~all_comparisons["exact_match"]).sum())
    semantic_disagreements = int((~all_comparisons["semantic_match"]).sum())
    print(f"Compared {len(all_comparisons)} record-field pairs.")
    print(f"Exact disagreements: {exact_disagreements}")
    print(f"Semantic disagreements: {semantic_disagreements}")
    print(f"Saved comparison tables to {processed_dir.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
