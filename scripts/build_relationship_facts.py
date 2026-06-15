#!/usr/bin/env python3
"""Build deterministic relationship/synastry facts from two existing case runs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from xuanxue_console import (
    FLOW_LABELS,
    PILLAR_LABELS,
    branch_relationships,
    named_items_from_pillars,
    stem_relationships,
)
from relationship_mode import relationship_mode_from_status


WESTERN_ASPECTS = [
    ("合相", 0, 8),
    ("冲相", 180, 8),
    ("刑相", 90, 6),
    ("拱相", 120, 6),
    ("六合", 60, 5),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a relationship fact package from two xuanxue case manifests.")
    parser.add_argument("--manifest", required=True, help="Relationship run case_manifest.json to update.")
    parser.add_argument("--person-a-manifest", required=True, help="First person's existing case_manifest.json.")
    parser.add_argument("--person-b-manifest", required=True, help="Second person's existing case_manifest.json.")
    parser.add_argument("--person-a-label", required=True)
    parser.add_argument("--person-b-label", required=True)
    parser.add_argument("--relationship-status", required=True, help="Known real-world relationship status, e.g. 男女朋友.")
    parser.add_argument("--distance-status", required=True, help="Known real-world distance status, e.g. 异地.")
    parser.add_argument("--person-a-mbti-type", help="Optional user-provided MBTI type, supports ENTP-A / ENTP-T.")
    parser.add_argument("--person-b-mbti-type", help="Optional user-provided MBTI type, supports ISFP-A / ISFP-T.")
    parser.add_argument("--output-json", help="Output JSON path; defaults to <run>/data/<case>-relationship.json.")
    parser.add_argument("--output-md", help="Output Markdown fact archive; defaults to <run>/data/<case>-relationship-facts.md.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def artifact_data(manifest: dict[str, Any], module: str) -> Path | None:
    artifacts = manifest.get("artifacts", {})
    data = artifacts.get("data", {}) if isinstance(artifacts, dict) else {}
    candidates = []
    if isinstance(data, dict):
        candidates.append(data.get(module))
    if isinstance(artifacts, dict):
        candidates.extend([artifacts.get(f"data_{module}"), artifacts.get(module)])
    for value in candidates:
        if value:
            path = Path(str(value))
            if path.exists():
                return path
    data_dir = Path(manifest.get("paths", {}).get("data_dir", ""))
    if data_dir.exists():
        matches = list(data_dir.glob(f"*-{module}.json"))
        if matches:
            return matches[0]
    return None


def load_module(manifest: dict[str, Any], module: str) -> dict[str, Any] | None:
    path = artifact_data(manifest, module)
    if not path:
        return None
    data = load_json(path)
    data["_source_path"] = str(path)
    return data


def pillars(module: dict[str, Any] | None) -> dict[str, str]:
    if not module:
        return {}
    value = module.get("facts", {}).get("pillars", {})
    return value if isinstance(value, dict) else {}


def flow_pillars(module: dict[str, Any] | None) -> dict[str, str]:
    if not module:
        return {}
    value = module.get("facts", {}).get("flow", {}).get("pillars", {})
    return value if isinstance(value, dict) else {}


def current_dayun(module: dict[str, Any] | None) -> dict[str, Any]:
    if not module:
        return {}
    value = module.get("facts", {}).get("flow", {}).get("current_dayun", {})
    return value if isinstance(value, dict) else {}


def annual_flows(module: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not module:
        return []
    rows = module.get("facts", {}).get("flow", {}).get("annual_flows", [])
    return [row for row in rows if isinstance(row, dict)]


def relationship_items(a_label: str, b_label: str, a_pillars: dict[str, str], b_pillars: dict[str, str]) -> list[dict[str, str]]:
    a_items = named_items_from_pillars(a_pillars, PILLAR_LABELS, a_label)
    b_items = named_items_from_pillars(b_pillars, PILLAR_LABELS, b_label)
    return a_items + b_items


def bazi_cross(a_label: str, b_label: str, a_bazi: dict[str, Any] | None, b_bazi: dict[str, Any] | None) -> dict[str, Any]:
    a_pillars = pillars(a_bazi)
    b_pillars = pillars(b_bazi)
    items = relationship_items(a_label, b_label, a_pillars, b_pillars)
    required = {a_label, b_label}
    a_dayun = current_dayun(a_bazi)
    b_dayun = current_dayun(b_bazi)
    dayun_items = []
    if a_dayun.get("gan_zhi"):
        dayun_items += named_items_from_pillars({"dayun": a_dayun["gan_zhi"]}, {"dayun": f"{a_label}当前大运"}, f"{a_label}大运")
    if b_dayun.get("gan_zhi"):
        dayun_items += named_items_from_pillars({"dayun": b_dayun["gan_zhi"]}, {"dayun": f"{b_label}当前大运"}, f"{b_label}大运")
    flow_items = []
    a_flow = flow_pillars(a_bazi)
    b_flow = flow_pillars(b_bazi)
    if a_flow:
        flow_items += named_items_from_pillars(a_flow, FLOW_LABELS, f"{a_label}流盘")
    if b_flow:
        flow_items += named_items_from_pillars(b_flow, FLOW_LABELS, f"{b_label}流盘")
    return {
        "person_a_pillars": a_pillars,
        "person_b_pillars": b_pillars,
        "person_a_day_master": a_bazi.get("facts", {}).get("day_master") if a_bazi else {},
        "person_b_day_master": b_bazi.get("facts", {}).get("day_master") if b_bazi else {},
        "person_a_current_dayun": a_dayun,
        "person_b_current_dayun": b_dayun,
        "person_a_annual_flows": annual_flows(a_bazi),
        "person_b_annual_flows": annual_flows(b_bazi),
        "stems": stem_relationships(items, required),
        "branches": branch_relationships(items, required),
        "dayun_cross": {
            "stems": stem_relationships(items + dayun_items, {a_label, b_label}),
            "branches": branch_relationships(items + dayun_items, {a_label, b_label}),
        },
        "flow_cross": {
            "person_a_flow": a_flow,
            "person_b_flow": b_flow,
            "stems": stem_relationships(items + flow_items, {a_label, b_label}),
            "branches": branch_relationships(items + flow_items, {a_label, b_label}),
        },
    }


def placements(module: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not module:
        return []
    rows = module.get("facts", {}).get("placements", [])
    return [row for row in rows if isinstance(row, dict) and row.get("body")]


def longitude(row: dict[str, Any]) -> float | None:
    for key in ["absolute_longitude", "longitude"]:
        if isinstance(row.get(key), (int, float)):
            return float(row[key])
    return None


def angular_distance(a: float, b: float) -> float:
    delta = abs(a - b) % 360
    return min(delta, 360 - delta)


def western_cross(a_western: dict[str, Any] | None, b_western: dict[str, Any] | None) -> dict[str, Any]:
    rows = []
    for a in placements(a_western):
        a_lon = longitude(a)
        if a_lon is None:
            continue
        for b in placements(b_western):
            b_lon = longitude(b)
            if b_lon is None:
                continue
            dist = angular_distance(a_lon, b_lon)
            for name, exact, max_orb in WESTERN_ASPECTS:
                orb = abs(dist - exact)
                if orb <= max_orb:
                    rows.append({
                        "person_a_body": a.get("body"),
                        "person_a_sign": a.get("sign"),
                        "person_b_body": b.get("body"),
                        "person_b_sign": b.get("sign"),
                        "aspect": name,
                        "orb": round(orb, 2),
                    })
    rows.sort(key=lambda item: item["orb"])
    return {
        "cross_aspects": rows,
        "person_a_angles": (a_western or {}).get("facts", {}).get("houses", {}).get("angles", {}),
        "person_b_angles": (b_western or {}).get("facts", {}).get("houses", {}).get("angles", {}),
        "time_sensitive_note": "上升、下降、天顶、宫位和轴线叠合依赖出生时间；月亮星座较稳定时可以优先使用。",
    }


def ziwei_summary(module: dict[str, Any] | None) -> dict[str, Any]:
    if not module:
        return {}
    facts = module.get("facts", {})
    return {
        "soul_palace_branch": facts.get("soul_palace_branch"),
        "body_palace_branch": facts.get("body_palace_branch"),
        "current_decadal": facts.get("current_decadal"),
        "year_mutagens": facts.get("year_mutagens", []),
        "relationship_palace": next(
            (item for item in facts.get("palaces", []) if isinstance(item, dict) and item.get("name") == "夫妻宫"),
            {},
        ),
    }


def mbti_summary(module: dict[str, Any] | None) -> dict[str, Any]:
    if not module:
        return {}
    return module.get("facts", {})


def extended_mbti_summary(type_text: str | None) -> dict[str, Any]:
    if not type_text:
        return {}
    value = type_text.strip().upper()
    match = re.fullmatch(r"([EI][SN][TF][JP])(?:-([AT]))?", value)
    if not match:
        raise SystemExit(f"Invalid MBTI type: {type_text}; expected ENTP, ENTP-A, ISFP-T, etc.")
    core, variant = match.groups()
    axes = {
        "energy": "外向 E" if core[0] == "E" else "内向 I",
        "information": "实感 S" if core[1] == "S" else "直觉 N",
        "decision": "思考 T" if core[2] == "T" else "情感 F",
        "lifestyle": "判断 J" if core[3] == "J" else "知觉 P",
    }
    variant_text = ""
    if variant == "A":
        variant_text = "Assertive A：更容易外显自信、恢复较快、表达更直接。"
    elif variant == "T":
        variant_text = "Turbulent T：更容易自我校准、在意反馈、情绪波动和细节感受更明显。"
    return {
        "type": value,
        "core_type": core,
        "variant": variant or "",
        "axes": axes,
        "variant_text": variant_text,
        "evidence_status": "user_provided_recent_test",
        "usage_boundary": "MBTI 只作行为语言和沟通偏好，不作为命理证据。",
    }


def bazi_auxiliary(module: dict[str, Any] | None) -> dict[str, Any]:
    if not module:
        return {}
    facts = module.get("facts", {})
    details = facts.get("details", {}) if isinstance(facts.get("details"), dict) else {}
    return {
        "nayin_by_pillar": {key: row.get("nayin") for key, row in details.items() if isinstance(row, dict)},
        "xun_kong_by_pillar": {key: row.get("xun_kong") for key, row in details.items() if isinstance(row, dict)},
        "twelve_growth": facts.get("twelve_growth", {}),
        "ten_gods_combined": facts.get("profiles", {}).get("ten_gods", {}).get("combined", {}),
        "elements_stems_plus_hidden": facts.get("profiles", {}).get("elements", {}).get("stems_plus_hidden", {}),
        "auxiliary_rule": "纳音、旬空、十二长生和神煞类信息只作辅助象意，不覆盖日主、月令、十神、合冲刑害、大运流年和现实校准。",
    }


def bazi_pattern_audit(module: dict[str, Any] | None) -> dict[str, Any]:
    if not module:
        return {}
    facts = module.get("facts", {})
    details = facts.get("details", {}) if isinstance(facts.get("details"), dict) else {}
    month = details.get("month", {}) if isinstance(details.get("month"), dict) else {}
    day = details.get("day", {}) if isinstance(details.get("day"), dict) else {}
    return {
        "day_master": facts.get("day_master"),
        "month_pillar": month.get("pillar"),
        "month_stem_ten_god": month.get("ten_god_gan"),
        "month_hidden_stems": month.get("hidden_gan", []),
        "month_hidden_ten_gods": month.get("ten_god_zhi", []),
        "day_branch_hidden_stems": day.get("hidden_gan", []),
        "day_branch_hidden_ten_gods": day.get("ten_god_zhi", []),
        "combined_ten_gods": facts.get("profiles", {}).get("ten_gods", {}).get("combined", {}),
        "combined_elements": facts.get("profiles", {}).get("elements", {}).get("stems_plus_hidden", {}),
        "current_dayun": current_dayun(module),
        "audit_rule": "格局核对先看月令、透干、藏干、十神组合与大运；只作为结构判断，不单凭格局名断事。",
    }


def career_overlap(
    a_label: str,
    b_label: str,
    a_bazi: dict[str, Any] | None,
    b_bazi: dict[str, Any] | None,
    a_ziwei: dict[str, Any] | None,
    b_ziwei: dict[str, Any] | None,
    a_western: dict[str, Any] | None,
    b_western: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "person_a": {
            "label": a_label,
            "current_dayun": current_dayun(a_bazi),
            "ten_gods_combined": bazi_auxiliary(a_bazi).get("ten_gods_combined", {}),
            "elements": bazi_auxiliary(a_bazi).get("elements_stems_plus_hidden", {}),
            "ziwei_current_decadal": ziwei_summary(a_ziwei).get("current_decadal"),
            "western_public_language": [
                row for row in placements(a_western)
                if row.get("body") in {"太阳", "水星", "金星", "火星", "土星", "天顶"}
            ],
        },
        "person_b": {
            "label": b_label,
            "current_dayun": current_dayun(b_bazi),
            "ten_gods_combined": bazi_auxiliary(b_bazi).get("ten_gods_combined", {}),
            "elements": bazi_auxiliary(b_bazi).get("elements_stems_plus_hidden", {}),
            "ziwei_current_decadal": ziwei_summary(b_ziwei).get("current_decadal"),
            "western_public_language": [
                row for row in placements(b_western)
                if row.get("body") in {"太阳", "水星", "金星", "火星", "土星", "天顶"}
            ],
        },
        "boundary": "事业交集只写合作可能、资源互补、角色差异和现实风险；不得断定两人一定共同创业、共事或发生利益绑定。",
    }


def western_body_subset(module: dict[str, Any] | None, bodies: set[str]) -> list[dict[str, Any]]:
    return [row for row in placements(module) if row.get("body") in bodies]


def western_aspect_subset(western_cross_facts: dict[str, Any], bodies: set[str], limit: int = 8) -> list[dict[str, Any]]:
    rows = []
    for row in western_cross_facts.get("cross_aspects", []):
        if row.get("person_a_body") in bodies or row.get("person_b_body") in bodies:
            rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def relation_summary(bazi_cross_facts: dict[str, Any], limit: int = 8) -> list[str]:
    rows = []
    for key in ["stems", "branches"]:
        for item in bazi_cross_facts.get(key, []):
            rows.append(render_relation_item(item))
            if len(rows) >= limit:
                return rows
    return rows


def life_domain_overlaps(
    a_label: str,
    b_label: str,
    a_bazi: dict[str, Any] | None,
    b_bazi: dict[str, Any] | None,
    a_ziwei: dict[str, Any] | None,
    b_ziwei: dict[str, Any] | None,
    a_western: dict[str, Any] | None,
    b_western: dict[str, Any] | None,
    bazi_cross_facts: dict[str, Any],
    western_cross_facts: dict[str, Any],
    relationship_status: str,
) -> dict[str, Any]:
    """Collect domain-specific anchors without turning them into real-world events."""

    relationship_mode = relationship_mode_from_status(relationship_status)

    domain_specs = {
        "career": {
            "label": "事业/合作",
            "western_bodies": {"太阳", "水星", "火星", "土星", "天顶"},
            "allowed": ["合作可能", "角色互补", "资源互相启发", "沟通分工", "现实边界"],
            "do_not_infer": ["一定共事", "共同创业", "利益绑定", "职业成败"],
            "boundary": "只写合作可能、角色差异和资源互补，不断定两人一定共事或共同创业。",
        },
        "family_life": {
            "label": "家庭/生活承载",
            "western_bodies": {"月亮", "金星", "土星", "天底"},
            "allowed": ["生活习惯", "照顾方式", "家庭感", "居住想象", "现实支持"],
            "do_not_infer": ["双方家庭态度", "同居安排", "婚姻时间", "家庭冲突史"],
            "boundary": "只写家庭感、生活承载和边界，不臆测双方家庭态度或婚姻安排。",
        },
        "wealth_resources": {
            "label": "财富/资源投入",
            "western_bodies": {"金星", "木星", "土星", "水星"},
            "allowed": ["见面成本", "时间投入", "共同计划", "钱账边界", "资源互补"],
            "do_not_infer": ["投资建议", "具体金额", "谁该付钱", "财务绑定"],
            "boundary": "只写资源分配、投入感和钱账边界，不给投资建议，不推具体金额。",
        },
        "health_energy": {
            "label": "健康/精力照顾",
            "western_bodies": {"月亮", "火星", "土星"},
            "allowed": ["作息节奏", "压力恢复", "情绪消耗", "陪伴方式", "精力边界"],
            "do_not_infer": ["医疗诊断", "疾病判断", "治疗建议", "寿命健康事件"],
            "boundary": "只写精力、压力、作息和恢复，不做医疗诊断。",
        },
        "intimacy_private": {
            "label": "亲近/私密边界",
            "western_bodies": {"金星", "火星", "月亮"},
            "allowed": relationship_mode["allowed_private_language"],
            "do_not_infer": relationship_mode["forbidden_private_language"],
            "boundary": relationship_mode["writing_boundary"],
        },
    }
    aux_a = bazi_auxiliary(a_bazi)
    aux_b = bazi_auxiliary(b_bazi)
    ziwei_a = ziwei_summary(a_ziwei)
    ziwei_b = ziwei_summary(b_ziwei)
    common_bazi_relations = relation_summary(bazi_cross_facts)
    domains: dict[str, Any] = {}
    for key, spec in domain_specs.items():
        bodies = spec["western_bodies"]
        domains[key] = {
            "label": spec["label"],
            "person_a": {
                "label": a_label,
                "current_dayun": current_dayun(a_bazi),
                "ten_gods_combined": aux_a.get("ten_gods_combined", {}),
                "elements": aux_a.get("elements_stems_plus_hidden", {}),
                "ziwei_current_decadal": ziwei_a.get("current_decadal"),
                "ziwei_relationship_palace": ziwei_a.get("relationship_palace"),
                "western_bodies": western_body_subset(a_western, bodies),
            },
            "person_b": {
                "label": b_label,
                "current_dayun": current_dayun(b_bazi),
                "ten_gods_combined": aux_b.get("ten_gods_combined", {}),
                "elements": aux_b.get("elements_stems_plus_hidden", {}),
                "ziwei_current_decadal": ziwei_b.get("current_decadal"),
                "ziwei_relationship_palace": ziwei_b.get("relationship_palace"),
                "western_bodies": western_body_subset(b_western, bodies),
            },
            "bazi_cross_anchors": common_bazi_relations,
            "western_cross_anchors": western_aspect_subset(western_cross_facts, bodies),
            "allowed_writing": spec["allowed"],
            "do_not_infer": spec["do_not_infer"],
            "writing_boundary": spec["boundary"],
        }
    return domains


def annual_intersections(
    a_label: str,
    b_label: str,
    a_bazi: dict[str, Any] | None,
    b_bazi: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build year-by-year relationship triggers from each person's annual flows."""

    a_natal = named_items_from_pillars(pillars(a_bazi), PILLAR_LABELS, a_label)
    b_natal = named_items_from_pillars(pillars(b_bazi), PILLAR_LABELS, b_label)
    a_by_year = {int(row["year"]): row for row in annual_flows(a_bazi) if row.get("year") is not None}
    b_by_year = {int(row["year"]): row for row in annual_flows(b_bazi) if row.get("year") is not None}
    rows: list[dict[str, Any]] = []
    for year in sorted(set(a_by_year).intersection(b_by_year)):
        a_row = a_by_year[year]
        b_row = b_by_year[year]
        a_flow_group = f"{a_label}流年"
        b_flow_group = f"{b_label}流年"
        a_dayun_group = f"{a_label}当年大运"
        b_dayun_group = f"{b_label}当年大运"
        a_flow_items = named_items_from_pillars(
            {"year": str(a_row.get("pillar", ""))},
            {"year": f"{a_label}流年"},
            a_flow_group,
        )
        b_flow_items = named_items_from_pillars(
            {"year": str(b_row.get("pillar", ""))},
            {"year": f"{b_label}流年"},
            b_flow_group,
        )
        a_dayun_items = named_items_from_pillars(
            {"dayun": str(a_row.get("dayun", ""))},
            {"dayun": f"{a_label}当年大运"},
            a_dayun_group,
        )
        b_dayun_items = named_items_from_pillars(
            {"dayun": str(b_row.get("dayun", ""))},
            {"dayun": f"{b_label}当年大运"},
            b_dayun_group,
        )
        flow_items = a_flow_items + b_flow_items
        rows.append(
            {
                "year": year,
                "person_a_flow": {
                    "pillar": a_row.get("pillar"),
                    "dayun": a_row.get("dayun"),
                    "age": a_row.get("age"),
                },
                "person_b_flow": {
                    "pillar": b_row.get("pillar"),
                    "dayun": b_row.get("dayun"),
                    "age": b_row.get("age"),
                },
                "flow_to_flow": {
                    "stems": stem_relationships(flow_items, {a_flow_group, b_flow_group}),
                    "branches": branch_relationships(flow_items, {a_flow_group, b_flow_group}),
                },
                "person_a_flow_to_person_b_natal": {
                    "stems": stem_relationships(a_flow_items + b_natal, {a_flow_group, b_label}),
                    "branches": branch_relationships(a_flow_items + b_natal, {a_flow_group, b_label}),
                },
                "person_b_flow_to_person_a_natal": {
                    "stems": stem_relationships(b_flow_items + a_natal, {b_flow_group, a_label}),
                    "branches": branch_relationships(b_flow_items + a_natal, {b_flow_group, a_label}),
                },
                "dayun_to_dayun": {
                    "stems": stem_relationships(a_dayun_items + b_dayun_items, {a_dayun_group, b_dayun_group}),
                    "branches": branch_relationships(a_dayun_items + b_dayun_items, {a_dayun_group, b_dayun_group}),
                },
                "writing_boundary": "年份交叉只说明同一年双方各自被触发的命理结构；不能反推两人一定在该年发生现实交集。",
            }
        )
    return rows


def render_relation_item(item: dict[str, Any]) -> str:
    bits = []
    for part in item.get("items", []):
        bits.append(f"{part.get('group')}{part.get('label')}({part.get('pillar')})")
    return f"{item.get('relation')}：" + " / ".join(bits)


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return []
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join("" if value is None else str(value) for value in row) + " |")
    return lines


def render_markdown(facts: dict[str, Any]) -> str:
    rel = facts["relationship_context"]
    bazi = facts["bazi_cross"]
    western = facts["western_cross"]
    lines = [
        "# 合盘事实复查档案",
        "",
        "这份文件只归档可复查事实，供合盘写作引用；它不是读者版解读。",
        "",
        f"- 对象：{facts['people']['person_a_label']} / {facts['people']['person_b_label']}",
        f"- 已知现实关系：{rel['relationship_status']}，{rel['distance_status']}",
        f"- 关系模式：{facts.get('relationship_mode', {}).get('category', '')}",
        f"- 亲近/私密写作边界：{facts.get('relationship_mode', {}).get('writing_boundary', '')}",
        f"- 现实边界：{rel['known_boundary']}",
        "",
        "## 八字交叉事实",
        "",
        f"- {facts['people']['person_a_label']}四柱：{' / '.join(bazi['person_a_pillars'].values())}",
        f"- {facts['people']['person_b_label']}四柱：{' / '.join(bazi['person_b_pillars'].values())}",
        f"- {facts['people']['person_a_label']}当前大运：{bazi['person_a_current_dayun'].get('gan_zhi')}（{bazi['person_a_current_dayun'].get('start_year')}-{bazi['person_a_current_dayun'].get('end_year')}）",
        f"- {facts['people']['person_b_label']}当前大运：{bazi['person_b_current_dayun'].get('gan_zhi')}（{bazi['person_b_current_dayun'].get('start_year')}-{bazi['person_b_current_dayun'].get('end_year')}）",
        "",
        "### 天干关系",
        "",
    ]
    lines.extend([f"- {render_relation_item(item)}" for item in bazi["stems"]] or ["- 无交叉天干合冲。"])
    lines.extend(["", "### 地支关系", ""])
    lines.extend([f"- {render_relation_item(item)}" for item in bazi["branches"]] or ["- 无交叉地支关系。"])
    lines.extend(["", "### 流年序列", ""])
    rows = []
    by_year: dict[int, dict[str, Any]] = {}
    for row in bazi["person_a_annual_flows"]:
        by_year.setdefault(int(row["year"]), {})["person_a"] = row
    for row in bazi["person_b_annual_flows"]:
        by_year.setdefault(int(row["year"]), {})["person_b"] = row
    for year in sorted(by_year):
        rows.append([
            year,
            by_year[year].get("person_a", {}).get("pillar"),
            by_year[year].get("person_a", {}).get("dayun"),
            by_year[year].get("person_b", {}).get("pillar"),
            by_year[year].get("person_b", {}).get("dayun"),
        ])
    person_a_label = facts["people"]["person_a_label"]
    person_b_label = facts["people"]["person_b_label"]
    lines.extend(
        table(
            ["年份", f"{person_a_label}流年", f"{person_a_label}大运", f"{person_b_label}流年", f"{person_b_label}大运"],
            rows,
        )
    )
    lines.extend(["", "### 年份交叉触发", ""])
    annual = facts.get("annual_intersections", [])
    if annual:
        for item in annual:
            flow_branches = [render_relation_item(row) for row in item.get("flow_to_flow", {}).get("branches", [])]
            a_to_b = [
                render_relation_item(row)
                for row in item.get("person_a_flow_to_person_b_natal", {}).get("branches", [])
            ]
            b_to_a = [
                render_relation_item(row)
                for row in item.get("person_b_flow_to_person_a_natal", {}).get("branches", [])
            ]
            lines.append(
                f"- {item.get('year')}："
                f"{facts['people']['person_a_label']}流年 {item.get('person_a_flow', {}).get('pillar')}，"
                f"{facts['people']['person_b_label']}流年 {item.get('person_b_flow', {}).get('pillar')}；"
                f"流年互触：{'；'.join(flow_branches) if flow_branches else '无明显地支交叉'}；"
                f"{facts['people']['person_a_label']}流年触发{facts['people']['person_b_label']}本命：{'；'.join(a_to_b) if a_to_b else '无明显地支交叉'}；"
                f"{facts['people']['person_b_label']}流年触发{facts['people']['person_a_label']}本命：{'；'.join(b_to_a) if b_to_a else '无明显地支交叉'}。"
            )
    else:
        lines.append("- 当前两边结构化流年没有可并列的共同年份。")
    lines.append("- 写作边界：年份交叉只说明同一年双方各自被触发的命理结构；不能反推两人一定在该年发生现实交集。")
    lines.extend(["", "## 西占交叉事实", ""])
    for item in western["cross_aspects"][:20]:
        lines.append(
            f"- {item['person_a_body']}{item['person_a_sign']} {item['aspect']} "
            f"{item['person_b_body']}{item['person_b_sign']}，orb {item['orb']}"
        )
    lines.extend(["", f"- 时间敏感提示：{western['time_sensitive_note']}", ""])
    lines.extend(["## 紫微阶段事实", ""])
    for key, label in [("person_a", facts["people"]["person_a_label"]), ("person_b", facts["people"]["person_b_label"])]:
        z = facts["ziwei"][key]
        decadal = z.get("current_decadal") or {}
        lines.append(f"- {label}当前大限：{decadal.get('name')}，主星：{'、'.join(decadal.get('major_stars') or [])}")
        lines.append(f"- {label}夫妻宫：{z.get('relationship_palace')}")
    lines.extend(["", "## MBTI 行为语言", ""])
    for key, label in [("person_a", facts["people"]["person_a_label"]), ("person_b", facts["people"]["person_b_label"])]:
        m = facts.get("mbti", {}).get(key) or {}
        if m:
            lines.append(f"- {label}：{m.get('type')}；{m.get('variant_text') or m.get('usage_boundary', '')}")
    lines.extend(["", "## 八字辅助象意", ""])
    for key, label in [("person_a", facts["people"]["person_a_label"]), ("person_b", facts["people"]["person_b_label"])]:
        aux = facts.get("bazi_auxiliary", {}).get(key) or {}
        lines.append(f"- {label}纳音：{aux.get('nayin_by_pillar')}")
        lines.append(f"- {label}旬空：{aux.get('xun_kong_by_pillar')}")
        lines.append(f"- {label}十二长生：{aux.get('twelve_growth')}")
    lines.extend(["", "## 八字格局核对事实", ""])
    for key, label in [("person_a", facts["people"]["person_a_label"]), ("person_b", facts["people"]["person_b_label"])]:
        audit = facts.get("bazi_pattern_audit", {}).get(key) or {}
        lines.append(
            f"- {label}月柱：{audit.get('month_pillar')}，"
            f"月干十神：{audit.get('month_stem_ten_god')}，"
            f"月支藏干十神：{audit.get('month_hidden_ten_gods')}"
        )
        lines.append(f"- {label}十神合计：{audit.get('combined_ten_gods')}，当前大运：{audit.get('current_dayun')}")
    lines.extend(["", "## 事业/合作交集事实", ""])
    lines.append(f"- 写作边界：{facts.get('career_overlap', {}).get('boundary')}")
    for key in ["person_a", "person_b"]:
        item = facts.get("career_overlap", {}).get(key) or {}
        if item:
            lines.append(f"- {item.get('label')}当前大运：{item.get('current_dayun')}")
            lines.append(f"- {item.get('label')}十神合计：{item.get('ten_gods_combined')}")
    lines.extend(["", "## 现实专题交集事实", ""])
    domains = facts.get("relationship_life_domains", {})
    if domains:
        for key, item in domains.items():
            lines.append(f"### {item.get('label') or key}")
            lines.append(f"- 可写范围：{'、'.join(item.get('allowed_writing', []))}")
            lines.append(f"- 不可推断：{'、'.join(item.get('do_not_infer', []))}")
            lines.append(f"- 写作边界：{item.get('writing_boundary')}")
            anchors = item.get("bazi_cross_anchors", [])
            if anchors:
                lines.append(f"- 八字交叉锚点：{'；'.join(anchors[:6])}")
            western_anchors = item.get("western_cross_anchors", [])
            if western_anchors:
                rendered = [
                    f"{row.get('person_a_body')}{row.get('aspect')}{row.get('person_b_body')} orb {row.get('orb')}"
                    for row in western_anchors[:5]
                ]
                lines.append(f"- 西占交叉锚点：{'；'.join(rendered)}")
            for person_key in ["person_a", "person_b"]:
                person = item.get(person_key, {})
                if person:
                    lines.append(
                        f"- {person.get('label')}专题锚点："
                        f"大运 {person.get('current_dayun')}；"
                        f"紫微大限 {person.get('ziwei_current_decadal')}；"
                        f"西占相关星体 {person.get('western_bodies')}"
                    )
            lines.append("")
    else:
        lines.append("- 当前 facts 未生成现实专题交集。")
    lines.extend(["", "## 写作约束", ""])
    for item in facts["writing_contract"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def update_manifest(manifest_path: Path, output_json: Path, output_md: Path, facts: dict[str, Any]) -> None:
    manifest = load_json(manifest_path)
    artifacts = manifest.setdefault("artifacts", {})
    data = artifacts.setdefault("data", {})
    if isinstance(data, dict):
        data["relationship"] = str(output_json)
    artifacts["relationship_fact_archive_markdown"] = str(output_md)
    existing_context = manifest.get("relationship_context", {})
    if not isinstance(existing_context, dict):
        existing_context = {}
    merged_context = {**existing_context, **facts["relationship_context"]}
    manifest["relationship_context"] = merged_context
    manifest["people"] = facts["people"]
    manifest["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    relationship_manifest = load_json(manifest_path)
    run_dir = Path(relationship_manifest["paths"]["run_dir"])
    case_id = relationship_manifest["case_id"]
    output_json = Path(args.output_json).resolve() if args.output_json else run_dir / "data" / f"{case_id}-relationship.json"
    output_md = Path(args.output_md).resolve() if args.output_md else run_dir / "data" / f"{case_id}-relationship-facts.md"

    a_manifest = load_json(Path(args.person_a_manifest).resolve())
    b_manifest = load_json(Path(args.person_b_manifest).resolve())
    a = {name: load_module(a_manifest, name) for name in ["bazi", "ziwei", "western", "mbti", "time_sensitivity"]}
    b = {name: load_module(b_manifest, name) for name in ["bazi", "ziwei", "western", "mbti", "time_sensitivity"]}
    bazi_cross_facts = bazi_cross(args.person_a_label, args.person_b_label, a["bazi"], b["bazi"])
    western_cross_facts = western_cross(a["western"], b["western"])
    relationship_mode = relationship_mode_from_status(args.relationship_status)

    facts = {
        "schema_version": "0.1.0",
        "module": "relationship",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "people": {
            "person_a_label": args.person_a_label,
            "person_b_label": args.person_b_label,
            "person_a_case_id": a_manifest.get("case_id"),
            "person_b_case_id": b_manifest.get("case_id"),
        },
        "relationship_context": {
            "person_a_label": args.person_a_label,
            "person_b_label": args.person_b_label,
            "person_a_mbti_type": args.person_a_mbti_type or "",
            "person_b_mbti_type": args.person_b_mbti_type or "",
            "relationship_status": args.relationship_status,
            "distance_status": args.distance_status,
            "relationship_mode": relationship_mode,
            "known_boundary": "只使用已知现实关系状态与距离状态；不预设线下见面频率、同居、婚姻、家庭介入、冲突史或稳定程度。",
            "forbidden_reality_assumptions": ["线下见面频率", "共同生活", "婚姻安排", "家庭介入", "冲突史", "稳定程度"],
        },
        "relationship_mode": relationship_mode,
        "source_manifests": {
            "person_a": str(Path(args.person_a_manifest).resolve()),
            "person_b": str(Path(args.person_b_manifest).resolve()),
        },
        "source_modules": {
            "person_a": {key: value.get("_source_path") for key, value in a.items() if value},
            "person_b": {key: value.get("_source_path") for key, value in b.items() if value},
        },
        "bazi_cross": bazi_cross_facts,
        "western_cross": western_cross_facts,
        "ziwei": {
            "person_a": ziwei_summary(a["ziwei"]),
            "person_b": ziwei_summary(b["ziwei"]),
        },
        "mbti": {
            "person_a": extended_mbti_summary(args.person_a_mbti_type) or mbti_summary(a["mbti"]),
            "person_b": extended_mbti_summary(args.person_b_mbti_type) or mbti_summary(b["mbti"]),
        },
        "bazi_auxiliary": {
            "person_a": bazi_auxiliary(a["bazi"]),
            "person_b": bazi_auxiliary(b["bazi"]),
        },
        "bazi_pattern_audit": {
            "person_a": bazi_pattern_audit(a["bazi"]),
            "person_b": bazi_pattern_audit(b["bazi"]),
        },
        "career_overlap": {
            **career_overlap(
                args.person_a_label,
                args.person_b_label,
                a["bazi"],
                b["bazi"],
                a["ziwei"],
                b["ziwei"],
                a["western"],
                b["western"],
            )
        },
        "relationship_life_domains": life_domain_overlaps(
            args.person_a_label,
            args.person_b_label,
            a["bazi"],
            b["bazi"],
            a["ziwei"],
            b["ziwei"],
            a["western"],
            b["western"],
            bazi_cross_facts,
            western_cross_facts,
            args.relationship_status,
        ),
        "annual_intersections": annual_intersections(args.person_a_label, args.person_b_label, a["bazi"], b["bazi"]),
        "template_contract": {
            "relationship_rich_outline": "22-section v4",
            "required_expansions": ["格局核对", "神煞与辅助象意", "亲近/私密边界", "事业/合作交集", "家庭与生活承载", "财富资源边界", "健康精力", "关系形态变化", "MBTI 行为链条"],
        },
        "time_sensitivity": {
            "person_a": a["time_sensitivity"],
            "person_b": b["time_sensitivity"],
            "relationship_rule": "涉及宫位、轴线、上升下降、小时柱变化时必须写成时间敏感项；稳定星座、四柱日柱和大运可作为主锚点。",
        },
        "writing_contract": [
            f"读者正文使用第三人称：{args.person_a_label}、{args.person_b_label}、两个人、这段关系。",
            f"不得使用“你和{args.person_b_label}”或“你们”作为主叙述。",
            f"现实输入只限{args.relationship_status}与{args.distance_status}；其他现实细节必须写成校准问题。",
            "先写牵引、互补与可经营价值，再写张力和误读；身体吸引语言必须服从 relationship_mode。",
            "张力不写成劝退结论，必须给出可观察表现和可经营落点。",
            "神煞、纳音、旬空、十二长生只作辅助象意，不覆盖主结构。",
            "事业交集只写合作可能、资源互补和边界，不断定一定共事或利益绑定。",
            "正文不得暴露脚本路径、JSON、命令、截图处理过程或生成过程。",
        ],
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(facts), encoding="utf-8")
    update_manifest(manifest_path, output_json, output_md, facts)
    print(json.dumps({"passed": True, "json": str(output_json), "markdown": str(output_md)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
