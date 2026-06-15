#!/usr/bin/env python3
"""Build a per-case knowledge context manifest from the reusable knowledge base."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_MAP = PROJECT_ROOT / "knowledge" / "knowledge_map.json"
SOURCE_REGISTER = PROJECT_ROOT / "knowledge" / "sources" / "source-register.json"
COVERAGE_MATRIX = PROJECT_ROOT / "knowledge" / "completeness" / "coverage-matrix.json"
RETRO_REQUIREMENTS = PROJECT_ROOT / "knowledge" / "completeness" / "retrospective-requirements.json"
RETRO_DIR = PROJECT_ROOT / "knowledge" / "case-retrospectives"

COMBO_MODULES = ["bazi", "ziwei", "western", "mbti", "liuyao", "xiaoliuren"]
ALWAYS_CONTEXT_MODULES = ["writing", "source_register", "completeness"]
TARGET_ARTIFACT_PRIORITIES = {
    "bazi": [
        "knowledge/bazi/foundations.md",
        "knowledge/bazi/classical-anchors.md",
        "knowledge/bazi/ten-gods.md",
        "knowledge/bazi/structure-and-flow.md",
        "knowledge/bazi/shenfeng-methods.md",
    ],
    "ziwei": [
        "knowledge/ziwei/foundations.md",
        "knowledge/ziwei/classical-anchors.md",
        "knowledge/ziwei/palaces-stars-four-transformations.md",
        "knowledge/ziwei/quanshu-vs-quanji-boundary.md",
    ],
    "western": [
        "knowledge/western/foundations.md",
        "knowledge/western/classical-anchors.md",
        "knowledge/western/modern-psychological.md",
        "knowledge/western/planets-aspects-houses.md",
    ],
    "mbti": [
        "knowledge/mbti/behavior-language.md",
    ],
    "liuyao": [
        "knowledge/liuyao/question-reading.md",
        "knowledge/liuyao/classical-anchors.md",
    ],
    "xiaoliuren": [
        "knowledge/xiaoliuren/quick-timing.md",
        "knowledge/xiaoliuren/classical-anchors.md",
    ],
    "writing": [
        "knowledge/writing/reader-rich-report.md",
        "templates/longform-analysis-template.md",
        "references/interpretation-guide.md",
        "scripts/validate_longform_report.py",
        "scripts/audit_longform_consistency.py",
    ],
    "relationship": [
        "templates/relationship-rich-template.md",
        "templates/relationship-concise-template.md",
        "scripts/build_relationship_facts.py",
        "scripts/create_relationship_workspace.py",
        "scripts/validate_relationship_report.py",
        "scripts/create_followup_context.py",
        "scripts/package_mobile_html.py",
    ],
    "source_register": [
        "knowledge/sources/source-register.json",
        "knowledge/sources/online-classics.md",
        "knowledge/source-index.md",
        "knowledge/rules/research-and-promotion.md",
        "scripts/check_source_urls.py",
    ],
    "case_retrospectives": [
        "knowledge/case-retrospectives/promotion-protocol.md",
        "knowledge/case-retrospectives/template.md",
        "schemas/case_retrospective.schema.json",
        "scripts/create_case_retrospective_candidate.py",
        "scripts/promote_case_retrospective.py",
    ],
    "completeness": [
        "knowledge/completeness/retrospective-requirements.json",
        "knowledge/completeness/coverage-matrix.json",
        "scripts/audit_knowledge_coverage.py",
    ],
    "quality": [
        "service/quality-gate.md",
        "scripts/validate_longform_report.py",
        "scripts/audit_longform_consistency.py",
        "scripts/audit_project_hygiene.py",
    ],
}
GLOBAL_RETROSPECTIVE_DOMAINS = ["writing", "case_retrospectives", "completeness", "source_register"]
GLOBAL_RETROSPECTIVE_TARGET_PRIORITIES = [
    "knowledge/writing/reader-rich-report.md",
    "knowledge/case-retrospectives/promotion-protocol.md",
    "knowledge/completeness/retrospective-requirements.json",
    "knowledge/sources/source-register.json",
    "knowledge/source-index.md",
    "knowledge/rules/research-and-promotion.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a knowledge context manifest for a xuanxue case.")
    parser.add_argument("--module", action="append", default=[], help="Module to include. Can repeat. Use combo for all domains.")
    parser.add_argument("--manifest", help="External case_manifest.json; output defaults to <runtime_dir>/knowledge_context.json.")
    parser.add_argument("--output", help="Output JSON path. Defaults to stdout, or manifest runtime_dir.")
    parser.add_argument("--no-default-writing", action="store_true", help="Do not add writing/source/completeness modules automatically.")
    parser.add_argument("--retro-dir", help=argparse.SUPPRESS)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def normalize_modules(raw_modules: list[str], known_modules: set[str], include_defaults: bool) -> list[str]:
    modules: list[str] = []
    for item in raw_modules:
        for part in item.split(","):
            value = part.strip()
            if not value:
                continue
            if value == "combo":
                modules.extend(COMBO_MODULES)
            else:
                modules.append(value)
    if not modules:
        modules = ["bazi", "ziwei", "western"]
    if include_defaults:
        modules.extend(ALWAYS_CONTEXT_MODULES)
    seen: set[str] = set()
    result: list[str] = []
    for module in modules:
        if module in seen:
            continue
        if module not in known_modules:
            raise SystemExit(f"unknown knowledge module: {module}")
        seen.add(module)
        result.append(module)
    return result


def source_entries_by_id(register: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = register.get("entries", [])
    if not isinstance(entries, list):
        raise SystemExit("source-register entries must be a list")
    return {str(entry.get("id")): entry for entry in entries if isinstance(entry, dict) and entry.get("id")}


def coverage_by_id(coverage: dict[str, Any]) -> dict[str, dict[str, Any]]:
    domains = coverage.get("domains", [])
    if not isinstance(domains, list):
        raise SystemExit("coverage domains must be a list")
    return {str(domain.get("id")): domain for domain in domains if isinstance(domain, dict) and domain.get("id")}


def retrospective_items(retro_dir: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(retro_dir.glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def count_retrospectives(items: list[dict[str, Any]], domain: str, min_status: str, status_rank: dict[str, int]) -> int:
    min_rank = status_rank.get(min_status, 999)
    count = 0
    for item in items:
        if item.get("human_approved") is not True:
            continue
        if status_rank.get(str(item.get("status", "")), -1) < min_rank:
            continue
        domains = item.get("domains", [])
        if domain == "*" or (isinstance(domains, list) and domain in domains):
            count += 1
    return count


def module_files(domain: str, modules_map: dict[str, Any]) -> list[str]:
    module = modules_map.get(domain, {})
    if not isinstance(module, dict):
        return []
    files = module.get("files", [])
    if not isinstance(files, list):
        return []
    return [str(item).replace("\\", "/") for item in files if isinstance(item, str)]


def existing_project_artifacts(paths: list[str], limit: int = 6) -> list[str]:
    result: list[str] = []
    for item in paths:
        normalized = item.replace("\\", "/")
        if normalized in result:
            continue
        if (PROJECT_ROOT / normalized).exists():
            result.append(normalized)
        if len(result) >= limit:
            break
    return result


def suggested_target_artifacts(domain: str, modules_map: dict[str, Any]) -> list[str]:
    if domain == "*":
        candidates: list[str] = [*GLOBAL_RETROSPECTIVE_TARGET_PRIORITIES]
        for item in GLOBAL_RETROSPECTIVE_DOMAINS:
            candidates.extend(TARGET_ARTIFACT_PRIORITIES.get(item, []))
            candidates.extend(module_files(item, modules_map))
        return existing_project_artifacts(candidates)

    candidates = [*TARGET_ARTIFACT_PRIORITIES.get(domain, []), *module_files(domain, modules_map)]
    return existing_project_artifacts(candidates)


def retrospective_candidate_command(domain: str, target_artifact: str) -> str:
    command_domain = domain if domain != "*" else "writing"
    return (
        "python scripts/create_case_retrospective_candidate.py "
        "--manifest <RUN_DIR>/case_manifest.json "
        f"--domain {command_domain} "
        "--slug <deidentified-slug> "
        "--title \"去隐私复盘标题\" "
        "--evidence-summary \"只写抽象证据\" "
        f"--target-artifact {target_artifact}"
    )


def retrospective_context(
    selected_modules: list[str], modules_map: dict[str, Any], retro_dir: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data = load_json(RETRO_REQUIREMENTS)
    status_rank = data.get("status_rank", {})
    if not isinstance(status_rank, dict):
        status_rank = {}
    requirements = data.get("requirements", [])
    if not isinstance(requirements, list):
        requirements = []
    items = retrospective_items(retro_dir)
    selected_domains = set(selected_modules) | {"*"}
    selected: list[dict[str, Any]] = []
    collection_plan: list[dict[str, Any]] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        domain = str(requirement.get("domain", ""))
        if domain not in selected_domains:
            continue
        min_entries = int(requirement.get("min_entries", 1))
        min_status = str(requirement.get("min_status", "curated"))
        current = count_retrospectives(items, domain, min_status, status_rank)
        needed = max(0, min_entries - current)
        row = {
            "id": requirement.get("id"),
            "domain": domain,
            "gap_id": requirement.get("gap_id"),
            "min_entries": min_entries,
            "min_status": min_status,
            "current_entries": current,
            "needed_entries": needed,
            "satisfied": needed == 0,
            "rationale": requirement.get("rationale"),
        }
        selected.append(row)
        if needed:
            targets = suggested_target_artifacts(domain, modules_map)
            command_targets = targets or ["<project-relative-artifact>"]
            collection_plan.append(
                {
                    "domain": domain,
                    "needed_entries": needed,
                    "suggested_target_artifacts": targets,
                    "evidence_to_collect": [
                        "读者明确反馈：哪一段准、哪一段不准、为什么。",
                        "至少一个反例或适用限制。",
                        "要改进的 target_artifacts，例如规则卡、写作模板、校验脚本或 SOP。",
                        "只保留抽象机制，不保留姓名、出生资料、截图路径、报告原文或本机路径。",
                    ],
                    "candidate_command": retrospective_candidate_command(domain, command_targets[0]),
                    "candidate_commands": [
                        retrospective_candidate_command(domain, target) for target in command_targets[:3]
                    ],
                }
            )
    return selected, collection_plan


def resolve_output(args: argparse.Namespace) -> tuple[Path | None, dict[str, Any] | None]:
    if args.output:
        output = Path(args.output).resolve()
        if is_relative_to(output, PROJECT_ROOT):
            raise SystemExit("knowledge context output must not be inside the project repo")
        return output, None
    if args.manifest:
        manifest_path = Path(args.manifest).resolve()
        manifest = load_json(manifest_path)
        runtime_dir = Path(manifest.get("paths", {}).get("runtime_dir", "")).resolve()
        if not runtime_dir.exists():
            raise SystemExit(f"runtime_dir missing or invalid in manifest: {runtime_dir}")
        if is_relative_to(runtime_dir, PROJECT_ROOT):
            raise SystemExit("runtime_dir must not be inside the project repo")
        return runtime_dir / "knowledge_context.json", manifest
    return None, None


def main() -> int:
    args = parse_args()
    knowledge_map = load_json(KNOWLEDGE_MAP)
    source_register = load_json(SOURCE_REGISTER)
    coverage = load_json(COVERAGE_MATRIX)
    modules_map = knowledge_map.get("modules", {})
    if not isinstance(modules_map, dict):
        raise SystemExit("knowledge_map.modules must be an object")

    modules = normalize_modules(args.module, set(modules_map), include_defaults=not args.no_default_writing)
    source_by_id = source_entries_by_id(source_register)
    coverage_domains = coverage_by_id(coverage)

    file_paths: list[str] = []
    for file_name in knowledge_map.get("always_read", []):
        if isinstance(file_name, str):
            file_paths.append(file_name)
    for module in modules:
        module_files = modules_map.get(module, {}).get("files", [])
        if isinstance(module_files, list):
            file_paths.extend(str(item) for item in module_files)
    deduped_files: list[str] = []
    for file_name in file_paths:
        if file_name not in deduped_files:
            deduped_files.append(file_name)

    selected_source_ids: list[str] = []
    selected_blockers: list[dict[str, Any]] = []
    for module in modules:
        domain = coverage_domains.get(module, {})
        for source_id in domain.get("source_ids", []):
            if isinstance(source_id, str) and source_id not in selected_source_ids:
                selected_source_ids.append(source_id)
        for gap in domain.get("remaining_gaps", []):
            if isinstance(gap, dict) and gap.get("blocks_goal_completion") is True:
                selected_blockers.append({"domain": module, **gap})
    retro_dir = Path(args.retro_dir).resolve() if args.retro_dir else RETRO_DIR
    selected_retro_requirements, retro_collection_plan = retrospective_context(modules, modules_map, retro_dir)

    files = [
        {
            "path": file_name,
            "exists": (PROJECT_ROOT / file_name).exists(),
            "absolute_path": str((PROJECT_ROOT / file_name).resolve()),
        }
        for file_name in deduped_files
    ]
    missing_files = [item["path"] for item in files if not item["exists"]]
    source_entries = []
    missing_sources = []
    for source_id in selected_source_ids:
        entry = source_by_id.get(source_id)
        if not entry:
            missing_sources.append(source_id)
            continue
        source_entries.append(
            {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "type": entry.get("type"),
                "status": entry.get("status"),
                "evidence_mode": entry.get("evidence_mode"),
                "used_for": entry.get("used_for"),
                "limits": entry.get("limits"),
            }
        )

    output_path, manifest = resolve_output(args)
    result = {
        "schema_version": "0.1.0",
        "selected_modules": modules,
        "case_id": manifest.get("case_id") if manifest else None,
        "run_id": manifest.get("run_id") if manifest else None,
        "knowledge_files": files,
        "source_ids": selected_source_ids,
        "source_entries": source_entries,
        "goal_completion_blockers": selected_blockers,
        "retrospective_requirements": selected_retro_requirements,
        "retrospective_collection_plan": retro_collection_plan,
        "global_blockers": coverage.get("global_blockers", []),
        "usage_rules": [
            "Read every knowledge_files entry before producing paid longform analysis.",
            "Reader-rich is the default paid delivery; concise reports are add-ons and must not replace rich unless the user explicitly requests short-only delivery.",
            "Missing Ziwei, Western, MBTI or divination inputs should narrow the evidence scope of the rich report, not skip it; write a single-system or available-systems rich report with clear limits.",
            "Use source_entries as provenance boundaries, not as client-facing quotations.",
            "Do not use random web pages directly in a client report.",
            "New online classics must enter source-register, online-classics and promoted rule cards before report use.",
            "Case feedback must enter via external retrospectives candidate and human approval.",
        ],
        "passed": not missing_files and not missing_sources,
        "failures": [
            *(f"missing knowledge file: {item}" for item in missing_files),
            *(f"missing source register entry: {item}" for item in missing_sources),
        ],
    }

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(json.dumps({"passed": result["passed"], "output": str(output_path)}, ensure_ascii=False, indent=2))
    else:
        print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
