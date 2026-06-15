#!/usr/bin/env python3
"""Audit a reader-facing article for facts that appear to belong to other cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check that a longform report does not leak markers from other fact JSON files.")
    parser.add_argument("article", help="Reader-facing Markdown article.")
    parser.add_argument("--facts-json", required=True, help="Current case combo JSON.")
    parser.add_argument(
        "--other-facts-json",
        action="append",
        default=[],
        help="Another case combo/module JSON whose unique markers must not appear. Can be repeated.",
    )
    parser.add_argument("--forbid", action="append", default=[], help="Extra exact marker that must not appear.")
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


def fact_markers(report: dict[str, Any]) -> set[str]:
    markers: set[str] = set()
    bazi = find_module(report, "bazi")
    if bazi:
        facts = bazi.get("facts", {})
        pillar_suffix = {"year": "年", "month": "月", "day": "日", "hour": "时"}
        for key, value in facts.get("pillars", {}).items():
            if value:
                suffix = pillar_suffix.get(key, "")
                markers.add(f"{value}{suffix}" if suffix else str(value))
        current_dayun = facts.get("flow", {}).get("current_dayun", {})
        if current_dayun.get("gan_zhi"):
            markers.add(f"当前大运{current_dayun['gan_zhi']}")
    ziwei = find_module(report, "ziwei")
    if ziwei:
        facts = ziwei.get("facts", {})
        if facts.get("soul_palace_branch"):
            markers.add(f"命宫{facts['soul_palace_branch']}")
        if facts.get("body_palace_branch"):
            markers.add(f"身宫{facts['body_palace_branch']}")
        current_decadal = facts.get("current_decadal") or {}
        if current_decadal.get("branch"):
            markers.add(f"大限{current_decadal['branch']}")
    western = find_module(report, "western")
    if western:
        facts = western.get("facts", {})
        for row in facts.get("placements", [])[:5]:
            if row.get("body") and row.get("sign"):
                markers.add(f"{row['body']}{row['sign']}")
        angles = facts.get("houses", {}).get("angles", {})
        for key in ["ascendant", "midheaven"]:
            display = angles.get(key, {}).get("display")
            if display:
                markers.add(str(display).replace("°", ""))
    return {item for item in markers if item}


def load_report(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    text = Path(args.article).read_text(encoding="utf-8")
    current_markers = fact_markers(load_report(args.facts_json))
    forbidden: set[str] = set(args.forbid)
    for other_path in args.other_facts_json:
        other_markers = fact_markers(load_report(other_path))
        forbidden.update(other_markers - current_markers)
    found = sorted(marker for marker in forbidden if marker and marker in text)
    result = {
        "article": args.article,
        "facts_json": args.facts_json,
        "other_facts_json": args.other_facts_json,
        "current_marker_count": len(current_markers),
        "forbidden_marker_count": len(forbidden),
        "forbidden_found": found,
        "passed": not found,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
