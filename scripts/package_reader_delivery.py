#!/usr/bin/env python3
"""Package a reader-facing longform report into clean MD/DOCX/PDF/ZIP outputs."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from export_longform_documents import export_docx, export_pdf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build clean reader delivery files from a longform Markdown report.")
    parser.add_argument("markdown", help="Source longform Markdown.")
    parser.add_argument("--output-dir", required=True, help="Directory for clean delivery files.")
    parser.add_argument("--basename", required=True, help="Reader-facing basename without extension.")
    parser.add_argument("--subtitle", default="综合命盘长文报告")
    parser.add_argument(
        "--no-subtitle",
        action="store_true",
        help="Do not render a fixed subtitle on DOCX/PDF cover pages.",
    )
    parser.add_argument("--zip", dest="zip_path", help="Optional zip output path.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of Python repr.")
    parser.add_argument("--manifest", help="Optional external case_manifest.json to update.")
    parser.add_argument(
        "--artifact-prefix",
        choices=["rich", "concise", "relationship_addendum", "relationship_concise"],
        help="Manifest artifact group to update when --manifest is provided.",
    )
    parser.add_argument(
        "--avoid-locked",
        action="store_true",
        help="If DOCX/PDF is locked by Windows, write a timestamp-suffixed filename instead of failing.",
    )
    return parser.parse_args()


def available_path(path: Path) -> Path:
    if not path.exists():
        return path
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.stem}-{stamp}{path.suffix}")


def write_with_lock_fallback(fn, source_text: str, output: Path, subtitle: str, avoid_locked: bool) -> Path:
    try:
        fn(source_text, output, subtitle)
        return output
    except PermissionError:
        if not avoid_locked:
            raise
        fallback = available_path(output)
        fn(source_text, fallback, subtitle)
        return fallback


def update_manifest(manifest_path: Path, prefix: str, outputs: dict[str, str | None]) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.setdefault("artifacts", {})
    if not isinstance(artifacts, dict):
        artifacts = {}
        manifest["artifacts"] = artifacts
    delivery = artifacts.setdefault("delivery", {})
    if not isinstance(delivery, dict):
        delivery = {}
        artifacts["delivery"] = delivery

    if prefix == "rich":
        mapping = {
            "reader_markdown": outputs["markdown"],
            "longform_markdown": outputs["markdown"],
            "reader_docx": outputs["docx"],
            "reader_pdf": outputs["pdf"],
            "reader_zip": outputs["zip"],
            "longform_pdf": outputs["pdf"],
        }
        nested = {
            "rich_markdown": outputs["markdown"],
            "rich_docx": outputs["docx"],
            "rich_pdf": outputs["pdf"],
            "rich_zip": outputs["zip"],
        }
    elif prefix == "concise":
        mapping = {
            "concise_markdown": outputs["markdown"],
            "concise_docx": outputs["docx"],
            "concise_pdf": outputs["pdf"],
            "concise_zip": outputs["zip"],
        }
        nested = mapping
    elif prefix == "relationship_addendum":
        mapping = {
            "relationship_addendum_markdown": outputs["markdown"],
            "relationship_addendum_docx": outputs["docx"],
            "relationship_addendum_pdf": outputs["pdf"],
            "relationship_addendum_zip": outputs["zip"],
        }
        nested = mapping
    else:
        mapping = {
            "relationship_concise_source_markdown": outputs["source_markdown"],
            "relationship_concise_markdown": outputs["markdown"],
            "relationship_concise_docx": outputs["docx"],
            "relationship_concise_pdf": outputs["pdf"],
            "relationship_concise_zip": outputs["zip"],
        }
        nested = mapping

    for key, value in mapping.items():
        if value:
            artifacts[key] = value
    for key, value in nested.items():
        if value:
            delivery[key] = value
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    source = Path(args.markdown)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown = source.read_text(encoding="utf-8")

    md_path = output_dir / f"{args.basename}.md"
    docx_path = output_dir / f"{args.basename}.docx"
    pdf_path = output_dir / f"{args.basename}.pdf"

    shutil.copyfile(source, md_path)
    subtitle = "" if args.no_subtitle else args.subtitle
    actual_docx = write_with_lock_fallback(export_docx, markdown, docx_path, subtitle, args.avoid_locked)
    actual_pdf = write_with_lock_fallback(export_pdf, markdown, pdf_path, subtitle, args.avoid_locked)

    zip_path = Path(args.zip_path) if args.zip_path else None
    if zip_path:
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for item in [md_path, actual_docx, actual_pdf]:
                zf.write(item, arcname=item.name)

    result = {
        "source_markdown": str(source),
        "markdown": str(md_path),
        "docx": str(actual_docx),
        "pdf": str(actual_pdf),
        "zip": str(zip_path) if zip_path else None,
        "manifest_updated": False,
    }
    if args.manifest:
        if not args.artifact_prefix:
            raise SystemExit("--artifact-prefix is required with --manifest")
        update_manifest(Path(args.manifest), args.artifact_prefix, result)
        result["manifest_updated"] = True

    if args.json or args.manifest:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
