#!/usr/bin/env python3
"""Create a relationship run and build deterministic relationship facts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from create_case_workspace import is_relative_to, load_profile, resolve_external_root, slugify
from validate_relationship_report import REQUIRED_HEADING_TOPICS


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an external relationship/synastry workspace.")
    parser.add_argument("--case-id", help="Stable relationship case id. Defaults to relationship-<a>-<b>.")
    parser.add_argument("--reader-name", default="", help="Reader-facing name, optional.")
    parser.add_argument("--external-root", help="Override external root.")
    parser.add_argument("--run-id", help="Run id. Defaults to run_<timestamp>.")
    parser.add_argument("--person-a-manifest", required=True, help="First person's existing case_manifest.json.")
    parser.add_argument("--person-b-manifest", required=True, help="Second person's existing case_manifest.json.")
    parser.add_argument("--person-a-label", required=True)
    parser.add_argument("--person-b-label", required=True)
    parser.add_argument("--relationship-status", required=True, help="Known real-world relationship status, e.g. 男女朋友.")
    parser.add_argument("--distance-status", required=True, help="Known distance status, e.g. 异地.")
    parser.add_argument("--person-a-mbti-type")
    parser.add_argument("--person-b-mbti-type")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_python(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
        encoding="utf-8",
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"stdout": proc.stdout.strip()}


def powershell_quote(path: str | Path) -> str:
    return '"' + str(path).replace('"', '`"') + '"'


def build_workflow_manifest(manifest_path: Path, run_dir: Path, case_id: str, reader_name: str) -> dict[str, Any]:
    draft = run_dir / "drafts" / f"{case_id}-relationship-longform.md"
    concise_draft = run_dir / "drafts" / f"{case_id}-relationship-concise.md"
    facts_json = run_dir / "data" / f"{case_id}-relationship.json"
    delivery = run_dir / "delivery"
    basename = f"{reader_name or case_id}合盘总评-丰富版"
    concise_basename = f"{reader_name or case_id}合盘简洁版"
    delivery_md = delivery / f"{basename}.md"
    delivery_html = delivery / f"{basename}-手机阅读.html"
    concise_delivery_md = delivery / f"{concise_basename}.md"
    concise_delivery_html = delivery / f"{concise_basename}-手机阅读.html"
    return {
        "schema_version": "0.1.0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "manifest": str(manifest_path),
        "draft_target": str(draft),
        "concise_draft_target": str(concise_draft),
        "required_template": "templates/relationship-rich-template.md",
        "concise_template": "templates/relationship-concise-template.md",
        "reader_contract": [
            "正文使用第三人称。",
            "H1 必须保留双方对象和合盘属性。",
            "现实输入只限已知 relationship_status 与 distance_status。",
            "先写牵引、互补和可经营价值，再写张力与误读；身体吸引语言必须服从 relationship_mode。",
            "完整交付默认另写合盘简洁版，方便双方手机快速阅读。",
            "对外读者交付默认为丰富 PDF、丰富手机阅读器、简洁 PDF 和简洁手机阅读器；Markdown/DOCX/ZIP 只作源稿、编辑或按需导出。",
            "手机阅读 HTML 使用单盘/合盘统一阅读器 UI 标准。",
        ],
        "commands": {
            "validate": (
                "python scripts/validate_relationship_report.py "
                f"{powershell_quote(draft)} --facts-json {powershell_quote(facts_json)} "
                "--min-chars 17000 --scenario-min 12"
            ),
            "validate_relationship_concise": (
                "python scripts/validate_relationship_report.py "
                f"{powershell_quote(concise_draft)} --facts-json {powershell_quote(facts_json)} "
                "--profile concise"
            ),
            "package_reader": (
                "python scripts/package_reader_delivery.py "
                f"{powershell_quote(draft)} --output-dir {powershell_quote(delivery)} "
                f"--basename {powershell_quote(basename)} "
                "--manifest "
                f"{powershell_quote(manifest_path)} --artifact-prefix rich --avoid-locked --json"
            ),
            "package_mobile_html": (
                "python scripts/package_mobile_html.py "
                f"{powershell_quote(delivery_md)} --output {powershell_quote(delivery_html)} "
                f"--manifest {powershell_quote(manifest_path)} --artifact-key relationship_mobile_html"
            ),
            "package_relationship_concise": (
                "python scripts/package_reader_delivery.py "
                f"{powershell_quote(concise_draft)} --output-dir {powershell_quote(delivery)} "
                f"--basename {powershell_quote(concise_basename)} --no-subtitle "
                f"--manifest {powershell_quote(manifest_path)} "
                "--artifact-prefix relationship_concise --avoid-locked --json"
            ),
            "package_relationship_concise_mobile_html": (
                "python scripts/package_mobile_html.py "
                f"{powershell_quote(concise_delivery_md)} --output {powershell_quote(concise_delivery_html)} "
                f"--manifest {powershell_quote(manifest_path)} "
                "--artifact-key relationship_concise_mobile_html"
            ),
            "finalize": f"python scripts/finalize_case.py --manifest {powershell_quote(manifest_path)} --normalize-manifest --write-status",
        },
    }


def main() -> int:
    args = parse_args()
    profile = load_profile()
    external_root = resolve_external_root(args.external_root)
    if is_relative_to(external_root, PROJECT_ROOT):
        print(
            json.dumps(
                {
                    "passed": False,
                    "error": "external root must not be inside project repo",
                    "project_root": str(PROJECT_ROOT),
                    "external_root": str(external_root),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    person_a_manifest = Path(args.person_a_manifest).resolve()
    person_b_manifest = Path(args.person_b_manifest).resolve()
    person_a = load_json(person_a_manifest)
    person_b = load_json(person_b_manifest)
    default_case = f"relationship-{person_a.get('case_id') or args.person_a_label}-{person_b.get('case_id') or args.person_b_label}"
    case_id = slugify(args.case_id or default_case)
    run_id = args.run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    input_dir = external_root / profile.get("inputs_subdir", "inputs") / case_id
    run_dir = external_root / profile.get("runs_subdir", "runs") / case_id / run_id
    paths = {
        "input_dir": input_dir,
        "run_dir": run_dir,
        "runtime_dir": run_dir / "runtime",
        "data_dir": run_dir / "data",
        "drafts_dir": run_dir / "drafts",
        "delivery_dir": run_dir / "delivery",
        "logs_dir": run_dir / "logs",
        "calibration_dir": run_dir / "calibration",
        "dialogue_dir": run_dir / "calibration" / "dialogue",
        "retrospectives_dir": run_dir / "retrospectives",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    reader_name = args.reader_name or f"{args.person_a_label}与{args.person_b_label}"
    manifest = {
        "schema_version": "0.1.0",
        "case_id": case_id,
        "reader_name": reader_name,
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(PROJECT_ROOT),
        "external_root": str(external_root),
        "paths": {key: str(path) for key, path in paths.items()},
        "status": {
            "stage": "relationship_created",
            "human_approved": False,
            "notes": "Relationship workspace created. Build reader draft from relationship facts and template.",
        },
        "source_manifests": {
            "person_a": str(person_a_manifest),
            "person_b": str(person_b_manifest),
        },
        "relationship_context": {
            "person_a_label": args.person_a_label,
            "person_b_label": args.person_b_label,
            "relationship_status": args.relationship_status,
            "distance_status": args.distance_status,
            "person_a_mbti_type": args.person_a_mbti_type or "",
            "person_b_mbti_type": args.person_b_mbti_type or "",
        },
        "validation_expectations": {
            "compare_recent_longforms": 2,
            "capture_followup_dialogue": True,
            "required_delivery_variants": ["rich", "relationship_concise"],
            "reader_delivery_artifacts": [
                "longform_pdf",
                "relationship_mobile_html",
                "relationship_concise_pdf",
                "relationship_concise_mobile_html",
            ],
            "required_data": ["relationship"],
            "required_modules": [],
            "required_artifacts": [
                "relationship_fact_archive_markdown",
                "relationship_workflow",
                "relationship_mobile_html",
                "relationship_concise_source_markdown",
                "relationship_concise_pdf",
                "relationship_concise_mobile_html",
                "longform_markdown",
                "longform_pdf",
                "final_delivery",
            ],
            "longform_markers": REQUIRED_HEADING_TOPICS,
            "fact_archive_markers": ["合盘事实复查档案", "现实专题交集事实", "写作约束"],
            "pdf_text_markers": ["合盘", "关系总评"],
            "min_longform_chars": 17000,
        },
    }
    manifest_path = run_dir / profile.get("case_manifest_name", "case_manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    knowledge_context = run_python(
        [
            str(PROJECT_ROOT / "scripts" / "build_knowledge_context.py"),
            "--manifest",
            str(manifest_path),
            "--module",
            "bazi",
            "--module",
            "ziwei",
            "--module",
            "western",
            "--module",
            "mbti",
            "--module",
            "relationship",
        ]
    )
    retrospective_intake = run_python(
        [
            str(PROJECT_ROOT / "scripts" / "create_retrospective_intake.py"),
            "--manifest",
            str(manifest_path),
        ]
    )
    relationship_args = [
        str(PROJECT_ROOT / "scripts" / "build_relationship_facts.py"),
        "--manifest",
        str(manifest_path),
        "--person-a-manifest",
        str(person_a_manifest),
        "--person-b-manifest",
        str(person_b_manifest),
        "--person-a-label",
        args.person_a_label,
        "--person-b-label",
        args.person_b_label,
        "--relationship-status",
        args.relationship_status,
        "--distance-status",
        args.distance_status,
    ]
    if args.person_a_mbti_type:
        relationship_args.extend(["--person-a-mbti-type", args.person_a_mbti_type])
    if args.person_b_mbti_type:
        relationship_args.extend(["--person-b-mbti-type", args.person_b_mbti_type])
    relationship_facts = run_python(relationship_args)

    workflow = build_workflow_manifest(manifest_path, run_dir, case_id, reader_name)
    workflow_path = paths["runtime_dir"] / "relationship_workflow.json"
    workflow_path.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    current_manifest = load_json(manifest_path)
    artifacts = current_manifest.setdefault("artifacts", {})
    artifacts["relationship_workflow"] = str(workflow_path)
    artifacts["relationship_concise_source_markdown"] = workflow["concise_draft_target"]
    current_manifest["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(current_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "passed": True,
                "manifest": str(manifest_path),
                "run_dir": str(run_dir),
                "relationship_facts": relationship_facts,
                "knowledge_context": knowledge_context,
                "retrospective_intake": retrospective_intake,
                "workflow": str(workflow_path),
                "next_commands": workflow["commands"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
