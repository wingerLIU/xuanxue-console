#!/usr/bin/env python3
"""Create a run-local context file for follow-up questions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from case_manifest_contract import normalize_manifest
    from relationship_mode import relationship_mode_from_facts, relationship_mode_schema_failures
except ModuleNotFoundError:  # pragma: no cover - importlib test fallback
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from case_manifest_contract import normalize_manifest
    from relationship_mode import relationship_mode_from_facts, relationship_mode_schema_failures


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FOLLOWUP_MODULES = {"bazi", "ziwei", "western", "mbti", "liuyao", "xiaoliuren", "relationship", "writing"}
DATA_MODULES = {"bazi", "ziwei", "western", "mbti", "liuyao", "xiaoliuren", "relationship"}
RELATIONSHIP_KNOWLEDGE_MODULES = ["bazi", "ziwei", "western", "mbti"]
RELATIONSHIP_KNOWLEDGE_PATH_PREFIXES = (
    "templates/relationship-",
    "scripts/build_relationship_facts.py",
    "scripts/create_relationship_workspace.py",
    "scripts/validate_relationship_report.py",
)
REQUIRED_RELATIONSHIP_LIFE_DOMAINS = {
    "career": "事业/合作",
    "family_life": "家庭/生活承载",
    "wealth_resources": "财富/资源投入",
    "health_energy": "健康/精力照顾",
    "intimacy_private": "亲近/私密边界",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a knowledge-backed follow-up context for a case.")
    parser.add_argument("--manifest", required=True, help="External case_manifest.json.")
    parser.add_argument("--question", required=True, help="User follow-up question.")
    parser.add_argument("--module", action="append", default=[], help="Relevant module. Can repeat or use comma-separated values.")
    parser.add_argument("--output", help="Output JSON. Defaults to <runtime_dir>/followups/<timestamp>-<slug>.json.")
    parser.add_argument("--slug", help="Short ASCII slug for the output filename.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def external_path(path: Path, label: str, failures: list[str]) -> Path:
    resolved = path.resolve()
    if is_relative_to(resolved, PROJECT_ROOT):
        failures.append(f"{label} must not be inside project repo: {resolved}")
    return resolved


def resolve_dialogue_note_path(manifest: dict[str, Any], output_path: Path, failures: list[str]) -> Path | None:
    paths = manifest.get("paths", {})
    if not isinstance(paths, dict):
        paths = {}

    dialogue_raw = paths.get("dialogue_dir")
    if dialogue_raw:
        dialogue_dir = external_path(Path(str(dialogue_raw)), "dialogue_dir", failures)
    elif paths.get("calibration_dir"):
        dialogue_dir = external_path(Path(str(paths["calibration_dir"])) / "dialogue", "dialogue_dir", failures)
    elif paths.get("run_dir"):
        dialogue_dir = external_path(Path(str(paths["run_dir"])) / "calibration" / "dialogue", "dialogue_dir", failures)
    else:
        failures.append("manifest missing paths.dialogue_dir or paths.calibration_dir")
        return None
    return dialogue_dir / f"{output_path.stem}.md"


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug[:48] or "followup"


def split_modules(raw_modules: list[str]) -> list[str]:
    modules: list[str] = []
    for item in raw_modules:
        for part in item.split(","):
            value = part.strip().lower()
            if not value:
                continue
            if value == "combo":
                modules.extend(["bazi", "ziwei", "western", "mbti", "liuyao", "xiaoliuren", "writing"])
            else:
                modules.append(value)
    return modules


def module_names_from_combo(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError):
        return []
    modules = data.get("facts", {}).get("modules", [])
    if not isinstance(modules, list):
        return []
    result: list[str] = []
    for item in modules:
        if isinstance(item, dict) and isinstance(item.get("module"), str):
            name = item["module"].lower()
            if name in DATA_MODULES and name not in result:
                result.append(name)
    return result


def normalize_selected_modules(raw_modules: list[str], manifest: dict[str, Any]) -> list[str]:
    modules = split_modules(raw_modules)
    if not modules:
        artifacts_data = manifest.get("artifacts", {}).get("data", {})
        if isinstance(artifacts_data, dict):
            combo_path = Path(str(artifacts_data.get("combo", ""))) if artifacts_data.get("combo") else None
            if combo_path:
                modules.extend(module_names_from_combo(combo_path))
            for name in DATA_MODULES:
                if artifacts_data.get(name):
                    modules.append(name)
    modules.append("writing")

    unknown = sorted({item for item in modules if item not in FOLLOWUP_MODULES})
    if unknown:
        raise SystemExit(f"unknown follow-up module: {', '.join(unknown)}")

    result: list[str] = []
    for module in modules:
        if module not in result:
            result.append(module)
    return result


def existing_data_paths(manifest: dict[str, Any], modules: list[str]) -> list[dict[str, str]]:
    artifacts_data = manifest.get("artifacts", {}).get("data", {})
    if not isinstance(artifacts_data, dict):
        artifacts_data = {}
    paths: list[dict[str, str]] = []

    combo = artifacts_data.get("combo")
    if combo:
        paths.append({"module": "combo", "path": str(combo), "role": "primary combined calculated facts"})

    for module in modules:
        if module not in DATA_MODULES:
            continue
        raw = artifacts_data.get(module)
        if raw and not any(item["path"] == str(raw) for item in paths):
            paths.append({"module": module, "path": str(raw), "role": "module calculated facts"})

    time_sensitivity = artifacts_data.get("time_sensitivity")
    if time_sensitivity:
        paths.append({"module": "time_sensitivity", "path": str(time_sensitivity), "role": "birth-time sensitivity boundaries"})
    return paths


def check_relationship_facts_schema(path: Path, failures: list[str]) -> list[str]:
    if not path.exists():
        return []
    try:
        facts = load_json(path)
    except json.JSONDecodeError as exc:
        failures.append(f"relationship facts invalid JSON: {exc}")
        return []
    if facts.get("module") != "relationship":
        failures.append("relationship facts module must be relationship")
    mode = relationship_mode_from_facts(facts)
    mode_failures = relationship_mode_schema_failures(mode)
    if mode_failures == ["relationship_mode missing or empty."]:
        failures.append("relationship facts missing relationship_mode; rebuild relationship facts before follow-up.")
    else:
        failures.extend(mode_failures)
    domains = facts.get("relationship_life_domains")
    if not isinstance(domains, dict):
        failures.append("relationship facts missing relationship_life_domains; rebuild relationship facts before follow-up.")
        return []
    missing = [key for key in REQUIRED_RELATIONSHIP_LIFE_DOMAINS if key not in domains]
    if missing:
        failures.append(f"relationship_life_domains missing required domains: {missing}")
    for key, label in REQUIRED_RELATIONSHIP_LIFE_DOMAINS.items():
        item = domains.get(key)
        if not isinstance(item, dict):
            continue
        if item.get("label") != label:
            failures.append(f"relationship_life_domains.{key}.label should be {label}")
        for list_key in ["allowed_writing", "do_not_infer"]:
            values = item.get(list_key)
            if not isinstance(values, list) or not values:
                failures.append(f"relationship_life_domains.{key}.{list_key} must be a non-empty list")
        boundary = item.get("writing_boundary")
        if not isinstance(boundary, str) or len(boundary.strip()) < 8:
            failures.append(f"relationship_life_domains.{key}.writing_boundary is missing or too short")
    return sorted(domains)


def knowledge_files_for_modules(context: dict[str, Any], modules: list[str]) -> list[dict[str, Any]]:
    selected = set(modules) | {"writing"}
    if "relationship" in selected:
        selected |= set(RELATIONSHIP_KNOWLEDGE_MODULES)
    context_modules = context.get("selected_modules", [])
    if isinstance(context_modules, list):
        selected |= {str(item) for item in context_modules if str(item) in {"source_register", "completeness"}}

    files = context.get("knowledge_files", [])
    if not isinstance(files, list):
        return []
    result: list[dict[str, Any]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", ""))
        include = False
        if path in {
            "knowledge/source-index.md",
            "knowledge/rules/inference-contract.md",
            "references/interpretation-guide.md",
        }:
            include = True
        for module in selected:
            if path.startswith(f"knowledge/{module}/") or module == "writing" and (
                path.startswith("templates/") or path.startswith("knowledge/writing/")
            ):
                include = True
            if module == "relationship" and (
                path.startswith("templates/relationship-")
                or path in RELATIONSHIP_KNOWLEDGE_PATH_PREFIXES
            ):
                include = True
        if include and path and not any(row.get("path") == path for row in result):
            result.append(item)
    return result


def prior_report_context(manifest: dict[str, Any]) -> list[dict[str, str]]:
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return []
    candidates = [
        ("longform_markdown", "previous rich report wording context"),
        ("reader_markdown", "delivered rich report wording context"),
        ("concise_markdown", "delivered concise report wording context"),
        ("relationship_addendum_markdown", "previous addendum wording context"),
        ("relationship_concise_source_markdown", "relationship concise source wording context"),
        ("relationship_concise_markdown", "delivered relationship concise wording context"),
    ]
    result: list[dict[str, str]] = []
    for key, role in candidates:
        value = artifacts.get(key)
        if value:
            result.append({"artifact": key, "path": str(value), "role": role, "evidence_status": "context_only"})
    return result


def build_dialogue_note(context: dict[str, Any], followup_context_path: Path) -> str:
    def bullet_paths(items: list[dict[str, Any]], *, label_key: str = "module", path_key: str = "path") -> list[str]:
        lines: list[str] = []
        for item in items:
            label = str(item.get(label_key) or item.get("artifact") or item.get("path") or "item")
            path = str(item.get(path_key) or item.get("absolute_path") or "")
            role = str(item.get("role") or item.get("evidence_status") or "").strip()
            suffix = f" ({role})" if role else ""
            lines.append(f"- {label}: `{path}`{suffix}")
        return lines or ["- 待补"]

    modules = ", ".join(context.get("selected_modules", [])) or "待补"
    lines = [
        "# 追加问题对话复盘",
        "",
        "## 基本信息",
        "",
        f"- case_id: `{context.get('case_id')}`",
        f"- run_id: `{context.get('run_id')}`",
        f"- created_at: `{context.get('created_at')}`",
        f"- selected_modules: `{modules}`",
        f"- followup_context: `{followup_context_path}`",
        "",
        "## 追问原文",
        "",
        str(context.get("question", "")).strip() or "待补",
        "",
        "## 回答前必读",
        "",
        "- facts_json:",
        *bullet_paths(context.get("facts_json", [])),
        f"- knowledge_context: `{context.get('knowledge_context')}`",
        "- required_knowledge_files:",
        *bullet_paths(context.get("required_knowledge_files", []), label_key="path", path_key="absolute_path"),
        "- prior_report_context:",
        *bullet_paths(context.get("prior_report_context", []), label_key="artifact"),
        "",
        "## 回答口径",
        "",
        "- 先给明确结论：这个问题更像 A，不是 B；不要先铺流程。",
        "- 标出判断级别：强 / 中 / 弱。证据够就直接排优先级，证据不够就说明为什么降级。",
        "- 客观不等于中庸；不要为了稳妥把每个问题写成两边都可以。",
        "- 再给证据、边界和可校准问题；旧报告只能当表达上下文，不能单独推出新结论。",
        "- 锋利不是恐吓、绝对化或宿命化；高风险决定仍降级为现实建议。",
        "",
        "## 回答后复盘",
        "",
        "- 最终回答摘要：",
        "- 读者反馈/继续追问：",
        "- 觉得过软、过硬或像旧稿的段落：",
        "- 可沉淀但需去隐私的候选复盘：",
        "",
    ]
    return "\n".join(lines)


def build_context(manifest_path: Path, question: str, modules_arg: list[str], output_arg: str | None, slug_arg: str | None) -> tuple[dict[str, Any], Path]:
    failures: list[str] = []
    manifest = load_json(manifest_path)
    manifest, _changes = normalize_manifest(manifest)
    modules = normalize_selected_modules(modules_arg, manifest)

    paths = manifest.get("paths", {})
    if not isinstance(paths, dict):
        paths = {}
    runtime_dir_raw = paths.get("runtime_dir")
    if not runtime_dir_raw:
        raise SystemExit("manifest missing paths.runtime_dir")
    runtime_dir = external_path(Path(str(runtime_dir_raw)), "runtime_dir", failures)
    knowledge_context_path = runtime_dir / "knowledge_context.json"
    if not knowledge_context_path.exists():
        failures.append(f"missing runtime:knowledge_context: {knowledge_context_path}")
        knowledge_context: dict[str, Any] = {}
    else:
        knowledge_context = load_json(knowledge_context_path)
        if knowledge_context.get("passed") is not True:
            failures.append("knowledge_context did not pass")
        context_modules = knowledge_context.get("selected_modules", [])
        if not isinstance(context_modules, list) or not context_modules:
            failures.append("knowledge_context missing selected_modules")
        else:
            context_module_set = {str(item) for item in context_modules}
            for module in modules:
                if module == "relationship":
                    if "relationship" not in context_module_set:
                        failures.append(
                            "knowledge_context missing requested module: relationship; rebuild with build_knowledge_context.py --module relationship"
                        )
                    missing = [item for item in RELATIONSHIP_KNOWLEDGE_MODULES if item not in context_module_set]
                    if missing:
                        failures.append(
                            "knowledge_context missing relationship component modules: "
                            f"{', '.join(missing)}; rebuild with build_knowledge_context.py --module bazi --module ziwei --module western --module mbti --module relationship"
                        )
                    continue
                if module != "writing" and module not in context_module_set:
                    failures.append(
                        f"knowledge_context missing requested module: {module}; rebuild with build_knowledge_context.py --module {module}"
                    )

    facts_json = existing_data_paths(manifest, modules)
    if not facts_json:
        failures.append("no facts_json available; follow-up answer would be prose-only")
    relationship_life_domains: list[str] = []
    relationship_mode: dict[str, Any] = {}
    for item in facts_json:
        path = Path(item["path"])
        if not path.exists():
            failures.append(f"missing fact json: {path}")
            continue
        if item.get("module") == "relationship":
            relationship_life_domains = check_relationship_facts_schema(path, failures)
            facts = load_json(path)
            relationship_mode = relationship_mode_from_facts(facts)

    required_knowledge_files = knowledge_files_for_modules(knowledge_context, modules)
    if not required_knowledge_files:
        failures.append("no required knowledge files resolved from knowledge_context")
    for item in required_knowledge_files:
        if item.get("exists") is not True:
            failures.append(f"missing knowledge file: {item.get('path')}")

    question_text = question.strip()
    if not question_text:
        failures.append("question is empty")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(slug_arg or question_text)
    output_path = Path(output_arg).resolve() if output_arg else runtime_dir / "followups" / f"{timestamp}-{slug}.json"
    output_path = external_path(output_path, "followup_context output", failures)
    dialogue_note_path = resolve_dialogue_note_path(manifest, output_path, failures)

    result = {
        "schema_version": "0.1.0",
        "case_id": manifest.get("case_id"),
        "run_id": manifest.get("run_id"),
        "created_at": timestamp,
        "question": question_text,
        "selected_modules": modules,
        "dialogue_note": str(dialogue_note_path) if dialogue_note_path else None,
        "facts_json": facts_json,
        "knowledge_context": str(knowledge_context_path),
        "required_knowledge_files": required_knowledge_files,
        "prior_report_context": prior_report_context(manifest),
        "relationship_life_domains": relationship_life_domains if "relationship" in modules else [],
        "relationship_mode": relationship_mode if "relationship" in modules else {},
        "answer_style": {
            "default": "evidence_bounded_sharp",
            "sequence": ["verdict", "confidence", "why_not", "evidence", "boundary", "calibration"],
            "rules": [
                "Start with a clear answer before process notes.",
                "Use stronger wording when calculated facts, rules, and calibration point in the same direction.",
                "Do not balance every answer into both-sides prose; explain why the weaker reading is weaker.",
                "Keep medical, legal, financial, and life-changing decisions bounded as practical advice.",
            ],
        },
        "answer_contract": [
            "Before answering, read every facts_json path and every required_knowledge_files absolute_path.",
            "Treat prior_report_context as wording context only; do not derive new claims from the old article alone.",
            "Give an evidence-bounded sharp verdict first; objective means sourced and bounded, not neutralized.",
            "For each important claim, keep the source layer clear: calculated_fact, classical_rule, modern_synthesis, case_calibration, or practical_advice.",
            "If the follow-up asks about a new concrete event or timing question, collect the missing question/casting data instead of stretching natal-chart prose.",
            "For relationship follow-ups, treat relationship facts as the primary calculated layer and individual-system facts/rules as supporting layers.",
            "For relationship follow-ups about career, family, wealth, health/energy, or intimacy, read relationship_life_domains first and obey allowed_writing, do_not_infer, and writing_boundary.",
            "For relationship follow-ups about attraction, closeness, or private life, read relationship_mode first; only write body-attraction/private romance language when romantic_language_supported is true.",
            "If evidence is thin or systems disagree, answer with a bounded tendency and a calibration question.",
        ],
        "passed": not failures,
        "failures": failures,
    }
    return result, output_path


def main() -> int:
    args = parse_args()
    result, output_path = build_context(Path(args.manifest).resolve(), args.question, args.module, args.output, args.slug)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result.get("dialogue_note"):
        dialogue_note = Path(str(result["dialogue_note"]))
        dialogue_note.parent.mkdir(parents=True, exist_ok=True)
        dialogue_note.write_text(build_dialogue_note(result, output_path), encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": result["passed"],
                "output": str(output_path),
                "dialogue_note": result.get("dialogue_note"),
                "failures": result["failures"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
