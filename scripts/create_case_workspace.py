#!/usr/bin/env python3
"""Create an external xuanxue case workspace.

The project repo should contain reusable code and knowledge only. Case inputs,
drafts, data, delivery files, logs, and runtime manifests live under the
external root.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PROFILE = PROJECT_ROOT / "config" / "runtime_profile.json"


def load_profile() -> dict[str, Any]:
    if RUNTIME_PROFILE.exists():
        return json.loads(RUNTIME_PROFILE.read_text(encoding="utf-8"))
    return {
        "external_root_env": "XUANXUE_RUNS_ROOT",
        "default_external_root": r"%USERPROFILE%\Documents\xuanxue_console_runs",
        "inputs_subdir": "inputs",
        "runs_subdir": "runs",
        "case_manifest_name": "case_manifest.json",
    }


def resolve_external_root(value: str | None = None) -> Path:
    profile = load_profile()
    env_name = profile.get("external_root_env", "XUANXUE_RUNS_ROOT")
    raw = value or os.environ.get(env_name) or profile.get("default_external_root")
    if not raw:
        raise SystemExit("external root is not configured")
    return Path(os.path.expandvars(str(raw))).expanduser().resolve()


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-_")
    return text or "case"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an external xuanxue case workspace.")
    parser.add_argument("--case-id", required=True, help="Stable case id, e.g. demo-1991-08-15.")
    parser.add_argument("--reader-name", default="", help="Reader-facing name or nickname.")
    parser.add_argument("--external-root", help="Override external root. Defaults to XUANXUE_RUNS_ROOT or profile.")
    parser.add_argument("--run-id", help="Run id. Defaults to run_<timestamp>.")
    return parser.parse_args()


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

    case_id = slugify(args.case_id)
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

    manifest = {
        "schema_version": "0.1.0",
        "case_id": case_id,
        "reader_name": args.reader_name,
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(PROJECT_ROOT),
        "external_root": str(external_root),
        "paths": {key: str(path) for key, path in paths.items()},
        "status": {
            "stage": "created",
            "human_approved": False,
            "notes": "External workspace created. Put source screenshots/files in input_dir; keep generated artifacts in run_dir.",
        },
        "validation_expectations": {
            "compare_recent_longforms": 2,
            "capture_followup_dialogue": True,
            "required_delivery_variants": ["rich", "concise"],
            "reader_delivery_artifacts": [
                "longform_pdf",
                "rich_mobile_html",
                "concise_pdf",
                "concise_mobile_html",
            ],
            "mobile_reader_contract": [
                "单盘丰富版和单盘简洁版必须使用同一套暖纸、深字、少色、无框、无卡片阅读器。",
                "H1/H2 优先在冒号后自然分行，不为了逗号强行换行；章节主题和金句同字号、同色、同字重。",
                "标题、章节主题、金句和正文重点统一使用深色体系；不额外跳色，不制造多余字号层级。",
                "正文重点句只用 700 字重加粗，不加底纹、荧光笔、色块、额外跳色或换字体。",
                "若源稿某章漏标重点，手机阅读器每章最多自动补 1 处白话结论句加粗。",
                "加粗句必须是短的白话结论、现实判断或行动建议，并自然分散到多个章节，不能整段高亮或机械集中在每章第一段。",
            ],
            "required_artifacts": [
                "fact_archive_markdown",
                "longform_markdown",
                "longform_pdf",
                "rich_mobile_html",
                "concise_markdown",
                "concise_pdf",
                "concise_mobile_html",
                "final_delivery",
            ],
        },
    }
    manifest_path = run_dir / profile.get("case_manifest_name", "case_manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "manifest": str(manifest_path), "paths": manifest["paths"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
