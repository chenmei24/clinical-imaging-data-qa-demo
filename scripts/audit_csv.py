"""Audit a de-identified CSV matching the synthetic demo schema.

All rows are retained. Only a known, documented cm-to-mm conversion is applied.
This is an example workflow, not a clinical validation or diagnostic tool.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tempfile import mkdtemp


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
OUTPUT_NAMES = (
    "02_standardized_with_flags.csv",
    "03_query_log.csv",
    "04_change_log.csv",
    "05_summary.json",
)


class DeliveryRecoveryError(OSError):
    """A failed rollback whose prior delivery files remain in staging."""


def write_csv(path: Path, rows: list[dict[str, object]], fields: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def check_output_paths(input_path: Path, output_dir: Path) -> None:
    """Reject source aliases and unusable destinations before writing any file."""
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"Output directory is not a directory: {output_dir}")
    targets = [output_dir / name for name in OUTPUT_NAMES]
    resolved: list[Path] = []
    for target in targets:
        destination = target.resolve()
        if destination == input_path or (target.exists() and target.samefile(input_path)):
            raise ValueError(f"Output path would overwrite the input file: {target}")
        # Reject all output symlinks, including broken links. It is safer to make
        # the destination explicit than to write through an unexpected alias.
        if target.is_symlink():
            raise ValueError(f"Output path must not be a symbolic link: {target}")
        if target.exists() and not target.is_file():
            raise ValueError(f"Output path is not a regular file: {target}")
        for previous, previous_resolved in zip(targets[:len(resolved)], resolved):
            if destination == previous_resolved or (
                target.exists() and previous.exists() and target.samefile(previous)
            ):
                raise ValueError(f"Output paths refer to the same file: {previous}, {target}")
        resolved.append(destination)


def validate_header(fields: list[str] | None) -> None:
    if fields is None:
        raise ValueError("Input has no CSV header")
    missing = [field for field in REQUIRED_FIELDS if field not in fields]
    unexpected = list(dict.fromkeys(field for field in fields if field not in REQUIRED_FIELDS))
    duplicates = [field for field, count in Counter(fields).items() if count > 1]
    problems = []
    if missing:
        problems.append(f"missing columns: {', '.join(missing)}")
    if unexpected:
        problems.append(f"unexpected columns: {', '.join(repr(field) for field in unexpected)}")
    if duplicates:
        problems.append(f"duplicate columns: {', '.join(repr(field) for field in duplicates)}")
    if problems:
        raise ValueError("Invalid CSV header; " + "; ".join(problems))


def convert_cm(value: Decimal) -> str:
    """Shift the decimal exponent exactly, without context rounding."""
    parts = value.as_tuple()
    converted = Decimal((parts.sign, parts.digits, int(parts.exponent) + 1))
    text = str(converted)
    # Keep the existing demonstration's 2.7 -> 27.0 representation, while
    # retaining all meaningful decimal places and bounded scientific notation.
    if "." not in text and "E" not in text:
        text += ".0"
    return text


def publish_outputs(staging: Path, output_dir: Path) -> None:
    """Replace complete files; restore prior outputs if replacement fails."""
    backups: dict[str, Path] = {}
    published: list[str] = []
    # Copy every prior file before replacing any destination. A backup failure
    # therefore leaves the entire prior delivery in place.
    for name in OUTPUT_NAMES:
        target = output_dir / name
        if target.exists():
            backup = staging / (name + ".previous")
            shutil.copyfile(target, backup)
            backups[name] = backup
    try:
        for name in OUTPUT_NAMES:
            target = output_dir / name
            os.replace(staging / name, target)
            published.append(name)
    except OSError as error:
        rollback_errors: list[str] = []
        for name in reversed(published):
            target = output_dir / name
            try:
                if name in backups:
                    os.replace(backups[name], target)
                else:
                    target.unlink()
            except OSError as rollback_error:
                rollback_errors.append(f"{name}: {rollback_error}")
        if rollback_errors:
            raise DeliveryRecoveryError(
                f"Delivery publication failed ({error}); rollback was incomplete. "
                f"Recovery files are preserved at {staging}; " + "; ".join(rollback_errors)
            ) from error
        raise


def audit(input_path: Path, output_dir: Path) -> dict[str, object]:
    """Write an auditable delivery package and return its summary."""
    input_path = input_path.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    output_dir = output_dir.resolve()
    check_output_paths(input_path, output_dir)

    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        validate_header(reader.fieldnames)
        source = list(reader)

    if not source:
        raise ValueError("Input has no data rows")
    for row_number, row in enumerate(source, start=2):
        if None in row:
            raise ValueError(f"Source row {row_number} has extra values beyond the header")
        missing_values = [field for field, value in row.items() if value is None]
        if missing_values:
            raise ValueError(f"Source row {row_number} is missing columns: {', '.join(missing_values)}")

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
        elif (not re.fullmatch(r"[0-9]+", age)
              or len(age.lstrip("0")) > 3 or int(age.lstrip("0") or "0") > 120):
            flag(row_number, record_id, "age_years", "Age outside 0-120", "Retained; source owner to verify")

        if record["sex_code"] not in {"F", "M"}:
            flag(row_number, record_id, "sex_code", "Unexpected code", "Retained; check data dictionary")
        if record["modality"] not in {"CT", "MRI"}:
            flag(row_number, record_id, "modality", "Unexpected modality", "Retained; check data dictionary")

        value_text = str(record["lesion_value"])
        try:
            value = Decimal(value_text)
        except InvalidOperation:
            value = None

        unit = str(record["lesion_unit"])
        converted = None
        if unit == "cm" and value is not None and value.is_finite() and value > 0:
            try:
                converted = convert_cm(value)
            except InvalidOperation:
                # Even Decimal has finite exponent limits. Preserve the text
                # and query measurements that cannot be represented in mm.
                value = None
        if converted is not None:
            record["lesion_value"] = converted
            record["lesion_unit"] = "mm"
            flag(row_number, record_id, "lesion_unit", "Unit conversion",
                 f"Converted {value_text} cm to {converted} mm")
            changes.append(dict(source_row=row_number, record_id=record_id,
                                field="lesion_value / lesion_unit", before=f"{value_text} cm",
                                after=f"{converted} mm", reason="cm-to-mm normalization"))
        elif unit != "mm":
            flag(row_number, record_id, "lesion_unit", "Unexpected unit", "Retained; source owner to verify")

        if value is None or not value.is_finite() or value <= 0:
            issue = "Nonpositive measurement" if value is not None and value.is_finite() else "Invalid measurement"
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
    # Complete validation and all serialization before replacing any delivery
    # file. A staging failure leaves existing outputs and the source untouched.
    check_output_paths(input_path, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(mkdtemp(prefix=".audit-staging-", dir=output_dir))
    preserve_recovery = False
    try:
        write_csv(staging / OUTPUT_NAMES[0], standardized, REQUIRED_FIELDS)
        write_csv(staging / OUTPUT_NAMES[1], issues, QUERY_FIELDS)
        write_csv(staging / OUTPUT_NAMES[2], changes, CHANGE_FIELDS)
        (staging / OUTPUT_NAMES[3]).write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        check_output_paths(input_path, output_dir)
        publish_outputs(staging, output_dir)
    except DeliveryRecoveryError:
        preserve_recovery = True
        raise
    finally:
        if not preserve_recovery:
            shutil.rmtree(staging)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV matching the demo schema")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for QA deliverables")
    args = parser.parse_args()
    try:
        summary = audit(args.input, args.output_dir)
    except (OSError, ValueError, UnicodeError, csv.Error) as error:
        parser.exit(2, f"Audit failed: {error}\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
