# Regex and AI-Assisted Cleaning Comparison

## Approaches

I cleaned the clinical sample CSV and FASTA file with two approaches. For the
regex approach, I used Python rules for each known format. The clinical script
standardized sample IDs, names, dates, sex categories, enrollment sites, and
glucose results. The FASTA script used several small header patterns because
the eight headers did not follow one layout. Both scripts preserved important
raw values and added quality-control flags instead of silently changing
questionable records.

For the AI-assisted approach, I used separate Codex chats for the clinical and
FASTA files. Each chat received only the official raw file, requested output
columns, and assignment requirements. It was not allowed to inspect the regex
scripts or outputs. This made the AI output an independent comparison.

## Agreement and disagreement

The comparison covered 536 record-field pairs: 480 clinical and 56 FASTA.
There were 85 exact string disagreements but no semantic disagreements after
accounting for equivalent identifier formats, numeric formatting, rounding,
and note wording.

Most differences were formatting choices. Regex used clinical IDs such as
`S-0001`, while AI used `S0001`, accounting for 60 differences. Regex FASTA
IDs used `SAMPLE-001`, while AI used `sample_001`, accounting for eight more.
The numeric identifiers still matched. Thirteen glucose values differed
exactly. Most were values like `120.0` versus `120`; three converted values
differed by 0.1 mg/dL because regex used a conversion factor of 18.0182 and AI
used 18.018. Four notes differed because regex preserved
`re-draw requested`, while AI wrote `Redraw requested`. Regex was more
traceable here because it retained the source wording.

The approaches agreed exactly on patient names, dates, sex, enrollment sites,
glucose units, organisms, genes, declared and observed sequence lengths, FASTA
notes, and sequences. This strong agreement did not mean every source value
was trustworthy.

## Failure modes and ambiguous records

Source row 40, sample `S0039`, contained `241.2* mmol/L`. Regex converted it to
4346.0 mg/dL, while AI produced 4345.9 mg/dL. Both removed the star from the
numeric value, preserved the raw field, and flagged the extreme result. The
small rounding difference was less important than the suspicious unit-value
combination. The source generator produced values in a range that looked like
mg/dL and then randomly assigned units. Neither approach could know whether
the label was wrong or the result was truly extreme. In real data, I would
confirm this with the provider instead of automatically correcting it.

Dates also contained ambiguity. Regex interpreted slash dates as
month/day/year because that was the documented generator format. AI still
flagged 13 numeric dates because a value such as `07/09/1962` could have two
interpretations if the source convention were unknown. Regex was justified
for this dataset, but the AI warning would be useful with undocumented data.

The first FASTA parser showed a regex failure mode. Record 7 included a note,
but a general pipe pattern matched it before the specific note pattern and put
key-value sections into the wrong columns. Validation caught the problem. I
moved the specific pattern first and changed the general pattern so an ID
could not contain spaces. This demonstrated that a regex can match text while
still interpreting its structure incorrectly.

FASTA records 3 and 5 also had mismatched lengths. Record 3 declared 150 bases
but contained 157, and record 5 declared 130 but contained 144. Both methods
kept both lengths and flagged the mismatch instead of truncating the sequence
or overwriting the declared value. AI additionally flagged unlabeled
positional fields in records 3, 5, and 6.

## Trust and effort

AI produced structured output faster, but reviewing it took longer because
plausible results still required record-by-record checking. Regex required
more work upfront to define, order, and debug the rules. After validation, its
behavior was easier to trace and rerun. I did not record exact minutes, so this
is a qualitative comparison.

For real data, I would trust validated regex rules more for production cleaning
because they are deterministic and auditable. I would use AI as a second
reviewer. Here, AI helped identify ambiguous dates, suspicious unit-value
pairs, abbreviated organism names, and unlabeled FASTA fields. A strong
workflow would use deterministic code for transformations and AI to identify
assumptions and records needing human review.

## Extra-credit analytic table

The extra-credit table has one row per sample. `glucose_mg_dl` is the feature;
sample ID, date of birth, sex, enrollment site, notes, and QC flags are
metadata. I removed patient name from this analysis-focused table, while the
audit-oriented cleaned table still preserves names and raw values.

The table is consistent but not ready for modeling without further review.
All 60 IDs are unique, dates are in ISO format, categories are standardized,
and glucose uses one numeric unit. However, five samples have missing sex and
13 glucose results exceed 1000 mg/dL after literal mmol/L conversion. Those
unit-value pairs need confirmation before analysis. The table also contains
only one measured feature, so useful modeling would require a defined outcome
and more validated predictors.
