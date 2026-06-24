#!/usr/bin/env python3
"""Create an external retrospective intake checklist from knowledge_context."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RETRO_REQUIREMENTS_PATH = PROJECT_ROOT / "knowledge" / "completeness" / "retrospective-requirements.json"
GLOBAL_RETRO_DIR = PROJECT_ROOT / "knowledge" / "case-retrospectives"
RETROSPECTIVE_INTAKE_SCHEMA = PROJECT_ROOT / "schemas" / "retrospective_intake.schema.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a run-local retrospective intake checklist.")
    parser.add_argument("--manifest", required=True, help="External case_manifest.json path.")
    parser.add_argument("--knowledge-context", help="Defaults to <runtime_dir>/knowledge_context.json.")
    parser.add_argument("--output-md", help="Defaults to <calibration_dir>/retrospective-intake.md.")
    parser.add_argument("--output-json", help="Defaults to <runtime_dir>/retrospective_intake.json.")
    parser.add_argument("--global-retro-dir", help=argparse.SUPPRESS)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def json_type_matches(value: Any, expected_type: str | list[str]) -> bool:
    expected = expected_type if isinstance(expected_type, list) else [expected_type]
    for item in expected:
        if item == "object" and isinstance(value, dict):
            return True
        if item == "array" and isinstance(value, list):
            return True
        if item == "string" and isinstance(value, str):
            return True
        if item == "boolean" and isinstance(value, bool):
            return True
        if item == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if item == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if item == "null" and value is None:
            return True
    return False


def validate_schema_node(
    value: Any,
    rules: dict[str, Any],
    path_name: str,
    failures: list[str],
) -> None:
    expected_type = rules.get("type")
    if expected_type is not None and not json_type_matches(value, expected_type):
        failures.append(f"{path_name} has invalid type")
        return
    if "const" in rules and value != rules["const"]:
        failures.append(f"{path_name} must be {rules['const']!r}")
    enum = rules.get("enum")
    if isinstance(enum, list) and value not in enum:
        failures.append(f"{path_name} must be one of {enum}")
    minimum = rules.get("minimum")
    if isinstance(minimum, (int, float)) and isinstance(value, (int, float)) and value < minimum:
        failures.append(f"{path_name} must be >= {minimum}")
    if isinstance(value, list):
        min_items = rules.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            failures.append(f"{path_name} must contain at least {min_items} item(s)")
        item_rules = rules.get("items", {})
        if isinstance(item_rules, dict):
            for index, item in enumerate(value):
                validate_schema_node(item, item_rules, f"{path_name}[{index}]", failures)
    if isinstance(value, dict):
        required = rules.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    failures.append(f"{path_name} missing schema-required key: {key}")
        properties = rules.get("properties", {})
        if isinstance(properties, dict):
            for key, child_rules in properties.items():
                if isinstance(child_rules, dict) and key in value:
                    validate_schema_node(value[key], child_rules, f"{path_name}.{key}", failures)


def retrospective_intake_schema_failures(payload: dict[str, Any]) -> list[str]:
    schema = load_json(RETROSPECTIVE_INTAKE_SCHEMA)
    failures: list[str] = []
    if schema.get("schema_version") != "0.1.0":
        failures.append("retrospective_intake schema file schema_version must be 0.1.0")
    validate_schema_node(payload, schema, "retrospective_intake", failures)
    return failures


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def external_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if is_relative_to(resolved, PROJECT_ROOT):
        raise SystemExit(f"{label} must stay outside project repo: {resolved}")
    return resolved


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def requirements_by_domain() -> dict[str, dict[str, Any]]:
    data = load_json(RETRO_REQUIREMENTS_PATH)
    requirements = data.get("requirements", [])
    if not isinstance(requirements, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in requirements:
        if not isinstance(item, dict):
            continue
        domain = item.get("domain")
        if isinstance(domain, str) and domain:
            result[domain] = item
    return result


def current_evidence_questions(domain: str, requirements: dict[str, dict[str, Any]]) -> list[str]:
    raw = requirements.get(domain, {}).get("evidence_questions", [])
    if not isinstance(raw, list):
        return []
    return [item.strip() for item in raw if isinstance(item, str) and item.strip()]


def append_missing_evidence(plan_item: dict[str, Any], questions: list[str]) -> dict[str, Any]:
    if not questions:
        return plan_item
    evidence = [str(item) for item in as_list(plan_item.get("evidence_to_collect")) if str(item).strip()]
    seen = set(evidence)
    for question in questions:
        if question not in seen:
            evidence.append(question)
            seen.add(question)
    updated = dict(plan_item)
    updated["evidence_to_collect"] = evidence
    return updated


def hydrate_context_with_current_retrospective_questions(context: dict[str, Any]) -> dict[str, Any]:
    requirements = requirements_by_domain()
    if not requirements:
        return context

    updated = dict(context)
    plan: list[dict[str, Any]] = []
    for item in as_list(context.get("retrospective_collection_plan")):
        if not isinstance(item, dict):
            continue
        domain = str(item.get("domain", ""))
        plan.append(append_missing_evidence(item, current_evidence_questions(domain, requirements)))
    updated["retrospective_collection_plan"] = plan

    hydrated_requirements: list[dict[str, Any]] = []
    for item in as_list(context.get("retrospective_requirements")):
        if not isinstance(item, dict):
            continue
        domain = str(item.get("domain", ""))
        questions = current_evidence_questions(domain, requirements)
        if questions and not as_list(item.get("evidence_questions")):
            item = {**item, "evidence_questions": questions}
        hydrated_requirements.append(item)
    updated["retrospective_requirements"] = hydrated_requirements
    return updated


def clean_blocker_line(item: Any) -> str:
    if isinstance(item, dict):
        domain = item.get("domain", "")
        gap_id = item.get("id") or item.get("gap_id") or ""
        description = item.get("description", "")
        blocked_by = item.get("blocked_by", "")
        parts = [f"`{gap_id}`"]
        if domain:
            parts.append(f"domain `{domain}`")
        if description:
            parts.append(str(description))
        if blocked_by:
            parts.append(f"blocked_by: {blocked_by}")
        return " / ".join(parts)
    return f"`{item}`"


def requirement_number(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if item.get(key) not in (None, ""):
            return item.get(key)
    return ""


def promotion_command_for_candidate(filename: str) -> str:
    return (
        "python scripts/promote_case_retrospective.py "
        f"--candidate '<RUN_DIR>\\retrospectives\\{filename}' --approved-by EDY"
    )


def promotion_dry_run_command_for_candidate(filename: str) -> str:
    return promotion_command_for_candidate(filename) + " --dry-run"


def inferred_domains_from_targets(target_artifacts: list[Any]) -> list[str]:
    domains: set[str] = set()
    for artifact in target_artifacts:
        normalized = str(artifact).replace("\\", "/")
        if normalized.startswith("templates/relationship-") or normalized in {
            "scripts/build_relationship_facts.py",
            "scripts/create_relationship_workspace.py",
            "scripts/validate_relationship_report.py",
        }:
            domains.add("relationship")
        if normalized.startswith("knowledge/team-career/") or normalized in {
            "service/multi-person-career-synastry-sop.md",
            "templates/team-career-synastry-template.md",
        }:
            domains.add("team_career")
        if normalized.startswith("knowledge/fengshui/"):
            domains.add("fengshui")
        if normalized.startswith("templates/") or normalized.startswith("service/") or normalized.startswith(
            "knowledge/writing/"
        ):
            domains.add("writing")
        if normalized.startswith("knowledge/"):
            parts = normalized.split("/")
            if len(parts) >= 2:
                domains.add(parts[1])
        if normalized.startswith("scripts/audit_") or normalized.startswith("scripts/validate_"):
            domains.add("quality")
    return sorted(domains)


def candidate_warnings(data: dict[str, Any]) -> list[str]:
    domains = {str(item) for item in as_list(data.get("domains"))}
    inferred = set(inferred_domains_from_targets(as_list(data.get("target_artifacts"))))
    warnings: list[str] = []
    missing = sorted(inferred - domains)
    if missing:
        warnings.append(
            "target_artifacts imply missing domains: "
            + ", ".join(missing)
            + "; regenerate candidate or add domains before promotion."
        )
    if data.get("human_approved") is True and data.get("status") == "candidate":
        warnings.append("candidate has human_approved=true but status is still candidate.")
    return warnings


def run_local_candidates(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    paths = manifest.get("paths", {})
    raw_dir = paths.get("retrospectives_dir") if isinstance(paths, dict) else None
    if not raw_dir:
        return []
    retro_dir = Path(raw_dir)
    if not retro_dir.exists() or is_relative_to(retro_dir.resolve(), PROJECT_ROOT):
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(retro_dir.glob("*.candidate.json")):
        try:
            data = load_json(path)
        except (json.JSONDecodeError, SystemExit):
            data = {}
        warnings = candidate_warnings(data) if isinstance(data, dict) else []
        domains = data.get("domains", []) if isinstance(data, dict) else []
        target_artifacts = data.get("target_artifacts", []) if isinstance(data, dict) else []
        approval_blockers: list[str] = []
        if warnings:
            approval_blockers.extend(str(item) for item in warnings)
        if not as_list(domains):
            approval_blockers.append("candidate has no domains.")
        if not as_list(target_artifacts):
            approval_blockers.append("candidate has no target_artifacts.")
        if data.get("human_approved") is True:
            approval_blockers.append("candidate is already marked human_approved; promote or normalize status instead of re-approving.")
        candidates.append(
            {
                "file": path.name,
                "id": data.get("id") or path.stem,
                "title": data.get("title") or "",
                "status": data.get("status") or "candidate",
                "domains": domains,
                "human_approved": data.get("human_approved") is True,
                "target_artifacts": target_artifacts,
                "warnings": warnings,
                "approval_ready": not approval_blockers,
                "approval_blockers": approval_blockers,
                "promotion_dry_run_command": promotion_dry_run_command_for_candidate(path.name),
                "promotion_command": promotion_command_for_candidate(path.name),
            }
        )
    return candidates


def approval_summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [item for item in candidates if item.get("approval_ready") is True]
    blocked = [item for item in candidates if item.get("approval_ready") is not True]
    already_approved = [item for item in candidates if item.get("human_approved") is True]
    return {
        "candidate_count": len(candidates),
        "ready_for_human_approval": len(ready),
        "needs_fix_before_approval": len(blocked),
        "already_human_approved": len(already_approved),
        "ready_candidate_ids": [item.get("id") for item in ready],
        "blocked_candidate_ids": [item.get("id") for item in blocked],
    }


def ready_candidate_commands(candidates: list[dict[str, Any]]) -> dict[str, list[str]]:
    ready = [item for item in candidates if item.get("approval_ready") is True]
    return {
        "dry_run": [str(item["promotion_dry_run_command"]) for item in ready],
        "promote": [str(item["promotion_command"]) for item in ready],
        "post_promotion_audits": [
            "python scripts/audit_case_retrospectives.py",
            "python scripts/audit_knowledge_coverage.py",
        ],
    }


def global_retrospective_items(retro_dir: Path = GLOBAL_RETRO_DIR) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(retro_dir.glob("*.json")):
        try:
            data = load_json(path)
        except (json.JSONDecodeError, SystemExit):
            continue
        if isinstance(data, dict):
            items.append(data)
    return items


def count_items_for_requirement(
    items: list[dict[str, Any]],
    requirement: dict[str, Any],
    status_rank: dict[str, Any],
) -> int:
    domain = str(requirement.get("domain", ""))
    min_status = str(requirement.get("min_status", "curated"))
    min_rank = int(status_rank.get(min_status, 999))
    count = 0
    for item in items:
        if item.get("human_approved") is not True:
            continue
        status = str(item.get("status", ""))
        if int(status_rank.get(status, -1)) < min_rank:
            continue
        domains = item.get("domains", [])
        if domain == "*" or (isinstance(domains, list) and domain in domains):
            count += 1
    return count


def ready_candidate_preview_items(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("approval_ready") is not True:
            continue
        preview.append(
            {
                "id": candidate.get("id"),
                "status": "curated",
                "human_approved": True,
                "domains": candidate.get("domains", []),
            }
        )
    return preview


def approval_impact_preview(candidates: list[dict[str, Any]], retro_dir: Path = GLOBAL_RETRO_DIR) -> dict[str, Any]:
    requirements_data = load_json(RETRO_REQUIREMENTS_PATH)
    status_rank = requirements_data.get("status_rank", {})
    requirements = requirements_data.get("requirements", [])
    if not isinstance(status_rank, dict) or not isinstance(requirements, list):
        return {"ready_candidate_count": 0, "requirements": []}
    ready_preview = ready_candidate_preview_items(candidates)
    current_items = global_retrospective_items(retro_dir)
    combined_items = current_items + ready_preview
    results: list[dict[str, Any]] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        min_entries = int(requirement.get("min_entries", 0) or 0)
        current = count_items_for_requirement(current_items, requirement, status_rank)
        preview = count_items_for_requirement(combined_items, requirement, status_rank)
        results.append(
            {
                "id": requirement.get("id"),
                "domain": requirement.get("domain"),
                "gap_id": requirement.get("gap_id"),
                "min_entries": min_entries,
                "current_entries": current,
                "preview_entries": preview,
                "would_satisfy": preview >= min_entries,
                "newly_satisfied": current < min_entries <= preview,
            }
        )
    return {
        "ready_candidate_count": len(ready_preview),
        "ready_candidate_ids": [item.get("id") for item in ready_preview],
        "requirements": results,
    }


def candidate_satisfies_domain(candidate: dict[str, Any], domain: str) -> bool:
    domains = candidate.get("domains", [])
    if domain == "*":
        return True
    return isinstance(domains, list) and domain in domains


def minimal_approval_plan(candidates: list[dict[str, Any]], retro_dir: Path = GLOBAL_RETRO_DIR) -> dict[str, Any]:
    requirements_data = load_json(RETRO_REQUIREMENTS_PATH)
    status_rank = requirements_data.get("status_rank", {})
    requirements = requirements_data.get("requirements", [])
    if not isinstance(status_rank, dict) or not isinstance(requirements, list):
        return {"selected_candidate_ids": [], "requirements": []}

    ready = [item for item in candidates if item.get("approval_ready") is True]
    current_items = global_retrospective_items(retro_dir)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    requirement_results: list[dict[str, Any]] = []

    ordered_requirements = [
        item for item in requirements if isinstance(item, dict) and str(item.get("domain", "")) != "*"
    ] + [item for item in requirements if isinstance(item, dict) and str(item.get("domain", "")) == "*"]

    for requirement in ordered_requirements:
        domain = str(requirement.get("domain", ""))
        min_entries = int(requirement.get("min_entries", 0) or 0)
        current = count_items_for_requirement(current_items, requirement, status_rank)
        needed = max(0, min_entries - current)
        ready_matching = [item for item in ready if candidate_satisfies_domain(item, domain)]
        selected_matching = [item for item in selected if candidate_satisfies_domain(item, domain)]
        can_satisfy = len(ready_matching) >= needed
        newly_satisfiable = needed > 0 and can_satisfy

        if newly_satisfiable and len(selected_matching) < needed:
            for item in ready_matching:
                if item.get("id") in selected_ids:
                    continue
                selected.append(item)
                selected_ids.add(str(item.get("id")))
                selected_matching.append(item)
                if len(selected_matching) >= needed:
                    break

        selected_matching = [item for item in selected if candidate_satisfies_domain(item, domain)]
        requirement_results.append(
            {
                "id": requirement.get("id"),
                "domain": domain,
                "gap_id": requirement.get("gap_id"),
                "min_entries": min_entries,
                "current_entries": current,
                "needed_entries": needed,
                "ready_matching_candidates": len(ready_matching),
                "selected_matching_candidates": len(selected_matching),
                "can_satisfy_with_ready": can_satisfy,
                "would_satisfy_with_selected": current + len(selected_matching) >= min_entries,
                "included_in_minimal_plan": newly_satisfiable,
            }
        )

    return {
        "selected_candidate_count": len(selected),
        "selected_candidate_ids": [str(item.get("id")) for item in selected],
        "requirements": requirement_results,
    }


def lines_for_plan(plan: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if not plan:
        lines.extend(
            [
                "## 当前复盘状态",
                "",
                "当前 `knowledge_context` 没有未满足的复盘采集计划。仍可记录客户反馈，但不要为了凑数量制造候选复盘。",
                "",
            ]
        )
        return lines

    lines.extend(["## 本次优先沉淀方向", ""])
    for item in plan:
        domain = item.get("domain", "")
        needed = item.get("needed_entries", "")
        lines.extend([f"### {domain}", "", f"- 还需要候选复盘数：`{needed}`"])
        targets = [str(target) for target in as_list(item.get("suggested_target_artifacts"))]
        if targets:
            lines.append("- 建议落点：")
            lines.extend(f"  - `{target}`" for target in targets[:6])
        evidence = [str(entry) for entry in as_list(item.get("evidence_to_collect"))]
        if evidence:
            lines.append("- 证据收集：")
            lines.extend(f"  - {entry}" for entry in evidence)
        commands = [str(command) for command in as_list(item.get("candidate_commands"))]
        if not commands and item.get("candidate_command"):
            commands = [str(item["candidate_command"])]
        if commands:
            lines.extend(["", "候选命令：", ""])
            for command in commands[:3]:
                lines.extend(["```powershell", command, "```", ""])
        lines.append("")
    return lines


def domain_label(domain: str) -> str:
    labels = {
        "bazi": "八字",
        "ziwei": "紫微",
        "western": "西占",
        "liuyao": "六爻",
        "relationship": "双人合盘",
        "team_career": "多人事业合盘",
        "fengshui": "风水方位",
        "writing": "写作表达",
        "*": "全局复盘",
    }
    return labels.get(domain, domain)


def domain_question_bank(
    requirements: list[dict[str, Any]],
    plan: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    plan_by_domain = {str(item.get("domain", "")): item for item in plan if isinstance(item, dict)}
    bank: list[dict[str, Any]] = []
    for item in requirements:
        if not isinstance(item, dict):
            continue
        if item.get("satisfied") is True:
            continue
        questions = [str(question).strip() for question in as_list(item.get("evidence_questions")) if str(question).strip()]
        if not questions:
            continue
        domain = str(item.get("domain", ""))
        plan_item = plan_by_domain.get(domain, {})
        bank.append(
            {
                "domain": domain,
                "label": domain_label(domain),
                "requirement_id": item.get("id"),
                "gap_id": item.get("gap_id"),
                "needed_entries": requirement_number(item, "needed_entries", "min_entries", "needed"),
                "min_status": item.get("min_status", ""),
                "questions": questions,
                "suggested_target_artifacts": [
                    str(target) for target in as_list(plan_item.get("suggested_target_artifacts"))
                ],
            }
        )
    return bank


def lines_for_domain_question_bank(
    requirements: list[dict[str, Any]],
    plan: list[dict[str, Any]],
) -> list[str]:
    bank = domain_question_bank(requirements, plan)
    if not bank:
        return []

    lines = [
        "## 按领域追问提示",
        "",
        "不要用同一批问题追所有读者；先按本 run 的模块和 blocker 选择领域，再问能验证或推翻判断的问题。",
        "",
    ]
    for item in bank:
        lines.extend([f"### {item['label']}", ""])
        lines.extend(f"- {question}" for question in item["questions"])
        targets = [str(target) for target in as_list(item.get("suggested_target_artifacts"))]
        if targets:
            lines.append("- 优先落点：")
            lines.extend(f"  - `{target}`" for target in targets[:3])
        lines.append("")
    return lines


def build_markdown(manifest: dict[str, Any], context: dict[str, Any], retro_dir: Path = GLOBAL_RETRO_DIR) -> str:
    plan = [item for item in as_list(context.get("retrospective_collection_plan")) if isinstance(item, dict)]
    blockers = as_list(context.get("goal_completion_blockers"))
    requirements = [
        item for item in as_list(context.get("retrospective_requirements")) if isinstance(item, dict)
    ]

    lines = [
        "# Retrospective Intake",
        "",
        f"- case_id: `{manifest.get('case_id', '')}`",
        f"- run_id: `{manifest.get('run_id', '')}`",
        f"- created_at: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "这个文件只放在外部 run 目录，用来收集可去隐私、可复用的反馈。它不是客户报告，也不能直接进入全局知识库。",
        "",
        "## 可以问读者的问题",
        "",
        "1. 你觉得最准的三段分别是什么？请只描述抽象感受，不要补新的隐私细节。",
        "2. 哪一段不准、过度、太笼统或没有帮助？原因是什么？",
        "3. 哪一段像是误读了你的表达边界、关系边界或修改次数？请说明它为什么让你有这种感觉。",
        "4. 哪一段让你愿意继续读，哪一段让你想跳过？",
        "5. 事业、关系、财富、健康/精力、人际合作、学习成长里，哪个专题最有用？哪个专题最弱？",
        "6. 未来趋势和行动建议里，有没有一条你真的会执行？如果没有，为什么？",
        "7. 这条反馈更像要改命理判断、改表达模板、改验收规则，还是只记录一个反例？",
        "",
        "## 去隐私整理要求",
        "",
        "- 不保留姓名、昵称、出生日期、出生时间、截图路径、本机路径或报告原文。",
        "- 不复制读者原话长段；只写抽象机制和可复用教训。",
        "- 必须保留至少一个反例、限制或误用风险。",
        "- 候选复盘先留在 `<RUN_DIR>/retrospectives`，人工批准前不得进入 `knowledge/case-retrospectives/`。",
        "",
        "## 复盘优先级",
        "",
        "- 优先记录“哪段准、哪段不准、为什么误读、怎么改”的真实反馈。",
        "- 没有明确案例证据时，不新增通用写作规则；先把它记成待验证假设或反例。",
        "- 每条候选复盘必须写清楚建议落点：命理知识、表达模板、验收脚本，还是只保留为案例校准。",
        "",
    ]
    lines.extend(lines_for_domain_question_bank(requirements, plan))
    if blockers:
        lines.extend(["## 仍然打开的 blocker", ""])
        for blocker in blockers:
            lines.append(f"- {clean_blocker_line(blocker)}")
        lines.append("")
    if requirements:
        lines.extend(["## 复盘门槛", ""])
        for item in requirements:
            lines.append(
                "- `{id}` / `{domain}`: current `{current}`，needed `{needed}`，min_status `{status}`".format(
                    id=item.get("id", ""),
                    domain=item.get("domain", ""),
                    current=requirement_number(item, "current_entries", "current"),
                    needed=requirement_number(item, "needed_entries", "min_entries", "needed"),
                    status=item.get("min_status", ""),
                )
            )
        lines.append("")
    candidates = run_local_candidates(manifest)
    if candidates:
        summary = approval_summary(candidates)
        lines.extend(
            [
                "## 候选复盘审批摘要",
                "",
                f"- 候选总数：`{summary['candidate_count']}`",
                f"- 可进入人工审批：`{summary['ready_for_human_approval']}`",
                f"- 需要先修复：`{summary['needs_fix_before_approval']}`",
                f"- 已标记人工批准：`{summary['already_human_approved']}`",
                "",
                "人工批准只代表“这条去隐私经验可以沉淀为项目知识”，不代表原报告所有判断都被证明为真。",
                "",
            ]
        )
        lines.extend(["## 本 run 已有候选复盘", ""])
        lines.append("这些候选仍是 run-local 材料；未人工批准前不计入全局知识库，也不关闭 curated 门槛。")
        lines.append("")
        for item in candidates:
            domains = "、".join(str(domain) for domain in as_list(item.get("domains"))) or ""
            lines.append(
                "- `{id}` / status `{status}` / domains `{domains}` / file `{file}`".format(
                    id=item.get("id", ""),
                    status=item.get("status", ""),
                    domains=domains,
                    file=item.get("file", ""),
                )
            )
            if item.get("title"):
                lines.append(f"  - title: {item['title']}")
            lines.append(f"  - approval_ready: `{str(item.get('approval_ready')).lower()}`")
            for blocker in as_list(item.get("approval_blockers")):
                lines.append(f"  - approval_blocker: {blocker}")
            for warning in as_list(item.get("warnings")):
                lines.append(f"  - warning: {warning}")
            lines.extend(
                [
                    "  - 人工确认前预览命令：",
                    "    ```powershell",
                    f"    {item['promotion_dry_run_command']}",
                    "    ```",
                    "  - 人工确认后晋升命令：",
                    "    ```powershell",
                    f"    {item['promotion_command']}",
                    "    ```",
                ]
            )
        lines.append("")
        impact = approval_impact_preview(candidates, retro_dir)
        lines.extend(["## 批准 ready 候选后的覆盖预览", ""])
        ready_ids = impact.get("ready_candidate_ids", [])
        if ready_ids:
            lines.append("- 预览假设：只把 `approval_ready=true` 的候选按人工批准后 `curated` 状态计入。")
            lines.append("- 本预览不写入全局知识库，不关闭 blocker，只帮助人工判断优先级。")
            lines.append(f"- ready 候选：`{', '.join(str(item) for item in ready_ids)}`")
            lines.append("")
            for item in as_list(impact.get("requirements")):
                if not isinstance(item, dict):
                    continue
                marker = "可满足" if item.get("would_satisfy") else "仍不足"
                newly = " / 新满足" if item.get("newly_satisfied") else ""
                lines.append(
                    "- `{id}` / `{domain}`: {current} -> {preview} / min `{min_entries}` / {marker}{newly}".format(
                        id=item.get("id", ""),
                        domain=item.get("domain", ""),
                        current=item.get("current_entries", 0),
                        preview=item.get("preview_entries", 0),
                        min_entries=item.get("min_entries", 0),
                        marker=marker,
                        newly=newly,
                    )
                )
        else:
            lines.append("当前没有 `approval_ready=true` 的候选；先修复候选 domains、target_artifacts 或人工审批状态。")
        lines.append("")
        minimal = minimal_approval_plan(candidates, retro_dir)
        selected_ids = [str(item) for item in as_list(minimal.get("selected_candidate_ids"))]
        lines.extend(["## 最小人工审批建议", ""])
        if selected_ids:
            lines.append("这是一个审批辅助建议，不会自动晋升；它只回答“先批哪几条最能关闭当前可关闭门槛”。")
            lines.append(f"- 建议先审批候选数：`{len(selected_ids)}`")
            lines.append(f"- 建议候选：`{', '.join(selected_ids)}`")
            lines.append("")
            lines.append("按这个最小集合预估：")
            for item in as_list(minimal.get("requirements")):
                if not isinstance(item, dict):
                    continue
                if item.get("included_in_minimal_plan") or item.get("would_satisfy_with_selected"):
                    marker = "可关闭" if item.get("would_satisfy_with_selected") else "仍不足"
                    lines.append(
                        "- `{id}` / `{domain}`: selected `{selected}` / needed `{needed}` / {marker}".format(
                            id=item.get("id", ""),
                            domain=item.get("domain", ""),
                            selected=item.get("selected_matching_candidates", 0),
                            needed=item.get("needed_entries", 0),
                            marker=marker,
                        )
                    )
            still_missing = [
                item
                for item in as_list(minimal.get("requirements"))
                if isinstance(item, dict)
                and item.get("needed_entries", 0)
                and not item.get("can_satisfy_with_ready")
            ]
            if still_missing:
                lines.append("")
                lines.append("仍不能靠本 run 候选关闭的门槛：")
                for item in still_missing:
                    lines.append(
                        "- `{id}` / `{domain}`: ready `{ready}` / needed `{needed}`".format(
                            id=item.get("id", ""),
                            domain=item.get("domain", ""),
                            ready=item.get("ready_matching_candidates", 0),
                            needed=item.get("needed_entries", 0),
                        )
                    )
        else:
            lines.append("当前没有可形成最小审批建议的 ready 候选。")
        lines.append("")
        commands = ready_candidate_commands(candidates)
        if commands["dry_run"]:
            lines.extend(
                [
                    "## ready 候选批量检查顺序",
                    "",
                    "先逐条 dry-run；人工确认后逐条晋升；全部晋升后再跑复盘审计和知识覆盖审计。这里仍然不自动晋升，人工批准边界不变。",
                    "",
                    "### 1. dry-run 预览",
                    "",
                ]
            )
            for command in commands["dry_run"]:
                lines.extend(["```powershell", command, "```", ""])
            lines.extend(["### 2. 人工批准后晋升", ""])
            for command in commands["promote"]:
                lines.extend(["```powershell", command, "```", ""])
            lines.extend(["### 3. 晋升后审计", ""])
            for command in commands["post_promotion_audits"]:
                lines.extend(["```powershell", command, "```", ""])
    lines.extend(lines_for_plan(plan))
    lines.extend(
        [
            "## 晋升前检查",
            "",
            "```powershell",
            "python scripts/promote_case_retrospective.py --candidate <RUN_DIR>\\retrospectives\\CR-YYYYMMDD-slug.candidate.json --approved-by EDY",
            "python scripts/audit_case_retrospectives.py",
            "python scripts/audit_knowledge_coverage.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    manifest_path = external_path(Path(args.manifest), "manifest")
    manifest = load_json(manifest_path)
    paths = manifest.get("paths", {})
    runtime_dir = external_path(Path(paths.get("runtime_dir", "")), "runtime_dir")
    calibration_dir = external_path(Path(paths.get("calibration_dir", "")), "calibration_dir")
    knowledge_context_path = (
        external_path(Path(args.knowledge_context), "knowledge_context")
        if args.knowledge_context
        else runtime_dir / "knowledge_context.json"
    )
    context = hydrate_context_with_current_retrospective_questions(load_json(knowledge_context_path))
    retro_dir = Path(args.global_retro_dir).resolve() if args.global_retro_dir else GLOBAL_RETRO_DIR

    output_md = (
        external_path(Path(args.output_md), "output_md")
        if args.output_md
        else calibration_dir / "retrospective-intake.md"
    )
    output_json = (
        external_path(Path(args.output_json), "output_json")
        if args.output_json
        else runtime_dir / "retrospective_intake.json"
    )
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    plan = [item for item in as_list(context.get("retrospective_collection_plan")) if isinstance(item, dict)]
    missing_targets = [
        str(item.get("domain", ""))
        for item in plan
        if not as_list(item.get("suggested_target_artifacts"))
    ]
    if missing_targets:
        print(
            json.dumps(
                {
                    "passed": False,
                    "failures": [f"collection plan item missing suggested_target_artifacts: {domain}" for domain in missing_targets],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    candidates = run_local_candidates(manifest)
    question_bank = domain_question_bank(
        [item for item in as_list(context.get("retrospective_requirements")) if isinstance(item, dict)],
        plan,
    )
    payload = {
        "schema_version": "0.1.0",
        "case_id": manifest.get("case_id"),
        "run_id": manifest.get("run_id"),
        "knowledge_context": "runtime/knowledge_context.json",
        "retrospective_collection_plan": plan,
        "domain_question_bank": question_bank,
        "run_local_candidates": candidates,
        "run_local_approval_summary": approval_summary(candidates),
        "run_local_approval_impact_preview": approval_impact_preview(candidates, retro_dir),
        "run_local_minimal_approval_plan": minimal_approval_plan(candidates, retro_dir),
        "run_local_ready_candidate_commands": ready_candidate_commands(candidates),
        "run_local_candidate_warnings": [
            {
                "id": item.get("id"),
                "file": item.get("file"),
                "warnings": item.get("warnings"),
            }
            for item in candidates
            if as_list(item.get("warnings"))
        ],
        "knowledge_growth_priority": {
            "prefer": "real reader feedback: accurate part, inaccurate part, misread reason, concrete correction",
            "avoid": "new generic writing rules without deidentified case evidence",
            "decision_labels": ["knowledge_rule", "expression_template", "validation_gate", "counterexample_only"],
        },
        "do_not_promote_without_human_approval": True,
    }
    schema_failures = retrospective_intake_schema_failures(payload)
    if schema_failures:
        print(
            json.dumps(
                {
                    "passed": False,
                    "failures": schema_failures,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    output_md.write_text(build_markdown(manifest, context, retro_dir), encoding="utf-8")
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": True,
                "markdown": str(output_md),
                "json": str(output_json),
                "plan_items": len(plan),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
