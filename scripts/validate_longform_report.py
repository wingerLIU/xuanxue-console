#!/usr/bin/env python3
"""Validate longform xuanxue articles for reusable structure and required facts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from reader_title_contract import reader_title_label_failures
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from reader_title_contract import reader_title_label_failures


DEFAULT_MARKERS = [
    "命理",
    "紫微",
    "西洋占星",
    "三套体系",
    "过去几年",
    "未来几年",
    "事业",
    "财富",
    "爱情",
    "健康",
    "建议",
]

READER_RICH_HEADINGS = [
    "01 判断型摘要",
    "02 先看结论",
    "03 基础排盘信息与时间可信度",
    "04 时间敏感性检查",
    "05 八字总论：格局、喜忌、十神与神煞辅助",
    "06 紫微总论：命身、命财官迁与四化大限",
    "07 西洋占星总论：落座、相位、宫位与时间敏感项",
    "08 三方合参人格画像与误读点",
    "09 别人眼里的你与外貌气质",
    "10 现实关系全景",
    "11 过去几年故事线",
    "12 未来几年趋势",
    "13 六大专题分析",
    "14 行动建议",
    "15 技术证据附录",
    "16 校准问题",
]

READER_RICH_REQUIRED_H3 = [
    "事业：适合赛道、工作方式与组织环境",
    "财富：收入模型、预算与合作边界",
    "爱情：亲密关系、沟通缺口与推进节奏",
    "健康与精力：压力、作息与恢复",
    "人际合作：贵人、同侪、分工与合同",
    "学习成长：作品、方法论与输出",
    "八字技术证据",
    "紫微技术证据",
    "西占技术证据",
    "时间敏感项",
]

READER_RICH_MARKERS = [
    "判断型摘要",
    "摘要",
    "先看结论",
    "基础排盘信息",
    "时间可信度",
    "时间敏感性",
    "八字总论",
    "神煞",
    "紫微总论",
    "西洋占星总论",
    "主要相位",
    "三方合参",
    "现实关系全景",
    "过去几年",
    "未来几年",
    "六大专题分析",
    "技术证据附录",
    "校准问题",
]

READER_RICH_SCENARIO_MARKERS = [
    "白话场景",
    "情景推演",
    "别人可能会",
    "风险在于",
    "更好的做法",
    "盘面触发",
    "现实倾向",
    "可校准问题",
]

READER_RICH_FORBIDDEN = [
    "scripts/",
    "scripts\\",
    "reports/data",
    "reports\\data",
    "xuanxue_console.py",
    ".json",
    "结构化 JSON",
    "脚本路径",
    "坐标来源",
    "这一章不再解释",
    "客户可以执行",
    "下面每一条都对应",
    "前文的命盘结构",
    "读者版正文",
    "截图显示",
    "基准盘",
    "本报告按照",
    "这篇文章",
    "这一章",
    "项目流程",
    "外部 run",
    "过程产物",
    "过程话术",
    "用于约束AI",
    "AI 约束",
    "AI约束",
    "新加段落",
    "乐观收束",
    "情绪价值",
    "真实感增强",
    "小红书",
    "新媒体图文",
    "找问题",
    "找茬",
    "编辑话术",
]

READER_CONCISE_MARKERS = [
    "专业锚点",
    "关系",
    "感情",
    "事业",
    "未来",
    "自查",
    "建议",
]

READER_CONCISE_ANY_MARKER_GROUPS = {
    "money": ["钱", "财富", "收入", "预算"],
}

READER_CONCISE_MIN_SECOND_PERSON_COUNT = 10
READER_CONCISE_MIN_BOLD_TAKEAWAYS = 6
READER_CONCISE_MIN_H2_COUNT = 5

READER_RICH_FIRST_SECTION_FORBIDDEN = [
    "截图",
    "基准盘",
    "基础排盘",
    "排盘信息",
    "出生时间",
    "出生地点",
    "四柱如下",
    "命盘如下",
    "本报告",
    "这一章",
]

READER_RICH_MIN_SECOND_PERSON_COUNT = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a longform xuanxue Markdown article.")
    parser.add_argument("article", help="Path to the Markdown article.")
    parser.add_argument(
        "--facts-json",
        help="Optional combo or module JSON report. When provided, key chart facts must also appear in the article.",
    )
    parser.add_argument(
        "--must-contain",
        action="append",
        default=[],
        help="Exact text that must appear in the article. Can be repeated.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=3000,
        help="Minimum article length in Unicode codepoints.",
    )
    parser.add_argument(
        "--profile",
        choices=["basic", "reader-rich", "reader-concise"],
        default="basic",
        help="Validation profile. reader-rich and reader-concise are reader-facing delivery standards.",
    )
    parser.add_argument(
        "--forbid",
        action="append",
        default=[],
        help="Exact text that must not appear in the article. Can be repeated.",
    )
    return parser.parse_args()


def modules_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    if report.get("module") == "combo":
        modules = report.get("facts", {}).get("modules", [])
        return modules if isinstance(modules, list) else []
    return [report]


def find_module(report: dict[str, Any], module_name: str) -> dict[str, Any] | None:
    for item in modules_from_report(report):
        if item.get("module") == module_name:
            return item
    return None


def facts_markers(report: dict[str, Any]) -> list[str]:
    markers: list[str] = []
    bazi = find_module(report, "bazi")
    if bazi:
        facts = bazi.get("facts", {})
        pillars = facts.get("pillars", {})
        markers.extend(str(pillars.get(key, "")) for key in ["year", "month", "day", "hour"])
        current_dayun = facts.get("flow", {}).get("current_dayun", {})
        markers.append(str(current_dayun.get("gan_zhi", "")))
    ziwei = find_module(report, "ziwei")
    if ziwei:
        facts = ziwei.get("facts", {})
        current_decadal = facts.get("current_decadal") or {}
        markers.append(str(current_decadal.get("name", "")))
        markers.extend(str(star) for star in current_decadal.get("major_stars", [])[:3])
        for palace in facts.get("palaces", []):
            if palace.get("name") == "命宫":
                markers.extend(str(star) for star in palace.get("major_stars", [])[:3])
                break
    western = find_module(report, "western")
    if western:
        for row in western.get("facts", {}).get("placements", [])[:5]:
            if row.get("body") and row.get("sign"):
                markers.append(f"{row['body']}{row['sign']}")
    return [marker for marker in markers if marker and marker != "None"]


def h2_headings(text: str) -> list[str]:
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def h1_headings(text: str) -> list[str]:
    return [line[2:].strip() for line in text.splitlines() if line.startswith("# ")]


def h3_headings(text: str) -> list[str]:
    return [line[4:].strip() for line in text.splitlines() if line.startswith("### ")]


def h2_section_map(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line)
    return {key: "\n".join(value) for key, value in sections.items()}


def concise_missing_marker_groups(text: str) -> list[str]:
    missing = []
    for label, markers in READER_CONCISE_ANY_MARKER_GROUPS.items():
        if not any(marker in text for marker in markers):
            missing.append(f"{label}: one of {markers}")
    return missing


def main() -> int:
    args = parse_args()
    path = Path(args.article)
    text = path.read_text(encoding="utf-8")
    required = list(DEFAULT_MARKERS)
    forbidden = list(args.forbid)
    min_chars = args.min_chars
    if args.profile == "reader-rich":
        required = list(READER_RICH_MARKERS)
        forbidden += READER_RICH_FORBIDDEN
        min_chars = max(min_chars, 18000)
        required += READER_RICH_SCENARIO_MARKERS
    if args.profile == "reader-concise":
        required = list(READER_CONCISE_MARKERS)
        forbidden += READER_RICH_FORBIDDEN
        min_chars = max(min_chars, 5500)
    required += args.must_contain
    if args.facts_json:
        report = json.loads(Path(args.facts_json).read_text(encoding="utf-8"))
        required += facts_markers(report)
    missing = [item for item in required if item not in text]
    forbidden_found = [item for item in forbidden if item in text]
    format_failures: list[str] = []
    h1s = h1_headings(text)
    title_failures = [
        f"{reason}: {heading}"
        for heading in h1s
        for reason in reader_title_label_failures(heading)
    ]
    if title_failures:
        format_failures.append(
            "reader-facing H1 title should be a report appraisal, not a delivery/process label: "
            + "；".join(title_failures[:4])
        )
    scenario_label_count = 0
    if args.profile == "reader-rich":
        actual_h2 = h2_headings(text)
        if actual_h2 != READER_RICH_HEADINGS:
            format_failures.append(
                "reader-rich H2 headings must exactly match the fixed 16-section product outline"
            )
        actual_h3 = h3_headings(text)
        missing_h3 = [heading for heading in READER_RICH_REQUIRED_H3 if heading not in actual_h3]
        if missing_h3:
            format_failures.append(f"reader-rich missing required H3 headings: {missing_h3}")
        scenario_label_count = text.count("白话场景") + text.count("情景推演")
        if scenario_label_count < 8:
            format_failures.append("reader-rich requires at least 8 白话场景/情景推演 blocks")
        sections = h2_section_map(text)
        first_section = sections.get("01 判断型摘要", "")
        opening_process_terms = [item for item in READER_RICH_FIRST_SECTION_FORBIDDEN if item in first_section]
        if opening_process_terms:
            format_failures.append(
                f"reader-rich opening summary contains process or raw-data terms: {opening_process_terms}"
            )
        second_person_count = text.count("你")
        if second_person_count < READER_RICH_MIN_SECOND_PERSON_COUNT:
            format_failures.append(
                "reader-rich requires second-person delivery: "
                f"found {second_person_count} occurrences of 你, "
                f"minimum {READER_RICH_MIN_SECOND_PERSON_COUNT}"
            )
    if args.profile == "reader-concise":
        h2_count = len(h2_headings(text))
        if h2_count < READER_CONCISE_MIN_H2_COUNT:
            format_failures.append(
                f"reader-concise should use at least {READER_CONCISE_MIN_H2_COUNT} scannable H2 sections; found {h2_count}"
            )
        second_person_count = text.count("你")
        if second_person_count < READER_CONCISE_MIN_SECOND_PERSON_COUNT:
            format_failures.append(
                "reader-concise requires second-person delivery: "
                f"found {second_person_count} occurrences of 你, "
                f"minimum {READER_CONCISE_MIN_SECOND_PERSON_COUNT}"
            )
        bold_count = len(re.findall(r"\*\*[^*\n]{6,90}\*\*", text))
        if bold_count < READER_CONCISE_MIN_BOLD_TAKEAWAYS:
            format_failures.append(
                "reader-concise needs at least "
                f"{READER_CONCISE_MIN_BOLD_TAKEAWAYS} concise bold reader-facing takeaway sentences; found {bold_count}"
            )
        missing_groups = concise_missing_marker_groups(text)
        if missing_groups:
            format_failures.append(f"reader-concise missing required theme groups: {missing_groups}")
    result = {
        "article": str(path),
        "chars": len(text),
        "min_chars": min_chars,
        "profile": args.profile,
        "missing": missing,
        "forbidden_found": forbidden_found,
        "format_failures": format_failures,
        "scenario_label_count": scenario_label_count,
        "second_person_count": text.count("你") if args.profile in {"reader-rich", "reader-concise"} else None,
        "passed": not missing and not forbidden_found and not format_failures and len(text) >= min_chars,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
