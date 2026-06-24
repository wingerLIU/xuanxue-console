#!/usr/bin/env python3
"""Promote a human-approved retrospective candidate into the global knowledge base."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RETRO_DIR = PROJECT_ROOT / "knowledge" / "case-retrospectives"
AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "audit_case_retrospectives.py"

FORBIDDEN_PATTERNS = [
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

ALLOWED_DOMAINS = {
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote a deidentified retrospective candidate.")
    parser.add_argument("--candidate", required=True, help="External candidate JSON path.")
    parser.add_argument("--approved-by", required=True, help="Human approver label.")
    parser.add_argument(
        "--status",
        choices=["curated", "verified"],
        default="curated",
        help="Promoted retrospectives must be curated or verified. Candidate files stay external.",
    )
    parser.add_argument("--retro-dir", help=argparse.SUPPRESS)
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing retrospective JSON.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview promotion without writing.")
    return parser.parse_args()


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"candidate missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_item(item: dict[str, Any], failures: list[str]) -> None:
    required = [
        "schema_version",
        "id",
        "title",
        "status",
        "human_approved",
        "privacy",
        "source_case",
        "evidence_summary",
        "domains",
        "target_artifacts",
        "promotions",
        "counterexamples",
        "limits",
    ]
    for key in required:
        if key not in item:
            failures.append(f"candidate missing {key}")
    if not re.match(r"^CR-[0-9]{8}-[a-z0-9-]+$", str(item.get("id", ""))):
        failures.append("candidate id must match CR-YYYYMMDD-slug")
    for artifact in item.get("target_artifacts", []):
        if not isinstance(artifact, str) or not (PROJECT_ROOT / artifact).exists():
            failures.append(f"target artifact missing: {artifact}")
    for key in ["domains", "promotions", "counterexamples", "limits"]:
        if not isinstance(item.get(key), list) or not item.get(key):
            failures.append(f"{key} must be a non-empty list")
    domains = item.get("domains", [])
    if isinstance(domains, list):
        unknown = sorted(set(str(domain) for domain in domains) - ALLOWED_DOMAINS)
        if unknown:
            failures.append(f"domains contain unknown values: {unknown}")
    serialized = json.dumps(item, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, serialized, flags=re.IGNORECASE):
            failures.append(f"candidate contains forbidden private/local pattern: {pattern}")


def main() -> int:
    args = parse_args()
    candidate_path = Path(args.candidate).resolve()
    if is_relative_to(candidate_path, PROJECT_ROOT):
        raise SystemExit("candidate should come from an external run folder, not the project repo")

    item = load_json(candidate_path)
    item["human_approved"] = True
    item["approved_by"] = args.approved_by.strip()
    item["status"] = args.status
    if not item["approved_by"]:
        raise SystemExit("--approved-by cannot be empty")

    failures: list[str] = []
    validate_item(item, failures)
    if failures:
        print(json.dumps({"passed": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1

    retro_dir = Path(args.retro_dir).resolve() if args.retro_dir else RETRO_DIR
    output = retro_dir / f"{item['id']}.json"
    if output.exists() and not args.overwrite:
        raise SystemExit(f"retrospective already exists: {output}")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "passed": True,
                    "dry_run": True,
                    "candidate": str(candidate_path),
                    "would_promote": str(output),
                    "id": item["id"],
                    "status": item["status"],
                    "domains": item.get("domains", []),
                    "target_artifacts": item.get("target_artifacts", []),
                    "audit_command": " ".join([sys.executable, str(AUDIT_SCRIPT)]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit_cmd = [sys.executable, str(AUDIT_SCRIPT)]
    if args.retro_dir:
        audit_cmd.extend(["--retro-dir", str(retro_dir)])
    proc = subprocess.run(
        audit_cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        try:
            output.unlink()
        finally:
            print(
                json.dumps(
                    {
                        "passed": False,
                        "promoted": str(output),
                        "rolled_back": True,
                        "audit_stdout": proc.stdout,
                        "audit_stderr": proc.stderr,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return 1

    print(
        json.dumps(
            {
                "passed": True,
                "promoted": str(output),
                "audit_stdout": proc.stdout,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
