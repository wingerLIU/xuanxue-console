#!/usr/bin/env python3
"""Source register, liveness, and documentation tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECK_SOURCE_URLS_SCRIPT = Path(__file__).with_name("check_source_urls.py")
AUDIT_SOURCE_DOCUMENTATION_SCRIPT = Path(__file__).with_name("audit_source_documentation.py")


class XuanxueSourceTests(unittest.TestCase):
    def test_source_url_check_can_write_external_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "runtime" / "source_liveness.json"
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(CHECK_SOURCE_URLS_SCRIPT),
                    "--dry-run",
                    "--type",
                    "classical_text",
                    "--evidence-mode",
                    "online_public_entry",
                    "--max-sources",
                    "1",
                    "--output",
                    str(output),
                    "--json",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
                env=env,
            )
            result = json.loads(proc.stdout)
            self.assertTrue(output.exists())
            self.assertFalse(output.resolve().is_relative_to(PROJECT_ROOT.resolve()))
            snapshot = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(snapshot["passed"])
            self.assertTrue(snapshot["dry_run"])
            self.assertEqual(snapshot["filters"]["type"], ["classical_text"])
            self.assertEqual(snapshot["checked_sources"], 1)
            self.assertEqual(result["checked_sources"], snapshot["checked_sources"])

    def test_source_documentation_audit_passes(self) -> None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(AUDIT_SOURCE_DOCUMENTATION_SCRIPT)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
            env=env,
        )
        result = json.loads(proc.stdout)
        self.assertTrue(result["passed"])
        self.assertGreaterEqual(result["documented_classical_sources"], 18)
        self.assertGreaterEqual(result["documented_modern_sources"], 4)
        self.assertIn("active_backlog_source_ids", result)
        self.assertIn("tracked_backlog_source_ids", result)
        self.assertIn("research_backlog_items", result)
        self.assertIn("SRC-ZIWEI-DOUSHU-QUANJI", result["active_backlog_source_ids"])
        self.assertIn("SRC-BAZI-SHENFENG-TONGKAO", result["tracked_backlog_source_ids"])
        self.assertIn("source_found_curated_boundary", result["backlog_status_counts"])
        self.assertEqual(result["failures"], [])


if __name__ == "__main__":
    unittest.main()
