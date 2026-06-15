#!/usr/bin/env python3
"""Package a reader-facing Markdown report as a mobile-first standalone HTML file."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


AUTO_STRONG_PATTERNS = [
    "一句话说",
    "一句话先说",
    "说到底",
    "说白了",
    "换句话说",
    "更直白地说",
    "最该记住",
    "最重要的是",
    "真正该",
    "真正要",
    "真正能",
    "真正让",
    "真正的问题",
    "真正的优势",
    "核心",
    "关键",
    "重点是",
    "总评",
    "可以定为",
    "更适合你",
    "适合你的",
    "最容易",
    "最像",
    "最怕",
    "最有价值",
    "要记住",
    "你要做的",
    "你现在要",
    "一定要",
    "这意味着",
    "这类盘",
    "这个盘",
    "现实里",
    "现实中",
    "现实层面",
    "现实表现是",
    "你会发现",
    "你不是",
    "真正要看",
    "真正要稳住",
    "最值得",
    "底层",
    "落地做法",
    "建议动作",
    "更现实的做法",
    "最稳的方式",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build mobile-first standalone HTML from reader Markdown.")
    parser.add_argument("markdown", help="Source Markdown file.")
    parser.add_argument("--output", required=True, help="Output HTML path.")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--label", default="")
    parser.add_argument("--manifest", help="Optional external case_manifest.json to update.")
    parser.add_argument(
        "--artifact-key",
        default="mobile_html",
        choices=[
            "mobile_html",
            "concise_mobile_html",
            "rich_mobile_html",
            "relationship_mobile_html",
            "relationship_concise_mobile_html",
        ],
        help="Manifest artifact key to update when --manifest is provided.",
    )
    return parser.parse_args()


def sentence_candidates(text: str) -> list[str]:
    return [match.group(0) for match in re.finditer(r"[^。！？!?；;]+[。！？!?；;]?", text)]


def should_auto_strong(sentence: str) -> bool:
    compact = sentence.strip()
    if len(compact) < 10 or len(compact) > 58:
        return False
    if re.search(r"(scripts/|scripts\\|\.json|\.py|RUN_DIR|manifest|截图路径|执行命令)", compact):
        return False
    if any(pattern in compact for pattern in AUTO_STRONG_PATTERNS):
        return True
    return bool(re.search(r"不是.+而是|不要.+要|先.+再|与其.+不如", compact))


def auto_strong_plain_sentence(text: str) -> str:
    if "**" in text:
        return text
    for sentence in sentence_candidates(text):
        if should_auto_strong(sentence):
            return text.replace(sentence, f"**{sentence}**", 1)
    return text


def inline_markdown(text: str, *, auto_strong: bool = False) -> str:
    if auto_strong:
        text = auto_strong_plain_sentence(text)
    escaped = html.escape(text.strip())
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def plain_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text.strip()


def section_title_html(title: str) -> str:
    if "：" in title:
        topic, hook = title.split("：", 1)
        return (
            f'<span class="section-topic">{html.escape(topic.strip())}：</span>'
            f'<span class="section-hook">{html.escape(hook.strip())}</span>'
        )
    if ":" in title:
        topic, hook = title.split(":", 1)
        return (
            f'<span class="section-topic">{html.escape(topic.strip())}:</span>'
            f'<span class="section-hook">{html.escape(hook.strip())}</span>'
        )
    return f'<span class="section-hook">{html.escape(title)}</span>'


def hero_title_html(title: str) -> str:
    if "：" in title:
        topic, hook = title.split("：", 1)
        return (
            f'<span class="title-topic">{html.escape(topic.strip())}：</span>'
            f'<span class="title-hook">{html.escape(hook.strip())}</span>'
        )
    if ":" in title:
        topic, hook = title.split(":", 1)
        return (
            f'<span class="title-topic">{html.escape(topic.strip())}:</span>'
            f'<span class="title-hook">{html.escape(hook.strip())}</span>'
        )
    return html.escape(title)


def section_id(index: int) -> str:
    return f"section-{index:02d}"


def parse_markdown(markdown: str) -> tuple[str, list[dict[str, object]]]:
    title = "命盘简洁版"
    sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    list_open = False

    def ensure_section() -> dict[str, object]:
        nonlocal current
        if current is None:
            current = {
                "title": "正文",
                "blocks": [],
                "id": section_id(1),
                "has_strong": False,
                "paragraph_count": 0,
            }
            sections.append(current)
        return current

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            ensure_section()["blocks"].append("</ul>")
            list_open = False

    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            close_list()
            continue
        if line.startswith("# "):
            title = plain_markdown(line[2:])
            continue
        if line.startswith("## "):
            close_list()
            current = {
                "title": plain_markdown(line[3:]),
                "blocks": [],
                "id": section_id(len(sections) + 1),
                "has_strong": False,
                "paragraph_count": 0,
            }
            sections.append(current)
            continue
        if line.startswith("### "):
            close_list()
            ensure_section()["blocks"].append(f"<h3>{inline_markdown(line[4:])}</h3>")
            continue
        if line.startswith("- "):
            if not list_open:
                ensure_section()["blocks"].append("<ul>")
                list_open = True
            ensure_section()["blocks"].append(f"<li>{inline_markdown(line[2:])}</li>")
            continue
        close_list()
        section = ensure_section()
        paragraph_count = int(section.get("paragraph_count") or 0)
        auto_strong = paragraph_count > 0 and not bool(section.get("has_strong")) and any(
            should_auto_strong(sentence) for sentence in sentence_candidates(line)
        )
        rendered = inline_markdown(line, auto_strong=auto_strong)
        if "<strong>" in rendered:
            section["has_strong"] = True
        section["paragraph_count"] = paragraph_count + 1
        paragraph_class = ' class="key-para"' if "<strong>" in rendered else ""
        section["blocks"].append(f"<p{paragraph_class}>{rendered}</p>")

    close_list()
    return title, sections


def render_html(title: str, subtitle: str, label: str, sections: list[dict[str, object]]) -> str:
    section_html_parts: list[str] = []
    for item in sections:
        blocks = "\n".join(str(block) for block in item["blocks"])
        section_html_parts.append(
            f'''
      <section class="article-section" id="{item["id"]}">
        <h2>{section_title_html(str(item["title"]))}</h2>
        {blocks}
      </section>'''.rstrip()
        )
    section_html = "\n".join(section_html_parts)
    toc_items = "\n".join(
        f'          <a href="#{item["id"]}">{html.escape(str(item["title"]))}</a>' for item in sections
    )
    safe_title = html.escape(title)
    safe_title_display = hero_title_html(title)
    safe_subtitle = html.escape(subtitle)
    safe_label = html.escape(label)
    label_html = f'<div class="eyebrow">{safe_label}</div>' if safe_label else ""
    subtitle_html = f'<p class="subtitle">{safe_subtitle}</p>' if safe_subtitle else ""
    toc_html = (
        f'''    <details class="toc">
      <summary>目录</summary>
      <nav>
{toc_items}
      </nav>
    </details>'''
        if sections
        else ""
    )
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="format-detection" content="telephone=no">
  <title>{safe_title}</title>
  <style>
    :root {{
      --bg: #fff7d8;
      --paper: #fff7d8;
      --ink: #3a2d1b;
      --title: #2b1d0e;
      --muted: #756246;
      --line: rgba(116, 92, 52, 0.22);
      --soft: rgba(116, 92, 52, 0.08);
    }}

    * {{
      box-sizing: border-box;
    }}

    html {{
      scroll-behavior: smooth;
      -webkit-text-size-adjust: 100%;
      text-size-adjust: 100%;
      width: 100%;
      overflow-x: hidden;
      hanging-punctuation: allow-end;
      font-kerning: normal;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "FangSong", "仿宋", "STFangsong", "华文仿宋", "Songti SC", "SimSun", serif;
      font-size: 17px;
      line-height: 1.9;
      letter-spacing: 0;
      width: 100%;
      overflow-x: hidden;
      word-break: normal;
      line-break: strict;
      text-wrap: pretty;
    }}

    .shell {{
      width: 100%;
      max-width: 430px;
      margin: 0 auto;
      background: var(--paper);
      min-height: 100vh;
      overflow-x: hidden;
      position: relative;
    }}

    .toc {{
      position: fixed;
      top: calc(12px + env(safe-area-inset-top));
      right: max(12px, calc((100vw - 430px) / 2 + 12px));
      z-index: 20;
      max-width: min(78vw, 310px);
      font-family: "FangSong", "仿宋", "STFangsong", "华文仿宋", "Songti SC", "SimSun", serif;
    }}

    .toc summary {{
      list-style: none;
      cursor: pointer;
      user-select: none;
      color: var(--title);
      background: rgba(255, 247, 216, 0.9);
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 12px;
      font-size: 14px;
      line-height: 1.25;
      box-shadow: none;
    }}

    .toc summary::-webkit-details-marker {{
      display: none;
    }}

    .toc[open] summary {{
      border-bottom-left-radius: 8px;
      border-bottom-right-radius: 8px;
    }}

    .toc nav {{
      margin-top: 6px;
      max-height: min(68vh, 540px);
      overflow-y: auto;
      padding: 8px 10px;
      background: rgba(255, 247, 216, 0.98);
      border: 1px solid var(--line);
      box-shadow: none;
    }}

    .toc a {{
      display: block;
      color: var(--title);
      text-decoration: none;
      font-size: 14px;
      line-height: 1.45;
      padding: 8px 2px;
      border-bottom: 1px solid rgba(226, 207, 150, 0.65);
    }}

    .toc a:last-child {{
      border-bottom: 0;
    }}

    .hero {{
      padding: calc(28px + env(safe-area-inset-top)) var(--page-x, 25px) 18px;
      border-bottom: 1px solid var(--line);
    }}

    .eyebrow {{
      color: var(--muted);
      font-size: 14px;
      font-weight: 400;
      letter-spacing: 0;
    }}

    h1 {{
      margin: 13px 0 7px;
      color: var(--title);
      font-size: 22px;
      line-height: 1.52;
      letter-spacing: 0;
      font-weight: 700;
      overflow-wrap: break-word;
      word-break: keep-all;
      line-break: strict;
      text-wrap: balance;
    }}

    .title-topic,
    .title-hook {{
      display: block;
      color: inherit;
      font-size: inherit;
      line-height: inherit;
      font-weight: inherit;
      overflow-wrap: break-word;
      word-break: keep-all;
      text-wrap: balance;
    }}

    .subtitle {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}

    main {{
      padding: 2px var(--page-x, 25px) 36px;
    }}

    .article-section {{
      padding: 27px 0 30px;
      border-bottom: 1px solid var(--line);
      scroll-margin-top: 66px;
    }}

    h2 {{
      margin: 0 0 19px;
      padding: 0 0 3px;
      color: var(--title);
      font-size: 20px;
      line-height: 1.42;
      letter-spacing: 0;
      font-weight: 700;
      overflow-wrap: break-word;
      word-break: keep-all;
      line-break: strict;
      text-wrap: balance;
    }}

    .section-topic {{
      display: block;
      color: var(--title);
      font-size: inherit;
      line-height: inherit;
      font-family: inherit;
      font-weight: inherit;
      overflow-wrap: break-word;
      word-break: keep-all;
      text-wrap: balance;
    }}

    .section-hook {{
      display: block;
      margin-top: 4px;
      color: var(--title);
      font-size: inherit;
      line-height: inherit;
      font-weight: inherit;
      overflow-wrap: break-word;
      word-break: keep-all;
      text-wrap: balance;
    }}

    h3 {{
      margin: 22px 0 8px;
      color: var(--title);
      font-size: 17px;
      line-height: 1.35;
      letter-spacing: 0;
      font-weight: 700;
    }}

    p {{
      margin: 0 0 15px;
      text-align: left;
      text-indent: 2em;
      overflow-wrap: break-word;
      word-break: normal;
      line-break: strict;
      text-wrap: pretty;
      orphans: 2;
      widows: 2;
    }}

    p.key-para {{
      margin: 0 0 15px;
      text-indent: 2em;
    }}

    strong {{
      color: var(--title);
      font-family: inherit;
      font-weight: 700;
      background: none;
      padding: 0;
    }}

    p.key-para strong {{
      background: none;
      padding: 0;
    }}

    code {{
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 0.92em;
      background: var(--soft);
      color: #5b3710;
      padding: 1px 5px;
      overflow-wrap: break-word;
      word-break: break-word;
    }}

    ul {{
      margin: 8px 0 16px;
      padding-left: 1.2em;
    }}

    li {{
      margin: 7px 0;
    }}

    .footer {{
      padding: 22px 18px calc(28px + env(safe-area-inset-bottom));
      color: var(--muted);
      font-size: 13px;
      line-height: 1.65;
      border-top: 1px solid var(--line);
    }}

    @media (max-width: 360px) {{
      :root {{
        --page-x: 21px;
      }}
    }}

    @media (min-width: 390px) {{
      :root {{
        --page-x: 28px;
      }}
    }}

  </style>
</head>
<body>
  <div class="shell">
{toc_html}
    <header class="hero">
      {label_html}
      <h1>{safe_title_display}</h1>
      {subtitle_html}
    </header>
    <main>
{section_html}
    </main>
    <footer class="footer">
      传统文化与自我观察参考，不替代医疗、法律、投资或重大关系决定。
    </footer>
  </div>
</body>
</html>
'''


def update_manifest(manifest_path: Path, artifact_key: str, output: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.setdefault("artifacts", {})
    if not isinstance(artifacts, dict):
        artifacts = {}
        manifest["artifacts"] = artifacts
    delivery = artifacts.setdefault("delivery", {})
    if not isinstance(delivery, dict):
        delivery = {}
        artifacts["delivery"] = delivery
    artifacts[artifact_key] = str(output)
    delivery[artifact_key] = str(output)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    markdown = Path(args.markdown).read_text(encoding="utf-8")
    title, sections = parse_markdown(markdown)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(title, args.subtitle, args.label, sections), encoding="utf-8")
    manifest_updated = False
    if args.manifest:
        update_manifest(Path(args.manifest), args.artifact_key, output)
        manifest_updated = True
    print(json.dumps({"html": str(output), "sections": len(sections), "title": title, "manifest_updated": manifest_updated}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
