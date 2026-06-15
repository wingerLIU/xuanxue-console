#!/usr/bin/env python3
"""Xuanxue Console: deterministic chart helpers for a combined metaphysics skill."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import math
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.2.0"

try:
    from xuanxue_longform import render_longform_markdown, report_modules
    from xuanxue_western import (
        WESTERN_BODIES,
        WESTERN_SIGN_META,
        WESTERN_SIGNS,
        ecliptic_longitude,
        western_angles_and_houses,
        western_aspects,
        western_moon_phase,
        western_retrogrades,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from xuanxue_longform import render_longform_markdown, report_modules
    from xuanxue_western import (
        WESTERN_BODIES,
        WESTERN_SIGN_META,
        WESTERN_SIGNS,
        ecliptic_longitude,
        western_angles_and_houses,
        western_aspects,
        western_moon_phase,
        western_retrogrades,
    )


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


configure_stdio()

GAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
GAN_POLARITY = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
}
BRANCH_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}
WUXING_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
PILLAR_LABELS = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}
FLOW_LABELS = {"year": "流年", "month": "流月", "day": "流日"}
STEM_COMBOS = {
    frozenset(("甲", "己")): "甲己合土",
    frozenset(("乙", "庚")): "乙庚合金",
    frozenset(("丙", "辛")): "丙辛合水",
    frozenset(("丁", "壬")): "丁壬合木",
    frozenset(("戊", "癸")): "戊癸合火",
}
STEM_CLASHES = {
    frozenset(("甲", "庚")): "甲庚冲",
    frozenset(("乙", "辛")): "乙辛冲",
    frozenset(("丙", "壬")): "丙壬冲",
    frozenset(("丁", "癸")): "丁癸冲",
}
BRANCH_PAIR_RELATIONS: dict[frozenset[str], list[str]] = {}
for a, b, relation in [
    ("子", "丑", "子丑六合土"),
    ("寅", "亥", "寅亥六合木"),
    ("卯", "戌", "卯戌六合火"),
    ("辰", "酉", "辰酉六合金"),
    ("巳", "申", "巳申六合水"),
    ("午", "未", "午未六合土"),
    ("子", "午", "子午冲"),
    ("丑", "未", "丑未冲"),
    ("寅", "申", "寅申冲"),
    ("卯", "酉", "卯酉冲"),
    ("辰", "戌", "辰戌冲"),
    ("巳", "亥", "巳亥冲"),
    ("子", "未", "子未害"),
    ("丑", "午", "丑午害"),
    ("寅", "巳", "寅巳害"),
    ("卯", "辰", "卯辰害"),
    ("申", "亥", "申亥害"),
    ("酉", "戌", "酉戌害"),
    ("子", "酉", "子酉破"),
    ("卯", "午", "卯午破"),
    ("辰", "丑", "辰丑破"),
    ("未", "戌", "未戌破"),
    ("寅", "亥", "寅亥破"),
    ("巳", "申", "巳申破"),
    ("子", "卯", "子卯刑"),
    ("丑", "戌", "丑戌刑"),
    ("丑", "未", "丑未刑"),
    ("寅", "巳", "寅巳刑"),
    ("寅", "申", "寅申刑"),
    ("巳", "申", "巳申刑"),
    ("戌", "未", "戌未刑"),
]:
    BRANCH_PAIR_RELATIONS.setdefault(frozenset((a, b)), []).append(relation)
BRANCH_SELF_PUNISH = {"辰": "辰辰自刑", "午": "午午自刑", "酉": "酉酉自刑", "亥": "亥亥自刑"}
BRANCH_TRINES = [
    ({"申", "子", "辰"}, "申子辰三合水局"),
    ({"亥", "卯", "未"}, "亥卯未三合木局"),
    ({"寅", "午", "戌"}, "寅午戌三合火局"),
    ({"巳", "酉", "丑"}, "巳酉丑三合金局"),
]
BRANCH_CN = {
    "ziEarthly": "子", "chouEarthly": "丑", "yinEarthly": "寅",
    "maoEarthly": "卯", "chenEarthly": "辰", "siEarthly": "巳",
    "wuEarthly": "午", "weiEarthly": "未", "shenEarthly": "申",
    "youEarthly": "酉", "xuEarthly": "戌", "haiEarthly": "亥",
}
STEM_CN = {
    "jiaHeavenly": "甲", "yiHeavenly": "乙", "bingHeavenly": "丙",
    "dingHeavenly": "丁", "wuHeavenly": "戊", "jiHeavenly": "己",
    "gengHeavenly": "庚", "xinHeavenly": "辛", "renHeavenly": "壬",
    "guiHeavenly": "癸",
}
FIVE_ELEMENTS_CN = {
    "water2": "水二局", "wood3": "木三局", "metal4": "金四局",
    "earth5": "土五局", "fire6": "火六局",
}
TRIGRAM_BITS = {
    (1, 1, 1): ("乾", "天"),
    (0, 1, 1): ("兑", "泽"),
    (1, 0, 1): ("离", "火"),
    (0, 0, 1): ("震", "雷"),
    (1, 1, 0): ("巽", "风"),
    (0, 1, 0): ("坎", "水"),
    (1, 0, 0): ("艮", "山"),
    (0, 0, 0): ("坤", "地"),
}
TRIGRAM_ELEMENTS = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}
NA_JIA = {
    "乾": [("甲", "子"), ("甲", "寅"), ("甲", "辰"), ("壬", "午"), ("壬", "申"), ("壬", "戌")],
    "坤": [("乙", "未"), ("乙", "巳"), ("乙", "卯"), ("癸", "丑"), ("癸", "亥"), ("癸", "酉")],
    "震": [("庚", "子"), ("庚", "寅"), ("庚", "辰"), ("庚", "午"), ("庚", "申"), ("庚", "戌")],
    "巽": [("辛", "丑"), ("辛", "亥"), ("辛", "酉"), ("辛", "未"), ("辛", "巳"), ("辛", "卯")],
    "坎": [("戊", "寅"), ("戊", "辰"), ("戊", "午"), ("戊", "申"), ("戊", "戌"), ("戊", "子")],
    "离": [("己", "卯"), ("己", "丑"), ("己", "亥"), ("己", "酉"), ("己", "未"), ("己", "巳")],
    "艮": [("丙", "辰"), ("丙", "午"), ("丙", "申"), ("丙", "戌"), ("丙", "子"), ("丙", "寅")],
    "兑": [("丁", "巳"), ("丁", "卯"), ("丁", "丑"), ("丁", "亥"), ("丁", "酉"), ("丁", "未")],
}
SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
SIX_SPIRIT_START = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5}
XIAO_LIUREN_STATES = ["大安", "留连", "速喜", "赤口", "小吉", "空亡"]
XIAO_LIUREN_HINTS = {
    "大安": "稳定、守成、宜静不宜急。",
    "留连": "拖延、反复、信息未定。",
    "速喜": "进展快、消息来、适合主动推进。",
    "赤口": "口舌、争执、合同沟通需谨慎。",
    "小吉": "小有助力，可试探推进。",
    "空亡": "落空、虚耗、先查证再行动。",
}
CHANGSHENG_STATES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]
CHANGSHENG_START_DIRECTION = {
    "甲": ("亥", 1),
    "乙": ("午", -1),
    "丙": ("寅", 1),
    "丁": ("酉", -1),
    "戊": ("寅", 1),
    "己": ("酉", -1),
    "庚": ("巳", 1),
    "辛": ("子", -1),
    "壬": ("申", 1),
    "癸": ("卯", -1),
}


def dump(obj: dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def changsheng_state(stem: str, branch: str) -> str:
    if stem not in CHANGSHENG_START_DIRECTION or branch not in BRANCHES:
        return ""
    start, direction = CHANGSHENG_START_DIRECTION[stem]
    start_index = BRANCHES.index(start)
    branch_index = BRANCHES.index(branch)
    state_index = ((branch_index - start_index) * direction) % 12
    return CHANGSHENG_STATES[state_index]


def pillar_changsheng(pillar_details: dict[str, Any], stem: str) -> dict[str, str]:
    return {
        key: changsheng_state(stem, row.get("zhi", ""))
        for key, row in pillar_details.items()
    }


def self_sitting_changsheng(pillar_details: dict[str, Any]) -> dict[str, str]:
    return {
        key: changsheng_state(row.get("gan", ""), row.get("zhi", ""))
        for key, row in pillar_details.items()
    }


def branch_from_pillar(pillar: str | None) -> str:
    if not pillar or len(pillar) < 2:
        return ""
    return pillar[1]


def named_items_from_pillars(pillars: dict[str, str], labels: dict[str, str], group: str) -> list[dict[str, str]]:
    rows = []
    for key, pillar in pillars.items():
        if not pillar or len(pillar) < 2:
            continue
        rows.append({
            "key": key,
            "label": labels.get(key, key),
            "group": group,
            "pillar": pillar,
            "gan": pillar[0],
            "zhi": pillar[1],
        })
    return rows


def relation_item_view(item: dict[str, str], attr: str) -> dict[str, str]:
    return {
        "label": item["label"],
        "group": item["group"],
        "pillar": item["pillar"],
        attr: item[attr],
    }


def has_required_groups(items: list[dict[str, str]], required_groups: set[str] | None) -> bool:
    if not required_groups:
        return True
    groups = {item["group"] for item in items}
    return required_groups <= groups


def stem_relationships(items: list[dict[str, str]], required_groups: set[str] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, first in enumerate(items):
        for second in items[index + 1:]:
            involved = [first, second]
            if not has_required_groups(involved, required_groups):
                continue
            key = frozenset((first["gan"], second["gan"]))
            for relation_map, kind in [(STEM_COMBOS, "天干合"), (STEM_CLASHES, "天干冲")]:
                relation = relation_map.get(key)
                if relation:
                    rows.append({
                        "kind": kind,
                        "relation": relation,
                        "items": [relation_item_view(item, "gan") for item in involved],
                    })
    return rows


def branch_relationships(items: list[dict[str, str]], required_groups: set[str] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, first in enumerate(items):
        for second in items[index + 1:]:
            involved = [first, second]
            if not has_required_groups(involved, required_groups):
                continue
            if first["zhi"] == second["zhi"]:
                relation = BRANCH_SELF_PUNISH.get(first["zhi"], f"{first['zhi']}{second['zhi']}伏吟/重叠")
                rows.append({
                    "kind": "地支重叠",
                    "relation": relation,
                    "items": [relation_item_view(item, "zhi") for item in involved],
                })
                continue
            for relation in BRANCH_PAIR_RELATIONS.get(frozenset((first["zhi"], second["zhi"])), []):
                rows.append({
                    "kind": "地支关系",
                    "relation": relation,
                    "items": [relation_item_view(item, "zhi") for item in involved],
                })
    branch_set = {item["zhi"] for item in items}
    for needed, relation in BRANCH_TRINES:
        if needed <= branch_set:
            involved = [item for item in items if item["zhi"] in needed]
            if has_required_groups(involved, required_groups):
                rows.append({
                    "kind": "三合局",
                    "relation": relation,
                    "items": [relation_item_view(item, "zhi") for item in involved],
                })
    return rows


def bazi_relationships(
    natal_pillars: dict[str, str],
    flow_pillars: dict[str, str] | None = None,
    current_dayun: dict[str, Any] | None = None,
) -> dict[str, Any]:
    natal_items = named_items_from_pillars(natal_pillars, PILLAR_LABELS, "natal")
    relationships: dict[str, Any] = {
        "natal": {
            "stems": stem_relationships(natal_items),
            "branches": branch_relationships(natal_items),
        }
    }
    if current_dayun and current_dayun.get("gan_zhi"):
        dayun_items = named_items_from_pillars({"dayun": current_dayun["gan_zhi"]}, {"dayun": "当前大运"}, "dayun")
        combined = natal_items + dayun_items
        relationships["current_dayun"] = {
            "pillar": current_dayun["gan_zhi"],
            "stems": stem_relationships(combined, {"natal", "dayun"}),
            "branches": branch_relationships(combined, {"natal", "dayun"}),
        }
    if flow_pillars:
        flow_items = named_items_from_pillars(flow_pillars, FLOW_LABELS, "flow")
        combined = natal_items + flow_items
        relationships["flow"] = {
            "pillars": flow_pillars,
            "stems": stem_relationships(combined, {"natal", "flow"}),
            "branches": branch_relationships(combined, {"natal", "flow"}),
        }
        if current_dayun and current_dayun.get("gan_zhi"):
            dayun_items = named_items_from_pillars({"dayun": current_dayun["gan_zhi"]}, {"dayun": "当前大运"}, "dayun")
            flow_dayun = flow_items + dayun_items
            relationships["flow_with_dayun"] = {
                "stems": stem_relationships(flow_dayun, {"flow", "dayun"}),
                "branches": branch_relationships(flow_dayun, {"flow", "dayun"}),
            }
    return relationships


def count_values(values: list[str], order: list[str] | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    if order:
        return {key: counts.get(key, 0) for key in order if counts.get(key, 0)}
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def bazi_profiles(pillar_details: dict[str, Any]) -> dict[str, Any]:
    stem_ten_gods = [row.get("ten_god_gan", "") for row in pillar_details.values()]
    hidden_ten_gods = [
        item
        for row in pillar_details.values()
        for item in row.get("ten_god_zhi", [])
    ]
    visible_stems = [row.get("gan", "") for row in pillar_details.values()]
    hidden_stems = [
        item
        for row in pillar_details.values()
        for item in row.get("hidden_gan", [])
    ]
    branches = [row.get("zhi", "") for row in pillar_details.values()]
    ten_god_order = ["日主", "比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"]
    element_order = ["木", "火", "土", "金", "水"]
    return {
        "ten_gods": {
            "visible_stems": count_values(stem_ten_gods, ten_god_order),
            "hidden_stems": count_values(hidden_ten_gods, ten_god_order),
            "combined": count_values(stem_ten_gods + hidden_ten_gods, ten_god_order),
        },
        "elements": {
            "visible_stems": count_values([GAN_WUXING.get(stem, "") for stem in visible_stems], element_order),
            "hidden_stems": count_values([GAN_WUXING.get(stem, "") for stem in hidden_stems], element_order),
            "branches": count_values([BRANCH_WUXING.get(branch, "") for branch in branches], element_order),
            "stems_plus_hidden": count_values(
                [GAN_WUXING.get(stem, "") for stem in visible_stems + hidden_stems],
                element_order,
            ),
        },
    }


def ten_god_for_stem(day_master: str, target_stem: str) -> str:
    base_element = GAN_WUXING.get(day_master, "")
    target_element = GAN_WUXING.get(target_stem, "")
    if not base_element or not target_element:
        return ""
    same_polarity = GAN_POLARITY.get(day_master) == GAN_POLARITY.get(target_stem)
    if target_element == base_element:
        return "比肩" if same_polarity else "劫财"
    if WUXING_GENERATES[base_element] == target_element:
        return "食神" if same_polarity else "伤官"
    if WUXING_CONTROLS[base_element] == target_element:
        return "偏财" if same_polarity else "正财"
    if WUXING_CONTROLS[target_element] == base_element:
        return "七杀" if same_polarity else "正官"
    if WUXING_GENERATES[target_element] == base_element:
        return "偏印" if same_polarity else "正印"
    return ""


def enrich_dayun_rows(dayun_rows: list[dict[str, Any]], day_master: str) -> list[dict[str, Any]]:
    enriched = []
    for row in dayun_rows:
        gan_zhi = row.get("gan_zhi", "")
        gan = gan_zhi[0] if len(gan_zhi) >= 2 else ""
        zhi = gan_zhi[1] if len(gan_zhi) >= 2 else ""
        enriched.append({
            **row,
            "gan": gan,
            "zhi": zhi,
            "gan_wuxing": GAN_WUXING.get(gan, ""),
            "zhi_wuxing": BRANCH_WUXING.get(zhi, ""),
            "ten_god_gan": ten_god_for_stem(day_master, gan),
            "growth_by_day_master": changsheng_state(day_master, zhi),
            "self_sitting": changsheng_state(gan, zhi),
        })
    return enriched


def result(module: str, input_data: dict[str, Any], facts: dict[str, Any], *,
           raw: dict[str, Any] | None = None, warnings: list[str] | None = None,
           uncertainties: list[str] | None = None, interpretation_hints: list[str] | None = None,
           calibration_questions: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "module": module,
        "input": input_data,
        "facts": facts,
        "warnings": warnings or [],
        "uncertainties": uncertainties or [],
        "interpretation_hints": interpretation_hints or [],
        "calibration_questions": calibration_questions or [],
        "raw": raw or {},
    }


def parse_ymd(text: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"\s*(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\s*", text)
    if not m:
        raise SystemExit(f"Invalid date: {text}; expected YYYY-MM-DD")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def parse_time(text: str | None) -> tuple[int, int, int]:
    if not text:
        return 0, 0, 0
    m = re.fullmatch(r"\s*(\d{1,2})(?::(\d{1,2}))?(?::(\d{1,2}))?\s*", text)
    if not m:
        raise SystemExit(f"Invalid time: {text}; expected HH:MM")
    return int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0)


def parse_date(text: str | None) -> date:
    if not text:
        return date.today()
    y, m, d = parse_ymd(text)
    return date(y, m, d)


def safe_call(obj: Any, name: str, default: Any = "") -> Any:
    try:
        return getattr(obj, name)()
    except Exception:
        return default


def require_import(module_name: str, install_name: str):
    try:
        return __import__(module_name)
    except ImportError as exc:
        raise SystemExit(
            f"Missing dependency: {install_name}. Install with: python -m pip install {install_name}"
        ) from exc


def zh_branch(value: Any) -> str:
    return BRANCH_CN.get(str(value), str(value))


def zh_stem(value: Any) -> str:
    return STEM_CN.get(str(value), str(value))


def equation_of_time_minutes(dt: datetime) -> float:
    n = dt.timetuple().tm_yday
    b = 2 * math.pi * (n - 81) / 364
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def apply_true_solar_time(dt: datetime, longitude: float | None, tz_offset: float, enable: bool) -> tuple[datetime, dict[str, Any]]:
    if longitude is None or not enable:
        return dt, {"enabled": False}
    mean_minutes = (longitude - tz_offset * 15) * 4
    eot = equation_of_time_minutes(dt)
    total = mean_minutes + eot
    adjusted = dt + timedelta(minutes=total)
    return adjusted, {
        "enabled": True,
        "longitude": longitude,
        "timezone_offset": tz_offset,
        "mean_solar_correction_minutes": round(mean_minutes, 2),
        "equation_of_time_minutes": round(eot, 2),
        "total_correction_minutes": round(total, 2),
        "adjusted_solar": adjusted.strftime("%Y-%m-%d %H:%M:%S"),
    }


def nearest_jieqi_warnings(lunar: Any, threshold_hours: float = 24.0) -> list[str]:
    warnings = []
    current = lunar.getSolar()
    current_jd = current.getJulianDay()
    seen = set()
    for name, solar in lunar.getJieQiTable().items():
        ymd = solar.toYmdHms()
        key = (name, ymd)
        if key in seen or not re.search(r"[\u4e00-\u9fff]", str(name)):
            continue
        seen.add(key)
        hours = abs(solar.getJulianDay() - current_jd) * 24
        if hours <= threshold_hours:
            warnings.append(f"出生时间距节气「{name}」约 {hours:.1f} 小时，月柱/起运需按精确时间复核。")
    return warnings


def ten_kin(base_element: str, line_element: str) -> str:
    if line_element == base_element:
        return "兄弟"
    if WUXING_GENERATES[line_element] == base_element:
        return "父母"
    if WUXING_GENERATES[base_element] == line_element:
        return "子孙"
    if WUXING_CONTROLS[line_element] == base_element:
        return "官鬼"
    if WUXING_CONTROLS[base_element] == line_element:
        return "妻财"
    return "未知"


def bazi(args: argparse.Namespace) -> dict[str, Any]:
    lunar_python = require_import("lunar_python", "lunar-python")
    Solar = lunar_python.Solar
    Lunar = lunar_python.Lunar
    warnings: list[str] = []
    uncertainties = ["不同流派对早晚子时、起运虚实岁、真太阳时校正可能有差异。"]

    true_solar = {"enabled": False}
    if args.solar:
        y, m, d = parse_ymd(args.solar)
        hh, mm, ss = parse_time(args.time)
        original_dt = datetime(y, m, d, hh, mm, ss)
        adjusted_dt, true_solar = apply_true_solar_time(original_dt, args.longitude, args.tz_offset, args.true_solar)
        lunar = Solar.fromYmdHms(
            adjusted_dt.year, adjusted_dt.month, adjusted_dt.day,
            adjusted_dt.hour, adjusted_dt.minute, adjusted_dt.second
        ).getLunar()
        solar_text = original_dt.strftime("%Y-%m-%d %H:%M:%S")
        calculation_solar_text = adjusted_dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        y, m, d = parse_ymd(args.lunar)
        hh, mm, ss = parse_time(args.time)
        lunar = Lunar.fromYmdHms(y, m, d, hh, mm, ss)
        solar_text = str(lunar.getSolar())
        calculation_solar_text = solar_text
        if args.true_solar or args.longitude is not None:
            warnings.append("农历输入未自动应用真太阳时；如需校正，请先转换为公历精确时间。")

    ec = lunar.getEightChar()
    pillars = {"year": ec.getYear(), "month": ec.getMonth(), "day": ec.getDay(), "hour": ec.getTime()}
    pillar_details = {}
    for key, prefix in [("year", "Year"), ("month", "Month"), ("day", "Day"), ("hour", "Time")]:
        pillar_details[key] = {
            "pillar": pillars[key],
            "gan": safe_call(ec, f"get{prefix}Gan"),
            "zhi": safe_call(ec, f"get{prefix}Zhi"),
            "wuxing": safe_call(ec, f"get{prefix}WuXing"),
            "nayin": safe_call(ec, f"get{prefix}NaYin"),
            "ten_god_gan": safe_call(ec, f"get{prefix}ShiShenGan"),
            "hidden_gan": safe_call(ec, f"get{prefix}HideGan", []),
            "ten_god_zhi": safe_call(ec, f"get{prefix}ShiShenZhi", []),
            "xun_kong": safe_call(ec, f"get{prefix}XunKong"),
        }

    h, _, _ = parse_time(args.time)
    if h in {0, 23}:
        warnings.append("出生在子时边界，请确认采用早子/晚子流派；日柱可能随流派变化。")
    warnings.extend(nearest_jieqi_warnings(lunar))

    gender_flag = 1 if str(args.gender).lower() in {"男", "male", "m", "1"} else 0
    luck: dict[str, Any] = {}
    dayun_rows = []
    try:
        yun = ec.getYun(gender_flag)
        luck = {
            "start_offset": {
                "years": yun.getStartYear(),
                "months": yun.getStartMonth(),
                "days": yun.getStartDay(),
                "hours": safe_call(yun, "getStartHour"),
            },
            "start_solar": str(yun.getStartSolar()),
        }
        for item in yun.getDaYun()[:10]:
            dayun_rows.append({
                "index": item.getIndex(),
                "gan_zhi": item.getGanZhi(),
                "start_age": item.getStartAge(),
                "end_age": item.getEndAge(),
                "start_year": item.getStartYear(),
                "end_year": item.getEndYear(),
                "xun_kong": item.getXunKong(),
            })
    except Exception as exc:
        warnings.append(f"大运计算失败：{exc}")

    day_master = pillar_details["day"]["gan"]
    growth_by_day_master = pillar_changsheng(pillar_details, day_master)
    self_sitting = self_sitting_changsheng(pillar_details)
    dayun_rows = enrich_dayun_rows(dayun_rows, day_master)

    as_of_text = getattr(args, "as_of", None)
    flow: dict[str, Any] = {}
    if as_of_text:
        as_of = parse_date(as_of_text)
        flow_lunar = Solar.fromYmdHms(as_of.year, as_of.month, as_of.day, 0, 0, 0).getLunar()
        flow_ec = flow_lunar.getEightChar()
        flow_window = max(1, min(int(getattr(args, "flow_window", 5) or 5), 20))
        annual_flows = []
        for year in range(as_of.year - flow_window + 1, as_of.year + 1):
            annual_ec = Solar.fromYmdHms(year, 6, 15, 0, 0, 0).getLunar().getEightChar()
            annual_dayun = next(
                (row for row in dayun_rows if row["start_year"] <= year <= row["end_year"]),
                None,
            )
            annual_flows.append({
                "year": year,
                "nominal_age": year - int(solar_text[:4]) + 1,
                "pillar": annual_ec.getYear(),
                "dayun": annual_dayun["gan_zhi"] if annual_dayun else "",
            })
        current_dayun = next(
            (row for row in dayun_rows if row["start_year"] <= as_of.year <= row["end_year"]),
            None,
        )
        birth_year = int(solar_text[:4])
        flow = {
            "as_of": as_of.isoformat(),
            "nominal_age": as_of.year - birth_year + 1,
            "pillars": {
                "year": flow_ec.getYear(),
                "month": flow_ec.getMonth(),
                "day": flow_ec.getDay(),
            },
            "lunar": str(flow_lunar),
            "current_dayun": current_dayun,
            "annual_flows": annual_flows,
        }
        flow["growth_by_day_master"] = {
            "dayun": changsheng_state(day_master, branch_from_pillar(current_dayun["gan_zhi"] if current_dayun else "")),
            "year": changsheng_state(day_master, branch_from_pillar(flow["pillars"]["year"])),
            "month": changsheng_state(day_master, branch_from_pillar(flow["pillars"]["month"])),
            "day": changsheng_state(day_master, branch_from_pillar(flow["pillars"]["day"])),
        }

    facts = {
        "name": args.name,
        "solar": solar_text,
        "calculation_solar": calculation_solar_text,
        "lunar": str(lunar),
        "pillars": pillars,
        "day_master": {"gan": day_master, "wuxing": GAN_WUXING.get(day_master, "")},
        "details": pillar_details,
        "twelve_growth": {
            "by_day_master": growth_by_day_master,
            "self_sitting": self_sitting,
        },
        "profiles": bazi_profiles(pillar_details),
        "relationships": bazi_relationships(
            pillars,
            flow.get("pillars") if flow else None,
            flow.get("current_dayun") if flow else None,
        ),
        "luck": luck,
        "dayun": dayun_rows,
        "flow": flow,
        "true_solar_time": true_solar,
    }
    return result(
        "bazi",
        {
            "solar": args.solar,
            "lunar": args.lunar,
            "time": args.time,
            "gender": args.gender,
            "birthplace": args.birthplace,
            "as_of": as_of_text,
        },
        facts,
        warnings=warnings,
        uncertainties=uncertainties,
        interpretation_hints=[
            "先看日主、月令、十神结构，再看大运是否引动喜忌。",
            "若真太阳时校正跨时辰，必须同时比较校正前后两个盘。",
        ],
        calibration_questions=[
            "过去换大运年份附近是否有明显学习、职业、居住或关系变化？",
            "日主对应的性格描述与本人自评是否一致？",
        ],
    )


def ziwei(args: argparse.Namespace) -> dict[str, Any]:
    require_import("iztro_py", "iztro-py")
    from iztro_py import astro

    y, _, _ = parse_ymd(args.solar)
    as_of = parse_date(args.as_of)
    nominal_age = as_of.year - y + 1
    chart = astro.by_solar(args.solar.replace("-0", "-"), args.hour_index, args.gender, "zh-CN")
    palaces = []
    current_decadal = None
    for p in chart.palaces:
        dec_range = list(p.decadal.range) if getattr(p, "decadal", None) else []
        row = {
            "name": str(p.translate_name() if hasattr(p, "translate_name") else p),
            "branch": zh_branch(getattr(p, "earthly_branch", "")),
            "major_stars": [s.translate_name() if hasattr(s, "translate_name") else str(s) for s in p.major_stars],
            "minor_stars": [s.translate_name() if hasattr(s, "translate_name") else str(s) for s in p.minor_stars],
            "decadal": {
                "range": dec_range,
                "stem": zh_stem(getattr(p.decadal, "heavenly_stem", "")) if getattr(p, "decadal", None) else "",
                "branch": zh_branch(getattr(p.decadal, "earthly_branch", "")) if getattr(p, "decadal", None) else "",
            },
        }
        if dec_range and dec_range[0] <= nominal_age <= dec_range[1]:
            current_decadal = row
        palaces.append(row)
    mutagens = []
    for p in chart.palaces:
        for s in list(p.major_stars) + list(p.minor_stars):
            if getattr(s, "mutagen", None):
                mutagens.append({
                    "star": s.translate_name() if hasattr(s, "translate_name") else str(s),
                    "mutagen": s.mutagen,
                    "palace": p.translate_name() if hasattr(p, "translate_name") else str(p),
                })
    facts = {
        "lunar_date": chart.lunar_date,
        "chinese_date": chart.chinese_date,
        "five_elements_class": FIVE_ELEMENTS_CN.get(str(chart.five_elements_class), str(chart.five_elements_class)),
        "soul_palace_branch": zh_branch(chart.earthly_branch_of_soul_palace),
        "body_palace_branch": zh_branch(chart.earthly_branch_of_body_palace),
        "nominal_age_as_of": {"date": as_of.isoformat(), "age": nominal_age},
        "current_decadal": current_decadal,
        "year_mutagens": mutagens,
        "palaces": palaces,
    }
    return result(
        "ziwei",
        {"solar": args.solar, "hour_index": args.hour_index, "gender": args.gender, "as_of": as_of.isoformat()},
        facts,
        uncertainties=["当前大限按虚岁粗定位；不同软件可能采用周岁/虚岁显示差异。"],
        interpretation_hints=[
            "优先看命宫、身宫、官禄、财帛、夫妻和生年四化。",
            "当前大限只作为阶段定位，细断还需要流年四化。"
        ],
        calibration_questions=["当前十年主要课题是否落在 current_decadal 所示宫位主题？"],
    )


def mbti(args: argparse.Namespace) -> dict[str, Any]:
    type_code = args.type.upper()
    if not re.fullmatch(r"[EI][SN][TF][JP]", type_code):
        raise SystemExit("--type must look like INTJ, ENFP, ISTP, etc.")
    axes = {
        "energy": "外向 E" if type_code[0] == "E" else "内向 I",
        "information": "实感 S" if type_code[1] == "S" else "直觉 N",
        "decision": "思考 T" if type_code[2] == "T" else "情感 F",
        "lifestyle": "判断 J" if type_code[3] == "J" else "知觉 P",
    }
    hints = {
        "I": "更依赖独处恢复能量，适合深度工作。",
        "E": "更依赖外部互动获得能量，适合即时反馈。",
        "N": "关注模式、可能性和抽象关系。",
        "S": "关注事实、经验和可验证细节。",
        "T": "决策时更重一致性、逻辑和边界。",
        "F": "决策时更重关系、价值和人的感受。",
        "J": "偏好计划、收束和确定性。",
        "P": "偏好探索、弹性和开放选项。",
    }
    facts = {"type": type_code, "axes": axes, "hints": [hints[c] for c in type_code]}
    return result(
        "mbti",
        {"type": type_code},
        facts,
        uncertainties=["MBTI 是行为偏好语言，不是命理证据，也不是临床人格测量。"],
        interpretation_hints=["用 MBTI 解释沟通、动机、压力反应；不要用它覆盖八字或紫微信息。"],
        calibration_questions=["这个 MBTI 类型是正式量表结果，还是自测/自评？"],
    )


def liuyao(args: argparse.Namespace) -> dict[str, Any]:
    values = [int(x.strip()) for x in args.lines.split(",") if x.strip()]
    if len(values) != 6 or any(v not in {6, 7, 8, 9} for v in values):
        raise SystemExit("--lines needs six values from bottom to top, each in {6,7,8,9}")
    bits = [1 if v in {7, 9} else 0 for v in values]
    changed_bits = [1 - b if values[i] in {6, 9} else b for i, b in enumerate(bits)]
    lower = TRIGRAM_BITS[tuple(bits[:3])]
    upper = TRIGRAM_BITS[tuple(bits[3:])]
    changed_lower = TRIGRAM_BITS[tuple(changed_bits[:3])]
    changed_upper = TRIGRAM_BITS[tuple(changed_bits[3:])]
    moving = [i + 1 for i, v in enumerate(values) if v in {6, 9}]
    line_names = ["老阴" if v == 6 else "少阳" if v == 7 else "少阴" if v == 8 else "老阳" for v in values]
    palace_element = args.palace_element or TRIGRAM_ELEMENTS[upper[0]]
    spirit_start = SIX_SPIRIT_START.get(args.day_gan, 0)
    line_attrs = []
    na_lower = NA_JIA[lower[0]][:3]
    na_upper = NA_JIA[upper[0]][3:]
    for i, (value, bit, label, ganzhi) in enumerate(zip(values, bits, line_names, na_lower + na_upper), start=1):
        _, branch = ganzhi
        line_element = BRANCH_WUXING[branch]
        line_attrs.append({
            "line": i,
            "value": value,
            "yin_yang": "阳" if bit else "阴",
            "line_name": label,
            "moving": value in {6, 9},
            "na_jia": f"{ganzhi[0]}{branch}",
            "element": line_element,
            "six_kin": ten_kin(palace_element, line_element),
            "six_spirit": SIX_SPIRITS[(spirit_start + i - 1) % 6] if args.day_gan else "",
        })
    facts = {
        "question": args.question,
        "base": {
            "lower_trigram": {"name": lower[0], "image": lower[1]},
            "upper_trigram": {"name": upper[0], "image": upper[1]},
            "binary_bottom_to_top": bits,
        },
        "moving_lines": moving,
        "changed": {
            "lower_trigram": {"name": changed_lower[0], "image": changed_lower[1]},
            "upper_trigram": {"name": changed_upper[0], "image": changed_upper[1]},
            "binary_bottom_to_top": changed_bits,
        },
        "palace_element_used": palace_element,
        "lines": line_attrs,
    }
    uncertainties = [
        "六亲以 palace-element 参数或上卦五行作工作基准；完整卦宫/世应排法仍需按流派细化。",
        "若未提供 day-gan，则六神为空。",
    ]
    return result(
        "liuyao",
        {"question": args.question, "lines": values, "day_gan": args.day_gan, "palace_element": args.palace_element},
        facts,
        uncertainties=uncertainties,
        interpretation_hints=[
            "先看所问事项对应用神，再看动爻、变卦、六亲和六神。",
            "单卦只回答当下问题，不覆盖出生盘结构。",
        ],
        calibration_questions=["起卦时的原问题是否足够具体？是否同一问题反复起卦？"],
    )


def xiaoliuren(args: argparse.Namespace) -> dict[str, Any]:
    if args.hour_branch not in BRANCHES:
        raise SystemExit("--hour-branch must be one of 子丑寅卯辰巳午未申酉戌亥")
    hour_index = BRANCHES.index(args.hour_branch) + 1
    if args.method == "standard":
        idx = (args.lunar_month + args.lunar_day + hour_index - 3) % 6
    else:
        idx = (args.lunar_month + args.lunar_day + hour_index) % 6
    state = XIAO_LIUREN_STATES[idx]
    facts = {
        "question": args.question,
        "method": args.method,
        "result": {"state": state, "hint": XIAO_LIUREN_HINTS[state]},
        "sequence": XIAO_LIUREN_STATES,
    }
    return result(
        "xiaoliuren",
        {"lunar_month": args.lunar_month, "lunar_day": args.lunar_day, "hour_branch": args.hour_branch, "question": args.question},
        facts,
        uncertainties=["小六壬有多种民俗起法；当前结果适合轻量参考。"],
        interpretation_hints=["只作为快问快答和时机气象，不替代六爻细断。"],
        calibration_questions=["这件事是短期事项还是长期决策？小六壬更适合短期。"],
    )


def western(args: argparse.Namespace) -> dict[str, Any]:
    ephem = require_import("ephem", "ephem")
    y, m, d = parse_ymd(args.solar)
    hh, mm, ss = parse_time(args.time)
    local_dt = datetime(y, m, d, hh, mm, ss)
    utc_dt = local_dt - timedelta(hours=args.tz_offset)
    ephem_date = ephem.Date(utc_dt)
    placements = []
    element_counts = {"火": 0, "土": 0, "风": 0, "水": 0}
    modality_counts = {"基本": 0, "固定": 0, "变动": 0}
    for key, label, class_name in WESTERN_BODIES:
        longitude = ecliptic_longitude(ephem, class_name, ephem_date)
        sign = WESTERN_SIGNS[int(longitude // 30)]
        degree = longitude % 30
        element, modality = WESTERN_SIGN_META[sign]
        element_counts[element] += 1
        modality_counts[modality] += 1
        placements.append({
            "key": key,
            "body": label,
            "sign": sign,
            "degree": round(degree, 2),
            "absolute_longitude": round(longitude, 2),
            "element": element,
            "modality": modality,
        })
    warnings = []
    latitude = getattr(args, "latitude", None)
    longitude_arg = getattr(args, "longitude", None)
    houses: dict[str, Any] = {}
    if latitude is None or longitude_arg is None:
        warnings.append("未提供出生地经纬度；暂不计算上升星座、宫位和精确宫主星。")
    else:
        houses = western_angles_and_houses(ephem, ephem_date, latitude, longitude_arg)
    facts = {
        "system": "Western tropical zodiac, geocentric apparent positions via ephem",
        "local_datetime": local_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "utc_datetime": utc_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone_offset": args.tz_offset,
        "placements": placements,
        "aspects": western_aspects(placements),
        "moon_phase": western_moon_phase(placements),
        "retrogrades": western_retrogrades(ephem, ephem_date, placements),
        "balance": {"elements": element_counts, "modalities": modality_counts},
        "houses": houses,
    }
    uncertainties = []
    calibration_questions = []
    if latitude is None or longitude_arg is None:
        uncertainties.append("未给出生地时，西占只能稳定解释行星星座；上升、宫位、轴线和宫主星需要出生地。")
        calibration_questions.append("出生地城市是什么？确认后可补上升星座、宫位和轴线。")
    else:
        uncertainties.append("宫位采用整宫制与等宫制参考；若需要 Placidus、Koch 等精密宫制，应另接 Swiss Ephemeris 类库复核。")
        calibration_questions.append("出生时间若有 10-20 分钟以上误差，需要复核上升度数与宫位主题。")
    return result(
        "western",
        {
            "solar": args.solar,
            "time": args.time,
            "tz_offset": args.tz_offset,
            "latitude": latitude,
            "longitude": longitude_arg,
        },
        facts,
        warnings=warnings,
        uncertainties=uncertainties,
        interpretation_hints=[
            "先看太阳/月亮/水星/金星/火星的人格与关系语言，再用木星、土星看扩张和压力。",
            "不要用西占覆盖八字或紫微；用于补充心理、沟通和关系模式。",
        ],
        calibration_questions=calibration_questions,
    )


def doctor(_: argparse.Namespace) -> dict[str, Any]:
    deps = {}
    for module, package in [("lunar_python", "lunar-python"), ("iztro_py", "iztro-py"), ("ephem", "ephem")]:
        deps[package] = {
            "import": module,
            "available": importlib.util.find_spec(module) is not None,
            "install": f"python -m pip install {package}",
        }
    return result(
        "doctor",
        {},
        {"dependencies": deps, "python_modules_optional_for": {"lunar-python": ["bazi"], "iztro-py": ["ziwei"], "ephem": ["western"]}},
        warnings=[f"{p} not installed" for p, d in deps.items() if not d["available"]],
        interpretation_hints=["Install missing dependencies before running Bazi or Ziwei calculations."],
    )


def render_html(report: dict[str, Any], output: str) -> None:
    title = "Xuanxue Console Report"
    body = html.escape(json.dumps(report, ensure_ascii=False, indent=2))
    modules = report["facts"].get("modules", [])
    cards = []
    for item in modules:
        facts = item.get("facts", {})
        summary = facts.get("pillars") or facts.get("type") or facts.get("result") or facts.get("soul_palace_branch") or facts.get("base") or {}
        cards.append(
            f"<section><h2>{html.escape(item.get('module', 'module'))}</h2>"
            f"<pre>{html.escape(json.dumps(summary, ensure_ascii=False, indent=2))}</pre></section>"
        )
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#101014;color:#f0eadc;line-height:1.6}}
main{{max-width:980px;margin:auto;padding:32px}}
section{{border:1px solid #3b3326;background:#18181f;margin:16px 0;padding:18px;border-radius:8px}}
h1,h2{{color:#d6b66e}} pre{{white-space:pre-wrap;background:#0a0a0d;padding:14px;border-radius:6px;overflow:auto}}
</style>
</head>
<body><main><h1>{title}</h1>{''.join(cards)}<section><h2>Full JSON</h2><pre>{body}</pre></section></main></body></html>"""
    Path(output).write_text(page, encoding="utf-8")


def longform(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.input_json)
    report = json.loads(source.read_text(encoding="utf-8"))
    markdown = render_longform_markdown(report, args.title or "")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    facts = {
        "source_json": str(source),
        "article": str(output),
        "chars": len(markdown),
        "modules": [item.get("module", "") for item in report_modules(report)],
        "template": "templates/longform-analysis-template.md",
    }
    return result(
        "longform",
        {"input_json": str(source), "output": str(output), "title": args.title},
        facts,
        warnings=[],
        uncertainties=[
            "longform 子命令生成的是基于结构化事实的 Markdown 初稿；传播文风和个案细节仍建议由人工或 LLM 二次润色校准。",
        ],
        interpretation_hints=[
            "生成后运行 scripts/validate_longform_report.py，并用真实经历校准过去年份。",
        ],
        calibration_questions=[
            "过去几年中，2020、2024、2026 是否有明显结构变化或压力升级？",
        ],
    )


def combo(args: argparse.Namespace) -> dict[str, Any]:
    modules = []
    warnings: list[str] = []
    has_birth_date = bool(args.solar or args.lunar)
    for name, fn, needed in [
        ("bazi", bazi, bool(has_birth_date and args.time and args.gender)),
        ("ziwei", ziwei, bool(args.solar and args.hour_index is not None and args.gender)),
        ("western", western, bool(args.western and args.solar and args.time)),
        ("mbti", mbti, bool(args.mbti_type)),
        ("liuyao", liuyao, bool(args.question and args.lines)),
        ("xiaoliuren", xiaoliuren, bool(args.question and args.lunar_month and args.lunar_day and args.hour_branch)),
    ]:
        if not needed:
            continue
        try:
            local = argparse.Namespace(**vars(args))
            if name == "mbti":
                local.type = args.mbti_type
            modules.append(fn(local))
        except SystemExit as exc:
            warnings.append(f"{name} skipped: {exc}")
    cross = []
    names = {m["module"] for m in modules}
    if {"bazi", "ziwei"} <= names:
        cross.append("八字用于季节/五行/十神结构，紫微用于宫位/四化分布；两者交集才作为重点判断。")
    if "mbti" in names:
        cross.append("MBTI 只解释沟通和行为偏好，不作为命理证据。")
    if {"liuyao", "xiaoliuren"} & names:
        cross.append("占事模块只回答当前问题或时机，不覆盖出生盘。")
    report = result(
        "combo",
        {k: v for k, v in vars(args).items() if k not in {"func"}},
        {"modules": modules, "cross_validation": cross},
        warnings=warnings,
        interpretation_hints=[
            "先列每个模块的事实，再只解释交叉出现的强信号。",
            "对冲突信号给出校准问题，不强行调和。"
        ],
        calibration_questions=[
            "你最想校准事业、关系、财务、健康还是当下决策？",
            "过去 3 年是否有可验证的重大转折？",
        ],
    )
    if args.html:
        render_html(report, args.html)
        report["facts"]["html_report"] = args.html
    return report


def add_birth_args(p: argparse.ArgumentParser, *, require_date: bool = False, require_gender: bool = False) -> None:
    g = p.add_mutually_exclusive_group(required=require_date)
    g.add_argument("--solar")
    g.add_argument("--lunar")
    p.add_argument("--time", default="00:00")
    p.add_argument("--gender", required=require_gender)
    p.add_argument("--name", default="")
    p.add_argument("--birthplace", default="")
    p.add_argument("--longitude", type=float)
    p.add_argument("--tz-offset", type=float, default=8.0)
    p.add_argument("--true-solar", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Xuanxue Console")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("doctor")
    p.set_defaults(func=doctor)

    p = sub.add_parser("bazi")
    add_birth_args(p, require_date=True, require_gender=True)
    p.add_argument("--as-of")
    p.add_argument("--flow-window", type=int, default=5)
    p.set_defaults(func=bazi)

    p = sub.add_parser("ziwei")
    p.add_argument("--solar", required=True)
    p.add_argument("--hour-index", type=int, required=True)
    p.add_argument("--gender", required=True, choices=["男", "女"])
    p.add_argument("--as-of")
    p.set_defaults(func=ziwei)

    p = sub.add_parser("mbti")
    p.add_argument("--type", required=True)
    p.set_defaults(func=mbti)

    p = sub.add_parser("western")
    p.add_argument("--solar", required=True)
    p.add_argument("--time", required=True)
    p.add_argument("--tz-offset", type=float, default=8.0)
    p.add_argument("--latitude", type=float)
    p.add_argument("--longitude", type=float)
    p.set_defaults(func=western)

    p = sub.add_parser("liuyao")
    p.add_argument("--question", required=True)
    p.add_argument("--lines", required=True)
    p.add_argument("--day-gan", choices=list(GAN_WUXING.keys()))
    p.add_argument("--palace-element", choices=["木", "火", "土", "金", "水"])
    p.set_defaults(func=liuyao)

    p = sub.add_parser("xiaoliuren")
    p.add_argument("--question", required=True)
    p.add_argument("--lunar-month", type=int, required=True)
    p.add_argument("--lunar-day", type=int, required=True)
    p.add_argument("--hour-branch", required=True)
    p.add_argument("--method", choices=["standard", "offset"], default="standard")
    p.set_defaults(func=xiaoliuren)

    p = sub.add_parser("combo")
    add_birth_args(p)
    p.add_argument("--hour-index", type=int)
    p.add_argument("--as-of")
    p.add_argument("--flow-window", type=int, default=5)
    p.add_argument("--western", action="store_true")
    p.add_argument("--latitude", type=float)
    p.add_argument("--mbti-type")
    p.add_argument("--question")
    p.add_argument("--lines")
    p.add_argument("--day-gan", choices=list(GAN_WUXING.keys()))
    p.add_argument("--palace-element", choices=["木", "火", "土", "金", "水"])
    p.add_argument("--lunar-month", type=int)
    p.add_argument("--lunar-day", type=int)
    p.add_argument("--hour-branch")
    p.add_argument("--method", choices=["standard", "offset"], default="standard")
    p.add_argument("--html")
    p.set_defaults(func=combo)

    p = sub.add_parser("longform")
    p.add_argument("--input-json", required=True, help="Path to a combo or single-module JSON report.")
    p.add_argument("--output", required=True, help="Path to write the Markdown longform draft.")
    p.add_argument("--title", default="")
    p.set_defaults(func=longform)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dump(args.func(args))


if __name__ == "__main__":
    main()
