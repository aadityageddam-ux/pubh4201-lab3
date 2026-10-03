# PUBH 4201 Lab 3: Parsing Messy Data

This repository contains my work for Lab 3 in PUBH 4201. The project compares regex-based cleaning with generative AI-assisted extraction using the clinical sample and FASTA datasets supplied with the course.

## Project status

Complete. This repository contains regex-based and AI-assisted cleaning for
both course datasets, their comparison tables, the extra-credit analytic
feature table, and the final comparison write-up.

## Repository structure

- `scripts/` contains the Python cleaning and comparison scripts.
- `data/raw/` stores local copies of the supplied data and is not committed.
- `data/processed/` contains the cleaned output tables required for submission.
- `writeup/` contains the comparison and failure-mode analysis.

## Environment setup

This project uses Python 3.12 and `uv` for dependency management.

```powershell
uv sync
```

## Running the project

Download fresh copies of both course datasets:

```powershell
uv run python scripts/download_data.py
```

The files are saved in `data/raw/`. This folder is ignored by Git because
the original data should be loaded from its source instead of committed to
this repository.

Clean the clinical sample data with the regex-based script:

```powershell
uv run python scripts/clean_samples_regex.py
```

This reads `data/raw/messy_samples.csv` and writes the structured result to
`data/processed/samples_regex_clean.csv`. Original values are kept beside
their standardized versions so that each change can be checked.

Clean the FASTA data with the regex-based script:

```powershell
uv run python scripts/clean_sequences_regex.py
```

This reads `data/raw/messy_sequences.fasta` and writes the structured result
to `data/processed/sequences_regex_clean.csv`. The original header is kept,
and declared sequence lengths are checked against the observed lengths.

Compare the regex and AI-assisted outputs:

```powershell
uv run python scripts/compare_outputs.py
```

The script writes record-level comparisons for both datasets and a summary by
field. It reports exact agreement separately from semantic agreement so that
formatting choices are not mistaken for different underlying values.

Build the extra-credit samples × features × metadata table:

```powershell
uv run python scripts/build_feature_table.py
```

This creates `data/processed/samples_feature_table.csv` from the regex-cleaned
clinical table. It keeps one row per sample, uses standardized glucose as the
feature, retains analysis-relevant metadata and QC flags, and excludes patient
names from the analytic table.
