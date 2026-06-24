#!/usr/bin/env python3
"""Audit the knowledge coverage matrix and goal-completion blockers."""

from __future__ import annotations

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Any

try:
    from .retrospective_priority import (
        repair_priority_for_requirements,
        requirement_ids_for_candidate,
        sort_repair_priority_queue,
    )
except ImportError:  # pragma: no cover - direct script execution
    from retrospective_priority import (
        repair_priority_for_requirements,
        requirement_ids_for_candidate,
        sort_repair_priority_queue,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PATH = PROJECT_ROOT / "knowledge" / "completeness" / "coverage-matrix.json"
RETRO_REQUIREMENTS_PATH = PROJECT_ROOT / "knowledge" / "completeness" / "retrospective-requirements.json"
KNOWLEDGE_MAP_PATH = PROJECT_ROOT / "knowledge" / "knowledge_map.json"
SOURCE_REGISTER_PATH = PROJECT_ROOT / "knowledge" / "sources" / "source-register.json"
SOURCE_INDEX_PATH = PROJECT_ROOT / "knowledge" / "source-index.md"
RUNTIME_PROFILE_PATH = PROJECT_ROOT / "config" / "runtime_profile.json"
RETRO_DIR = PROJECT_ROOT / "knowledge" / "case-retrospectives"
SOURCE_ID_RE = re.compile(r"SRC-[A-Z0-9-]+")
FORBIDDEN_CANDIDATE_PATTERNS = [
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
RETROSPECTIVE_DOMAINS = {
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


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the knowledge coverage matrix and goal-completion blockers.")
    parser.add_argument(
        "--retro-dir",
        default=str(RETRO_DIR),
        help="Retrospective directory to count. Defaults to knowledge/case-retrospectives; use a temp dir for approval previews.",
    )
    parser.add_argument(
        "--runs-root",
        help=(
            "Optional external root to scan for run-local retrospective candidates. "
            "Defaults to XUANXUE_RUNS_ROOT or config/runtime_profile.json when available."
        ),
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


def default_runs_root(explicit_root: str | None = None) -> Path | None:
    if explicit_root:
        return Path(explicit_root).expanduser().resolve()
    import os

    env_key = "XUANXUE_RUNS_ROOT"
    profile: dict[str, Any] = {}
    if RUNTIME_PROFILE_PATH.exists():
        try:
            profile = json.loads(RUNTIME_PROFILE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            profile = {}
    if isinstance(profile.get("external_root_env"), str):
        env_key = str(profile["external_root_env"])
    env_value = os.environ.get(env_key)
    if env_value:
        return Path(env_value).expanduser().resolve()
    default_value = profile.get("default_external_root")
    if isinstance(default_value, str) and default_value.strip():
        expanded = default_value.replace("%USERPROFILE%", str(Path.home()))
        return Path(expanded).expanduser().resolve()
    return None


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


def normalized_evidence_questions(requirement: dict[str, Any], failures: list[str]) -> list[str]:
    req_id = str(requirement.get("id", "<missing-id>"))
    raw = requirement.get("evidence_questions", [])
    if not isinstance(raw, list) or not raw:
        failures.append(f"{req_id} evidence_questions must be a non-empty list")
        return []
    questions: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            failures.append(f"{req_id} evidence_questions entries must be non-empty strings")
            continue
        questions.append(item.strip())
    return questions


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
        evidence_questions = normalized_evidence_questions(requirement, failures)
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
                "evidence_questions": evidence_questions,
            }
        )
        if not satisfied and gap_id not in blocker_set:
            failures.append(f"{req_id} is unsatisfied but its blocker is not open: {gap_id}")
        if satisfied and gap_id in blocker_set:
            warnings.append(f"{req_id} appears satisfied but blocker remains open: {gap_id}")
    return results


def suggested_target_artifacts(domain: str, knowledge_map: dict[str, Any]) -> list[str]:
    modules = knowledge_map.get("modules", {})
    if not isinstance(modules, dict):
        return []
    if domain == "*":
        candidates = [
            "knowledge/case-retrospectives/promotion-protocol.md",
            "knowledge/completeness/retrospective-requirements.json",
            "knowledge/writing/reader-rich-report.md",
        ]
    else:
        module = modules.get(domain, {})
        files = module.get("files", []) if isinstance(module, dict) else []
        candidates = [str(item).replace("\\", "/") for item in files if isinstance(item, str)]
    result: list[str] = []
    for item in candidates:
        if item not in result and (PROJECT_ROOT / item).exists():
            result.append(item)
    return result[:6]


def retrospective_next_actions(
    requirement_results: list[dict[str, Any]], knowledge_map: dict[str, Any]
) -> list[dict[str, Any]]:
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
        targets = suggested_target_artifacts(domain, knowledge_map)
        command_target = targets[0] if targets else "<project/artifact/path>"
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
                "evidence_questions": item.get("evidence_questions", []),
                "suggested_target_artifacts": targets,
                "commands": [
                    "python scripts/create_retrospective_intake.py --manifest <RUN_DIR>\\case_manifest.json",
                    (
                        "python scripts/create_case_retrospective_candidate.py "
                        "--manifest <RUN_DIR>\\case_manifest.json "
                        "--slug <short-ascii-slug> "
                        "--title <deidentified-retrospective-title> "
                        f"--domain {command_domain} "
                        "--evidence-summary <deidentified-evidence-summary> "
                        f"--domain-evidence \"{command_domain}|<evidence-anchor>|<observed-feedback>|<promotion-limit>\" "
                        f"--target-artifact {command_target}"
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


def candidate_has_private_text(candidate: dict[str, Any]) -> bool:
    serialized = json.dumps(candidate, ensure_ascii=False)
    return any(re.search(pattern, serialized, flags=re.IGNORECASE) for pattern in FORBIDDEN_CANDIDATE_PATTERNS)


DOMAIN_EVIDENCE_REQUIRED = RETROSPECTIVE_DOMAINS - {
    "source_register",
    "quality",
    "case_retrospectives",
    "completeness",
}
DOMAIN_EVIDENCE_REQUIRED_FIELDS = ("evidence_anchor", "observed_feedback", "promotion_limit")


def candidate_approval_blockers(candidate: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if candidate.get("status") != "candidate":
        blockers.append("candidate status must be candidate.")
    if candidate.get("human_approved") is True:
        blockers.append("candidate is already human_approved.")
    domains = candidate.get("domains", [])
    target_artifacts = candidate.get("target_artifacts", [])
    if not isinstance(domains, list) or not domains:
        blockers.append("candidate has no domains.")
    if not isinstance(target_artifacts, list) or not target_artifacts:
        blockers.append("candidate has no target_artifacts.")
    privacy = candidate.get("privacy")
    if isinstance(privacy, dict):
        if privacy.get("deidentified") is not True:
            blockers.append("privacy.deidentified must be true.")
        if privacy.get("contains_client_name") is not False:
            blockers.append("privacy.contains_client_name must be false.")
        if privacy.get("contains_local_paths") is not False:
            blockers.append("privacy.contains_local_paths must be false.")
        if privacy.get("contains_delivery_text") is not False:
            blockers.append("privacy.contains_delivery_text must be false.")
    required_domains = sorted({str(item) for item in domains} & DOMAIN_EVIDENCE_REQUIRED) if isinstance(domains, list) else []
    evidence = candidate.get("domain_evidence")
    if required_domains and not isinstance(evidence, dict):
        blockers.append(
            "candidate missing domain_evidence; add evidence_anchor, observed_feedback and promotion_limit for: "
            + ", ".join(required_domains)
        )
    elif required_domains and isinstance(evidence, dict):
        for domain in required_domains:
            domain_evidence = evidence.get(domain)
            if not isinstance(domain_evidence, dict):
                blockers.append(
                    f"candidate missing domain_evidence for {domain}; add evidence_anchor, observed_feedback and promotion_limit before approval."
                )
                continue
            missing_fields = [
                field
                for field in DOMAIN_EVIDENCE_REQUIRED_FIELDS
                if not str(domain_evidence.get(field, "")).strip()
            ]
            if missing_fields:
                blockers.append(f"candidate domain_evidence for {domain} missing fields: {', '.join(missing_fields)}.")
    if candidate_has_private_text(candidate):
        blockers.append("candidate contains forbidden private/local text.")
    return blockers


def candidate_approval_ready(candidate: dict[str, Any]) -> bool:
    return not candidate_approval_blockers(candidate)


def evidence_questions_for_domain(domain: str, requirement_results: list[dict[str, Any]]) -> list[str]:
    for requirement in requirement_results:
        if str(requirement.get("domain", "")) == domain:
            questions = requirement.get("evidence_questions", [])
            return [str(item) for item in questions] if isinstance(questions, list) else []
    return []


def domain_evidence_required_items(
    candidate: dict[str, Any],
    requirement_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    domains = candidate.get("domains", [])
    required_domains = sorted({str(item) for item in domains} & DOMAIN_EVIDENCE_REQUIRED) if isinstance(domains, list) else []
    evidence = candidate.get("domain_evidence")
    items: list[dict[str, Any]] = []
    for domain in required_domains:
        domain_evidence = evidence.get(domain) if isinstance(evidence, dict) else None
        if isinstance(domain_evidence, dict):
            missing_fields = [
                field
                for field in DOMAIN_EVIDENCE_REQUIRED_FIELDS
                if not str(domain_evidence.get(field, "")).strip()
            ]
        else:
            missing_fields = list(DOMAIN_EVIDENCE_REQUIRED_FIELDS)
        if missing_fields:
            items.append(
                {
                    "domain": domain,
                    "missing_fields": missing_fields,
                    "evidence_questions": evidence_questions_for_domain(domain, requirement_results),
                }
            )
    return items


def repair_actions_for_candidate(candidate: dict[str, Any], warnings: list[str]) -> list[str]:
    actions: list[str] = []
    domains = candidate.get("domains", [])
    target_artifacts = candidate.get("target_artifacts", [])
    if not isinstance(domains, list) or not domains:
        actions.append("补齐 domains；只能填写候选真实覆盖的知识域。")
    if not isinstance(target_artifacts, list) or not target_artifacts:
        actions.append("补齐 target_artifacts；必须指向这条复盘实际要改进的项目文件。")
    if domain_evidence_required_items(candidate, []):
        actions.append("补齐 domain_evidence；必须来自去隐私真实反馈，不要用模型推测代替证据。")
    if candidate_has_private_text(candidate):
        actions.append("删除候选中的姓名、本机路径、图片路径、时间戳等隐私或本地信息。")
    if candidate.get("human_approved") is True:
        actions.append("候选已标记 human_approved；不要重复审批，先晋升或规范化 status。")
    for warning in warnings:
        if "target_artifacts imply missing domains" in str(warning):
            actions.append("复核 target_artifacts 推断出的 domain；若确实覆盖该领域，补进 domains，否则调整 target_artifacts。")
    return actions


def blocked_candidate_repair_item(
    candidate: dict[str, Any],
    path_name: str,
    approval_blockers: list[str],
    requirement_results: list[dict[str, Any]],
) -> dict[str, Any]:
    warnings = []
    domains = candidate.get("domains", [])
    target_artifacts = candidate.get("target_artifacts", [])
    # Keep this local and conservative; audit output must not expose real paths.
    inferred = set()
    if isinstance(target_artifacts, list):
        for artifact in target_artifacts:
            normalized = str(artifact).replace("\\", "/")
            if normalized.startswith("templates/relationship-"):
                inferred.add("relationship")
            if normalized.startswith("knowledge/team-career/"):
                inferred.add("team_career")
            if normalized.startswith("knowledge/fengshui/"):
                inferred.add("fengshui")
            if normalized.startswith("templates/") or normalized.startswith("service/") or normalized.startswith("knowledge/writing/"):
                inferred.add("writing")
    domain_set = {str(item) for item in domains} if isinstance(domains, list) else set()
    missing_domains = sorted(inferred - domain_set)
    if missing_domains:
        warnings.append("target_artifacts imply missing domains: " + ", ".join(missing_domains))
    required_items = domain_evidence_required_items(candidate, requirement_results)
    return {
        "id": str(candidate.get("id") or Path(path_name).stem),
        "file": path_name,
        "candidate_path": f"<RUN_DIR>\\retrospectives\\{path_name}",
        "approval_blockers": approval_blockers,
        "domain_evidence_required": required_items,
        "repair_actions": repair_actions_for_candidate(candidate, warnings),
        "recheck_command": "python scripts/audit_knowledge_coverage.py",
        "intake_recheck_command": "python scripts/create_retrospective_intake.py --manifest <RUN_DIR>\\case_manifest.json",
        "promotion_dry_run_command_after_fix": (
            "python scripts/promote_case_retrospective.py "
            f"--candidate <RUN_DIR>\\retrospectives\\{path_name} --approved-by <APPROVER> --dry-run"
        ),
    }


def scan_run_local_candidates(
    runs_root: Path | None,
    requirement_results: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, Any]:
    """Summarize external run-local retrospective candidates without exposing paths.

    Candidates remain external and do not count toward completion. This output is
    only an approval queue hint for humans.
    """

    if runs_root is None:
        return {
            "enabled": False,
            "reason": "no runs_root configured",
            "candidate_count": 0,
            "ready_for_human_approval": 0,
            "needs_fix_before_approval": 0,
            "items": [],
            "blocked_items": [],
            "repair_plan": [],
            "repair_priority_queue": [],
        }
    if not runs_root.exists():
        return {
            "enabled": False,
            "reason": "runs_root does not exist",
            "candidate_count": 0,
            "ready_for_human_approval": 0,
            "needs_fix_before_approval": 0,
            "items": [],
            "blocked_items": [],
            "repair_plan": [],
            "repair_priority_queue": [],
        }
    if runs_root.resolve().is_relative_to(PROJECT_ROOT.resolve()):
        warnings.append("run-local candidate scan skipped because runs_root is inside the project repo")
        return {
            "enabled": False,
            "reason": "runs_root inside project repo",
            "candidate_count": 0,
            "ready_for_human_approval": 0,
            "needs_fix_before_approval": 0,
            "items": [],
            "blocked_items": [],
            "repair_plan": [],
            "repair_priority_queue": [],
        }
    runs_dir = runs_root / "runs"
    if not runs_dir.exists():
        return {
            "enabled": True,
            "reason": "runs directory missing",
            "candidate_count": 0,
            "ready_for_human_approval": 0,
            "needs_fix_before_approval": 0,
            "items": [],
            "blocked_items": [],
            "repair_plan": [],
            "repair_priority_queue": [],
        }

    items: list[dict[str, Any]] = []
    blocked_items: list[dict[str, Any]] = []
    repair_plan: list[dict[str, Any]] = []
    candidate_count = 0
    for path in sorted(runs_dir.glob("*/*/retrospectives/*.candidate.json")):
        candidate_count += 1
        try:
            candidate = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate, dict):
            continue
        approval_blockers = candidate_approval_blockers(candidate)
        if approval_blockers:
            matched_requirements_after_repair = requirement_ids_for_candidate(candidate, requirement_results)
            priority = repair_priority_for_requirements(matched_requirements_after_repair, requirement_results)
            repair_item = blocked_candidate_repair_item(
                candidate,
                path.name,
                approval_blockers,
                requirement_results,
            )
            repair_item["matched_unsatisfied_requirements_after_repair"] = matched_requirements_after_repair
            repair_item["repair_priority_score"] = priority["score"]
            repair_item["repair_priority_reason"] = priority["reason"]
            repair_plan.append(repair_item)
            blocked_items.append(
                {
                    "id": str(candidate.get("id") or path.stem),
                    "title": str(candidate.get("title") or ""),
                    "domains": [str(item) for item in candidate.get("domains", [])]
                    if isinstance(candidate.get("domains"), list)
                    else [],
                    "target_artifacts": [str(item) for item in candidate.get("target_artifacts", [])]
                    if isinstance(candidate.get("target_artifacts"), list)
                    else [],
                    "approval_ready": False,
                    "approval_blockers": approval_blockers,
                    "domain_evidence_required": repair_item["domain_evidence_required"],
                    "repair_actions": repair_item["repair_actions"],
                    "matched_unsatisfied_requirements_after_repair": matched_requirements_after_repair,
                    "repair_priority_score": priority["score"],
                    "repair_priority_reason": priority["reason"],
                    "intake_recheck_command": repair_item["intake_recheck_command"],
                    "promotion_dry_run_command_after_fix": repair_item["promotion_dry_run_command_after_fix"],
                    "location": "external_run_retrospectives",
                }
            )
            continue
        matched_requirements = requirement_ids_for_candidate(candidate, requirement_results)
        items.append(
            {
                "id": str(candidate.get("id") or path.stem),
                "title": str(candidate.get("title") or ""),
                "domains": [str(item) for item in candidate.get("domains", [])],
                "target_artifacts": [str(item) for item in candidate.get("target_artifacts", [])],
                "matched_unsatisfied_requirements": matched_requirements,
                "approval_ready": True,
                "location": "external_run_retrospectives",
                "dry_run_command": (
                    "python scripts/promote_case_retrospective.py "
                    f"--candidate <RUN_DIR>\\retrospectives\\{path.name} --approved-by <APPROVER> --dry-run"
                ),
            }
        )

    repair_priority_queue = sort_repair_priority_queue(repair_plan)
    return {
        "enabled": True,
        "reason": "",
        "candidate_count": candidate_count,
        "ready_for_human_approval": len(items),
        "needs_fix_before_approval": len(blocked_items),
        "items": items[:20],
        "items_truncated": max(0, len(items) - 20),
        "blocked_items": blocked_items[:20],
        "blocked_items_truncated": max(0, len(blocked_items) - 20),
        "repair_plan": repair_plan[:20],
        "repair_plan_truncated": max(0, len(repair_plan) - 20),
        "repair_priority_queue": repair_priority_queue[:20],
        "repair_priority_queue_truncated": max(0, len(repair_priority_queue) - 20),
    }


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
    run_local_candidate_summary = scan_run_local_candidates(
        default_runs_root(args.runs_root),
        retrospective_requirement_results,
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
        "run_local_candidate_summary": run_local_candidate_summary,
        "next_actions": retrospective_next_actions(retrospective_requirement_results, knowledge_map),
        "goal_completion_blockers": goal_completion_blockers,
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
