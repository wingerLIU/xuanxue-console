#!/usr/bin/env python3
"""Audit deidentified case retrospectives before they can influence knowledge."""

from __future__ import annotations

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RETRO_DIR = PROJECT_ROOT / "knowledge" / "case-retrospectives"

REQUIRED_KEYS = [
    "schema_version",
    "id",
    "title",
    "status",
    "human_approved",
    "privacy",
    "source_case",
    "evidence_summary",
    "domains",
    "target_artifacts",
    "promotions",
    "counterexamples",
    "limits",
]

ALLOWED_DOMAINS = {
    "bazi",
    "ziwei",
    "western",
    "mbti",
    "liuyao",
    "xiaoliuren",
    "writing",
    "relationship",
    "team_career",
    "fengshui",
    "source_register",
    "quality",
    "case_retrospectives",
    "completeness",
}

FORBIDDEN_PATTERNS = [
    r"C:\\Users\\",
    r"wxid_",
    r"run_20\d{6}_",
    r"\.jpg\b",
    r"\.jpeg\b",
    r"\.png\b",
    r"\.webp\b",
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
    r"\b\d{1,2}:\d{2}\b",
]


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit deidentified case retrospectives.")
    parser.add_argument("--retro-dir", default=str(DEFAULT_RETRO_DIR), help=argparse.SUPPRESS)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_text_privacy(path: Path, failures: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            failures.append(f"{rel(path)} contains forbidden private/case pattern: {pattern}")


def main() -> int:
    args = parse_args()
    retro_dir = Path(args.retro_dir).resolve()
    failures: list[str] = []
    warnings: list[str] = []
    required_files = [
        retro_dir / "README.md",
        retro_dir / "promotion-protocol.md",
        retro_dir / "template.md",
        PROJECT_ROOT / "schemas" / "case_retrospective.schema.json",
    ]

    for path in required_files:
        if not path.exists():
            failures.append(f"missing case-retrospective control file: {rel(path)}")
        elif path.stat().st_size < 80:
            failures.append(f"case-retrospective control file too small: {rel(path)}")

    schema_path = PROJECT_ROOT / "schemas" / "case_retrospective.schema.json"
    if schema_path.exists():
        try:
            schema = load_json(schema_path)
        except json.JSONDecodeError as exc:
            failures.append(f"case retrospective schema invalid JSON: {exc}")
            schema = {}
        if schema.get("schema_version") != "0.1.0":
            failures.append("case retrospective schema_version must be 0.1.0")

    for path in retro_dir.glob("*.md"):
        check_text_privacy(path, failures)

    retrospectives = sorted(path for path in retro_dir.glob("*.json"))
    candidate_files: list[str] = []
    for path in retrospectives:
        try:
            item = load_json(path)
        except json.JSONDecodeError as exc:
            failures.append(f"{rel(path)} invalid JSON: {exc}")
            continue

        missing = [key for key in REQUIRED_KEYS if key not in item]
        if missing:
            failures.append(f"{rel(path)} missing keys: {missing}")
            continue

        if item.get("schema_version") != "0.1.0":
            failures.append(f"{rel(path)} schema_version must be 0.1.0")
        if not re.match(r"^CR-[0-9]{8}-[a-z0-9-]+$", str(item.get("id", ""))):
            failures.append(f"{rel(path)} id must match CR-YYYYMMDD-slug")
        if item.get("status") not in {"curated", "verified"}:
            failures.append(
                f"{rel(path)} invalid status for global retrospective: {item.get('status')}; "
                "candidate files must stay in external run folders"
            )
            if item.get("status") == "candidate":
                candidate_files.append(path.name)
        if item.get("human_approved") is not True:
            failures.append(f"{rel(path)} must have human_approved=true before entering knowledge")

        privacy = item.get("privacy")
        if not isinstance(privacy, dict):
            failures.append(f"{rel(path)} privacy must be an object")
        else:
            expected = {
                "deidentified": True,
                "contains_birth_data": False,
                "contains_client_name": False,
                "contains_local_paths": False,
                "contains_delivery_text": False,
            }
            for key, expected_value in expected.items():
                if privacy.get(key) is not expected_value:
                    failures.append(f"{rel(path)} privacy.{key} must be {expected_value}")

        for key in ["domains", "target_artifacts", "promotions", "counterexamples", "limits"]:
            value = item.get(key)
            if not isinstance(value, list) or not value:
                failures.append(f"{rel(path)} {key} must be a non-empty list")
        domains = item.get("domains", [])
        if isinstance(domains, list):
            unknown = sorted(set(str(domain) for domain in domains) - ALLOWED_DOMAINS)
            if unknown:
                failures.append(f"{rel(path)} domains contain unknown values: {unknown}")

        serialized = json.dumps(item, ensure_ascii=False)
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, serialized, flags=re.IGNORECASE):
                failures.append(f"{rel(path)} contains forbidden private/case pattern: {pattern}")

    run_local_candidate_hint = ""
    if candidate_files:
        run_local_candidate_hint = (
            "This audit is for promoted global retrospectives. Run-local candidate files should stay external; "
            "validate them with create_retrospective_intake.py and promote_case_retrospective.py --dry-run."
        )

    result = {
        "passed": not failures,
        "retrospective_files": len(retrospectives),
        "candidate_files": candidate_files,
        "run_local_candidate_hint": run_local_candidate_hint,
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
