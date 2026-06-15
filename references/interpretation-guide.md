# Interpretation Guide

source_id: `SRC-PROJECT-INTERPRETATION-GUIDE`

## Output Shape

Use this structure for user-facing readings:

1. **排盘证据**: state which scripts/modules were used and list the key structured facts.
2. **核心判断**: give 3-5 direct but non-fatalistic observations.
3. **交叉印证**: compare Bazi, Ziwei, MBTI, Liuyao, and Xiao Liuren only when those modules were actually run.
4. **现实建议**: convert symbolic findings into practical choices, communication style, timing, risk control, or reflection prompts.
5. **校准问题**: ask 2-4 concrete questions about past events or current facts.

## Longform Article Mode

When the user wants a less dense, more readable, shareable report, create a separate plain-text Markdown article in addition to the structured JSON and fact-archive Markdown.

Use `templates/longform-analysis-template.md` as the reusable structure:

1. Start with a judgment-style summary: a memorable, direct, non-fatalistic claim; then a core contradiction; then a compact evidence preview.
2. Explain Bazi, Ziwei, and Western astrology separately before combining them.
3. Derive personality from evidence, not from generic adjectives.
4. Write past years as a calibration story: chart trigger -> likely lived experience -> validation question.
5. Write future years as trend and preparation, not as fixed prophecy.
6. Cover career, love, wealth, health/energy, collaboration, and learning/output.
7. End with practical advice tied to the chart evidence.

The longform article should be readable by non-specialists. Avoid dense tables unless the user asks for them. Prefer short sections, clear paragraphs, and repeated grounding phrases such as "从这个盘面看", "更像", "倾向于", and "需要校准".

For paid reader-facing reports, the first 1500-2500 Chinese characters must work like a strong Chinese social-media article without becoming a marketing article. Use the structure: direct judgment -> lived scene -> why this matters -> evidence preview -> what the reader can do with it. Technical facts are evidence, not the opening attraction. Avoid starting with screenshots, baseline chart wording, command/process notes, or long lists of birth data.

Use second person ("你") by default for paid reader-facing reports. This makes the report feel like a personal document instead of an observer profile. Use third person only when the user explicitly says the report is for a third party, parent, partner, or consultant.

Preferred delivery is the "reader-rich" version:

- Target 18000-24000 Unicode characters unless the user asks for a shorter version.
- Use the fixed 16-section H2 outline plus required H3 from `templates/longform-analysis-template.md`; do not freely rename, add, or remove required sections in reader-rich delivery.
- Treat birth minutes as approximate by default unless the user explicitly says the time comes from a birth certificate, hospital record, or another verifiable source. Run `scripts/audit_birth_time_sensitivity.py` by default and separate stable anchors from time-sensitive anchors in the article.
- Include at least 8 explicit "白话场景" or "情景推演" blocks that translate symbolic findings into realistic work, money, love, family, friendship, collaboration, and energy-management situations.
- Keep script names, JSON paths, execution commands, coordinate-source details, and validation notes out of the reader-facing article.
- Put the evidence chain, commands, coordinates, validation, and known limits in the manifest/final delivery files instead.
- Include concrete scenes: how the person behaves, how others may misread them, risks, and practical corrections.
- Reduce repetitive filler. Each paragraph should add at least one new judgment, new evidence, new lived scene, new risk, new action, or new calibration point.
- Do not leak production/process language into the reader-facing article, such as "这一章不再解释", "客户可以执行", "下面每一条都对应", or "前文的命盘结构".
- Validate with `scripts/validate_longform_report.py --profile reader-rich`.
- Audit consistency with `scripts/audit_longform_consistency.py --strict` before packaging.

Default complete delivery also includes a concise reader version:

- Use `templates/concise-report-template.md` as the shape reference.
- Target 5500-9000 Unicode characters.
- Save the editable source as `<RUN_DIR>/drafts/<case>-concise-report.md`.
- Package to `<RUN_DIR>/delivery/<reader-title>简洁版.md|docx|pdf`.
- Keep the same second-person paid-report voice, but reduce evidence density and avoid the fixed reader-rich 16-section outline.
- Include one compact professional-anchor paragraph with the strongest stable Bazi/Ziwei/Western facts.
- Cover relationship/love, career, money, and the next 3-5 years.
- Do not use internal style labels such as "小红书", "情绪价值", or "真实感增强" in filenames, titles, final-delivery notes, or reader-facing text.
- Run `scripts/audit_longform_consistency.py` with facts JSON. Non-strict `passed=true` is sufficient for concise delivery; strict warnings about missing reader-rich fixed sections can be kept as template differences, but hard failures must be resolved.

After drafting, run `scripts/validate_longform_report.py` with `--facts-json` whenever a combo JSON is available. Add case-specific `--must-contain` facts only when the fact is not present in the JSON.

## Schema Handling

- Treat `facts` as calculation evidence.
- Treat `warnings` as things that must be disclosed before interpretation.
- Treat `uncertainties` as scope limits, not errors.
- Use `interpretation_hints` to choose the reading order.
- Ask `calibration_questions` after the initial reading; do not change raw calculated facts based on feedback.

## Knowledge Handling

- Use `knowledge/source-index.md` as the source map and `knowledge/rules/inference-contract.md` as the claim contract.
- Before writing paid analysis, read the relevant domain cards: `knowledge/bazi/*`, `knowledge/ziwei/*`, `knowledge/western/*`, `knowledge/mbti/*`, `knowledge/liuyao/*`, `knowledge/xiaoliuren/*`, and `knowledge/writing/reader-rich-report.md` as applicable.
- Classify important claims as `calculated_fact`, `classical_rule`, `modern_synthesis`, `case_calibration`, or `practical_advice`.
- Do not imply that a modern paid-report judgment is directly from a classic unless a curated knowledge card supports it.
- Classical sources provide principles and vocabulary; they do not override script facts, time sensitivity checks, or user calibration.
- If a rule is only candidate-level knowledge, write it as a tendency and keep a limit or calibration question.
- Case lessons can enter global knowledge only after they are anonymized and human approved.
- Network research is allowed only as source acquisition. It must be promoted through `knowledge/rules/research-and-promotion.md` before it becomes runtime report evidence.

## Tone

- Use concise Chinese.
- Avoid terror, absolutist language, and claims of certainty.
- Say “倾向于”, “更像”, “需要验证”, “从这个盘面看” instead of “必定”.
- For health, finance, legal, and relationships, give grounded caution and suggest professional help where appropriate.

## Cross-System Rules

- Bazi: treat as structure of season, day master, ten gods, luck cycle, and five-element tension.
- Ziwei: treat as palace/star role distribution and four-hua motion.
- MBTI: treat as behavioral language, not fate.
- Liuyao: treat as question-specific snapshot; do not override natal charts with a single divination result.
- Xiao Liuren: treat as quick timing/weather check, weaker than Liuyao.
- Combo: explain overlap first, then contradictions. If two systems disagree, ask calibration questions instead of forcing one conclusion.

## Red Lines

- Do not predict death.
- Do not pressure the user into paid or high-risk decisions.
- Do not claim medical diagnosis.
- Do not fabricate calculations when a dependency is missing; report the missing dependency and proceed only with available modules.
