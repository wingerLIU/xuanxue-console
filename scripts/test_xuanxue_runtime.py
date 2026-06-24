#!/usr/bin/env python3
"""Runtime workflow tests for xuanxue console external case runs."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from . import test_xuanxue_console as support
except ImportError:  # pragma: no cover - unittest discovery from scripts/
    import test_xuanxue_console as support


PROJECT_ROOT = support.PROJECT_ROOT
CREATE_WORKSPACE_SCRIPT = support.CREATE_WORKSPACE_SCRIPT
AUDIT_WORKSPACE_SCRIPT = support.AUDIT_WORKSPACE_SCRIPT
KNOWLEDGE_CONTEXT_SCRIPT = support.KNOWLEDGE_CONTEXT_SCRIPT
RETRO_INTAKE_SCRIPT = support.RETRO_INTAKE_SCRIPT
FOLLOWUP_CONTEXT_SCRIPT = support.FOLLOWUP_CONTEXT_SCRIPT
KNOWLEDGE_CONTEXT_SCHEMA = PROJECT_ROOT / "schemas" / "knowledge_context.schema.json"
RETROSPECTIVE_INTAKE_SCHEMA = PROJECT_ROOT / "schemas" / "retrospective_intake.schema.json"


class RuntimeWorkflowTests(unittest.TestCase):
    def assert_knowledge_context_contract(self, context: dict) -> None:
        schema = json.loads(KNOWLEDGE_CONTEXT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["schema_version"], "0.1.0")
        self.assertEqual(context["schema_version"], schema["schema_version"])
        for key in schema["required"]:
            self.assertIn(key, context)
        for key, rules in schema["properties"].items():
            if "minItems" in rules:
                self.assertGreaterEqual(len(context[key]), rules["minItems"], key)
            item_rules = rules.get("items", {})
            item_required = item_rules.get("required", []) if isinstance(item_rules, dict) else []
            if item_required:
                for item in context[key]:
                    for required_key in item_required:
                        self.assertIn(required_key, item, f"{key} missing {required_key}")

    def assert_retrospective_intake_contract(self, intake: dict) -> None:
        schema = json.loads(RETROSPECTIVE_INTAKE_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["schema_version"], "0.1.0")
        self.assertEqual(intake["schema_version"], schema["schema_version"])
        for key in schema["required"]:
            self.assertIn(key, intake)
        self.assertTrue(intake["do_not_promote_without_human_approval"])
        properties = schema["properties"]
        for item in intake["retrospective_collection_plan"]:
            for required_key in properties["retrospective_collection_plan"]["items"]["required"]:
                self.assertIn(required_key, item, f"retrospective_collection_plan missing {required_key}")
        for item in intake["domain_question_bank"]:
            for required_key in properties["domain_question_bank"]["items"]["required"]:
                self.assertIn(required_key, item, f"domain_question_bank missing {required_key}")
            self.assertIn(item["domain"], properties["domain_question_bank"]["items"]["properties"]["domain"]["enum"])
            self.assertIn(item["min_status"], properties["domain_question_bank"]["items"]["properties"]["min_status"]["enum"])
            self.assertGreaterEqual(item["needed_entries"], 1)
            self.assertTrue(item["questions"])
            self.assertTrue(item["suggested_target_artifacts"])

    def test_case_workspace_includes_retrospectives_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "case-a",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            manifest_path = Path(result["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIn("retrospectives_dir", manifest["paths"])
            self.assertIn("dialogue_dir", manifest["paths"])
            self.assertTrue(Path(manifest["paths"]["retrospectives_dir"]).is_dir())
            self.assertTrue(Path(manifest["paths"]["dialogue_dir"]).is_dir())
            self.assertEqual(manifest["validation_expectations"]["compare_recent_longforms"], 2)
            self.assertTrue(manifest["validation_expectations"]["capture_followup_dialogue"])
            self.assertEqual(manifest["validation_expectations"]["required_delivery_variants"], ["rich", "concise"])
            reader_contract = manifest["validation_expectations"]["mobile_reader_contract"]
            self.assertIn("单盘丰富版和单盘简洁版必须使用同一套暖纸、深字、少色、无框、无卡片阅读器。", reader_contract)
            self.assertIn("标题、章节主题、金句和正文重点统一使用深色体系；不额外跳色，不制造多余字号层级。", reader_contract)
            self.assertIn("正文重点句只用 700 字重加粗，不加底纹、荧光笔、色块、额外跳色或换字体。", reader_contract)
            self.assertIn("concise_pdf", manifest["validation_expectations"]["required_artifacts"])
            self.assertIn("rich_mobile_html", manifest["validation_expectations"]["required_artifacts"])
            self.assertIn("concise_mobile_html", manifest["validation_expectations"]["required_artifacts"])
            audit = subprocess.run(
                [sys.executable, str(AUDIT_WORKSPACE_SCRIPT), "--manifest", str(manifest_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertTrue(json.loads(audit.stdout)["passed"])

    def test_build_knowledge_context_writes_runtime_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "case-a",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            candidate_dir = Path(manifest["paths"]["retrospectives_dir"])
            candidate_dir.mkdir(parents=True, exist_ok=True)
            (candidate_dir / "CR-20260613-reader-tone.candidate.json").write_text(
                json.dumps(
                    {
                        "id": "CR-20260613-reader-tone",
                        "title": "去隐私读者口吻复盘",
                        "status": "candidate",
                        "human_approved": False,
                        "domains": ["writing"],
                        "target_artifacts": ["templates/relationship-rich-template.md"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            proc = subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "bazi",
                    "--module",
                    "ziwei",
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
            output = Path(result["output"])
            self.assertTrue(output.exists())
            self.assertFalse(output.resolve().is_relative_to(PROJECT_ROOT.resolve()))
            context = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(context["passed"])
            self.assert_knowledge_context_contract(context)
            self.assertIn("bazi", context["selected_modules"])
            self.assertIn("ziwei", context["selected_modules"])
            self.assertIn("writing", context["selected_modules"])
            paths = {item["path"] for item in context["knowledge_files"]}
            self.assertIn("knowledge/source-index.md", paths)
            self.assertIn("knowledge/bazi/foundations.md", paths)
            self.assertIn("knowledge/ziwei/foundations.md", paths)
            self.assertIn("SRC-BAZI-PROJECT-SYNTHESIS", context["source_ids"])
            retrospective_requirements = {item["id"]: item for item in context["retrospective_requirements"]}
            self.assertIn("REQ-RETRO-BAZI", retrospective_requirements)
            self.assertIn("REQ-RETRO-ZIWEI", retrospective_requirements)
            self.assertIn("REQ-RETRO-ANY", retrospective_requirements)
            self.assertIn("current_entries", retrospective_requirements["REQ-RETRO-BAZI"])
            self.assertIn("needed_entries", retrospective_requirements["REQ-RETRO-BAZI"])
            self.assertGreaterEqual(retrospective_requirements["REQ-RETRO-BAZI"]["needed_entries"], 0)
            self.assertIsInstance(context["retrospective_collection_plan"], list)
            self.assertTrue(context["retrospective_collection_plan"])
            collection_plan = {item["domain"]: item for item in context["retrospective_collection_plan"]}
            self.assertIn("bazi", collection_plan)
            self.assertIn("writing", collection_plan)
            for item in context["retrospective_collection_plan"]:
                self.assertIsInstance(item.get("suggested_target_artifacts"), list)
                self.assertTrue(item["suggested_target_artifacts"])
                self.assertIsInstance(item.get("candidate_commands"), list)
                self.assertTrue(item["candidate_commands"])
                self.assertNotIn("<project-relative-artifact>", item["candidate_command"])
                self.assertNotIn("<domain>", item["candidate_command"])
                for command in item["candidate_commands"]:
                    self.assertNotIn("<domain>", command)
            self.assertIn("knowledge/bazi/foundations.md", collection_plan["bazi"]["suggested_target_artifacts"])
            self.assertIn("knowledge/writing/reader-rich-report.md", collection_plan["writing"]["suggested_target_artifacts"])
            self.assertIn(
                "--target-artifact knowledge/bazi/foundations.md",
                collection_plan["bazi"]["candidate_command"],
            )
            bazi_evidence = "\n".join(collection_plan["bazi"]["evidence_to_collect"])
            self.assertIn("哪个八字结构判断被现实经历验证或推翻", bazi_evidence)
            writing_evidence = "\n".join(collection_plan["writing"]["evidence_to_collect"])
            self.assertIn("哪段让读者愿意继续读", writing_evidence)
            usage_rules = "\n".join(context["usage_rules"])
            self.assertIn("Reader-rich is the default paid delivery", usage_rules)
            self.assertIn("Missing Ziwei, Western, MBTI or divination inputs", usage_rules)
            self.assertTrue(context["goal_completion_blockers"])

    def test_relationship_knowledge_context_has_specific_retrospective_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "relationship-case",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            proc = subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "relationship",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            output = Path(json.loads(proc.stdout)["output"])
            context = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(context["passed"])
            self.assert_knowledge_context_contract(context)
            self.assertIn("relationship", context["selected_modules"])
            knowledge_paths = {item["path"] for item in context["knowledge_files"]}
            self.assertIn("templates/relationship-rich-template.md", knowledge_paths)
            self.assertIn("templates/relationship-concise-template.md", knowledge_paths)
            self.assertIn("scripts/build_relationship_facts.py", knowledge_paths)
            retrospective_requirements = {item["id"]: item for item in context["retrospective_requirements"]}
            self.assertIn("REQ-RETRO-RELATIONSHIP", retrospective_requirements)
            collection_plan = {item["domain"]: item for item in context["retrospective_collection_plan"]}
            self.assertIn("relationship", collection_plan)
            relationship_plan = collection_plan["relationship"]
            self.assertIn("templates/relationship-rich-template.md", relationship_plan["suggested_target_artifacts"])
            self.assertIn("scripts/validate_relationship_report.py", relationship_plan["suggested_target_artifacts"])
            self.assertIn("--domain relationship", relationship_plan["candidate_command"])
            self.assertIn(
                "--target-artifact templates/relationship-rich-template.md",
                relationship_plan["candidate_command"],
            )
            relationship_evidence = "\n".join(relationship_plan["evidence_to_collect"])
            self.assertIn("哪个吸引或互补判断准", relationship_evidence)
            self.assertIn("现实关系细节误写成命理事实", relationship_evidence)

    def test_team_career_and_fengshui_context_have_retrospective_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "team-career-case",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            proc = subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "team_career",
                    "--module",
                    "fengshui",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            output = Path(json.loads(proc.stdout)["output"])
            context = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(context["passed"])
            self.assert_knowledge_context_contract(context)
            self.assertIn("team_career", context["selected_modules"])
            self.assertIn("fengshui", context["selected_modules"])
            knowledge_paths = {item["path"] for item in context["knowledge_files"]}
            self.assertIn("knowledge/team-career/README.md", knowledge_paths)
            self.assertIn("service/multi-person-career-synastry-sop.md", knowledge_paths)
            self.assertIn("templates/team-career-synastry-template.md", knowledge_paths)
            self.assertIn("knowledge/fengshui/README.md", knowledge_paths)
            self.assertIn("service/client-intake-form.md", knowledge_paths)
            self.assertIn("templates/concise-report-template.md", knowledge_paths)
            retrospective_requirements = {item["id"]: item for item in context["retrospective_requirements"]}
            self.assertIn("REQ-RETRO-TEAM-CAREER", retrospective_requirements)
            self.assertIn("REQ-RETRO-FENGSHUI", retrospective_requirements)
            collection_plan = {item["domain"]: item for item in context["retrospective_collection_plan"]}
            self.assertIn("team_career", collection_plan)
            self.assertIn("fengshui", collection_plan)
            team_plan = collection_plan["team_career"]
            self.assertIn("knowledge/team-career/README.md", team_plan["suggested_target_artifacts"])
            self.assertIn("templates/team-career-synastry-template.md", team_plan["suggested_target_artifacts"])
            self.assertIn("--domain team_career", team_plan["candidate_command"])
            self.assertIn(
                "--target-artifact knowledge/team-career/README.md",
                team_plan["candidate_command"],
            )
            team_evidence = "\n".join(team_plan["evidence_to_collect"])
            self.assertIn("哪个角色判断被团队现实验证", team_evidence)
            self.assertIn("城市判断里哪个商业变量", team_evidence)
            fengshui_plan = collection_plan["fengshui"]
            self.assertIn("knowledge/fengshui/README.md", fengshui_plan["suggested_target_artifacts"])
            self.assertIn("--domain fengshui", fengshui_plan["candidate_command"])
            self.assertIn(
                "--target-artifact knowledge/fengshui/README.md",
                fengshui_plan["candidate_command"],
            )
            fengshui_evidence = "\n".join(fengshui_plan["evidence_to_collect"])
            self.assertIn("哪条空间、方位或城市建议执行后可观察", fengshui_evidence)
            self.assertIn("缺现场勘测、罗盘坐向或户型图", fengshui_evidence)

    def test_followup_context_requires_facts_and_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "case-a",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            run_dir = Path(manifest["paths"]["run_dir"])
            data_dir = Path(manifest["paths"]["data_dir"])
            drafts_dir = Path(manifest["paths"]["drafts_dir"])
            combo_path = data_dir / "case-a-combo.json"
            combo_path.write_text(
                json.dumps(
                    {
                        "schema_version": "0.2.0",
                        "module": "combo",
                        "facts": {"modules": [{"module": "bazi"}, {"module": "western"}]},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (drafts_dir / "case-a-longform.md").write_text("# 旧报告\n\n这里只能作为表达上下文。\n", encoding="utf-8")

            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "bazi",
                    "--module",
                    "western",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            knowledge_context_path = Path(manifest["paths"]["runtime_dir"]) / "knowledge_context.json"
            stale_context = json.loads(knowledge_context_path.read_text(encoding="utf-8"))
            for item in stale_context["retrospective_collection_plan"]:
                item["evidence_to_collect"] = item["evidence_to_collect"][:4]
            for item in stale_context["retrospective_requirements"]:
                item.pop("evidence_questions", None)
            knowledge_context_path.write_text(json.dumps(stale_context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(FOLLOWUP_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--question",
                    "感情部分为什么会这样判断？",
                    "--slug",
                    "relationship",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            output = Path(result["output"])
            dialogue_note = Path(result["dialogue_note"])
            self.assertTrue(output.exists())
            self.assertTrue(dialogue_note.exists())
            self.assertEqual(output.parent, run_dir / "runtime" / "followups")
            self.assertEqual(dialogue_note.parent, run_dir / "calibration" / "dialogue")
            self.assertFalse(output.resolve().is_relative_to(PROJECT_ROOT.resolve()))
            self.assertFalse(dialogue_note.resolve().is_relative_to(PROJECT_ROOT.resolve()))

            context = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(context["question"], "感情部分为什么会这样判断？")
            self.assertEqual(Path(context["dialogue_note"]), dialogue_note)
            self.assertEqual(context["answer_style"]["default"], "evidence_bounded_sharp")
            self.assertIn("bazi", context["selected_modules"])
            self.assertIn("western", context["selected_modules"])
            self.assertIn("writing", context["selected_modules"])
            self.assertEqual(context["facts_json"][0]["module"], "combo")
            self.assertEqual(Path(context["facts_json"][0]["path"]), combo_path)
            knowledge_paths = {item["path"] for item in context["required_knowledge_files"]}
            self.assertIn("knowledge/source-index.md", knowledge_paths)
            self.assertIn("knowledge/rules/inference-contract.md", knowledge_paths)
            self.assertIn("knowledge/bazi/foundations.md", knowledge_paths)
            self.assertIn("knowledge/western/foundations.md", knowledge_paths)
            self.assertIn("knowledge/writing/reader-rich-report.md", knowledge_paths)
            self.assertTrue(context["prior_report_context"])
            self.assertEqual(context["prior_report_context"][0]["evidence_status"], "context_only")
            self.assertTrue(any("old article alone" in item for item in context["answer_contract"]))
            note_text = dialogue_note.read_text(encoding="utf-8")
            self.assertIn("追加问题对话复盘", note_text)
            self.assertIn("客观不等于中庸", note_text)
            self.assertIn("感情部分为什么会这样判断？", note_text)

    def test_followup_context_infers_fengshui_module_from_direction_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "case-a",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            data_dir = Path(manifest["paths"]["data_dir"])
            combo_path = data_dir / "case-a-combo.json"
            team_source_summary = data_dir / "case-a-team-source-summary.json"
            team_flow_timing = data_dir / "case-a-team-flow-timing.json"
            combo_path.write_text(
                json.dumps(
                    {
                        "schema_version": "0.2.0",
                        "module": "combo",
                        "facts": {"modules": [{"module": "bazi"}, {"module": "western"}]},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            team_source_summary.write_text(
                json.dumps(
                    {
                        "schema_version": "0.1.0",
                        "case_id": "case-a",
                        "scenario": "去隐私团队事业合盘",
                        "team_hypotheses": ["客户入口需要现实验证"],
                        "validation_plan": ["30 天观察客户响应和工位调整后的沟通效率"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            team_flow_timing.write_text(
                json.dumps(
                    {
                        "schema_version": "0.1.0",
                        "case_id": "case-a",
                        "windows": [{"period": "2026-Q3", "focus": "团队试点和空间调整反馈"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            manifest.setdefault("artifacts", {}).setdefault("data", {})["team_source_summary"] = str(team_source_summary)
            manifest["artifacts"]["data"]["team_flow_timing_json"] = str(team_flow_timing)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "bazi",
                    "--module",
                    "western",
                    "--module",
                    "team_career",
                    "--module",
                    "fengshui",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(FOLLOWUP_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--question",
                    "办公室方位和工位怎么调整更适合？",
                    "--slug",
                    "fengshui-direction",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            context = json.loads(Path(result["output"]).read_text(encoding="utf-8"))
            self.assertIn("bazi", context["selected_modules"])
            self.assertIn("western", context["selected_modules"])
            self.assertIn("team_career", context["selected_modules"])
            self.assertIn("fengshui", context["selected_modules"])
            self.assertIn("writing", context["selected_modules"])
            fact_modules = [item["module"] for item in context["facts_json"]]
            self.assertIn("combo", fact_modules)
            self.assertIn("team_career", fact_modules)
            knowledge_paths = {item["path"] for item in context["required_knowledge_files"]}
            self.assertIn("knowledge/fengshui/README.md", knowledge_paths)
            self.assertIn("knowledge/team-career/README.md", knowledge_paths)
            self.assertIn("templates/team-career-synastry-template.md", knowledge_paths)
            self.assertIn("knowledge/bazi/foundations.md", knowledge_paths)
            self.assertIn("knowledge/western/foundations.md", knowledge_paths)
            self.assertTrue(any("team_source_summary" in item for item in context["answer_contract"]))
            self.assertTrue(any("fengshui/direction follow-ups" in item for item in context["answer_contract"]))
            note_text = Path(result["dialogue_note"]).read_text(encoding="utf-8")
            self.assertIn("team_career", note_text)
            self.assertIn("fengshui", note_text)
            self.assertIn("办公室方位和工位怎么调整更适合？", note_text)

    def test_followup_context_requires_fengshui_knowledge_for_direction_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "case-a",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            data_dir = Path(manifest["paths"]["data_dir"])
            combo_path = data_dir / "case-a-combo.json"
            combo_path.write_text(
                json.dumps(
                    {
                        "schema_version": "0.2.0",
                        "module": "combo",
                        "facts": {"modules": [{"module": "bazi"}, {"module": "western"}]},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "bazi",
                    "--module",
                    "western",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(FOLLOWUP_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--question",
                    "办公室方位和工位怎么调整更适合？",
                    "--slug",
                    "fengshui-direction",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            result = json.loads(proc.stdout)
            self.assertFalse(result["passed"])
            self.assertTrue(any("knowledge_context missing requested module: fengshui" in item for item in result["failures"]))

    def test_relationship_followup_context_uses_relationship_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "relationship-demo" / "run_demo"
            runtime_dir = run_dir / "runtime"
            data_dir = run_dir / "data"
            drafts_dir = run_dir / "drafts"
            delivery_dir = run_dir / "delivery"
            calibration_dir = run_dir / "calibration"
            for path in [runtime_dir, data_dir, drafts_dir, delivery_dir, calibration_dir / "dialogue"]:
                path.mkdir(parents=True, exist_ok=True)

            relationship_facts = data_dir / "relationship-demo-relationship.json"
            relationship_facts.write_text(
                json.dumps(
                    {
                        "schema_version": "0.1.0",
                        "module": "relationship",
                        "case_id": "relationship-demo",
                        "people": [{"label": "甲方"}, {"label": "乙方"}],
                        "bazi_cross": {"stems": [{"relation": "乙庚合金"}]},
                        "relationship_mode": {
                            "status": "男女朋友",
                            "category": "romantic_or_ambiguous",
                            "romantic_language_supported": True,
                            "allowed_private_language": ["身体吸引", "调情节奏", "想靠近", "安全感", "主动与回应"],
                            "forbidden_private_language": ["具体行为", "具体频率", "露骨细节", "身体隐私"],
                            "writing_boundary": "已知关系状态支持时，可以写身体吸引、调情和安全感；不写具体行为细节或频率。",
                        },
                        "relationship_life_domains": {
                            key: {
                                "label": label,
                                "allowed_writing": ["只写关系里的现实表现和可校准倾向。"],
                                "do_not_infer": ["不推断具体事件、金额、医疗诊断或私密频率。"],
                                "writing_boundary": "只能作为合盘追问的现实专题边界，不替代现实决定。",
                            }
                            for key, label in {
                                "career": "事业/合作",
                                "family_life": "家庭/生活承载",
                                "wealth_resources": "财富/资源投入",
                                "health_energy": "健康/精力照顾",
                                "intimacy_private": "亲近/私密边界",
                            }.items()
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            rich = delivery_dir / "甲方与乙方合盘总评-丰富版.md"
            concise_source = drafts_dir / "relationship-demo-relationship-concise.md"
            rich.write_text("# 合盘丰富版\n\n旧报告只能作为表达上下文。\n", encoding="utf-8")
            concise_source.write_text("# 合盘简洁版源稿\n\n旧简洁版只能作为表达上下文。\n", encoding="utf-8")
            manifest = {
                "schema_version": "0.1.0",
                "case_id": "relationship-demo",
                "reader_name": "甲方与乙方",
                "run_id": "run_demo",
                "paths": {
                    "run_dir": str(run_dir),
                    "runtime_dir": str(runtime_dir),
                    "data_dir": str(data_dir),
                    "drafts_dir": str(drafts_dir),
                    "delivery_dir": str(delivery_dir),
                    "calibration_dir": str(calibration_dir),
                    "dialogue_dir": str(calibration_dir / "dialogue"),
                },
                "relationship_context": {"relationship_status": "男女朋友", "distance_status": "异地"},
                "artifacts": {
                    "longform_markdown": str(rich),
                    "relationship_concise_source_markdown": str(concise_source),
                    "data": {"relationship": str(relationship_facts)},
                },
            }
            manifest_path = run_dir / "case_manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            knowledge_context = {
                "passed": True,
                "selected_modules": ["bazi", "ziwei", "western", "mbti", "relationship", "writing"],
                "knowledge_files": [
                    {"path": "knowledge/source-index.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/source-index.md")},
                    {"path": "knowledge/rules/inference-contract.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/rules/inference-contract.md")},
                    {"path": "knowledge/bazi/foundations.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/bazi/foundations.md")},
                    {"path": "knowledge/ziwei/foundations.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/ziwei/foundations.md")},
                    {"path": "knowledge/western/foundations.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/western/foundations.md")},
                    {"path": "knowledge/mbti/behavior-language.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/mbti/behavior-language.md")},
                    {"path": "templates/relationship-rich-template.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "templates/relationship-rich-template.md")},
                    {"path": "templates/relationship-concise-template.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "templates/relationship-concise-template.md")},
                    {"path": "scripts/build_relationship_facts.py", "exists": True, "absolute_path": str(PROJECT_ROOT / "scripts/build_relationship_facts.py")},
                    {"path": "scripts/validate_relationship_report.py", "exists": True, "absolute_path": str(PROJECT_ROOT / "scripts/validate_relationship_report.py")},
                    {"path": "knowledge/writing/reader-rich-report.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/writing/reader-rich-report.md")},
                ],
            }
            (runtime_dir / "knowledge_context.json").write_text(
                json.dumps(knowledge_context, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(FOLLOWUP_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--question",
                    "这段关系后续应该怎么判断？",
                    "--slug",
                    "relationship-followup",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            context = json.loads(Path(result["output"]).read_text(encoding="utf-8"))
            self.assertIn("relationship", context["selected_modules"])
            self.assertIn("writing", context["selected_modules"])
            self.assertEqual(context["facts_json"][0]["module"], "relationship")
            self.assertEqual(Path(context["facts_json"][0]["path"]), relationship_facts)
            self.assertEqual(
                set(context["relationship_life_domains"]),
                {"career", "family_life", "wealth_resources", "health_energy", "intimacy_private"},
            )
            self.assertEqual(context["relationship_mode"]["category"], "romantic_or_ambiguous")
            self.assertTrue(context["relationship_mode"]["romantic_language_supported"])
            knowledge_paths = {item["path"] for item in context["required_knowledge_files"]}
            self.assertIn("knowledge/bazi/foundations.md", knowledge_paths)
            self.assertIn("knowledge/ziwei/foundations.md", knowledge_paths)
            self.assertIn("knowledge/western/foundations.md", knowledge_paths)
            self.assertIn("knowledge/mbti/behavior-language.md", knowledge_paths)
            self.assertIn("templates/relationship-rich-template.md", knowledge_paths)
            self.assertIn("templates/relationship-concise-template.md", knowledge_paths)
            self.assertIn("scripts/build_relationship_facts.py", knowledge_paths)
            self.assertIn("scripts/validate_relationship_report.py", knowledge_paths)
            prior_artifacts = {item["artifact"] for item in context["prior_report_context"]}
            self.assertIn("longform_markdown", prior_artifacts)
            self.assertIn("relationship_concise_source_markdown", prior_artifacts)
            self.assertTrue(any("relationship facts" in item for item in context["answer_contract"]))
            self.assertTrue(any("relationship_life_domains" in item for item in context["answer_contract"]))
            note_text = Path(result["dialogue_note"]).read_text(encoding="utf-8")
            self.assertIn("relationship", note_text)
            self.assertIn("这段关系后续应该怎么判断？", note_text)

    def test_relationship_followup_fails_with_legacy_relationship_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "relationship-demo" / "run_demo"
            runtime_dir = run_dir / "runtime"
            data_dir = run_dir / "data"
            calibration_dir = run_dir / "calibration"
            for path in [runtime_dir, data_dir, calibration_dir / "dialogue"]:
                path.mkdir(parents=True, exist_ok=True)
            relationship_facts = data_dir / "relationship-demo-relationship.json"
            relationship_facts.write_text(
                json.dumps(
                    {
                        "schema_version": "0.1.0",
                        "module": "relationship",
                        "case_id": "relationship-demo",
                        "people": [{"label": "甲方"}, {"label": "乙方"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            manifest = {
                "schema_version": "0.1.0",
                "case_id": "relationship-demo",
                "run_id": "run_demo",
                "paths": {
                    "run_dir": str(run_dir),
                    "runtime_dir": str(runtime_dir),
                    "data_dir": str(data_dir),
                    "calibration_dir": str(calibration_dir),
                    "dialogue_dir": str(calibration_dir / "dialogue"),
                },
                "relationship_context": {"relationship_status": "男女朋友", "distance_status": "异地"},
                "artifacts": {"data": {"relationship": str(relationship_facts)}},
            }
            manifest_path = run_dir / "case_manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            knowledge_context = {
                "passed": True,
                "selected_modules": ["bazi", "ziwei", "western", "mbti", "relationship", "writing"],
                "knowledge_files": [
                    {"path": "knowledge/source-index.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/source-index.md")},
                    {"path": "knowledge/rules/inference-contract.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/rules/inference-contract.md")},
                    {"path": "templates/relationship-rich-template.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "templates/relationship-rich-template.md")},
                    {"path": "scripts/build_relationship_facts.py", "exists": True, "absolute_path": str(PROJECT_ROOT / "scripts/build_relationship_facts.py")},
                    {"path": "scripts/validate_relationship_report.py", "exists": True, "absolute_path": str(PROJECT_ROOT / "scripts/validate_relationship_report.py")},
                ],
            }
            (runtime_dir / "knowledge_context.json").write_text(
                json.dumps(knowledge_context, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(FOLLOWUP_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--question",
                    "事业和亲近边界要怎么看？",
                    "--slug",
                    "legacy-relationship-followup",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            result = json.loads(proc.stdout)
            self.assertFalse(result["passed"])
            self.assertTrue(any("missing relationship_life_domains" in item for item in result["failures"]))

    def test_relationship_followup_fails_without_relationship_knowledge_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "relationship-demo" / "run_demo"
            runtime_dir = run_dir / "runtime"
            data_dir = run_dir / "data"
            calibration_dir = run_dir / "calibration"
            for path in [runtime_dir, data_dir, calibration_dir / "dialogue"]:
                path.mkdir(parents=True, exist_ok=True)
            relationship_facts = data_dir / "relationship-demo-relationship.json"
            relationship_facts.write_text(
                json.dumps({"schema_version": "0.1.0", "case_id": "relationship-demo"}, ensure_ascii=False),
                encoding="utf-8",
            )
            manifest = {
                "schema_version": "0.1.0",
                "case_id": "relationship-demo",
                "run_id": "run_demo",
                "paths": {
                    "run_dir": str(run_dir),
                    "runtime_dir": str(runtime_dir),
                    "data_dir": str(data_dir),
                    "calibration_dir": str(calibration_dir),
                    "dialogue_dir": str(calibration_dir / "dialogue"),
                },
                "artifacts": {"data": {"relationship": str(relationship_facts)}},
            }
            manifest_path = run_dir / "case_manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            knowledge_context = {
                "passed": True,
                "selected_modules": ["bazi", "ziwei", "western", "mbti", "writing"],
                "knowledge_files": [
                    {"path": "knowledge/source-index.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/source-index.md")},
                    {"path": "knowledge/bazi/foundations.md", "exists": True, "absolute_path": str(PROJECT_ROOT / "knowledge/bazi/foundations.md")},
                ],
            }
            (runtime_dir / "knowledge_context.json").write_text(
                json.dumps(knowledge_context, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(FOLLOWUP_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--question",
                    "这段关系后续应该怎么判断？",
                    "--slug",
                    "relationship-followup",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            result = json.loads(proc.stdout)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("knowledge_context missing requested module: relationship" in item for item in result["failures"])
            )

    def test_followup_context_fails_when_knowledge_context_lacks_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "case-a",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            data_dir = Path(manifest["paths"]["data_dir"])
            combo_path = data_dir / "case-a-combo.json"
            combo_path.write_text(
                json.dumps(
                    {
                        "schema_version": "0.2.0",
                        "module": "combo",
                        "facts": {"modules": [{"module": "bazi"}, {"module": "western"}]},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "bazi",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(FOLLOWUP_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--question",
                    "感情部分为什么会这样判断？",
                    "--slug",
                    "relationship",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            result = json.loads(proc.stdout)
            self.assertFalse(result["passed"])
            self.assertTrue(any("knowledge_context missing requested module: western" in item for item in result["failures"]))

    def test_retrospective_intake_uses_knowledge_context_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "case-a",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            candidate_dir = Path(manifest["paths"]["retrospectives_dir"])
            candidate_dir.mkdir(parents=True, exist_ok=True)
            (candidate_dir / "CR-20260613-reader-tone.candidate.json").write_text(
                json.dumps(
                    {
                        "id": "CR-20260613-reader-tone",
                        "title": "去隐私读者口吻复盘",
                        "status": "candidate",
                        "human_approved": False,
                        "domains": ["writing"],
                        "target_artifacts": ["templates/relationship-rich-template.md"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "bazi",
                    "--module",
                    "ziwei",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RETRO_INTAKE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--global-retro-dir",
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
            markdown_path = Path(result["markdown"])
            json_path = Path(result["json"])
            self.assertTrue(markdown_path.exists())
            self.assertTrue(json_path.exists())
            self.assertFalse(markdown_path.resolve().is_relative_to(PROJECT_ROOT.resolve()))
            self.assertFalse(json_path.resolve().is_relative_to(PROJECT_ROOT.resolve()))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("可以问读者的问题", markdown)
            self.assertIn("按领域追问提示", markdown)
            self.assertIn("### 八字", markdown)
            self.assertIn("### 紫微", markdown)
            self.assertIn("不要用同一批问题追所有读者", markdown)
            self.assertIn("knowledge/bazi/foundations.md", markdown)
            self.assertIn("优先落点", markdown)
            self.assertIn("create_case_retrospective_candidate.py", markdown)
            self.assertIn("哪个八字结构判断被现实经历验证或推翻", markdown)
            self.assertNotIn("{'domain':", markdown)
            self.assertNotIn("needed ``", markdown)
            self.assertNotIn("--domain <domain>", markdown)
            self.assertIn("domain `bazi`", markdown)
            self.assertIn("本 run 已有候选复盘", markdown)
            self.assertIn("候选复盘审批摘要", markdown)
            self.assertIn("CR-20260613-reader-tone", markdown)
            self.assertIn("未人工批准前不计入全局知识库", markdown)
            self.assertIn("approval_ready: `false`", markdown)
            self.assertIn("target_artifacts imply missing domains: relationship", markdown)
            self.assertIn("promote_case_retrospective.py", markdown)
            self.assertIn("人工确认前预览命令", markdown)
            self.assertIn("--dry-run", markdown)
            self.assertIn("<RUN_DIR>\\retrospectives\\CR-20260613-reader-tone.candidate.json", markdown)
            self.assertNotIn(str(candidate_dir), markdown)
            intake = json.loads(json_path.read_text(encoding="utf-8"))
            self.assert_retrospective_intake_contract(intake)
            self.assertTrue(intake["do_not_promote_without_human_approval"])
            self.assertIn("run_local_candidates", intake)
            self.assertEqual(len(intake["run_local_candidates"]), 1)
            local_candidate = intake["run_local_candidates"][0]
            self.assertEqual(local_candidate["id"], "CR-20260613-reader-tone")
            self.assertEqual(local_candidate["file"], "CR-20260613-reader-tone.candidate.json")
            self.assertEqual(local_candidate["domains"], ["writing"])
            self.assertFalse(local_candidate["human_approved"])
            self.assertFalse(local_candidate["approval_ready"])
            self.assertTrue(local_candidate["approval_blockers"])
            self.assertIn("target_artifacts", local_candidate)
            self.assertTrue(any("missing domains: relationship" in item for item in local_candidate["warnings"]))
            self.assertIn("promote_case_retrospective.py", local_candidate["promotion_command"])
            self.assertIn("--dry-run", local_candidate["promotion_dry_run_command"])
            self.assertIn("<RUN_DIR>\\retrospectives\\CR-20260613-reader-tone.candidate.json", local_candidate["promotion_command"])
            self.assertIn("<RUN_DIR>\\retrospectives\\CR-20260613-reader-tone.candidate.json", local_candidate["promotion_dry_run_command"])
            self.assertEqual(intake["run_local_approval_summary"]["candidate_count"], 1)
            self.assertEqual(intake["run_local_approval_summary"]["ready_for_human_approval"], 0)
            self.assertEqual(intake["run_local_approval_summary"]["needs_fix_before_approval"], 1)
            self.assertEqual(intake["run_local_approval_impact_preview"]["ready_candidate_count"], 0)
            self.assertEqual(intake["run_local_minimal_approval_plan"]["selected_candidate_ids"], [])
            self.assertEqual(intake["run_local_ready_candidate_commands"]["dry_run"], [])
            self.assertEqual(intake["run_local_ready_candidate_commands"]["promote"], [])
            self.assertEqual(
                intake["run_local_ready_candidate_commands"]["post_promotion_audits"],
                [
                    "python scripts/audit_case_retrospectives.py",
                    "python scripts/audit_knowledge_coverage.py",
                ],
            )
            self.assertIn("当前没有 `approval_ready=true` 的候选", markdown)
            self.assertIn("当前没有可形成最小审批建议的 ready 候选", markdown)
            self.assertNotIn("ready 候选批量检查顺序", markdown)
            self.assertNotIn(str(candidate_dir), json.dumps(intake, ensure_ascii=False))
            self.assertEqual(
                intake["knowledge_growth_priority"]["decision_labels"],
                ["knowledge_rule", "expression_template", "validation_gate", "counterexample_only"],
            )
            question_bank = {item["domain"]: item for item in intake["domain_question_bank"]}
            self.assertIn("bazi", question_bank)
            self.assertIn("ziwei", question_bank)
            self.assertEqual(question_bank["bazi"]["label"], "八字")
            self.assertIn("REQ-RETRO-BAZI", question_bank["bazi"]["requirement_id"])
            self.assertIn("哪个八字结构判断被现实经历验证或推翻？", question_bank["bazi"]["questions"])
            self.assertIn("knowledge/bazi/foundations.md", question_bank["bazi"]["suggested_target_artifacts"])
            self.assertEqual(question_bank["ziwei"]["label"], "紫微")
            self.assertEqual(
                intake["run_local_candidate_warnings"][0]["id"],
                "CR-20260613-reader-tone",
            )
            self.assertTrue(intake["retrospective_collection_plan"])
            bazi_plan = {
                item["domain"]: item for item in intake["retrospective_collection_plan"] if isinstance(item, dict)
            }["bazi"]
            self.assertIn("哪个八字结构判断被现实经历验证或推翻？", bazi_plan["evidence_to_collect"])
            for item in intake["retrospective_collection_plan"]:
                self.assertTrue(item["suggested_target_artifacts"])

    def test_retrospective_intake_previews_ready_candidate_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "relationship-case",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            candidate_dir = Path(manifest["paths"]["retrospectives_dir"])
            candidate_dir.mkdir(parents=True, exist_ok=True)
            for idx in [1, 2]:
                (candidate_dir / f"CR-20260613-relationship-ready-{idx}.candidate.json").write_text(
                    json.dumps(
                        {
                            "id": f"CR-20260613-relationship-ready-{idx}",
                            "title": "去隐私合盘口吻复盘",
                            "status": "candidate",
                            "human_approved": False,
                            "domains": ["relationship", "writing"],
                            "target_artifacts": ["templates/relationship-rich-template.md"],
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "relationship",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RETRO_INTAKE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--global-retro-dir",
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
            markdown = Path(result["markdown"]).read_text(encoding="utf-8")
            intake = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
            self.assert_retrospective_intake_contract(intake)
            self.assertEqual(intake["run_local_approval_summary"]["ready_for_human_approval"], 2)
            preview = intake["run_local_approval_impact_preview"]
            self.assertEqual(preview["ready_candidate_count"], 2)
            requirements = {item["id"]: item for item in preview["requirements"]}
            self.assertTrue(requirements["REQ-RETRO-RELATIONSHIP"]["would_satisfy"])
            self.assertTrue(requirements["REQ-RETRO-RELATIONSHIP"]["newly_satisfied"])
            self.assertTrue(requirements["REQ-RETRO-WRITING"]["would_satisfy"])
            self.assertTrue(requirements["REQ-RETRO-WRITING"]["newly_satisfied"])
            self.assertTrue(requirements["REQ-RETRO-ANY"]["would_satisfy"])
            minimal = intake["run_local_minimal_approval_plan"]
            self.assertEqual(
                minimal["selected_candidate_ids"],
                [
                    "CR-20260613-relationship-ready-1",
                    "CR-20260613-relationship-ready-2",
                ],
            )
            minimal_requirements = {item["id"]: item for item in minimal["requirements"]}
            self.assertTrue(minimal_requirements["REQ-RETRO-RELATIONSHIP"]["would_satisfy_with_selected"])
            self.assertTrue(minimal_requirements["REQ-RETRO-WRITING"]["would_satisfy_with_selected"])
            self.assertTrue(minimal_requirements["REQ-RETRO-ANY"]["would_satisfy_with_selected"])
            self.assertFalse(minimal_requirements["REQ-RETRO-BAZI"]["can_satisfy_with_ready"])
            self.assertIn("批准 ready 候选后的覆盖预览", markdown)
            self.assertIn("最小人工审批建议", markdown)
            self.assertIn("建议先审批候选数：`2`", markdown)
            self.assertIn("仍不能靠本 run 候选关闭的门槛", markdown)
            self.assertIn("ready 候选批量检查顺序", markdown)
            self.assertIn("CR-20260613-relationship-ready-1", markdown)
            self.assertIn("REQ-RETRO-RELATIONSHIP", markdown)
            commands = intake["run_local_ready_candidate_commands"]
            self.assertEqual(len(commands["dry_run"]), 2)
            self.assertEqual(len(commands["promote"]), 2)
            self.assertTrue(all("--dry-run" in command for command in commands["dry_run"]))
            self.assertTrue(all("--dry-run" not in command for command in commands["promote"]))
            self.assertTrue(any("CR-20260613-relationship-ready-1.candidate.json" in command for command in commands["dry_run"]))
            self.assertTrue(any("CR-20260613-relationship-ready-2.candidate.json" in command for command in commands["promote"]))
            self.assertEqual(
                commands["post_promotion_audits"],
                [
                    "python scripts/audit_case_retrospectives.py",
                    "python scripts/audit_knowledge_coverage.py",
                ],
            )
            self.assertIn("python scripts/audit_case_retrospectives.py", markdown)
            self.assertIn("python scripts/audit_knowledge_coverage.py", markdown)

    def test_retrospective_intake_normalizes_team_career_target_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            created = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_WORKSPACE_SCRIPT),
                    "--case-id",
                    "team-career-case",
                    "--reader-name",
                    "reader",
                    "--external-root",
                    tmp,
                    "--run-id",
                    "run_demo",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            manifest_path = Path(json.loads(created.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            candidate_dir = Path(manifest["paths"]["retrospectives_dir"])
            candidate_dir.mkdir(parents=True, exist_ok=True)
            (candidate_dir / "CR-20260624-team-career-ready.candidate.json").write_text(
                json.dumps(
                    {
                        "id": "CR-20260624-team-career-ready",
                        "title": "去隐私团队事业合盘复盘",
                        "status": "candidate",
                        "human_approved": False,
                        "domains": ["team_career", "writing"],
                        "target_artifacts": [
                            "knowledge/team-career/README.md",
                            "service/multi-person-career-synastry-sop.md",
                            "templates/team-career-synastry-template.md",
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            retro_dir = Path(tmp) / "empty-retrospectives"
            retro_dir.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(KNOWLEDGE_CONTEXT_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--module",
                    "team_career",
                    "--retro-dir",
                    str(retro_dir),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RETRO_INTAKE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--global-retro-dir",
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
            markdown = Path(result["markdown"]).read_text(encoding="utf-8")
            intake = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
            self.assert_retrospective_intake_contract(intake)
            self.assertEqual(intake["run_local_approval_summary"]["ready_for_human_approval"], 1)
            local_candidate = intake["run_local_candidates"][0]
            self.assertTrue(local_candidate["approval_ready"])
            self.assertEqual(local_candidate["warnings"], [])
            self.assertNotIn("missing domains: team-career", markdown)


if __name__ == "__main__":
    unittest.main()
