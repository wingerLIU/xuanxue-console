#!/usr/bin/env python3
"""Final acceptance checks for a xuanxue report case."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from case_manifest_contract import normalize_manifest, runtime_contract_policy
    from reader_title_contract import reader_title_label_failures
    from relationship_mode import relationship_mode_from_facts, relationship_mode_schema_failures
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from case_manifest_contract import normalize_manifest, runtime_contract_policy
    from reader_title_contract import reader_title_label_failures
    from relationship_mode import relationship_mode_from_facts, relationship_mode_schema_failures


DEFAULT_MANIFEST = "case_manifest.json"
MOBILE_HTML_REQUIRED_MARKERS = [
    "viewport",
    "FangSong",
    "仿宋",
    "--bg: #fff7d8",
    "--paper: #fff7d8",
    '<details class="toc">',
    "<summary>目录</summary>",
    "font-weight: 700",
    "word-break: keep-all",
    "overflow-wrap: break-word",
    "text-wrap: balance",
    "background: none",
    "title-topic",
    "title-hook",
    "section-topic",
    "section-hook",
    "font-size: inherit",
]
MOBILE_HTML_FORBIDDEN_MARKERS = [
    "http://",
    "https://",
    "linear-gradient",
    "overflow-wrap: anywhere",
    "position: sticky",
    "简洁阅读器",
    "脚本路径",
    "JSON 路径",
    "执行命令",
    "项目流程",
    "外部 run",
    "过程产物",
    "过程话术",
    "用于约束AI",
    "AI 约束",
    "AI约束",
    "新加段落",
    "乐观收束",
    "情绪价值",
    "真实感增强",
    "小红书",
    "新媒体图文",
    "找问题",
    "找茬",
    "编辑话术",
]
READER_FACING_MARKDOWN_ARTIFACTS = {
    "longform_markdown",
    "reader_markdown",
    "concise_markdown",
    "relationship_addendum_markdown",
    "relationship_concise_markdown",
}
READER_MARKDOWN_FORBIDDEN_MARKERS = [
    "用于测试",
    "测试源稿",
    "只作为 finalize",
    "finalize readiness",
    "验证器",
    "脚本路径",
    "JSON 路径",
    "执行命令",
    "内部验收",
    "交付方说明",
    "项目流程",
    "外部 run",
    "过程产物",
    "过程话术",
    "用于约束AI",
    "AI 约束",
    "AI约束",
    "新加段落",
    "乐观收束",
    "情绪价值",
    "真实感增强",
    "小红书",
    "新媒体图文",
    "找问题",
    "找茬",
    "编辑话术",
]
MOBILE_HTML_BOLD_CONTRACT = {
    "rich_mobile_html": {"min_strong": 10, "min_strong_sections": 8},
    "relationship_mobile_html": {"min_strong": 8, "min_strong_sections": 6},
    "concise_mobile_html": {"min_strong": 6, "min_strong_sections": 5},
    "relationship_concise_mobile_html": {"min_strong": 5, "min_strong_sections": 4},
    "mobile_html": {"min_strong": 4, "min_strong_sections": 3},
}
MAX_MOBILE_STRONG_TEXT_CHARS = 110
REQUIRED_RELATIONSHIP_LIFE_DOMAINS = {
    "career": "事业/合作",
    "family_life": "家庭/生活承载",
    "wealth_resources": "财富/资源投入",
    "health_energy": "健康/精力照顾",
    "intimacy_private": "亲近/私密边界",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate final xuanxue case delivery artifacts.")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Path to the case manifest JSON.")
    parser.add_argument("--min-longform-chars", type=int, default=18000)
    parser.add_argument(
        "--normalize-manifest",
        action="store_true",
        help="Write canonical artifact aliases back to the manifest before returning.",
    )
    parser.add_argument(
        "--write-status",
        action="store_true",
        help="Write finalize status back to manifest.status. Use this for final acceptance.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def check_file(path: Path, failures: list[str], label: str, *, min_bytes: int = 1) -> None:
    require(path.exists(), failures, f"{label} missing: {path}")
    if path.exists():
        require(path.stat().st_size >= min_bytes, failures, f"{label} too small: {path}")


def check_mobile_html_contract(path: Path, failures: list[str], label: str) -> None:
    if not path.exists():
        return
    html_text = path.read_text(encoding="utf-8")
    missing = [marker for marker in MOBILE_HTML_REQUIRED_MARKERS if marker not in html_text]
    forbidden = [marker for marker in MOBILE_HTML_FORBIDDEN_MARKERS if marker in html_text]
    require(not missing, failures, f"{label} mobile reader missing markers: {missing}")
    require(not forbidden, failures, f"{label} mobile reader contains forbidden markers: {forbidden}")
    title_match = re.search(r"<h1>(?P<body>.*?)</h1>", html_text, re.S)
    require(title_match is not None, failures, f"{label} mobile reader missing h1 title")
    if title_match is not None:
        title_text = html.unescape(re.sub(r"<[^>]+>", "", title_match.group("body"))).strip()
        bad_title_labels = reader_title_label_failures(title_text)
        require(
            not bad_title_labels,
            failures,
            f"{label} mobile reader title contains delivery/process labels: {bad_title_labels}; title={title_text}",
        )
    for selector in ["h1", "h2", ".title-topic", ".title-hook", ".section-topic", ".section-hook"]:
        block = css_block(html_text, selector)
        require(block is not None, failures, f"{label} mobile reader missing CSS block: {selector}")
        if block is None:
            continue
        require(
            "overflow-wrap: anywhere" not in block,
            failures,
            f"{label} mobile reader title CSS must not hard-cut Chinese text: {selector}",
        )
        require(
            "word-break: keep-all" in block,
            failures,
            f"{label} mobile reader title CSS missing keep-all: {selector}",
        )
        require(
            "text-wrap: balance" in block,
            failures,
            f"{label} mobile reader title CSS missing balanced wrapping: {selector}",
        )
        if selector in [".title-topic", ".title-hook", ".section-topic", ".section-hook"]:
            require(
                "font-size: inherit" in block and "font-weight: inherit" in block,
                failures,
                f"{label} mobile reader title parts must keep the same size and weight: {selector}",
            )
            require(
                "color: var(--title)" in block or "color: inherit" in block,
                failures,
                f"{label} mobile reader title parts must stay in the same dark color system: {selector}",
            )
    check_mobile_html_bold_contract(html_text, failures, label)


def check_reader_markdown_contract(path: Path, failures: list[str], label: str) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    found = [marker for marker in READER_MARKDOWN_FORBIDDEN_MARKERS if marker in text]
    require(
        not found,
        failures,
        f"{label} reader-facing Markdown contains process/delivery markers: {found}",
    )
    h1s = [line[2:].strip() for line in text.splitlines() if line.startswith("# ")]
    if h1s:
        bad_title_labels = reader_title_label_failures(h1s[0])
        require(
            not bad_title_labels,
            failures,
            f"{label} reader-facing Markdown H1 contains delivery/process labels: {bad_title_labels}; title={h1s[0]}",
        )


def check_mobile_html_bold_contract(html_text: str, failures: list[str], label: str) -> None:
    section_blocks = [
        match.group("body")
        for match in re.finditer(
            r'<section class="article-section"[^>]*>(?P<body>.*?)</section>',
            html_text,
            re.S,
        )
    ]
    if not section_blocks:
        return
    strong_texts = [
        html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
        for match in re.finditer(r"<strong>(.*?)</strong>", html_text, re.S)
    ]
    strong_texts = [text for text in strong_texts if text]
    long_strong = [text[:28] for text in strong_texts if len(text) > MAX_MOBILE_STRONG_TEXT_CHARS]
    require(
        not long_strong,
        failures,
        f"{label} mobile reader bold text should be short takeaway sentences, not long highlighted paragraphs: {long_strong}",
    )

    contract = MOBILE_HTML_BOLD_CONTRACT.get(label)
    if not contract:
        return
    section_count = len(section_blocks)
    if section_count < 5:
        return
    min_strong = min(int(contract["min_strong"]), section_count)
    min_strong_sections = min(int(contract["min_strong_sections"]), section_count)
    strong_sections = [block for block in section_blocks if "<strong>" in block]
    require(
        len(strong_texts) >= min_strong,
        failures,
        f"{label} mobile reader needs at least {min_strong} concise bold takeaway sentences; found {len(strong_texts)}",
    )
    require(
        len(strong_sections) >= min_strong_sections,
        failures,
        f"{label} mobile reader bold takeaways should be distributed across at least {min_strong_sections} sections; found {len(strong_sections)}",
    )

    first_para_strong = 0
    for block in strong_sections:
        paragraph = re.search(r"<p[^>]*>(?P<body>.*?)</p>", block, re.S)
        if paragraph and "<strong>" in paragraph.group("body"):
            first_para_strong += 1
    require(
        first_para_strong <= max(4, int(len(strong_sections) * 0.75)),
        failures,
        f"{label} mobile reader bold takeaways are too mechanically concentrated in first paragraphs",
    )


def css_block(html_text: str, selector: str) -> str | None:
    for match in re.finditer(r"(?P<selectors>[^{}]+)\{(?P<body>.*?)\n\s*\}", html_text, re.S):
        selectors = [item.strip() for item in match.group("selectors").split(",")]
        if selector in selectors:
            return match.group("body")
    return None


def load_json_if_present(path: Path, failures: list[str], label: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        failures.append(f"{label} invalid JSON: {exc}")
        return {}


def check_relationship_facts_contract(path: Path, failures: list[str]) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": str(path),
        "schema_checked": False,
        "life_domains": [],
    }
    facts = load_json_if_present(path, failures, "data:relationship")
    if not facts:
        return info
    info["schema_checked"] = True
    require(facts.get("module") == "relationship", failures, "relationship facts module must be relationship")
    mode = relationship_mode_from_facts(facts)
    mode_failures = relationship_mode_schema_failures(mode)
    if mode_failures == ["relationship_mode missing or empty."]:
        failures.append("relationship facts missing relationship_mode; rebuild relationship facts before finalize.")
    else:
        failures.extend(mode_failures)
    domains = facts.get("relationship_life_domains")
    if not isinstance(domains, dict):
        failures.append("relationship facts missing relationship_life_domains; rebuild relationship facts before finalize.")
        return info
    info["life_domains"] = sorted(domains)
    missing = [key for key in REQUIRED_RELATIONSHIP_LIFE_DOMAINS if key not in domains]
    require(not missing, failures, f"relationship_life_domains missing required domains: {missing}")
    for key, label in REQUIRED_RELATIONSHIP_LIFE_DOMAINS.items():
        item = domains.get(key)
        if not isinstance(item, dict):
            continue
        require(item.get("label") == label, failures, f"relationship_life_domains.{key}.label should be {label}")
        for list_key in ["allowed_writing", "do_not_infer"]:
            values = item.get(list_key)
            require(
                isinstance(values, list) and bool(values),
                failures,
                f"relationship_life_domains.{key}.{list_key} must be a non-empty list",
            )
        boundary = item.get("writing_boundary")
        require(
            isinstance(boundary, str) and len(boundary.strip()) >= 8,
            failures,
            f"relationship_life_domains.{key}.writing_boundary is missing or too short",
        )
        for person_key in ["person_a", "person_b"]:
            person = item.get(person_key)
            require(isinstance(person, dict), failures, f"relationship_life_domains.{key}.{person_key} missing")
            if not isinstance(person, dict):
                continue
            require(bool(person.get("label")), failures, f"relationship_life_domains.{key}.{person_key}.label missing")
            require(
                isinstance(person.get("western_bodies"), list),
                failures,
                f"relationship_life_domains.{key}.{person_key}.western_bodies must be a list",
            )
        require(
            isinstance(item.get("bazi_cross_anchors"), list),
            failures,
            f"relationship_life_domains.{key}.bazi_cross_anchors must be a list",
        )
        require(
            isinstance(item.get("western_cross_anchors"), list),
            failures,
            f"relationship_life_domains.{key}.western_cross_anchors must be a list",
        )
    return info


def manifest_path(manifest: dict[str, Any], key: str, failures: list[str]) -> Path | None:
    paths = manifest.get("paths", {})
    raw = paths.get(key) if isinstance(paths, dict) else None
    if not raw:
        failures.append(f"path missing from manifest: {key}")
        return None
    return Path(raw)


def module_map(combo: dict[str, Any]) -> dict[str, dict[str, Any]]:
    modules = combo.get("facts", {}).get("modules", [])
    return {item.get("module", ""): item for item in modules if isinstance(item, dict)}


def explicit_expectation(expectations: dict[str, Any], key: str) -> Any:
    return expectations[key] if key in expectations else None


def write_manifest_status(
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    passed: bool,
    failures: list[str],
    warnings: list[str],
    relationship_concise: dict[str, Any],
    repair_commands: list[str],
) -> None:
    status = manifest.setdefault("status", {})
    if not isinstance(status, dict):
        status = {}
        manifest["status"] = status
    status["stage"] = "finalized" if passed else "finalize_failed"
    status["finalize_passed"] = passed
    status["finalize_checked_at"] = datetime.now().isoformat(timespec="seconds")
    status["finalize_failures"] = failures[:20]
    status["finalize_warnings"] = warnings[:20]
    status["finalize_repair_commands"] = repair_commands[:20]
    if relationship_concise.get("expected"):
        status["relationship_concise"] = relationship_concise
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_runtime_context(manifest: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    runtime_dir = manifest_path(manifest, "runtime_dir", failures)
    calibration_dir = manifest_path(manifest, "calibration_dir", failures)
    info: dict[str, Any] = {
        "knowledge_context": "",
        "retrospective_intake_json": "",
        "retrospective_intake_markdown": "",
        "collection_plan_items": 0,
        "domain_question_bank_items": 0,
    }
    if runtime_dir is None or calibration_dir is None:
        return info

    knowledge_context_path = runtime_dir / "knowledge_context.json"
    intake_json_path = runtime_dir / "retrospective_intake.json"
    intake_md_path = calibration_dir / "retrospective-intake.md"
    info.update(
        {
            "knowledge_context": str(knowledge_context_path),
            "retrospective_intake_json": str(intake_json_path),
            "retrospective_intake_markdown": str(intake_md_path),
        }
    )
    check_file(knowledge_context_path, failures, "runtime:knowledge_context", min_bytes=100)
    check_file(intake_json_path, failures, "runtime:retrospective_intake", min_bytes=100)
    check_file(intake_md_path, failures, "calibration:retrospective-intake", min_bytes=100)

    context = load_json_if_present(knowledge_context_path, failures, "runtime:knowledge_context")
    intake = load_json_if_present(intake_json_path, failures, "runtime:retrospective_intake")
    intake_md = intake_md_path.read_text(encoding="utf-8") if intake_md_path.exists() else ""

    if context:
        require(context.get("schema_version") == "0.1.0", failures, "knowledge_context schema_version must be 0.1.0")
        require(context.get("passed") is True, failures, "knowledge_context did not pass")
        require(
            isinstance(context.get("selected_modules"), list) and bool(context.get("selected_modules")),
            failures,
            "knowledge_context missing selected_modules",
        )
        require(
            isinstance(context.get("usage_rules"), list) and bool(context.get("usage_rules")),
            failures,
            "knowledge_context missing usage_rules",
        )
        for key in ["knowledge_files", "source_entries", "retrospective_requirements"]:
            require(isinstance(context.get(key), list) and bool(context.get(key)), failures, f"knowledge_context missing {key}")
        plan = context.get("retrospective_collection_plan", [])
        require(isinstance(plan, list), failures, "knowledge_context retrospective_collection_plan is not a list")
        info["collection_plan_items"] = len(plan) if isinstance(plan, list) else 0
        for idx, item in enumerate(plan if isinstance(plan, list) else []):
            if not isinstance(item, dict):
                failures.append(f"knowledge_context collection plan item {idx} is not an object")
                continue
            require(
                isinstance(item.get("suggested_target_artifacts"), list) and bool(item.get("suggested_target_artifacts")),
                failures,
                f"knowledge_context collection plan item {idx} missing suggested_target_artifacts",
            )
            require(
                isinstance(item.get("candidate_commands"), list) and bool(item.get("candidate_commands")),
                failures,
                f"knowledge_context collection plan item {idx} missing candidate_commands",
            )
        for key in ["case_id", "run_id"]:
            if context.get(key) is not None:
                require(context.get(key) == manifest.get(key), failures, f"knowledge_context {key} does not match manifest")

    if intake:
        require(intake.get("do_not_promote_without_human_approval") is True, failures, "retrospective_intake allows promotion without human approval")
        intake_plan = intake.get("retrospective_collection_plan")
        require(isinstance(intake_plan, list), failures, "retrospective_intake missing collection plan")
        question_bank = intake.get("domain_question_bank")
        require(isinstance(question_bank, list), failures, "retrospective_intake missing domain_question_bank")
        if isinstance(question_bank, list):
            info["domain_question_bank_items"] = len(question_bank)
            for idx, item in enumerate(question_bank):
                if not isinstance(item, dict):
                    failures.append(f"retrospective_intake domain_question_bank item {idx} is not an object")
                    continue
                require(isinstance(item.get("domain"), str) and bool(item.get("domain")), failures, f"retrospective_intake domain_question_bank item {idx} missing domain")
                require(isinstance(item.get("requirement_id"), str) and bool(item.get("requirement_id")), failures, f"retrospective_intake domain_question_bank item {idx} missing requirement_id")
                require(isinstance(item.get("questions"), list) and bool(item.get("questions")), failures, f"retrospective_intake domain_question_bank item {idx} missing questions")
                require(
                    isinstance(item.get("suggested_target_artifacts"), list) and bool(item.get("suggested_target_artifacts")),
                    failures,
                    f"retrospective_intake domain_question_bank item {idx} missing suggested_target_artifacts",
                )
        for key in ["case_id", "run_id"]:
            require(intake.get(key) == manifest.get(key), failures, f"retrospective_intake {key} does not match manifest")
        if context and isinstance(context.get("retrospective_collection_plan"), list):
            require(
                isinstance(intake_plan, list)
                and len(intake_plan) == len(context.get("retrospective_collection_plan", [])),
                failures,
                "retrospective_intake collection plan length does not match knowledge_context",
            )
            if isinstance(question_bank, list):
                context_domains = {
                    item.get("domain")
                    for item in context.get("retrospective_collection_plan", [])
                    if isinstance(item, dict) and item.get("domain")
                }
                bank_domains = {item.get("domain") for item in question_bank if isinstance(item, dict) and item.get("domain")}
                require(
                    context_domains == bank_domains,
                    failures,
                    "retrospective_intake domain_question_bank domains do not match knowledge_context collection plan",
                )

    for marker in ["可以问读者的问题", "去隐私整理要求", "create_case_retrospective_candidate.py"]:
        require(marker in intake_md, failures, f"retrospective-intake markdown missing marker: {marker}")
    return info


def existing_path(raw: Any) -> str:
    if not raw:
        return ""
    return str(raw)


def path_exists(raw: Any) -> bool:
    if not raw:
        return False
    return Path(str(raw)).exists()


def check_relationship_concise_readiness(
    manifest: dict[str, Any],
    artifacts: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    data_paths = artifacts.get("data", {})
    if not isinstance(data_paths, dict):
        data_paths = {}
    is_relationship = bool(
        manifest.get("relationship_context")
        or data_paths.get("relationship")
        or artifacts.get("relationship_workflow")
        or artifacts.get("relationship_mobile_html")
        or artifacts.get("relationship_fact_archive_markdown")
    )
    info: dict[str, Any] = {
        "expected": is_relationship,
        "draft_target": "",
        "draft_exists": False,
        "markdown": existing_path(artifacts.get("relationship_concise_markdown")),
        "markdown_exists": path_exists(artifacts.get("relationship_concise_markdown")),
        "docx": existing_path(artifacts.get("relationship_concise_docx")),
        "docx_exists": path_exists(artifacts.get("relationship_concise_docx")),
        "pdf": existing_path(artifacts.get("relationship_concise_pdf")),
        "pdf_exists": path_exists(artifacts.get("relationship_concise_pdf")),
        "mobile_html": existing_path(artifacts.get("relationship_concise_mobile_html")),
        "mobile_html_exists": path_exists(artifacts.get("relationship_concise_mobile_html")),
    }
    if not is_relationship:
        return info

    workflow_path = artifacts.get("relationship_workflow")
    workflow: dict[str, Any] = {}
    if workflow_path and Path(str(workflow_path)).exists():
        try:
            workflow = load_json(Path(str(workflow_path)))
        except json.JSONDecodeError as exc:
            warnings.append(f"relationship workflow invalid JSON; skipped concise readiness details: {exc}")
    draft_target = artifacts.get("relationship_concise_source_markdown") or workflow.get("concise_draft_target")
    if not draft_target:
        paths = manifest.get("paths", {})
        drafts_dir = paths.get("drafts_dir") if isinstance(paths, dict) else None
        case_id = manifest.get("case_id") or "case"
        if drafts_dir:
            draft_target = str(Path(str(drafts_dir)) / f"{case_id}-relationship-concise.md")
    info["draft_target"] = existing_path(draft_target)
    info["draft_exists"] = path_exists(draft_target)

    if not info["draft_exists"]:
        warnings.append("relationship concise draft not found yet; workflow has package command but concise delivery is not ready.")
    delivery_complete = bool(info["pdf_exists"] and info["mobile_html_exists"])
    info["delivery_complete"] = delivery_complete
    if not delivery_complete:
        warnings.append("relationship concise PDF/mobile delivery artifacts not complete yet.")
    return info


def workflow_commands_from_manifest(artifacts: dict[str, Any], warnings: list[str]) -> dict[str, str]:
    workflow_path = artifacts.get("relationship_workflow")
    if not workflow_path or not Path(str(workflow_path)).exists():
        return {}
    try:
        workflow = load_json(Path(str(workflow_path)))
    except json.JSONDecodeError as exc:
        warnings.append(f"relationship workflow invalid JSON; skipped repair command extraction: {exc}")
        return {}
    commands = workflow.get("commands", {})
    return commands if isinstance(commands, dict) else {}


def relationship_repair_commands(
    manifest: dict[str, Any],
    artifacts: dict[str, Any],
    relationship_concise: dict[str, Any],
    relationship_facts: dict[str, Any],
    failures: list[str],
    warnings: list[str],
) -> list[str]:
    data_paths = artifacts.get("data", {})
    if not isinstance(data_paths, dict):
        data_paths = {}
    is_relationship = bool(
        manifest.get("relationship_context")
        or data_paths.get("relationship")
        or artifacts.get("relationship_workflow")
        or artifacts.get("relationship_mobile_html")
        or artifacts.get("relationship_fact_archive_markdown")
    )
    if not is_relationship:
        return []

    commands = workflow_commands_from_manifest(artifacts, warnings)
    repairs: list[str] = []

    def add(command_key: str) -> None:
        command = commands.get(command_key)
        if command and command not in repairs:
            repairs.append(command)

    failure_text = "\n".join(failures)
    if any("relationship_life_domains" in failure or "relationship facts" in failure for failure in failures):
        source_manifests = manifest.get("source_manifests", {})
        context = manifest.get("relationship_context", {})
        person_a = source_manifests.get("person_a") if isinstance(source_manifests, dict) else ""
        person_b = source_manifests.get("person_b") if isinstance(source_manifests, dict) else ""
        context = context if isinstance(context, dict) else {}
        person_a_label = context.get("person_a_label") or "<甲>"
        person_b_label = context.get("person_b_label") or "<乙>"
        relationship_status = context.get("relationship_status") or "<已知关系>"
        distance_status = context.get("distance_status") or "<已知距离状态>"
        person_a_mbti = context.get("person_a_mbti_type") or ""
        person_b_mbti = context.get("person_b_mbti_type") or ""
        if person_a and person_b:
            command = (
                "python scripts/build_relationship_facts.py "
                f"--manifest \"{manifest.get('paths', {}).get('run_dir', '')}\\case_manifest.json\" "
                f"--person-a-manifest \"{person_a}\" --person-b-manifest \"{person_b}\" "
                f"--person-a-label \"{person_a_label}\" --person-b-label \"{person_b_label}\" "
                f"--relationship-status \"{relationship_status}\" "
                f"--distance-status \"{distance_status}\""
            )
            if person_a_mbti:
                command += f" --person-a-mbti-type \"{person_a_mbti}\""
            if person_b_mbti:
                command += f" --person-b-mbti-type \"{person_b_mbti}\""
            repairs.append(command)

    if "relationship_mobile_html" in failure_text:
        add("package_mobile_html")

    if relationship_concise.get("expected"):
        if not relationship_concise.get("draft_exists"):
            draft = relationship_concise.get("draft_target") or "<RUN_DIR>\\drafts\\<case>-relationship-concise.md"
            repairs.append(f"write relationship concise draft at \"{draft}\" using templates/relationship-concise-template.md")
        if not relationship_concise.get("pdf_exists"):
            add("validate_relationship_concise")
            add("package_relationship_concise")
        if not relationship_concise.get("mobile_html_exists"):
            add("package_relationship_concise_mobile_html")

    if failures:
        add("finalize")
    return repairs


def check_pdf(
    pdf_path: Path,
    failures: list[str],
    warnings: list[str],
    *,
    text_markers: list[str] | None = None,
) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(pdf_path), "header_ok": False}
    if not pdf_path.exists():
        failures.append(f"PDF missing: {pdf_path}")
        return info
    header = pdf_path.read_bytes()[:5]
    info["header_ok"] = header == b"%PDF-"
    require(info["header_ok"], failures, f"PDF header invalid: {pdf_path}")

    if importlib.util.find_spec("pypdf") is None:
        warnings.append("pypdf unavailable; skipped PDF text extraction.")
        return info

    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(pdf_path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages[:2])
    info["pages"] = len(reader.pages)
    markers = text_markers if text_markers is not None else ["综合命盘", "判断型摘要", "开篇钩子"]
    info["sample_has_chinese"] = any(marker in text for marker in markers)
    require(len(reader.pages) > 0, failures, f"PDF has no pages: {pdf_path}")
    require(info["sample_has_chinese"], failures, f"PDF text extraction missing expected Chinese text: {pdf_path}")
    return info


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    failures: list[str] = []
    warnings: list[str] = []
    check_file(manifest_path, failures, "manifest")
    if failures:
        print(json.dumps({"passed": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1

    raw_manifest = load_json(manifest_path)
    manifest, normalization_changes = normalize_manifest(raw_manifest)
    policy = runtime_contract_policy()
    expectations = manifest.get("validation_expectations", {})
    if not isinstance(expectations, dict):
        expectations = {}
    runtime_context_info = check_runtime_context(manifest, failures)
    artifacts = manifest.get("artifacts", {})
    paths = {
        "project_readme": Path(artifacts.get("project_readme", "README.md")),
        "finalize_check": Path(artifacts.get("finalize_check", "scripts/finalize_case.py")),
        "manifest": manifest_path,
    }
    required_artifacts = expectations.get("required_artifacts", policy["canonical_required_artifacts"])
    if required_artifacts is None:
        required_artifacts = []
    for key in required_artifacts:
        if key not in artifacts:
            failures.append(f"artifact path missing from manifest: {key}")
        else:
            paths[key] = Path(artifacts[key])
    for key in policy.get("optional_debug_artifacts", []):
        if artifacts.get(key):
            paths[key] = Path(artifacts[key])
    for label, path in paths.items():
        check_file(path, failures, label, min_bytes=100 if label != "manifest" else 1)
        if label.endswith("mobile_html"):
            check_mobile_html_contract(path, failures, label)
        if label in READER_FACING_MARKDOWN_ARTIFACTS:
            check_reader_markdown_contract(path, failures, label)
    relationship_concise_info = check_relationship_concise_readiness(manifest, artifacts, warnings)

    data_paths = artifacts.get("data", {})
    if not isinstance(data_paths, dict):
        data_paths = {}
        failures.append("artifacts.data is not an object")
    relationship_facts_info: dict[str, Any] = {}
    required_data = expectations.get("required_data", policy["canonical_required_data"])
    if required_data is None:
        required_data = []
    for key in required_data:
        if key not in data_paths:
            failures.append(f"data path missing from manifest: {key}")
        else:
            data_path = Path(data_paths[key])
            check_file(data_path, failures, f"data:{key}", min_bytes=100)
            if key == "relationship" and data_path.exists():
                relationship_facts_info = check_relationship_facts_contract(data_path, failures)

    combo_raw = data_paths.get("combo") if isinstance(data_paths, dict) else None
    combo_path = Path(combo_raw) if combo_raw else None
    combo = load_json(combo_path) if combo_path and combo_path.exists() else {}
    mods = module_map(combo)

    fact_archive_path = paths.get("fact_archive_markdown") or paths.get("relationship_fact_archive_markdown")
    fact_archive_text = (
        fact_archive_path.read_text(encoding="utf-8") if fact_archive_path and fact_archive_path.exists() else ""
    )
    fact_archive_markers = expectations.get("fact_archive_markers", ["排盘事实复查档案", "JSON 源文件", "复查约定"])
    for marker in fact_archive_markers:
        require(marker in fact_archive_text, failures, f"fact archive missing marker: {marker}")

    expected_modules = expectations.get("required_modules", ["bazi", "ziwei", "western"])
    if expected_modules is None:
        expected_modules = []
    for label in expected_modules:
        if label in data_paths:
            check_file(Path(data_paths[label]), failures, f"data:{label}", min_bytes=100)
        elif label in mods:
            warnings.append(f"data:{label} path missing; using combo module only.")
        else:
            failures.append(f"data path missing and combo module absent: {label}")
    bazi = mods.get("bazi", {})
    western = mods.get("western", {})
    flow = bazi.get("facts", {}).get("flow", {})
    houses = western.get("facts", {}).get("houses", {})
    angles = houses.get("angles", {})

    expected_flow_as_of = explicit_expectation(expectations, "flow_as_of")
    expected_flow_day = explicit_expectation(expectations, "flow_day")
    expected_ascendant = explicit_expectation(expectations, "ascendant_sign")
    expected_midheaven = explicit_expectation(expectations, "midheaven_sign")

    if expected_flow_as_of is not None:
        require(
            flow.get("as_of") == expected_flow_as_of,
            failures,
            f"combo bazi as_of is not {expected_flow_as_of}",
        )
    if expected_flow_day is not None:
        require(
            flow.get("pillars", {}).get("day") == expected_flow_day,
            failures,
            f"flow day is not {expected_flow_day}",
        )
    if expected_ascendant is not None:
        require(
            angles.get("ascendant", {}).get("sign") == expected_ascendant,
            failures,
            f"western ascendant is not {expected_ascendant}",
        )
    if expected_midheaven is not None:
        require(
            angles.get("midheaven", {}).get("sign") == expected_midheaven,
            failures,
            f"western midheaven is not {expected_midheaven}",
        )

    longform_path = paths.get("longform_markdown")
    longform_text = longform_path.read_text(encoding="utf-8") if longform_path and longform_path.exists() else ""
    default_longform_markers = [
        "01 判断型摘要",
        "先看结论",
        "基础排盘信息与时间可信度",
        "时间敏感性检查",
        "八字总论",
        "神煞",
        "紫微总论",
        "西洋占星总论",
        "三方合参人格画像与误读点",
        "别人眼里的你与外貌气质",
        "现实关系全景",
        "过去几年故事线",
        "未来几年趋势",
        "六大专题分析",
        "技术证据附录",
        "校准问题",
    ]
    longform_markers = expectations.get("longform_markers", default_longform_markers)
    missing_longform = [marker for marker in longform_markers if marker not in longform_text]
    require(not missing_longform, failures, f"longform missing markers: {missing_longform}")
    min_longform_chars = int(expectations.get("min_longform_chars", args.min_longform_chars))
    require(len(longform_text) >= min_longform_chars, failures, "longform is shorter than required minimum")

    html_path = paths.get("main_html")
    if html_path:
        html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
        default_html_markers: list[str] = []
        html_markers = expectations.get("html_markers", default_html_markers)
        missing_html = [marker for marker in html_markers if marker not in html_text]
        require(not missing_html, failures, f"html missing markers: {missing_html}")

    pdf_path = paths.get("longform_pdf")
    pdf_text_markers = expectations.get("pdf_text_markers")
    pdf_info = (
        check_pdf(
            pdf_path,
            failures,
            warnings,
            text_markers=pdf_text_markers if isinstance(pdf_text_markers, list) else None,
        )
        if pdf_path
        else {"path": "", "header_ok": False}
    )
    repair_commands = relationship_repair_commands(
        manifest,
        artifacts,
        relationship_concise_info,
        relationship_facts_info,
        failures,
        warnings,
    )

    result = {
        "passed": not failures,
        "case_id": manifest.get("case_id"),
        "manifest": str(manifest_path),
        "normalization_changes": normalization_changes,
        "longform_chars": len(longform_text),
        "runtime_context": runtime_context_info,
        "relationship_concise": relationship_concise_info,
        "relationship_facts": relationship_facts_info,
        "pdf": pdf_info,
        "repair_commands": repair_commands,
        "warnings": warnings,
        "failures": failures,
    }
    if args.normalize_manifest or args.write_status:
        if args.write_status:
            write_manifest_status(
                manifest_path,
                manifest,
                passed=result["passed"],
                failures=failures,
                warnings=warnings,
                relationship_concise=relationship_concise_info,
                repair_commands=repair_commands,
            )
        else:
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["manifest_written"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
