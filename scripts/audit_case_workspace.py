#!/usr/bin/env python3
"""Validate an external xuanxue case workspace manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit an external xuanxue case workspace.")
    parser.add_argument("--manifest", required=True, help="Path to case_manifest.json.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    failures: list[str] = []
    if not manifest_path.exists():
        failures.append(f"manifest missing: {manifest_path}")
        print(json.dumps({"passed": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = manifest.get("paths", {})
    for key in [
        "input_dir",
        "run_dir",
        "runtime_dir",
        "data_dir",
        "drafts_dir",
        "delivery_dir",
        "logs_dir",
        "calibration_dir",
        "dialogue_dir",
        "retrospectives_dir",
    ]:
        if key not in paths:
            failures.append(f"path missing from manifest: {key}")
            continue
        path = Path(paths[key]).resolve()
        if is_relative_to(path, PROJECT_ROOT):
            failures.append(f"{key} is inside project repo: {path}")
        if not path.exists():
            failures.append(f"{key} does not exist: {path}")
    if is_relative_to(manifest_path, PROJECT_ROOT):
        failures.append(f"manifest is inside project repo: {manifest_path}")
    result = {
        "passed": not failures,
        "manifest": str(manifest_path),
        "case_id": manifest.get("case_id"),
        "run_id": manifest.get("run_id"),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
