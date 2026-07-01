#!/usr/bin/env python3
"""Build a flow timing Markdown + HTML draft from Bazi flow facts."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

try:
    from xuanxue_console import bazi_relationships
except ModuleNotFoundError:  # pragma: no cover - direct script execution from repo root
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from xuanxue_console import bazi_relationships


SCHEMA_VERSION = "0.1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build flow_timing_report Markdown and HTML drafts.")
    parser.add_argument("--facts-json", required=True, help="Bazi or combo JSON with natal pillars and dayun rows.")
    parser.add_argument("--start", required=True, help="Start date, YYYY-MM-DD.")
    parser.add_argument("--end", help="End date, YYYY-MM-DD. Defaults to --start + --days - 1.")
    parser.add_argument("--days", type=int, default=30, help="Number of days when --end is omitted.")
    parser.add_argument("--title", default="流月流日行动节奏报告")
    parser.add_argument("--reader-name", default="")
    parser.add_argument("--case-keyword", action="append", default=[], help="Case-specific keyword. Repeat at least 5 times.")
    parser.add_argument("--context", action="append", default=[], help="Short real-world context sentence. Can be repeated.")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-html", required=True)
    parser.add_argument("--json-output", help="Optional machine-readable timing facts output.")
    return parser.parse_args()


def parse_ymd(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid date {value!r}; expected YYYY-MM-DD") from exc


def require_lunar_python():
    try:
        from lunar_python import Solar
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit("Missing dependency: lunar-python. Install with: python -m pip install lunar-python") from exc
    return Solar


def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def modules_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    if report.get("module") == "combo":
        modules = report.get("facts", {}).get("modules", [])
        return modules if isinstance(modules, list) else []
    return [report]


def bazi_facts(report: dict[str, Any]) -> dict[str, Any]:
    for item in modules_from_report(report):
        if item.get("module") == "bazi":
            facts = item.get("facts", {})
            if isinstance(facts, dict):
                return facts
    raise SystemExit("facts-json does not contain bazi facts")


def clean_keywords(raw: list[str]) -> list[str]:
    keywords: list[str] = []
    for item in raw:
        for part in re.split(r"[,，/、]", item):
            text = part.strip()
            if text and text not in keywords:
                keywords.append(text)
    return keywords


def keyword_at(keywords: list[str], index: int) -> str:
    if not keywords:
        return "本项目"
    return keywords[index % len(keywords)]


def flow_pillars(day: date) -> dict[str, str]:
    Solar = require_lunar_python()
    ec = Solar.fromYmdHms(day.year, day.month, day.day, 0, 0, 0).getLunar().getEightChar()
    return {"year": ec.getYear(), "month": ec.getMonth(), "day": ec.getDay()}


def current_dayun(dayun_rows: list[dict[str, Any]], day: date) -> dict[str, Any] | None:
    return next(
        (row for row in dayun_rows if row.get("start_year", 9999) <= day.year <= row.get("end_year", -9999)),
        None,
    )


def relation_names(relationships: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for section in ["flow", "flow_with_dayun"]:
        data = relationships.get(section, {})
        for key in ["stems", "branches"]:
            for row in data.get(key, []) if isinstance(data, dict) else []:
                relation = str(row.get("relation", "")).strip()
                if relation and relation not in names:
                    names.append(relation)
    return names


def action_for_day(index: int, keywords: list[str], relation_count: int) -> tuple[str, str]:
    kw0 = keyword_at(keywords, index)
    kw1 = keyword_at(keywords, index + 1)
    kw2 = keyword_at(keywords, index + 2)
    templates = [
        (f"今天就盯 {kw0} 的一个小闭环。", f"只跑一个能当天回收反馈的动作，把结果写进 {kw0} 复盘。"),
        (f"把 {kw0} 里的口头承诺翻译成条款。", f"围绕 {kw1} 写清责任、金额、时间或交付口径，没讲清的不进执行。"),
        (f"高冲突日，只谈 {kw0} 的事实。", f"对 {kw1} 只发事实、数据和下一步，不在群里临时拍大板。"),
        (f"别替 {kw0} 认领新锅。", f"先问谁拍板、谁给资源、谁验收，再决定 {kw1} 是否进入本周动作。"),
        (f"今天适合把 {kw0} 压成一句可确认的话。", f"把 {kw1} 的报价、回款、ROI 或交付边界写成对方能回复的确认句。"),
        (f"{kw0} 可以试运行，别搞大改革。", f"只给 {kw1} 一个小版本和一个观测指标，别同时改组织、产品和人。"),
        (f"今天先把 {kw0} 的人情账说清楚。", f"把熟人合作里的 {kw1}、边界和回款写进备忘，不靠感觉推进。"),
    ]
    judgment, action = templates[index % len(templates)]
    if relation_count >= 3:
        action += f" {kw2} 相关事项今天先控范围，不扩承诺。"
    return judgment, action


def month_theme(month_pillar: str, ordinal: int, keywords: list[str]) -> str:
    kw0 = keyword_at(keywords, ordinal)
    kw1 = keyword_at(keywords, ordinal + 1)
    themes = [
        f"{month_pillar}：别在火气里认领新锅，先把 {kw0} 的小闭环收住。",
        f"{month_pillar}：把 {kw0}、钱、责任翻译成条款；{kw1} 不能只靠感觉。",
        f"{month_pillar}：只跑小闭环，不搞大改革，用 {kw0} 的试运行数据换下一步授权。",
        f"{month_pillar}：对上汇报先讲事实和 ROI，再谈 {kw0} 的扩展。",
    ]
    return themes[ordinal % len(themes)]


def build_rows(facts: dict[str, Any], start: date, end: date, keywords: list[str]) -> list[dict[str, Any]]:
    natal_pillars = facts.get("pillars", {})
    if not isinstance(natal_pillars, dict) or not natal_pillars:
        raise SystemExit("bazi facts missing pillars")
    dayun_rows = facts.get("dayun", [])
    rows: list[dict[str, Any]] = []
    day = start
    index = 0
    while day <= end:
        flow = flow_pillars(day)
        dayun = current_dayun(dayun_rows if isinstance(dayun_rows, list) else [], day)
        relationships = bazi_relationships(natal_pillars, flow, dayun)
        relations = relation_names(relationships)
        judgment, action = action_for_day(index, keywords, len(relations))
        trigger = "、".join(relations[:3]) if relations else f"流月{flow['month']}、流日{flow['day']}"
        if dayun and dayun.get("gan_zhi"):
            trigger = f"大运{dayun['gan_zhi']}；{trigger}"
        rows.append({
            "date": day.isoformat(),
            "flow_year": flow["year"],
            "flow_month": flow["month"],
            "flow_day": flow["day"],
            "current_dayun": dayun.get("gan_zhi", "") if dayun else "",
            "judgment": judgment,
            "action": action,
            "trigger": trigger,
            "relation_count": len(relations),
        })
        day += timedelta(days=1)
        index += 1
    return rows


def month_sections(rows: list[dict[str, Any]], keywords: list[str]) -> list[str]:
    month_order: list[str] = []
    for row in rows:
        month = str(row["flow_month"])
        if month not in month_order:
            month_order.append(month)
    return [month_theme(month, index, keywords) for index, month in enumerate(month_order)]


def key_dates(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    selected = sorted(rows, key=lambda row: (int(row["relation_count"]), row["date"]), reverse=True)[:limit]
    return sorted(selected, key=lambda row: row["date"])


def markdown_report(args: argparse.Namespace, rows: list[dict[str, Any]], keywords: list[str]) -> str:
    reader = f"{args.reader_name} " if args.reader_name else ""
    context = "；".join(args.context) if args.context else "、".join(keywords[:6]) or "本阶段现实事项"
    lines = [
        f"# {reader}{args.title}",
        "",
        "## 一句话总判断",
        "",
        f"这段时间不要把流日当玄学按钮，而是每天盯一个现实动作：围绕 {context}，先收小闭环、条款、回款和复盘，再决定是否扩大承诺。",
        "",
        "## 未来几段流月差异",
        "",
    ]
    for item in month_sections(rows, keywords):
        lines.append(f"- {item}")
    lines.extend(["", "## 重点日期", ""])
    for row in key_dates(rows):
        lines.extend([
            f"### {row['date']}：{row['flow_month']}月 / {row['flow_day']}日",
            "",
            f"- 今天就看这件事：{row['judgment']}",
            f"- 现实动作：{row['action']}",
            f"- 盘面触发：{row['trigger']}",
            "",
        ])
    lines.extend([
        "## 每日表",
        "",
        "| 日期 | 流月 | 流日 | 今天就看这件事 | 现实动作 | 盘面触发 |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in rows:
        lines.append(
            "| {date} | {flow_month} | {flow_day} | {judgment} | {action} | {trigger} |".format(**row)
        )
    lines.extend([
        "",
        "## 使用边界",
        "",
        "- 这份报告只把流月流日转成行动节奏，不承诺无条件成功。",
        "- 流日只适合已有明确事项后的短窗口；没有事项时，只看月度节奏。",
        "- 医疗、法律、投资、婚恋和重大人生决定必须回到专业意见和现实证据。",
        "- 如果出生时间、真太阳时或时辰边界不稳，本报告只能作为待校准倾向。",
    ])
    return "\n".join(lines) + "\n"


def html_report(markdown: str, title: str) -> str:
    body_lines: list[str] = []
    in_table = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            if in_table:
                body_lines.append("</tbody></table>")
                in_table = False
            continue
        if line.startswith("# "):
            body_lines.append(f"<h1>{html.escape(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            if in_table:
                body_lines.append("</tbody></table>")
                in_table = False
            body_lines.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            body_lines.append(f"<h3>{html.escape(line[4:].strip())}</h3>")
        elif line.startswith("- "):
            body_lines.append(f"<p class=\"bullet\">{html.escape(line[2:].strip())}</p>")
        elif line.startswith("| "):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if set(cells) == {"---"}:
                continue
            if not in_table:
                body_lines.append("<table><tbody>")
                in_table = True
            tag = "th" if cells and cells[0] == "日期" else "td"
            body_lines.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
        else:
            body_lines.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        body_lines.append("</tbody></table>")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
body{{margin:0;background:#f6f0e5;color:#241f1a;font-family:"Songti SC","SimSun",serif;line-height:1.75;}}
main{{max-width:980px;margin:0 auto;padding:28px 18px 56px;}}
h1{{font-size:30px;line-height:1.25;margin:8px 0 28px;}}
h2{{font-size:22px;margin:34px 0 12px;border-top:1px solid #d8c8ad;padding-top:22px;}}
h3{{font-size:18px;margin:24px 0 8px;}}
p{{font-size:16px;margin:10px 0;}}
.bullet::before{{content:"- ";}}
table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:15px;background:#fffaf1;}}
th,td{{border:1px solid #dccdb4;padding:9px 10px;vertical-align:top;text-align:left;}}
th{{background:#efe2cf;font-weight:700;}}
@media (max-width:720px){{main{{padding:22px 12px 44px;}} table{{display:block;overflow-x:auto;white-space:nowrap;}} h1{{font-size:26px;}}}}
</style>
</head>
<body><main>
{chr(10).join(body_lines)}
</main></body>
</html>
"""


def main() -> int:
    args = parse_args()
    start = parse_ymd(args.start)
    end = parse_ymd(args.end) if args.end else start + timedelta(days=max(1, args.days) - 1)
    if end < start:
        raise SystemExit("--end must be on or after --start")
    if (end - start).days > 120:
        raise SystemExit("flow_timing_report is capped at 121 days; split longer windows")
    keywords = clean_keywords(args.case_keyword)
    facts = bazi_facts(load_json(args.facts_json))
    rows = build_rows(facts, start, end, keywords)
    markdown = markdown_report(args, rows, keywords)
    html_text = html_report(markdown, args.title)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_html).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(markdown, encoding="utf-8")
    Path(args.output_html).write_text(html_text, encoding="utf-8")
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "type": "flow_timing_report",
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "case_keywords": keywords,
                    "rows": rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    print(json.dumps({"passed": True, "output_md": args.output_md, "output_html": args.output_html, "days": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
