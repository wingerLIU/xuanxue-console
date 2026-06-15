#!/usr/bin/env python3
"""Run birth-time sensitivity checks for Bazi, Ziwei, and Western astrology."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).with_name("xuanxue_console.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether shifted birth minutes change chart anchors.")
    parser.add_argument("--solar", required=True, help="Birth date YYYY-MM-DD.")
    parser.add_argument("--time", required=True, help="Birth time HH:MM.")
    parser.add_argument("--gender", required=True)
    parser.add_argument("--name", default="")
    parser.add_argument("--birthplace", default="")
    parser.add_argument("--latitude", type=float)
    parser.add_argument("--longitude", type=float)
    parser.add_argument("--tz-offset", type=float, default=8.0)
    parser.add_argument("--true-solar", action="store_true")
    parser.add_argument(
        "--ziwei-true-solar",
        action="store_true",
        help="Use Bazi true-solar-adjusted time to derive Ziwei hour index. Default uses local clock time.",
    )
    parser.add_argument("--as-of", default="2026-06-12")
    parser.add_argument("--windows", default="30,60", help="Comma-separated minute windows, e.g. 15,30,60.")
    parser.add_argument("--output", help="Optional JSON output path.")
    return parser.parse_args()


def run_json(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    return json.loads(proc.stdout)


def hour_index(dt: datetime) -> int:
    hour = dt.hour
    if hour == 23:
        return 12
    if hour == 0:
        return 0
    return (hour + 1) // 2


def shifted_points(solar: str, time: str, windows: list[int]) -> list[tuple[str, datetime]]:
    base = datetime.strptime(f"{solar} {time}", "%Y-%m-%d %H:%M")
    points: list[tuple[str, datetime]] = [("baseline", base)]
    for window in windows:
        points.append((f"minus_{window}", base - timedelta(minutes=window)))
        points.append((f"plus_{window}", base + timedelta(minutes=window)))
    seen: set[str] = set()
    unique: list[tuple[str, datetime]] = []
    for label, dt in points:
        key = dt.strftime("%Y-%m-%d %H:%M")
        if key not in seen:
            seen.add(key)
            unique.append((label, dt))
    return unique


def summarize_variant(label: str, dt: datetime, args: argparse.Namespace) -> dict[str, Any]:
    date_s = dt.strftime("%Y-%m-%d")
    time_s = dt.strftime("%H:%M")
    bazi_cmd = [
        "bazi",
        "--solar",
        date_s,
        "--time",
        time_s,
        "--gender",
        args.gender,
        "--tz-offset",
        str(args.tz_offset),
        "--as-of",
        args.as_of,
        "--flow-window",
        "1",
    ]
    if args.name:
        bazi_cmd += ["--name", args.name]
    if args.birthplace:
        bazi_cmd += ["--birthplace", args.birthplace]
    if args.longitude is not None:
        bazi_cmd += ["--longitude", str(args.longitude)]
    if args.true_solar:
        bazi_cmd.append("--true-solar")
    bazi = run_json(bazi_cmd)

    ziwei_dt = dt
    adjusted_solar = bazi.get("facts", {}).get("true_solar_time", {}).get("adjusted_solar")
    if args.ziwei_true_solar and adjusted_solar:
        ziwei_dt = datetime.strptime(adjusted_solar[:16], "%Y-%m-%d %H:%M")

    ziwei = run_json(
        [
            "ziwei",
            "--solar",
            ziwei_dt.strftime("%Y-%m-%d"),
            "--hour-index",
            str(hour_index(ziwei_dt)),
            "--gender",
            args.gender,
            "--as-of",
            args.as_of,
        ]
    )

    western_cmd = ["western", "--solar", date_s, "--time", time_s, "--tz-offset", str(args.tz_offset)]
    if args.latitude is not None and args.longitude is not None:
        western_cmd += ["--latitude", str(args.latitude), "--longitude", str(args.longitude)]
    western = run_json(western_cmd)

    western_facts = western.get("facts", {})
    angles = western_facts.get("houses", {}).get("angles", {})
    moon = next((row for row in western_facts.get("placements", []) if row.get("body") == "月亮"), {})
    return {
        "label": label,
        "local_datetime": f"{date_s} {time_s}",
        "hour_index": hour_index(dt),
        "ziwei_hour_index": hour_index(ziwei_dt),
        "ziwei_hour_basis": "true_solar" if args.ziwei_true_solar else "local_clock",
        "bazi": {
            "pillars": bazi.get("facts", {}).get("pillars", {}),
            "true_solar_adjusted": bazi.get("facts", {}).get("true_solar_time", {}).get("adjusted_solar"),
        },
        "ziwei": {
            "soul_palace_branch": ziwei.get("facts", {}).get("soul_palace_branch"),
            "body_palace_branch": ziwei.get("facts", {}).get("body_palace_branch"),
            "current_decadal": ziwei.get("facts", {}).get("current_decadal"),
        },
        "western": {
            "moon": {
                "sign": moon.get("sign"),
                "degree": moon.get("degree"),
            },
            "ascendant": angles.get("ascendant", {}).get("display"),
            "midheaven": angles.get("midheaven", {}).get("display"),
        },
    }


def stability(variants: list[dict[str, Any]]) -> dict[str, Any]:
    def values(path: list[str]) -> list[Any]:
        output = []
        for item in variants:
            cur: Any = item
            for key in path:
                cur = cur.get(key) if isinstance(cur, dict) else None
            output.append(cur)
        return output

    checks = {
        "bazi_pillars_stable": values(["bazi", "pillars"]),
        "ziwei_soul_stable": values(["ziwei", "soul_palace_branch"]),
        "ziwei_body_stable": values(["ziwei", "body_palace_branch"]),
        "western_ascendant_stable": values(["western", "ascendant"]),
        "western_midheaven_stable": values(["western", "midheaven"]),
        "western_moon_sign_stable": values(["western", "moon", "sign"]),
    }
    return {
        key: {
            "stable": len({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in value_list}) == 1,
            "values": value_list,
        }
        for key, value_list in checks.items()
    }


def main() -> int:
    args = parse_args()
    windows = [int(item.strip()) for item in args.windows.split(",") if item.strip()]
    variants = [summarize_variant(label, dt, args) for label, dt in shifted_points(args.solar, args.time, windows)]
    result = {
        "schema_version": "0.1.0",
        "module": "birth_time_sensitivity",
        "input": vars(args),
        "variants": variants,
        "stability": stability(variants),
        "summary": {
            "all_core_anchors_stable": all(row["stable"] for row in stability(variants).values()),
            "note": "If any anchor is unstable, reader-facing interpretation must mark the affected items as time-sensitive.",
        },
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
