#!/usr/bin/env python3
"""Shared reader-facing title contract for Markdown and mobile HTML delivery."""

from __future__ import annotations

import re


TITLE_FORBIDDEN_PATTERNS = [
    (re.compile(r"(丰富版|简洁版)\s*[vV]\s*\d+"), "versioned delivery label"),
    (re.compile(r"合盘长文分析丰富版"), "internal relationship delivery label"),
    (re.compile(r"简洁阅读器"), "reader-widget label"),
    (re.compile(r"手机阅读"), "artifact format label"),
]


def reader_title_label_failures(title: str) -> list[str]:
    return [reason for pattern, reason in TITLE_FORBIDDEN_PATTERNS if pattern.search(title)]
