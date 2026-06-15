#!/usr/bin/env python3
"""Runtime contract helpers for external xuanxue case runs.

This module is the single place for manifest artifact names, legacy aliases,
and finalization requirements. Keep validation scripts reading this contract
instead of introducing new one-off gates.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_ARTIFACT_ALIASES = {
    "main_html": ["main_html", "html_report"],
    "fact_archive_markdown": ["fact_archive_markdown", "facts_markdown", "fact_archive_md", "data.fact_archive_markdown"],
    "longform_markdown": [
        "longform_markdown",
        "longform_source_md",
        "reader_markdown",
        "rich_markdown",
        "relationship_addendum_markdown",
        "delivery.rich_markdown",
        "delivery.relationship_addendum_markdown",
        "drafts.longform_markdown",
    ],
    "longform_pdf": ["longform_pdf", "reader_pdf", "rich_pdf", "delivery.rich_pdf"],
    "concise_markdown": ["concise_markdown", "concise_source_md", "delivery.concise_markdown"],
    "concise_docx": ["concise_docx", "delivery.concise_docx"],
    "concise_pdf": ["concise_pdf", "delivery.concise_pdf"],
    "concise_zip": ["concise_zip", "delivery.concise_zip"],
    "mobile_html": ["mobile_html", "reader_mobile_html", "delivery.mobile_html"],
    "concise_mobile_html": ["concise_mobile_html", "delivery.concise_mobile_html"],
    "rich_mobile_html": ["rich_mobile_html", "delivery.rich_mobile_html"],
    "relationship_mobile_html": ["relationship_mobile_html", "delivery.relationship_mobile_html"],
    "relationship_concise_source_markdown": [
        "relationship_concise_source_markdown",
        "drafts.relationship_concise_markdown",
    ],
    "relationship_concise_markdown": ["relationship_concise_markdown", "delivery.relationship_concise_markdown"],
    "relationship_concise_docx": ["relationship_concise_docx", "delivery.relationship_concise_docx"],
    "relationship_concise_pdf": ["relationship_concise_pdf", "delivery.relationship_concise_pdf"],
    "relationship_concise_zip": ["relationship_concise_zip", "delivery.relationship_concise_zip"],
    "relationship_concise_mobile_html": [
        "relationship_concise_mobile_html",
        "delivery.relationship_concise_mobile_html",
    ],
    "relationship_fact_archive_markdown": ["relationship_fact_archive_markdown", "relationship_facts_markdown"],
    "relationship_workflow": ["relationship_workflow", "runtime.relationship_workflow"],
    "final_delivery": ["final_delivery"],
    "project_readme": ["project_readme"],
    "finalize_check": ["finalize_check"],
}

CANONICAL_DATA_ALIASES = {
    "bazi": ["data.bazi", "data_bazi"],
    "ziwei": ["data.ziwei", "data_ziwei"],
    "western": ["data.western", "data_western"],
    "combo": ["data.combo", "data_combo"],
    "relationship": ["data.relationship", "data_relationship"],
    "time_sensitivity": ["data.time_sensitivity", "time_sensitivity"],
}

LEGACY_ALIAS_SUNSET = "2026-07-31"

RELATIONSHIP_REQUIRED_ARTIFACTS = [
    "relationship_fact_archive_markdown",
    "relationship_workflow",
    "relationship_mobile_html",
    "relationship_concise_source_markdown",
    "relationship_concise_pdf",
    "relationship_concise_mobile_html",
    "longform_markdown",
    "longform_pdf",
    "final_delivery",
]

RELATIONSHIP_LONGFORM_MARKERS = [
    "关系总评",
    "现实锚点",
    "情感底色",
    "八字格局",
    "日主互动",
    "互动张力",
    "神煞气质",
    "大运流年",
    "西占吸引",
    "MBTI语言",
    "距离节奏",
    "亲近边界",
    "事业交集",
    "家庭生活",
    "财富投入",
    "精力照顾",
    "关系阶段",
    "过去年份",
    "未来年份",
    "互补价值",
    "相处心法",
    "综合评语",
]

RUNTIME_CONTRACT_POLICY = {
    "schema_version": "0.1.0",
    "canonical_required_artifacts": [
        "fact_archive_markdown",
        "longform_markdown",
        "longform_pdf",
        "rich_mobile_html",
        "concise_markdown",
        "concise_pdf",
        "concise_mobile_html",
        "final_delivery",
    ],
    "canonical_reader_delivery_artifacts": [
        "longform_pdf",
        "rich_mobile_html",
        "concise_pdf",
        "concise_mobile_html",
    ],
    "relationship_reader_delivery_artifacts": [
        "longform_pdf",
        "relationship_mobile_html",
        "relationship_concise_pdf",
        "relationship_concise_mobile_html",
    ],
    "canonical_required_data": ["combo"],
    "optional_debug_artifacts": ["main_html"],
    "legacy_alias_sunset": LEGACY_ALIAS_SUNSET,
    "legacy_aliases": {
        "main_html": ["html_report"],
        "fact_archive_markdown": ["facts_markdown", "fact_archive_md", "data.fact_archive_markdown"],
        "longform_markdown": ["longform_source_md", "drafts.longform_markdown"],
        "longform_pdf": ["reader_pdf", "rich_pdf", "delivery.rich_pdf"],
        "concise_markdown": ["concise_source_md", "delivery.concise_markdown"],
        "concise_docx": ["delivery.concise_docx"],
        "concise_pdf": ["delivery.concise_pdf"],
        "concise_zip": ["delivery.concise_zip"],
        "mobile_html": ["reader_mobile_html", "delivery.mobile_html"],
        "concise_mobile_html": ["delivery.concise_mobile_html"],
        "rich_mobile_html": ["delivery.rich_mobile_html"],
        "relationship_mobile_html": ["delivery.relationship_mobile_html"],
        "relationship_concise_source_markdown": ["drafts.relationship_concise_markdown"],
        "relationship_concise_markdown": ["delivery.relationship_concise_markdown"],
        "relationship_concise_docx": ["delivery.relationship_concise_docx"],
        "relationship_concise_pdf": ["delivery.relationship_concise_pdf"],
        "relationship_concise_zip": ["delivery.relationship_concise_zip"],
        "relationship_concise_mobile_html": ["delivery.relationship_concise_mobile_html"],
        "relationship_fact_archive_markdown": ["relationship_facts_markdown"],
        "relationship_workflow": ["runtime.relationship_workflow"],
        "data.combo": ["data_combo"],
        "data.relationship": ["data_relationship"],
        "data.bazi": ["data_bazi"],
        "data.ziwei": ["data_ziwei"],
        "data.western": ["data_western"],
    },
    "gate_freeze": {
        "effective_date": "2026-06-13",
        "rule": "Do not add new gate scripts unless fixing a hard error or explicitly approved.",
        "reuse_first": [
            "scripts/finalize_case.py",
            "scripts/audit_longform_consistency.py",
            "scripts/create_followup_context.py",
            "scripts/create_retrospective_intake.py",
        ],
    },
    "knowledge_growth_priority": {
        "prefer": "approved deidentified case retrospectives with clear reader feedback",
        "avoid": "new generic writing rules without a real case counterexample",
        "minimum_before_new_rules": "at least one approved retrospective or explicit reader counterexample",
    },
    "large_file_split": {
        "soft_limit_kb": {
            "scripts/xuanxue_console.py": 75,
            "scripts/test_xuanxue_console.py": 65,
        },
        "completed_splits": [
            "scripts/xuanxue_longform.py",
            "scripts/xuanxue_western.py",
            "scripts/test_xuanxue_runtime.py",
            "scripts/test_xuanxue_relationship.py",
            "scripts/test_xuanxue_delivery.py",
        ],
        "next_split_targets": [
            "cli entrypoints",
            "bazi calculators",
            "ziwei calculators",
            "runtime contract tests",
        ],
    },
}


def runtime_contract_policy() -> dict[str, Any]:
    """Return a copy of the run artifact contract and maintenance policy."""

    return copy.deepcopy(RUNTIME_CONTRACT_POLICY)


def _get_nested(data: dict[str, Any], dotted_key: str) -> Any:
    current: Any = data
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _first_value(data: dict[str, Any], aliases: list[str]) -> Any:
    for alias in aliases:
        value = _get_nested(data, alias)
        if value:
            return value
    return None


def _existing_path_value(value: Any) -> str | None:
    if not value:
        return None
    try:
        path = Path(str(value))
    except (TypeError, ValueError):
        return None
    return str(path) if path.exists() else None


def _first_existing_value(data: dict[str, Any], aliases: list[str]) -> str | None:
    for alias in aliases:
        value = _existing_path_value(_get_nested(data, alias))
        if value:
            return value
    return None


def _first_existing(candidates: list[Path]) -> str | None:
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def _glob_one(directory: Path | None, patterns: list[str], *, exclude_contains: list[str] | None = None) -> str | None:
    if directory is None or not directory.exists():
        return None
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(sorted(directory.glob(pattern)))
    files = [path for path in matches if path.is_file()]
    if exclude_contains:
        files = [path for path in files if not any(token in path.name for token in exclude_contains)]
    if files:
        return str(sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[0])
    return None


def _path_from_manifest(manifest: dict[str, Any], key: str) -> Path | None:
    raw = manifest.get("paths", {}).get(key) if isinstance(manifest.get("paths"), dict) else None
    return Path(raw) if raw else None


def _is_relationship_run(manifest: dict[str, Any], artifacts: dict[str, Any], data_artifacts: dict[str, Any]) -> bool:
    if manifest.get("relationship_context") or manifest.get("source_manifests"):
        return True
    if data_artifacts.get("relationship"):
        return True
    if artifacts.get("relationship_fact_archive_markdown") or artifacts.get("relationship_mobile_html"):
        return True
    case_id = str(manifest.get("case_id") or "")
    return "relationship" in case_id.lower() or "合盘" in str(manifest.get("reader_name") or "")


def _ensure_list_value(target: dict[str, Any], key: str, value: list[Any], changes: list[str]) -> None:
    if target.get(key) != value:
        target[key] = copy.deepcopy(value)
        changes.append(f"validation_expectations.{key}")


def _ensure_scalar_value(target: dict[str, Any], key: str, value: Any, changes: list[str]) -> None:
    if target.get(key) != value:
        target[key] = value
        changes.append(f"validation_expectations.{key}")


def _ensure_default_scalar_value(target: dict[str, Any], key: str, value: Any, changes: list[str]) -> None:
    if key not in target or target.get(key) in (None, ""):
        target[key] = value
        changes.append(f"validation_expectations.{key}")


def _normalize_relationship_expectations(
    normalized: dict[str, Any],
    artifacts: dict[str, Any],
    data_artifacts: dict[str, Any],
    changes: list[str],
) -> None:
    if not _is_relationship_run(normalized, artifacts, data_artifacts):
        return
    expectations = normalized.setdefault("validation_expectations", {})
    if not isinstance(expectations, dict):
        expectations = {}
        normalized["validation_expectations"] = expectations
        changes.append("validation_expectations")

    _ensure_list_value(expectations, "required_delivery_variants", ["rich", "relationship_concise"], changes)
    _ensure_list_value(expectations, "required_data", ["relationship"], changes)
    _ensure_list_value(expectations, "required_modules", [], changes)
    _ensure_list_value(expectations, "required_artifacts", RELATIONSHIP_REQUIRED_ARTIFACTS, changes)
    _ensure_list_value(expectations, "longform_markers", RELATIONSHIP_LONGFORM_MARKERS, changes)
    _ensure_list_value(expectations, "fact_archive_markers", ["合盘事实复查档案", "现实专题交集事实", "写作约束"], changes)
    _ensure_list_value(expectations, "pdf_text_markers", ["合盘", "关系总评"], changes)
    _ensure_default_scalar_value(expectations, "min_longform_chars", 17000, changes)


def normalize_manifest(manifest: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return a copy with canonical artifact keys filled from known aliases."""

    normalized = copy.deepcopy(manifest)
    changes: list[str] = []
    paths = normalized.setdefault("paths", {})
    artifacts = normalized.setdefault("artifacts", {})
    if not isinstance(paths, dict):
        normalized["paths"] = paths = {}
    if not isinstance(artifacts, dict):
        normalized["artifacts"] = artifacts = {}

    run_dir = _path_from_manifest(normalized, "run_dir")
    data_dir = _path_from_manifest(normalized, "data_dir")
    runtime_dir = _path_from_manifest(normalized, "runtime_dir")
    drafts_dir = _path_from_manifest(normalized, "drafts_dir")
    delivery_dir = _path_from_manifest(normalized, "delivery_dir")
    case_id = str(normalized.get("case_id") or "").strip()

    if run_dir and "retrospectives_dir" not in paths:
        paths["retrospectives_dir"] = str(run_dir / "retrospectives")
        changes.append("paths.retrospectives_dir")
    if run_dir and "dialogue_dir" not in paths:
        calibration_dir = _path_from_manifest(normalized, "calibration_dir") or run_dir / "calibration"
        paths["dialogue_dir"] = str(calibration_dir / "dialogue")
        changes.append("paths.dialogue_dir")

    fallback_artifacts: dict[str, str | None] = {
        "project_readme": str(PROJECT_ROOT / "README.md"),
        "finalize_check": str(PROJECT_ROOT / "scripts" / "finalize_case.py"),
        "final_delivery": str(run_dir / "final-delivery.md") if run_dir else None,
        "main_html": _first_existing([run_dir / f"{case_id}.html"]) if run_dir and case_id else None,
        "fact_archive_markdown": (
            _first_existing([data_dir / f"{case_id}-facts.md", data_dir / f"{case_id}-fact-archive.md"])
            if data_dir and case_id
            else None
        )
        or _glob_one(data_dir, ["*-facts.md", "*-fact-archive.md", "*-facts-archive.md"])
        or _glob_one(runtime_dir, ["*-facts.md", "*-fact-archive.md", "*-facts-archive.md"]),
        "longform_markdown": (
            _first_existing([drafts_dir / f"{case_id}-longform.md"])
            if drafts_dir and case_id
            else None
        )
        or _glob_one(drafts_dir, ["*-longform.md"]),
        "longform_pdf": _glob_one(delivery_dir, ["*丰富版.pdf", "*长文*.pdf", "*-rich.pdf"]),
        "concise_markdown": (
            _glob_one(delivery_dir, ["*简洁版.md", "*concise*.md"])
            or (
                _first_existing([drafts_dir / f"{case_id}-concise-report.md"])
                if drafts_dir and case_id
                else _glob_one(drafts_dir, ["*-concise-report.md", "*concise*.md"])
            )
        ),
        "concise_docx": _glob_one(delivery_dir, ["*简洁版.docx", "*concise*.docx"], exclude_contains=["合盘"]),
        "concise_pdf": _glob_one(delivery_dir, ["*简洁版.pdf", "*concise*.pdf"]),
        "concise_zip": _glob_one(delivery_dir, ["*简洁版.zip", "*concise*.zip"], exclude_contains=["合盘"]),
        "mobile_html": _glob_one(delivery_dir, ["*手机阅读.html", "*mobile*.html"]),
        "concise_mobile_html": _glob_one(
            delivery_dir,
            ["*简洁版-手机阅读.html", "*concise*mobile*.html"],
            exclude_contains=["合盘"],
        ),
        "rich_mobile_html": _glob_one(delivery_dir, ["*丰富版-手机阅读.html", "*rich*mobile*.html"]),
        "relationship_mobile_html": _glob_one(
            delivery_dir,
            ["*合盘*手机阅读.html", "*relationship*mobile*.html"],
            exclude_contains=["简洁版", "concise"],
        ),
        "relationship_concise_source_markdown": (
            _first_existing([drafts_dir / f"{case_id}-relationship-concise.md"])
            if drafts_dir and case_id
            else None
        )
        or _glob_one(drafts_dir, ["*-relationship-concise.md", "*relationship*concise*.md"]),
        "relationship_concise_markdown": _glob_one(delivery_dir, ["*合盘简洁版.md", "*relationship*concise*.md"]),
        "relationship_concise_docx": _glob_one(delivery_dir, ["*合盘简洁版.docx", "*relationship*concise*.docx"]),
        "relationship_concise_pdf": _glob_one(delivery_dir, ["*合盘简洁版.pdf", "*relationship*concise*.pdf"]),
        "relationship_concise_zip": _glob_one(delivery_dir, ["*合盘简洁版.zip", "*relationship*concise*.zip"]),
        "relationship_concise_mobile_html": _glob_one(
            delivery_dir,
            ["*合盘简洁版-手机阅读.html", "*relationship*concise*mobile*.html"],
        ),
        "relationship_fact_archive_markdown": (
            _first_existing([data_dir / f"{case_id}-relationship-facts.md"])
            if data_dir and case_id
            else None
        )
        or _glob_one(data_dir, ["*-relationship-facts.md", "*合盘*facts.md"]),
        "relationship_workflow": (
            _first_existing([runtime_dir / "relationship_workflow.json"])
            if runtime_dir
            else None
        ),
    }

    for key, aliases in CANONICAL_ARTIFACT_ALIASES.items():
        value = (
            _existing_path_value(artifacts.get(key))
            or _first_existing_value(artifacts, aliases)
            or fallback_artifacts.get(key)
            or artifacts.get(key)
            or _first_value(artifacts, aliases)
        )
        if value and artifacts.get(key) != value:
            artifacts[key] = str(value)
            changes.append(f"artifacts.{key}")

    data_artifacts = artifacts.setdefault("data", {})
    if not isinstance(data_artifacts, dict):
        data_artifacts = {}
        artifacts["data"] = data_artifacts
        changes.append("artifacts.data")

    data_fallbacks: dict[str, str | None] = {}
    if data_dir and case_id:
        for module in ["bazi", "ziwei", "western", "combo", "relationship", "time_sensitivity"]:
            suffix = "time-sensitivity" if module == "time_sensitivity" else module
            data_fallbacks[module] = _first_existing([data_dir / f"{case_id}-{suffix}.json"])

    for key, aliases in CANONICAL_DATA_ALIASES.items():
        value = (
            _existing_path_value(data_artifacts.get(key))
            or _first_existing_value(artifacts, aliases)
            or data_fallbacks.get(key)
            or data_artifacts.get(key)
            or _first_value(artifacts, aliases)
        )
        if value and data_artifacts.get(key) != value:
            data_artifacts[key] = str(value)
            changes.append(f"artifacts.data.{key}")

    _normalize_relationship_expectations(normalized, artifacts, data_artifacts, changes)

    return normalized, changes


def normalize_manifest_file(path: Path, *, write: bool = False) -> tuple[dict[str, Any], list[str]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    normalized, changes = normalize_manifest(manifest)
    if write and changes:
        path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return normalized, changes
