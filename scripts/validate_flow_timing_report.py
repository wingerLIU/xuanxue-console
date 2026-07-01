#!/usr/bin/env python3
"""Validate flow_timing_report drafts for concrete daily actions."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


BANNED_GENERIC_PHRASES = [
    "结构排雷",
    "资源谈判",
    "压力落地",
    "注意沟通",
    "适合推进",
    "谨慎合作",
    "注意合作",
    "谨慎推进",
]

HYPE_PHRASES = [
    "大桃花",
    "大机会",
    "大贵人",
    "大转折",
    "必成",
    "必发财",
    "必翻身",
]

WEAK_ACTION_PATTERNS = [
    r"^注意[^，。；;]{0,8}$",
    r"^适合[^，。；;]{0,8}$",
    r"^谨慎[^，。；;]{0,8}$",
    r"^可以推进$",
    r"^保持沟通$",
]

ACTION_MARKERS = [
    "把",
    "先",
    "只",
    "别",
    "不要",
    "写",
    "谈",
    "问",
    "检查",
    "确认",
    "复盘",
    "收",
    "跑",
    "盯",
    "压成",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate flow_timing_report Markdown or HTML.")
    parser.add_argument("report")
    parser.add_argument("--case-keyword", action="append", default=[], help="Case-specific keyword. Repeat at least 5 times.")
    parser.add_argument("--min-case-keywords", type=int, default=5)
    parser.add_argument("--sample-days", type=int, default=10)
    parser.add_argument("--min-days", type=int, default=1)
    return parser.parse_args()


def clean_keywords(raw: list[str]) -> list[str]:
    keywords: list[str] = []
    for item in raw:
        for part in re.split(r"[,，/、]", item):
            text = part.strip()
            if text and text not in keywords:
                keywords.append(text)
    return keywords


def strip_tags(text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", "", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", "", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def parse_markdown_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-"} for cell in cells):
            continue
        if "日期" in cells and "今天就看这件事" in cells:
            headers = cells
            continue
        if headers and re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[0] if cells else ""):
            rows.append({headers[idx]: cells[idx] if idx < len(cells) else "" for idx in range(len(headers))})
    return rows


def parse_html_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", text, flags=re.I | re.S):
        cells = [strip_tags(cell).strip() for cell in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", tr, flags=re.I | re.S)]
        if not cells:
            continue
        if "日期" in cells and "今天就看这件事" in cells:
            headers = cells
            continue
        if headers and re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[0] if cells else ""):
            rows.append({headers[idx]: cells[idx] if idx < len(cells) else "" for idx in range(len(headers))})
    return rows


def sampled_rows(rows: list[dict[str, str]], sample_days: int) -> list[dict[str, str]]:
    if len(rows) <= sample_days:
        return rows
    step = (len(rows) - 1) / max(1, sample_days - 1)
    indexes = sorted({round(idx * step) for idx in range(sample_days)})
    return [rows[index] for index in indexes]


def weak_action(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return True
    if any(re.fullmatch(pattern, compact) for pattern in WEAK_ACTION_PATTERNS):
        return True
    return not any(marker in compact for marker in ACTION_MARKERS)


def main() -> int:
    args = parse_args()
    path = Path(args.report)
    text = path.read_text(encoding="utf-8-sig")
    plain = strip_tags(text) if path.suffix.lower() in {".html", ".htm"} else text
    rows = parse_html_rows(text) if path.suffix.lower() in {".html", ".htm"} else parse_markdown_rows(text)
    keywords = clean_keywords(args.case_keyword)

    failures: list[str] = []
    warnings: list[str] = []
    if "今天就看这件事" not in plain:
        failures.append("missing required phrase: 今天就看这件事")
    if len(rows) < args.min_days:
        failures.append(f"daily table has {len(rows)} rows; minimum is {args.min_days}")
    banned = [phrase for phrase in BANNED_GENERIC_PHRASES if phrase in plain]
    if banned:
        failures.append(f"banned generic phrases found: {banned}")
    hype = [phrase for phrase in HYPE_PHRASES if phrase in plain]
    if hype:
        failures.append(f"banned hype phrases found: {hype}")
    distinct_hits = [keyword for keyword in keywords if keyword in plain]
    required_keyword_count = min(args.min_case_keywords, len(keywords)) if keywords else args.min_case_keywords
    if len(distinct_hits) < required_keyword_count:
        failures.append(
            f"case-specific keyword hits {len(distinct_hits)} {distinct_hits}; minimum is {required_keyword_count}"
        )
    if not keywords:
        warnings.append("no --case-keyword provided; report may pass structure but cannot prove personalization")

    weak_rows: list[str] = []
    missing_action_rows: list[str] = []
    for row in sampled_rows(rows, args.sample_days):
        date = row.get("日期", "")
        judgment = row.get("今天就看这件事", "")
        action = row.get("现实动作", "")
        if not judgment or not action:
            missing_action_rows.append(date)
            continue
        if weak_action(judgment) or weak_action(action):
            weak_rows.append(date)
    if missing_action_rows:
        failures.append(f"sampled rows missing judgment or action: {missing_action_rows}")
    if weak_rows:
        failures.append(f"sampled rows have weak generic action language: {weak_rows}")

    result = {
        "report": str(path),
        "rows": len(rows),
        "sample_days": min(args.sample_days, len(rows)),
        "case_keyword_hits": distinct_hits,
        "failures": failures,
        "warnings": warnings,
        "passed": not failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
