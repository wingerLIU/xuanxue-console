"""Western astrology helpers for xuanxue_console."""

from __future__ import annotations

import math
from typing import Any


WESTERN_SIGNS = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女", "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
WESTERN_SIGN_META = {
    "白羊": ("火", "基本"), "金牛": ("土", "固定"), "双子": ("风", "变动"), "巨蟹": ("水", "基本"),
    "狮子": ("火", "固定"), "处女": ("土", "变动"), "天秤": ("风", "基本"), "天蝎": ("水", "固定"),
    "射手": ("火", "变动"), "摩羯": ("土", "基本"), "水瓶": ("风", "固定"), "双鱼": ("水", "变动"),
}
WESTERN_SIGN_RULERS = {
    "白羊": "火星",
    "金牛": "金星",
    "双子": "水星",
    "巨蟹": "月亮",
    "狮子": "太阳",
    "处女": "水星",
    "天秤": "金星",
    "天蝎": "火星/冥王星",
    "射手": "木星",
    "摩羯": "土星",
    "水瓶": "土星/天王星",
    "双鱼": "木星/海王星",
}
WESTERN_BODIES = [
    ("sun", "太阳", "Sun"),
    ("moon", "月亮", "Moon"),
    ("mercury", "水星", "Mercury"),
    ("venus", "金星", "Venus"),
    ("mars", "火星", "Mars"),
    ("jupiter", "木星", "Jupiter"),
    ("saturn", "土星", "Saturn"),
    ("uranus", "天王星", "Uranus"),
    ("neptune", "海王星", "Neptune"),
    ("pluto", "冥王星", "Pluto"),
]
WESTERN_MAJOR_ASPECTS = [
    ("合相", 0, 8),
    ("六合", 60, 5),
    ("刑相", 90, 7),
    ("拱相", 120, 7),
    ("冲相", 180, 8),
]


def aspect_separation(lon_a: float, lon_b: float) -> float:
    diff = abs(lon_a - lon_b) % 360
    return min(diff, 360 - diff)


def signed_longitude_delta(lon_after: float, lon_before: float) -> float:
    return ((lon_after - lon_before + 180) % 360) - 180


def ecliptic_longitude(ephem_module: Any, class_name: str, ephem_date: Any) -> float:
    body = getattr(ephem_module, class_name)(ephem_date)
    return math.degrees(float(ephem_module.Ecliptic(body).lon)) % 360


def western_aspects(placements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    aspects: list[dict[str, Any]] = []
    for idx, first in enumerate(placements):
        for second in placements[idx + 1:]:
            separation = aspect_separation(first["absolute_longitude"], second["absolute_longitude"])
            for name, exact_angle, max_orb in WESTERN_MAJOR_ASPECTS:
                orb = abs(separation - exact_angle)
                if orb <= max_orb:
                    aspects.append({
                        "body_a": first["body"],
                        "body_b": second["body"],
                        "aspect": name,
                        "exact_angle": exact_angle,
                        "separation": round(separation, 2),
                        "orb": round(orb, 2),
                    })
                    break
    return sorted(aspects, key=lambda row: (row["orb"], row["exact_angle"], row["body_a"], row["body_b"]))


def moon_phase_from_angle(angle: float) -> str:
    phases = [
        (22.5, "新月"),
        (67.5, "娥眉月"),
        (112.5, "上弦月"),
        (157.5, "盈凸月"),
        (202.5, "满月"),
        (247.5, "亏凸月"),
        (292.5, "下弦月"),
        (337.5, "残月"),
        (360.0, "新月"),
    ]
    for boundary, name in phases:
        if angle < boundary:
            return name
    return "新月"


def western_moon_phase(placements: list[dict[str, Any]]) -> dict[str, Any]:
    by_key = {row["key"]: row for row in placements}
    sun_lon = by_key["sun"]["absolute_longitude"]
    moon_lon = by_key["moon"]["absolute_longitude"]
    angle = (moon_lon - sun_lon) % 360
    illumination = (1 - math.cos(math.radians(angle))) / 2
    return {
        "phase": moon_phase_from_angle(angle),
        "sun_moon_angle": round(angle, 2),
        "illumination_percent": round(illumination * 100, 1),
        "waxing": angle < 180,
    }


def western_retrogrades(ephem_module: Any, ephem_date: Any, placements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in placements:
        if row["key"] in {"sun", "moon"}:
            rows.append({**row, "retrograde": False, "daily_motion_degrees": None})
            continue
        class_name = next(class_name for key, _, class_name in WESTERN_BODIES if key == row["key"])
        before = ecliptic_longitude(ephem_module, class_name, ephem_date - 1)
        after = ecliptic_longitude(ephem_module, class_name, ephem_date + 1)
        daily_motion = signed_longitude_delta(after, before) / 2
        rows.append({
            **row,
            "retrograde": daily_motion < 0,
            "daily_motion_degrees": round(daily_motion, 4),
        })
    return rows


def western_position(longitude: float) -> dict[str, Any]:
    absolute = longitude % 360
    sign = WESTERN_SIGNS[int(absolute // 30)]
    degree = absolute % 30
    return {
        "sign": sign,
        "degree": round(degree, 2),
        "absolute_longitude": round(absolute, 2),
        "ruler": WESTERN_SIGN_RULERS[sign],
        "display": f"{sign}{degree:.2f}°",
    }


def western_angles_and_houses(ephem_module: Any, ephem_date: Any, latitude: float, longitude: float) -> dict[str, Any]:
    observer = ephem_module.Observer()
    observer.lat = str(latitude)
    observer.lon = str(longitude)
    observer.date = ephem_date

    local_sidereal = float(observer.sidereal_time())
    obliquity = math.radians(23.4392911)
    latitude_rad = math.radians(latitude)

    ascendant = math.degrees(math.atan2(
        math.cos(local_sidereal),
        -(math.sin(local_sidereal) * math.cos(obliquity) + math.tan(latitude_rad) * math.sin(obliquity)),
    )) % 360
    midheaven = math.degrees(math.atan2(
        math.sin(local_sidereal),
        math.cos(local_sidereal) * math.cos(obliquity),
    )) % 360

    ascendant_position = western_position(ascendant)
    ascendant_sign_index = WESTERN_SIGNS.index(ascendant_position["sign"])
    whole_sign_houses = []
    equal_house_cusps = []
    for idx in range(12):
        sign = WESTERN_SIGNS[(ascendant_sign_index + idx) % 12]
        house_number = idx + 1
        whole_sign_houses.append({
            "house": house_number,
            "sign": sign,
            "ruler": WESTERN_SIGN_RULERS[sign],
        })
        equal_house_cusps.append({
            "house": house_number,
            "cusp": western_position(ascendant + idx * 30),
        })

    return {
        "system_note": "轴线按出生地经纬度与本地恒星时计算；宫位提供整宫制与等宫制参考，不等同于 Placidus 等精密宫制。",
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "local_sidereal_degrees": round(math.degrees(local_sidereal) % 360, 2),
        "angles": {
            "ascendant": ascendant_position,
            "descendant": western_position(ascendant + 180),
            "midheaven": western_position(midheaven),
            "imum_coeli": western_position(midheaven + 180),
        },
        "whole_sign_houses": whole_sign_houses,
        "equal_house_cusps": equal_house_cusps,
    }
