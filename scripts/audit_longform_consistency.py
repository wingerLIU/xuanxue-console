#!/usr/bin/env python3
"""Audit longform xuanxue reports for fact grounding and risky over-claims."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


H3_SECTION_REQUIREMENTS = {
    "事业：适合赛道、工作方式与组织环境": ["白话场景", "风险在于", "更好的做法"],
    "财富：收入模型、预算与合作边界": ["白话场景", "风险在于", "更好的做法"],
    "爱情：亲密关系、沟通缺口与推进节奏": ["白话场景", "风险在于", "更好的做法"],
    "健康与精力：压力、作息与恢复": ["白话场景", "风险在于", "更好的做法"],
    "人际合作：贵人、同侪、分工与合同": ["白话场景", "风险在于", "更好的做法"],
    "学习成长：作品、方法论与输出": ["白话场景", "风险在于", "更好的做法"],
}

PAST_YEAR_REQUIREMENTS = ["盘面触发", "现实倾向", "可校准问题"]
FUTURE_YEAR_REQUIREMENTS = ["事业", "财富", "感情", "精力", "建议动作"]

ABSOLUTE_CLAIMS = [
    r"(?<!不)必然",
    r"(?<!不)必定",
    r"(?<!不)注定",
    r"一定会",
    r"绝对会",
    r"肯定会",
    r"必赚",
    r"稳赚",
    r"必亏",
    r"必离婚",
    r"会离婚",
    r"会得[一-龥A-Za-z0-9]{0,8}(病|癌|症)",
    r"诊断为",
    r"买入",
    r"卖出",
    r"满仓",
    r"梭哈",
]

SCOPE_MARKERS = [
    "不替代医疗",
    "不替代法律",
    "不替代投资",
    "不做诊断",
    "不写投资承诺",
    "不做投资承诺",
]

LEXICAL_OVERUSE_LIMITS = {
    "边界": 34,
    "表达": 42,
}

COMMERCIAL_TEMPLATE_LIMITS = {
    "修改次数": 2,
    "报价表": 2,
    "交付表": 2,
    "变更表": 1,
}

BOUNDARY_PERSONA_PATTERNS = [
    r"不表达",
    r"不够会表达",
    r"需求藏",
    r"需求压",
    r"不说.*对方",
    r"对方.*猜",
]

TEMPLATE_DRIFT_CLUSTERS = {
    "boundary_expression": [
        r"边界",
        r"表达",
        r"说清楚",
        r"提前说明",
        r"对方.*猜",
        r"沉默",
        r"冷处理",
    ],
    "safety_sensitivity": [
        r"安全感",
        r"敏感",
        r"被消耗",
        r"防御",
        r"慢热",
        r"心里",
    ],
    "productization": [
        r"作品",
        r"作品集",
        r"可见产物",
        r"交付",
        r"流程",
        r"复盘",
        r"方法论",
    ],
    "money_contract": [
        r"预算",
        r"合同",
        r"回款",
        r"钱账",
        r"报价",
        r"分工",
        r"修改",
    ],
    "energy_recovery": [
        r"恢复",
        r"作息",
        r"睡眠",
        r"运动",
        r"独处",
        r"精力",
    ],
    "quality_environment": [
        r"粗糙",
        r"质量",
        r"细节",
        r"标准",
        r"催促",
        r"临时",
    ],
    "misread_template": [
        r"别人可能会怎样误读",
        r"别人.*误读",
        r"看起来.*其实",
        r"表面.*内心",
        r"不适合长期",
    ],
}

TEMPLATE_DRIFT_MIN_COUNTS = {
    "boundary_expression": 12,
    "safety_sensitivity": 18,
    "productization": 18,
    "money_contract": 8,
    "energy_recovery": 8,
    "quality_environment": 18,
    "misread_template": 8,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit longform report consistency and over-claim risk.")
    parser.add_argument("article", help="Path to the longform Markdown article.")
    parser.add_argument("--facts-json", required=True, help="Current case combo/module JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on section-structure warnings, not only hard fact and risk failures.",
    )
    parser.add_argument(
        "--compare-article",
        action="append",
        default=[],
        help="Previous report Markdown to compare for expression/template drift. Can be repeated.",
    )
    parser.add_argument(
        "--compare-recent",
        type=int,
        default=0,
        help="Auto-discover this many recent reader-rich longform reports from the runs root.",
    )
    parser.add_argument(
        "--compare-run-root",
        help="Runs root for --compare-recent. Defaults to inferring from <RUN_DIR>/drafts/<case>-longform.md.",
    )
    parser.add_argument(
        "--current-run-dir",
        help="Current run directory to exclude for --compare-recent. Defaults to inferring from article path.",
    )
    parser.add_argument(
        "--max-ngram-jaccard",
        type=float,
        default=0.015,
        help="Warn when normalized 12-character n-gram overlap with a previous report exceeds this value.",
    )
    parser.add_argument(
        "--max-shared-theme-clusters",
        type=int,
        default=4,
        help="Warn when too many generic expression theme clusters are active in both current and compared reports.",
    )
    return parser.parse_args()


def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def section_map(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line)
    return {key: "\n".join(value) for key, value in sections.items()}


def h3_section_map(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        if line.startswith("### "):
            current = line[4:].strip()
            sections.setdefault(current, [])
        elif line.startswith("## "):
            current = ""
        elif current:
            sections[current].append(line)
    return {key: "\n".join(value) for key, value in sections.items()}


def expected_facts(report: dict[str, Any]) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "natal_pillars": [],
        "current_dayun": None,
        "flow_pillars": [],
        "western_placements": [],
        "ziwei_markers": [],
    }
    bazi = find_module(report, "bazi")
    if bazi:
        bazi_facts = bazi.get("facts", {})
        pillars = bazi_facts.get("pillars", {})
        facts["natal_pillars"] = [str(pillars.get(key, "")) for key in ["year", "month", "day", "hour"] if pillars.get(key)]
        current_dayun = bazi_facts.get("flow", {}).get("current_dayun", {})
        if current_dayun.get("gan_zhi"):
            facts["current_dayun"] = str(current_dayun["gan_zhi"])
        flow_pillars = bazi_facts.get("flow", {}).get("pillars", {})
        facts["flow_pillars"] = [str(flow_pillars.get(key, "")) for key in ["year", "month", "day"] if flow_pillars.get(key)]
    ziwei = find_module(report, "ziwei")
    if ziwei:
        ziwei_facts = ziwei.get("facts", {})
        if ziwei_facts.get("soul_palace_branch"):
            facts["ziwei_markers"].append(f"命宫{ziwei_facts['soul_palace_branch']}")
        if ziwei_facts.get("body_palace_branch"):
            facts["ziwei_markers"].append(f"身宫{ziwei_facts['body_palace_branch']}")
        current_decadal = ziwei_facts.get("current_decadal") or {}
        if current_decadal.get("name"):
            facts["ziwei_markers"].append(str(current_decadal["name"]))
    western = find_module(report, "western")
    if western:
        for row in western.get("facts", {}).get("placements", [])[:5]:
            if row.get("body") and row.get("sign"):
                facts["western_placements"].append(f"{row['body']}{row['sign']}")
    return facts


def fact_failures(text: str, facts: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for marker in facts["natal_pillars"]:
        if marker not in text:
            failures.append(f"missing natal pillar marker: {marker}")
    current_dayun = facts.get("current_dayun")
    if current_dayun and current_dayun not in text:
        failures.append(f"missing current dayun marker: {current_dayun}")
    for marker in facts["flow_pillars"]:
        if marker not in text:
            failures.append(f"missing flow pillar marker: {marker}")
    for marker in facts["western_placements"]:
        if marker not in text:
            failures.append(f"missing western placement marker: {marker}")
    for marker in facts["ziwei_markers"]:
        alternates = [marker]
        if marker.startswith(("命宫", "身宫")) and len(marker) > 2:
            alternates.append(f"{marker[:2]}在{marker[2:]}")
        if not any(item in text for item in alternates):
            failures.append(f"missing ziwei marker: {marker}")
    return failures


def risk_failures(text: str) -> list[str]:
    failures: list[str] = []
    for pattern in ABSOLUTE_CLAIMS:
        matches = sorted(set(re.findall(pattern, text)))
        if matches:
            failures.append(f"risky absolute or high-stakes claim matched /{pattern}/: {matches[:5]}")
    if not any(marker in text for marker in SCOPE_MARKERS):
        failures.append("missing scope boundary marker: report should state it does not replace professional decisions")
    return failures


def section_warnings(text: str) -> list[str]:
    sections = section_map(text)
    h3_sections = h3_section_map(text)
    warnings: list[str] = []
    for title, required in H3_SECTION_REQUIREMENTS.items():
        body = h3_sections.get(title)
        if body is None:
            warnings.append(f"missing fixed topic subsection: {title}")
            continue
        for marker in required:
            if marker not in body:
                warnings.append(f"subsection {title} missing marker: {marker}")
    past = sections.get("11 过去几年故事线", "")
    for marker in PAST_YEAR_REQUIREMENTS:
        if marker not in past:
            warnings.append(f"past-year section missing marker: {marker}")
    future = sections.get("12 未来几年趋势", "")
    for marker in FUTURE_YEAR_REQUIREMENTS:
        if marker not in future:
            warnings.append(f"future-year section missing marker: {marker}")
    time_boundary = sections.get("03 基础排盘信息与时间可信度", "") + "\n" + sections.get("04 时间敏感性检查", "")
    for marker in ["时间可信度", "稳定", "敏感"]:
        if marker not in time_boundary:
            warnings.append(f"time-sensitivity sections missing marker: {marker}")
    return warnings


def contradiction_warnings(text: str) -> list[str]:
    warnings: list[str] = []
    sections = section_map(text)
    polarity_pairs = [
        ("适合稳定", "不适合稳定"),
        ("适合合伙", "不适合合伙"),
        ("适合创业", "不适合创业"),
        ("感情推进", "感情收缩"),
        ("财富扩张", "财富收缩"),
    ]
    for title, body in sections.items():
        for left, right in polarity_pairs:
            if left in body and right in body and not any(token in body for token in ["前提", "条件", "分情况", "但", "风险"]):
                warnings.append(f"possible unresolved polarity in {title}: {left} / {right}")
    return warnings


def lexical_overuse_warnings(text: str) -> list[str]:
    warnings: list[str] = []
    for token, limit in LEXICAL_OVERUSE_LIMITS.items():
        count = text.count(token)
        if count > limit:
            warnings.append(
                f"possible template overuse: `{token}` appears {count} times; keep only evidence-backed uses"
            )
    persona_hits = 0
    for pattern in BOUNDARY_PERSONA_PATTERNS:
        persona_hits += len(re.findall(pattern, text))
    if persona_hits > 3:
        warnings.append(
            "possible repeated boundary-expression persona: make it a calibrated claim or vary by concrete evidence"
        )
    for token, limit in COMMERCIAL_TEMPLATE_LIMITS.items():
        count = text.count(token)
        if count > limit:
            warnings.append(
                f"possible commercial-template overuse: `{token}` appears {count} times; use only when business/service context is evidence-backed"
            )
    return warnings


def comparable_body(text: str) -> str:
    body = re.split(r"\n## 15 技术证据附录", text, maxsplit=1)[0]
    body = re.sub(r"^#+ .*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"`[^`]+`", "", body)
    body = re.sub(r"[A-Za-z0-9_\-./\\:]+", "", body)
    return re.sub(r"\s+", "", body)


def char_ngrams(text: str, n: int = 12) -> set[str]:
    clean = re.sub(r"[#*_，。；：、“”\"'（）()！？!?、\s]+", "", comparable_body(text))
    return {clean[idx : idx + n] for idx in range(max(0, len(clean) - n + 1)) if len(clean[idx : idx + n]) == n}


def ngram_jaccard(left: str, right: str, n: int = 12) -> float:
    left_ngrams = char_ngrams(left, n=n)
    right_ngrams = char_ngrams(right, n=n)
    union = left_ngrams | right_ngrams
    if not union:
        return 0.0
    return len(left_ngrams & right_ngrams) / len(union)


def theme_cluster_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cluster, patterns in TEMPLATE_DRIFT_CLUSTERS.items():
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text))
        counts[cluster] = count
    return counts


def active_theme_clusters(counts: dict[str, int]) -> set[str]:
    return {
        cluster
        for cluster, count in counts.items()
        if count >= TEMPLATE_DRIFT_MIN_COUNTS.get(cluster, 1)
    }


def infer_current_run_dir(article: Path) -> Path | None:
    parts = article.resolve().parts
    if len(parts) >= 2 and article.parent.name == "drafts":
        return article.parent.parent
    return None


def infer_runs_root(article: Path) -> Path | None:
    run_dir = infer_current_run_dir(article)
    if run_dir and run_dir.parent.parent.exists():
        return run_dir.parent.parent
    return None


def is_reader_rich_longform(path: Path) -> bool:
    name = path.name.lower()
    if not name.endswith("-longform.md") or name.endswith("-longform-draft.md"):
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    chars = len(re.sub(r"\s+", "", text))
    h2_count = len(re.findall(r"^##\s+", text, flags=re.MULTILINE))
    return chars >= 12000 and h2_count >= 12


def discover_recent_compare_articles(
    article: Path,
    *,
    compare_recent: int,
    compare_run_root: str | None,
    current_run_dir: str | None,
) -> list[str]:
    if compare_recent <= 0:
        return []
    runs_root = Path(compare_run_root).resolve() if compare_run_root else infer_runs_root(article)
    if runs_root is None or not runs_root.exists():
        return []
    current_run = Path(current_run_dir).resolve() if current_run_dir else infer_current_run_dir(article)
    current_article = article.resolve()
    candidates: list[Path] = []
    for path in runs_root.glob("*/*/drafts/*-longform.md"):
        resolved = path.resolve()
        if resolved == current_article:
            continue
        if current_run is not None:
            try:
                resolved.relative_to(current_run)
                continue
            except ValueError:
                pass
        if is_reader_rich_longform(resolved):
            candidates.append(resolved)
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [str(path) for path in candidates[:compare_recent]]


def similarity_warnings(
    text: str,
    compare_articles: list[str],
    *,
    max_ngram_jaccard: float,
    max_shared_theme_clusters: int,
) -> tuple[list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    comparisons: list[dict[str, Any]] = []
    current_clusters = theme_cluster_counts(text)
    for article in compare_articles:
        path = Path(article)
        previous = path.read_text(encoding="utf-8")
        previous_clusters = theme_cluster_counts(previous)
        current_active = active_theme_clusters(current_clusters)
        previous_active = active_theme_clusters(previous_clusters)
        shared_clusters = sorted(
            cluster
            for cluster in current_active
            if cluster in previous_active
        )
        jaccard = ngram_jaccard(text, previous)
        comparison = {
            "article": str(path),
            "ngram_jaccard_12": round(jaccard, 6),
            "shared_theme_clusters": shared_clusters,
            "current_theme_counts": {cluster: current_clusters[cluster] for cluster in shared_clusters},
            "previous_theme_counts": {cluster: previous_clusters[cluster] for cluster in shared_clusters},
        }
        comparisons.append(comparison)
        if jaccard > max_ngram_jaccard:
            warnings.append(
                f"possible expression reuse with {path}: 12-char ngram jaccard {jaccard:.4f} exceeds {max_ngram_jaccard:.4f}"
            )
        if len(shared_clusters) > max_shared_theme_clusters:
            warnings.append(
                "possible report-to-report template drift with {path}: shared generic theme clusters {clusters}; "
                "rewrite first two sections and topic advice around case-specific discriminators".format(
                    path=path,
                    clusters=", ".join(shared_clusters),
                )
            )
    return warnings, comparisons


def main() -> int:
    args = parse_args()
    article_path = Path(args.article)
    text = article_path.read_text(encoding="utf-8")
    report = load_json(args.facts_json)
    facts = expected_facts(report)
    hard_failures = fact_failures(text, facts) + risk_failures(text)
    discovered_compare_articles = discover_recent_compare_articles(
        article_path,
        compare_recent=args.compare_recent,
        compare_run_root=args.compare_run_root,
        current_run_dir=args.current_run_dir,
    )
    compare_articles = list(dict.fromkeys([*args.compare_article, *discovered_compare_articles]))
    similarity_items_warnings, comparisons = similarity_warnings(
        text,
        compare_articles,
        max_ngram_jaccard=args.max_ngram_jaccard,
        max_shared_theme_clusters=args.max_shared_theme_clusters,
    )
    warnings = (
        section_warnings(text)
        + contradiction_warnings(text)
        + lexical_overuse_warnings(text)
        + similarity_items_warnings
    )
    failures = hard_failures + (warnings if args.strict else [])
    result = {
        "article": args.article,
        "facts_json": args.facts_json,
        "strict": args.strict,
        "discovered_compare_articles": discovered_compare_articles,
        "comparisons": comparisons,
        "hard_failures": hard_failures,
        "warnings": warnings,
        "passed": not failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
