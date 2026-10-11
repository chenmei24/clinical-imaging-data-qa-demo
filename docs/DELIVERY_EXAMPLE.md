# Sample delivery note — synthetic imaging data

**Illustrative only.** These 120 CT/MRI records are fictional and were created for this portfolio. No patient or client data was used.

## What was received

`01_synthetic_source.csv` — 120 records, 7 columns. The original is preserved unchanged.

## What was delivered

| File | Use |
| --- | --- |
| [`02_standardized_with_flags.csv`](../examples/02_standardized_with_flags.csv) | All 120 rows, with one documented unit normalization |
| [`03_query_log.csv`](../examples/03_query_log.csv) | Eight row-level QA events, including seven open questions and one conversion |
| [`04_change_log.csv`](../examples/04_change_log.csv) | Before/after value for the one applied change |
| [`05_summary.json`](../examples/05_summary.json) | Machine-readable counts for review or downstream automation |
| [`audit_csv.py`](../scripts/audit_csv.py) | Reproducible command for files matching this demo schema |

## Review points for the source owner

- Confirm the two repeated record IDs. The script does **not** decide which record is valid.
- Confirm the blank and implausible ages, unexpected category, invalid date, and nonpositive measurement against the data dictionary and source system.
- The `2.7 cm` measurement was converted to `27.0 mm`; the change log preserves the original value and reason.

**Acceptance check:** 120 input rows → 120 output rows; no silent deletion or invented value; all eight events trace to a source row. The source owner decides whether and how to resolve the seven open queries. No statistical or clinical conclusion is made.
