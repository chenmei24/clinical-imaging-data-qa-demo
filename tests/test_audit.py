"""Exercise the user-facing demo workflow and its data-preservation contract."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_csv import audit  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


if __name__ == "__main__":
    unittest.main()
