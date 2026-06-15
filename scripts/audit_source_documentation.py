#!/usr/bin/env python3
"""Audit alignment between source-register and human-readable source documents."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTER = PROJECT_ROOT / "knowledge" / "sources" / "source-register.json"
SOURCE_INDEX = PROJECT_ROOT / "knowledge" / "source-index.md"
ONLINE_CLASSICS = PROJECT_ROOT / "knowledge" / "sources" / "online-classics.md"
MODERN_REFERENCES = PROJECT_ROOT / "knowledge" / "sources" / "modern-references.md"
RESEARCH_BACKLOG = PROJECT_ROOT / "knowledge" / "sources" / "research-backlog.md"

SOURCE_ID_RE = re.compile(r"SRC-[A-Z0-9-]+")


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def load_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.exists():
        failures.append(f"missing JSON file: {rel(path)}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{rel(path)} invalid JSON: {exc}")
        return {}


def load_text(path: Path, failures: list[str]) -> str:
    if not path.exists():
        failures.append(f"missing source documentation file: {rel(path)}")
        return ""
    return path.read_text(encoding="utf-8")


def ids_in_text(text: str) -> set[str]:
    return set(SOURCE_ID_RE.findall(text))


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    register = load_json(SOURCE_REGISTER, failures)
    entries = register.get("entries", [])
    if not isinstance(entries, list):
        failures.append("source-register entries must be a list")
        entries = []
    registered = {
        str(entry.get("id")): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }

    index_text = load_text(SOURCE_INDEX, failures)
    online_text = load_text(ONLINE_CLASSICS, failures)
    modern_text = load_text(MODERN_REFERENCES, failures)
    backlog_text = load_text(RESEARCH_BACKLOG, failures)
    combined_source_docs = "\n".join([online_text, modern_text, backlog_text])

    for path, text, marker in [
        (ONLINE_CLASSICS, online_text, "last_checked:"),
        (MODERN_REFERENCES, modern_text, "last_checked:"),
        (RESEARCH_BACKLOG, backlog_text, "last_updated:"),
    ]:
        if marker not in text:
            failures.append(f"{rel(path)} missing freshness marker: {marker}")

    all_doc_ids = ids_in_text(index_text) | ids_in_text(combined_source_docs)
    unknown_doc_ids = sorted(all_doc_ids - set(registered))
    if unknown_doc_ids:
        failures.append(f"source docs reference IDs not in source-register: {unknown_doc_ids}")

    missing_from_index = sorted(set(registered) - ids_in_text(index_text))
    if missing_from_index:
        failures.append(f"source-index missing registered IDs: {missing_from_index}")

    documented_classical = 0
    documented_modern = 0
    backlog_ids = ids_in_text(backlog_text)
    for source_id, entry in sorted(registered.items()):
        source_type = entry.get("type")
        status = entry.get("status")
        evidence_mode = entry.get("evidence_mode")
        urls = entry.get("urls", [])
        if not isinstance(urls, list):
            urls = []

        if source_type == "classical_text":
            if source_id not in online_text and source_id not in backlog_text:
                failures.append(f"{source_id} classical source is not documented in online-classics or research-backlog")
            else:
                documented_classical += 1
            if evidence_mode in {"catalog_or_boundary", "tradition_placeholder"} and source_id not in backlog_ids:
                failures.append(f"{source_id} boundary/tradition source must be tracked in research-backlog")
        elif source_type == "modern_reference":
            if source_id not in modern_text:
                failures.append(f"{source_id} modern source is not documented in modern-references")
            else:
                documented_modern += 1

        if evidence_mode in {"online_public_entry", "catalog_or_boundary", "modern_public_reference"}:
            for url in urls:
                if isinstance(url, str) and url and url not in combined_source_docs:
                    failures.append(f"{source_id} URL missing from human-readable source docs: {url}")

        if status == "candidate" and source_type in {"classical_text", "modern_reference"}:
            if source_id not in combined_source_docs:
                failures.append(f"{source_id} candidate source lacks human-readable boundary notes")

    result = {
        "passed": not failures,
        "registered_sources": len(registered),
        "documented_classical_sources": documented_classical,
        "documented_modern_sources": documented_modern,
        "backlog_source_ids": sorted(backlog_ids),
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
