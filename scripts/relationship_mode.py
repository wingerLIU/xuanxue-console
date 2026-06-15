#!/usr/bin/env python3
"""Shared relationship-mode rules for relationship facts and report validation."""

from __future__ import annotations

from typing import Any


ROMANTIC_STATUS_MARKERS = [
    "男女朋友",
    "情侣",
    "恋人",
    "恋爱",
    "对象",
    "伴侣",
    "夫妻",
    "婚",
    "暧昧",
    "追求",
    "喜欢",
]

RELATIONSHIP_MODE_CATEGORIES = {"romantic_or_ambiguous", "non_romantic_or_unsupported"}

ROMANTIC_ALLOWED_PRIVATE_LANGUAGE = ["身体吸引", "调情节奏", "想靠近", "安全感", "主动与回应"]
ROMANTIC_FORBIDDEN_PRIVATE_LANGUAGE = ["具体行为", "具体频率", "露骨细节", "身体隐私"]
NON_ROMANTIC_ALLOWED_PRIVATE_LANGUAGE = ["亲近感", "信任边界", "互动距离", "安全感", "主动与回应"]
NON_ROMANTIC_FORBIDDEN_PRIVATE_LANGUAGE = [
    "身体吸引",
    "调情节奏",
    "私密生活",
    "具体行为",
    "具体频率",
    "露骨细节",
]
NON_ROMANTIC_INTIMACY_MARKERS = [
    "身体吸引",
    "身体感",
    "调情",
    "私密生活",
    "想靠近",
    "有火",
    "有甜",
]


def is_romantic_status(status: str) -> bool:
    return any(marker in status for marker in ROMANTIC_STATUS_MARKERS)


def relationship_mode_from_status(status: str) -> dict[str, Any]:
    status_text = status.strip()
    is_romantic = is_romantic_status(status_text)
    return {
        "status": status_text,
        "category": "romantic_or_ambiguous" if is_romantic else "non_romantic_or_unsupported",
        "romantic_language_supported": is_romantic,
        "allowed_private_language": (
            ROMANTIC_ALLOWED_PRIVATE_LANGUAGE
            if is_romantic
            else NON_ROMANTIC_ALLOWED_PRIVATE_LANGUAGE
        ),
        "forbidden_private_language": (
            ROMANTIC_FORBIDDEN_PRIVATE_LANGUAGE
            if is_romantic
            else NON_ROMANTIC_FORBIDDEN_PRIVATE_LANGUAGE
        ),
        "writing_boundary": (
            "已知关系状态支持时，可以写身体吸引、调情和安全感；不写具体行为细节或频率。"
            if is_romantic
            else "关系状态不支持恋爱化推断时，只写亲近感、信任边界、互动距离和安全感，不写身体吸引或私密生活。"
        ),
    }


def relationship_mode_from_facts(facts: dict[str, Any]) -> dict[str, Any]:
    mode = facts.get("relationship_mode")
    if isinstance(mode, dict):
        return mode
    context = facts.get("relationship_context", {})
    if isinstance(context, dict) and isinstance(context.get("relationship_mode"), dict):
        return context["relationship_mode"]
    return {}


def is_romantic_facts(facts: dict[str, Any]) -> bool:
    mode = relationship_mode_from_facts(facts)
    if "romantic_language_supported" in mode:
        return bool(mode.get("romantic_language_supported"))
    context = facts.get("relationship_context", {})
    status = ""
    if isinstance(context, dict):
        status = str(context.get("relationship_status") or "").strip()
    return is_romantic_status(status)


def relationship_mode_schema_failures(mode: dict[str, Any], *, prefix: str = "relationship_mode") -> list[str]:
    failures: list[str] = []
    if not isinstance(mode, dict) or not mode:
        return [f"{prefix} missing or empty."]
    if mode.get("category") not in RELATIONSHIP_MODE_CATEGORIES:
        failures.append(f"{prefix}.category is invalid or missing.")
    if not isinstance(mode.get("romantic_language_supported"), bool):
        failures.append(f"{prefix}.romantic_language_supported must be a boolean.")
    for key in ["allowed_private_language", "forbidden_private_language"]:
        value = mode.get(key)
        if not isinstance(value, list) or not value:
            failures.append(f"{prefix}.{key} must be a non-empty list.")
    boundary = mode.get("writing_boundary")
    if not isinstance(boundary, str) or len(boundary.strip()) < 8:
        failures.append(f"{prefix}.writing_boundary is missing or too short.")
    return failures
