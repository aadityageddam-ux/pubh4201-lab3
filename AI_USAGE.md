# Generative AI Use

## Tool and model

I used OpenAI Codex, described in the application as GPT-5-based. The exact
deployment identifier was not exposed.

## How I used AI

I used Codex throughout this assignment to help with:

- Setting up the Python and `uv` project structure.
- Drafting and revising the regex-cleaning scripts.
- Identifying possible parsing rules and edge cases.
- Debugging the FASTA pattern order.
- Creating the comparison and extra-credit feature-table scripts.
- Independently generating the two AI-assisted output tables.
- Checking output schemas, record counts, standardized values, QC flags, and
  reproducibility.
- Organizing and editing the comparison write-up.
- Drafting this AI-use disclosure.

I made the final cleaning decisions. These included the identifier formats,
date interpretation rules, glucose conversion policy, name normalization,
raw-value preservation, QC flags, and ordering of the FASTA regex patterns. I
reviewed each proposed change before it was added to the repository.

## Independent AI-assisted clinical extraction

I started a separate Codex chat that could only use the official raw clinical
CSV. I instructed it not to inspect the regex code, regex output, or previous
parsing decisions. This separation was intended to make the AI output an
independent comparison.

### Clinical prompt

```text
Independently perform the generative-AI-assisted cleaning for PUBH 4201 Lab 3 using the official synthetic clinical dataset at https://raw.githubusercontent.com/gwcbi/applied-computing-HDS/refs/heads/main/data/raw/lab3-messy-data/messy_samples.csv.

Important isolation rule: do not inspect, search for, or use any existing regex cleaning script, regex output table, or prior Lab 3 solution. This output must be an independent AI-assisted interpretation of the raw CSV.

Create a user-facing CSV file named samples_ai_clean.csv in your outputs directory. Preserve all 60 records in their original order. Use exactly these columns: source_row, sample_id_raw, sample_id, patient_name_raw, patient_name, dob_raw, dob, sex_raw, sex, enrollment_site_raw, enrollment_site, glucose_value_raw, glucose_unit_raw, glucose_value, glucose_unit, notes_raw, notes, qc_flags.

Clean the data using your own interpretation of the raw records. Use one consistent sample-ID format; standardize patient-name spacing and capitalization; convert valid dates to YYYY-MM-DD; standardize sex and enrollment-site categories; standardize glucose to mg/dL using the recorded unit and a scientifically appropriate conversion; preserve missing values rather than inventing them; and use semicolon-separated qc_flags for ambiguity, missingness, annotations, or suspicious results. Preserve every requested raw field exactly as it appeared in the CSV. source_row should be the original CSV line number, where the header is line 1 and the first data record is line 2.

Do not create or draft AI_USAGE.md. Do not create or modify a GitHub repository. After writing the CSV, validate the row count, output schema, missing values, standardized categories, and several edge cases. In the final response, report the absolute output path, the cleaning assumptions you independently chose, the model name if available, and any ambiguous or suspicious records. Do not include or consult the regex solution.
```

The AI produced `data/processed/samples_ai_clean.csv`. It used `S0001`-style
identifiers, interpreted numeric dates as month-first, converted recorded
mmol/L results using a factor of 18.018, and added flags for ambiguous dates,
missing or unknown sex values, glucose annotations, suspicious unit-value
combinations, and redraw notes.

## Independent AI-assisted FASTA extraction

I used another separate Codex chat for the FASTA file. It was also prohibited
from inspecting the repository, regex parser, regex output, or earlier parsing
discussion.

### FASTA prompt

```text
This is the independent generative-AI-assisted FASTA-cleaning portion of PUBH 4201 Lab 3, completed for the undergraduate extra-credit addendum. The final assignment compares this AI-assisted result against a separately developed regex parser.

Use only the official synthetic FASTA dataset at https://raw.githubusercontent.com/gwcbi/applied-computing-HDS/refs/heads/main/data/raw/lab3-messy-data/messy_sequences.fasta.

Isolation rule: do not inspect, search for, or use any existing Lab 3 repository, regex parser, regex output table, prior Lab 3 solution, or earlier conversation about parsing rules. Make your own cleaning and normalization decisions from the raw FASTA file and the requirements below.

Create a user-facing CSV named sequences_ai_clean.csv in your outputs directory. It must contain one row for each of the eight FASTA records, in original order, using exactly these columns: source_record, header_raw, sequence_id_raw, sequence_id, organism_raw, organism, gene_raw, gene, declared_length_raw, declared_length, observed_length, note_raw, note, sequence, qc_flags.

Requirements:
- Preserve header_raw exactly, including the leading > character.
- Preserve and join each full sequence without line breaks; do not truncate or invent bases.
- Extract the raw identifier, organism/species, gene/target, declared length, and optional note from the varied header layouts using your own interpretation.
- Choose and apply one consistent cleaned identifier format.
- Standardize organism and gene values consistently.
- Store a numeric declared length when one is present; distinguish an explicit NA from a missing header field using qc_flags.
- Compute observed_length from the joined sequence.
- Preserve both declared and observed length; flag disagreements instead of editing the sequence.
- Validate sequence characters and use semicolon-separated qc_flags for missing, ambiguous, suspicious, or invalid values.
- Do not create or draft AI_USAGE.md.
- Do not create or modify a GitHub repository.

After saving the CSV, validate the eight-record count, exact schema, raw header and sequence preservation, identifier uniqueness, standardized categories, observed lengths, declared-length comparisons, notes, and QC flags. In the final response, report the absolute output path, the independent cleaning assumptions you chose, the model name if available, any ambiguous or suspicious records, and confirmation that no regex solution or prior Lab 3 output was consulted.
```

The AI produced `data/processed/sequences_ai_clean.csv`. It standardized
identifiers as `sample_001` through `sample_008`, organisms as `Homo sapiens`,
and gene symbols in uppercase. It preserved complete sequences, calculated
observed lengths, distinguished missing lengths from explicit `NA`, and
flagged unlabeled or abbreviated header fields.

## What I accepted, changed, or rejected

I kept both AI-generated CSV files unchanged so they could remain independent
comparison outputs. I did not alter them to match the regex results.

Several AI choices differed from my regex choices:

- The AI used clinical IDs such as `S0001`; my regex output uses `S-0001`.
- The AI used FASTA IDs such as `sample_001`; my regex output uses
  `SAMPLE-001`.
- The AI used 18.018 as its mmol/L-to-mg/dL conversion factor; the regex
  script uses 18.0182.
- The AI changed `re-draw requested` to `Redraw requested`; the regex output
  preserves the source wording.
- The AI flagged 13 numeric dates as potentially ambiguous even though the
  course data generator documents the month-first convention.
- The AI added useful warnings for suspicious glucose unit-value combinations
  and unlabeled or abbreviated FASTA fields.

I treated the identifier, numeric-formatting, rounding, and note differences
as semantically equivalent in the comparison instead of forcing the two
outputs to be textually identical.

The AI initially included an incorrect expected value in one clinical
validation assertion. Recalculating the conversion showed that
`159.9 × 18.018` rounds to `2881.1`, not `2880.9`, so the assertion was
corrected before the final AI table was accepted.

During regex development, an early general FASTA pipe pattern incorrectly
matched record 7 before the more specific note-containing pattern. After
reviewing the problem, I approved moving the specific pattern earlier and
restricting the general identifier pattern so it could not contain spaces.

## Verification and limitations

I did not accept the AI outputs only because they looked reasonable. The final
workflow checked record counts, required columns, unique identifiers, allowed
categories, date formats, glucose units, raw-value preservation, sequence
characters, observed lengths, declared-length mismatches, and comparison
totals.

The complete documented workflow was also rerun in a fresh clone. All
regenerated output tables matched the committed versions. The comparison
found 85 exact string disagreements across 536 record-field pairs but no
semantic disagreements under the documented comparison rules.

AI produced structured output quickly, but reviewing it took longer because
plausible results still needed to be checked carefully. The regex rules
required more work upfront, but their final behavior was easier to trace and
reproduce.
