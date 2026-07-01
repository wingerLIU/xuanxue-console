#!/usr/bin/env python3
"""Tests for flow_timing_report generator and validator."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = PROJECT_ROOT / "scripts" / "build_flow_timing_report.py"
VALIDATE_SCRIPT = PROJECT_ROOT / "scripts" / "validate_flow_timing_report.py"


def combo_fixture() -> dict:
    return {
        "schema_version": "0.2.0",
        "module": "combo",
        "input": {},
        "facts": {
            "modules": [
                {
                    "schema_version": "0.2.0",
                    "module": "bazi",
                    "input": {},
                    "facts": {
                        "pillars": {"year": "辛未", "month": "丙申", "day": "丁巳", "hour": "辛丑"},
                        "day_master": {"gan": "丁", "wuxing": "火"},
                        "dayun": [
                            {"gan_zhi": "壬辰", "start_year": 2023, "end_year": 2032},
                        ],
                    },
                    "warnings": [],
                    "uncertainties": [],
                    "interpretation_hints": [],
                    "calibration_questions": [],
                    "raw": {},
                }
            ]
        },
        "warnings": [],
        "uncertainties": [],
        "interpretation_hints": [],
        "calibration_questions": [],
        "raw": {},
    }


class FlowTimingReportTests(unittest.TestCase):
    def run_validator(self, report: Path, *keywords: str, min_days: int = 10) -> tuple[subprocess.CompletedProcess[str], dict]:
        command = [sys.executable, "-X", "utf8", str(VALIDATE_SCRIPT), str(report), "--min-days", str(min_days)]
        for keyword in keywords:
            command.extend(["--case-keyword", keyword])
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
            env=env,
        )
        return proc, json.loads(proc.stdout)

    @unittest.skipIf(importlib.util.find_spec("lunar_python") is None, "lunar-python not installed")
    def test_build_flow_timing_report_outputs_valid_md_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            facts = root / "combo.json"
            md = root / "flow.md"
            html = root / "flow.html"
            machine = root / "flow.json"
            facts.write_text(json.dumps(combo_fixture(), ensure_ascii=False), encoding="utf-8")
            keywords = ["OPC", "小闭环", "报价", "对上汇报", "Agent项目包"]
            command = [
                sys.executable,
                "-X",
                "utf8",
                str(BUILD_SCRIPT),
                "--facts-json",
                str(facts),
                "--start",
                "2026-07-02",
                "--days",
                "12",
                "--reader-name",
                "liujiang",
                "--output-md",
                str(md),
                "--output-html",
                str(html),
                "--json-output",
                str(machine),
            ]
            for keyword in keywords:
                command.extend(["--case-keyword", keyword])
            proc = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertEqual(result["days"], 12)
            self.assertTrue(md.exists())
            self.assertTrue(html.exists())
            self.assertTrue(machine.exists())
            markdown = md.read_text(encoding="utf-8")
            self.assertIn("今天就看这件事", markdown)
            self.assertIn("OPC", markdown)
            self.assertIn("小闭环", markdown)
            for report in [md, html]:
                check, validation = self.run_validator(report, *keywords, min_days=12)
                self.assertEqual(check.returncode, 0, validation)
                self.assertTrue(validation["passed"])

    def test_validate_flow_timing_report_rejects_generic_daily_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "bad.md"
            report.write_text(
                "\n".join(
                    [
                        "# 流月流日行动节奏报告",
                        "## 每日表",
                        "| 日期 | 流月 | 流日 | 今天就看这件事 | 现实动作 | 盘面触发 |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| 2026-07-02 | 甲午 | 丁丑 | 注意沟通 | 适合推进 | 流月甲午、流日丁丑 |",
                    ]
                ),
                encoding="utf-8",
            )
            proc, result = self.run_validator(report, "OPC", "小闭环", "报价", "对上汇报", "Agent项目包", min_days=1)
            self.assertNotEqual(proc.returncode, 0)
            joined = "\n".join(result["failures"])
            self.assertIn("banned generic phrases", joined)
            self.assertIn("weak generic action", joined)


if __name__ == "__main__":
    unittest.main()
