#!/usr/bin/env python3
"""Optionally check live URLs registered in knowledge/sources/source-register.json."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTER = PROJECT_ROOT / "knowledge" / "sources" / "source-register.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check live source URLs from source-register.json.")
    parser.add_argument("--source-id", action="append", default=[], help="Limit checks to one or more source IDs.")
    parser.add_argument("--type", dest="source_type", action="append", default=[], help="Limit checks to one or more source types.")
    parser.add_argument("--domain", action="append", default=[], help="Limit checks to one or more knowledge domains.")
    parser.add_argument("--evidence-mode", action="append", default=[], help="Limit checks to one or more evidence modes.")
    parser.add_argument("--max-sources", type=int, default=0, help="Limit number of source entries checked.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    parser.add_argument("--output", help="Optional external JSON path for the source liveness snapshot.")
    parser.add_argument("--dry-run", action="store_true", help="Validate selection without network requests.")
    parser.add_argument("--json", action="store_true", help="Print JSON result.")
    return parser.parse_args()


def load_register() -> list[dict[str, Any]]:
    data = json.loads(SOURCE_REGISTER.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("source register entries must be a list")
    return [entry for entry in entries if isinstance(entry, dict)]


def entry_matches(entry: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.source_id and entry.get("id") not in set(args.source_id):
        return False
    if args.source_type and entry.get("type") not in set(args.source_type):
        return False
    if args.evidence_mode and entry.get("evidence_mode") not in set(args.evidence_mode):
        return False
    if args.domain:
        domains = entry.get("domains", [])
        if not isinstance(domains, list) or not set(args.domain).intersection(set(domains)):
            return False
    return True


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def check_url(url: str, timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": "xuanxue-console-source-check/0.1",
            "Range": "bytes=0-0",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            return {"url": url, "ok": status < 400, "status": status, "error": ""}
    except HTTPError as exc:
        return {"url": url, "ok": exc.code < 400, "status": exc.code, "error": str(exc)}
    except URLError as exc:
        return {"url": url, "ok": False, "status": None, "error": str(exc.reason)}
    except TimeoutError as exc:
        return {"url": url, "ok": False, "status": None, "error": str(exc)}


def main() -> int:
    args = parse_args()
    entries = [entry for entry in load_register() if entry.get("urls")]
    entries = [entry for entry in entries if entry_matches(entry, args)]
    if args.max_sources > 0:
        entries = entries[: args.max_sources]

    checked: list[dict[str, Any]] = []
    for entry in entries:
        urls = entry.get("urls", [])
        if not isinstance(urls, list):
            continue
        item = {"id": entry.get("id"), "title": entry.get("title"), "urls": []}
        for url in urls:
            if not isinstance(url, str):
                continue
            if args.dry_run:
                item["urls"].append({"url": url, "ok": True, "status": "dry_run", "error": ""})
            else:
                item["urls"].append(check_url(url, args.timeout))
        checked.append(item)

    failures = [
        {"id": item["id"], **url_result}
        for item in checked
        for url_result in item["urls"]
        if not url_result.get("ok")
    ]
    result = {
        "schema_version": "0.1.0",
        "checked_at": datetime.now(UTC).isoformat(),
        "passed": not failures,
        "dry_run": args.dry_run,
        "filters": {
            "source_id": args.source_id,
            "type": args.source_type,
            "domain": args.domain,
            "evidence_mode": args.evidence_mode,
            "max_sources": args.max_sources,
        },
        "checked_sources": len(checked),
        "checked_urls": sum(len(item["urls"]) for item in checked),
        "failures": failures,
        "results": checked,
    }

    if args.output:
        output = Path(args.output).expanduser().resolve()
        if is_relative_to(output, PROJECT_ROOT):
            raise SystemExit("source liveness output must stay outside project repo")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({k: v for k, v in result.items() if k != "results"}, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
