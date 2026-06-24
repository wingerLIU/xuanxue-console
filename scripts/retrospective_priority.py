"""Shared retrospective candidate priority helpers.

This module is deliberately import-only: it is not a new gate or workflow
entrypoint. Keep run-local evidence handling in the caller.
"""

from __future__ import annotations

from typing import Any


def requirement_ids_for_candidate(
    candidate: dict[str, Any],
    requirement_results: list[dict[str, Any]],
) -> list[str]:
    domains = candidate.get("domains", [])
    domain_set = {str(item) for item in domains} if isinstance(domains, list) else set()
    requirement_ids: list[str] = []
    for requirement in requirement_results:
        if requirement.get("satisfied") is True:
            continue
        domain = str(requirement.get("domain", ""))
        if domain == "*" or domain in domain_set:
            req_id = str(requirement.get("id", ""))
            if req_id:
                requirement_ids.append(req_id)
    return requirement_ids


def repair_priority_for_requirements(
    requirement_ids: list[str],
    requirement_results: list[dict[str, Any]],
) -> dict[str, Any]:
    requirement_domains = {str(item.get("id", "")): str(item.get("domain", "")) for item in requirement_results}
    specific_requirements = [
        req_id for req_id in requirement_ids if requirement_domains.get(req_id) and requirement_domains.get(req_id) != "*"
    ]
    wildcard_requirements = [req_id for req_id in requirement_ids if requirement_domains.get(req_id) == "*"]
    score = len(specific_requirements) * 10 + len(wildcard_requirements)
    if specific_requirements:
        reason = "修复后可推进未满足领域门槛：" + ", ".join(specific_requirements)
    elif wildcard_requirements:
        reason = "修复后只推进通用复盘门槛：" + ", ".join(wildcard_requirements)
    else:
        reason = "修复后暂不直接推进当前未满足门槛，低优先级。"
    return {"score": score, "reason": reason}


def sort_repair_priority_queue(repair_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        repair_plan,
        key=lambda item: (-int(item.get("repair_priority_score", 0) or 0), str(item.get("id", ""))),
    )
