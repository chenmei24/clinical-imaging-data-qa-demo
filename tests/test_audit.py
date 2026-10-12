"""Exercise the user-facing demo workflow and its data-preservation contract."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_csv  # noqa: E402
from audit_csv import OUTPUT_NAMES, REQUIRED_FIELDS, audit  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_source(path: Path, **overrides: str) -> None:
    row = dict(zip(REQUIRED_FIELDS, ("SYN-X", "30", "F", "MRI", "2.7", "cm", "2025-01-01")))
    row.update(overrides)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def create_symlink(test: unittest.TestCase, link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError as error:
        test.skipTest(f"Symlink creation unavailable on this platform: {error}")


class AuditDemoTests(unittest.TestCase):
    def test_regenerates_portfolio_examples_without_changing_source(self) -> None:
        source_path = ROOT / "examples" / "01_synthetic_source.csv"
        original_bytes = source_path.read_bytes()
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            output = Path(temp)
            summary = audit(source_path, output)
            self.assertEqual((summary["source_rows"], summary["output_rows"]), (120, 120))
            self.assertEqual((summary["qa_events"], summary["open_queries"], summary["documented_changes"]), (8, 7, 1))
            for name in ("02_standardized_with_flags.csv", "03_query_log.csv", "04_change_log.csv"):
                self.assertEqual(read_csv(output / name), read_csv(ROOT / "examples" / name))
            self.assertEqual(
                json.loads((output / "05_summary.json").read_text(encoding="utf-8")),
                json.loads((ROOT / "examples" / "05_summary.json").read_text(encoding="utf-8")),
            )
        self.assertEqual(source_path.read_bytes(), original_bytes)

    def test_flags_are_retained_and_conversion_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            output = Path(temp)
            audit(ROOT / "examples" / "01_synthetic_source.csv", output)
            rows = read_csv(output / "02_standardized_with_flags.csv")
            queries = read_csv(output / "03_query_log.csv")
            self.assertEqual(rows[9]["age_years"], "155")
            self.assertEqual(rows[47]["age_years"], "")
            self.assertEqual(rows[79]["lesion_value"], "27.0")
            self.assertEqual(rows[79]["lesion_unit"], "mm")
            self.assertEqual(rows[118]["record_id"], rows[0]["record_id"])
            self.assertEqual(sum(q["issue"] == "Duplicate ID" for q in queries), 2)

    def test_nonfinite_measurement_is_queried_not_converted(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(("record_id", "age_years", "sex_code", "modality",
                                 "lesion_value", "lesion_unit", "scan_date"))
                writer.writerow(("SYN-X", "30", "F", "MRI", "NaN", "cm", "2025-01-01"))
            audit(source, directory / "result")
            row = read_csv(directory / "result" / "02_standardized_with_flags.csv")[0]
            self.assertEqual((row["lesion_value"], row["lesion_unit"]), ("NaN", "cm"))
            self.assertEqual(read_csv(directory / "result" / "04_change_log.csv"), [])
            issues = {item["issue"] for item in read_csv(directory / "result" / "03_query_log.csv")}
            self.assertIn("Invalid measurement", issues)
            self.assertIn("Unexpected unit", issues)

    def test_cm_conversion_preserves_small_values_and_full_precision(self) -> None:
        cases = {
            "0.004": "0.04",
            "2.7": "27.0",
            "2.700": "27.00",
            "0.12345678901234567890123456789012345": "1.2345678901234567890123456789012345",
            "1e1000": "1E+1001",
        }
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            for original, expected in cases.items():
                with self.subTest(original=original):
                    write_source(source, lesion_value=original)
                    source_bytes = source.read_bytes()
                    summary = audit(source, directory / "result")
                    row = read_csv(directory / "result" / OUTPUT_NAMES[0])[0]
                    self.assertEqual((row["lesion_value"], row["lesion_unit"]), (expected, "mm"))
                    change = read_csv(directory / "result" / OUTPUT_NAMES[2])[0]
                    self.assertEqual((change["before"], change["after"]), (f"{original} cm", f"{expected} mm"))
                    self.assertEqual(summary["documented_changes"], 1)
                    self.assertEqual(source.read_bytes(), source_bytes)

    def test_invalid_and_nonpositive_cm_values_are_retained(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            for value in ("-2", "0", "-0", "NaN", "sNaN", "Infinity", "-Infinity", "", "abc", "1e999999999999999999"):
                with self.subTest(value=value):
                    write_source(source, lesion_value=value)
                    audit(source, directory / "result")
                    row = read_csv(directory / "result" / OUTPUT_NAMES[0])[0]
                    self.assertEqual((row["lesion_value"], row["lesion_unit"]), (value, "cm"))
                    self.assertEqual(read_csv(directory / "result" / OUTPUT_NAMES[2]), [])
                    self.assertTrue(read_csv(directory / "result" / OUTPUT_NAMES[1]))

    def test_header_can_be_reordered_and_output_remains_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(reversed(REQUIRED_FIELDS)))
                writer.writeheader()
                writer.writerow(dict(zip(REQUIRED_FIELDS, ("SYN-X", "30", "F", "MRI", "5", "mm", "2025-01-01"))))
            original = source.read_bytes()
            audit(source, directory / "result")
            with (directory / "result" / OUTPUT_NAMES[0]).open(encoding="utf-8", newline="") as handle:
                self.assertEqual(next(csv.reader(handle)), list(REQUIRED_FIELDS))
            self.assertEqual(read_csv(directory / "result" / OUTPUT_NAMES[0])[0]["record_id"], "SYN-X")
            self.assertEqual(source.read_bytes(), original)

    def test_bad_headers_have_specific_diagnostics_and_write_nothing(self) -> None:
        cases = (
            (list(REQUIRED_FIELDS[:-1]), "missing columns: scan_date"),
            (list(REQUIRED_FIELDS) + ["surprise"], "unexpected columns: 'surprise'"),
            (list(REQUIRED_FIELDS) + ["record_id"], "duplicate columns: 'record_id'"),
        )
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            output = directory / "result"
            for fields, message in cases:
                with self.subTest(fields=fields):
                    with source.open("w", encoding="utf-8", newline="") as handle:
                        csv.writer(handle).writerow(fields)
                    original = source.read_bytes()
                    with self.assertRaises(ValueError) as context:
                        audit(source, output)
                    self.assertIn(message, str(context.exception))
                    self.assertFalse(output.exists())
                    self.assertEqual(source.read_bytes(), original)

    def test_empty_inputs_and_malformed_rows_write_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            output = directory / "result"
            header = ",".join(REQUIRED_FIELDS) + "\n"
            cases = (
                ("", "no CSV header"),
                (header, "no data rows"),
                (header + "SYN-X,30,F,MRI,5,mm\n", "Source row 2 is missing columns: scan_date"),
                (header + "SYN-X,30,F,MRI,5,mm,2025-01-01,extra\n", "Source row 2 has extra values"),
                (header + 'SYN-X,30,F,MRI,"unterminated\n', "unexpected end of data"),
            )
            for contents, message in cases:
                with self.subTest(message=message):
                    source.write_text(contents, encoding="utf-8")
                    original = source.read_bytes()
                    with self.assertRaises((ValueError, csv.Error)) as context:
                        audit(source, output)
                    self.assertIn(message, str(context.exception))
                    self.assertFalse(output.exists())
                    self.assertEqual(source.read_bytes(), original)

    def test_input_cannot_be_any_delivery_file(self) -> None:
        for name in OUTPUT_NAMES:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                source = directory / name
                write_source(source)
                original = source.read_bytes()
                with self.assertRaisesRegex(ValueError, "overwrite the input"):
                    audit(source, directory)
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(sorted(path.name for path in directory.iterdir()), [name])

    def test_resolved_parent_path_cannot_overwrite_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "nested").mkdir()
            source = directory / OUTPUT_NAMES[0]
            write_source(source)
            original = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "overwrite the input"):
                audit(source, directory / "nested" / "..")
            self.assertEqual(source.read_bytes(), original)

    def test_input_symlink_cannot_bypass_collision_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / OUTPUT_NAMES[0]
            write_source(source)
            alias = directory / "source.csv"
            create_symlink(self, alias, source)
            original = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "overwrite the input"):
                audit(alias, directory)
            self.assertEqual(source.read_bytes(), original)

    def test_output_symlink_cannot_overwrite_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            write_source(source)
            output = directory / "result"
            output.mkdir()
            create_symlink(self, output / OUTPUT_NAMES[1], source)
            original = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "overwrite the input"):
                audit(source, output)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(len(list(output.iterdir())), 1)

    def test_output_directory_symlink_cannot_bypass_collision_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / OUTPUT_NAMES[3]
            write_source(source)
            alias = directory / "alias"
            create_symlink(self, alias, directory, directory=True)
            original = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "overwrite the input"):
                audit(source, alias)
            self.assertEqual(source.read_bytes(), original)

    def test_hardlink_to_input_cannot_bypass_collision_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            write_source(source)
            output = directory / "result"
            output.mkdir()
            try:
                os.link(source, output / OUTPUT_NAMES[2])
            except OSError as error:
                self.skipTest(f"Hardlink creation unavailable: {error}")
            original = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "overwrite the input"):
                audit(source, output)
            self.assertEqual(source.read_bytes(), original)

    def test_delivery_files_cannot_alias_one_another(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            write_source(source)
            output = directory / "result"
            output.mkdir()
            first = output / OUTPUT_NAMES[0]
            first.write_text("previous output", encoding="utf-8")
            try:
                os.link(first, output / OUTPUT_NAMES[1])
            except OSError as error:
                self.skipTest(f"Hardlink creation unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "Output paths refer to the same file"):
                audit(source, output)
            self.assertEqual(first.read_text(encoding="utf-8"), "previous output")
            self.assertEqual(len(list(output.iterdir())), 2)

    def test_unusable_destination_is_rejected_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            write_source(source)
            output = directory / "result"
            output.mkdir()
            (output / OUTPUT_NAMES[3]).mkdir()
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                audit(source, output)
            self.assertEqual(len(list(output.iterdir())), 1)

    def test_staging_failure_preserves_existing_delivery_and_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            write_source(source)
            original = source.read_bytes()
            output = directory / "result"
            output.mkdir()
            for name in OUTPUT_NAMES:
                (output / name).write_bytes(b"previous output\n")
            real_writer = audit_csv.write_csv
            calls = 0

            def fail_second_write(*args: object) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated staging failure")
                real_writer(*args)

            with patch.object(audit_csv, "write_csv", side_effect=fail_second_write):
                with self.assertRaisesRegex(OSError, "simulated staging failure"):
                    audit(source, output)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(sorted(path.name for path in output.iterdir()), sorted(OUTPUT_NAMES))
            self.assertTrue(all((output / name).read_bytes() == b"previous output\n" for name in OUTPUT_NAMES))

    def test_publish_failure_restores_previous_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            write_source(source)
            output = directory / "result"
            output.mkdir()
            for name in OUTPUT_NAMES:
                (output / name).write_bytes(b"previous output\n")
            real_replace = os.replace
            failed = False

            def fail_summary_publish(src: Path, dst: Path) -> None:
                nonlocal failed
                if Path(src).name == OUTPUT_NAMES[3] and not failed:
                    failed = True
                    raise OSError("simulated publish failure")
                real_replace(src, dst)

            with patch.object(audit_csv.os, "replace", side_effect=fail_summary_publish):
                with self.assertRaisesRegex(OSError, "simulated publish failure"):
                    audit(source, output)
            self.assertTrue(all((output / name).read_bytes() == b"previous output\n" for name in OUTPUT_NAMES))
            self.assertEqual(sorted(path.name for path in output.iterdir()), sorted(OUTPUT_NAMES))

    def test_cli_reports_invalid_input_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            source.write_text("", encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "audit_csv.py"), "--input", str(source),
                 "--output-dir", str(directory / "result")],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(process.returncode, 2)
            self.assertIn("Audit failed: Input has no CSV header", process.stderr)
            self.assertNotIn("Traceback", process.stderr)
            self.assertFalse((directory / "result").exists())

    def test_failed_rollback_preserves_recovery_files_and_restores_other_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.csv"
            write_source(source)
            original = source.read_bytes()
            output = directory / "result"
            output.mkdir()
            for name in OUTPUT_NAMES:
                (output / name).write_bytes(b"previous output\n")
            real_replace = os.replace

            def fail_publish_and_one_restore(src: Path, dst: Path) -> None:
                name = Path(src).name
                if name in (OUTPUT_NAMES[3], OUTPUT_NAMES[2] + ".previous"):
                    raise OSError("simulated persistent replacement failure")
                real_replace(src, dst)

            with patch.object(audit_csv.os, "replace", side_effect=fail_publish_and_one_restore):
                with self.assertRaises(audit_csv.DeliveryRecoveryError) as context:
                    audit(source, output)
            self.assertIn("Recovery files are preserved at", str(context.exception))
            recovery = [path for path in output.iterdir() if path.is_dir()]
            self.assertEqual(len(recovery), 1)
            self.assertEqual(
                (recovery[0] / (OUTPUT_NAMES[2] + ".previous")).read_bytes(), b"previous output\n"
            )
            for name in (OUTPUT_NAMES[0], OUTPUT_NAMES[1], OUTPUT_NAMES[3]):
                self.assertEqual((output / name).read_bytes(), b"previous output\n")
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
