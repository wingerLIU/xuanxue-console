#!/usr/bin/env python3
"""Smoke tests for xuanxue_console.py."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("xuanxue_console.py")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CREATE_WORKSPACE_SCRIPT = Path(__file__).with_name("create_case_workspace.py")
AUDIT_WORKSPACE_SCRIPT = Path(__file__).with_name("audit_case_workspace.py")
KNOWLEDGE_CONTEXT_SCRIPT = Path(__file__).with_name("build_knowledge_context.py")
RETRO_INTAKE_SCRIPT = Path(__file__).with_name("create_retrospective_intake.py")
RETRO_CANDIDATE_SCRIPT = Path(__file__).with_name("create_case_retrospective_candidate.py")
PROMOTE_RETRO_SCRIPT = Path(__file__).with_name("promote_case_retrospective.py")
AUDIT_CASE_RETROSPECTIVES_SCRIPT = Path(__file__).with_name("audit_case_retrospectives.py")
CHECK_SOURCE_URLS_SCRIPT = Path(__file__).with_name("check_source_urls.py")
AUDIT_SOURCE_DOCUMENTATION_SCRIPT = Path(__file__).with_name("audit_source_documentation.py")
AUDIT_KNOWLEDGE_COVERAGE_SCRIPT = Path(__file__).with_name("audit_knowledge_coverage.py")
AUDIT_PROMOTION_MANIFEST_SCRIPT = Path(__file__).with_name("audit_promotion_manifest.py")
AUDIT_RULE_CARDS_SCRIPT = Path(__file__).with_name("audit_rule_cards.py")
VALIDATE_LONGFORM_SCRIPT = Path(__file__).with_name("validate_longform_report.py")
AUDIT_LONGFORM_CONSISTENCY_SCRIPT = Path(__file__).with_name("audit_longform_consistency.py")
FINALIZE_CASE_SCRIPT = Path(__file__).with_name("finalize_case.py")
MANIFEST_CONTRACT_SCRIPT = Path(__file__).with_name("case_manifest_contract.py")
FOLLOWUP_CONTEXT_SCRIPT = Path(__file__).with_name("create_followup_context.py")
FACT_ARCHIVE_SCRIPT = Path(__file__).with_name("build_fact_archive.py")


def load_longform_validator():
    spec = importlib.util.spec_from_file_location("validate_longform_report", VALIDATE_LONGFORM_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate_longform_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_finalize_case():
    spec = importlib.util.spec_from_file_location("finalize_case", FINALIZE_CASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load finalize_case.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_manifest_contract():
    spec = importlib.util.spec_from_file_location("case_manifest_contract", MANIFEST_CONTRACT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load case_manifest_contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cmd(*args: str) -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return json.loads(proc.stdout.decode("utf-8"))


class XuanxueConsoleTests(unittest.TestCase):
    def assert_schema(self, data: dict, module: str) -> None:
        self.assertEqual(data["schema_version"], "0.2.0")
        self.assertEqual(data["module"], module)
        for key in ["input", "facts", "warnings", "uncertainties", "interpretation_hints", "calibration_questions", "raw"]:
            self.assertIn(key, data)

    def make_reader_rich_article(self, *, second_person: bool = True, opening_extra: str = "") -> str:
        validator = load_longform_validator()
        h3_by_section = {
            "13 六大专题分析": validator.READER_RICH_REQUIRED_H3[:6],
            "15 技术证据附录": validator.READER_RICH_REQUIRED_H3[6:],
        }
        sections: list[str] = ["# 读者丰富版测试稿", ""]
        if second_person:
            voice = (
                "你在现实里最需要看见的是自己的判断方式。"
                "你不是缺少能力，而是容易把能量花在证明、解释和重复确认上。"
                "别人可能会误读你太强势，风险在于你把真实需求压到最后。"
                "更好的做法是把目标、边界和交付物提前讲清楚。"
            )
        else:
            voice = (
                "当事人在现实里最需要看见的是自身判断方式。"
                "当事人不是缺少能力，而是容易把能量花在证明、解释和重复确认上。"
                "别人可能会误读其过于强势，风险在于真实需求被压到最后。"
                "更好的做法是把目标、边界和交付物提前讲清楚。"
            )
        common_markers = (
            "命理 紫微 西洋占星 三套体系 过去几年 未来几年 事业 财富 爱情 健康 建议 "
            "判断型摘要 摘要 先看结论 基础排盘信息 时间可信度 时间敏感性 八字总论 神煞 "
            "紫微总论 西洋占星总论 主要相位 三方合参 现实关系全景 六大专题分析 技术证据附录 校准问题 "
            "盘面触发 现实倾向 可校准问题"
        )
        opening_markers = (
            "命理 紫微 西洋占星 三套体系 过去几年 未来几年 事业 财富 爱情 健康 建议 "
            "判断型摘要 摘要 先看结论 八字总论 神煞 紫微总论 西洋占星总论 主要相位 "
            "三方合参 现实关系全景 六大专题分析 技术证据附录 校准问题 "
            "盘面触发 现实倾向 可校准问题"
        )
        long_neutral = (
            "这部分用白话把结构落到现实选择里，强调可观察表现、可验证反馈和可调整动作。"
            "重点不是堆砌术语，而是把证据变成稳定的生活判断，方便后续复盘和校准。"
        )
        for idx, heading in enumerate(validator.READER_RICH_HEADINGS, start=1):
            sections.append(f"## {heading}")
            if heading == "01 判断型摘要" and opening_extra:
                sections.append(opening_extra)
            label = "白话场景" if idx % 2 else "情景推演"
            markers = opening_markers if heading == "01 判断型摘要" else common_markers
            sections.append(f"{label}：{voice}{markers}")
            sections.append(long_neutral * 12)
            for h3 in h3_by_section.get(heading, []):
                sections.append(f"### {h3}")
                sections.append(f"{voice}{long_neutral * 8}")
            sections.append("")
        return "\n".join(sections)

    def run_longform_validator(self, text: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "article.md"
            article.write_text(text, encoding="utf-8")
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(
                [sys.executable, "-X", "utf8", str(VALIDATE_LONGFORM_SCRIPT), str(article), "--profile", "reader-rich"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
                env=env,
            )
            return proc, json.loads(proc.stdout)

    def make_reader_concise_article(self, *, internal_terms: str = "") -> str:
        sections = [
            "# 乙方命盘：慢热不是退缩，是在确认谁值得放心",
            "",
            "## 先说最像你的地方",
            "**你最该记住的是，慢热不是退缩，而是在确认谁值得你放心。**",
            "你在关系和工作里都不是没有反应，而是会先观察对方是否稳定、是否尊重你的节奏。"
            "你越被催，越容易退回自己的壳里；你越被认真对待，越能把温柔、审美和执行力拿出来。",
            internal_terms,
            "",
            "## 专业锚点",
            "**专业锚点不用铺满，关键是它们都指向同一条主线。**",
            "你的命盘里，专业锚点需要服务于现实判断：四柱、大运、紫微和西洋占星只保留稳定项。"
            "这不是术语展示，而是在说明你为什么会先观察、再投入，也为什么适合把细腻变成作品和长期能力。",
            "",
            "## 底层矛盾",
            "**你真正要处理的，不是敏感本身，而是敏感之后怎么表达。**",
            "你容易先感受到气氛变化，再决定要不要开口。这个能力让你很会照顾人，也让你容易把压力吞回去。"
            "如果你一直不说，别人会以为你没有需求；如果你一下子说太满，又会觉得自己失控。",
            "",
            "## 关系与感情",
            "**你在感情里最需要的不是热闹，而是稳定、被看见和被认真回应。**",
            "你会在细节里确认一个人：回复是否稳定，承诺是否兑现，见面之后是否更安心。"
            "关系里真正适合你的节奏，是先给你安全感，再慢慢打开表达，而不是用忽冷忽热测试你。",
            "",
            "## 事业和钱",
            "**事业和钱的关键，是把你的审美、判断和服务感变成可见成果。**",
            "你适合做需要细节、体验、审美、陪伴和稳定交付的事情。钱和财富不是只看冲劲，"
            "更要看你是否能把边界、预算、回款和合作口径讲清楚。你越能提前定规则，越不容易被情绪消耗。",
            "",
            "## 未来三到五年",
            "**未来几年最值得你做的，是把喜欢的事做成稳定节奏。**",
            "你不适合只靠短期兴奋推进人生。未来三到五年，事业、关系和生活都会反复提醒你："
            "不要只看当下感受，也要看对方是否能长期承接你的节奏。你稳下来，机会才更容易留下来。",
            "",
            "## 自查问题",
            "**自查的目的不是怀疑自己，而是帮你确认这份报告是否贴近真实经历。**",
            "你可以问自己：你是不是越喜欢越谨慎？你是不是在工作里很在意细节和感受？"
            "你是不是遇到催促时容易沉默？你是不是只有在足够安心时，才愿意表达真正想要什么？",
            "",
            "## 收束建议",
            "**最后要带走的一句话是：你不是不够坚定，你只是需要把感受翻译成清楚的选择。**",
            "建议你少用沉默让别人猜，多用具体表达保护自己。传统文化与自我观察只能作为参考，"
            "不替代医疗、法律、投资或重大关系决定。",
            "",
        ]
        filler = (
            "你可以把这段当成现实里的反复提醒：先观察没有错，但不要让观察变成长期拖延。"
            "你越能把感受、边界和行动说清楚，越容易遇到愿意认真承接你的人和机会。"
        )
        return "\n".join(sections) + filler * 70

    def run_concise_validator(self, text: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "concise.md"
            article.write_text(text, encoding="utf-8")
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(
                [sys.executable, "-X", "utf8", str(VALIDATE_LONGFORM_SCRIPT), str(article), "--profile", "reader-concise"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
                env=env,
            )
            return proc, json.loads(proc.stdout)

    def write_retrospective_control_files(self, retro_dir: Path) -> None:
        retro_dir.mkdir(parents=True, exist_ok=True)
        body = "去隐私复盘控制文件。只用于测试目录，不包含客户资料、本机路径、出生资料或交付正文。" * 4
        for name in ["README.md", "promotion-protocol.md", "template.md"]:
            (retro_dir / name).write_text(f"# {name}\n\n{body}\n", encoding="utf-8")

    def test_mbti_schema(self) -> None:
        data = run_cmd("mbti", "--type", "INTJ")
        self.assert_schema(data, "mbti")
        self.assertEqual(data["facts"]["type"], "INTJ")

    def test_reader_rich_validator_accepts_second_person_article(self) -> None:
        proc, result = self.run_longform_validator(self.make_reader_rich_article())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(result["passed"])
        self.assertGreaterEqual(result["second_person_count"], 20)

    def test_reader_rich_validator_blocks_process_opening(self) -> None:
        article = self.make_reader_rich_article(opening_extra="截图显示基准盘如下，所以先说明基础排盘信息。")
        proc, result = self.run_longform_validator(article)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(result["passed"])
        self.assertTrue(any("opening summary contains process or raw-data terms" in item for item in result["format_failures"]))
        self.assertIn("截图显示", result["forbidden_found"])

    def test_reader_rich_validator_blocks_internal_discussion_terms(self) -> None:
        article = self.make_reader_rich_article(
            opening_extra=(
                "这段文字混入项目流程、外部 run、过程产物、用于约束AI、新加段落、"
                "乐观收束、情绪价值、真实感增强、小红书、新媒体图文、找问题、找茬和编辑话术。"
            )
        )
        proc, result = self.run_longform_validator(article)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(result["passed"])
        for marker in [
            "项目流程",
            "外部 run",
            "过程产物",
            "用于约束AI",
            "新加段落",
            "乐观收束",
            "情绪价值",
            "真实感增强",
            "小红书",
            "新媒体图文",
            "找问题",
            "找茬",
            "编辑话术",
        ]:
            self.assertIn(marker, result["forbidden_found"])

    def test_reader_rich_validator_blocks_versioned_delivery_title(self) -> None:
        article = self.make_reader_rich_article().replace("# 读者丰富版测试稿", "# 乙方命盘丰富版v5：越稳越能成事", 1)
        proc, result = self.run_longform_validator(article)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(result["passed"])
        joined = "\n".join(result["format_failures"])
        self.assertIn("H1 title should be a report appraisal", joined)
        self.assertIn("versioned delivery label", joined)

    def test_reader_concise_validator_accepts_reader_report(self) -> None:
        proc, result = self.run_concise_validator(self.make_reader_concise_article())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(result["passed"])
        self.assertEqual(result["profile"], "reader-concise")
        self.assertGreaterEqual(result["chars"], 5500)
        self.assertGreaterEqual(result["second_person_count"], 10)

    def test_reader_concise_validator_blocks_internal_terms_and_weak_structure(self) -> None:
        article = (
            "# 乙方命盘简洁版v3：测试标题\n\n"
            "## 只有一节\n\n"
            "你可以看看。这里混入小红书、情绪价值、真实感增强、项目流程和外部 run。"
        )
        proc, result = self.run_concise_validator(article)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(result["passed"])
        joined = "\n".join(result["format_failures"])
        self.assertIn("H1 title should be a report appraisal", joined)
        self.assertIn("reader-concise should use at least", joined)
        self.assertIn("reader-concise requires second-person delivery", joined)
        self.assertIn("reader-concise needs at least", joined)
        self.assertIn("小红书", result["forbidden_found"])
        self.assertIn("情绪价值", result["forbidden_found"])
        self.assertIn("真实感增强", result["forbidden_found"])
        self.assertIn("项目流程", result["forbidden_found"])
        self.assertIn("外部 run", result["forbidden_found"])

    def test_reader_rich_validator_requires_second_person_voice(self) -> None:
        proc, result = self.run_longform_validator(self.make_reader_rich_article(second_person=False))
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(result["passed"])
        self.assertLess(result["second_person_count"], 20)
        self.assertTrue(any("second-person delivery" in item for item in result["format_failures"]))

    def test_liuyao_enriched_lines(self) -> None:
        data = run_cmd("liuyao", "--question", "合作能否推进", "--lines", "7,8,9,7,8,6", "--day-gan", "丁")
        self.assert_schema(data, "liuyao")
        self.assertEqual(data["facts"]["moving_lines"], [3, 6])
        self.assertEqual(len(data["facts"]["lines"]), 6)
        self.assertIn("na_jia", data["facts"]["lines"][0])
        self.assertIn("six_spirit", data["facts"]["lines"][0])

    def test_xiaoliuren_schema(self) -> None:
        data = run_cmd("xiaoliuren", "--question", "今天适合推进吗", "--lunar-month", "7", "--lunar-day", "6", "--hour-branch", "丑")
        self.assert_schema(data, "xiaoliuren")
        self.assertEqual(data["facts"]["result"]["state"], "大安")

    def test_western_placements(self) -> None:
        data = run_cmd("western", "--solar", "1991-08-15", "--time", "01:30")
        self.assert_schema(data, "western")
        placements = {row["body"]: row["sign"] for row in data["facts"]["placements"]}
        self.assertEqual(placements["太阳"], "狮子")
        self.assertEqual(placements["月亮"], "天秤")
        aspects = {(row["body_a"], row["body_b"], row["aspect"]) for row in data["facts"]["aspects"]}
        self.assertIn(("太阳", "月亮", "六合"), aspects)
        self.assertIn(("水星", "金星", "合相"), aspects)
        self.assertEqual(data["facts"]["moon_phase"]["phase"], "娥眉月")
        self.assertAlmostEqual(data["facts"]["moon_phase"]["sun_moon_angle"], 60.92)
        retrogrades = {row["body"]: row["retrograde"] for row in data["facts"]["retrogrades"]}
        self.assertTrue(retrogrades["水星"])
        self.assertTrue(retrogrades["天王星"])
        self.assertTrue(retrogrades["海王星"])
        self.assertFalse(retrogrades["冥王星"])
        self.assertTrue(any("未提供出生地经纬度" in warning for warning in data["warnings"]))

    def test_western_angles_with_location(self) -> None:
        data = run_cmd(
            "western",
            "--solar", "1991-08-15",
            "--time", "01:30",
            "--tz-offset", "8",
            "--latitude", "31.23",
            "--longitude", "121.47",
        )
        self.assert_schema(data, "western")
        self.assertEqual(data["warnings"], [])
        houses = data["facts"]["houses"]
        self.assertEqual(houses["angles"]["ascendant"]["sign"], "巨蟹")
        self.assertEqual(houses["angles"]["midheaven"]["sign"], "双鱼")
        self.assertEqual(houses["whole_sign_houses"][0]["sign"], "巨蟹")
        self.assertEqual(houses["whole_sign_houses"][6]["sign"], "摩羯")
        self.assertEqual(len(houses["equal_house_cusps"]), 12)

    def test_combo_and_html_without_birth_deps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            html_path = str(Path(tmp) / "combo.html")
            data = run_cmd(
                "combo",
                "--mbti-type", "INTJ",
                "--question", "合作能否推进",
                "--lines", "7,8,9,7,8,6",
                "--day-gan", "丁",
                "--html", html_path,
            )
            self.assert_schema(data, "combo")
            self.assertEqual([m["module"] for m in data["facts"]["modules"]], ["mbti", "liuyao"])
            self.assertTrue(Path(html_path).exists())

    def test_build_fact_archive_writes_markdown_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            combo = root / "case-a-combo.json"
            archive = root / "case-a-facts.md"
            manifest = root / "case_manifest.json"
            combo.write_text(
                json.dumps(
                    {
                        "schema_version": "0.2.0",
                        "module": "combo",
                        "facts": {
                            "modules": [
                                {
                                    "module": "bazi",
                                    "facts": {
                                        "solar": "1991-08-15",
                                        "pillars": {"year": "辛未", "month": "丙申", "day": "丁巳", "hour": "辛丑"},
                                        "day_master": "丁",
                                        "profiles": {
                                            "ten_gods": {"combined": {"偏财": 3, "正财": 2}},
                                            "elements": {"stems_plus_hidden": {"火": 4, "金": 5}},
                                        },
                                        "flow": {
                                            "as_of": "2026-06-12",
                                            "pillars": {"year": "丙午", "month": "甲午", "day": "丁巳"},
                                            "current_dayun": {"gan_zhi": "壬辰", "start_year": 2023, "end_year": 2032},
                                            "annual_flows": [{"year": 2027, "pillar": "丁未", "dayun": "壬辰"}],
                                        },
                                        "dayun": [{"gan_zhi": "壬辰", "start_year": 2023, "end_year": 2032}],
                                    },
                                },
                                {
                                    "module": "western",
                                    "facts": {
                                        "placements": [{"body": "太阳", "sign": "巨蟹", "longitude": 100.2}],
                                        "houses": {"angles": {"ascendant": {"sign": "金牛"}, "midheaven": {"sign": "摩羯"}}},
                                    },
                                },
                            ]
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            manifest.write_text(json.dumps({"artifacts": {}}, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(FACT_ARCHIVE_SCRIPT),
                    str(combo),
                    "--output",
                    str(archive),
                    "--manifest",
                    str(manifest),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["passed"])
            text = archive.read_text(encoding="utf-8")
            for expected in ["排盘事实复查档案", "辛未 / 丙申 / 丁巳 / 辛丑", "壬辰", "2027", "太阳", "复查约定"]:
                self.assertIn(expected, text)
            updated = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(updated["artifacts"]["fact_archive_markdown"], str(archive.resolve()))
            self.assertEqual(updated["artifacts"]["data"]["combo"], str(combo.resolve()))

    def test_case_retrospective_candidate_stays_external(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "case-a" / "run_demo"
            for name in ["runtime", "data", "drafts", "delivery", "logs", "calibration", "retrospectives"]:
                (run_dir / name).mkdir(parents=True, exist_ok=True)
            manifest = {
                "schema_version": "0.1.0",
                "case_id": "case-a",
                "run_id": "run_demo",
                "created_at": "redacted",
                "project_root": "redacted",
                "paths": {
                    "input_dir": str(root / "inputs" / "case-a"),
                    "run_dir": str(run_dir),
                    "runtime_dir": str(run_dir / "runtime"),
                    "data_dir": str(run_dir / "data"),
                    "drafts_dir": str(run_dir / "drafts"),
                    "delivery_dir": str(run_dir / "delivery"),
                    "logs_dir": str(run_dir / "logs"),
                    "calibration_dir": str(run_dir / "calibration"),
                    "retrospectives_dir": str(run_dir / "retrospectives"),
                },
                "status": {"stage": "test", "human_approved": False},
            }
            manifest_path = run_dir / "case_manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RETRO_CANDIDATE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--slug",
                    "reader-hook",
                    "--title",
                    "去隐私读者摘要机制",
                    "--evidence-summary",
                    "读者更容易接受先给判断再给证据的摘要结构。",
                    "--target-artifact",
                    "knowledge/writing/reader-rich-report.md",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            candidate_path = Path(result["candidate"])
            self.assertTrue(candidate_path.exists())
            self.assertEqual(candidate_path.parent, run_dir / "retrospectives")
            self.assertFalse(candidate_path.resolve().is_relative_to(PROJECT_ROOT.resolve()))
            item = json.loads(candidate_path.read_text(encoding="utf-8"))
            self.assertFalse(item["human_approved"])
            self.assertTrue(item["privacy"]["deidentified"])
            self.assertEqual(item["domains"], ["writing"])
            serialized = json.dumps(item, ensure_ascii=False)
            self.assertNotIn(str(root), serialized)
            self.assertEqual(item["source_case"]["raw_material_location"], "external-only")

            relationship_proc = subprocess.run(
                [
                    sys.executable,
                    str(RETRO_CANDIDATE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--slug",
                    "relationship-feedback",
                    "--title",
                    "去隐私合盘反馈机制",
                    "--evidence-summary",
                    "合盘读者反馈指向关系总评和章节收束方式，需要先落到合盘模板复核。",
                    "--domain",
                    "relationship",
                    "--target-artifact",
                    "templates/relationship-rich-template.md",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            relationship_result = json.loads(relationship_proc.stdout)
            relationship_candidate = json.loads(Path(relationship_result["candidate"]).read_text(encoding="utf-8"))
            self.assertEqual(relationship_candidate["domains"], ["relationship", "writing"])
            self.assertEqual(relationship_candidate["target_artifacts"], ["templates/relationship-rich-template.md"])

    def test_finalize_case_requires_runtime_knowledge_context(self) -> None:
        finalize_case = load_finalize_case()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "runtime"
            calibration_dir = root / "calibration"
            runtime_dir.mkdir()
            calibration_dir.mkdir()
            manifest = {
                "case_id": "case-a",
                "run_id": "run_demo",
                "paths": {
                    "runtime_dir": str(runtime_dir),
                    "calibration_dir": str(calibration_dir),
                },
            }
            plan_item = {
                "domain": "writing",
                "needed_entries": 1,
                "suggested_target_artifacts": ["knowledge/writing/reader-rich-report.md"],
                "candidate_commands": [
                    "python scripts/create_case_retrospective_candidate.py --manifest <RUN_DIR>/case_manifest.json --domain writing --slug demo --title \"去隐私复盘标题\" --evidence-summary \"抽象证据\" --target-artifact knowledge/writing/reader-rich-report.md"
                ],
            }
            question_bank_item = {
                "domain": "writing",
                "label": "写作",
                "requirement_id": "REQ-RETRO-WRITING",
                "gap_id": "GAP-WRITING-LIVE-CLIENT-RETROSPECTIVES",
                "needed_entries": 1,
                "min_status": "curated",
                "questions": ["哪段让读者愿意继续读，哪段像模板话？"],
                "suggested_target_artifacts": ["knowledge/writing/reader-rich-report.md"],
            }
            (runtime_dir / "knowledge_context.json").write_text(
                json.dumps(
                    {
                        "passed": True,
                        "case_id": "case-a",
                        "run_id": "run_demo",
                        "knowledge_files": [{"path": "knowledge/source-index.md"}],
                        "source_entries": [{"id": "SRC-PROJECT-KNOWLEDGE-CONTEXT"}],
                        "retrospective_requirements": [{"id": "REQ-RETRO-WRITING"}],
                        "retrospective_collection_plan": [plan_item],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (runtime_dir / "retrospective_intake.json").write_text(
                json.dumps(
                    {
                        "case_id": "case-a",
                        "run_id": "run_demo",
                        "do_not_promote_without_human_approval": True,
                        "retrospective_collection_plan": [plan_item],
                        "domain_question_bank": [question_bank_item],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (calibration_dir / "retrospective-intake.md").write_text(
                "# Retrospective Intake\n\n## 可以问读者的问题\n\n## 去隐私整理要求\n\ncreate_case_retrospective_candidate.py\n",
                encoding="utf-8",
            )
            failures: list[str] = []
            info = finalize_case.check_runtime_context(manifest, failures)
            self.assertEqual(failures, [])
            self.assertEqual(info["collection_plan_items"], 1)
            self.assertEqual(info["domain_question_bank_items"], 1)
            (runtime_dir / "retrospective_intake.json").write_text(
                json.dumps(
                    {
                        "case_id": "case-a",
                        "run_id": "run_demo",
                        "do_not_promote_without_human_approval": False,
                        "retrospective_collection_plan": [plan_item],
                        "domain_question_bank": [question_bank_item],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            failures = []
            finalize_case.check_runtime_context(manifest, failures)
            self.assertTrue(any("without human approval" in item for item in failures))
            (runtime_dir / "retrospective_intake.json").write_text(
                json.dumps(
                    {
                        "case_id": "case-a",
                        "run_id": "run_demo",
                        "do_not_promote_without_human_approval": True,
                        "retrospective_collection_plan": [plan_item],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            failures = []
            finalize_case.check_runtime_context(manifest, failures)
            self.assertTrue(any("domain_question_bank" in item for item in failures))

    def test_case_manifest_contract_normalizes_legacy_artifacts(self) -> None:
        contract = load_manifest_contract()
        policy = contract.runtime_contract_policy()
        self.assertEqual(policy["legacy_alias_sunset"], "2026-07-31")
        self.assertEqual(
            policy["canonical_required_artifacts"],
            [
                "fact_archive_markdown",
                "longform_markdown",
                "longform_pdf",
                "rich_mobile_html",
                "concise_markdown",
                "concise_pdf",
                "concise_mobile_html",
                "final_delivery",
            ],
        )
        self.assertEqual(policy["canonical_required_data"], ["combo"])
        self.assertEqual(
            policy["canonical_reader_delivery_artifacts"],
            ["longform_pdf", "rich_mobile_html", "concise_pdf", "concise_mobile_html"],
        )
        self.assertEqual(
            policy["relationship_reader_delivery_artifacts"],
            [
                "longform_pdf",
                "relationship_mobile_html",
                "relationship_concise_pdf",
                "relationship_concise_mobile_html",
            ],
        )
        self.assertEqual(policy["optional_debug_artifacts"], ["main_html"])
        self.assertLessEqual(
            Path("scripts/test_xuanxue_console.py").stat().st_size / 1024,
            policy["large_file_split"]["soft_limit_kb"]["scripts/test_xuanxue_console.py"],
        )
        for expected_split in [
            "scripts/test_xuanxue_runtime.py",
            "scripts/test_xuanxue_relationship.py",
            "scripts/test_xuanxue_delivery.py",
        ]:
            self.assertIn(expected_split, policy["large_file_split"]["completed_splits"])
            self.assertTrue((PROJECT_ROOT / expected_split).exists())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "case-a" / "run_demo"
            data_dir = run_dir / "data"
            runtime_dir = run_dir / "runtime"
            drafts_dir = run_dir / "drafts"
            delivery_dir = run_dir / "delivery"
            for path in [data_dir, runtime_dir, drafts_dir, delivery_dir]:
                path.mkdir(parents=True, exist_ok=True)
            html = run_dir / "case-a.html"
            final_delivery = run_dir / "final-delivery.md"
            fact_archive = data_dir / "case-a-facts.md"
            relationship_fact_archive = data_dir / "case-a-relationship-facts.md"
            relationship_workflow = runtime_dir / "relationship_workflow.json"
            longform = drafts_dir / "case-a-longform.md"
            pdf = delivery_dir / "case-a-丰富版.pdf"
            concise_markdown = delivery_dir / "case-a简洁版.md"
            concise_pdf = delivery_dir / "case-a简洁版.pdf"
            combo = data_dir / "case-a-combo.json"
            relationship = data_dir / "case-a-relationship.json"
            for path in [html, final_delivery, fact_archive, relationship_fact_archive, relationship_workflow, longform, pdf, concise_markdown, concise_pdf, combo, relationship]:
                path.write_text("x" * 120, encoding="utf-8")

            manifest = {
                "case_id": "case-a",
                "run_id": "run_demo",
                "paths": {
                    "run_dir": str(run_dir),
                    "data_dir": str(data_dir),
                    "runtime_dir": str(runtime_dir),
                    "drafts_dir": str(drafts_dir),
                    "delivery_dir": str(delivery_dir),
                },
                "artifacts": {
                    "html_report": str(html),
                    "facts_markdown": str(fact_archive),
                    "longform_source_md": str(longform),
                    "reader_pdf": str(pdf),
                    "relationship_mobile_html": str(delivery_dir / "missing-old-relationship-mobile.html"),
                    "data_combo": str(combo),
                },
            }
            normalized, changes = contract.normalize_manifest(manifest)
            self.assertIn("paths.retrospectives_dir", changes)
            self.assertIn("paths.dialogue_dir", changes)
            self.assertEqual(normalized["paths"]["dialogue_dir"], str(run_dir / "calibration" / "dialogue"))
            self.assertEqual(normalized["artifacts"]["main_html"], str(html))
            self.assertEqual(normalized["artifacts"]["fact_archive_markdown"], str(fact_archive))
            self.assertEqual(normalized["artifacts"]["relationship_fact_archive_markdown"], str(relationship_fact_archive))
            self.assertEqual(normalized["artifacts"]["relationship_workflow"], str(relationship_workflow))
            self.assertEqual(normalized["artifacts"]["longform_markdown"], str(longform))
            self.assertEqual(normalized["artifacts"]["longform_pdf"], str(pdf))
            self.assertEqual(normalized["artifacts"]["concise_markdown"], str(concise_markdown))
            self.assertEqual(normalized["artifacts"]["concise_pdf"], str(concise_pdf))
            concise_mobile = delivery_dir / "case-a简洁版-手机阅读.html"
            relationship_mobile = delivery_dir / "case-a合盘总评-丰富版-手机阅读.html"
            relationship_concise = delivery_dir / "case-a合盘简洁版.md"
            relationship_concise_source = drafts_dir / "case-a-relationship-concise.md"
            relationship_concise_docx = delivery_dir / "case-a合盘简洁版.docx"
            relationship_concise_pdf = delivery_dir / "case-a合盘简洁版.pdf"
            relationship_concise_zip = delivery_dir / "case-a合盘简洁版.zip"
            relationship_concise_mobile = delivery_dir / "case-a合盘简洁版-手机阅读.html"
            for path in [
                concise_mobile,
                relationship_mobile,
                relationship_concise_source,
                relationship_concise,
                relationship_concise_docx,
                relationship_concise_pdf,
                relationship_concise_zip,
                relationship_concise_mobile,
            ]:
                path.write_text("x" * 120, encoding="utf-8")
            normalized, changes = contract.normalize_manifest(manifest)
            self.assertEqual(normalized["artifacts"]["concise_mobile_html"], str(concise_mobile))
            self.assertEqual(normalized["artifacts"]["relationship_mobile_html"], str(relationship_mobile))
            self.assertEqual(normalized["artifacts"]["relationship_concise_source_markdown"], str(relationship_concise_source))
            self.assertEqual(normalized["artifacts"]["relationship_concise_markdown"], str(relationship_concise))
            self.assertEqual(normalized["artifacts"]["relationship_concise_docx"], str(relationship_concise_docx))
            self.assertEqual(normalized["artifacts"]["relationship_concise_pdf"], str(relationship_concise_pdf))
            self.assertEqual(normalized["artifacts"]["relationship_concise_zip"], str(relationship_concise_zip))
            self.assertEqual(normalized["artifacts"]["relationship_concise_mobile_html"], str(relationship_concise_mobile))
            self.assertEqual(normalized["artifacts"]["final_delivery"], str(final_delivery))
            self.assertEqual(normalized["artifacts"]["data"]["combo"], str(combo))
            self.assertEqual(normalized["artifacts"]["data"]["relationship"], str(relationship))
            expectations = normalized["validation_expectations"]
            self.assertEqual(expectations["required_delivery_variants"], ["rich", "relationship_concise"])
            self.assertEqual(expectations["required_data"], ["relationship"])
            self.assertEqual(expectations["required_modules"], [])
            self.assertEqual(
                expectations["required_artifacts"],
                [
                    "relationship_fact_archive_markdown",
                    "relationship_workflow",
                    "relationship_mobile_html",
                    "relationship_concise_source_markdown",
                    "relationship_concise_pdf",
                    "relationship_concise_mobile_html",
                    "longform_markdown",
                    "longform_pdf",
                    "final_delivery",
                ],
            )
            self.assertIn("关系总评", expectations["longform_markers"])
            self.assertIn("综合评语", expectations["longform_markers"])
            self.assertNotIn("关系总评：强牵引互补缘，越懂越入心", expectations["longform_markers"])
            self.assertEqual(expectations["fact_archive_markers"], ["合盘事实复查档案", "现实专题交集事实", "写作约束"])
            self.assertEqual(expectations["pdf_text_markers"], ["合盘", "关系总评"])
            self.assertEqual(expectations["min_longform_chars"], 17000)

    def test_finalize_expectations_are_explicit_not_sample_defaults(self) -> None:
        finalize_case = load_finalize_case()
        self.assertIsNone(finalize_case.explicit_expectation({}, "flow_day"))
        self.assertEqual(finalize_case.explicit_expectation({"flow_day": "丁巳"}, "flow_day"), "丁巳")

    def test_audit_longform_can_compare_previous_article_for_template_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "current.md"
            previous = root / "previous.md"
            facts = root / "facts.json"
            shared_theme_text = (
                "不替代医疗、不替代法律、不替代投资。\n\n"
                + "边界、表达、说清楚、提前说明、沉默、冷处理。" * 12
                + "安全感、敏感、被消耗、防御、慢热、心里。" * 18
                + "作品、作品集、可见产物、交付、流程、复盘、方法论。" * 18
                + "预算、合同、回款、钱账、报价、分工、修改。" * 8
                + "恢复、作息、睡眠、运动、独处、精力。" * 8
                + "粗糙、质量、细节、标准、催促、临时。" * 18
                + "别人可能会怎样误读，看起来温和其实很强，不适合长期消耗。" * 8
            )
            current.write_text("# 当前\n\n" + shared_theme_text, encoding="utf-8")
            previous.write_text("# 旧稿\n\n" + shared_theme_text.replace("当前", "旧稿"), encoding="utf-8")
            facts.write_text(
                json.dumps({"schema_version": "0.2.0", "module": "combo", "facts": {"modules": []}}, ensure_ascii=False),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(AUDIT_LONGFORM_CONSISTENCY_SCRIPT),
                    str(current),
                    "--facts-json",
                    str(facts),
                    "--compare-article",
                    str(previous),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["comparisons"])
            self.assertTrue(any("template drift" in item for item in result["warnings"]))

    def test_audit_longform_can_auto_discover_recent_reader_rich_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runs_root = root / "runs"
            current_run = runs_root / "current-case" / "run_current"
            old_run = runs_root / "old-case" / "run_old"
            for run in [current_run, old_run]:
                (run / "drafts").mkdir(parents=True)
            current = current_run / "drafts" / "current-case-longform.md"
            old = old_run / "drafts" / "old-case-longform.md"
            draft = old_run / "drafts" / "old-case-longform-draft.md"
            facts = current_run / "facts.json"
            h2s = "\n".join(f"## {str(idx).zfill(2)} 章节\n" for idx in range(1, 17))
            repeated = (
                "不替代医疗、不替代法律、不替代投资。\n"
                + "边界 表达 说清楚 提前说明 沉默 冷处理 " * 12
                + "安全感 敏感 被消耗 防御 慢热 心里 " * 18
                + "作品 作品集 可见产物 交付 流程 复盘 方法论 " * 18
                + "预算 合同 回款 钱账 报价 分工 修改 " * 8
                + "恢复 作息 睡眠 运动 独处 精力 " * 8
                + "粗糙 质量 细节 标准 催促 临时 " * 18
                + "别人可能会怎样误读 看起来其实 表面内心 不适合长期 " * 8
            )
            body = (h2s + "\n" + repeated + "\n") * 12
            current.write_text("# 当前\n\n" + body, encoding="utf-8")
            old.write_text("# 旧稿\n\n" + body, encoding="utf-8")
            draft.write_text("# 草稿\n\n" + body, encoding="utf-8")
            facts.write_text(
                json.dumps({"schema_version": "0.2.0", "module": "combo", "facts": {"modules": []}}, ensure_ascii=False),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(AUDIT_LONGFORM_CONSISTENCY_SCRIPT),
                    str(current),
                    "--facts-json",
                    str(facts),
                    "--compare-recent",
                    "1",
                    "--compare-run-root",
                    str(runs_root),
                    "--current-run-dir",
                    str(current_run),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertEqual(result["discovered_compare_articles"], [str(old.resolve())])
            self.assertTrue(any("template drift" in item for item in result["warnings"]))

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
        proc = subprocess.run(
            [sys.executable, str(AUDIT_SOURCE_DOCUMENTATION_SCRIPT)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
        )
        result = json.loads(proc.stdout)
        self.assertTrue(result["passed"])
        self.assertGreaterEqual(result["documented_classical_sources"], 18)
        self.assertGreaterEqual(result["documented_modern_sources"], 4)
        self.assertEqual(result["failures"], [])

    def test_knowledge_coverage_reports_retrospective_requirements(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(AUDIT_KNOWLEDGE_COVERAGE_SCRIPT)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
        )
        result = json.loads(proc.stdout)
        self.assertTrue(result["passed"])
        self.assertIn("retrospective_requirements", result)
        requirements = {item["id"]: item for item in result["retrospective_requirements"]}
        self.assertIn("REQ-RETRO-BAZI", requirements)
        self.assertFalse(requirements["REQ-RETRO-BAZI"]["satisfied"])
        self.assertEqual(requirements["REQ-RETRO-BAZI"]["min_entries"], 2)
        self.assertIn("GAP-BAZI-VERIFIED-CASES", result["goal_completion_blockers"])
        next_actions = {item["requirement_id"]: item for item in result["next_actions"]}
        self.assertIn("REQ-RETRO-BAZI", next_actions)
        self.assertEqual(next_actions["REQ-RETRO-BAZI"]["needed_entries"], 2)
        self.assertTrue(next_actions["REQ-RETRO-BAZI"]["human_approval_required"])
        self.assertTrue(next_actions["REQ-RETRO-BAZI"]["do_not_create_synthetic_retrospectives"])
        self.assertTrue(
            any("--dry-run" in command for command in next_actions["REQ-RETRO-BAZI"]["commands"])
        )
        coverage = json.loads((PROJECT_ROOT / "knowledge/completeness/coverage-matrix.json").read_text(encoding="utf-8"))
        domains = {item["id"]: item for item in coverage["domains"]}
        liuyao_source_ids = set(domains["liuyao"]["source_ids"])
        self.assertIn("SRC-LIUYAO-BUSHI-ZHENGZONG", liuyao_source_ids)
        self.assertIn("SRC-LIUYAO-HUOZHULIN", liuyao_source_ids)

    def test_promotion_manifest_audit_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(AUDIT_PROMOTION_MANIFEST_SCRIPT)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
        )
        result = json.loads(proc.stdout)
        self.assertTrue(result["passed"])
        self.assertGreaterEqual(result["entries"], 1)
        self.assertGreaterEqual(result["promoted_paths"], 1)

    def test_rule_card_audit_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(AUDIT_RULE_CARDS_SCRIPT)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
        )
        result = json.loads(proc.stdout)
        self.assertTrue(result["passed"])
        self.assertGreaterEqual(result["audited_cards"], 20)
        self.assertEqual(result["promoted_cards"], result["audited_cards"])
        self.assertGreaterEqual(result["structured_rules"], 20)
        self.assertEqual(result["failures"], [])

    def test_combo_can_include_western(self) -> None:
        data = run_cmd("combo", "--solar", "1991-08-15", "--time", "01:30", "--gender", "男", "--western")
        self.assert_schema(data, "combo")
        self.assertIn("western", [m["module"] for m in data["facts"]["modules"]])

    def test_longform_from_combo_json(self) -> None:
        fixture = {
            "schema_version": "0.2.0",
            "module": "combo",
            "input": {"solar": "1991-08-15", "time": "01:30"},
            "facts": {
                "modules": [
                    {
                        "module": "bazi",
                        "input": {"time": "01:30"},
                        "facts": {
                            "solar": "1991-08-15",
                            "pillars": {"year": "辛未", "month": "丙申", "day": "丁巳", "hour": "辛丑"},
                            "day_master": "丁",
                            "profiles": {
                                "ten_gods": {"combined": {"偏财": 3, "正财": 2}},
                                "elements": {"stems_plus_hidden": {"木": 1, "火": 4, "土": 4, "金": 5, "水": 2}},
                            },
                            "flow": {
                                "current_dayun": {
                                    "gan_zhi": "壬辰",
                                    "start_year": 2023,
                                    "end_year": 2032,
                                    "ten_god_gan": "正官",
                                    "gan_wuxing": "水",
                                    "zhi_wuxing": "土",
                                },
                                "annual_flows": [
                                    {"year": 2024, "pillar": "甲辰", "dayun": "壬辰"},
                                    {"year": 2026, "pillar": "丙午", "dayun": "壬辰"},
                                ],
                            },
                            "dayun": [
                                {"gan_zhi": "壬辰", "start_year": 2023, "end_year": 2032, "ten_god_gan": "正官", "growth_by_day_master": "衰", "self_sitting": "墓"},
                                {"gan_zhi": "辛卯", "start_year": 2033, "end_year": 2042, "ten_god_gan": "偏财", "growth_by_day_master": "病", "self_sitting": "绝"},
                            ],
                        },
                        "warnings": [],
                        "uncertainties": [],
                    },
                    {
                        "module": "ziwei",
                        "facts": {
                            "soul_palace_branch": "巳",
                            "body_palace_branch": "未",
                            "current_decadal": {"name": "福德宫", "major_stars": ["天梁"]},
                            "year_mutagens": [{"star": "太阴", "mutagen": "权", "palace": "夫妻宫"}],
                            "palaces": [
                                {"name": "命宫", "major_stars": ["巨门"]},
                                {"name": "夫妻宫", "major_stars": ["太阴"]},
                                {"name": "财帛宫", "major_stars": ["天机"]},
                                {"name": "官禄宫", "major_stars": ["天同"]},
                            ],
                        },
                        "warnings": [],
                        "uncertainties": [],
                    },
                    {
                        "module": "western",
                        "facts": {
                            "placements": [
                                {"body": "太阳", "sign": "狮子"},
                                {"body": "月亮", "sign": "天秤"},
                                {"body": "水星", "sign": "处女"},
                                {"body": "金星", "sign": "处女"},
                                {"body": "火星", "sign": "处女"},
                            ],
                            "aspects": [{"body_a": "太阳", "aspect": "六合", "body_b": "月亮", "orb": 0.92}],
                            "moon_phase": {"phase": "娥眉月", "sun_moon_angle": 60.92},
                            "balance": {"elements": {"土": 5}, "modalities": {"固定": 4}},
                        },
                        "warnings": ["未提供出生地经纬度；暂不计算上升星座、宫位和精确宫主星。"],
                        "uncertainties": [],
                    },
                ]
            },
            "warnings": [],
            "uncertainties": [],
            "interpretation_hints": [],
            "calibration_questions": [],
            "raw": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "combo.json"
            output = Path(tmp) / "longform.md"
            source.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            data = run_cmd("longform", "--input-json", str(source), "--output", str(output), "--title", "demo")
            self.assert_schema(data, "longform")
            self.assertTrue(output.exists())
            text = output.read_text(encoding="utf-8")
            for marker in ["命理", "紫微", "西洋占星", "过去几年", "未来几年", "事业", "财富", "爱情", "健康", "建议"]:
                self.assertIn(marker, text)
            for fact in ["辛未", "丙申", "丁巳", "辛丑", "壬辰", "巨门", "天梁", "太阳狮子", "月亮天秤"]:
                self.assertIn(fact, text)
            self.assertGreater(data["facts"]["chars"], 3000)

    def test_combo_lunar_birth_is_not_silently_ignored(self) -> None:
        data = run_cmd("combo", "--lunar", "1991-07-06", "--time", "01:30", "--gender", "男", "--mbti-type", "INTJ")
        self.assert_schema(data, "combo")
        modules = [m["module"] for m in data["facts"]["modules"]]
        if importlib.util.find_spec("lunar_python") is None:
            self.assertEqual(modules, ["mbti"])
            self.assertTrue(any(w.startswith("bazi skipped: Missing dependency: lunar-python") for w in data["warnings"]))
        else:
            self.assertIn("bazi", modules)

    @unittest.skipIf(importlib.util.find_spec("lunar_python") is None, "lunar-python not installed")
    def test_bazi_true_solar(self) -> None:
        data = run_cmd("bazi", "--solar", "1991-08-15", "--time", "01:30", "--gender", "男", "--longitude", "121.47", "--true-solar")
        self.assert_schema(data, "bazi")
        self.assertEqual(data["facts"]["pillars"]["day"], "丁巳")
        self.assertTrue(data["facts"]["true_solar_time"]["enabled"])

    @unittest.skipIf(importlib.util.find_spec("lunar_python") is None, "lunar-python not installed")
    def test_bazi_flow_as_of(self) -> None:
        data = run_cmd("bazi", "--solar", "1991-08-15", "--time", "01:30", "--gender", "男", "--as-of", "2026-06-11")
        self.assert_schema(data, "bazi")
        self.assertEqual(data["facts"]["pillars"], {"year": "辛未", "month": "丙申", "day": "丁巳", "hour": "辛丑"})
        self.assertEqual(data["facts"]["flow"]["nominal_age"], 36)
        self.assertEqual(data["facts"]["flow"]["pillars"], {"year": "丙午", "month": "甲午", "day": "丙辰"})
        self.assertEqual(data["facts"]["flow"]["current_dayun"]["gan_zhi"], "壬辰")
        self.assertEqual(
            data["facts"]["twelve_growth"]["by_day_master"],
            {"year": "冠带", "month": "沐浴", "day": "帝旺", "hour": "墓"},
        )
        self.assertEqual(
            data["facts"]["twelve_growth"]["self_sitting"],
            {"year": "衰", "month": "病", "day": "帝旺", "hour": "养"},
        )
        self.assertEqual(
            data["facts"]["flow"]["growth_by_day_master"],
            {"dayun": "衰", "year": "临官", "month": "临官", "day": "衰"},
        )
        self.assertEqual(data["facts"]["profiles"]["ten_gods"]["visible_stems"], {"日主": 1, "劫财": 1, "偏财": 2})
        self.assertEqual(
            data["facts"]["profiles"]["ten_gods"]["hidden_stems"],
            {"比肩": 1, "劫财": 1, "食神": 2, "伤官": 2, "偏财": 1, "正财": 2, "七杀": 1, "正官": 1, "偏印": 1},
        )
        self.assertEqual(data["facts"]["profiles"]["elements"]["visible_stems"], {"火": 2, "金": 2})
        self.assertEqual(data["facts"]["profiles"]["elements"]["hidden_stems"], {"木": 1, "火": 2, "土": 4, "金": 3, "水": 2})
        dayun = {row["gan_zhi"]: row for row in data["facts"]["dayun"] if row["gan_zhi"]}
        self.assertEqual(dayun["壬辰"]["ten_god_gan"], "正官")
        self.assertEqual(dayun["壬辰"]["growth_by_day_master"], "衰")
        self.assertEqual(dayun["壬辰"]["self_sitting"], "墓")
        self.assertEqual(dayun["辛卯"]["ten_god_gan"], "偏财")
        self.assertEqual(dayun["庚寅"]["ten_god_gan"], "正财")
        self.assertEqual(dayun["己丑"]["ten_god_gan"], "食神")
        natal_branch_relations = {row["relation"] for row in data["facts"]["relationships"]["natal"]["branches"]}
        self.assertIn("丑未冲", natal_branch_relations)
        self.assertIn("丑未刑", natal_branch_relations)
        self.assertIn("巳申六合水", natal_branch_relations)
        dayun_branch_relations = {row["relation"] for row in data["facts"]["relationships"]["current_dayun"]["branches"]}
        self.assertIn("辰丑破", dayun_branch_relations)
        flow_stem_relations = {row["relation"] for row in data["facts"]["relationships"]["flow"]["stems"]}
        flow_branch_relations = {row["relation"] for row in data["facts"]["relationships"]["flow"]["branches"]}
        self.assertIn("丙辛合水", flow_stem_relations)
        self.assertIn("午未六合土", flow_branch_relations)
        self.assertIn("丑午害", flow_branch_relations)
        flow_dayun_stem_relations = {row["relation"] for row in data["facts"]["relationships"]["flow_with_dayun"]["stems"]}
        self.assertIn("丙壬冲", flow_dayun_stem_relations)
        self.assertEqual(
            [(row["year"], row["pillar"], row["dayun"]) for row in data["facts"]["flow"]["annual_flows"]],
            [(2022, "壬寅", "癸巳"), (2023, "癸卯", "壬辰"), (2024, "甲辰", "壬辰"), (2025, "乙巳", "壬辰"), (2026, "丙午", "壬辰")],
        )

    @unittest.skipIf(importlib.util.find_spec("iztro_py") is None, "iztro-py not installed")
    def test_ziwei_current_decadal(self) -> None:
        data = run_cmd("ziwei", "--solar", "1991-08-15", "--hour-index", "1", "--gender", "男", "--as-of", "2026-06-11")
        self.assert_schema(data, "ziwei")
        self.assertEqual(data["facts"]["soul_palace_branch"], "未")
        self.assertIsNotNone(data["facts"]["current_decadal"])


if __name__ == "__main__":
    unittest.main()
