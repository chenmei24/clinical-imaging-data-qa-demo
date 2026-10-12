# Contributing

Small, reproducible improvements are welcome. This repository demonstrates a fixed-schema research-data QA workflow; it is not a configurable clinical validation framework.

## Report a problem

Open a [bug report](https://github.com/chenmei24/clinical-imaging-data-qa-demo/issues/new?template=bug_report.yml) with your operating system, Python version, command, expected behavior, and a minimal **fictional** CSV. Do not attach patient-identifiable or confidential project data. You can describe a custom-schema request in a feature request; changes to an actual client's rules belong in a separately agreed scope.

## Run checks

Python 3.10+ and the standard library are sufficient. From the repository root:

```bash
python -m unittest discover -s tests -v
python scripts/audit_csv.py --input examples/01_synthetic_source.csv --output-dir output
```

CI runs the tests on Linux and Windows with Python 3.10 and 3.13. Symlink tests skip with an explicit reason when the operating system does not grant permission to create them.

## Propose a change

1. Use a branch and explain the behavior being changed.
2. Add a focused regression test for a data-preservation or correctness fix.
3. Keep the source read only, all records retained, transformations documented, and unresolved values visible.
4. Preserve the committed example's **120 rows / 8 events / 7 open queries / 1 conversion** unless a separately explained change to the demonstration is intended.
5. Update both README languages and the data dictionary when a fixed input rule changes. Add a short changelog entry.

The data dictionary describes the implementation; editing it alone does not change program behavior. Avoid adding clinical claims, invented customer outcomes, or large dependencies for this small demonstration.

Contributions are provided under the repository's [MIT license](LICENSE).
