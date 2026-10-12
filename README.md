# Clinical imaging data QA — a reproducible synthetic demo

[![Reproduce synthetic QA example](https://github.com/chenmei24/clinical-imaging-data-qa-demo/actions/workflows/qa.yml/badge.svg)](https://github.com/chenmei24/clinical-imaging-data-qa-demo/actions/workflows/qa.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

English · [简体中文](README.zh-CN.md)

**120 synthetic records · 8 documented QA events · 1 defensible unit conversion · 0 silently dropped rows**

This portfolio project shows how a messy clinical-imaging research export can become a **traceable review package**. Every record is fictional (`SYN-*`); this is a self-created demonstration, not a client project, patient dataset, diagnosis, or research result.

**Try it with Python 3.10+, no packages to install.** From the repository root:

```bash
python scripts/audit_csv.py --input examples/01_synthetic_source.csv --output-dir output
```

Need the same audit for your own authorized, de-identified dataset? [Request a scoped project through Upwork](https://www.upwork.com/freelancers/~0149df5417ad7e0bcf).

![One-page synthetic data quality audit preview](assets/portfolio_preview.png)

## See the difference

| Source row | Before | After | Audit trail |
| --- | --- | --- | --- |
| 81 · `SYN-080` | `lesion_value=2.7`, `lesion_unit=cm` | `lesion_value=27.0`, `lesion_unit=mm` | Conversion logged; source preserved |
| 11 · `SYN-010` | `age_years=155` | **Retained as 155** | Flagged for source-owner verification |
| 120 · `SYN-001` | Repeated record ID | **Both rows retained** | Duplicate flagged; no guessed merge |

The one-page [case study PDF](assets/portfolio_case_study.pdf) and the committed [source](examples/01_synthetic_source.csv), [standardized copy](examples/02_standardized_with_flags.csv), [query log](examples/03_query_log.csv), [change log](examples/04_change_log.csv), and [summary](examples/05_summary.json) let a buyer inspect the actual deliverables.

## What this demo checks

| Check | Example in this dataset | Handling |
| --- | --- | --- |
| Duplicate key | 2 repeated IDs | Retain and query; do not merge |
| Missing / implausible age | Blank, `155` | Retain and query; do not impute |
| Unexpected category | `sex_code=X` | Retain and query against the data dictionary |
| Nonpositive measurement | `lesion_value=-2` | Retain and query |
| Invalid date | `2025/04/31` | Retain and query |
| Unit mismatch | `2.7 cm` among millimetres | Convert to `27.0 mm` and log before/after |

The eight events comprise **seven unresolved queries and one documented conversion**. The checks are demonstration rules for this schema; a real engagement starts by agreeing on the client's data dictionary, valid ranges, units, exclusions, and acceptance criteria.

## Run it

Python 3.10+; **standard library only** for the audit. From the repository root:

```bash
python scripts/audit_csv.py --input examples/01_synthetic_source.csv --output-dir output
python -m unittest discover -s tests -v
```

The command writes `02_standardized_with_flags.csv`, `03_query_log.csv`, `04_change_log.csv`, and `05_summary.json` into `output/`. Questionable values stay in the standardized copy; the separate query log records their flags. Successful reruns replace these four output files.

The tests check the committed demonstration and error cases: exact decimal conversions, invalid values, malformed headers/rows, source aliases, and failures during delivery writing. CI runs the suite on Linux and Windows with Python 3.10 and 3.13.

On Windows, if you clone this repository under a path containing non-ASCII characters and your Python installation uses a legacy locale, run `python -X utf8` in place of `python`.

For a concise handoff example, see [Sample delivery note](docs/DELIVERY_EXAMPLE.md).

## Input format and preservation

Use a UTF-8 CSV with these **exact, case-sensitive column names**. Column order may change; the output always uses the order below. Missing, extra, or duplicate column names are rejected with a specific error. Each record must have the same number of fields as the header; an empty field is retained and checked, whereas a structurally absent field is rejected.

| Column | Fixed demonstration rule |
| --- | --- |
| `record_id` | Nonempty and unique; missing/duplicate IDs are retained and queried |
| `age_years` | Integer text between 0 and 120; blank/invalid values are retained and queried |
| `sex_code` | `F` or `M`; other codes require source-owner review |
| `modality` | `CT` or `MRI` |
| `lesion_value` | Finite, positive decimal measurement |
| `lesion_unit` | `mm`, or `cm` for a documented conversion of a finite positive value |
| `scan_date` | Valid calendar date in `YYYY-MM-DD` format |

The human-readable rules are also in [the data dictionary](schemas/data_dictionary.json). The file documents the fixed demo schema; it is **not a runtime configuration file**. The ranges and categories are example conventions, not universal clinical limits.

- Positive `cm` measurements are multiplied by 10 using exact decimal arithmetic. `2.7 cm` becomes `27.0 mm`; `0.004 cm` becomes `0.04 mm`. Very large/small values may use scientific notation; no decimal place is rounded away.
- Negative, zero, nonfinite, and unparseable measurements are retained without conversion. A finite value whose conversion exceeds Decimal's representation limits is also retained and queried. Empty input, malformed CSV, and unusable destinations fail with exit code 2.
- The source is read only. Input/output path collisions are rejected, including resolved paths, symbolic links, and hard links. Output files cannot be symlinks or aliases of one another.
- All four deliverables are prepared in a temporary staging directory before publication. Ordinary replacement failures trigger restoration of the previous delivery files; if restoration also fails, the error reports a preserved recovery directory. Run one process per output directory; this is not a concurrent-writer or crash-recovery system.
- `source_row` in logs counts logical CSV records, with the header at 1. It is not a physical line number if a quoted field contains a newline or blank text lines are skipped.

## How a client project differs

1. Review an **authorized, de-identified** sample, column definitions, and intended use.
2. Agree on record keys, valid ranges/codes, units, transformations, and how open queries will be resolved.
3. Deliver a source-preserving cleaned copy, row-level QA log, documented changes, concise summary, and—if scoped—a reusable batch script.
4. Re-run checks after source-owner answers; support a scheduled QA workflow if ongoing maintenance is needed.

This repository demonstrates the method; it is not a universal clinical validation pipeline. If you need a custom data cleaning or automated QA workflow, [contact me through my Upwork profile](https://www.upwork.com/freelancers/~0149df5417ad7e0bcf) with an authorized **de-identified** sample and data dictionary. Do not post patient-identifiable data in a public issue.

## Repository map

```text
assets/      Portfolio preview and one-page PDF
examples/    Synthetic source plus inspectable delivery examples
scripts/     Reusable CSV audit command
tests/       Reproducibility and data-preservation checks
schemas/     Fixed demonstration data dictionary
```

See [changes](CHANGELOG.md), [contribution instructions](CONTRIBUTING.md), and the [MIT license](LICENSE). Bug reports with a small **fictional** reproduction are welcome through [GitHub Issues](https://github.com/chenmei24/clinical-imaging-data-qa-demo/issues).

No clinical conclusion is inferred from these values. Ambiguous records are left for the authorized source owner to resolve.

## Related tools / 相关工具

- [Medical-imaging manifest audits](https://github.com/chenmei24/dicleak)
- [Manuscript rule checks](https://github.com/chenmei24/manulint)

[Launch tutorials and share images / 推广教程与展示图](docs/launch/README.md)
