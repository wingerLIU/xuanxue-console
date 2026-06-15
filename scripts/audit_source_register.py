#!/usr/bin/env python3
"""Audit the machine-readable source register."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_INDEX = PROJECT_ROOT / "knowledge" / "source-index.md"
SOURCE_REGISTER = PROJECT_ROOT / "knowledge" / "sources" / "source-register.json"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "source_register.schema.json"

SOURCE_ID_RE = re.compile(r"SRC-[A-Z0-9-]+")
STATUS_RE = re.compile(r"^\|\s*`(?P<id>SRC-[A-Z0-9-]+)`\s*\|[^|]*\|\s*(?P<status>[a-z_]+)\s*\|")

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

ALLOWED_URL_HOSTS = {
    "archive.org",
    "chinese.ncku.edu.tw",
    "commons.wikimedia.org",
    "cpalondon.com",
    "ctext.org",
    "en.wikisource.org",
    "kostma.aks.ac.kr",
    "penelope.uchicago.edu",
    "undsci.berkeley.edu",
    "upload.wikimedia.org",
    "www.airitilibrary.com",
    "www.astro.com",
    "www.britannica.com",
    "www.digital.archives.go.jp",
    "www.gutenberg.org",
    "www.myersbriggs.org",
    "www.ncbi.nlm.nih.gov",
    "www.themyersbriggs.com",
    "www.toyo-bunko.org",
    "zh.wikisource.org",
}


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


def parse_source_index() -> tuple[set[str], dict[str, str]]:
    text = SOURCE_INDEX.read_text(encoding="utf-8") if SOURCE_INDEX.exists() else ""
    ids = set(SOURCE_ID_RE.findall(text))
    statuses: dict[str, str] = {}
    for line in text.splitlines():
        match = STATUS_RE.match(line)
        if match:
            statuses[match.group("id")] = match.group("status")
    return ids, statuses


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    schema = load_json(SCHEMA_PATH, failures)
    register = load_json(SOURCE_REGISTER, failures)
    declared_ids, declared_statuses = parse_source_index()

    allowed_statuses = set(schema.get("allowed_statuses", []))
    allowed_types = set(schema.get("allowed_types", []))
    allowed_evidence_modes = set(schema.get("allowed_evidence_modes", []))
    required_entry_keys = list(schema.get("required_entry_keys", []))

    if register.get("schema_version") != "0.1.0":
        failures.append("source register schema_version must be 0.1.0")
    for key in schema.get("required_top_level_keys", []):
        if key not in register:
            failures.append(f"source register missing top-level key: {key}")

    entries = register.get("entries", [])
    if not isinstance(entries, list) or not entries:
        failures.append("source register entries must be a non-empty list")
        entries = []

    by_id: dict[str, dict[str, Any]] = {}
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            failures.append(f"source register entry {idx} is not an object")
            continue
        source_id = str(entry.get("id", ""))
        if not source_id:
            failures.append(f"source register entry {idx} missing id")
            continue
        if source_id in by_id:
            failures.append(f"duplicate source register id: {source_id}")
        by_id[source_id] = entry

        missing = [key for key in required_entry_keys if key not in entry]
        if missing:
            failures.append(f"{source_id} missing keys: {missing}")

        if entry.get("status") not in allowed_statuses:
            failures.append(f"{source_id} invalid status: {entry.get('status')}")
        if entry.get("type") not in allowed_types:
            failures.append(f"{source_id} invalid type: {entry.get('type')}")
        if entry.get("evidence_mode") not in allowed_evidence_modes:
            failures.append(f"{source_id} invalid evidence_mode: {entry.get('evidence_mode')}")

        declared_status = declared_statuses.get(source_id)
        if declared_status and entry.get("status") != declared_status:
            failures.append(f"{source_id} status mismatch: index={declared_status}, register={entry.get('status')}")

        for list_key in ["domains", "urls", "local_paths", "promotion_targets"]:
            value = entry.get(list_key)
            if not isinstance(value, list):
                failures.append(f"{source_id} {list_key} must be a list")

        for text_key in ["title", "used_for", "limits"]:
            value = entry.get(text_key)
            min_len = 2 if text_key == "title" else 6
            if not isinstance(value, str) or len(value.strip()) < min_len:
                failures.append(f"{source_id} {text_key} must be a meaningful string")

        serialized = json.dumps(entry, ensure_ascii=False)
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, serialized, flags=re.IGNORECASE):
                failures.append(f"{source_id} contains forbidden private/case pattern: {pattern}")

        urls = entry.get("urls", [])
        if isinstance(urls, list):
            evidence_mode = entry.get("evidence_mode")
            if evidence_mode in {"online_public_entry", "catalog_or_boundary", "modern_public_reference"} and not urls:
                failures.append(f"{source_id} requires at least one URL for evidence_mode={evidence_mode}")
            for url in urls:
                if not isinstance(url, str) or not url.startswith("https://"):
                    failures.append(f"{source_id} URL must be https: {url}")
                    continue
                host = urlparse(url).netloc.lower()
                if host not in ALLOWED_URL_HOSTS:
                    failures.append(f"{source_id} URL host is not allowlisted: {host}")

        local_paths = entry.get("local_paths", [])
        if isinstance(local_paths, list):
            if entry.get("evidence_mode") in {"project_artifact", "case_retrospective_protocol"} and not local_paths:
                failures.append(f"{source_id} requires local_paths for project evidence")
            for path_name in local_paths:
                if not isinstance(path_name, str):
                    failures.append(f"{source_id} local_paths must contain strings")
                    continue
                target = PROJECT_ROOT / path_name
                if path_name.endswith("/"):
                    if not target.exists() or not target.is_dir():
                        failures.append(f"{source_id} local directory missing: {path_name}")
                elif not target.exists():
                    failures.append(f"{source_id} local file missing: {path_name}")

        if entry.get("evidence_mode") == "runtime_package" and not entry.get("package"):
            failures.append(f"{source_id} runtime package entry requires package")

    missing_from_register = sorted(declared_ids - set(by_id))
    extra_in_register = sorted(set(by_id) - declared_ids)
    if missing_from_register:
        failures.append(f"source register missing declared source IDs: {missing_from_register}")
    if extra_in_register:
        failures.append(f"source register has source IDs not declared in source-index: {extra_in_register}")

    result = {
        "passed": not failures,
        "declared_sources": len(declared_ids),
        "registered_sources": len(by_id),
        "allowlisted_url_hosts": sorted(ALLOWED_URL_HOSTS),
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
