"""Contract tests for complete reports, findings and scanner failures."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("summarize_dependency_audits.py")
SPEC = importlib.util.spec_from_file_location("audit_summary", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditSummaryTests(unittest.TestCase):
    def test_npm_clean(self):
        self.assertEqual(
            audit.summarize_npm({"vulnerabilities": {}}, {})["status"], "clean"
        )

    def test_npm_keeps_dependency_and_installed_version(self):
        report = {
            "vulnerabilities": {
                "example": {
                    "severity": "high",
                    "isDirect": False,
                    "nodes": ["node_modules/example"],
                    "via": ["upstream"],
                    "fixAvailable": False,
                }
            }
        }
        lock = {"packages": {"node_modules/example": {"version": "1.0.0", "dev": True}}}
        summary = audit.summarize_npm(report, lock)
        self.assertEqual(summary["status"], "findings")
        self.assertEqual(summary["findings"][0]["instances"][0]["version"], "1.0.0")
        self.assertTrue(summary["findings"][0]["instances"][0]["dev"])
        self.assertFalse(summary["findings"][0]["fix_available"])

    def test_npm_server_error_is_not_clean(self):
        with self.assertRaises(ValueError):
            audit.summarize_npm({"error": {"code": "E503"}}, {})

    def test_npm_unknown_lock_node_is_error(self):
        with self.assertRaises(ValueError):
            audit.summarize_npm({"vulnerabilities": {"x": {"nodes": ["missing"]}}}, {})

    def test_python_clean(self):
        self.assertEqual(
            audit.summarize_python({"dependencies": []})["status"], "clean"
        )

    def test_python_distinguishes_pairs_and_unique_advisories(self):
        report = {
            "dependencies": [
                {"name": n, "version": "1.0", "vulns": [{"id": "TEST-1"}]}
                for n in ["first", "second"]
            ]
        }
        summary = audit.summarize_python(report)
        self.assertEqual(summary["package_advisory_pairs"], 2)
        self.assertEqual(summary["unique_advisory_ids"], ["TEST-1"])

    def test_python_skipped_dependency_is_not_clean(self):
        report = {"dependencies": [{"name": "unknown", "skip_reason": "not available"}]}
        self.assertEqual(audit.summarize_python(report)["status"], "error")

    def test_cli_exit_codes_and_error_report(self):
        cases = [
            ({"dependencies": []}, 0),
            (
                {
                    "dependencies": [
                        {"name": "x", "version": "1", "vulns": [{"id": "TEST"}]}
                    ]
                },
                1,
            ),
            ({"unexpected": []}, 2),
        ]
        with tempfile.TemporaryDirectory() as directory:
            source, target = (
                Path(directory) / "input.json",
                Path(directory) / "summary.json",
            )
            for report, expected in cases:
                with self.subTest(expected=expected):
                    source.write_text(json.dumps(report), encoding="utf-8")
                    result = subprocess.run(  # noqa: S603 - fixed interpreter and local test script
                        [
                            sys.executable,
                            str(SCRIPT),
                            "--python-report",
                            str(source),
                            "--output",
                            str(target),
                        ],
                        check=False,
                    )
                    self.assertEqual(result.returncode, expected)
                    summary = json.loads(target.read_text(encoding="utf-8"))
                    self.assertFalse(summary["exploitability_assessed"])
                    self.assertFalse(summary["findings_accepted"])


if __name__ == "__main__":
    unittest.main()
