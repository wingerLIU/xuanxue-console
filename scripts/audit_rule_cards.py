#!/usr/bin/env python3
"""Audit runtime rule cards for source provenance and rule-field structure."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_MAP = PROJECT_ROOT / "knowledge" / "knowledge_map.json"
SOURCE_INDEX = PROJECT_ROOT / "knowledge" / "source-index.md"
SOURCE_REGISTER = PROJECT_ROOT / "knowledge" / "sources" / "source-register.json"
RULE_SCHEMA = PROJECT_ROOT / "schemas" / "knowledge_rule.schema.json"
COVERAGE_MATRIX = PROJECT_ROOT / "knowledge" / "completeness" / "coverage-matrix.json"
PROMOTION_MANIFEST = PROJECT_ROOT / "knowledge" / "promotion" / "knowledge_promotion_manifest.json"
SOURCE_ID_RE = re.compile(r"SRC-[A-Z0-9-]+")
SOURCE_ID_HEADER_RE = re.compile(r"^source_id:\s*`?(SRC-[A-Z0-9-]+)`?\s*$", re.MULTILINE)
SECTION_RE = re.compile(r"^##\s+", re.MULTILINE)
RULE_MODULES = {"bazi", "ziwei", "western", "mbti", "liuyao", "xiaoliuren", "writing"}


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


def registered_source_ids(source_register: dict[str, Any]) -> set[str]:
    entries = source_register.get("entries", [])
    if not isinstance(entries, list):
        return set()
    return {str(entry.get("id")) for entry in entries if isinstance(entry, dict) and entry.get("id")}


def source_registered_paths(source_register: dict[str, Any]) -> dict[str, set[str]]:
    paths_by_source: dict[str, set[str]] = {}
    entries = source_register.get("entries", [])
    if not isinstance(entries, list):
        return paths_by_source
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            continue
        paths: set[str] = set()
        for key in ["local_paths", "promotion_targets"]:
            values = entry.get(key, [])
            if isinstance(values, list):
                paths.update(str(value) for value in values if isinstance(value, str))
        paths_by_source[entry["id"]] = paths
    return paths_by_source


def coverage_runtime_files(coverage: dict[str, Any]) -> set[str]:
    files: set[str] = set()
    domains = coverage.get("domains", [])
    if not isinstance(domains, list):
        return files
    for domain in domains:
        if not isinstance(domain, dict):
            continue
        runtime_files = domain.get("runtime_files", [])
        if isinstance(runtime_files, list):
            files.update(str(item) for item in runtime_files if isinstance(item, str))
    return files


def promoted_paths(promotion_manifest: dict[str, Any]) -> set[str]:
    entries = promotion_manifest.get("entries", [])
    if not isinstance(entries, list):
        return set()
    return {str(entry.get("path")) for entry in entries if isinstance(entry, dict) and entry.get("path")}


def runtime_rule_cards(knowledge_map: dict[str, Any], failures: list[str]) -> list[str]:
    modules = knowledge_map.get("modules", {})
    if not isinstance(modules, dict):
        failures.append("knowledge_map modules must be an object")
        return []
    cards: list[str] = []
    for module_id in sorted(RULE_MODULES):
        module = modules.get(module_id)
        if not isinstance(module, dict):
            failures.append(f"knowledge_map missing rule module: {module_id}")
            continue
        files = module.get("files", [])
        if not isinstance(files, list) or not files:
            failures.append(f"knowledge_map module {module_id} files must be a non-empty list")
            continue
        cards.extend(str(item) for item in files if isinstance(item, str) and item.endswith(".md"))
    return sorted(set(cards))


def section_blocks(text: str) -> list[str]:
    starts = [match.start() for match in SECTION_RE.finditer(text)]
    blocks: list[str] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(text)
        blocks.append(text[start:end])
    return blocks


def extract_field_sources(block: str) -> set[str]:
    source_lines = re.findall(r"^-\s+`source`:\s*(.+)$", block, flags=re.MULTILINE)
    sources: set[str] = set()
    for line in source_lines:
        sources.update(SOURCE_ID_RE.findall(line))
    return sources


def audit_structured_rule_blocks(
    path_name: str,
    text: str,
    required_fields: list[str],
    declared_sources: set[str],
    registered_sources: set[str],
    failures: list[str],
) -> int:
    structured_count = 0
    section_index = 0
    for block in section_blocks(text):
        section_index += 1
        if "- `rule`:" not in block:
            continue
        structured_count += 1
        for field in required_fields:
            marker = f"- `{field}`:"
            if marker not in block:
                failures.append(f"{path_name} structured rule section {section_index} missing field: {field}")
        sources = extract_field_sources(block)
        if not sources:
            failures.append(f"{path_name} structured rule section {section_index} has no SRC-* source")
        unknown = sorted(sources - declared_sources)
        if unknown:
            failures.append(f"{path_name} structured rule section {section_index} has undeclared sources: {unknown}")
        unregistered = sorted(sources - registered_sources)
        if unregistered:
            failures.append(f"{path_name} structured rule section {section_index} has unregistered sources: {unregistered}")
    return structured_count


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    knowledge_map = load_json(KNOWLEDGE_MAP, failures)
    source_register = load_json(SOURCE_REGISTER, failures)
    rule_schema = load_json(RULE_SCHEMA, failures)
    coverage = load_json(COVERAGE_MATRIX, failures)
    promotion_manifest = load_json(PROMOTION_MANIFEST, failures)
    declared_sources = declared_source_ids()
    registered_sources = registered_source_ids(source_register)
    registered_paths_by_source = source_registered_paths(source_register)
    coverage_files = coverage_runtime_files(coverage)
    promoted_file_paths = promoted_paths(promotion_manifest)

    required_fields = rule_schema.get("required", [])
    if not isinstance(required_fields, list) or not required_fields:
        failures.append("knowledge rule schema required must be a non-empty list")
        required_fields = ["rule", "source", "scope", "limits", "modern_translation", "report_usage"]
    for field in ["rule", "source", "scope", "limits", "modern_translation", "report_usage"]:
        if field not in required_fields:
            failures.append(f"knowledge rule schema missing required field: {field}")

    cards = runtime_rule_cards(knowledge_map, failures)
    structured_rule_count = 0
    audited_sources: set[str] = set()
    for path_name in cards:
        path = PROJECT_ROOT / path_name
        if not path.exists():
            failures.append(f"runtime rule card missing: {path_name}")
            continue
        if path_name not in coverage_files:
            failures.append(f"runtime rule card not listed in coverage matrix: {path_name}")
        if path_name not in promoted_file_paths:
            failures.append(f"runtime rule card not promoted in promotion manifest: {path_name}")
        text = path.read_text(encoding="utf-8")
        header_match = SOURCE_ID_HEADER_RE.search(text)
        if not header_match:
            failures.append(f"{path_name} missing top-level source_id")
            top_source = ""
        else:
            top_source = header_match.group(1)
            audited_sources.add(top_source)
            if top_source not in declared_sources:
                failures.append(f"{path_name} source_id not declared in source-index: {top_source}")
            if top_source not in registered_sources:
                failures.append(f"{path_name} source_id not registered in source-register: {top_source}")

        used_sources = set(SOURCE_ID_RE.findall(text))
        audited_sources.update(used_sources)
        unknown = sorted(used_sources - declared_sources)
        if unknown:
            failures.append(f"{path_name} references undeclared sources: {unknown}")
        unregistered = sorted(used_sources - registered_sources)
        if unregistered:
            failures.append(f"{path_name} references unregistered sources: {unregistered}")

        linked_sources = [
            source_id
            for source_id, paths in registered_paths_by_source.items()
            if path_name in paths
        ]
        if not linked_sources:
            failures.append(f"{path_name} is not linked by any source-register local_paths or promotion_targets")
        structured_in_file = audit_structured_rule_blocks(
            path_name,
            text,
            [str(item) for item in required_fields],
            declared_sources,
            registered_sources,
            failures,
        )
        structured_rule_count += structured_in_file
        if structured_in_file == 0 and not any(marker in text for marker in ["边界", "禁区", "不得", "limits"]):
            failures.append(f"{path_name} has no structured rule blocks and no boundary language")

    result = {
        "passed": not failures,
        "audited_cards": len(cards),
        "promoted_cards": len(set(cards).intersection(promoted_file_paths)),
        "structured_rules": structured_rule_count,
        "audited_sources": len(audited_sources),
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
