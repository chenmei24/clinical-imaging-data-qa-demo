# Changelog

## 0.1.1 — 2026-10-12

### Fixed

- Reject source/output collisions for all four delivery paths, including resolved paths, symbolic links, and hard links; reject output aliases and unusable destinations before writing.
- Preserve decimal precision in cm-to-mm conversions, including `0.004 cm` to `0.04 mm`. Retain nonpositive, nonfinite, and unrepresentable values for review rather than converting them.
- Validate complete CSV structure before creating a delivery. Accept reordered named columns while reporting missing, unexpected, and duplicate headers separately.
- Stage all delivery files before publication, restore previous outputs after ordinary replacement failures, and preserve recovery files if restoration also fails.
- Show concise command-line input errors with exit code 2.

### Added

- Regression tests for precision, malformed inputs, source preservation, aliases, staging, and recovery failures.
- Linux/Windows CI matrix with Python 3.10 and 3.13.
- Full Chinese README, fixed-schema data dictionary, contribution guide, issue templates, and MIT license.

### Preserved

- Committed portfolio example: 120 source and output records, 8 QA events, 7 open queries, 1 documented conversion, and no dropped records.
- Existing fictional-data preview, case-study PDF, and Upwork contact link.

## Initial demonstration

- Published a standard-library-only CSV audit with fictional CT/MRI records, source-preserving examples, a one-page preview, and reproducibility tests.
