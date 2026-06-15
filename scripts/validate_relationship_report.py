#!/usr/bin/env python3
"""Validate reader-facing relationship reports against fact and style guardrails."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from reader_title_contract import reader_title_label_failures
    from relationship_mode import (
        NON_ROMANTIC_INTIMACY_MARKERS,
        is_romantic_facts,
        relationship_mode_from_facts,
        relationship_mode_schema_failures,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from reader_title_contract import reader_title_label_failures
    from relationship_mode import (
        NON_ROMANTIC_INTIMACY_MARKERS,
        is_romantic_facts,
        relationship_mode_from_facts,
        relationship_mode_schema_failures,
    )


REQUIRED_HEADING_TOPICS = [
    "关系总评",
    "现实锚点",
    "情感底色",
    "八字格局",
    "日主互动",
    "互动张力",
    "神煞气质",
    "大运流年",
    "西占吸引",
    "MBTI语言",
    "距离节奏",
    "亲近边界",
    "事业交集",
    "家庭生活",
    "财富投入",
    "精力照顾",
    "关系阶段",
    "过去年份",
    "未来年份",
    "互补价值",
    "相处心法",
    "综合评语",
]

DEFAULT_RICH_HEADINGS = [
    "关系总评：强牵引互补缘，越懂越入心",
    "现实锚点：以已经发生的关系为准",
    "情感底色：确定感与珍惜感互相牵引",
    "八字格局：标准感遇见细腻感",
    "日主互动：日主关系牵动核心感",
    "互动张力：靠近感强，磨合感也深",
    "神煞气质：审美、贵人与距离感",
    "大运流年：意义感与生活节奏同步变化",
    "西占吸引：语言火花与身体气场都明显",
    "MBTI语言：讨论感与感受力的互译",
    "距离节奏：距离状态里看见安全感",
    "亲近边界：靠近感要看关系性质",
    "事业交集：灵感与审美可以互相成就",
    "家庭生活：把喜欢放进日常细节",
    "财富投入：时间、成本与诚意的平衡",
    "精力照顾：状态说明也是亲密的一部分",
    "关系阶段：从心动走向承接",
    "过去年份：各自关系课题逐渐成熟",
    "未来年份：吸引落地，关系更有形",
    "互补价值：一个给方向，一个给温度",
    "相处心法：读懂对方的爱语",
    "综合评语：值得认真经营的高牵引关系",
]

REQUIRED_HEADINGS = DEFAULT_RICH_HEADINGS

CONCISE_THEME_MARKERS = [
    "合盘总评",
    "互补",
    "误读",
    "事业",
    "家庭",
    "财富",
    "精力",
    "未来",
]

ROMANTIC_CONCISE_THEME_MARKERS = ["吸引"]

FORBIDDEN = [
    "你们",
    "脚本",
    "命令",
    ".json",
    "JSON",
    "截图显示",
    "本报告按照",
    "过程",
    "生成",
    "路径",
    "强证据",
    "中等证据",
    "辅助证据",
    "证据强弱",
    "不预设",
    "必须写得克制",
    "只讨论成年关系",
    "不推断具体频率",
    "露骨细节",
    "乐观收束",
    "找问题",
    "找茬",
    "正文会",
    "这章",
    "校准问题",
    "C:\\",
    "scripts/",
    "scripts\\",
]

PROBLEM_HEADING_MARKERS = [
    "虽然",
    "但是",
    "不过",
    "问题",
    "风险",
    "警示",
    "避雷",
    "找茬",
    "劝退",
    "需要",
    "必须",
    "不能",
    "不要",
    "避免",
    "警惕",
    "小心",
    "焦虑",
    "压力",
]

PROCESS_TALK_MARKERS = [
    "本章",
    "本节",
    "这一章",
    "上一章",
    "下一章",
    "下面会",
    "以下会",
    "新增段落",
    "新加段落",
    "新增模块",
    "本模块",
    "这一模块",
    "前文",
    "上文",
    "后文",
    "上述",
    "如前所述",
    "这里不再",
    "正文会",
    "报告会",
    "读者会看到",
    "用于测试",
    "测试正文",
    "验证器",
]

EXPLICIT_INTIMACY_MARKERS = [
    "做爱",
    "性交",
    "上床",
    "开房",
    "床上表现",
    "性行为",
    "性频率",
    "器官",
    "裸",
]

POSITIVE_APPRAISAL_MARKERS = [
    "吸引",
    "牵引",
    "互补",
    "入心",
    "珍惜",
    "安全感",
    "温度",
    "成就",
    "值得",
    "认真经营",
    "越走越稳",
    "更稳",
    "更甜",
    "有力量",
    "安心",
    "靠近",
]

PRESSURE_MARKERS = [
    "问题",
    "风险",
    "警惕",
    "劝退",
    "焦虑",
    "冲突",
    "矛盾",
    "压力",
    "必须",
    "不能",
    "不要",
    "不适合",
    "很难",
]

REQUIRED_MARKERS = [
    "紫微",
    "西洋占星",
    "MBTI",
    "ENTP-A",
    "ISFP-T",
    "格局",
    "神煞",
    "空亡",
    "长生",
    "纳音",
    "事业",
    "亲近",
    "边界",
    "家庭",
    "合作",
    "资源",
    "财富",
    "健康",
    "精力",
    "关系形态",
]

REQUIRED_LIFE_DOMAINS = {
    "career": "事业/合作",
    "family_life": "家庭/生活承载",
    "wealth_resources": "财富/资源投入",
    "health_energy": "健康/精力照顾",
    "intimacy_private": "亲近/私密边界",
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a relationship longform Markdown report.")
    parser.add_argument("article")
    parser.add_argument("--facts-json", required=True)
    parser.add_argument("--profile", choices=["rich", "concise"], default="rich")
    parser.add_argument("--min-chars", type=int)
    parser.add_argument("--scenario-min", type=int)
    return parser.parse_args()


def h2_headings(text: str) -> list[str]:
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def paragraph_repetition_failures(text: str) -> list[str]:
    paragraphs = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    seen: dict[str, int] = {}
    failures = []
    for paragraph in paragraphs:
        normalized = re.sub(r"\s+", "", paragraph)
        if len(normalized) < 36:
            continue
        seen[normalized] = seen.get(normalized, 0) + 1
    duplicates = [paragraph for paragraph, count in seen.items() if count > 1]
    if duplicates:
        failures.append(f"duplicate paragraph-like blocks found: {len(duplicates)}")
    scene_count = text.count("白话场景") + text.count("情景推演")
    if scene_count and len(text) // scene_count < 650:
        failures.append("scene labels are too dense for article length; likely decorative repetition.")
    return failures


def paragraph_tone_failures(text: str) -> list[str]:
    paragraphs = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    failures = []
    dense = []
    for paragraph in paragraphs:
        score = sum(paragraph.count(word) for word in ["不是", "而是", "不能", "不要", "需要"])
        if score >= 5:
            dense.append(paragraph[:32])
    if dense:
        failures.append(f"too many corrective/negative transition words in {len(dense)} paragraph(s).")
    return failures


def h2_sections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^## (.+)$", text))
    sections = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections.append((match.group(1).strip(), text[start:end].strip()))
    return sections


def first_paragraph_starts_bold(body: str) -> bool:
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if block:
            return bool(re.match(r"^\*\*[^*\n]{6,120}\*\*", block))
    return False


def relation_markers(facts: dict[str, Any]) -> list[str]:
    markers: set[str] = set()
    for section in ["stems", "branches"]:
        for item in facts.get("bazi_cross", {}).get(section, []):
            if item.get("relation"):
                markers.add(str(item["relation"]))
    for item in facts.get("western_cross", {}).get("cross_aspects", [])[:10]:
        if item.get("person_a_body") and item.get("person_b_body"):
            markers.add(str(item["person_a_body"]))
            markers.add(str(item["person_b_body"]))
    rel = facts.get("relationship_context", {})
    for key in ["relationship_status", "distance_status"]:
        if rel.get(key):
            markers.add(str(rel[key]))
    for key in ["person_a", "person_b"]:
        mbti = facts.get("mbti", {}).get(key) or {}
        if mbti.get("type"):
            markers.add(str(mbti["type"]))
    return sorted(markers)


def temporal_markers(facts: dict[str, Any]) -> list[str]:
    markers: set[str] = set()
    for item in facts.get("annual_intersections", []):
        if isinstance(item, dict) and item.get("year"):
            markers.add(str(item["year"]))
    return sorted(markers)


def relationship_required_markers(facts: dict[str, Any], *, profile: str) -> list[str]:
    if profile == "concise":
        required = [
            "事业",
            "家庭",
            "财富",
            "精力",
            "未来",
        ]
    else:
        required = list(REQUIRED_MARKERS)
        if is_romantic_relationship(facts):
            required += ["身体吸引"]
    required += relation_markers(facts)
    if profile == "rich":
        required += temporal_markers(facts)
    return sorted({item for item in required if item})


def relationship_mode(facts: dict[str, Any]) -> dict[str, Any]:
    return relationship_mode_from_facts(facts)


def is_romantic_relationship(facts: dict[str, Any]) -> bool:
    return is_romantic_facts(facts)


def forbidden_markers(article: str, labels: tuple[str, str]) -> list[str]:
    person_a_label, person_b_label = labels
    dynamic = [
        f"你和{person_a_label}",
        f"你和{person_b_label}",
        f"你跟{person_a_label}",
        f"你跟{person_b_label}",
    ]
    markers = FORBIDDEN + [item for item in dynamic if item.strip()]
    return [item for item in markers if item and item in article]


def relationship_labels(facts: dict[str, Any]) -> tuple[str, str]:
    context = facts.get("relationship_context", {})
    if not isinstance(context, dict):
        context = {}
    labels = [
        str(context.get("person_a_label") or "").strip(),
        str(context.get("person_b_label") or "").strip(),
    ]
    if not all(labels):
        people = facts.get("people", [])
        if isinstance(people, dict):
            labels = [
                labels[0] or str(people.get("person_a_label") or "").strip(),
                labels[1] or str(people.get("person_b_label") or "").strip(),
            ]
        if isinstance(people, list):
            people_by_role = {
                str(person.get("role", "")): str(person.get("label", "")).strip()
                for person in people
                if isinstance(person, dict)
            }
            labels = [
                labels[0] or people_by_role.get("person_a", ""),
                labels[1] or people_by_role.get("person_b", ""),
            ]
            if not all(labels):
                ordered = [
                    str(person.get("label", "")).strip()
                    for person in people
                    if isinstance(person, dict) and person.get("label")
                ]
                labels = [
                    labels[0] or (ordered[0] if len(ordered) > 0 else ""),
                    labels[1] or (ordered[1] if len(ordered) > 1 else ""),
                ]
    return (labels[0] or "甲方", labels[1] or "乙方")


def concise_theme_failures(article: str, headings: list[str], facts: dict[str, Any]) -> list[str]:
    haystack = "\n".join(headings) + "\n" + article
    markers = list(CONCISE_THEME_MARKERS)
    if is_romantic_relationship(facts):
        markers += ROMANTIC_CONCISE_THEME_MARKERS
    missing = [marker for marker in markers if marker not in haystack]
    if missing:
        return [f"concise relationship report missing theme markers: {missing}"]
    return []


def heading_quality_failures(headings: list[str]) -> list[str]:
    failures: list[str] = []
    bad = [heading for heading in headings if any(marker in heading for marker in PROBLEM_HEADING_MARKERS)]
    if bad:
        failures.append(
            "relationship headings should be reader-facing appraisals, not problem/risk-framed: "
            + "；".join(bad[:3])
        )
    return failures


def heading_hook_customization_failures(headings: list[str]) -> list[str]:
    failures: list[str] = []
    hooks = [heading_hook(heading) for heading in headings if heading_hook(heading)]
    if not hooks:
        return failures
    default_heading_set = set(DEFAULT_RICH_HEADINGS)
    exact_default_count = sum(1 for heading in headings if heading in default_heading_set)
    if exact_default_count > 6:
        failures.append(
            "H2 heading hooks look like uncustomized template defaults; rewrite the words after the colon for this relationship."
        )
    hook_counts: dict[str, int] = {}
    for hook in hooks:
        hook_counts[hook] = hook_counts.get(hook, 0) + 1
    repeated_hooks = [hook for hook, count in hook_counts.items() if count > 3]
    if repeated_hooks:
        failures.append(
            "H2 heading hooks are too repetitive; each section needs a distinct reader-facing takeaway: "
            + "；".join(repeated_hooks[:3])
        )
    return failures


def process_talk_failures(article: str) -> list[str]:
    found = [marker for marker in PROCESS_TALK_MARKERS if marker in article]
    if not found:
        return []
    return [
        "reader-facing article contains process/editorial scaffolding language: "
        + "；".join(found[:8])
    ]


def scenario_distribution_failures(text: str, *, min_sections: int) -> list[str]:
    sections = h2_sections(text)
    if not sections:
        return []
    with_scenario = [
        heading
        for heading, body in sections
        if "白话场景" in body or "情景推演" in body
    ]
    if len(with_scenario) < min_sections:
        return [
            f"白话场景/情景推演 should be distributed across at least {min_sections} sections; "
            f"found {len(with_scenario)}."
        ]
    return []


def heading_topic(heading: str) -> str:
    if "：" in heading:
        return heading.split("：", 1)[0].strip()
    if ":" in heading:
        return heading.split(":", 1)[0].strip()
    return heading.strip()


def heading_hook(heading: str) -> str:
    if "：" in heading:
        return heading.split("：", 1)[1].strip()
    if ":" in heading:
        return heading.split(":", 1)[1].strip()
    return ""


def intimacy_boundary_failures(article: str, facts: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    explicit = [marker for marker in EXPLICIT_INTIMACY_MARKERS if marker in article]
    if explicit:
        failures.append(f"intimacy section contains explicit/private markers: {explicit}")
    if not is_romantic_relationship(facts):
        unsupported = [marker for marker in NON_ROMANTIC_INTIMACY_MARKERS if marker in article]
        if unsupported:
            failures.append(
                "non-romantic or unsupported relationship status should not use body-attraction/private romance framing: "
                + "；".join(unsupported[:6])
            )
    intimacy_terms = ["亲密", "私密", "身体吸引", "身体感", "调情"]
    concrete_frequency_terms = ["每天", "每周", "一周", "一天", "几次", "多少次"]
    sentences = [item for item in re.split(r"[。！？!?；;\n]+", article) if item.strip()]
    if any(
        any(term in sentence for term in intimacy_terms)
        and any(term in sentence for term in concrete_frequency_terms)
        for sentence in sentences
    ):
        failures.append("intimacy section should not infer concrete frequency or behavior cadence.")
    return failures


def relationship_balance_failures(article: str, *, profile: str) -> list[str]:
    failures: list[str] = []
    positive_count = sum(article.count(marker) for marker in POSITIVE_APPRAISAL_MARKERS)
    pressure_count = sum(article.count(marker) for marker in PRESSURE_MARKERS)
    min_positive = 12 if profile == "rich" else 6
    if positive_count < min_positive:
        failures.append(
            f"relationship appraisal is too thin: positive/constructive markers {positive_count} < {min_positive}."
        )
    if pressure_count > max(10, int(positive_count * 1.15)):
        failures.append(
            f"relationship tone is too pressure-framed: pressure markers {pressure_count} > positive markers {positive_count}."
        )
    return failures


def facts_schema_failures(facts: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if facts.get("module") != "relationship":
        failures.append("facts-json must be a relationship facts file.")
    mode = relationship_mode(facts)
    mode_failures = relationship_mode_schema_failures(mode)
    if mode_failures == ["relationship_mode missing or empty."]:
        failures.append("facts-json missing relationship_mode; rebuild relationship facts before validating.")
    else:
        failures.extend(mode_failures)
    domains = facts.get("relationship_life_domains")
    if not isinstance(domains, dict):
        return ["facts-json missing relationship_life_domains; rebuild relationship facts before validating."]
    missing_domains = [key for key in REQUIRED_LIFE_DOMAINS if key not in domains]
    if missing_domains:
        failures.append(f"relationship_life_domains missing required domains: {missing_domains}")
    for key, label in REQUIRED_LIFE_DOMAINS.items():
        item = domains.get(key)
        if not isinstance(item, dict):
            continue
        if item.get("label") != label:
            failures.append(f"relationship_life_domains.{key}.label should be {label}")
        for list_key in ["allowed_writing", "do_not_infer"]:
            values = item.get(list_key)
            if not isinstance(values, list) or not values:
                failures.append(f"relationship_life_domains.{key}.{list_key} must be a non-empty list")
        boundary = item.get("writing_boundary")
        if not isinstance(boundary, str) or len(boundary.strip()) < 8:
            failures.append(f"relationship_life_domains.{key}.writing_boundary is missing or too short")
        for person_key in ["person_a", "person_b"]:
            person = item.get(person_key)
            if not isinstance(person, dict):
                failures.append(f"relationship_life_domains.{key}.{person_key} missing")
                continue
            if not person.get("label"):
                failures.append(f"relationship_life_domains.{key}.{person_key}.label missing")
            if not isinstance(person.get("western_bodies"), list):
                failures.append(f"relationship_life_domains.{key}.{person_key}.western_bodies must be a list")
        if not isinstance(item.get("bazi_cross_anchors"), list):
            failures.append(f"relationship_life_domains.{key}.bazi_cross_anchors must be a list")
        if not isinstance(item.get("western_cross_anchors"), list):
            failures.append(f"relationship_life_domains.{key}.western_cross_anchors must be a list")
    return failures


def validate_rich_format(
    article: str,
    headings: list[str],
    *,
    min_chars: int,
    scenario_min: int,
    labels: tuple[str, str],
) -> list[str]:
    format_failures: list[str] = []
    topics = [heading_topic(heading) for heading in headings]
    if topics != REQUIRED_HEADING_TOPICS:
        format_failures.append("H2 heading topics must match the relationship rich outline.")
    weak_hooks = [
        heading
        for heading in headings
        if len(heading_hook(heading)) < 4 or len(heading_hook(heading)) > 28
    ]
    if weak_hooks:
        format_failures.append(
            "H2 headings must use topic plus a concise reader-facing hook after the colon: "
            + "；".join(weak_hooks[:3])
        )
    format_failures.extend(heading_hook_customization_failures(headings))
    scenario_count = article.count("白话场景") + article.count("情景推演")
    if scenario_count < scenario_min:
        format_failures.append(f"requires at least {scenario_min} 白话场景/情景推演 blocks")
    format_failures.extend(scenario_distribution_failures(article, min_sections=min(6, scenario_min)))
    if len(article) < min_chars:
        format_failures.append(f"article too short: {len(article)} < {min_chars}")
    person_a_label, person_b_label = labels
    if article.count(person_a_label) < 20 or article.count(person_b_label) < 20:
        format_failures.append(
            f"third-person naming is too weak; expected repeated {person_a_label} and {person_b_label} references."
        )
    bold_count = len(re.findall(r"\*\*[^*\n]{6,80}\*\*", article))
    if bold_count < 10:
        format_failures.append("expected at least 10 concise bold reader-facing takeaway sentences.")
    sections = h2_sections(article)
    first_bold_count = sum(1 for _, body in sections if first_paragraph_starts_bold(body))
    if sections and first_bold_count > max(12, int(len(sections) * 0.65)):
        format_failures.append("bold takeaways are too mechanically concentrated at the start of chapters.")
    return format_failures


def validate_concise_format(
    article: str,
    headings: list[str],
    *,
    min_chars: int,
    scenario_min: int,
    labels: tuple[str, str],
    facts: dict[str, Any],
) -> list[str]:
    format_failures: list[str] = []
    scenario_count = article.count("白话场景") + article.count("情景推演")
    if scenario_count < scenario_min:
        format_failures.append(f"requires at least {scenario_min} 白话场景/情景推演 blocks")
    format_failures.extend(scenario_distribution_failures(article, min_sections=min(2, scenario_min)))
    if len(article) < min_chars:
        format_failures.append(f"article too short: {len(article)} < {min_chars}")
    person_a_label, person_b_label = labels
    if article.count(person_a_label) < 8 or article.count(person_b_label) < 8:
        format_failures.append(
            f"third-person naming is too weak for concise relationship report; expected {person_a_label} and {person_b_label}."
        )
    bold_count = len(re.findall(r"\*\*[^*\n]{6,90}\*\*", article))
    if bold_count < 5:
        format_failures.append("expected at least 5 concise bold reader-facing takeaway sentences.")
    if not headings:
        format_failures.append("concise relationship report should still use scannable H2 sections.")
    format_failures.extend(concise_theme_failures(article, headings, facts))
    return format_failures


def main() -> int:
    args = parse_args()
    article = Path(args.article).read_text(encoding="utf-8")
    facts = json.loads(Path(args.facts_json).read_text(encoding="utf-8-sig"))
    person_a_label, person_b_label = relationship_labels(facts)
    min_chars = args.min_chars if args.min_chars is not None else (12000 if args.profile == "rich" else 6500)
    scenario_min = args.scenario_min if args.scenario_min is not None else (8 if args.profile == "rich" else 5)
    required = relationship_required_markers(facts, profile=args.profile)
    missing = [item for item in required if item and item not in article]
    forbidden_found = forbidden_markers(article, (person_a_label, person_b_label))
    schema_failures = facts_schema_failures(facts)
    format_failures: list[str] = []
    h1s = [line[2:].strip() for line in article.splitlines() if line.startswith("# ")]
    if not h1s:
        format_failures.append("article must have a reader-facing H1 title.")
    elif reader_title_label_failures(h1s[0]):
        format_failures.append(
            "reader-facing H1 should be a refined relationship appraisal, not a delivery/process label: "
            + "；".join(reader_title_label_failures(h1s[0]))
        )
    elif "问题" in h1s[0]:
        format_failures.append("reader-facing H1 should express an overall relationship rating, not frame the report as problems.")
    elif "合盘" not in h1s[0]:
        format_failures.append("relationship H1 must retain the relationship object, e.g. include 合盘 instead of only an abstract rating.")
    elif person_a_label not in h1s[0] or person_b_label not in h1s[0]:
        format_failures.append(
            f"relationship H1 must retain both relationship labels: {person_a_label} and {person_b_label}."
        )
    headings = h2_headings(article)
    scenario_count = article.count("白话场景") + article.count("情景推演")
    format_failures.extend(heading_quality_failures(headings))
    if args.profile == "rich":
        format_failures.extend(
            validate_rich_format(article, headings, min_chars=min_chars, scenario_min=scenario_min, labels=(person_a_label, person_b_label))
        )
    else:
        format_failures.extend(
            validate_concise_format(
                article,
                headings,
                min_chars=min_chars,
                scenario_min=scenario_min,
                labels=(person_a_label, person_b_label),
                facts=facts,
            )
        )
    ending = article[-900:]
    if not any(word in ending for word in ["越走越稳", "值得", "更甜", "更稳", "更有力量", "认真经营"]):
        format_failures.append("ending should close with a constructive relationship appraisal.")
    format_failures.extend(paragraph_repetition_failures(article))
    format_failures.extend(paragraph_tone_failures(article))
    format_failures.extend(process_talk_failures(article))
    format_failures.extend(intimacy_boundary_failures(article, facts))
    format_failures.extend(relationship_balance_failures(article, profile=args.profile))
    result = {
        "article": str(Path(args.article).resolve()),
        "facts_json": str(Path(args.facts_json).resolve()),
        "profile": args.profile,
        "chars": len(article),
        "scenario_count": scenario_count,
        "headings": headings,
        "missing": missing,
        "forbidden_found": forbidden_found,
        "facts_schema_failures": schema_failures,
        "format_failures": format_failures,
        "passed": not missing and not forbidden_found and not schema_failures and not format_failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
