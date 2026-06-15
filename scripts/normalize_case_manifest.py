#!/usr/bin/env python3
"""Normalize an external xuanxue case manifest to the current artifact contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from case_manifest_contract import normalize_manifest_file, runtime_contract_policy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize case_manifest.json artifact keys.")
    parser.add_argument("--manifest", required=True, help="External case_manifest.json path.")
    parser.add_argument("--write", action="store_true", help="Write normalized keys back to the manifest.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(
            json.dumps(
                {"passed": False, "manifest": str(manifest_path), "failures": ["manifest missing"]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    normalized, changes = normalize_manifest_file(manifest_path, write=args.write)
    artifacts = normalized.get("artifacts", {})
    data = artifacts.get("data", {}) if isinstance(artifacts, dict) else {}
    policy = runtime_contract_policy()
    required_artifacts = policy["canonical_required_artifacts"]
    missing_artifacts = []
    for key in required_artifacts:
        raw = artifacts.get(key)
        if not raw:
            missing_artifacts.append(key)
        elif not Path(str(raw)).exists():
            missing_artifacts.append(f"{key}: {raw}")
    missing_data = []
    for key in policy["canonical_required_data"]:
        raw = data.get(key) if isinstance(data, dict) else None
        if not raw:
            missing_data.append(key)
        elif not Path(str(raw)).exists():
            missing_data.append(f"{key}: {raw}")
    result = {
        "passed": not missing_artifacts and not missing_data,
        "manifest": str(manifest_path),
        "written": bool(args.write and changes),
        "changes": changes,
        "missing_artifacts": missing_artifacts,
        "missing_data": missing_data,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
