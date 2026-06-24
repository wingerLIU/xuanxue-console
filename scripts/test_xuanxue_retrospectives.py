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
    domain_evidence = {
        domain: {
            "evidence_anchor": f"{domain} 去隐私证据锚点",
            "observed_feedback": f"{domain} 可观察反馈",
            "promotion_limit": f"{domain} 推广边界",
        }
        for domain in domains
    }
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
        "domain_evidence": domain_evidence,
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
    def test_retrospective_protocol_documents_domain_evidence_thresholds(self) -> None:
        protocol = (PROJECT_ROOT / "knowledge" / "case-retrospectives" / "promotion-protocol.md").read_text(
            encoding="utf-8"
        )
        template = (PROJECT_ROOT / "knowledge" / "case-retrospectives" / "template.md").read_text(encoding="utf-8")
        for domain in ["bazi", "ziwei", "western", "liuyao", "relationship", "team_career", "fengshui", "writing"]:
            self.assertIn(f"`{domain}`", protocol)
            self.assertIn(f"`{domain}`", template)
        self.assertIn("证据只够写作反馈时，就只选 `writing` 或 `quality`", protocol)
        self.assertIn("不要为了填补 coverage 把证据不足的命理域写进去", template)
        self.assertIn("起卦时间/方式、判断窗口和后续真实结果", protocol)
        self.assertIn("执行动作、观察周期、实际变化", protocol)

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
            self.assertIn(
                "knowledge/bazi/foundations.md",
                next_actions["REQ-RETRO-BAZI"]["suggested_target_artifacts"],
            )
            self.assertIn(
                "--target-artifact knowledge/bazi/foundations.md",
                next_actions["REQ-RETRO-BAZI"]["commands"][1],
            )
            self.assertNotIn("<project/artifact/path>", next_actions["REQ-RETRO-BAZI"]["commands"][1])
            bazi_questions = "\n".join(next_actions["REQ-RETRO-BAZI"]["evidence_questions"])
            self.assertIn("哪个八字结构判断被现实经历验证或推翻", bazi_questions)
            self.assertIn(
                "knowledge/fengshui/README.md",
                next_actions["REQ-RETRO-FENGSHUI"]["suggested_target_artifacts"],
            )
            fengshui_questions = "\n".join(next_actions["REQ-RETRO-FENGSHUI"]["evidence_questions"])
            self.assertIn("哪条空间、方位或城市建议执行后可观察", fengshui_questions)
            self.assertIn("缺现场勘测、罗盘坐向或户型图", fengshui_questions)
            self.assertFalse(result["goal_complete"])

    def test_knowledge_coverage_reports_external_ready_candidates_without_completing_goal(self) -> None:
        candidate = candidate_base(
            retro_id="CR-20990101-team-career-ready",
            domains=["team_career", "writing"],
            target_artifacts=["knowledge/team-career/README.md"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            retro_dir = Path(tmp) / "retrospectives"
            write_retrospective_control_files(retro_dir)
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
            runs_root = Path(tmp) / "external-runs"
            candidate_dir = runs_root / "runs" / "case-redacted" / "run_redacted" / "retrospectives"
            candidate_dir.mkdir(parents=True)
            (candidate_dir / "CR-20990101-team-career-ready.candidate.json").write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            blocked_candidate = candidate_base(
                retro_id="CR-20990101-team-career-needs-evidence",
                domains=["team_career", "writing"],
                target_artifacts=["knowledge/team-career/README.md"],
            )
            blocked_candidate.pop("domain_evidence")
            (candidate_dir / "CR-20990101-team-career-needs-evidence.candidate.json").write_text(
                json.dumps(blocked_candidate, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_KNOWLEDGE_COVERAGE_SCRIPT),
                    "--retro-dir",
                    str(retro_dir),
                    "--runs-root",
                    str(runs_root),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            self.assertFalse(result["goal_complete"])
            summary = result["run_local_candidate_summary"]
            self.assertTrue(summary["enabled"])
            self.assertEqual(summary["candidate_count"], 2)
            self.assertEqual(summary["ready_for_human_approval"], 1)
            self.assertEqual(summary["needs_fix_before_approval"], 1)
            item = summary["items"][0]
            self.assertEqual(item["id"], "CR-20990101-team-career-ready")
            self.assertEqual(item["location"], "external_run_retrospectives")
            self.assertIn("REQ-RETRO-TEAM-CAREER", item["matched_unsatisfied_requirements"])
            self.assertNotIn("REQ-RETRO-ANY", item["matched_unsatisfied_requirements"])
            self.assertIn("<RUN_DIR>\\retrospectives\\CR-20990101-team-career-ready.candidate.json", item["dry_run_command"])
            blocked = summary["blocked_items"][0]
            self.assertEqual(blocked["id"], "CR-20990101-team-career-needs-evidence")
            self.assertFalse(blocked["approval_ready"])
            self.assertTrue(any("missing domain_evidence" in reason for reason in blocked["approval_blockers"]))
            self.assertIn("domain_evidence_required", blocked)
            required_domains = {item["domain"]: item for item in blocked["domain_evidence_required"]}
            self.assertIn("team_career", required_domains)
            self.assertIn("writing", required_domains)
            self.assertIn("evidence_anchor", required_domains["team_career"]["missing_fields"])
            self.assertTrue(any("哪个角色判断被团队现实验证" in question for question in required_domains["team_career"]["evidence_questions"]))
            self.assertTrue(any("补齐 domain_evidence" in action for action in blocked["repair_actions"]))
            self.assertIn("create_retrospective_intake.py", blocked["intake_recheck_command"])
            self.assertIn("--dry-run", blocked["promotion_dry_run_command_after_fix"])
            self.assertIn("repair_plan", summary)
            self.assertEqual(summary["repair_plan"][0]["id"], "CR-20990101-team-career-needs-evidence")
            self.assertEqual(
                summary["repair_plan"][0]["candidate_path"],
                "<RUN_DIR>\\retrospectives\\CR-20990101-team-career-needs-evidence.candidate.json",
            )
            self.assertNotIn(str(runs_root), json.dumps(summary, ensure_ascii=False))

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
