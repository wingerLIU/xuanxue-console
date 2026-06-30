#!/usr/bin/env python3
"""Tests for reader-rich case specificity and anti-cliche checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from . import validate_longform_report as validator
except ImportError:  # pragma: no cover - unittest discovery from scripts/
    import validate_longform_report as validator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_LONGFORM_SCRIPT = Path(__file__).with_name("validate_longform_report.py")
AUDIT_LONGFORM_CONSISTENCY_SCRIPT = Path(__file__).with_name("audit_longform_consistency.py")


def combo_facts() -> dict:
    return {
        "schema_version": "0.2.0",
        "module": "combo",
        "input": {},
        "facts": {
            "modules": [
                {
                    "module": "bazi",
                    "facts": {
                        "pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
                        "flow": {
                            "current_dayun": {"gan_zhi": "戊辰"},
                            "pillars": {"year": "己巳", "month": "庚午", "day": "辛未"},
                        },
                    },
                },
                {
                    "module": "ziwei",
                    "facts": {
                        "soul_palace_branch": "子",
                        "body_palace_branch": "午",
                        "current_decadal": {"name": "紫微大限", "major_stars": ["紫微", "天府"]},
                        "palaces": [{"name": "命宫", "major_stars": ["紫微", "天府"]}],
                    },
                },
                {
                    "module": "western",
                    "facts": {
                        "placements": [
                            {"body": "太阳", "sign": "狮子"},
                            {"body": "月亮", "sign": "天秤"},
                            {"body": "水星", "sign": "处女"},
                            {"body": "金星", "sign": "巨蟹"},
                        ]
                    },
                },
            ]
        },
        "warnings": [],
        "uncertainties": [],
        "interpretation_hints": [],
        "calibration_questions": [],
        "raw": {},
    }


def reader_rich_article(opening_extra: str = "", tail: str = "") -> str:
    h3_by_section = {
        "13 六大专题分析": validator.READER_RICH_REQUIRED_H3[:6],
        "15 技术证据附录": validator.READER_RICH_REQUIRED_H3[6:],
    }
    sections: list[str] = ["# 读者丰富版测试稿", ""]
    voice = (
        "你在现实里最需要看见的是自己的判断方式。"
        "你不是缺少能力，而是容易把能量花在证明、解释和重复确认上。"
        "别人可能会误读你太强势，风险在于你把真实需求压到最后。"
        "更好的做法是把目标、边界和交付物提前讲清楚。"
    )
    common_markers = (
        "命理 紫微 西洋占星 三套体系 过去几年 未来几年 事业 财富 爱情 健康 建议 "
        "判断型摘要 摘要 先看结论 基础排盘信息 时间可信度 时间敏感性 八字总论 神煞 "
        "紫微总论 西洋占星总论 主要相位 三方合参 现实关系全景 六大专题分析 技术证据附录 校准问题 "
        "盘面触发 现实倾向 可校准问题 不替代医疗 不替代法律 不替代投资"
    )
    opening_markers = (
        "命理 紫微 西洋占星 三套体系 过去几年 未来几年 事业 财富 爱情 健康 建议 "
        "判断型摘要 摘要 先看结论 八字总论 神煞 紫微总论 西洋占星总论 主要相位 "
        "三方合参 现实关系全景 六大专题分析 技术证据附录 校准问题 "
        "盘面触发 现实倾向 可校准问题 不替代医疗 不替代法律 不替代投资"
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
    if tail:
        sections.append(tail)
    return "\n".join(sections)


def run_script(script: Path, article: str, facts: dict, *extra_args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    with tempfile.TemporaryDirectory() as tmp:
        article_path = Path(tmp) / "article.md"
        article_path.write_text(article, encoding="utf-8")
        facts_path = Path(tmp) / "facts.json"
        facts_path.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(script), str(article_path), "--facts-json", str(facts_path), *extra_args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
            env=env,
        )
        return proc, json.loads(proc.stdout)


class ReaderSpecificityTests(unittest.TestCase):
    def test_validator_requires_case_specific_opening_anchors(self) -> None:
        facts = combo_facts()
        fact_tail = "甲子 乙丑 丙寅 丁卯 戊辰 己巳 庚午 辛未 命宫子 身宫午 紫微大限 紫微 天府 太阳狮子 月亮天秤 水星处女 金星巨蟹"
        article = reader_rich_article(
            opening_extra="你需要被理解，也需要安全感和边界感，不适合被消耗。",
            tail=fact_tail,
        )
        proc, result = run_script(VALIDATE_LONGFORM_SCRIPT, article, facts, "--profile", "reader-rich")
        self.assertNotEqual(proc.returncode, 0)
        joined = "\n".join(result["format_failures"])
        self.assertIn("opening needs case-specific fact anchors", joined)
        self.assertIn("generic reader-facing phrases", joined)

    def test_validator_accepts_case_specific_opening_anchors(self) -> None:
        facts = combo_facts()
        fact_text = "甲子 乙丑 丙寅 丁卯 戊辰 己巳 庚午 辛未 命宫子 身宫午 紫微大限 紫微 天府 太阳狮子 月亮天秤 水星处女 金星巨蟹"
        proc, result = run_script(
            VALIDATE_LONGFORM_SCRIPT,
            reader_rich_article(opening_extra=fact_text),
            facts,
            "--profile",
            "reader-rich",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(result["passed"])

    def test_consistency_audit_flags_generic_opening_without_case_anchors(self) -> None:
        facts = combo_facts()
        fact_tail = "甲子 乙丑 丙寅 丁卯 戊辰 己巳 庚午 辛未 命宫子 身宫午 紫微大限 紫微 天府 太阳狮子 月亮天秤 水星处女 金星巨蟹"
        article = reader_rich_article(
            opening_extra="你需要被理解，也需要安全感和边界感，不适合被消耗。",
            tail=fact_tail,
        )
        proc, result = run_script(AUDIT_LONGFORM_CONSISTENCY_SCRIPT, article, facts, "--strict")
        self.assertNotEqual(proc.returncode, 0)
        joined = "\n".join(result["warnings"])
        self.assertIn("opening sections lack case-specific anchors", joined)
        self.assertIn("opening sections may feel like reusable copy", joined)


if __name__ == "__main__":
    unittest.main()
