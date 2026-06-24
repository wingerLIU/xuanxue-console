---
name: xuanxue-console
description: 综合玄学结构化排盘与解读 skill。Use when the user asks for 八字、四柱、紫微斗数、命盘、命理、星座、西洋占星、MBTI、人格画像、六爻、金钱卦、小六壬、占事、运势、合盘、综合玄学分析、玄学工具、赛博算命、AI 命理 agent, or wants Codex to collect birth/question data, run deterministic chart scripts, and produce grounded interpretation. This skill combines Bazi, Ziwei, Western astrology, MBTI, Liuyao, and Xiao Liuren workflows while keeping calculations in scripts and LLM prose in analysis.
---

# Xuanxue Console

综合玄学控制台。目标是把“算”的部分交给确定性脚本，把“解释”的部分交给 Codex；不要让模型手算四柱、时柱、大运、星曜或卦象。

## Core Rules

- 先问清楚用户要看的体系：`bazi`、`ziwei`、`western`、`mbti`、`liuyao`、`xiaoliuren`，或 `combo` 综合分析。
- 出生类问题必须收集：公历/农历日期、出生时间或时辰、性别；若用户给出生地或经度，八字可用 `--longitude` + `--true-solar` 做近似真太阳时校正。
- 占事类问题必须收集：明确问题、起卦方式、起卦时间；六爻优先使用用户给出的 6 次铜钱/数字结果。
- 先运行 `scripts/xuanxue_console.py` 生成 JSON，再阅读 `references/interpretation-guide.md` 输出解释。
- 明确区分：脚本输出是结构化排盘，解读是文化/娱乐参考，不替代医疗、法律、财务或人生重大决策。

## Agent Usage

用户不需要直接运行下面的命令。正常使用时，用户只要用自然语言说明要看什么，并提供出生信息、占事问题或 MBTI 类型；Codex 负责补齐必要参数、调用 helper script 生成 JSON，再按 `references/interpretation-guide.md` 输出解释。

Helper script 的作用是确定性计算，不是用户界面。不要把命令清单当成用户表单，也不要让模型手算四柱、时柱、大运、星曜或卦象。

## Helper Script Quick Start

如果依赖缺失，先安装：

```bash
python -m pip install lunar-python iztro-py ephem
```

依赖检查：

```bash
python scripts/xuanxue_console.py doctor
```

八字，带真太阳时校正；`--as-of` 可输出指定日期的流年、流月、流日、当前大运和近 N 年流年序列：

```bash
python scripts/xuanxue_console.py bazi --solar 1991-08-15 --time 01:30 --gender 男 --longitude 121.47 --true-solar --as-of 2026-06-12 --flow-window 5 --name demo
```

紫微：

```bash
python scripts/xuanxue_console.py ziwei --solar 1991-08-15 --hour-index 1 --gender 男
```

MBTI：

```bash
python scripts/xuanxue_console.py mbti --type INTJ
```

西洋占星基础行星星座：

```bash
python scripts/xuanxue_console.py western --solar 1991-08-15 --time 01:30 --tz-offset 8
```

六爻，六个数从初爻到上爻，6 老阴、7 少阳、8 少阴、9 老阳：

```bash
python scripts/xuanxue_console.py liuyao --question "这次合作能不能推进" --lines 7,8,9,7,8,6
```

小六壬：

```bash
python scripts/xuanxue_console.py xiaoliuren --lunar-month 7 --lunar-day 6 --hour-branch 丑 --question "今天适合推进吗"
```

综合报告默认输出 JSON；HTML 只作为可选 debug 快照，不进入默认交付：

```bash
python scripts/xuanxue_console.py combo --solar 1991-08-15 --time 01:30 --gender 男 --longitude 121.47 --true-solar --hour-index 1 --mbti-type INTJ --question "这次合作能不能推进" --lines 7,8,9,7,8,6 --day-gan 丁 --lunar-month 7 --lunar-day 6 --hour-branch 丑
```

## Runtime Contract

- `scripts/case_manifest_contract.py` 是 runtime contract 层；manifest alias、required artifacts、optional debug artifact 和 legacy sunset 都以它为准。
- `finalize_case.py` 必须读取 manifest 的 `validation_expectations`；单盘默认验 `combo`、rich、concise、丰富 PDF、简洁 PDF 和两个手机阅读 HTML，合盘由 `create_relationship_workspace.py` 写入 `relationship` facts、合盘事实档案、合盘章节 marker、PDF marker、rich 手机阅读 HTML 和合盘简洁版 PDF/手机阅读 artifacts。Markdown/DOCX/ZIP 只作源稿、编辑或按需导出，不作为默认读者交付失败项。失败时查看输出和 manifest.status 里的 `finalize_repair_commands`，按命令补齐后再 finalize。
- 除非出现硬错误或用户明确批准，不新增 gate 脚本；先复用 `finalize_case.py`、`audit_longform_consistency.py`、`create_followup_context.py`、`create_retrospective_intake.py`。
- 2026-07-31 后，新 run 必须写 canonical manifest keys；legacy aliases 只用于历史 run 修复。
- 知识库优先补真实去隐私复盘：哪段准、哪段不准、为什么误读、怎么改。没有案例证据时，不新增泛化写作规则。`audit_knowledge_coverage.py` 里的 `run_local_candidate_summary.repair_plan` 只提供 blocked 候选补证据路线；不能把 repair plan 当作证据本身。
- 追加问题和读者反馈先进入 `<RUN_DIR>/calibration/dialogue`；原始对话只留在 run-local，只有去隐私、人工确认过的候选复盘才晋升知识库。
- 长文 Markdown 渲染已拆到 `scripts/xuanxue_longform.py`，西占计算已拆到 `scripts/xuanxue_western.py`，runtime/workflow 测试已拆到 `scripts/test_xuanxue_runtime.py`，合盘测试已拆到 `scripts/test_xuanxue_relationship.py`，交付阅读器测试已拆到 `scripts/test_xuanxue_delivery.py`；大文件继续增长时，优先拆 CLI、八字、紫微和剩余测试模块，而不是继续向 `xuanxue_console.py` 和 `test_xuanxue_console.py` 加逻辑。

## Workflow

1. **Collect**: 用自然语言补齐必要参数，不要一次性丢长表单。
2. **Context**: 新 case 创建外部 workspace 后，运行 `scripts/build_knowledge_context.py --manifest <RUN_DIR>/case_manifest.json --module <module>`，把本次必读知识文件、来源、blocker、复盘需求、复盘采集计划和建议 `target_artifacts` 写入 `<RUN_DIR>/runtime/knowledge_context.json`。
3. **Retrospective Intake**: 运行 `scripts/create_retrospective_intake.py --manifest <RUN_DIR>/case_manifest.json`，把复盘问题、建议 `target_artifacts`、候选命令、blocked 候选修复计划、ready 候选批量 dry-run/promote 顺序、后置审计命令和“最小人工审批建议”写入 `<RUN_DIR>/calibration/retrospective-intake.md` 与 `<RUN_DIR>/runtime/retrospective_intake.json`；这些命令只辅助人工审批，不自动晋升。blocked 候选先按 `run_local_blocked_candidate_repair_plan` 补真实去隐私证据，不能用模型推测补 `domain_evidence`。最小审批建议只回答先批准哪几条最能关闭当前可关闭门槛，不能替代人工判断，也不能把候选直接写入全局知识库。
4. **Relationship Workspace**: 合盘/关系报告先确保双方单盘 manifest 和结构化 facts 已存在，再运行 `scripts/create_relationship_workspace.py --person-a-manifest <A_RUN>/case_manifest.json --person-b-manifest <B_RUN>/case_manifest.json ...` 创建外部 relationship run；脚本会生成 run-local relationship facts、知识上下文、复盘 intake，以及 rich/concise/mobile 的下一步 validate/package 命令。不要在旧合盘稿上直接续写，也不要跳过 relationship facts。relationship facts 必须包含 `relationship_mode` 和 `relationship_life_domains`，其中 `relationship_mode` 记录关系状态是否支持恋爱/私密语言，`relationship_life_domains` 覆盖事业/合作、家庭/生活承载、财富/资源投入、健康/精力照顾、亲近/私密边界五个现实专题；事实档案必须包含“合盘事实复查档案”“现实专题交集事实”“写作约束”。合盘正文交付前必须运行 `scripts/validate_relationship_report.py`；它会同时检查事实锚点、第三人称、章节主题锚点、标题口吻、重复段落、找茬感、正向牵引与张力配平、亲近边界和结尾收束。合盘 rich 固定的是 22 个章节主题，不是固定同一套“强牵引”评级；冒号后的金句必须按本盘事实改写。问题/风险/虽然但是式标题、露骨亲密细节、具体亲密频率推断或压力词压过关系价值，都应先改稿再打包；身体吸引、调情、私密生活只在 `relationship_mode.romantic_language_supported=true` 时写，合作、朋友、同事或未知关系只写亲近感、信任边界和互动距离。
5. **Team Career Synastry**: 三人及以上事业合作、合伙创业或组织关键人协同分析，先按 `service/multi-person-career-synastry-sop.md` 收口流程：每个人有单盘 facts，每两个人有 relationship facts，团队总评另建外部 team run，集中保存 `team-source-summary.json`、现实角色校准、城市商业判断和流年流月窗口。正文使用 `templates/team-career-synastry-template.md`；默认商业判断优先、命理开运辅助，不把双人 relationship 稿直接扩写成多人结论，不在读者正文写“你确认自己”“这一点与盘面吻合”“前稿判断相符”等主观确认句。新增成员时只补新增成员的单盘 facts 和其与既有成员的 pair relationship facts，再更新团队矩阵和交付版本。
6. **Fengshui / Direction**: 用户关心城市、方位、办公位置、居住环境或开运辅助时，`build_knowledge_context.py` 需要加入 `--module fengshui` 并读取 `knowledge/fengshui/README.md`。方位和空间建议只作低风险辅助：没有现场勘测、罗盘坐向、户型图和长期反馈时，不做传统风水强断，不承诺“换方向必发财”或“摆物必转运”。城市判断仍然商业和生活条件优先，命理象意只作补充。
7. **Source Liveness**: 只有当本次新增、复核或晋升联网来源时，运行 `scripts/check_source_urls.py --type classical_text --evidence-mode online_public_entry --output <RUN_DIR>/runtime/source_liveness.json --json`；核验快照必须留在外部 run，不写回项目仓库。随后运行 `scripts/audit_source_documentation.py`，确保 source-register、source-index 和人读来源文档一致。
8. **Calculate**: 调用 `scripts/xuanxue_console.py`。如果用户要求综合分析，分别跑对应模块并合并 JSON 证据。
9. **Interpret**: 读取 `references/interpretation-guide.md`、`knowledge/source-index.md`、`knowledge/rules/inference-contract.md`、`<RUN_DIR>/runtime/knowledge_context.json` 和对应体系规则卡，按“证据约束下的锋利判断”输出：证据同向时先给明确结论、强弱和排除项，再给证据、边界和校准问题；证据薄时说明降级原因。
10. **Follow-up**: 用户对已交付报告追加问题时，先运行 `scripts/create_followup_context.py --manifest <RUN_DIR>/case_manifest.json --question "<追问>"`，生成 `<RUN_DIR>/runtime/followups/*.json` 和 `<RUN_DIR>/calibration/dialogue/*.md`。回答前必须读取其中的 `facts_json`、`knowledge_context` 和 `required_knowledge_files`；旧长文只能当表达上下文，不能从旧文章单独推新结论。脚本会按已存在 facts 和追问关键词推断模块：多人事业 run 会读取 `team_source_summary`、`team_flow_timing_json` 和两两 relationship facts；方位、风水、城市、工位、居住或开运追问会要求 `fengshui` knowledge module。合盘追问必须有 `relationship` knowledge module，并读取合盘模板、`build_relationship_facts.py` 与 `validate_relationship_report.py` 等合盘专属上下文；事业、家庭、财富、精力或亲近/私密问题必须先读 `relationship_mode` 与 `relationship_life_domains` 的 `allowed_writing`、`do_not_infer` 和 `writing_boundary`。否则先重建 knowledge context / relationship facts，不降级成单盘追问。回答后如用户反馈“太中庸、太冲、像旧稿”，先写回 dialogue note，再决定是否生成去隐私候选复盘。
11. **Calibrate**: 问 2-4 个已经发生或可验证的问题，用用户反馈修正解读，不改脚本事实。
12. **Retrospect**: 交付或校准后，如用户给出可沉淀反馈，先按 `<RUN_DIR>/calibration/retrospective-intake.md` 整理去隐私证据，再用 `scripts/create_case_retrospective_candidate.py` 在外部 run 目录生成候选复盘；复盘必须有 `domains`，说明它覆盖 `bazi`、`ziwei`、`western`、`liuyao`、`relationship`、`team_career`、`fengshui`、`writing` 等哪个知识域。没有人工确认前不得写入 `knowledge/case-retrospectives/`。`audit_knowledge_coverage.py` 的 `run_local_candidate_summary` 只提示外部 ready 候选和可关闭的未满足门槛，不计入 goal complete。人工批准后再用 `scripts/promote_case_retrospective.py` 晋升并审计。
13. **Longform**: 当用户需要“文章版”“小白版”“传播版”或“愿意读完的长文”时，保留结构化报告，同时按 `templates/longform-analysis-template.md` 另写纯文本 Markdown 长文；长文必须先有判断型摘要，再引用脚本事实解释命理、紫微、西占、过去校准、未来趋势和行动建议。默认写“读者丰富版”：18000-24000 字符，固定 16 个 H2 大章和必要 H3，像能直接发人的文章，不像流程报告。丰富版是默认主交付，不能因为输入只含八字/流盘截图、缺紫微或缺西占而跳过；资料不足时写“单体系丰富版”或“可用体系丰富版”，把缺失模块放进边界和校准问题。只有用户明确说只要简洁版/短版，或没有任何可用结构化 facts，才停止丰富版。第 01 章要先下有记忆点的判断，再写现实场景、核心矛盾、证据预告和付费价值；技术事实是论据，不是开篇主角。正文要多写白话和情景推演，至少 8 处明确写出“白话场景”或“情景推演”；事业、财富、爱情、健康/精力、人际合作、学习成长都要写表现、误读、风险和做法。正文不要灌脚本路径、JSON 路径、坐标来源、执行命令或内部验收说明；这些放进 manifest / final delivery。出生分钟默认按不精确处理；除非用户明确说来自出生证明/医院记录，否则先运行 `scripts/audit_birth_time_sensitivity.py`，正文只把稳定项写死，敏感项写成待校准。完成后用 `scripts/validate_longform_report.py --profile reader-rich` 和 `scripts/audit_longform_consistency.py --strict` 检查章节、事实、强断语和一致性；若近 1-2 份旧稿可用，再加 `--compare-recent 2 --current-run-dir <RUN_DIR>`，避免“敏感/边界/作品化/预算合同/恢复机制/别人误读”跨 case 复用成同一套话术。
14. **Concise**: 完整交付默认同时生成简洁版，除非用户明确只要丰富版。简洁版按 `templates/concise-report-template.md` 写，源稿放 `<RUN_DIR>/drafts/<case>-concise-report.md`，默认读者交付为 `<reader-title>简洁版.pdf` 和 `<reader-title>简洁版-手机阅读.html`；Markdown/DOCX 只作为源稿、编辑或按需导出。默认 5500-9000 字符，第二人称、付费报告口吻、少量专业锚点，覆盖关系/感情、事业、钱和未来三到五年；不使用“小红书”“情绪价值”“真实感增强”等内部讨论词，不暴露脚本路径、JSON 路径、命令、截图路径或内部验收说明。简洁版要有自然分布的加粗白话结论句，但正文重点只做 700 字重加粗，不加底纹、不换字体、不额外跳色。简洁版先用 `scripts/validate_longform_report.py --profile reader-concise` 检查长度、第二人称、核心专题和加粗结论，再用 `scripts/audit_longform_consistency.py` 非 strict 口径检查事实硬失败；strict 里 reader-rich 固定章节警告可作为模板差异保留。
15. **Relationship Concise**: 合盘完整交付默认必须补齐简洁版。合盘简洁版按 `templates/relationship-concise-template.md` 写，源稿放 `<RUN_DIR>/drafts/<case>-relationship-concise.md`，默认读者交付为 `<双方名>合盘简洁版.pdf` 和 `<双方名>合盘简洁版-手机阅读.html`；默认第三人称，适合双方都读，保留合盘评级、牵引互补、误读点、事业/家庭/财富/精力、未来阶段和双方收束建议。手机 HTML 使用 `relationship_concise_mobile_html`，不要覆盖 rich 合盘的 `relationship_mobile_html`；缺源稿、PDF 或手机阅读 HTML 都不能 finalize，Markdown/DOCX/ZIP 缺失不算默认交付失败。

## IO Boundary

- 项目仓库只放通用代码、模板、规则、知识库和服务文档。
- 输入放外部：`<EXTERNAL_ROOT>\inputs\<case_id>`。
- 运行和交付放外部：`<EXTERNAL_ROOT>\runs\<case_id>\<run_id>`。
- `<EXTERNAL_ROOT>` 优先读环境变量 `XUANXUE_RUNS_ROOT`，否则使用 `config/runtime_profile.json` 里的默认位置。
- 新 case 先运行 `python scripts/create_case_workspace.py --case-id <case_id> --reader-name <name>` 创建外部 workspace。
- 候选复盘固定放在 `<RUN_DIR>\retrospectives`；未人工批准前不得进入 `knowledge/case-retrospectives/`。
- 不在项目仓库内创建 `reports/`、`output/`、`inputs/`、`runs/`、`.playwright-cli/` 或交付 zip/docx/pdf/html。
- 开工和交付前运行 `python scripts/audit_project_hygiene.py`，确保没有 repo-local 产物泄漏。
- 新 case 前运行 `python scripts/audit_source_documentation.py` 和 `python scripts/audit_knowledge_base.py`，确保来源索引、来源说明、规则卡和晋升清单完整；不要让模型只凭记忆解释。

## Final Delivery

完整交付默认包含在外部 run 目录：

- `<RUN_DIR>/data/<case>-combo.json`: 机器可复用的结构化事实，后续复查优先读取，不重复推算。
- `<RUN_DIR>/data/<case>-facts.md`: 从 JSON 生成的人读事实复查档案，用来快速核对四柱、大运、流年、紫微、西占等关键字段。
- `<RUN_DIR>/drafts/<case>-longform.md`: 传播型纯文本长文，适合直接阅读或二次编辑。
- `<RUN_DIR>/delivery/<reader-title>-丰富版.pdf`: 默认丰富版 PDF，方便直接阅读和发送。
- `<RUN_DIR>/drafts/<case>-concise-report.md`: 简洁版源稿。
- `<RUN_DIR>/drafts/<case>-relationship-concise.md`: 合盘简洁版源稿；仅合盘 run 需要。
- `<RUN_DIR>/data/team-source-summary.json`: 多人事业合盘的团队级证据索引，记录成员单盘 manifest、两两 relationship run、现实角色校准、城市候选和流年流月窗口；仅 team run 需要。
- `<RUN_DIR>/drafts/<case>-team-career-synastry.md`: 多人事业合盘团队总评源稿；仅 team run 需要。
- `<RUN_DIR>/delivery/<reader-title>简洁版.pdf`: 默认简洁版 PDF，方便直接发送。
- `<RUN_DIR>/delivery/<reader-title>-丰富版-手机阅读.html`: 默认单盘丰富版阅读器，使用统一移动端阅读标准：暖纸、深字、少色、无框、无卡片，仿宋/宋体优先、单列滚动，适合微信/手机浏览器转发和复制文本；H1/H2 优先在冒号后自然分行，不在逗号处硬断，不用 `overflow-wrap: anywhere` 硬切中文词组，H2 两行同字号同色同字重，H3 也使用同一深色体系，不额外跳色，不制造多余字号层级。正文加粗只用 700 字重。单盘源稿某章漏标重点时，阅读器可每章最多补 1 处直白结论句加粗；加粗句必须短、直白、可扫读，分散到多个章节，不整段高亮，也不机械集中在每章开头；自动补重点优先选第二段以后或章节收束句，不抢每章第一段；不加底纹、荧光笔、色块或换字体；manifest key 使用 `rich_mobile_html`。
- `<RUN_DIR>/delivery/<reader-title>简洁版-手机阅读.html`: 默认单盘简洁版阅读器，沿用同一移动端阅读标准；manifest key 使用 `concise_mobile_html`。
- `<RUN_DIR>/delivery/<双方名>合盘简洁版.pdf` 和 `<RUN_DIR>/delivery/<双方名>合盘简洁版-手机阅读.html`: 默认合盘简洁版读者交付；源稿 manifest key 使用 `relationship_concise_source_markdown`，读者交付 keys 使用 `relationship_concise_pdf`、`relationship_concise_mobile_html`。
- `<RUN_DIR>/delivery/*.md|*.docx|*.zip`: 可选导出，只在编辑、归档或用户明确要求时使用，不作为默认读者交付标准。
- `<RUN_DIR>/retrospectives/*.candidate.json`: 去隐私候选复盘，只在人工批准后晋升为全局知识库。
- `<RUN_DIR>/calibration/dialogue/*.md`: 追加问题和读者反馈的人读复盘位，保存追问原文、回答口径和后续校准，不直接晋升知识库。
- `<RUN_DIR>/runtime/knowledge_context.json`: 本次必读知识文件、来源边界、blocker、复盘需求和建议 `target_artifacts` 清单。
- `<RUN_DIR>/calibration/retrospective-intake.md`: 交付后反馈收集清单、去隐私要求和候选复盘命令。
- `<RUN_DIR>/runtime/retrospective_intake.json`: 机器可读的复盘 intake 计划。
- `<RUN_DIR>/runtime/source_liveness.json`: 本次联网来源核验快照；只有新增、复核或晋升来源时需要。
- `<RUN_DIR>/data/*.json`: 八字、紫微、西占和 combo 结构化事实。
- `<RUN_DIR>/case_manifest.json`: 输入口径、执行命令、产物路径和验证结果。
- 验证结果：单元测试、长文 validator、DOCX/PDF 结构检查、manifest/facts 归档检查。

长文 validator 推荐带上事实 JSON：

```bash
python scripts/build_fact_archive.py <RUN_DIR>/data/<case>-combo.json --output <RUN_DIR>/data/<case>-facts.md --manifest <RUN_DIR>/case_manifest.json
python scripts/validate_longform_report.py <RUN_DIR>/drafts/<case>-longform.md --facts-json <RUN_DIR>/data/<case>-combo.json --profile reader-rich
python scripts/audit_longform_consistency.py <RUN_DIR>/drafts/<case>-longform.md --facts-json <RUN_DIR>/data/<case>-combo.json --strict
python scripts/validate_longform_report.py <RUN_DIR>/drafts/<case>-concise-report.md --facts-json <RUN_DIR>/data/<case>-combo.json --profile reader-concise
```

出生时间敏感性检查：

```bash
python scripts/audit_birth_time_sensitivity.py --solar 1991-08-15 --time 01:30 --gender 男 --birthplace 上海 --latitude 31.23 --longitude 121.47 --true-solar --as-of 2026-06-12 --output <RUN_DIR>/data/<case>-time-sensitivity.json
```

读者版打包推荐：

```bash
python scripts/package_reader_delivery.py <RUN_DIR>/drafts/<case>-longform.md --output-dir <RUN_DIR>/delivery --basename <reader-title>-丰富版 --avoid-locked
python scripts/package_reader_delivery.py <RUN_DIR>/drafts/<case>-concise-report.md --output-dir <RUN_DIR>/delivery --basename <reader-title>简洁版 --no-subtitle --avoid-locked
python scripts/package_mobile_html.py <RUN_DIR>/delivery/<reader-title>-丰富版.md --output <RUN_DIR>/delivery/<reader-title>-丰富版-手机阅读.html --manifest <RUN_DIR>/case_manifest.json --artifact-key rich_mobile_html
python scripts/package_mobile_html.py <RUN_DIR>/delivery/<reader-title>简洁版.md --output <RUN_DIR>/delivery/<reader-title>简洁版-手机阅读.html --manifest <RUN_DIR>/case_manifest.json --artifact-key concise_mobile_html
```

## Module Notes

- `bazi`: 使用 `lunar_python` 获取四柱、五行、十神、纳音、大运；支持经度近似真太阳时、节气边界、子时边界警告，以及按 `--as-of` 输出流年/流月/流日和近年流年序列。
- `ziwei`: 使用 `iztro_py` 获取十二宫、主星、四化、大限，并按 `--as-of` 自动粗定位当前大限。`hour-index` 遵循 `0=早子, 1=丑, ..., 11=亥, 12=晚子`。
- `western`: 使用 `ephem` 输出热带黄道行星星座；提供 `--latitude` 和 `--longitude` 时输出上升、下降、天顶、天底、整宫制和等宫制宫位参考；未提供出生地时，不计算上升、宫位和宫主星。
- `mbti`: 作为人格语言层，不要把 MBTI 当作命理证据；只用于行为偏好、沟通风格和动机画像。
- `liuyao`: 输出卦体、动爻、变卦、纳甲、六亲和六神骨架；完整用神、世应、卦宫流派差异需在解读中说明。
- `xiaoliuren`: 支持 `standard` / `offset` 两种轻量起法，适合短期问事，不适合替代六爻细断。
- `combo`: 合并可用模块为统一 schema；默认保存 JSON，HTML 仅作可选 debug 快照。
- `fengshui`: 方位、空间、城市和开运建议只作辅助；没有现场勘测、罗盘坐向、户型图和执行反馈时，只写低风险建议和校准问题。

## JSON Schema

每个命令都输出同一外层结构：

```json
{
  "schema_version": "0.2.0",
  "module": "bazi",
  "input": {},
  "facts": {},
  "warnings": [],
  "uncertainties": [],
  "interpretation_hints": [],
  "calibration_questions": [],
  "raw": {}
}
```

## References

- Read `references/source-notes.md` before changing calculation strategy or adding dependencies.
- Read `references/interpretation-guide.md` before producing user-facing analysis.
- Read `knowledge/source-index.md`, `knowledge/rules/inference-contract.md`, and the relevant domain rule cards before producing paid longform analysis.
- Network research may be used only for source acquisition and rule-card promotion; do not use random web pages directly inside a client report.
