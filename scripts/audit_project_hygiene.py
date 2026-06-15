#!/usr/bin/env python3
"""Audit that the project repo contains no case outputs or local runtime artifacts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from case_manifest_contract import runtime_contract_policy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IO_POLICY = PROJECT_ROOT / "config" / "io_policy.json"
RUNTIME_PROFILE = PROJECT_ROOT / "config" / "runtime_profile.json"


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return fallback


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def resolve_external_root(profile: dict[str, Any]) -> Path:
    env_name = profile.get("external_root_env", "XUANXUE_RUNS_ROOT")
    raw = os.environ.get(env_name) or profile.get("default_external_root") or r"%USERPROFILE%\Documents\xuanxue_console_runs"
    return Path(os.path.expandvars(str(raw))).expanduser().resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit xuanxue project hygiene.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument(
        "--strict-cache",
        action="store_true",
        help="Fail when generated Python cache directories are present instead of warning.",
    )
    return parser.parse_args()


def large_file_soft_limit_warnings(policy: dict[str, Any]) -> list[dict[str, Any]]:
    large_file_policy = policy.get("large_file_split", {})
    soft_limits = large_file_policy.get("soft_limit_kb", {}) if isinstance(large_file_policy, dict) else {}
    if not isinstance(soft_limits, dict):
        return []

    warnings: list[dict[str, Any]] = []
    for rel_path, limit_kb in sorted(soft_limits.items()):
        try:
            limit = float(limit_kb)
        except (TypeError, ValueError):
            continue
        path = PROJECT_ROOT / str(rel_path)
        if not path.exists() or not path.is_file():
            continue
        size_kb = path.stat().st_size / 1024
        if size_kb > limit:
            warnings.append(
                {
                    "path": str(path),
                    "size_kb": round(size_kb, 1),
                    "soft_limit_kb": limit,
                }
            )
    return warnings


def main() -> int:
    args = parse_args()
    policy = load_json(
        IO_POLICY,
        {
            "forbidden_root_dirs": ["reports", "output", "inputs", "runs", ".playwright-cli"],
            "forbidden_dir_names": ["__pycache__", ".pytest_cache"],
            "forbidden_artifact_extensions": [".zip", ".pdf", ".docx", ".html", ".png", ".jpg", ".jpeg", ".webp"],
            "allowed_artifact_roots": ["templates", "references", "knowledge", "service", "docs"],
        },
    )
    profile = load_json(RUNTIME_PROFILE, {})
    runtime_policy = runtime_contract_policy()
    failures: list[str] = []
    warnings: list[str] = []

    for name in policy.get("forbidden_root_dirs", []):
        path = PROJECT_ROOT / name
        if path.exists():
            failures.append(f"repo-local runtime/artifact dir exists: {path}")

    forbidden_dir_names = set(policy.get("forbidden_dir_names", []))
    for path in PROJECT_ROOT.rglob("*"):
        if path.is_dir() and path.name in forbidden_dir_names:
            message = f"generated cache dir exists: {path}"
            if args.strict_cache:
                failures.append(message)
            else:
                warnings.append(message)

    allowed_roots = {PROJECT_ROOT / item for item in policy.get("allowed_artifact_roots", [])}
    forbidden_exts = {str(item).lower() for item in policy.get("forbidden_artifact_extensions", [])}
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in forbidden_exts:
            continue
        if any(is_relative_to(path, root) for root in allowed_roots if root.exists()):
            continue
        failures.append(f"repo-local deliverable/media artifact exists: {path}")

    external_root = resolve_external_root(profile)
    if is_relative_to(external_root, PROJECT_ROOT):
        failures.append(f"external root is inside project repo: {external_root}")
    if not external_root.exists():
        warnings.append(f"external root does not exist yet: {external_root}")

    large_file_warnings = large_file_soft_limit_warnings(runtime_policy)
    for item in large_file_warnings:
        warnings.append(
            "file exceeds soft split limit: "
            f"{item['path']} ({item['size_kb']} KB > {item['soft_limit_kb']} KB)"
        )

    result = {
        "passed": not failures,
        "project_root": str(PROJECT_ROOT),
        "external_root": str(external_root),
        "large_file_soft_limits": large_file_warnings,
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
