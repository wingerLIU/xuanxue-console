#!/usr/bin/env python3
"""Audit the knowledge promotion manifest as its own provenance gate."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_INDEX = PROJECT_ROOT / "knowledge" / "source-index.md"
PROMOTION_MANIFEST = PROJECT_ROOT / "knowledge" / "promotion" / "knowledge_promotion_manifest.json"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "promotion_manifest.schema.json"
SOURCE_ID_RE = re.compile(r"SRC-[A-Z0-9-]+")

FORBIDDEN_PATTERNS = [
    r"C:\\Users\\",
    r"wxid_",
    r"run_20\d{6}_",
    r"\.jpg\b",
    r"\.jpeg\b",
    r"\.png\b",
    r"\.webp\b",
    r"1992-12-23",
    r"\bWei\b",
]


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def load_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.exists():
        failures.append(f"missing JSON file: {rel(path)}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{rel(path)} invalid JSON: {exc}")
        return {}


def declared_source_ids() -> set[str]:
    if not SOURCE_INDEX.exists():
        return set()
    return set(SOURCE_ID_RE.findall(SOURCE_INDEX.read_text(encoding="utf-8")))


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    schema = load_json(SCHEMA_PATH, failures)
    manifest = load_json(PROMOTION_MANIFEST, failures)
    declared_sources = declared_source_ids()
    if not declared_sources:
        failures.append("source-index declares no source IDs")

    if schema.get("schema_version") != "0.1.0":
        failures.append("promotion manifest schema_version must be 0.1.0")
    if manifest.get("schema_version") != "0.1.0":
        failures.append("promotion manifest schema_version must be 0.1.0")

    for key in schema.get("required_top_level_keys", []):
        if key not in manifest:
            failures.append(f"promotion manifest missing top-level key: {key}")

    policy = manifest.get("policy")
    if not isinstance(policy, str) or not (PROJECT_ROOT / policy).exists():
        failures.append(f"promotion manifest policy missing or invalid: {policy}")

    allowed_statuses = set(schema.get("allowed_statuses", []))
    allowed_types = set(schema.get("allowed_types", []))
    allowed_approval_statuses = set(schema.get("allowed_approval_statuses", []))
    required_entry_keys = list(schema.get("required_entry_keys", []))

    entries = manifest.get("entries", [])
    if not isinstance(entries, list) or not entries:
        failures.append("promotion manifest entries must be a non-empty list")
        entries = []

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            failures.append(f"promotion entry {idx} is not an object")
            continue
        entry_id = str(entry.get("id", ""))
        if not re.match(r"^PROMO-[0-9]{8}-[A-Z0-9-]+$", entry_id):
            failures.append(f"promotion entry id must match PROMO-YYYYMMDD-SLUG: {entry_id or idx}")
        if entry_id in seen_ids:
            failures.append(f"duplicate promotion entry id: {entry_id}")
        seen_ids.add(entry_id)

        missing = [key for key in required_entry_keys if key not in entry]
        if missing:
            failures.append(f"promotion entry {entry_id or idx} missing keys: {missing}")

        if entry.get("status") not in allowed_statuses:
            failures.append(f"{entry_id} invalid status: {entry.get('status')}")
        if entry.get("type") not in allowed_types:
            failures.append(f"{entry_id} invalid type: {entry.get('type')}")
        if entry.get("approval_status") not in allowed_approval_statuses:
            failures.append(f"{entry_id} invalid approval_status: {entry.get('approval_status')}")
        if entry.get("status") in {"curated", "verified"} and entry.get("human_approved") is not True:
            failures.append(f"{entry_id} curated/verified entries require human_approved=true")

        path_name = entry.get("path")
        if not isinstance(path_name, str) or not path_name.strip():
            failures.append(f"{entry_id} path must be a non-empty string")
        else:
            if Path(path_name).is_absolute() or ".." in Path(path_name).parts:
                failures.append(f"{entry_id} path must be project-relative and normalized: {path_name}")
            elif not (PROJECT_ROOT / path_name).exists():
                failures.append(f"{entry_id} path missing: {path_name}")
            seen_paths.add(path_name)

        source_ids = entry.get("source_ids", [])
        if not isinstance(source_ids, list) or not source_ids:
            failures.append(f"{entry_id} source_ids must be a non-empty list")
        else:
            unknown = sorted(set(str(item) for item in source_ids) - declared_sources)
            if unknown:
                failures.append(f"{entry_id} references unknown source_ids: {unknown}")

        notes = entry.get("notes")
        if not isinstance(notes, str) or len(notes.strip()) < 12:
            failures.append(f"{entry_id} notes must be a meaningful string")

        serialized = json.dumps(entry, ensure_ascii=False)
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, serialized, flags=re.IGNORECASE):
                failures.append(f"{entry_id} contains forbidden private/case pattern: {pattern}")

    for required_path in [
        "knowledge/sources/source-register.json",
        "knowledge/completeness/coverage-matrix.json",
        "knowledge/completeness/retrospective-requirements.json",
        "scripts/audit_knowledge_coverage.py",
        "scripts/audit_rule_cards.py",
        "scripts/audit_source_documentation.py",
        "scripts/build_knowledge_context.py",
        "scripts/check_source_urls.py",
        "scripts/create_case_retrospective_candidate.py",
        "scripts/promote_case_retrospective.py",
        "scripts/audit_case_retrospectives.py",
        "scripts/validate_longform_report.py",
        "scripts/audit_longform_consistency.py",
        "schemas/case_retrospective.schema.json",
    ]:
        if required_path not in seen_paths:
            failures.append(f"promotion manifest missing required promoted path: {required_path}")

    result = {
        "passed": not failures,
        "entries": len(entries),
        "declared_sources": len(declared_sources),
        "promoted_paths": len(seen_paths),
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
