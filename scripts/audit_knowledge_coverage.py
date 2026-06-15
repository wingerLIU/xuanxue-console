#!/usr/bin/env python3
"""Audit the knowledge coverage matrix and goal-completion blockers."""

from __future__ import annotations

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PATH = PROJECT_ROOT / "knowledge" / "completeness" / "coverage-matrix.json"
RETRO_REQUIREMENTS_PATH = PROJECT_ROOT / "knowledge" / "completeness" / "retrospective-requirements.json"
KNOWLEDGE_MAP_PATH = PROJECT_ROOT / "knowledge" / "knowledge_map.json"
SOURCE_REGISTER_PATH = PROJECT_ROOT / "knowledge" / "sources" / "source-register.json"
SOURCE_INDEX_PATH = PROJECT_ROOT / "knowledge" / "source-index.md"
RETRO_DIR = PROJECT_ROOT / "knowledge" / "case-retrospectives"
SOURCE_ID_RE = re.compile(r"SRC-[A-Z0-9-]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the knowledge coverage matrix and goal-completion blockers.")
    parser.add_argument(
        "--retro-dir",
        default=str(RETRO_DIR),
        help="Retrospective directory to count. Defaults to knowledge/case-retrospectives; use a temp dir for approval previews.",
    )
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


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
    if not SOURCE_INDEX_PATH.exists():
        return set()
    return set(SOURCE_ID_RE.findall(SOURCE_INDEX_PATH.read_text(encoding="utf-8")))


def retrospective_domain_counts(retro_dir: Path, failures: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in sorted(retro_dir.glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            failures.append(f"{rel(path)} invalid JSON while counting domains: {exc}")
            continue
        if item.get("human_approved") is not True:
            continue
        domains = item.get("domains", [])
        if not isinstance(domains, list):
            failures.append(f"{rel(path)} domains must be a list")
            continue
        for domain in domains:
            key = str(domain)
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def load_retrospective_items(retro_dir: Path, failures: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(retro_dir.glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            failures.append(f"{rel(path)} invalid JSON while loading retrospective requirements: {exc}")
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def required_registered_sources_for_domain(
    source_register: dict[str, Any],
    domain_id: str,
    runtime_files: list[str],
) -> list[str]:
    entries = source_register.get("entries", [])
    if not isinstance(entries, list):
        return []
    runtime_file_set = set(runtime_files)
    required: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source_id = entry.get("id")
        domains = entry.get("domains", [])
        if not isinstance(source_id, str) or not isinstance(domains, list) or domain_id not in domains:
            continue
        paths: set[str] = set()
        for key in ["promotion_targets", "local_paths"]:
            values = entry.get(key, [])
            if isinstance(values, list):
                paths.update(str(value) for value in values)
        if paths.intersection(runtime_file_set):
            required.add(source_id)
    return sorted(required)


def count_retrospectives_for_requirement(
    items: list[dict[str, Any]],
    requirement: dict[str, Any],
    status_rank: dict[str, int],
) -> int:
    domain = str(requirement.get("domain", ""))
    min_status = str(requirement.get("min_status", "curated"))
    min_rank = status_rank.get(min_status, 999)
    count = 0
    for item in items:
        if item.get("human_approved") is not True:
            continue
        status = str(item.get("status", ""))
        if status_rank.get(status, -1) < min_rank:
            continue
        domains = item.get("domains", [])
        if domain == "*" or (isinstance(domains, list) and domain in domains):
            count += 1
    return count


def evaluate_retrospective_requirements(
    requirements_data: dict[str, Any],
    goal_completion_blockers: list[str],
    retro_dir: Path,
    failures: list[str],
    warnings: list[str],
) -> list[dict[str, Any]]:
    if requirements_data.get("schema_version") != "0.1.0":
        failures.append("retrospective requirements schema_version must be 0.1.0")
    status_rank = requirements_data.get("status_rank", {})
    if not isinstance(status_rank, dict) or not status_rank:
        failures.append("retrospective requirements status_rank must be a non-empty object")
        status_rank = {}
    requirements = requirements_data.get("requirements", [])
    if not isinstance(requirements, list) or not requirements:
        failures.append("retrospective requirements must be a non-empty list")
        requirements = []

    items = load_retrospective_items(retro_dir, failures)
    blocker_set = set(goal_completion_blockers)
    results: list[dict[str, Any]] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            failures.append("retrospective requirement entries must be objects")
            continue
        for key in ["id", "domain", "gap_id", "min_entries", "min_status", "rationale"]:
            if key not in requirement:
                failures.append(f"retrospective requirement missing {key}: {requirement.get('id', '<missing-id>')}")
        req_id = str(requirement.get("id", "<missing-id>"))
        gap_id = str(requirement.get("gap_id", ""))
        min_entries = requirement.get("min_entries", 0)
        if not isinstance(min_entries, int) or min_entries < 1:
            failures.append(f"{req_id} min_entries must be a positive integer")
            min_entries = 1
        min_status = str(requirement.get("min_status", ""))
        if min_status not in status_rank:
            failures.append(f"{req_id} min_status not in status_rank: {min_status}")
        current = count_retrospectives_for_requirement(items, requirement, status_rank)
        satisfied = current >= min_entries
        results.append(
            {
                "id": req_id,
                "domain": requirement.get("domain"),
                "gap_id": gap_id,
                "min_entries": min_entries,
                "min_status": min_status,
                "current_entries": current,
                "satisfied": satisfied,
            }
        )
        if not satisfied and gap_id not in blocker_set:
            failures.append(f"{req_id} is unsatisfied but its blocker is not open: {gap_id}")
        if satisfied and gap_id in blocker_set:
            warnings.append(f"{req_id} appears satisfied but blocker remains open: {gap_id}")
    return results


def retrospective_next_actions(requirement_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return human-actionable steps for unsatisfied retrospective blockers.

    These are intentionally templates. The audit can point to the required
    workflow, but it must not synthesize evidence or silently promote a
    retrospective on its own.
    """

    actions: list[dict[str, Any]] = []
    for item in requirement_results:
        if item.get("satisfied") is True:
            continue
        min_entries = int(item.get("min_entries", 0) or 0)
        current_entries = int(item.get("current_entries", 0) or 0)
        needed_entries = max(0, min_entries - current_entries)
        domain = str(item.get("domain", ""))
        command_domain = "<DOMAIN>" if domain == "*" else domain
        actions.append(
            {
                "type": "promote_human_approved_retrospective",
                "requirement_id": item.get("id"),
                "domain": item.get("domain"),
                "gap_id": item.get("gap_id"),
                "needed_entries": needed_entries,
                "min_status": item.get("min_status"),
                "human_approval_required": True,
                "do_not_create_synthetic_retrospectives": True,
                "evidence_rule": (
                    "Only deidentified run-local candidate retrospectives promoted after "
                    "human approval count toward knowledge completion."
                ),
                "commands": [
                    "python scripts/create_retrospective_intake.py --manifest <RUN_DIR>\\case_manifest.json",
                    (
                        "python scripts/create_case_retrospective_candidate.py "
                        "--manifest <RUN_DIR>\\case_manifest.json "
                        "--slug <short-ascii-slug> "
                        "--title <deidentified-retrospective-title> "
                        f"--domain {command_domain} "
                        "--evidence-summary <deidentified-evidence-summary> "
                        "--target-artifact <project/artifact/path>"
                    ),
                    (
                        "python scripts/promote_case_retrospective.py "
                        "--candidate <RUN_DIR>\\retrospectives\\CR-YYYYMMDD-<slug>.candidate.json "
                        "--approved-by <APPROVER> --dry-run"
                    ),
                    (
                        "python scripts/promote_case_retrospective.py "
                        "--candidate <RUN_DIR>\\retrospectives\\CR-YYYYMMDD-<slug>.candidate.json "
                        "--approved-by <APPROVER>"
                    ),
                    "python scripts/audit_case_retrospectives.py",
                    "python scripts/audit_knowledge_coverage.py",
                ],
            }
        )
    return actions


def validate_domain(
    domain: dict[str, Any],
    declared_sources: set[str],
    source_register: dict[str, Any],
    failures: list[str],
    warnings: list[str],
) -> list[str]:
    blockers: list[str] = []
    domain_id = str(domain.get("id", "<missing-id>"))
    for key in ["id", "status", "runtime_files", "source_ids", "claim_levels", "remaining_gaps"]:
        if key not in domain:
            failures.append(f"coverage domain {domain_id} missing {key}")

    runtime_files = domain.get("runtime_files", [])
    if not isinstance(runtime_files, list) or not runtime_files:
        failures.append(f"coverage domain {domain_id} runtime_files must be a non-empty list")
    else:
        for file_name in runtime_files:
            if not isinstance(file_name, str):
                failures.append(f"coverage domain {domain_id} has non-string runtime file")
                continue
            if not (PROJECT_ROOT / file_name).exists():
                failures.append(f"coverage domain {domain_id} missing runtime file: {file_name}")

    source_ids = domain.get("source_ids", [])
    if not isinstance(source_ids, list) or not source_ids:
        failures.append(f"coverage domain {domain_id} source_ids must be a non-empty list")
    else:
        unknown = sorted(set(str(item) for item in source_ids) - declared_sources)
        if unknown:
            failures.append(f"coverage domain {domain_id} references unknown source IDs: {unknown}")
        if isinstance(runtime_files, list):
            required_sources = required_registered_sources_for_domain(
                source_register,
                domain_id,
                [str(item) for item in runtime_files if isinstance(item, str)],
            )
            missing_registered_sources = sorted(set(required_sources) - set(str(item) for item in source_ids))
            if missing_registered_sources:
                failures.append(
                    f"coverage domain {domain_id} missing source-register-linked IDs: {missing_registered_sources}"
                )

    claim_levels = domain.get("claim_levels", [])
    if not isinstance(claim_levels, list) or not claim_levels:
        failures.append(f"coverage domain {domain_id} claim_levels must be a non-empty list")

    gaps = domain.get("remaining_gaps", [])
    if not isinstance(gaps, list):
        failures.append(f"coverage domain {domain_id} remaining_gaps must be a list")
    else:
        if not gaps:
            warnings.append(f"coverage domain {domain_id} has no remaining_gaps entries")
        for gap in gaps:
            if not isinstance(gap, dict):
                failures.append(f"coverage domain {domain_id} has non-object gap")
                continue
            for key in ["id", "description", "blocks_goal_completion", "blocked_by"]:
                if key not in gap:
                    failures.append(f"coverage domain {domain_id} gap missing {key}")
            if gap.get("blocks_goal_completion") is True:
                blockers.append(str(gap.get("id", "<missing-gap-id>")))
    return blockers


def main() -> int:
    args = parse_args()
    retro_dir = Path(args.retro_dir).resolve()
    failures: list[str] = []
    warnings: list[str] = []

    coverage = load_json(COVERAGE_PATH, failures)
    retrospective_requirements = load_json(RETRO_REQUIREMENTS_PATH, failures)
    knowledge_map = load_json(KNOWLEDGE_MAP_PATH, failures)
    source_register = load_json(SOURCE_REGISTER_PATH, failures)
    declared_sources = declared_source_ids()
    if not declared_sources:
        failures.append("source-index declares no source IDs")

    if coverage.get("schema_version") != "0.1.0":
        failures.append("coverage matrix schema_version must be 0.1.0")

    for key in ["purpose", "goal_complete", "completion_rule", "domains", "global_blockers"]:
        if key not in coverage:
            failures.append(f"coverage matrix missing {key}")

    completion_rule = coverage.get("completion_rule", {})
    if not isinstance(completion_rule, dict):
        failures.append("coverage completion_rule must be an object")
    else:
        required_audits = completion_rule.get("required_audits", [])
        if not isinstance(required_audits, list) or "scripts/audit_knowledge_coverage.py" not in required_audits:
            failures.append("coverage completion_rule must include scripts/audit_knowledge_coverage.py")
        if completion_rule.get("goal_complete_requires_no_blockers") is not True:
            failures.append("coverage completion_rule.goal_complete_requires_no_blockers must be true")

    domains = coverage.get("domains", [])
    if not isinstance(domains, list) or not domains:
        failures.append("coverage domains must be a non-empty list")
        domain_by_id: dict[str, dict[str, Any]] = {}
    else:
        domain_by_id = {}
        for domain in domains:
            if not isinstance(domain, dict):
                failures.append("coverage domains must contain only objects")
                continue
            domain_id = str(domain.get("id", ""))
            if not domain_id:
                failures.append("coverage domain missing id")
                continue
            if domain_id in domain_by_id:
                failures.append(f"duplicate coverage domain id: {domain_id}")
            domain_by_id[domain_id] = domain

    domain_blockers: list[str] = []
    for domain in domain_by_id.values():
        domain_blockers.extend(validate_domain(domain, declared_sources, source_register, failures, warnings))

    modules = knowledge_map.get("modules", {})
    if not isinstance(modules, dict) or not modules:
        failures.append("knowledge map has no modules")
    else:
        for module_id, module in modules.items():
            coverage_domain = domain_by_id.get(module_id)
            if coverage_domain is None:
                failures.append(f"knowledge map module missing coverage domain: {module_id}")
                continue
            map_files = set(module.get("files", [])) if isinstance(module, dict) else set()
            coverage_files = set(coverage_domain.get("runtime_files", []))
            missing = sorted(map_files - coverage_files)
            if missing:
                failures.append(f"coverage domain {module_id} missing knowledge_map files: {missing}")

    global_blockers = coverage.get("global_blockers", [])
    if not isinstance(global_blockers, list):
        failures.append("coverage global_blockers must be a list")
        global_blocker_ids: list[str] = []
    else:
        global_blocker_ids = []
        for blocker in global_blockers:
            if not isinstance(blocker, dict):
                failures.append("coverage global_blockers contains non-object entry")
                continue
            for key in ["id", "description", "blocks_goal_completion", "required_evidence"]:
                if key not in blocker:
                    failures.append(f"global blocker missing {key}")
            if blocker.get("blocks_goal_completion") is True:
                global_blocker_ids.append(str(blocker.get("id", "<missing-blocker-id>")))

    retrospective_files = sorted(path for path in retro_dir.glob("*.json"))
    retro_domain_counts = retrospective_domain_counts(retro_dir, failures)
    if not retrospective_files and "GAP-CASE-RETROSPECTIVES-VERIFIED" not in global_blocker_ids:
        failures.append("zero retrospective JSON files requires GAP-CASE-RETROSPECTIVES-VERIFIED global blocker")

    goal_completion_blockers = sorted(set(domain_blockers + global_blocker_ids))
    retrospective_requirement_results = evaluate_retrospective_requirements(
        retrospective_requirements,
        goal_completion_blockers,
        retro_dir,
        failures,
        warnings,
    )
    goal_complete_expected = not goal_completion_blockers
    if coverage.get("goal_complete") is not goal_complete_expected:
        failures.append(
            "coverage goal_complete must match blocker state: "
            f"expected {goal_complete_expected}, got {coverage.get('goal_complete')}"
        )

    result = {
        "passed": not failures,
        "goal_complete": goal_complete_expected,
        "domains": sorted(domain_by_id),
        "declared_sources": len(declared_sources),
        "retrospective_dir": str(retro_dir),
        "retrospective_files": len(retrospective_files),
        "retrospective_domain_counts": retro_domain_counts,
        "retrospective_requirements": retrospective_requirement_results,
        "next_actions": retrospective_next_actions(retrospective_requirement_results),
        "goal_completion_blockers": goal_completion_blockers,
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
