#!/usr/bin/env python3
"""Reader delivery packaging tests for xuanxue-console."""

from __future__ import annotations

import json
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_READER_DELIVERY_SCRIPT = Path(__file__).with_name("package_reader_delivery.py")
PACKAGE_MOBILE_HTML_SCRIPT = Path(__file__).with_name("package_mobile_html.py")
FINALIZE_CASE_SCRIPT = Path(__file__).with_name("finalize_case.py")


def load_finalize_case():
    spec = importlib.util.spec_from_file_location("finalize_case", FINALIZE_CASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load finalize_case.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeliveryPackagingTests(unittest.TestCase):
    def test_package_mobile_html_outputs_plain_reader(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "concise.md"
            output = Path(tmp) / "mobile.html"
            manifest = Path(tmp) / "case_manifest.json"
            manifest.write_text(json.dumps({"artifacts": {}}, ensure_ascii=False), encoding="utf-8")
            source.write_text(
                "# 乙方命盘：你不是软，你是在确认谁值得你放心\n\n"
                "## 先说最像你的地方：先观察，再靠近\n\n"
                "**你最该记住的是：慢不是拒绝，而是在确认谁值得你放心。**\n\n"
                "你是不是经常这样：先观察，再决定要不要靠近。\n\n"
                "## 专业锚点：事实只做短锚点\n\n"
                "### 只保留必要锚点\n\n"
                "这一段先交代专业事实的边界，不急着把重点放粗。\n\n"
                "专业事实不需要铺得很满。一句话说，专业锚点只负责帮你抓住主线。\n\n"
                "四柱和星盘只作为短锚点，不暴露过程文字。\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_MOBILE_HTML_SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                    "--manifest",
                    str(manifest),
                    "--artifact-key",
                    "concise_mobile_html",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertEqual(result["sections"], 2)
            self.assertTrue(result["manifest_updated"])
            updated = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(updated["artifacts"]["concise_mobile_html"], str(output))
            self.assertEqual(updated["artifacts"]["delivery"]["concise_mobile_html"], str(output))
            html_text = output.read_text(encoding="utf-8")
            for expected in [
                "viewport",
                "FangSong",
                "仿宋",
                "#fff7d8",
                '<details class="toc">',
                "<summary>目录</summary>",
                'href="#section-01"',
                '<span class="title-topic">乙方命盘：</span>',
                '<span class="title-hook">你不是软，你是在确认谁值得你放心</span>',
                '<span class="section-topic">先说最像你的地方：</span>',
                '<span class="section-hook">先观察，再靠近</span>',
                "专业事实不需要铺得很满。<strong>一句话说，专业锚点只负责帮你抓住主线。</strong>",
                "font-size: inherit",
                "font-weight: 700",
                "h3 {",
                "font-size: 17px",
            ]:
                self.assertIn(expected, html_text)
            root_css = re.search(r":root \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(root_css)
            self.assertIn("--bg: #fff7d8", root_css.group("body"))
            self.assertIn("--paper: #fff7d8", root_css.group("body"))
            h2_css = re.search(r"h2 \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(h2_css)
            self.assertIn("font-size: 20px", h2_css.group("body"))
            self.assertIn("font-weight: 700", h2_css.group("body"))
            self.assertIn("word-break: keep-all", h2_css.group("body"))
            self.assertIn("overflow-wrap: break-word", h2_css.group("body"))
            self.assertIn("text-wrap: balance", h2_css.group("body"))
            self.assertNotIn("overflow-wrap: anywhere", h2_css.group("body"))
            self.assertNotIn("background", h2_css.group("body"))
            self.assertNotIn("border-left", h2_css.group("body"))
            section_topic_css = re.search(r"\.section-topic \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(section_topic_css)
            self.assertIn("font-size: inherit", section_topic_css.group("body"))
            self.assertIn("font-weight: inherit", section_topic_css.group("body"))
            self.assertIn("color: var(--title)", section_topic_css.group("body"))
            self.assertIn("text-wrap: balance", section_topic_css.group("body"))
            section_hook_css = re.search(r"\.section-hook \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(section_hook_css)
            self.assertIn("font-size: inherit", section_hook_css.group("body"))
            self.assertIn("font-weight: inherit", section_hook_css.group("body"))
            self.assertIn("color: var(--title)", section_hook_css.group("body"))
            self.assertIn("text-wrap: balance", section_hook_css.group("body"))
            strong_css = re.search(r"strong \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(strong_css)
            self.assertNotIn("linear-gradient", strong_css.group("body"))
            self.assertNotIn("background: rgba", strong_css.group("body"))
            h3_css = re.search(r"h3 \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(h3_css)
            self.assertIn("color: var(--title)", h3_css.group("body"))
            footer_css = re.search(r"\.footer \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(footer_css)
            self.assertNotIn("background:", footer_css.group("body"))
            for forbidden in ["http://", "https://", "progress", "sticky", "简洁阅读器", "脚本路径", "JSON 路径", "执行命令"]:
                self.assertNotIn(forbidden, html_text)
            self.assertNotIn("overflow-wrap: anywhere", html_text)
            self.assertNotIn("星命人格简洁版报告", html_text)

    def test_single_rich_mobile_html_uses_same_reader_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "rich.md"
            output = Path(tmp) / "rich-mobile.html"
            manifest = Path(tmp) / "case_manifest.json"
            manifest.write_text(json.dumps({"artifacts": {"delivery": {}}}, ensure_ascii=False), encoding="utf-8")
            source.write_text(
                "# 甲方命盘总评：清醒有锋芒，越稳越能成事\n\n"
                "## 事业主线：把聪明落成稳定作品\n\n"
                "这一章先把事业主线铺开，不把加粗机械地放在开头。\n\n"
                "你真正该记住的是，聪明不是只用来反应快，而是要变成可复用的判断、作品和交付节奏。\n\n"
                "这类盘在现实里很容易先看见机会，再被细节、承诺和长期节奏筛选。\n\n"
                "## 关系节奏：先被吸引，再看能否安心\n\n"
                "你在关系里并不缺火花，**真正要稳住的是持续回应和现实安排。**\n\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_MOBILE_HTML_SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                    "--manifest",
                    str(manifest),
                    "--artifact-key",
                    "rich_mobile_html",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertEqual(result["sections"], 2)
            updated = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(updated["artifacts"]["rich_mobile_html"], str(output))
            self.assertEqual(updated["artifacts"]["delivery"]["rich_mobile_html"], str(output))
            html_text = output.read_text(encoding="utf-8")
            self.assertIn('<span class="title-topic">甲方命盘总评：</span>', html_text)
            self.assertIn('<span class="title-hook">清醒有锋芒，越稳越能成事</span>', html_text)
            self.assertIn('<span class="section-topic">事业主线：</span>', html_text)
            self.assertIn('<span class="section-hook">把聪明落成稳定作品</span>', html_text)
            self.assertIn(
                "<strong>你真正该记住的是，聪明不是只用来反应快，而是要变成可复用的判断、作品和交付节奏。</strong>",
                html_text,
            )
            self.assertIn("font-weight: 700", html_text)
            h1_css = re.search(r"h1 \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(h1_css)
            self.assertIn("word-break: keep-all", h1_css.group("body"))
            self.assertIn("overflow-wrap: break-word", h1_css.group("body"))
            self.assertIn("text-wrap: balance", h1_css.group("body"))
            self.assertNotIn("overflow-wrap: anywhere", h1_css.group("body"))
            self.assertNotIn("overflow-wrap: anywhere", html_text)
            strong_css = re.search(r"strong \{(?P<body>.*?)\n    \}", html_text, re.S)
            self.assertIsNotNone(strong_css)
            self.assertIn("background: none", strong_css.group("body"))
            self.assertNotIn("linear-gradient", strong_css.group("body"))
            self.assertNotIn("box-shadow", strong_css.group("body"))
            self.assertNotIn("简洁阅读器", html_text)
            self.assertNotIn("丰富版v", html_text)

    def test_single_mobile_html_autofills_distributed_reader_takeaways(self) -> None:
        finalize_case = load_finalize_case()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "single-reader.md"
            output = Path(tmp) / "single-reader.html"
            sections = []
            takeaway_phrases = [
                "更直白地说，你的优势不是反应快，而是能把判断落成稳定节奏。",
                "最重要的是，你要把聪明用在可持续的选择上。",
                "现实表现是，你会先看见机会，再用细节确认它值不值得投入。",
                "更现实的做法，是先稳住日常节奏，再放大关键机会。",
                "真正的问题，不是你没有能力，而是容易被短期波动打乱排序。",
                "真正的优势，是你能在复杂局面里很快抓住主线。",
                "最稳的方式，是把情绪、关系和事业分开处理。",
                "说白了，你不是缺方向，而是需要一个能反复执行的框架。",
                "换句话说，你越能稳住基本盘，越容易把好运接住。",
                "你会发现，真正适合你的路通常不是最热闹的那条。",
            ]
            for index, phrase in enumerate(takeaway_phrases, start=1):
                sections.append(
                    f"## 第{index}章：单盘阅读重点\n\n"
                    "这一章先写普通说明，避免加粗总是落在第一句。\n\n"
                    f"{phrase}\n\n"
                    "后面再补充现实场景，让段落读起来不是术语清单。\n"
                )
            source.write_text(
                "# 甲方命盘总评：清醒有锋芒，越稳越能成事\n\n" + "\n".join(sections),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_MOBILE_HTML_SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            html_text = output.read_text(encoding="utf-8")
            self.assertGreaterEqual(html_text.count("<strong>"), 10)
            self.assertIn("<strong>更直白地说，你的优势不是反应快，而是能把判断落成稳定节奏。</strong>", html_text)
            self.assertIn("<strong>更现实的做法，是先稳住日常节奏，再放大关键机会。</strong>", html_text)
            for label in ["rich_mobile_html", "concise_mobile_html"]:
                failures: list[str] = []
                finalize_case.check_mobile_html_contract(output, failures, label)
                self.assertFalse(failures, f"{label} failures: {failures}")

    def test_finalize_mobile_html_contract_rejects_card_like_reader(self) -> None:
        finalize_case = load_finalize_case()
        with tempfile.TemporaryDirectory() as tmp:
            bad_html = Path(tmp) / "bad-mobile.html"
            bad_html.write_text(
                '<html><head><meta name="viewport" content="width=device-width"></head>'
                '<body><h1>简洁阅读器</h1><section style="background: linear-gradient(red, blue);">'
                "脚本路径 JSON 路径 执行命令</section></body></html>",
                encoding="utf-8",
            )
            failures: list[str] = []
            finalize_case.check_mobile_html_contract(bad_html, failures, "concise_mobile_html")
            self.assertTrue(failures)
            joined = "\n".join(failures)
            self.assertIn("missing markers", joined)
            self.assertIn("forbidden markers", joined)
            self.assertIn("linear-gradient", joined)
            self.assertIn("简洁阅读器", joined)

    def test_finalize_reader_markdown_contract_rejects_process_markers(self) -> None:
        finalize_case = load_finalize_case()
        with tempfile.TemporaryDirectory() as tmp:
            markdown = Path(tmp) / "reader.md"
            markdown.write_text(
                "# 甲方命盘总评：清醒有锋芒，越稳越能成事\n\n"
                "这份简洁版只作为 finalize readiness 测试源稿，确认 Markdown、DOCX、PDF 都能被识别。\n"
                "这里不能混入项目流程、外部 run、过程产物、用于约束AI或新加段落这类内部话术。\n"
                "也不能把乐观收束、情绪价值、真实感增强、小红书、新媒体图文、找问题、找茬写进读者稿。\n",
                encoding="utf-8",
            )
            failures: list[str] = []
            finalize_case.check_reader_markdown_contract(markdown, failures, "concise_markdown")
            joined = "\n".join(failures)
            self.assertIn("reader-facing Markdown contains process/delivery markers", joined)
            self.assertIn("测试源稿", joined)
            self.assertIn("finalize readiness", joined)
            self.assertIn("项目流程", joined)
            self.assertIn("外部 run", joined)
            self.assertIn("过程产物", joined)
            self.assertIn("用于约束AI", joined)
            self.assertIn("新加段落", joined)
            self.assertIn("乐观收束", joined)
            self.assertIn("情绪价值", joined)
            self.assertIn("真实感增强", joined)
            self.assertIn("小红书", joined)
            self.assertIn("新媒体图文", joined)
            self.assertIn("找问题", joined)
            self.assertIn("找茬", joined)

    def test_finalize_reader_markdown_contract_rejects_versioned_title(self) -> None:
        finalize_case = load_finalize_case()
        with tempfile.TemporaryDirectory() as tmp:
            markdown = Path(tmp) / "reader.md"
            markdown.write_text(
                "# 甲方命盘丰富版v9：清醒有锋芒，越稳越能成事\n\n"
                "这是一份读者正文，标题不应该把版本号或交付标签写给读者看。\n",
                encoding="utf-8",
            )
            failures: list[str] = []
            finalize_case.check_reader_markdown_contract(markdown, failures, "reader_markdown")
            joined = "\n".join(failures)
            self.assertIn("reader-facing Markdown H1 contains delivery/process labels", joined)
            self.assertIn("versioned delivery label", joined)

    def test_finalize_mobile_html_contract_rejects_hard_cut_title_css(self) -> None:
        finalize_case = load_finalize_case()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "reader.md"
            output = Path(tmp) / "mobile.html"
            source.write_text(
                "\n".join(
                    [
                        "# 甲方命盘总评：强牵引互补缘",
                        "",
                        "## 关系总评：越懂越入心",
                        "",
                        "一句话说，真正要稳住的是表达节奏。",
                    ]
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_MOBILE_HTML_SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            html_text = output.read_text(encoding="utf-8")
            output.write_text(
                html_text.replace("overflow-wrap: break-word;", "overflow-wrap: anywhere;", 1),
                encoding="utf-8",
            )
            failures: list[str] = []
            finalize_case.check_mobile_html_contract(output, failures, "rich_mobile_html")
            self.assertIn("title CSS must not hard-cut Chinese text: h1", "\n".join(failures))

    def test_finalize_mobile_html_contract_rejects_versioned_delivery_title(self) -> None:
        finalize_case = load_finalize_case()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "reader.md"
            output = Path(tmp) / "mobile.html"
            source.write_text(
                "# 甲方命盘丰富版v9：清醒有锋芒，越稳越能成事\n\n"
                "## 第一章：稳定判断\n\n"
                "更直白地说，你的优势不是反应快，而是能把判断落成稳定节奏。\n\n"
                "## 第二章：关系节奏\n\n"
                "最重要的是，你要把聪明用在可持续的选择上。\n\n"
                "## 第三章：事业路径\n\n"
                "现实表现是，你会先看见机会，再用细节确认它值不值得投入。\n\n"
                "## 第四章：财富方式\n\n"
                "更现实的做法，是先稳住日常节奏，再放大关键机会。\n\n"
                "## 第五章：精力管理\n\n"
                "真正的问题，不是你没有能力，而是容易被短期波动打乱排序。\n\n"
                "## 第六章：未来几年\n\n"
                "真正的优势，是你能在复杂局面里很快抓住主线。\n\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_MOBILE_HTML_SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            failures: list[str] = []
            finalize_case.check_mobile_html_contract(output, failures, "rich_mobile_html")
            joined = "\n".join(failures)
            self.assertIn("title contains delivery/process labels", joined)
            self.assertIn("versioned delivery label", joined)

    def test_finalize_mobile_html_contract_requires_distributed_bold_takeaways(self) -> None:
        finalize_case = load_finalize_case()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "reader.md"
            output = Path(tmp) / "mobile.html"
            source.write_text(
                "# 甲方命盘总评：清醒有锋芒，越稳越能成事\n\n"
                "## 第一章：稳定判断\n\n普通段落只说明背景，没有直白结论。\n\n"
                "## 第二章：关系节奏\n\n普通段落只说明背景，没有直白结论。\n\n"
                "## 第三章：事业路径\n\n普通段落只说明背景，没有直白结论。\n\n"
                "## 第四章：财富方式\n\n普通段落只说明背景，没有直白结论。\n\n"
                "## 第五章：精力管理\n\n普通段落只说明背景，没有直白结论。\n\n"
                "## 第六章：未来几年\n\n普通段落只说明背景，没有直白结论。\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_MOBILE_HTML_SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            failures: list[str] = []
            finalize_case.check_mobile_html_contract(output, failures, "rich_mobile_html")
            joined = "\n".join(failures)
            self.assertIn("needs at least 6 concise bold takeaway sentences", joined)
            self.assertIn("bold takeaways should be distributed across at least 6 sections", joined)

    def test_package_reader_delivery_can_write_json_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            delivery = root / "delivery"
            manifest = root / "case_manifest.json"
            source.write_text("# 测试报告\n\n这是用于打包脚本的短文本。\n" * 8, encoding="utf-8")
            manifest.write_text(json.dumps({"artifacts": {}}, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_READER_DELIVERY_SCRIPT),
                    str(source),
                    "--output-dir",
                    str(delivery),
                    "--basename",
                    "测试丰富版",
                    "--zip",
                    str(delivery / "rich.zip"),
                    "--json",
                    "--manifest",
                    str(manifest),
                    "--artifact-prefix",
                    "rich",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            self.assertTrue(result["manifest_updated"])
            updated = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(updated["artifacts"]["reader_markdown"], result["markdown"])
            self.assertEqual(updated["artifacts"]["longform_markdown"], result["markdown"])
            self.assertEqual(updated["artifacts"]["longform_pdf"], result["pdf"])
            self.assertEqual(updated["artifacts"]["delivery"]["rich_zip"], result["zip"])

            manifest.write_text(json.dumps({"artifacts": {}}, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_READER_DELIVERY_SCRIPT),
                    str(source),
                    "--output-dir",
                    str(delivery),
                    "--basename",
                    "测试合盘简洁版",
                    "--zip",
                    str(delivery / "relationship-concise.zip"),
                    "--json",
                    "--manifest",
                    str(manifest),
                    "--artifact-prefix",
                    "relationship_concise",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            relationship_result = json.loads(proc.stdout)
            relationship_updated = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                relationship_updated["artifacts"]["relationship_concise_source_markdown"],
                str(source),
            )
            self.assertEqual(relationship_result["source_markdown"], str(source))
            self.assertEqual(relationship_updated["artifacts"]["relationship_concise_markdown"], relationship_result["markdown"])
            self.assertEqual(relationship_updated["artifacts"]["relationship_concise_docx"], relationship_result["docx"])
            self.assertEqual(relationship_updated["artifacts"]["relationship_concise_pdf"], relationship_result["pdf"])
            self.assertEqual(relationship_updated["artifacts"]["relationship_concise_zip"], relationship_result["zip"])
            self.assertEqual(
                relationship_updated["artifacts"]["delivery"]["relationship_concise_markdown"],
                relationship_result["markdown"],
            )
            self.assertEqual(
                relationship_updated["artifacts"]["delivery"]["relationship_concise_docx"],
                relationship_result["docx"],
            )

    def test_package_reader_delivery_can_omit_fixed_subtitle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.md"
            delivery = root / "delivery"
            source.write_text(
                "# 乙方命盘：慢热不是退缩，是在确认谁值得放心\n\n"
                "## 先说最像你的地方：先观察，再靠近\n\n"
                "你真正该记住的是，慢不是拒绝，而是在确认谁值得你放心。\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(PACKAGE_READER_DELIVERY_SCRIPT),
                    str(source),
                    "--output-dir",
                    str(delivery),
                    "--basename",
                    "乙方命盘简洁版",
                    "--no-subtitle",
                    "--json",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                encoding="utf-8",
            )
            result = json.loads(proc.stdout)
            with zipfile.ZipFile(result["docx"]) as docx_zip:
                document_xml = docx_zip.read("word/document.xml").decode("utf-8")
            self.assertIn("乙方命盘：慢热不是退缩，是在确认谁值得放心", document_xml)
            self.assertNotIn("综合命盘长文报告", document_xml)
            self.assertNotIn("星命人格简洁版报告", document_xml)



if __name__ == "__main__":
    unittest.main()
