#!/usr/bin/env python3
"""Retrospective promotion and coverage preview tests for xuanxue-console."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMOTE_RETRO_SCRIPT = Path(__file__).with_name("promote_case_retrospective.py")
AUDIT_CASE_RETROSPECTIVES_SCRIPT = Path(__file__).with_name("audit_case_retrospectives.py")
AUDIT_KNOWLEDGE_COVERAGE_SCRIPT = Path(__file__).with_name("audit_knowledge_coverage.py")


def write_retrospective_control_files(retro_dir: Path) -> None:
    retro_dir.mkdir(parents=True, exist_ok=True)
    body = "去隐私复盘控制文件。只用于测试目录，不包含客户资料、本机路径、出生资料或交付正文。" * 4
    for name in ["README.md", "promotion-protocol.md", "template.md"]:
        (retro_dir / name).write_text(f"# {name}\n\n{body}\n", encoding="utf-8")


def candidate_base(*, retro_id: str, domains: list[str], target_artifacts: list[str]) -> dict:
    return {
        "schema_version": "0.1.0",
        "id": retro_id,
        "title": "去隐私单测复盘",
        "status": "candidate",
        "human_approved": False,
        "approved_by": "",
        "privacy": {
            "deidentified": True,
            "contains_birth_data": False,
            "contains_client_name": False,
            "contains_local_paths": False,
            "contains_delivery_text": False,
        },
        "source_case": {
            "case_type": "relationship-rich-report" if "relationship" in domains else "xuanxue-longform",
            "date_bucket": "redacted-quarter",
            "raw_material_location": "external-only",
            "case_id_hash": "casehash",
            "run_id_hash": "runhash",
        },
        "evidence_summary": "抽象复盘机制，只用于验证脚本行为。",
        "domains": domains,
        "target_artifacts": target_artifacts,
        "promotions": [
            {
                "artifact": target_artifacts[0],
                "change_type": "unit_test",
                "summary": "验证复盘晋升和覆盖预览。",
            }
        ],
        "counterexamples": ["没有人工确认时不能晋升。"],
        "limits": ["这是脚本单测，不代表真实案例复盘。"],
    }


class RetrospectivePromotionTests(unittest.TestCase):
    def test_promote_retrospective_defaults_to_curated(self) -> None:
        candidate = candidate_base(
            retro_id="CR-20990101-unit-retro-promote",
            domains=["writing"],
            target_artifacts=["knowledge/writing/reader-rich-report.md"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            retro_dir = Path(tmp) / "retrospectives"
            write_retrospective_control_files(retro_dir)
            candidate_path = Path(tmp) / "candidate.json"
            candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
            promoted = retro_dir / "CR-20990101-unit-retro-promote.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE_RETRO_SCRIPT),
                    "--candidate",
                    str(candidate_path),
                    "--approved-by",
                    "unit-test",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            item = json.loads(promoted.read_text(encoding="utf-8"))
            self.assertTrue(item["human_approved"])
            self.assertEqual(item["status"], "curated")
            self.assertEqual(item["approved_by"], "unit-test")

    def test_promote_retrospective_dry_run_does_not_write(self) -> None:
        candidate = candidate_base(
            retro_id="CR-20990101-unit-retro-dry-run",
            domains=["writing"],
            target_artifacts=["knowledge/writing/reader-rich-report.md"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            retro_dir = Path(tmp) / "retrospectives"
            write_retrospective_control_files(retro_dir)
            candidate_path = Path(tmp) / "candidate.json"
            candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
            promoted = retro_dir / "CR-20990101-unit-retro-dry-run.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE_RETRO_SCRIPT),
                    "--candidate",
                    str(candidate_path),
                    "--approved-by",
                    "unit-test",
                    "--retro-dir",
                    str(retro_dir),
                    "--dry-run",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            self.assertTrue(result["dry_run"])
            self.assertEqual(result["would_promote"], str(promoted))
            self.assertEqual(result["status"], "curated")
            self.assertFalse(promoted.exists())

    def test_promote_relationship_retrospective_domain_passes_audit(self) -> None:
        candidate = candidate_base(
            retro_id="CR-20990101-relationship-domain-promote",
            domains=["relationship", "writing"],
            target_artifacts=["templates/relationship-rich-template.md"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            retro_dir = Path(tmp) / "retrospectives"
            write_retrospective_control_files(retro_dir)
            candidate_path = Path(tmp) / "candidate.json"
            candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
            promoted = retro_dir / "CR-20990101-relationship-domain-promote.json"

            dry_run = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE_RETRO_SCRIPT),
                    "--candidate",
                    str(candidate_path),
                    "--approved-by",
                    "unit-test",
                    "--retro-dir",
                    str(retro_dir),
                    "--dry-run",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            dry_result = json.loads(dry_run.stdout)
            self.assertTrue(dry_result["passed"])
            self.assertEqual(dry_result["domains"], ["relationship", "writing"])
            self.assertFalse(promoted.exists())

            promoted_proc = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE_RETRO_SCRIPT),
                    "--candidate",
                    str(candidate_path),
                    "--approved-by",
                    "unit-test",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            promoted_result = json.loads(promoted_proc.stdout)
            self.assertTrue(promoted_result["passed"])
            item = json.loads(promoted.read_text(encoding="utf-8"))
            self.assertEqual(item["domains"], ["relationship", "writing"])
            self.assertEqual(item["status"], "curated")
            self.assertTrue(item["human_approved"])

    def test_promote_team_career_and_fengshui_domains_pass_audit(self) -> None:
        candidate = candidate_base(
            retro_id="CR-20990101-team-fengshui-domain-promote",
            domains=["team_career", "fengshui", "writing"],
            target_artifacts=["knowledge/team-career/README.md", "knowledge/fengshui/README.md"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            retro_dir = Path(tmp) / "retrospectives"
            write_retrospective_control_files(retro_dir)
            candidate_path = Path(tmp) / "candidate.json"
            candidate_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
            promoted = retro_dir / "CR-20990101-team-fengshui-domain-promote.json"

            proc = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE_RETRO_SCRIPT),
                    "--candidate",
                    str(candidate_path),
                    "--approved-by",
                    "unit-test",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            item = json.loads(promoted.read_text(encoding="utf-8"))
            self.assertEqual(item["domains"], ["team_career", "fengshui", "writing"])
            self.assertEqual(item["status"], "curated")
            self.assertTrue(item["human_approved"])

    def test_knowledge_coverage_can_preview_with_temp_retrospective_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            retro_dir = Path(tmp) / "retrospectives"
            retro_dir.mkdir()
            for idx in [1, 2]:
                item = candidate_base(
                    retro_id=f"CR-20990101-relationship-preview-{idx}",
                    domains=["relationship", "writing"],
                    target_artifacts=["templates/relationship-rich-template.md"],
                )
                item["status"] = "curated"
                item["human_approved"] = True
                item["approved_by"] = "unit-test"
                (retro_dir / f"{item['id']}.json").write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_KNOWLEDGE_COVERAGE_SCRIPT),
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            self.assertEqual(result["retrospective_dir"], str(retro_dir.resolve()))
            self.assertEqual(result["retrospective_domain_counts"]["relationship"], 2)
            self.assertEqual(result["retrospective_domain_counts"]["writing"], 2)
            requirements = {item["id"]: item for item in result["retrospective_requirements"]}
            self.assertTrue(requirements["REQ-RETRO-RELATIONSHIP"]["satisfied"])
            self.assertTrue(requirements["REQ-RETRO-WRITING"]["satisfied"])
            next_actions = {item["requirement_id"]: item for item in result["next_actions"]}
            self.assertNotIn("REQ-RETRO-RELATIONSHIP", next_actions)
            self.assertNotIn("REQ-RETRO-WRITING", next_actions)
            self.assertIn("REQ-RETRO-BAZI", next_actions)
            self.assertEqual(next_actions["REQ-RETRO-BAZI"]["needed_entries"], 2)
            self.assertTrue(next_actions["REQ-RETRO-BAZI"]["do_not_create_synthetic_retrospectives"])
            self.assertFalse(result["goal_complete"])

    def test_global_retrospective_rejects_candidate_status(self) -> None:
        bad = candidate_base(
            retro_id="CR-20990101-unit-retro-candidate",
            domains=["writing"],
            target_artifacts=["knowledge/writing/reader-rich-report.md"],
        )
        bad["status"] = "candidate"
        bad["human_approved"] = True
        bad["approved_by"] = "unit-test"
        with tempfile.TemporaryDirectory() as tmp:
            retro_dir = Path(tmp) / "retrospectives"
            write_retrospective_control_files(retro_dir)
            path = retro_dir / "CR-20990101-unit-retro-candidate.json"
            path.write_text(json.dumps(bad, ensure_ascii=False, indent=2), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(AUDIT_CASE_RETROSPECTIVES_SCRIPT), "--retro-dir", str(retro_dir)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(result["passed"])
            self.assertTrue(any("candidate files must stay in external run folders" in item for item in result["failures"]))
            self.assertIn("CR-20990101-unit-retro-candidate.json", result["candidate_files"])
            self.assertIn("Run-local candidate files should stay external", result["run_local_candidate_hint"])


if __name__ == "__main__":
    unittest.main()
