#!/usr/bin/env python3
"""Relationship workflow tests for xuanxue-console."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CREATE_RELATIONSHIP_WORKSPACE_SCRIPT = Path(__file__).with_name("create_relationship_workspace.py")
BUILD_RELATIONSHIP_FACTS_SCRIPT = Path(__file__).with_name("build_relationship_facts.py")
VALIDATE_RELATIONSHIP_REPORT_SCRIPT = Path(__file__).with_name("validate_relationship_report.py")
FINALIZE_CASE_SCRIPT = Path(__file__).with_name("finalize_case.py")
PACKAGE_READER_DELIVERY_SCRIPT = Path(__file__).with_name("package_reader_delivery.py")
PACKAGE_MOBILE_HTML_SCRIPT = Path(__file__).with_name("package_mobile_html.py")
RELATIONSHIP_MODE_SCRIPT = Path(__file__).with_name("relationship_mode.py")


def load_relationship_mode():
    spec = importlib.util.spec_from_file_location("relationship_mode", RELATIONSHIP_MODE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load relationship_mode.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_relationship_headings() -> list[str]:
    spec = importlib.util.spec_from_file_location("validate_relationship_report", VALIDATE_RELATIONSHIP_REPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate_relationship_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.REQUIRED_HEADINGS)


def load_relationship_heading_topics() -> list[str]:
    spec = importlib.util.spec_from_file_location("validate_relationship_report", VALIDATE_RELATIONSHIP_REPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate_relationship_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.REQUIRED_HEADING_TOPICS)


class RelationshipWorkflowTests(unittest.TestCase):
    def test_relationship_mode_shared_schema(self) -> None:
        module = load_relationship_mode()
        romantic = module.relationship_mode_from_status("男女朋友，异地")
        self.assertEqual(romantic["category"], "romantic_or_ambiguous")
        self.assertTrue(romantic["romantic_language_supported"])
        self.assertIn("身体吸引", romantic["allowed_private_language"])
        self.assertFalse(module.relationship_mode_schema_failures(romantic))

        work = module.relationship_mode_from_status("合作伙伴")
        self.assertEqual(work["category"], "non_romantic_or_unsupported")
        self.assertFalse(work["romantic_language_supported"])
        self.assertIn("身体吸引", work["forbidden_private_language"])
        self.assertFalse(module.relationship_mode_schema_failures(work))
        self.assertEqual(module.relationship_mode_schema_failures({}), ["relationship_mode missing or empty."])
        self.assertTrue(module.is_romantic_facts({"relationship_mode": romantic}))
        self.assertFalse(module.is_romantic_facts({"relationship_mode": work}))

    def test_relationship_facts_and_validator_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel_run = root / "runs" / "relationship" / "run_demo"
            a_run = root / "runs" / "person-a" / "run_demo"
            b_run = root / "runs" / "person-b" / "run_demo"
            for run in [rel_run, a_run, b_run]:
                (run / "data").mkdir(parents=True, exist_ok=True)
                (run / "drafts").mkdir(parents=True, exist_ok=True)
                (run / "delivery").mkdir(parents=True, exist_ok=True)
                (run / "runtime").mkdir(parents=True, exist_ok=True)
                (run / "logs").mkdir(parents=True, exist_ok=True)
                (run / "calibration").mkdir(parents=True, exist_ok=True)
                (run / "retrospectives").mkdir(parents=True, exist_ok=True)
            relationship_manifest = {
                "schema_version": "0.1.0",
                "case_id": "relationship",
                "run_id": "run_demo",
                "created_at": "test",
                "paths": {
                    "run_dir": str(rel_run),
                    "data_dir": str(rel_run / "data"),
                    "drafts_dir": str(rel_run / "drafts"),
                    "delivery_dir": str(rel_run / "delivery"),
                    "runtime_dir": str(rel_run / "runtime"),
                    "logs_dir": str(rel_run / "logs"),
                    "calibration_dir": str(rel_run / "calibration"),
                    "retrospectives_dir": str(rel_run / "retrospectives"),
                },
                "status": {"stage": "test", "human_approved": False},
            }
            rel_manifest = rel_run / "case_manifest.json"
            rel_manifest.write_text(json.dumps(relationship_manifest, ensure_ascii=False), encoding="utf-8")
            a_bazi = a_run / "data" / "person-a-bazi.json"
            b_bazi = b_run / "data" / "person-b-bazi.json"
            a_western = a_run / "data" / "person-a-western.json"
            b_western = b_run / "data" / "person-b-western.json"
            a_ziwei = a_run / "data" / "person-a-ziwei.json"
            b_ziwei = b_run / "data" / "person-b-ziwei.json"
            b_mbti = b_run / "data" / "person-b-mbti.json"
            a_bazi.write_text(json.dumps({"facts": {"pillars": {"year": "戊寅", "month": "戊午", "day": "庚戌", "hour": "丁丑"}, "flow": {"current_dayun": {"gan_zhi": "辛酉", "start_year": 2020, "end_year": 2029}, "annual_flows": [{"year": 2026, "pillar": "丙午", "dayun": "辛酉"}]}}}, ensure_ascii=False), encoding="utf-8")
            b_bazi.write_text(json.dumps({"facts": {"pillars": {"year": "甲申", "month": "壬申", "day": "乙亥", "hour": "辛巳"}, "flow": {"current_dayun": {"gan_zhi": "庚午", "start_year": 2020, "end_year": 2029}, "annual_flows": [{"year": 2026, "pillar": "丙午", "dayun": "庚午"}]}}}, ensure_ascii=False), encoding="utf-8")
            a_western.write_text(json.dumps({"facts": {"placements": [{"body": "金星", "sign": "双子", "absolute_longitude": 68.59}, {"body": "月亮", "sign": "天秤", "absolute_longitude": 189.15}]}}, ensure_ascii=False), encoding="utf-8")
            b_western.write_text(json.dumps({"facts": {"placements": [{"body": "火星", "sign": "处女", "absolute_longitude": 158.62}, {"body": "月亮", "sign": "射手", "absolute_longitude": 249.99}]}}, ensure_ascii=False), encoding="utf-8")
            a_ziwei.write_text(json.dumps({"facts": {"current_decadal": {"name": "福德宫", "major_stars": ["天梁"]}, "palaces": [{"name": "夫妻宫", "major_stars": ["太阴"]}]}}, ensure_ascii=False), encoding="utf-8")
            b_ziwei.write_text(json.dumps({"facts": {"current_decadal": {"name": "兄弟宫", "major_stars": ["破军"]}, "palaces": [{"name": "夫妻宫", "major_stars": ["天同"]}]}}, ensure_ascii=False), encoding="utf-8")
            b_mbti.write_text(json.dumps({"facts": {"type": "ISFP"}}, ensure_ascii=False), encoding="utf-8")
            a_manifest = a_run / "case_manifest.json"
            b_manifest = b_run / "case_manifest.json"
            a_manifest.write_text(json.dumps({"case_id": "person-a", "paths": {"data_dir": str(a_run / "data")}, "artifacts": {"data": {"bazi": str(a_bazi), "western": str(a_western), "ziwei": str(a_ziwei)}}}, ensure_ascii=False), encoding="utf-8")
            b_manifest.write_text(json.dumps({"case_id": "person-b", "paths": {"data_dir": str(b_run / "data")}, "artifacts": {"data": {"bazi": str(b_bazi), "western": str(b_western), "ziwei": str(b_ziwei), "mbti": str(b_mbti)}}}, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(BUILD_RELATIONSHIP_FACTS_SCRIPT),
                    "--manifest",
                    str(rel_manifest),
                    "--person-a-manifest",
                    str(a_manifest),
                    "--person-b-manifest",
                    str(b_manifest),
                    "--person-a-label",
                    "甲方",
                    "--person-b-label",
                    "乙方",
                    "--relationship-status",
                    "男女朋友",
                    "--distance-status",
                    "异地",
                    "--person-a-mbti-type",
                    "ENTP-A",
                    "--person-b-mbti-type",
                    "ISFP-T",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            facts = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
            stem_relations = {item["relation"] for item in facts["bazi_cross"]["stems"]}
            self.assertIn("乙庚合金", stem_relations)
            self.assertIn("甲庚冲", stem_relations)
            self.assertIn("丁壬合木", stem_relations)
            self.assertEqual(facts["mbti"]["person_a"]["type"], "ENTP-A")
            self.assertEqual(facts["mbti"]["person_b"]["type"], "ISFP-T")
            self.assertEqual(facts["relationship_context"]["person_a_label"], "甲方")
            self.assertEqual(facts["relationship_context"]["person_b_label"], "乙方")
            self.assertEqual(facts["relationship_context"]["relationship_status"], "男女朋友")
            self.assertEqual(facts["relationship_context"]["distance_status"], "异地")
            self.assertEqual(facts["relationship_context"]["person_a_mbti_type"], "ENTP-A")
            self.assertEqual(facts["relationship_context"]["person_b_mbti_type"], "ISFP-T")
            self.assertEqual(facts["relationship_mode"]["category"], "romantic_or_ambiguous")
            self.assertTrue(facts["relationship_mode"]["romantic_language_supported"])
            self.assertEqual(facts["relationship_context"]["relationship_mode"], facts["relationship_mode"])
            self.assertIn("bazi_auxiliary", facts)
            self.assertIn("career_overlap", facts)
            self.assertIn("relationship_life_domains", facts)
            self.assertEqual(
                set(facts["relationship_life_domains"]),
                {"career", "family_life", "wealth_resources", "health_energy", "intimacy_private"},
            )
            self.assertIn(
                "不写具体行为细节或频率",
                facts["relationship_life_domains"]["intimacy_private"]["writing_boundary"],
            )
            self.assertIn(
                "医疗诊断",
                facts["relationship_life_domains"]["health_energy"]["do_not_infer"],
            )
            self.assertIn("annual_intersections", facts)
            self.assertEqual(facts["annual_intersections"][0]["year"], 2026)
            annual_branch_relations = {
                item["relation"]
                for item in facts["annual_intersections"][0]["flow_to_flow"]["branches"]
            }
            self.assertIn("午午自刑", annual_branch_relations)
            a_flow_to_b = {
                item["relation"]
                for item in facts["annual_intersections"][0]["person_a_flow_to_person_b_natal"]["stems"]
            }
            self.assertIn("丙辛合水", a_flow_to_b)
            self.assertTrue(Path(result["markdown"]).exists())
            markdown = Path(result["markdown"]).read_text(encoding="utf-8")
            self.assertIn("年份交叉触发", markdown)
            self.assertIn("不能反推两人一定在该年发生现实交集", markdown)
            self.assertIn("现实专题交集事实", markdown)
            self.assertIn("关系模式：romantic_or_ambiguous", markdown)
            self.assertIn("亲近/私密写作边界", markdown)
            self.assertIn("事业/合作", markdown)
            self.assertIn("家庭/生活承载", markdown)
            self.assertIn("财富/资源投入", markdown)
            self.assertIn("健康/精力照顾", markdown)
            self.assertIn("亲近/私密边界", markdown)
            self.assertIn("甲方流年", markdown)
            self.assertIn("乙方流年", markdown)
            updated = json.loads(rel_manifest.read_text(encoding="utf-8"))
            self.assertEqual(updated["relationship_context"]["relationship_status"], "男女朋友")
            self.assertEqual(updated["artifacts"]["data"]["relationship"], result["json"])

            alt_rel_manifest = rel_run / "case_manifest_alt.json"
            alt_rel_manifest.write_text(
                json.dumps(
                    {
                        "case_id": "relationship-alt",
                        "paths": {"run_dir": str(rel_run)},
                        "artifacts": {"data": {}},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(BUILD_RELATIONSHIP_FACTS_SCRIPT),
                    "--manifest",
                    str(alt_rel_manifest),
                    "--person-a-manifest",
                    str(a_manifest),
                    "--person-b-manifest",
                    str(b_manifest),
                    "--person-a-label",
                    "阿甲",
                    "--person-b-label",
                    "阿乙",
                    "--relationship-status",
                    "暧昧观察",
                    "--distance-status",
                    "同城",
                    "--person-a-mbti-type",
                    "INTJ",
                    "--person-b-mbti-type",
                    "ENFP",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            alt_result = json.loads(proc.stdout)
            alt_facts_path = Path(alt_result["json"])
            alt_facts = json.loads(alt_facts_path.read_text(encoding="utf-8"))
            alt_markdown = Path(alt_result["markdown"]).read_text(encoding="utf-8")
            self.assertEqual(alt_facts["relationship_context"]["relationship_status"], "暧昧观察")
            self.assertEqual(alt_facts["relationship_context"]["distance_status"], "同城")
            self.assertIn("阿甲流年", alt_markdown)
            self.assertIn("阿乙流年", alt_markdown)
            self.assertNotIn("甲方流年", alt_markdown)
            self.assertIn("现实输入只限暧昧观察与同城", "\n".join(alt_facts["writing_contract"]))

            work_rel_manifest = rel_run / "case_manifest_work.json"
            work_rel_manifest.write_text(
                json.dumps(
                    {
                        "case_id": "relationship-work",
                        "paths": {"run_dir": str(rel_run)},
                        "artifacts": {"data": {}},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(BUILD_RELATIONSHIP_FACTS_SCRIPT),
                    "--manifest",
                    str(work_rel_manifest),
                    "--person-a-manifest",
                    str(a_manifest),
                    "--person-b-manifest",
                    str(b_manifest),
                    "--person-a-label",
                    "阿甲",
                    "--person-b-label",
                    "阿乙",
                    "--relationship-status",
                    "合作伙伴",
                    "--distance-status",
                    "同城",
                    "--person-a-mbti-type",
                    "INTJ",
                    "--person-b-mbti-type",
                    "ENFP",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            work_result = json.loads(proc.stdout)
            work_facts_path = Path(work_result["json"])
            work_facts = json.loads(work_facts_path.read_text(encoding="utf-8"))
            self.assertEqual(work_facts["relationship_context"]["relationship_status"], "合作伙伴")
            self.assertEqual(work_facts["relationship_mode"]["category"], "non_romantic_or_unsupported")
            self.assertFalse(work_facts["relationship_mode"]["romantic_language_supported"])
            work_private = work_facts["relationship_life_domains"]["intimacy_private"]
            self.assertEqual(work_private["label"], "亲近/私密边界")
            self.assertIn("亲近感", work_private["allowed_writing"])
            self.assertIn("身体吸引", work_private["do_not_infer"])
            self.assertIn("不写身体吸引", work_private["writing_boundary"])

            article = rel_run / "drafts" / "relationship.md"
            body = (
                "甲方与乙方是男女朋友，也是异地关系。乙庚合金、甲庚冲、丁壬合木、寅申冲、寅巳刑、巳亥冲、"
                "寅亥六合木、寅亥破、寅巳害、寅申刑、"
                "金星、火星、月亮、紫微、西洋占星、MBTI、ENTP-A、ISFP-T、格局、神煞、空亡、长生、纳音、事业、私密、身体吸引、家庭、合作、资源、财富、健康、精力、关系形态、"
                "2020、2025、2026、2030都要作为可复查锚点。"
                "议题：现实承载如何？议题：沟通节奏如何？议题：见面频率如何？议题：边界如何？议题：事业合作如何？议题：关系形态如何？"
            )
            h2_parts = []
            for idx, topic in enumerate(load_relationship_heading_topics(), start=1):
                label = "白话场景：" if idx <= 10 else ""
                heading = f"{topic}：{topic}里的靠近要落到现实"
                unique = f"{topic} 这一段落回到不同关系议题，写清楚各自的靠近方式和现实承接。"
                takeaway = f"**第{idx:02d}章的白话结论是关系要落到具体行动。**\n" if idx <= 11 else ""
                h2_parts.append(f"## {heading}\n{takeaway}{label}{body}{unique}\n" + ("甲方 乙方 " * (14 + idx)))
            h2s = "\n".join(h2_parts)
            article.write_text(
                "# 甲方与乙方合盘评级：强吸引型互补佳缘\n\n"
                + h2s
                + "\n\n甲方与乙方这组关系仍然值得认真经营，越能把差异翻译成照顾和行动，越容易越走越稳。\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(article),
                    "--facts-json",
                    result["json"],
                    "--min-chars",
                    "3000",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue(json.loads(proc.stdout)["passed"])

            legacy_facts = rel_run / "data" / "relationship-legacy-missing-life-domains.json"
            legacy_payload = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
            legacy_payload.pop("relationship_life_domains", None)
            legacy_facts.write_text(json.dumps(legacy_payload, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(article),
                    "--facts-json",
                    str(legacy_facts),
                    "--min-chars",
                    "3000",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            legacy_result = json.loads(proc.stdout)
            self.assertFalse(legacy_result["passed"])
            self.assertIn("missing relationship_life_domains", "\n".join(legacy_result["facts_schema_failures"]))

            default_heading_article = rel_run / "drafts" / "relationship-default-heading-hooks.md"
            default_h2_parts = []
            for idx, heading in enumerate(load_relationship_headings(), start=1):
                label = "白话场景：" if idx <= 10 else ""
                unique = f"{heading} 这一段落故意沿用模板默认标题，用来验证冒号后的金句不能整套复用。"
                takeaway = f"**第{idx:02d}章的白话结论是关系要落到具体行动。**\n" if idx <= 11 else ""
                default_h2_parts.append(f"## {heading}\n{takeaway}{label}{body}{unique}\n" + ("甲方 乙方 " * (14 + idx)))
            default_heading_article.write_text(
                "# 甲方与乙方合盘：强牵引互补缘，越懂越入心\n\n"
                + "\n".join(default_h2_parts)
                + "\n\n这组关系仍然值得认真经营，越能把差异翻译成照顾和行动，越容易越走越稳。\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(default_heading_article),
                    "--facts-json",
                    result["json"],
                    "--min-chars",
                    "3000",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            default_heading_result = json.loads(proc.stdout)
            self.assertFalse(default_heading_result["passed"])
            self.assertIn("uncustomized template defaults", "\n".join(default_heading_result["format_failures"]))

            variant_article = rel_run / "drafts" / "relationship-variant-headings.md"
            variant_h2_parts = []
            for idx, topic in enumerate(load_relationship_heading_topics(), start=1):
                label = "白话场景：" if idx <= 10 else ""
                heading = f"{topic}：{topic}里能看见不同的牵引"
                unique = f"{topic} 这一段落回到不同关系议题，允许不同合盘按事实改写冒号后的金句。"
                takeaway = f"**第{idx:02d}章的白话结论是关系要落到具体行动。**\n" if idx <= 11 else ""
                variant_h2_parts.append(f"## {heading}\n{takeaway}{label}{body}{unique}\n" + ("甲方 乙方 " * (14 + idx)))
            variant_article.write_text(
                "# 甲方与乙方合盘：稳中有甜，差异也能变成牵引\n\n"
                + "\n".join(variant_h2_parts)
                + "\n\n这组关系的收束仍然要落在值得认真经营：差异不是结论，能不能把差异翻译成照顾和行动，才决定关系能否越走越稳。\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(variant_article),
                    "--facts-json",
                    result["json"],
                    "--min-chars",
                    "3000",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            variant_result = json.loads(proc.stdout)
            self.assertTrue(variant_result["passed"])
            self.assertIn("关系总评：关系总评里能看见不同的牵引", variant_result["headings"])

            concise_article = rel_run / "drafts" / "relationship-concise.md"
            concise_body = (
                "# 甲方与乙方合盘：强牵引互补缘，越懂越入心\n\n"
                "## 合盘总评\n"
                "**甲方与乙方这组合盘的核心，是强牵引和互补感同时存在。**"
                "甲方与乙方是男女朋友，也是异地关系，乙庚合金、甲庚冲、丁壬合木、寅申冲、寅巳刑、巳亥冲、寅亥六合木、寅亥破、寅巳害、寅申刑都说明靠近感和磨合感会一起出现。"
                "金星、火星、月亮、紫微、西洋占星、MBTI、ENTP-A、ISFP-T一起看，甲方与乙方的关系不是只靠热度，而要靠现实承接。"
                "甲方容易把关系推进成讨论和判断，乙方更在意对方是否真的把感受放在心上，所以这组盘最值得看的，是吸引之后能不能把节奏接住。\n\n"
                "## 吸引与互补\n"
                "白话场景：甲方更容易用语言、判断和变化感启动关系，乙方更容易用感受、审美和回应感让关系变软。甲方会带来方向、玩笑和新鲜感，乙方会带来温度、细节和被照顾的感觉。"
                "**吸引不是单方面追逐，而是两个人都能在对方身上看到自己缺的那一块。**"
                "事业、家庭、合作、资源、财富、健康、精力和关系形态都可以从这个互补里展开。甲方与乙方如果只看差异，会觉得对方难懂；如果把差异当成分工，反而会觉得彼此有用、有趣，也有被补上的感觉。\n\n"
                "## 容易误读的地方\n"
                "情景推演：异地时，甲方可能用讨论和试探确认关系，乙方可能用安静和慢回应确认安全。"
                "**真正要避免的，是把对方的节奏误读成不在乎。**"
                "甲方需要看见乙方的慢不是冷，乙方也需要看见甲方的快不是压迫。2020、2025、2026、2030这些阶段只作为趋势锚点，不写成绝对事件，重点是甲方与乙方在这些阶段更容易校准关系节奏、见面安排和现实承诺。\n\n"
                "## 事业、家庭、财富与精力\n"
                "甲方与乙方在事业上可以互相启发，甲方更容易提方向、拆问题、找机会，乙方更容易看体验、看质感、看人的真实反应。家庭主题适合先谈感受和边界，财富主题重在见面成本、时间投入和诚意分配，精力主题重在作息和恢复。"
                "**关系要走稳，不是把所有现实议题都浪漫化，而是把喜欢放进能执行的安排里。**"
                "当甲方与乙方愿意把钱、时间、距离和情绪都讲清楚，关系就会从好感变成可持续的生活安排。"
                "事业交集不一定表现为一起做同一件事，也可能是甲方帮乙方看方向、乙方帮甲方看体验；家庭交集不一定马上进入承诺，也可能先体现为彼此是否愿意照顾对方的现实处境。"
                "财富交集也不只是花钱多少，而是谁愿意为见面、沟通和未来计划投入成本。精力交集则更细：忙的时候怎么解释，累的时候怎么安放，情绪上来时谁先把话说软。\n\n"
                "## 未来两到五年\n"
                "未来更适合把联系节奏、见面安排、钱和时间的投入说清楚。"
                "甲方与乙方都不适合只靠猜，越猜越容易错过对方真正的用心。甲方适合把承诺说成具体安排，乙方适合把在意说成可被回应的需求；一个负责把方向点亮，一个负责让关系有温度。"
                "如果两个人愿意定期复盘联系频率、见面计划、情绪消耗和现实投入，这段关系会更像慢慢搭起来的生活，而不是只停在好感和想象里。"
                "可验证的点也很清楚：甲方与乙方越能把想念、委屈、期待和成本说成具体话，关系越不容易被距离稀释，彼此也越能安心稳定，也更愿意继续靠近。"
                "所以未来的重点不是预测某一天一定发生什么，而是看甲方与乙方能不能把喜欢变成稳定的互动习惯。**这段关系值得认真经营，越能把差异翻译成爱语，越容易越走越稳。**"
            )
            concise_article.write_text(concise_body, encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(concise_article),
                    "--facts-json",
                    result["json"],
                    "--profile",
                    "concise",
                    "--min-chars",
                    "800",
                    "--scenario-min",
                    "2",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            concise_result = json.loads(proc.stdout)
            self.assertTrue(concise_result["passed"])
            self.assertEqual(concise_result["profile"], "concise")

            alt_concise_article = rel_run / "drafts" / "relationship-alt-concise.md"
            alt_concise_article.write_text(
                "# 阿甲与阿乙合盘：同城里的强吸引，慢慢确认更入心\n\n"
                "## 合盘总评\n"
                "**阿甲与阿乙这组合盘的核心，是在暧昧观察里慢慢确认彼此的吸引。**"
                "阿甲与阿乙是暧昧观察关系，也是同城关系；乙庚合金、甲庚冲、丁壬合木、寅申冲、寅巳刑、巳亥冲、寅亥六合木、寅亥破、寅巳害、寅申刑都说明阿甲与阿乙之间有靠近感，也有互相试探的张力。"
                "金星、火星、月亮、紫微、西洋占星、MBTI、INTJ、ENFP一起看，阿甲与阿乙有明显火花，也适合把火花放进更清楚的表达。"
                "同城让两个人更容易验证感觉，阿甲与阿乙不用只靠想象判断关系温度，可以从见面后的自然度、聊天后的余味、忙碌时的回应方式里看彼此是否真的愿意靠近。\n\n"
                "## 吸引与互补\n"
                "白话场景：阿甲更容易用判断、计划和观察确认关系，阿乙更容易用热度、回应和情绪流动打开关系。"
                "**阿甲与阿乙的互补感，来自一个想看清楚，一个想让关系动起来。**"
                "阿甲与阿乙如果愿意把吸引说清楚，关系会从猜测进入更真实的互动。阿甲可以把观察说得柔和一点，阿乙可以把热度落到稳定一点的回应里。这样一来，阿甲不会觉得阿乙只是情绪上头，阿乙也不会觉得阿甲只是在评估自己。"
                "这组互补最有价值的地方，是两个人都能补到对方短板：阿甲给阿乙方向和判断，阿乙给阿甲流动感和亲近感。\n\n"
                "## 容易误读的地方\n"
                "情景推演：阿甲慢一点时，阿乙可能会以为热度下降；阿乙快一点时，阿甲也可能觉得节奏太满。"
                "**真正容易误读的，不是有没有吸引，而是谁用什么速度确认吸引。**"
                "阿甲与阿乙适合把自己的节奏讲出来。阿甲慢，是在确认这段关系是否可靠；阿乙快，是在确认这段关系是否有回应。两个人如果能把这层差异说开，很多小误会会变成更懂彼此的入口。"
                "暧昧观察阶段最怕的不是没有感觉，而是感觉存在，却因为表达方式不同而互相误读。\n\n"
                "## 事业、家庭、财富与精力\n"
                "阿甲与阿乙在事业上可以互相启发，家庭议题先看相处舒服度，财富主题先看见面成本和时间投入，精力主题则看忙碌时是否愿意解释。"
                "**关系要继续推进，事业、家庭、财富和精力都要从现实安排里看诚意。**"
                "阿甲与阿乙不用一开始就把所有未来讲死，但可以把可见的安排做出来。比如谁更主动约见面，谁更愿意为沟通留时间，谁在累的时候还愿意说明状态，这些都会比口头承诺更能说明关系质量。"
                "同城的优势在于验证成本低，阿甲与阿乙如果愿意把时间、金钱、情绪和现实节奏放到台面上，关系会比单纯暧昧更稳。\n\n"
                "## 未来两到五年\n"
                "未来重点是把同城的便利用起来，而不是让关系停在暧昧想象里。阿甲与阿乙越能把见面、沟通、投入和边界说清楚，越容易让关系越走越稳。"
                "如果阿甲与阿乙后续能把好感变成稳定互动，把试探变成明确表达，把临时兴起变成可以期待的安排，这段关系就会更容易从暧昧观察走向真正的承接。"
                "阿甲与阿乙都不用急着用一个词给关系盖章，更适合用一段时间看双方是否愿意持续投入。"
                "对阿甲与阿乙来说，最好的推进方式是让每一次靠近都有回声：见面后有复盘，忙碌时有说明，想念时有表达，犹豫时也能把话说得真诚。"
                "这样关系会更自然，也更容易被双方安心接住，并逐渐形成稳定期待。"
                "**这段关系值得继续观察和认真经营，阿甲与阿乙越能把差异翻译成爱语，越容易更稳。**",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(alt_concise_article),
                    "--facts-json",
                    str(alt_facts_path),
                    "--profile",
                    "concise",
                    "--min-chars",
                    "800",
                    "--scenario-min",
                    "2",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            alt_concise_result = json.loads(proc.stdout)
            self.assertTrue(alt_concise_result["passed"])
            self.assertNotIn("男女朋友", alt_concise_result["missing"])
            self.assertNotIn("异地", alt_concise_result["missing"])
            self.assertNotIn("ENTP-A", alt_concise_result["missing"])
            self.assertNotIn("ISFP-T", alt_concise_result["missing"])

            work_concise_article = rel_run / "drafts" / "relationship-work-concise.md"
            work_concise_article.write_text(
                "# 阿甲与阿乙合盘：协同互补型关系，越清楚越能成事\n\n"
                "## 合盘总评\n"
                "**阿甲与阿乙这组合盘的核心，是合作伙伴关系里的互补牵引。**"
                "阿甲与阿乙是合作伙伴，也是同城关系；乙庚合金、甲庚冲、丁壬合木、寅申冲、寅巳刑、巳亥冲、寅亥六合木、寅亥破、寅巳害、寅申刑都说明两个人容易在判断和执行上互相触发。"
                "金星、火星、月亮、紫微、西洋占星、MBTI、INTJ、ENFP一起看，阿甲与阿乙的关系更适合写成信任、协同、节奏和边界。"
                "阿甲与阿乙如果能把分工、沟通频率和反馈方式说清楚，这段关系会更容易从互相欣赏走向稳定合作。\n\n"
                "## 牵引与互补\n"
                "白话场景：阿甲更容易负责判断、计划和结构，阿乙更容易负责流动、表达和外部连接。"
                "**阿甲与阿乙的互补，落在彼此能把事情推进，也能把边界说清。**"
                "阿甲与阿乙适合建立清楚的边界感、信任感和互动距离。阿甲给阿乙稳定框架，阿乙给阿甲变化和反馈，两个人如果尊重各自节奏，就能把差异变成协同价值。"
                "这组盘里的亲近感更适合落在信任、欣赏和配合上，而不是越界推断现实关系。\n\n"
                "## 容易误读的地方\n"
                "情景推演：阿甲慢下来时，阿乙可能以为对方不够投入；阿乙表达太快时，阿甲可能觉得信息太散。"
                "**真正容易误读的，是一个人在校准结构，另一个人在校准回应。**"
                "阿甲与阿乙如果能把反馈节点说清楚，误读会少很多。阿甲不必把阿乙的热度理解成不稳定，阿乙也不必把阿甲的审慎理解成拒绝。"
                "合作伙伴关系最重要的是边界、信任和节奏，阿甲与阿乙越能把规则讲在前面，越容易更稳。\n\n"
                "## 事业、家庭、财富与精力\n"
                "事业上，阿甲与阿乙适合互相补位；家庭生活只写生活承载和边界；财富主题只写资源投入、时间成本和钱账边界；精力主题则看忙碌时如何说明状态。"
                "**这段关系的价值，是把互补变成能执行、能复盘、也能持续优化的合作方式。**"
                "阿甲与阿乙在事业、家庭、财富、精力这些现实专题上，都需要先讲边界，再讲投入。这样的顺序会让关系更安心，也更容易避免因为期待不同而消耗。"
                "如果阿甲与阿乙愿意把资源、时间和反馈机制放到台面上，关系会更有力量。现实里最值得观察的，是两个人是否能在分歧出现时继续把话说完整，而不是让一次卡顿影响整体信任。\n\n"
                "## 未来两到五年\n"
                "未来重点是让协同更清楚，用明确期待减少彼此消耗。2020、2025、2026、2030这些阶段只作为趋势锚点。"
                "阿甲与阿乙越能把合作边界、沟通节奏、资源投入和情绪消耗说清楚，越容易把这段关系经营成稳定支持。"
                "阿甲与阿乙的关系值得继续观察和认真经营，因为它不是单纯热闹，而是有互补、有牵引，也有现实承接空间。"
                "更具体地说，阿甲与阿乙适合把未来两到五年的关系观察点落在三个地方：第一是任务推进时谁更擅长定方向，谁更擅长补反馈；第二是资源投入时能不能提前说清边界，让期待更透明；第三是忙碌或压力上来时，双方是否还能维持基本说明，让沉默少一点误会。"
                "如果这些地方能被稳定处理，阿甲与阿乙的关系会更像长期可复用的协同，也会比一次性的热闹配合更有价值。这样的合盘价值在于让两个人都看见：彼此确实能补位，也确实适合建立规则、节奏和复盘机制。"
                "**对阿甲与阿乙来说，越清楚边界，关系越能长久发挥价值，也越容易更稳。**",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(work_concise_article),
                    "--facts-json",
                    str(work_facts_path),
                    "--profile",
                    "concise",
                    "--min-chars",
                    "800",
                    "--scenario-min",
                    "2",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            work_concise_result = json.loads(proc.stdout)
            self.assertTrue(work_concise_result["passed"])
            self.assertNotIn("吸引", work_concise_result["missing"])
            self.assertNotIn("身体吸引", work_concise_result["missing"])

            work_bad_article = rel_run / "drafts" / "relationship-work-bad-private.md"
            work_bad_article.write_text(
                work_concise_article.read_text(encoding="utf-8")
                + "\n\n阿甲与阿乙这里故意写身体吸引和调情节奏，验证合作伙伴状态不能被写成恋爱化私密关系。\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(work_bad_article),
                    "--facts-json",
                    str(work_facts_path),
                    "--profile",
                    "concise",
                    "--min-chars",
                    "800",
                    "--scenario-min",
                    "2",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            work_bad_result = json.loads(proc.stdout)
            self.assertIn("non-romantic", "\n".join(work_bad_result["format_failures"]))

            alt_second_person_article = rel_run / "drafts" / "relationship-alt-second-person.md"
            alt_second_person_article.write_text(
                alt_concise_article.read_text(encoding="utf-8") + "\n\n你和阿乙这一句故意使用二人称，应该被合盘 validator 拦住。\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(alt_second_person_article),
                    "--facts-json",
                    str(alt_facts_path),
                    "--profile",
                    "concise",
                    "--min-chars",
                    "800",
                    "--scenario-min",
                    "2",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            alt_second_person_result = json.loads(proc.stdout)
            self.assertIn("你和阿乙", alt_second_person_result["forbidden_found"])

            bad_h1_article = rel_run / "drafts" / "relationship-bad-h1.md"
            bad_h1_article.write_text(
                concise_body.replace("# 甲方与乙方合盘：强牵引互补缘，越懂越入心", "# 合盘总评：强牵引互补缘，越懂越入心", 1),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(bad_h1_article),
                    "--facts-json",
                    result["json"],
                    "--profile",
                    "concise",
                    "--min-chars",
                    "800",
                    "--scenario-min",
                    "2",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            bad_h1_result = json.loads(proc.stdout)
            self.assertFalse(bad_h1_result["passed"])
            self.assertIn("must retain both relationship labels", "\n".join(bad_h1_result["format_failures"]))

            bad_delivery_label_article = rel_run / "drafts" / "relationship-bad-delivery-label.md"
            bad_delivery_label_article.write_text(
                concise_body.replace(
                    "# 甲方与乙方合盘：强牵引互补缘，越懂越入心",
                    "# 甲方与乙方合盘长文分析丰富版：强牵引互补缘，越懂越入心",
                    1,
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(bad_delivery_label_article),
                    "--facts-json",
                    result["json"],
                    "--profile",
                    "concise",
                    "--min-chars",
                    "800",
                    "--scenario-min",
                    "2",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            bad_delivery_label_result = json.loads(proc.stdout)
            self.assertFalse(bad_delivery_label_result["passed"])
            joined_delivery_label_failures = "\n".join(bad_delivery_label_result["format_failures"])
            self.assertIn("delivery/process label", joined_delivery_label_failures)
            self.assertIn("internal relationship delivery label", joined_delivery_label_failures)

            bad_article = rel_run / "drafts" / "relationship-bad-tone.md"
            bad_article.write_text(
                "# 甲方与乙方合盘：强牵引互补缘\n\n"
                "## 虽然吸引但是风险很多\n"
                "甲方与乙方是男女朋友，也是异地关系，乙庚合金、金星、火星、MBTI、事业、家庭、财富、精力、未来都在正文里。"
                "白话场景：这段文字用于测试标题是否带有找问题的压力感。"
                "亲密和身体吸引可以写，但这里故意写上床和每周几次亲密，验证器应该拦住这种越界表达。"
                "问题、风险、压力、冲突、矛盾、必须、不能、不要、不适合、很难被连续堆叠时，也应该被识别为找问题清单。"
                "问题、风险、压力、冲突、矛盾、必须、不能、不要、不适合、很难继续重复，会让合盘读起来像劝退。"
                "甲方与乙方这段关系如果认真经营，也仍然值得越走越稳。\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(VALIDATE_RELATIONSHIP_REPORT_SCRIPT),
                    str(bad_article),
                    "--facts-json",
                    result["json"],
                    "--profile",
                    "concise",
                    "--min-chars",
                    "100",
                    "--scenario-min",
                    "0",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0)
            bad_result = json.loads(proc.stdout)
            self.assertFalse(bad_result["passed"])
            joined_failures = "\n".join(bad_result["format_failures"])
            self.assertIn("reader-facing appraisals", joined_failures)
            self.assertIn("explicit/private markers", joined_failures)
            self.assertIn("concrete frequency", joined_failures)
            self.assertIn("pressure-framed", joined_failures)
            self.assertIn("process/editorial scaffolding", joined_failures)

    def test_create_relationship_workspace_builds_external_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_run = root / "runs" / "person-a" / "run_demo"
            b_run = root / "runs" / "person-b" / "run_demo"
            for run in [a_run, b_run]:
                (run / "data").mkdir(parents=True, exist_ok=True)

            a_bazi = a_run / "data" / "person-a-bazi.json"
            b_bazi = b_run / "data" / "person-b-bazi.json"
            a_western = a_run / "data" / "person-a-western.json"
            b_western = b_run / "data" / "person-b-western.json"
            a_ziwei = a_run / "data" / "person-a-ziwei.json"
            b_ziwei = b_run / "data" / "person-b-ziwei.json"
            a_bazi.write_text(
                json.dumps(
                    {
                        "facts": {
                            "pillars": {"year": "戊寅", "month": "戊午", "day": "庚戌", "hour": "丁丑"},
                            "day_master": "庚",
                            "flow": {"current_dayun": {"gan_zhi": "辛酉", "start_year": 2020, "end_year": 2029}},
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            b_bazi.write_text(
                json.dumps(
                    {
                        "facts": {
                            "pillars": {"year": "甲申", "month": "壬申", "day": "乙亥", "hour": "辛巳"},
                            "day_master": "乙",
                            "flow": {"current_dayun": {"gan_zhi": "庚午", "start_year": 2020, "end_year": 2029}},
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            a_western.write_text(
                json.dumps({"facts": {"placements": [{"body": "金星", "sign": "双子", "absolute_longitude": 68.59}]}}, ensure_ascii=False),
                encoding="utf-8",
            )
            b_western.write_text(
                json.dumps({"facts": {"placements": [{"body": "火星", "sign": "处女", "absolute_longitude": 158.62}]}}, ensure_ascii=False),
                encoding="utf-8",
            )
            a_ziwei.write_text(
                json.dumps({"facts": {"current_decadal": {"name": "福德宫", "major_stars": ["天梁"]}}}, ensure_ascii=False),
                encoding="utf-8",
            )
            b_ziwei.write_text(
                json.dumps({"facts": {"current_decadal": {"name": "兄弟宫", "major_stars": ["破军"]}}}, ensure_ascii=False),
                encoding="utf-8",
            )
            a_manifest = a_run / "case_manifest.json"
            b_manifest = b_run / "case_manifest.json"
            a_manifest.write_text(
                json.dumps(
                    {
                        "case_id": "person-a",
                        "paths": {"data_dir": str(a_run / "data")},
                        "artifacts": {"data": {"bazi": str(a_bazi), "western": str(a_western), "ziwei": str(a_ziwei)}},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            b_manifest.write_text(
                json.dumps(
                    {
                        "case_id": "person-b",
                        "paths": {"data_dir": str(b_run / "data")},
                        "artifacts": {"data": {"bazi": str(b_bazi), "western": str(b_western), "ziwei": str(b_ziwei)}},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(CREATE_RELATIONSHIP_WORKSPACE_SCRIPT),
                    "--external-root",
                    str(root),
                    "--case-id",
                    "relationship-demo",
                    "--run-id",
                    "run_demo",
                    "--person-a-manifest",
                    str(a_manifest),
                    "--person-b-manifest",
                    str(b_manifest),
                    "--person-a-label",
                    "甲方",
                    "--person-b-label",
                    "乙方",
                    "--relationship-status",
                    "男女朋友",
                    "--distance-status",
                    "异地",
                    "--person-a-mbti-type",
                    "ENTP-A",
                    "--person-b-mbti-type",
                    "ISFP-T",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            rel_manifest = Path(result["manifest"])
            self.assertTrue(rel_manifest.exists())
            self.assertFalse(rel_manifest.resolve().is_relative_to(PROJECT_ROOT.resolve()))
            manifest = json.loads(rel_manifest.read_text(encoding="utf-8"))
            run_dir = Path(manifest["paths"]["run_dir"])
            self.assertEqual(manifest["relationship_context"]["relationship_status"], "男女朋友")
            self.assertEqual(manifest["relationship_context"]["distance_status"], "异地")
            expectations = manifest["validation_expectations"]
            self.assertEqual(expectations["required_data"], ["relationship"])
            self.assertEqual(manifest["relationship_context"]["person_a_label"], "甲方")
            self.assertEqual(manifest["relationship_context"]["person_b_label"], "乙方")
            self.assertEqual(manifest["relationship_context"]["relationship_status"], "男女朋友")
            self.assertEqual(manifest["relationship_context"]["distance_status"], "异地")
            self.assertIn("relationship_fact_archive_markdown", expectations["required_artifacts"])
            self.assertIn("relationship_workflow", expectations["required_artifacts"])
            self.assertIn("relationship_mobile_html", expectations["required_artifacts"])
            self.assertIn("relationship_concise_source_markdown", expectations["required_artifacts"])
            self.assertIn("relationship_concise_pdf", expectations["required_artifacts"])
            self.assertIn("relationship_concise_mobile_html", expectations["required_artifacts"])
            self.assertNotIn("relationship_concise_markdown", expectations["required_artifacts"])
            self.assertNotIn("relationship_concise_docx", expectations["required_artifacts"])
            self.assertEqual(expectations["required_delivery_variants"], ["rich", "relationship_concise"])
            self.assertEqual(
                expectations["reader_delivery_artifacts"],
                [
                    "longform_pdf",
                    "relationship_mobile_html",
                    "relationship_concise_pdf",
                    "relationship_concise_mobile_html",
                ],
            )
            self.assertIn("关系总评", expectations["longform_markers"])
            self.assertIn("综合评语", expectations["longform_markers"])
            self.assertNotIn("关系总评：强牵引互补缘，越懂越入心", expectations["longform_markers"])
            self.assertEqual(expectations["fact_archive_markers"], ["合盘事实复查档案", "现实专题交集事实", "写作约束"])
            self.assertTrue((run_dir / "runtime" / "knowledge_context.json").exists())
            self.assertTrue((run_dir / "runtime" / "retrospective_intake.json").exists())
            self.assertTrue((run_dir / "calibration" / "retrospective-intake.md").exists())
            knowledge_context = json.loads((run_dir / "runtime" / "knowledge_context.json").read_text(encoding="utf-8"))
            self.assertIn("relationship", knowledge_context["selected_modules"])
            knowledge_paths = {item["path"] for item in knowledge_context["knowledge_files"]}
            self.assertIn("templates/relationship-rich-template.md", knowledge_paths)
            relationship_requirements = {
                item["id"]: item for item in knowledge_context["retrospective_requirements"]
            }
            collection_plan = {
                item["domain"]: item for item in knowledge_context["retrospective_collection_plan"]
            }
            if "relationship" in collection_plan:
                relationship_plan = collection_plan["relationship"]
                self.assertIn("templates/relationship-rich-template.md", relationship_plan["suggested_target_artifacts"])
                self.assertIn("scripts/validate_relationship_report.py", relationship_plan["suggested_target_artifacts"])
            else:
                self.assertEqual(relationship_requirements["REQ-RETRO-RELATIONSHIP"]["needed_entries"], 0)
            retrospective_intake = json.loads((run_dir / "runtime" / "retrospective_intake.json").read_text(encoding="utf-8"))
            intake_domains = {item["domain"] for item in retrospective_intake["retrospective_collection_plan"]}
            if "relationship" not in intake_domains:
                self.assertEqual(relationship_requirements["REQ-RETRO-RELATIONSHIP"]["needed_entries"], 0)
            intake_markdown = (run_dir / "calibration" / "retrospective-intake.md").read_text(encoding="utf-8")
            if "relationship" in intake_domains:
                self.assertIn("templates/relationship-rich-template.md", intake_markdown)
            self.assertTrue(Path(manifest["artifacts"]["data"]["relationship"]).exists())
            self.assertTrue(Path(manifest["artifacts"]["relationship_fact_archive_markdown"]).exists())
            self.assertEqual(
                manifest["artifacts"]["relationship_concise_source_markdown"],
                str(run_dir / "drafts" / "relationship-demo-relationship-concise.md"),
            )
            workflow_path = Path(manifest["artifacts"]["relationship_workflow"])
            workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
            self.assertIn("手机阅读 HTML 使用单盘/合盘统一阅读器 UI 标准。", workflow["reader_contract"])
            self.assertIn("validate_relationship_report.py", workflow["commands"]["validate"])
            self.assertIn(str(Path(manifest["artifacts"]["data"]["relationship"])), workflow["commands"]["validate"])
            self.assertNotIn(str(rel_manifest), workflow["commands"]["validate"])
            self.assertIn("validate_relationship_concise", workflow["commands"])
            self.assertIn("--profile concise", workflow["commands"]["validate_relationship_concise"])
            self.assertIn(
                str(Path(manifest["artifacts"]["data"]["relationship"])),
                workflow["commands"]["validate_relationship_concise"],
            )
            self.assertNotIn(str(rel_manifest), workflow["commands"]["validate_relationship_concise"])
            self.assertIn("package_mobile_html.py", workflow["commands"]["package_mobile_html"])
            self.assertIn("--artifact-key relationship_mobile_html", workflow["commands"]["package_mobile_html"])
            self.assertEqual(workflow["concise_template"], "templates/relationship-concise-template.md")
            self.assertIn("relationship-concise.md", workflow["concise_draft_target"])
            self.assertIn("package_relationship_concise", workflow["commands"])
            self.assertIn("--artifact-prefix relationship_concise", workflow["commands"]["package_relationship_concise"])
            self.assertIn("--no-subtitle", workflow["commands"]["package_relationship_concise"])
            self.assertNotIn("--subtitle", workflow["commands"]["package_relationship_concise"])
            self.assertNotIn("--zip", workflow["commands"]["package_reader"])
            self.assertNotIn("--zip", workflow["commands"]["package_relationship_concise"])
            self.assertIn("package_relationship_concise_mobile_html", workflow["commands"])
            self.assertIn(
                "--artifact-key relationship_concise_mobile_html",
                workflow["commands"]["package_relationship_concise_mobile_html"],
            )
            self.assertNotIn("--subtitle", workflow["commands"]["package_relationship_concise_mobile_html"])
            self.assertIn("完整交付默认另写合盘简洁版", "\n".join(workflow["reader_contract"]))
            self.assertIn("对外读者交付默认为丰富 PDF", "\n".join(workflow["reader_contract"]))
            self.assertIn("H1 必须保留双方对象和合盘属性。", workflow["reader_contract"])

    def test_relationship_workspace_can_finalize_with_relationship_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_run = root / "runs" / "person-a" / "run_demo"
            b_run = root / "runs" / "person-b" / "run_demo"
            for run in [a_run, b_run]:
                (run / "data").mkdir(parents=True, exist_ok=True)
            a_bazi = a_run / "data" / "person-a-bazi.json"
            b_bazi = b_run / "data" / "person-b-bazi.json"
            a_western = a_run / "data" / "person-a-western.json"
            b_western = b_run / "data" / "person-b-western.json"
            a_ziwei = a_run / "data" / "person-a-ziwei.json"
            b_ziwei = b_run / "data" / "person-b-ziwei.json"
            a_bazi.write_text(json.dumps({"facts": {"pillars": {"year": "戊寅", "month": "戊午", "day": "庚戌", "hour": "丁丑"}, "day_master": "庚", "flow": {"current_dayun": {"gan_zhi": "辛酉", "start_year": 2020, "end_year": 2029}}}}, ensure_ascii=False), encoding="utf-8")
            b_bazi.write_text(json.dumps({"facts": {"pillars": {"year": "甲申", "month": "壬申", "day": "乙亥", "hour": "辛巳"}, "day_master": "乙", "flow": {"current_dayun": {"gan_zhi": "庚午", "start_year": 2020, "end_year": 2029}}}}, ensure_ascii=False), encoding="utf-8")
            a_western.write_text(json.dumps({"facts": {"placements": [{"body": "金星", "sign": "双子", "absolute_longitude": 68.59}]}}, ensure_ascii=False), encoding="utf-8")
            b_western.write_text(json.dumps({"facts": {"placements": [{"body": "火星", "sign": "处女", "absolute_longitude": 158.62}]}}, ensure_ascii=False), encoding="utf-8")
            a_ziwei.write_text(json.dumps({"facts": {"current_decadal": {"name": "福德宫", "major_stars": ["天梁"]}}}, ensure_ascii=False), encoding="utf-8")
            b_ziwei.write_text(json.dumps({"facts": {"current_decadal": {"name": "兄弟宫", "major_stars": ["破军"]}}}, ensure_ascii=False), encoding="utf-8")
            a_manifest = a_run / "case_manifest.json"
            b_manifest = b_run / "case_manifest.json"
            a_manifest.write_text(json.dumps({"case_id": "person-a", "paths": {"data_dir": str(a_run / "data")}, "artifacts": {"data": {"bazi": str(a_bazi), "western": str(a_western), "ziwei": str(a_ziwei)}}}, ensure_ascii=False), encoding="utf-8")
            b_manifest.write_text(json.dumps({"case_id": "person-b", "paths": {"data_dir": str(b_run / "data")}, "artifacts": {"data": {"bazi": str(b_bazi), "western": str(b_western), "ziwei": str(b_ziwei)}}}, ensure_ascii=False), encoding="utf-8")

            created = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(CREATE_RELATIONSHIP_WORKSPACE_SCRIPT),
                    "--external-root",
                    str(root),
                    "--case-id",
                    "relationship-demo",
                    "--run-id",
                    "run_demo",
                    "--person-a-manifest",
                    str(a_manifest),
                    "--person-b-manifest",
                    str(b_manifest),
                    "--person-a-label",
                    "甲方",
                    "--person-b-label",
                    "乙方",
                    "--relationship-status",
                    "男女朋友",
                    "--distance-status",
                    "异地",
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
            draft = run_dir / "drafts" / "relationship-demo-relationship-longform.md"
            headings = load_relationship_headings()
            body = ["# 甲方与乙方合盘：强牵引互补缘，越懂越入心", ""]
            for idx, heading in enumerate(headings, start=1):
                body.append(f"## {heading}")
                if idx % 3 == 0:
                    body.append(
                        "甲方与乙方在这一层会先出现现实画面：一个人推进很快，一个人确认很细，"
                        "两个人都不是没感觉，而是在用不同方式确认安全感和可持续性。"
                    )
                    body.append(
                        "**真正该记住的是，差异不是把关系推远，而是提醒两个人把喜欢翻译成更能被接住的行动。**"
                    )
                else:
                    body.append(
                        "**甲方与乙方合盘在这里先给出白话判断：这段关系有吸引、有互补，也需要靠现实节奏承接。**"
                        "这份合盘把两个人怎样靠近、怎样误读、怎样经营写清楚。"
                        "关系总评、八字、西占、紫微和 MBTI 都只作为可复查锚点，最终落到相处、事业、家庭和精力。"
                    )
                body.append("")
            draft.write_text("\n".join(body), encoding="utf-8")
            manifest["validation_expectations"]["min_longform_chars"] = 1000
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            final_delivery = run_dir / "final-delivery.md"
            final_delivery.write_text("# final delivery\n\n合盘 final delivery 验收记录。" * 8, encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_READER_DELIVERY_SCRIPT),
                    str(draft),
                    "--output-dir",
                    str(run_dir / "delivery"),
                    "--basename",
                    "甲方与乙方合盘总评-丰富版",
                    "--zip",
                    str(run_dir / "delivery" / "relationship-rich.zip"),
                    "--manifest",
                    str(manifest_path),
                    "--artifact-prefix",
                    "rich",
                    "--json",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            delivery_md = run_dir / "delivery" / "甲方与乙方合盘总评-丰富版.md"
            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_MOBILE_HTML_SCRIPT),
                    str(delivery_md),
                    "--output",
                    str(run_dir / "delivery" / "甲方与乙方合盘总评-丰富版-手机阅读.html"),
                    "--manifest",
                    str(manifest_path),
                    "--artifact-key",
                    "relationship_mobile_html",
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
                    "-X",
                    "utf8",
                    str(FINALIZE_CASE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--normalize-manifest",
                    "--write-status",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = json.loads(proc.stdout)
            self.assertFalse(result["passed"])
            self.assertTrue(any("relationship_concise" in failure for failure in result["failures"]))
            self.assertTrue(result["relationship_concise"]["expected"])
            self.assertFalse(result["relationship_concise"]["draft_exists"])
            self.assertFalse(result["relationship_concise"]["delivery_complete"])
            self.assertTrue(any("relationship concise" in warning for warning in result["warnings"]))
            repairs = "\n".join(result["repair_commands"])
            self.assertIn("relationship-concise.md", repairs)
            self.assertIn("templates/relationship-concise-template.md", repairs)
            self.assertIn("validate_relationship_report.py", repairs)
            self.assertIn("--profile concise", repairs)
            self.assertIn("--artifact-prefix relationship_concise", repairs)
            self.assertIn("--artifact-key relationship_concise_mobile_html", repairs)
            self.assertIn("finalize_case.py", repairs)
            status_after_warning = json.loads(manifest_path.read_text(encoding="utf-8"))["status"]
            self.assertFalse(status_after_warning["finalize_passed"])
            self.assertTrue(any("relationship_concise" in failure for failure in status_after_warning["finalize_failures"]))
            self.assertTrue(any("relationship concise" in warning for warning in status_after_warning["finalize_warnings"]))
            self.assertIn("finalize_repair_commands", status_after_warning)
            self.assertTrue(any("relationship-concise.md" in command for command in status_after_warning["finalize_repair_commands"]))
            self.assertFalse(status_after_warning["relationship_concise"]["delivery_complete"])
            self.assertTrue(result["relationship_facts"]["schema_checked"])
            self.assertEqual(
                set(result["relationship_facts"]["life_domains"]),
                {"career", "family_life", "wealth_resources", "health_energy", "intimacy_private"},
            )

            concise_draft = Path(result["relationship_concise"]["draft_target"])
            concise_draft.write_text(
                "# 甲方与乙方合盘简洁版\n\n"
                "## 合盘总评\n\n"
                "**甲方与乙方这组关系有吸引、有互补，也需要现实承接。**\n\n"
                "甲方与乙方的关系重点不是把差异抹平，而是把吸引、节奏、现实安排和安全感放在同一张桌上谈清楚。\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_READER_DELIVERY_SCRIPT),
                    str(concise_draft),
                    "--output-dir",
                    str(run_dir / "delivery"),
                    "--basename",
                    "甲方与乙方合盘简洁版",
                    "--manifest",
                    str(manifest_path),
                    "--artifact-prefix",
                    "relationship_concise",
                    "--json",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_MOBILE_HTML_SCRIPT),
                    str(run_dir / "delivery" / "甲方与乙方合盘简洁版.md"),
                    "--output",
                    str(run_dir / "delivery" / "甲方与乙方合盘简洁版-手机阅读.html"),
                    "--manifest",
                    str(manifest_path),
                    "--artifact-key",
                    "relationship_concise_mobile_html",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            relationship_json = Path(json.loads(manifest_path.read_text(encoding="utf-8"))["artifacts"]["data"]["relationship"])
            original_relationship_json = relationship_json.read_text(encoding="utf-8")
            legacy_relationship_payload = json.loads(original_relationship_json)
            legacy_relationship_payload.pop("relationship_life_domains", None)
            relationship_json.write_text(json.dumps(legacy_relationship_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(FINALIZE_CASE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--normalize-manifest",
                    "--write-status",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            legacy_finalize = json.loads(proc.stdout)
            self.assertFalse(legacy_finalize["passed"])
            self.assertTrue(
                any("relationship_life_domains" in failure for failure in legacy_finalize["failures"])
            )
            legacy_repairs = "\n".join(legacy_finalize["repair_commands"])
            self.assertIn("build_relationship_facts.py", legacy_repairs)
            self.assertIn('--person-a-label "甲方"', legacy_repairs)
            self.assertIn('--person-b-label "乙方"', legacy_repairs)
            self.assertIn('--relationship-status "男女朋友"', legacy_repairs)
            self.assertIn('--distance-status "异地"', legacy_repairs)
            relationship_json.write_text(original_relationship_json, encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(FINALIZE_CASE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--normalize-manifest",
                    "--write-status",
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = json.loads(proc.stdout)
            self.assertTrue(result["relationship_concise"]["draft_exists"])
            self.assertTrue(result["relationship_concise"]["delivery_complete"])
            self.assertTrue(result["relationship_facts"]["schema_checked"])
            self.assertEqual(
                set(result["relationship_facts"]["life_domains"]),
                {"career", "family_life", "wealth_resources", "health_energy", "intimacy_private"},
            )
            self.assertFalse(any("relationship concise" in warning for warning in result["warnings"]))
            self.assertEqual(result["repair_commands"], [])
            finalized = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(finalized["status"]["finalize_warnings"], [])
            self.assertEqual(finalized["status"]["finalize_repair_commands"], [])
            self.assertTrue(finalized["status"]["relationship_concise"]["delivery_complete"])
            self.assertTrue(Path(finalized["artifacts"]["relationship_workflow"]).exists())
            self.assertTrue(Path(finalized["artifacts"]["relationship_mobile_html"]).exists())
            self.assertEqual(finalized["artifacts"]["relationship_concise_source_markdown"], str(concise_draft))
            self.assertEqual(finalized["artifacts"]["data"]["relationship"], str(run_dir / "data" / "relationship-demo-relationship.json"))



if __name__ == "__main__":
    unittest.main()
