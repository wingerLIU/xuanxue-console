#!/usr/bin/env python3
"""Audit the reusable xuanxue knowledge base for structure and provenance."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "knowledge/README.md",
    "knowledge/knowledge_map.json",
    "knowledge/source-index.md",
    "knowledge/sources/README.md",
    "knowledge/sources/source-register.json",
    "knowledge/sources/online-classics.md",
    "knowledge/sources/modern-references.md",
    "knowledge/sources/research-backlog.md",
    "knowledge/rules/inference-contract.md",
    "knowledge/rules/research-and-promotion.md",
    "knowledge/completeness/README.md",
    "knowledge/completeness/coverage-matrix.json",
    "knowledge/completeness/retrospective-requirements.json",
    "knowledge/bazi/README.md",
    "knowledge/bazi/classical-anchors.md",
    "knowledge/bazi/foundations.md",
    "knowledge/bazi/shenfeng-anchors.md",
    "knowledge/bazi/shenfeng-methods.md",
    "knowledge/bazi/ten-gods.md",
    "knowledge/bazi/structure-and-flow.md",
    "knowledge/ziwei/README.md",
    "knowledge/ziwei/classical-anchors.md",
    "knowledge/ziwei/foundations.md",
    "knowledge/ziwei/quanshu-vs-quanji-boundary.md",
    "knowledge/ziwei/palaces-stars-four-transformations.md",
    "knowledge/western/README.md",
    "knowledge/western/classical-anchors.md",
    "knowledge/western/foundations.md",
    "knowledge/western/modern-psychological.md",
    "knowledge/western/planets-aspects-houses.md",
    "knowledge/mbti/README.md",
    "knowledge/mbti/behavior-language.md",
    "knowledge/liuyao/README.md",
    "knowledge/liuyao/classical-anchors.md",
    "knowledge/liuyao/question-reading.md",
    "knowledge/xiaoliuren/README.md",
    "knowledge/xiaoliuren/classical-anchors.md",
    "knowledge/xiaoliuren/quick-timing.md",
    "knowledge/writing/reader-rich-report.md",
    "knowledge/team-career/README.md",
    "knowledge/fengshui/README.md",
    "knowledge/case-retrospectives/README.md",
    "knowledge/case-retrospectives/promotion-protocol.md",
    "knowledge/case-retrospectives/template.md",
    "knowledge/promotion/knowledge_promotion_manifest.json",
    "schemas/case_retrospective.schema.json",
    "schemas/retrospective_intake.schema.json",
    "schemas/knowledge_rule.schema.json",
    "schemas/promotion_manifest.schema.json",
    "schemas/source_register.schema.json",
]

REQUIRED_MARKERS = {
    "knowledge/source-index.md": [
        "SRC-RUNTIME-LUNAR-PYTHON",
        "SRC-RUNTIME-IZTRO-PY",
        "SRC-RUNTIME-EPHEM",
        "SRC-BAZI-PROJECT-SYNTHESIS",
        "SRC-ZIWEI-PROJECT-SYNTHESIS",
        "SRC-WESTERN-MODERN-PSYCHOLOGICAL",
        "SRC-WESTERN-SCIENTIFIC-BOUNDARY",
        "SRC-WESTERN-PROJECT-SYNTHESIS",
        "SRC-MBTI-PROJECT-SYNTHESIS",
        "SRC-LIUYAO-PROJECT-SYNTHESIS",
        "SRC-XIAOLIUREN-DUONENG-BISHI",
        "SRC-XIAOLIUREN-XIEJI-BIANFANG",
        "SRC-XIAOLIUREN-PROJECT-SYNTHESIS",
        "SRC-PROJECT-CASE-RETROSPECTIVE-PROTOCOL",
        "SRC-PROJECT-TEAM-CAREER-SYNTHESIS",
        "SRC-PROJECT-FENGSHUI-DIRECTION-SYNTHESIS",
        "SRC-PROJECT-COMPLETENESS-AUDIT",
        "SRC-PROJECT-SOURCE-REGISTER",
        "SRC-PROJECT-KNOWLEDGE-CONTEXT",
        "build_fact_archive.py",
        "build_knowledge_context.py",
        "create_followup_context.py",
        "create_retrospective_intake.py",
        "retrospective_intake.schema.json",
        "finalize_case.py",
        "validate_longform_report.py",
        "promote_case_retrospective.py",
        "audit_case_retrospectives.py",
        "audit_source_documentation.py",
        "retrospective-requirements.json",
        "复盘采集计划",
        "target_artifacts",
        "source-register.json",
        "online-classics.md",
        "联网吸收原则",
    ],
    "knowledge/sources/README.md": [
        "source-register.json",
        "check_source_urls.py",
        "audit_source_register.py",
        "audit_source_documentation.py",
        "audit_promotion_manifest.py",
        "默认",
        "不联网",
    ],
    "knowledge/sources/source-register.json": [
        "SRC-PROJECT-SOURCE-REGISTER",
        "evidence_mode",
        "promotion_targets",
        "online_public_entry",
        "catalog_or_boundary",
        "modern_public_reference",
        "project_artifact",
        "check_source_urls.py",
        "build_fact_archive.py",
        "build_knowledge_context.py",
        "create_followup_context.py",
        "create_retrospective_intake.py",
        "retrospective_intake.schema.json",
        "finalize_case.py",
        "target_artifacts",
        "audit_rule_cards.py",
        "validate_longform_report.py",
        "audit_source_documentation.py",
        "audit_case_retrospectives.py",
    ],
    "knowledge/sources/online-classics.md": [
        "last_checked",
        "Wikisource",
        "Project Gutenberg",
        "Internet Archive",
        "SRC-BAZI-DITIAN-SUI",
        "SRC-ZIWEI-DOUSHU-QUANSHU",
        "東洋文庫",
        "KOSTMA",
        "SRC-LIUYAO-ZENGSHAN-BU",
        "周易",
        "SRC-XIAOLIUREN-DUONENG-BISHI",
        "SRC-XIAOLIUREN-XIEJI-BIANFANG",
        "多能鄙事",
        "欽定協紀辨方書",
        "SRC-WESTERN-PTOLEMY-TETRABIBLOS",
    ],
    "knowledge/sources/research-backlog.md": [
        "source_found_curated_methods",
        "source_found_curated_boundary",
        "catalog_found_no_public_fulltext",
        "SRC-ZIWEI-DOUSHU-QUANJI",
        "SRC-XIAOLIUREN-TRADITION",
    ],
    "knowledge/sources/modern-references.md": [
        "SRC-MBTI-MODERN-TYPOLOGY",
        "SRC-MBTI-CRITICAL-BOUNDARY",
        "SRC-WESTERN-MODERN-PSYCHOLOGICAL",
        "SRC-WESTERN-SCIENTIFIC-BOUNDARY",
        "Myers",
        "NCBI",
        "Astrodienst",
        "Berkeley",
    ],
    "knowledge/bazi/classical-anchors.md": [
        "BZ-C001",
        "SRC-BAZI-ZIPING-ZHENQUAN",
        "SRC-BAZI-QIONGTONG-BAOJIAN",
    ],
    "knowledge/bazi/shenfeng-anchors.md": [
        "SF-C001",
        "SRC-BAZI-SHENFENG-TONGKAO",
        "病药",
        "盖头",
    ],
    "knowledge/bazi/shenfeng-methods.md": [
        "SF-M001",
        "病药四步",
        "盖头截脚",
        "动静触发",
        "反例",
    ],
    "knowledge/ziwei/classical-anchors.md": [
        "ZW-C001",
        "SRC-ZIWEI-DOUSHU-QUANSHU",
        "SRC-ZIWEI-FU-TEXTS",
    ],
    "knowledge/ziwei/foundations.md": [
        "ZW-F001",
        "结论强度",
        "领域证据链",
        "常见误读",
        "复盘采集点",
    ],
    "knowledge/ziwei/palaces-stars-four-transformations.md": [
        "星曜置信度",
        "四化写作步骤",
        "领域校准问题",
    ],
    "knowledge/ziwei/quanshu-vs-quanji-boundary.md": [
        "ZW-QJ001",
        "SRC-ZIWEI-DOUSHU-QUANJI",
        "馆藏目录",
        "不作为客户报告正文判断依据",
        "付费、网盘、Scribd",
    ],
    "knowledge/western/classical-anchors.md": [
        "WS-C001",
        "SRC-WESTERN-PTOLEMY-TETRABIBLOS",
        "SRC-WESTERN-LILLY-CHRISTIAN-ASTROLOGY",
    ],
    "knowledge/western/modern-psychological.md": [
        "WS-M001",
        "SRC-WESTERN-MODERN-PSYCHOLOGICAL",
        "SRC-WESTERN-SCIENTIFIC-BOUNDARY",
        "象征语言",
        "科学边界",
        "不作为科学人格测评",
        "禁止",
    ],
    "knowledge/western/foundations.md": [
        "WS-F001",
        "结论强度",
        "特异性要求",
        "时间敏感处理",
        "复盘采集点",
    ],
    "knowledge/western/planets-aspects-houses.md": [
        "相位置信度",
        "宫位置信度",
        "防泛化写法",
    ],
    "knowledge/liuyao/classical-anchors.md": [
        "LY-C001",
        "SRC-LIUYAO-ZENGSHAN-BU",
        "用神",
    ],
    "knowledge/rules/inference-contract.md": [
        "Claim Packet",
        "证据优先级",
        "禁止事项",
    ],
    "knowledge/rules/research-and-promotion.md": [
        "两层知识结构",
        "联网资料进入流程",
        "联网来源优先级",
        "晋升条件",
        "target_artifacts",
    ],
    "knowledge/bazi/ten-gods.md": [
        "比肩",
        "食神",
        "正官",
        "七杀",
        "官印",
    ],
    "knowledge/writing/reader-rich-report.md": [
        "第二人称",
        "机器校验口径",
        "validate_longform_report.py",
        "价值感来源",
        "付费报告禁区",
    ],
    "knowledge/case-retrospectives/README.md": [
        "human_approved=true",
        "curated",
        "candidate",
        "去 case 化",
        "反例",
        "create_case_retrospective_candidate.py",
        "create_retrospective_intake.py",
        "promote_case_retrospective.py",
        "默认晋升状态是 `curated`",
        "domains",
    ],
    "knowledge/case-retrospectives/promotion-protocol.md": [
        "SRC-PROJECT-CASE-RETROSPECTIVE-PROTOCOL",
        "晋升门槛",
        "禁止晋升",
        "audit_case_retrospectives.py",
        "create_retrospective_intake.py",
        "retrospective_intake.schema.json",
        "create_case_retrospective_candidate.py",
        "promote_case_retrospective.py",
        "candidate` 只能保存在外部 run 目录",
        "默认晋升为 `curated`",
    ],
    "knowledge/case-retrospectives/template.md": [
        "CR-YYYYMMDD",
        "去隐私摘要",
        "counterexamples",
        "contains_birth_data",
        "create_case_retrospective_candidate.py",
        "create_retrospective_intake.py",
        "promote_case_retrospective.py",
        "晋升后默认状态为 `curated`",
        "domains",
    ],
    "knowledge/team-career/README.md": [
        "SRC-PROJECT-TEAM-CAREER-SYNTHESIS",
        "单盘 facts",
        "两两 relationship facts",
        "team-source-summary.json",
        "商业结构",
        "城市判断",
        "复盘采集点",
        "retrospectives",
    ],
    "knowledge/fengshui/README.md": [
        "SRC-PROJECT-FENGSHUI-DIRECTION-SYNTHESIS",
        "方位",
        "空间",
        "城市",
        "现场勘测",
        "罗盘坐向",
        "低风险建议",
        "复盘采集点",
    ],
    "knowledge/completeness/README.md": [
        "goal_complete",
        "blocks_goal_completion",
        "audit_knowledge_coverage.py",
    ],
    "knowledge/completeness/coverage-matrix.json": [
        "GAP-CASE-RETROSPECTIVES-VERIFIED",
        "blocks_goal_completion",
        "audit_knowledge_coverage.py",
        "network_source_rule",
        "build_knowledge_context.py",
        "create_retrospective_intake.py",
        "finalize_case.py",
        "retrospective-requirements.json",
        "audit_promotion_manifest.py",
        "audit_rule_cards.py",
        "validate_longform_report.py",
        "audit_case_retrospectives.py",
        "audit_source_documentation.py",
    ],
    "knowledge/completeness/retrospective-requirements.json": [
        "REQ-RETRO-BAZI",
        "REQ-RETRO-ZIWEI",
        "REQ-RETRO-WRITING",
        "GAP-CASE-RETROSPECTIVES-VERIFIED",
        "min_entries",
        "min_status",
    ],
    "knowledge/promotion/knowledge_promotion_manifest.json": [
        "PROMO-20260612-SOURCE-REGISTER",
        "PROMO-20260612-RETROSPECTIVE-REQUIREMENTS",
        "PROMO-20260612-LONGFORM-VALIDATOR",
        "PROMO-20260612-RETROSPECTIVE-PROMOTER",
        "PROMO-20260612-SOURCE-DOCUMENTATION-AUDIT",
        "PROMO-20260612-RETROSPECTIVE-COLLECTION-PLAN",
        "PROMO-20260612-RETROSPECTIVE-TARGET-SUGGESTIONS",
        "PROMO-20260612-RETROSPECTIVE-INTAKE",
        "PROMO-20260612-FINALIZE-RUNTIME-CONTEXT",
        "SRC-PROJECT-COMPLETENESS-AUDIT",
        "human_approved",
        "approval_status",
        "PROMO-20260612-RULE-CARD-AUDIT",
    ],
    "knowledge/mbti/behavior-language.md": [
        "不作命理证据",
        "四组偏好",
        "报告使用",
    ],
    "knowledge/liuyao/question-reading.md": [
        "具体问题",
        "世应",
        "用神",
        "结论等级",
        "问题类型映射",
        "复盘字段",
    ],
    "knowledge/xiaoliuren/classical-anchors.md": [
        "XLR-C001",
        "SRC-XIAOLIUREN-DUONENG-BISHI",
        "SRC-XIAOLIUREN-XIEJI-BIANFANG",
        "弱信号",
    ],
    "knowledge/xiaoliuren/quick-timing.md": [
        "弱信号",
        "短期提示",
        "不得用于重大决定",
    ],
}

FORBIDDEN_PATTERNS = [
    r"C:\\Users\\",
    r"wxid_",
    r"run_20\d{6}_",
    r"\.jpg\b",
    r"\.jpeg\b",
    r"\.png\b",
    r"\.webp\b",
    r"1992-12-23",
    r"\bWei\b",
]

SOURCE_ID_RE = re.compile(r"SRC-[A-Z0-9-]+")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    for item in REQUIRED_FILES:
        path = PROJECT_ROOT / item
        if not path.exists():
            failures.append(f"missing required knowledge file: {item}")
        elif path.is_file() and path.stat().st_size < 80:
            failures.append(f"knowledge file too small: {item}")

    source_index_path = PROJECT_ROOT / "knowledge/source-index.md"
    source_text = load_text(source_index_path) if source_index_path.exists() else ""
    declared_sources = set(SOURCE_ID_RE.findall(source_text))
    if len(declared_sources) < 12:
        failures.append("source-index declares too few source IDs")

    for item, markers in REQUIRED_MARKERS.items():
        path = PROJECT_ROOT / item
        text = load_text(path) if path.exists() else ""
        missing = [marker for marker in markers if marker not in text]
        if missing:
            failures.append(f"{item} missing markers: {missing}")

    for path in (PROJECT_ROOT / "knowledge").rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json"}:
            warnings.append(f"unexpected knowledge file extension: {rel(path)}")
            continue
        text = load_text(path)
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                failures.append(f"{rel(path)} contains forbidden case/local pattern: {pattern}")
        if path.name != "source-index.md":
            used_sources = set(SOURCE_ID_RE.findall(text))
            unknown = sorted(used_sources - declared_sources)
            if unknown:
                failures.append(f"{rel(path)} references unknown source IDs: {unknown}")

    promotion_path = PROJECT_ROOT / "knowledge/promotion/knowledge_promotion_manifest.json"
    if promotion_path.exists():
        try:
            manifest: dict[str, Any] = json.loads(load_text(promotion_path))
        except json.JSONDecodeError as exc:
            failures.append(f"promotion manifest is invalid JSON: {exc}")
            manifest = {}
        entries = manifest.get("entries", [])
        if not isinstance(entries, list) or not entries:
            failures.append("promotion manifest has no entries")
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                failures.append(f"promotion entry {idx} is not an object")
                continue
            for key in ["id", "type", "status", "path", "source_ids", "approval_status", "human_approved"]:
                if key not in entry:
                    failures.append(f"promotion entry {entry.get('id', idx)} missing {key}")
            entry_path = entry.get("path")
            if isinstance(entry_path, str) and not (PROJECT_ROOT / entry_path).exists():
                failures.append(f"promotion entry path missing: {entry_path}")
            source_ids = entry.get("source_ids", [])
            if isinstance(source_ids, list):
                unknown = sorted(set(source_ids) - declared_sources)
                if unknown:
                    failures.append(f"promotion entry {entry.get('id', idx)} unknown sources: {unknown}")
            else:
                failures.append(f"promotion entry {entry.get('id', idx)} source_ids is not a list")

    policy_path = PROJECT_ROOT / "config/knowledge_policy.json"
    if policy_path.exists():
        try:
            policy: dict[str, Any] = json.loads(load_text(policy_path))
        except json.JSONDecodeError as exc:
            failures.append(f"knowledge policy is invalid JSON: {exc}")
            policy = {}
        runtime_files = policy.get("required_runtime_knowledge", [])
        if not isinstance(runtime_files, list) or not runtime_files:
            failures.append("knowledge policy has no required_runtime_knowledge")
        else:
            for file_name in runtime_files:
                if not isinstance(file_name, str) or not (PROJECT_ROOT / file_name).exists():
                    failures.append(f"knowledge policy missing runtime file: {file_name}")

    map_path = PROJECT_ROOT / "knowledge/knowledge_map.json"
    if map_path.exists():
        try:
            knowledge_map: dict[str, Any] = json.loads(load_text(map_path))
        except json.JSONDecodeError as exc:
            failures.append(f"knowledge map is invalid JSON: {exc}")
            knowledge_map = {}
        modules = knowledge_map.get("modules", {})
        if not isinstance(modules, dict) or not modules:
            failures.append("knowledge map has no modules")
        for module_name, module in modules.items():
            if not isinstance(module, dict):
                failures.append(f"knowledge map module {module_name} is not an object")
                continue
            files = module.get("files", [])
            if not isinstance(files, list) or not files:
                failures.append(f"knowledge map module {module_name} has no files")
                continue
            for file_name in files:
                if not isinstance(file_name, str) or not (PROJECT_ROOT / file_name).exists():
                    failures.append(f"knowledge map module {module_name} missing file: {file_name}")

    result = {
        "passed": not failures,
        "required_files": len(REQUIRED_FILES),
        "declared_sources": len(declared_sources),
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
