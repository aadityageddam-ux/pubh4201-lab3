"""Clean the Lab 3 FASTA data with explicit regex header patterns."""

import argparse
import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "messy_sequences.fasta"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "sequences_regex_clean.csv"

# Each expression handles one complete header layout found in the supplied file.
HEADER_PATTERNS = [
    re.compile(
        r"^(?P<id>[^|\s;]+)\|organism=(?P<organism>[^|]+)"
        r"\|gene=(?P<gene>[^|]+)\|len=(?P<length>\d+)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<id>\S+)\s+organism:(?P<organism>.+?)\s+gene:(?P<gene>\S+)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<id>\S+)\s*\|\s*(?P<organism>[^|]+?)\s*\|\s*"
        r"(?P<gene>[^|]+?)\s*\|\s*length=(?P<length>\d+)\s*bp$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<id>[^;]+);species=(?P<organism>[^;]+);target=(?P<gene>[^;]+)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<id>\S+)\s+(?P<organism>[^;]+);\s*(?P<gene>[^;]+);\s*"
        r"(?P<length>\d+)\s*bp$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<id>\S+)\s+organism=(?P<organism>[^|]+)"
        r"\|gene=(?P<gene>[^|]+)\|note[:=](?P<note>.+)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<id>\S+)\|(?P<organism>[A-Za-z._]+)"
        r"\|(?P<gene>[A-Za-z][A-Za-z0-9-]*)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?P<id>\S+)\s+species:(?P<organism>\S+)\s+"
        r"gene:(?P<gene>\S+)\s+len:(?P<length>NA|\d+)$",
        re.IGNORECASE,
    ),
]


def read_fasta(path: Path) -> list[tuple[str, str]]:
    """Read a FASTA file and return its headers and joined sequences."""
    records: list[tuple[str, str]] = []
    current_header: str | None = None
    sequence_lines: list[str] = []

    with path.open(encoding="utf-8") as fasta_file:
        for line_number, line in enumerate(fasta_file, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            if stripped_line.startswith(">"):
                if current_header is not None:
                    records.append((current_header, "".join(sequence_lines)))
                current_header = stripped_line
                sequence_lines = []
            elif current_header is None:
                raise ValueError(
                    f"Sequence data appeared before a header on line {line_number}."
                )
            else:
                sequence_lines.append(stripped_line)

    if current_header is not None:
        records.append((current_header, "".join(sequence_lines)))

    return records


def parse_header(header_raw: str) -> dict[str, str | None] | None:
    header_text = header_raw.removeprefix(">")
    for pattern in HEADER_PATTERNS:
        match = pattern.fullmatch(header_text)
        if match is not None:
            fields = match.groupdict()
            return {
                field: value.strip() if value is not None else None
                for field, value in fields.items()
            }
    return None


def clean_sequence_id(raw_value: str, qc_flags: list[str]) -> str | None:
    match = re.fullmatch(
        r"(?:sample|seq)[_-]?0*(\d+)",
        raw_value,
        flags=re.IGNORECASE,
    )
    if match is None:
        qc_flags.append("invalid_sequence_id")
        return None
    return f"SAMPLE-{int(match.group(1)):03d}"


def clean_organism(raw_value: str, qc_flags: list[str]) -> str | None:
    if re.fullmatch(r"Homo[_ ]sapiens", raw_value, flags=re.IGNORECASE):
        return "Homo sapiens"
    if re.fullmatch(r"H\.?sapiens", raw_value, flags=re.IGNORECASE):
        return "Homo sapiens"

    qc_flags.append("invalid_organism")
    return None


def clean_gene(raw_value: str, qc_flags: list[str]) -> str | None:
    gene = raw_value.strip()
    if not gene:
        qc_flags.append("missing_gene")
        return None
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", gene) is None:
        qc_flags.append("invalid_gene")
        return None
    return gene.upper()


def clean_declared_length(
    raw_value: str | None,
    qc_flags: list[str],
) -> int | None:
    if raw_value is None:
        qc_flags.append("declared_length_not_provided")
        return None
    if re.fullmatch(r"NA", raw_value, flags=re.IGNORECASE):
        qc_flags.append("declared_length_na")
        return None
    if re.fullmatch(r"\d+", raw_value) is None:
        qc_flags.append("invalid_declared_length")
        return None
    return int(raw_value)


def clean_sequence(raw_sequence: str, qc_flags: list[str]) -> str:
    sequence = re.sub(r"\s+", "", raw_sequence).upper()
    if not sequence:
        qc_flags.append("missing_sequence")
    elif re.fullmatch(r"[ACGT]+", sequence) is None:
        qc_flags.append("invalid_sequence_characters")
    return sequence


def clean_record(
    header_raw: str,
    raw_sequence: str,
    source_record: int,
) -> dict[str, object]:
    qc_flags: list[str] = []
    header_fields = parse_header(header_raw)
    sequence = clean_sequence(raw_sequence, qc_flags)
    observed_length = len(sequence)

    if header_fields is None:
        qc_flags.append("unrecognized_header_format")
        return {
            "source_record": source_record,
            "header_raw": header_raw,
            "sequence_id_raw": None,
            "sequence_id": None,
            "organism_raw": None,
            "organism": None,
            "gene_raw": None,
            "gene": None,
            "declared_length_raw": None,
            "declared_length": None,
            "observed_length": observed_length,
            "note_raw": None,
            "note": None,
            "sequence": sequence,
            "qc_flags": ";".join(qc_flags),
        }

    sequence_id_raw = header_fields["id"]
    organism_raw = header_fields["organism"]
    gene_raw = header_fields["gene"]
    declared_length_raw = header_fields.get("length")
    note_raw = header_fields.get("note")

    declared_length = clean_declared_length(declared_length_raw, qc_flags)
    if declared_length is not None and declared_length != observed_length:
        qc_flags.append("length_mismatch")

    return {
        "source_record": source_record,
        "header_raw": header_raw,
        "sequence_id_raw": sequence_id_raw,
        "sequence_id": clean_sequence_id(sequence_id_raw, qc_flags),
        "organism_raw": organism_raw,
        "organism": clean_organism(organism_raw, qc_flags),
        "gene_raw": gene_raw,
        "gene": clean_gene(gene_raw, qc_flags),
        "declared_length_raw": declared_length_raw,
        "declared_length": declared_length,
        "observed_length": observed_length,
        "note_raw": note_raw,
        "note": note_raw.strip() if note_raw else None,
        "sequence": sequence,
        "qc_flags": ";".join(qc_flags),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean messy_sequences.fasta with explicit regex rules."
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

    try:
        fasta_records = read_fasta(args.input)
    except ValueError as error:
        raise SystemExit(f"Could not read FASTA file: {error}") from error

    cleaned_rows = [
        clean_record(header, sequence, source_record=index)
        for index, (header, sequence) in enumerate(fasta_records, start=1)
    ]
    cleaned_data = pd.DataFrame(cleaned_rows)
    cleaned_data["declared_length"] = cleaned_data["declared_length"].astype("Int64")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cleaned_data.to_csv(args.output, index=False, na_rep="")

    flagged_rows = (cleaned_data["qc_flags"] != "").sum()
    print(f"Cleaned {len(cleaned_data)} FASTA records.")
    print(f"Rows with at least one QC flag: {flagged_rows}")
    print(f"Saved output to {args.output.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
