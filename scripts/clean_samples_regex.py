"""Clean the Lab 3 clinical sample data with explicit regex rules."""

import argparse
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "messy_samples.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "samples_regex_clean.csv"

EXPECTED_COLUMNS = {
    "sample_id",
    "patient_name",
    "dob",
    "sex",
    "enrollment_site",
    "glucose_value",
    "glucose_unit",
    "notes",
}


def clean_sample_id(raw_value: str, qc_flags: list[str]) -> str | None:
    match = re.fullmatch(r"[Ss]-?(\d{4})", raw_value.strip())
    if match is None:
        qc_flags.append("invalid_sample_id")
        return None
    return f"S-{match.group(1)}"


def clean_patient_name(raw_value: str, qc_flags: list[str]) -> str | None:
    name = re.sub(r"\s+", " ", raw_value.strip())
    if not name:
        qc_flags.append("missing_patient_name")
        return None
    return name.title()


def clean_dob(raw_value: str, qc_flags: list[str]) -> str | None:
    value = raw_value.strip()

    try:
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
            parsed_date = datetime.strptime(value, "%m/%d/%Y").date()
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
        elif re.fullmatch(r"\d{2}-[A-Za-z]{3}-\d{4}", value):
            parsed_date = datetime.strptime(value.title(), "%d-%b-%Y").date()
        else:
            dotted_match = re.fullmatch(
                r"(?P<month>\d{2})\.(?P<day>\d{2})\.(?P<year>\d{2})",
                value,
            )
            if dotted_match is None:
                qc_flags.append("invalid_dob_format")
                return None

            short_year = int(dotted_match.group("year"))
            if 0 <= short_year <= 18:
                full_year = 2000 + short_year
            elif 50 <= short_year <= 99:
                full_year = 1900 + short_year
            else:
                qc_flags.append("ambiguous_two_digit_year")
                return None

            parsed_date = datetime(
                full_year,
                int(dotted_match.group("month")),
                int(dotted_match.group("day")),
            ).date()
            qc_flags.append("two_digit_year_inferred")
    except ValueError:
        qc_flags.append("invalid_dob")
        return None

    return parsed_date.isoformat()


def clean_sex(raw_value: str, qc_flags: list[str]) -> str | None:
    value = raw_value.strip()
    if not value:
        qc_flags.append("missing_sex")
        return None
    if re.fullmatch(r"m(?:ale)?", value, flags=re.IGNORECASE):
        return "Male"
    if re.fullmatch(r"f(?:emale)?", value, flags=re.IGNORECASE):
        return "Female"
    if re.fullmatch(r"u|unknown", value, flags=re.IGNORECASE):
        return "Unknown"

    qc_flags.append("invalid_sex")
    return None


def clean_site(raw_value: str, qc_flags: list[str]) -> str | None:
    match = re.fullmatch(
        r"site[\s_-]*([abc])",
        raw_value.strip(),
        flags=re.IGNORECASE,
    )
    if match is None:
        qc_flags.append("invalid_enrollment_site")
        return None
    return f"Site {match.group(1).upper()}"


def clean_glucose(
    raw_value: str,
    raw_unit: str,
    qc_flags: list[str],
) -> tuple[float | None, str | None]:
    value = raw_value.strip()
    unit = raw_unit.strip()

    if not value or re.fullmatch(r"N/?A", value, flags=re.IGNORECASE):
        qc_flags.append("missing_glucose_value")
        return None, None

    value_match = re.fullmatch(r"(\d+(?:\.\d+)?)(\*)?", value)
    if value_match is None:
        qc_flags.append("invalid_glucose_value")
        return None, None
    if value_match.group(2):
        qc_flags.append("annotated_glucose_value")

    numeric_value = float(value_match.group(1))
    if re.fullmatch(r"mg/dl", unit, flags=re.IGNORECASE):
        standardized_value = numeric_value
    elif re.fullmatch(r"mmol/l", unit, flags=re.IGNORECASE):
        standardized_value = numeric_value * 18.0182
    else:
        qc_flags.append("invalid_glucose_unit" if unit else "missing_glucose_unit")
        return None, None

    standardized_value = round(standardized_value, 1)
    if standardized_value > 1000:
        qc_flags.append("extreme_glucose_after_conversion")

    return standardized_value, "mg/dL"


def clean_notes(raw_value: str) -> str | None:
    # Blank notes stay missing instead of becoming the text "None" or "NaN".
    notes = raw_value.strip()
    return notes or None


def clean_row(row: pd.Series, source_row: int) -> dict[str, object]:
    qc_flags: list[str] = []
    glucose_value, glucose_unit = clean_glucose(
        row["glucose_value"],
        row["glucose_unit"],
        qc_flags,
    )

    return {
        "source_row": source_row,
        "sample_id_raw": row["sample_id"],
        "sample_id": clean_sample_id(row["sample_id"], qc_flags),
        "patient_name_raw": row["patient_name"],
        "patient_name": clean_patient_name(row["patient_name"], qc_flags),
        "dob_raw": row["dob"],
        "dob": clean_dob(row["dob"], qc_flags),
        "sex_raw": row["sex"],
        "sex": clean_sex(row["sex"], qc_flags),
        "enrollment_site_raw": row["enrollment_site"],
        "enrollment_site": clean_site(row["enrollment_site"], qc_flags),
        "glucose_value_raw": row["glucose_value"],
        "glucose_unit_raw": row["glucose_unit"],
        "glucose_value": glucose_value,
        "glucose_unit": glucose_unit,
        "notes_raw": row["notes"],
        "notes": clean_notes(row["notes"]),
        "qc_flags": ";".join(qc_flags),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean messy_samples.csv with explicit regex rules."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(
            f"Input file not found: {args.input}\n"
            "Run 'uv run python scripts/download_data.py' first."
        )

    # Reading everything as text keeps values such as "N/A" available for review.
    raw_data = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    missing_columns = EXPECTED_COLUMNS - set(raw_data.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise SystemExit(f"Input is missing required columns: {missing_list}")

    cleaned_rows = [
        clean_row(row, source_row=index + 2)
        for index, (_, row) in enumerate(raw_data.iterrows())
    ]
    cleaned_data = pd.DataFrame(cleaned_rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cleaned_data.to_csv(args.output, index=False, na_rep="")

    flagged_rows = (cleaned_data["qc_flags"] != "").sum()
    print(f"Cleaned {len(cleaned_data)} records.")
    print(f"Rows with at least one QC flag: {flagged_rows}")
    print(f"Saved output to {args.output.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
