#!/usr/bin/env python3
"""Create an external deidentified case retrospective candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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

FORBIDDEN_PATTERNS = [
    r"[A-Za-z]:\\",
    r"wxid_",
    r"run_20\d{6}_",
    r"\.jpg\b",
    r"\.jpeg\b",
    r"\.png\b",
    r"\.webp\b",
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
    r"\b\d{1,2}:\d{2}\b",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a deidentified retrospective candidate in an external run folder.")
    parser.add_argument("--manifest", required=True, help="External case_manifest.json path.")
    parser.add_argument("--slug", required=True, help="Short ASCII slug, e.g. reader-hook-summary.")
    parser.add_argument("--title", required=True, help="Deidentified retrospective title.")
    parser.add_argument("--case-type", default="xuanxue-longform", help="Abstract case type.")
    parser.add_argument("--domain", action="append", default=[], help="Affected knowledge domain. Can repeat.")
    parser.add_argument("--date-bucket", help="Coarse bucket such as 2026-Q2. Defaults to current quarter.")
    parser.add_argument("--evidence-summary", required=True, help="Abstract evidence only; no customer facts or quotes.")
    parser.add_argument("--target-artifact", action="append", required=True, help="Project artifact to improve. Can repeat.")
    parser.add_argument(
        "--promotion",
        action="append",
        default=[],
        help="Promotion item as artifact|change_type|summary. Can repeat.",
    )
    parser.add_argument("--counterexample", action="append", default=[], help="Counterexample or misuse risk. Can repeat.")
    parser.add_argument("--limit", action="append", default=[], help="Applicability limit. Can repeat.")
    parser.add_argument("--output", help="Output JSON path. Defaults to <run_dir>/retrospectives/<id>.candidate.json.")
    return parser.parse_args()


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "retrospective"


def current_quarter() -> str:
    now = datetime.now()
    quarter = ((now.month - 1) // 3) + 1
    return f"{now.year}-Q{quarter}"


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"manifest missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_clean_text(label: str, value: Any, failures: list[str]) -> None:
    serialized = json.dumps(value, ensure_ascii=False)
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, serialized, flags=re.IGNORECASE):
            failures.append(f"{label} contains forbidden private/local pattern: {pattern}")


def parse_promotions(raw_items: list[str], target_artifacts: list[str]) -> list[dict[str, str]]:
    promotions: list[dict[str, str]] = []
    for item in raw_items:
        parts = item.split("|", 2)
        if len(parts) != 3:
            raise SystemExit("--promotion must use artifact|change_type|summary")
        promotions.append({"artifact": parts[0].strip(), "change_type": parts[1].strip(), "summary": parts[2].strip()})
    if promotions:
        return promotions
    return [
        {
            "artifact": artifact,
            "change_type": "review_required",
            "summary": "人工复核后再决定是否改动该 artifact。",
        }
        for artifact in target_artifacts
    ]


def infer_domains(target_artifacts: list[str]) -> list[str]:
    domains: set[str] = set()
    for artifact in target_artifacts:
        normalized = artifact.replace("\\", "/")
        parts = normalized.split("/")
        if len(parts) >= 2 and parts[0] == "knowledge" and parts[1] in ALLOWED_DOMAINS:
            domains.add(parts[1])
        if normalized.startswith("templates/") or normalized.startswith("service/"):
            domains.add("writing")
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
        if normalized.startswith("scripts/audit_") or normalized.startswith("scripts/validate_"):
            domains.add("quality")
        if normalized.startswith("knowledge/sources/"):
            domains.add("source_register")
        if normalized.startswith("knowledge/completeness/"):
            domains.add("completeness")
        if normalized.startswith("knowledge/case-retrospectives/"):
            domains.add("case_retrospectives")
    return sorted(domains)


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path)
    paths = manifest.get("paths", {})
    run_dir = Path(paths.get("run_dir", "")).resolve()
    if not run_dir.exists():
        raise SystemExit(f"run_dir missing or invalid in manifest: {run_dir}")
    if is_relative_to(run_dir, PROJECT_ROOT):
        raise SystemExit("run_dir must be outside project repo")

    slug = slugify(args.slug)
    retro_id = f"CR-{datetime.now().strftime('%Y%m%d')}-{slug}"
    target_artifacts = [item.strip().replace("\\", "/") for item in args.target_artifact if item.strip()]
    if not target_artifacts:
        raise SystemExit("at least one --target-artifact is required")
    for artifact in target_artifacts:
        if not (PROJECT_ROOT / artifact).exists():
            raise SystemExit(f"target artifact does not exist: {artifact}")
    raw_domains = [item.strip() for item in args.domain if item.strip()]
    inferred_domains = infer_domains(target_artifacts)
    domains = sorted(set(raw_domains) | set(inferred_domains))
    unknown_domains = sorted(set(domains) - ALLOWED_DOMAINS)
    if unknown_domains:
        raise SystemExit(f"unknown retrospective domains: {unknown_domains}")
    if not domains:
        raise SystemExit("at least one --domain is required when domains cannot be inferred from target artifacts")

    counterexamples = args.counterexample or ["如果没有人工复核或反例支持，不能把一次反馈升为通用规则。"]
    limits = args.limit or ["这是候选复盘，只能作为人工复核材料；未批准前不得进入全局知识库。"]
    item: dict[str, Any] = {
        "schema_version": "0.1.0",
        "id": retro_id,
        "title": args.title,
        "status": "candidate",
        "human_approved": False,
        "approved_by": "",
        "privacy": {
            "deidentified": True,
            "contains_birth_data": False,
            "contains_client_name": False,
            "contains_local_paths": False,
            "contains_delivery_text": False,
        },
        "source_case": {
            "case_type": args.case_type,
            "date_bucket": args.date_bucket or current_quarter(),
            "raw_material_location": "external-only",
            "case_id_hash": stable_hash(str(manifest.get("case_id", ""))),
            "run_id_hash": stable_hash(str(manifest.get("run_id", ""))),
        },
        "evidence_summary": args.evidence_summary,
        "domains": domains,
        "target_artifacts": target_artifacts,
        "promotions": parse_promotions(args.promotion, target_artifacts),
        "counterexamples": counterexamples,
        "limits": limits,
        "approval_checklist": [
            "确认没有客户姓名、昵称、出生年月日时、截图路径、本机路径或报告原文。",
            "确认 evidence_summary 只保留抽象机制。",
            "确认 promotions 指向真实项目 artifact。",
            "确认至少一个反例或限制仍然成立。",
            "人工批准后再运行 promote_case_retrospective.py。",
        ],
    }

    failures: list[str] = []
    assert_clean_text("candidate", item, failures)
    if failures:
        print(json.dumps({"passed": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1

    retrospectives_dir = Path(paths.get("retrospectives_dir", run_dir / "retrospectives")).resolve()
    if is_relative_to(retrospectives_dir, PROJECT_ROOT):
        raise SystemExit("retrospectives_dir must stay outside project repo")
    output = Path(args.output).resolve() if args.output else retrospectives_dir / f"{retro_id}.candidate.json"
    if is_relative_to(output, PROJECT_ROOT):
        raise SystemExit("candidate output must stay outside project repo")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": True,
                "candidate": str(output),
                "id": retro_id,
                "human_approved": False,
                "next_step": "After human approval, run promote_case_retrospective.py with --approved-by.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
