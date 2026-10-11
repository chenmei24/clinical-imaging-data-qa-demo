"""Audit a de-identified CSV matching the synthetic demo schema.

All rows are retained. Only a known, documented cm-to-mm conversion is applied.
This is an example workflow, not a clinical validation or diagnostic tool.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path


REQUIRED_FIELDS = (
    "record_id",
    "age_years",
    "sex_code",
    "modality",
    "lesion_value",
    "lesion_unit",
    "scan_date",
)
QUERY_FIELDS = ("source_row", "record_id", "field", "issue", "action")
CHANGE_FIELDS = ("source_row", "record_id", "field", "before", "after", "reason")


def write_csv(path: Path, rows: list[dict[str, object]], fields: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def audit(input_path: Path, output_dir: Path) -> dict[str, object]:
    """Write an auditable delivery package and return its summary."""
    # `absolute()` avoids a Windows sandbox issue with strict realpath resolution.
    input_path = input_path.absolute()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != REQUIRED_FIELDS:
            raise ValueError(f"Expected columns in this order: {', '.join(REQUIRED_FIELDS)}")
        source = list(reader)

    if not source:
        raise ValueError("Input has no data rows")
    if any(None in row or any(value is None for value in row.values()) for row in source):
        raise ValueError("Input contains a row with a missing or extra column")

    standardized: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    changes: list[dict[str, object]] = []
    seen: set[str] = set()

    def flag(row_number: int, record_id: str, field: str, issue: str, action: str) -> None:
        issues.append(dict(source_row=row_number, record_id=record_id, field=field,
                           issue=issue, action=action))

    for row_number, original in enumerate(source, start=2):
        record: dict[str, object] = original.copy()
        record_id = str(record["record_id"])

        if not record_id:
            flag(row_number, record_id, "record_id", "Missing ID", "Retained; source owner to resolve")
        elif record_id in seen:
            flag(row_number, record_id, "record_id", "Duplicate ID", "Retained; source owner to resolve")
        seen.add(record_id)

        age = str(record["age_years"])
        if age == "":
            flag(row_number, record_id, "age_years", "Missing age", "Retained blank; no imputation")
        elif not re.fullmatch(r"[0-9]+", age) or not 0 <= int(age) <= 120:
            flag(row_number, record_id, "age_years", "Age outside 0-120", "Retained; source owner to verify")

        if record["sex_code"] not in {"F", "M"}:
            flag(row_number, record_id, "sex_code", "Unexpected code", "Retained; check data dictionary")
        if record["modality"] not in {"CT", "MRI"}:
            flag(row_number, record_id, "modality", "Unexpected modality", "Retained; check data dictionary")

        value_text = str(record["lesion_value"])
        try:
            value = float(value_text)
        except ValueError:
            value = None

        unit = str(record["lesion_unit"])
        if unit == "cm" and value is not None and math.isfinite(value):
            converted = round(value * 10, 1)
            record["lesion_value"] = str(converted)
            record["lesion_unit"] = "mm"
            flag(row_number, record_id, "lesion_unit", "Unit conversion",
                 f"Converted {value_text} cm to {converted} mm")
            changes.append(dict(source_row=row_number, record_id=record_id,
                                field="lesion_value / lesion_unit", before=f"{value_text} cm",
                                after=f"{converted} mm", reason="cm-to-mm normalization"))
        elif unit != "mm":
            flag(row_number, record_id, "lesion_unit", "Unexpected unit", "Retained; source owner to verify")

        if value is None or not math.isfinite(value) or value <= 0:
            issue = "Nonpositive measurement" if value is not None and math.isfinite(value) else "Invalid measurement"
            flag(row_number, record_id, "lesion_value", issue,
                 "Retained; source owner to verify")

        scan_date = str(record["scan_date"])
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", scan_date):
                raise ValueError("not ISO format")
            date.fromisoformat(scan_date)
        except ValueError:
            flag(row_number, record_id, "scan_date", "Invalid ISO date", "Retained; source owner to verify")

        standardized.append(record)

    if len(standardized) != len(source):
        raise AssertionError("A source row was lost")

    write_csv(output_dir / "02_standardized_with_flags.csv", standardized, REQUIRED_FIELDS)
    write_csv(output_dir / "03_query_log.csv", issues, QUERY_FIELDS)
    write_csv(output_dir / "04_change_log.csv", changes, CHANGE_FIELDS)

    counts = Counter(str(item["issue"]) for item in issues)
    summary: dict[str, object] = {
        "dataset": "synthetic demonstration; no real patient data claimed",
        "source_rows": len(source),
        "output_rows": len(standardized),
        "rows_dropped": 0,
        "qa_events": len(issues),
        "open_queries": len(issues) - len(changes),
        "documented_changes": len(changes),
        "issue_counts": dict(sorted(counts.items())),
    }
    (output_dir / "05_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV matching the demo schema")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for QA deliverables")
    args = parser.parse_args()
    summary = audit(args.input, args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
