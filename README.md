# Xuanxue Console Report Case

这个目录是 `xuanxue-console` 的项目仓库：只保留结构化排盘脚本、模板、规则、知识库和服务文档。客户输入、结构化 JSON、HTML、长文、DOCX/PDF/ZIP 等运行产物必须放在项目外部 workspace，避免串 case 和污染后续输出。

## Open Source Boundary

这个仓库可以公开分享，但不展示真实 case。

- 仓库内只保留通用代码、规则卡、模板、测试 fixture、服务 SOP 和去隐私机制复盘。
- 真实客户资料、出生信息、原始对话、报告正文、截图、PDF、HTML、ZIP 和 run-local JSON 不进入仓库。
- 去隐私复盘只保留可复用机制，不保留客户姓名、生日、城市、本机路径或交付原文。
- 传播展示图、报告截图和样例成果应放在单独的 showcase/export 目录或独立仓库中，发布前再人工确认隐私边界。

## Service Layer

如果要把这个流程作为付费服务交付，优先阅读：

- `service/README.md`: 服务产品形态、卖点和边界。
- `service/client-intake-form.md`: 客户资料收集表。
- `service/production-sop.md`: 从接单到打包的生产 SOP。
- `service/quality-gate.md`: 交付前质量闸门。
- `service/pricing-and-cost-model.md`: 报价、人工成本和模型成本拆分。
- `service/case-retrospective-2026-06-12.md`: 当前项目复盘和下一步优化。

商业交付新增一个推荐检查：用 `scripts/audit_case_isolation.py` 对比旧 case，防止相似命盘或模板写作造成串案。

## Knowledge Layer

本项目不让模型只凭记忆做专业解释。付费报告默认使用三层依据：

1. `<RUN_DIR>/data/*.json`: 结构化排盘事实。
2. `knowledge/`: 来源索引、规则卡、推断合同和写作规则。
3. `<RUN_DIR>/calibration` 或 retrospective: 客户反馈和去隐私校准。

核心文件：

- `knowledge/source-index.md`: 经典、现代资料、运行时依赖和项目规则的来源索引。
- `knowledge/rules/inference-contract.md`: 判断如何从事实和规则变成报告结论。
- `knowledge/rules/research-and-promotion.md`: 联网资料和案例复盘如何晋升为全局知识。
- `knowledge/completeness/retrospective-requirements.json`: 各知识域关闭复盘 blocker 前需要满足的最小人工批准复盘数量和状态。
- `knowledge/bazi/`: 八字结构、十神、地支关系和流年规则卡。
- `knowledge/ziwei/`: 紫微命身、宫位、星曜、四化和大限规则卡。
- `knowledge/western/`: 西占行星、相位、宫位和时间敏感边界。
- `knowledge/writing/reader-rich-report.md`: 付费读者版写作规则。

知识库审计：

```powershell
python scripts\audit_knowledge_base.py
```

## Legacy Deliverables

历史样例和旧 case 产物已迁移到外部 archive：

```text
%USERPROFILE%\Documents\xuanxue_console_runs\archive\repo_cleanup_20260612_194441
```

新 case 不再使用项目内 `reports/` 目录。

## Current Preferred Standard

后续新 case 默认采用“双读者版”标准：丰富版负责完整覆盖，简洁版负责快速阅读和直接发送。

1. 主文像能直接发人的长文，不像流程报告。
2. 第 01 章统一为“判断型摘要”：先下有记忆点的判断，再写现实场景、核心矛盾、证据预告和读者可执行价值；不要用截图、基准盘或出生资料列表开头。
3. 默认采用“证据约束下的锋利判断”：证据同向时先给明确结论和优先级，不把所有问题写成两边都可以；证据薄时才降级成倾向和校准问题。
4. 排盘事实必须来自 `<RUN_DIR>/data/*.json`，但正文不灌脚本路径、JSON 路径、坐标来源和执行命令。
5. 事实复查先看 `<RUN_DIR>/data/<case>-facts.md`，精确字段再回到 `<RUN_DIR>/data/<case>-combo.json`；不要为了复查再次手算或重跑。
6. 过程证据、坐标口径、验证命令、已知边界放进 `<RUN_DIR>/case_manifest.json` 和 `<RUN_DIR>/final-delivery.md`。
7. 长文目标长度 `18000-24000` 字符；低于 `18000` 默认不交付，除非用户明确要短版。
8. 正式 reader-rich 长文使用固定 16 个 H2 大章和必要 H3；每份至少 8 处“白话场景”或“情景推演”。
9. 资料缺紫微、西占、MBTI 或占事信息时，不跳过丰富版；改写成单体系/可用体系丰富版，并把缺失模块写成边界和校准问题。
10. 出生分钟默认按不精确处理；除非明确来自出生证明/医院记录，否则先跑 `scripts/audit_birth_time_sensitivity.py`，正文区分稳定项和敏感项。
11. 完整交付默认另写简洁版：`<RUN_DIR>/drafts/<case>-concise-report.md`，读者必交为 `<昵称>命盘简洁版.pdf` 和 `<昵称>命盘简洁版-手机阅读.html`；Markdown/DOCX 只作为源稿、编辑或按需导出。简洁版正文默认 5500-9000 字符，使用第二人称、少量专业锚点和更顺滑的阅读结构，不写内部过程词；草稿先用 `validate_longform_report.py --profile reader-concise` 验长度、第二人称、核心专题和加粗结论。
12. 完整交付默认同时生成 `*-手机阅读.html`。单盘丰富版和简洁版都使用同一套阅读器 UI 标准：单文件、移动端优先、暖纸、深字、少色、无框、无卡片、仿宋/宋体优先、可复制文本；H1/H2 优先在冒号后自然分行，不在逗号处硬断，不用 `overflow-wrap: anywhere` 硬切中文词组，H2 两行同字号同色同字重，H3 不额外跳色；正文重点只做 700 字重加粗，不加底纹和色块。加粗句必须短、直白、可扫读，分散到多个章节，不整段高亮，也不机械集中在每章开头；阅读器自动补重点时优先选第二段以后或章节收束句，不抢每章第一段。生成后必须回写 manifest，单盘丰富版使用 `rich_mobile_html`，单盘简洁版使用 `concise_mobile_html`，合盘 rich 手机版使用 `relationship_mobile_html`，合盘简洁手机版使用 `relationship_concise_mobile_html`。
13. 交付入口放在 `<RUN_DIR>/delivery/`，默认读者交付只认四类：`*-丰富版.pdf`、`*-丰富版-手机阅读.html`、`*简洁版.pdf`、`*简洁版-手机阅读.html`。Markdown/DOCX/ZIP 可以生成，但只作为内部源稿、编辑备份或用户明确要求时的附加导出，不列入默认对外交付。
14. 合盘 case 先用 `scripts\create_relationship_workspace.py` 从两个已完成单盘 manifest 建立外部 run，再写读者正文；不要在旧稿上直接改合盘，也不要跳过 run-local relationship facts。relationship facts 必须包含 `relationship_mode` 和 `relationship_life_domains`，前者记录关系状态是否支持恋爱/私密语言，后者覆盖事业/合作、家庭/生活承载、财富/资源投入、健康/精力照顾、亲近/私密边界五个现实专题；合盘事实档案必须包含“合盘事实复查档案”“现实专题交集事实”“写作约束”。脚本会同时给出 rich 合盘、合盘简洁版和手机阅读器的打包命令。

## Runtime Contract

- `scripts/case_manifest_contract.py` 是 runtime contract 层；`normalize_case_manifest.py`、`finalize_case.py` 和追问/复盘流程都应复用这里的 artifact/data 口径。
- `finalize_case.py` 默认按单盘 rich+concise 合同验收；合盘 run 必须由 `create_relationship_workspace.py` 在 manifest 的 `validation_expectations` 写入 `required_data`、`required_artifacts`、`longform_markers`、`fact_archive_markers` 和 `pdf_text_markers`，避免用单盘 `combo/concise` 规则误验合盘。
- `finalize_case.py --write-status` 会把 `finalize_failures`、`finalize_warnings`、`finalize_repair_commands` 和合盘 `relationship_concise` readiness 写回 manifest.status；合盘简洁版是默认交付，缺源稿、PDF 或手机阅读 HTML 会进入 `finalize_failures`，并给出对应的 validate/package/finalize 修复命令。Markdown/DOCX/ZIP 缺失不作为默认交付失败。
- 2026-07-31 后，新 run 必须写 canonical manifest keys；`artifact_aliases` 和 legacy manifest fallback 只保留给旧 run 修复，不再扩大。
- 质量闸门冻结：除非出现硬错误或用户明确批准，不再新增 gate 脚本；优先复用 `finalize_case.py`、`audit_longform_consistency.py`、`create_followup_context.py`、`create_retrospective_intake.py`。
- 知识库增长优先靠去隐私真实复盘：哪段准、哪段不准、为什么误读、怎么改。没有案例证据时，不新增通用写作规则。
- 追加问题和读者反馈先进入 run-local `calibration/dialogue`；只有去隐私、可复用、人工确认过的复盘候选才晋升到知识库。
- 长文 Markdown 渲染已拆到 `scripts/xuanxue_longform.py`，西占计算已拆到 `scripts/xuanxue_western.py`，runtime/workflow 测试已拆到 `scripts/test_xuanxue_runtime.py`，合盘测试已拆到 `scripts/test_xuanxue_relationship.py`，交付阅读器测试已拆到 `scripts/test_xuanxue_delivery.py`；后续再增长时，先拆 CLI、八字、紫微和剩余测试模块，不继续往主文件塞逻辑。

## IO Boundary

新 case 不再写入项目内 `reports/` 或 `output/`。

- 外部根目录：优先读 `XUANXUE_RUNS_ROOT`，否则使用 `config/runtime_profile.json` 的默认值。
- 输入：`<EXTERNAL_ROOT>\inputs\<case_id>`。
- 运行：`<EXTERNAL_ROOT>\runs\<case_id>\<run_id>`。
- 知识上下文：`<RUN_DIR>\runtime\knowledge_context.json`，包含本次必读知识、来源边界、completion blocker、复盘需求、复盘采集计划和建议 `target_artifacts`。
- 来源核验快照：`<RUN_DIR>\runtime\source_liveness.json`，只在新增或复核联网来源时生成。
- 结构化事实：`<RUN_DIR>\data\*.json`。
- 事实复查档案：`<RUN_DIR>\data\<case>-facts.md`，由 JSON 直接生成，方便后续复核而不重算。
- 长文草稿：`<RUN_DIR>\drafts\*.md`。
- 读者交付：`<RUN_DIR>\delivery\*.pdf` 和 `<RUN_DIR>\delivery\*-手机阅读.html`；`*.md|*.docx|*.zip` 只作为内部源稿、编辑备份或按需附加导出。
- 校准反馈：`<RUN_DIR>\calibration\*`。
- 追加问题对话复盘：`<RUN_DIR>\calibration\dialogue\*.md`，保存追问原文、回答前必读证据、回答口径和后续复盘位；原始对话不进入全局知识库。
- 复盘 intake：`<RUN_DIR>\calibration\retrospective-intake.md` 和 `<RUN_DIR>\runtime\retrospective_intake.json`；如果 run-local 已有 `approval_ready=true` 候选，intake 会同时输出批量 dry-run、人工批准后 promote、后置审计顺序，以及“最小人工审批建议”。这个建议只帮助判断先批哪几条最能关闭当前可关闭门槛，不会自动晋升。
- 去隐私候选复盘：`<RUN_DIR>\retrospectives\*.candidate.json`。

创建外部 workspace：

```powershell
python scripts\create_case_workspace.py --case-id <case_id> --reader-name <name>
```

创建合盘 workspace。两个单盘必须已经有各自的 `case_manifest.json` 和结构化 facts；脚本会在外部 run 中生成合盘 facts、知识上下文、复盘 intake 和下一步写作/打包命令：

```powershell
python scripts\create_relationship_workspace.py --case-id <relationship_case_id> --reader-name <甲与乙> --person-a-manifest <A_RUN>\case_manifest.json --person-b-manifest <B_RUN>\case_manifest.json --person-a-label <甲> --person-b-label <乙> --relationship-status <已知关系> --distance-status <已知距离状态>
```

合盘完整交付默认另写简洁版。源稿使用 `<RUN_DIR>\drafts\<case>-relationship-concise.md`，模板看 `templates\relationship-concise-template.md`；打包命令由 `<RUN_DIR>\runtime\relationship_workflow.json` 给出。manifest 里源稿 key 为 `relationship_concise_source_markdown`，默认读者交付 keys 为 `relationship_concise_pdf`、`relationship_concise_mobile_html`；Markdown/DOCX/ZIP 可作为按需导出写入 `relationship_concise_markdown`、`relationship_concise_docx`、`relationship_concise_zip`，但不列入默认验收。

合盘 run 的 `runtime\knowledge_context.json` 必须包含 `relationship` 模块。后续读者反馈如果指向合盘判断、合盘标题、双方配平、亲密/事业/家庭/财富/精力章节或关系阶段表达，候选复盘 domain 应写 `relationship`，target artifacts 优先落到 `templates\relationship-rich-template.md`、`templates\relationship-concise-template.md`、`scripts\build_relationship_facts.py`、`scripts\validate_relationship_report.py` 或 `scripts\create_relationship_workspace.py`，不要只归到通用 `writing`。

`scripts\validate_relationship_report.py` 不只校验合盘事实锚点，也会拦截缺失 `relationship_mode` / `relationship_life_domains` 的旧 facts、问题/风险/虽然但是式标题、露骨亲密细节和具体亲密频率推断；同时会检查正文的正向牵引、互补、值得经营等画像锚点是否足够，避免压力词压过关系价值。合盘 rich 固定的是 22 个章节主题锚点，不是固定“强牵引互补缘”这类案例评级；冒号后的金句必须按本盘事实改写。合盘可以写亲近温度，但身体吸引、调情和私密生活必须由 `relationship_mode.romantic_language_supported` 支持；合作、朋友、同事或未知关系只写亲近感、信任边界和互动距离。

合盘追问也必须保留这个边界。`scripts\create_followup_context.py` 会把 `relationship` facts 作为主事实层，同时要求 `knowledge_context` 包含 `relationship` 模块；缺少时应重建上下文，而不是用单盘 bazi/ziwei/western 规则直接回答。

生成本次 case 的知识上下文：

```powershell
python scripts\build_knowledge_context.py --manifest <RUN_DIR>\case_manifest.json --module combo
```

生成交付后反馈收集清单：

```powershell
python scripts\create_retrospective_intake.py --manifest <RUN_DIR>\case_manifest.json
```

处理追加问题前，先生成追问上下文，防止只根据旧文章自由发挥：

```powershell
python scripts\create_followup_context.py --manifest <RUN_DIR>\case_manifest.json --question "<追问原文>" --module combo
```

回答追问时必须读取生成的 `<RUN_DIR>\runtime\followups\*.json`，再按其中的 `facts_json`、`knowledge_context` 和 `required_knowledge_files` 回答。旧长文或简洁版只能作为表达上下文，不能单独作为事实依据。
脚本会同步写入 `<RUN_DIR>\calibration\dialogue\*.md`，用于记录追问、回答口径和后续“过软/过硬/像旧稿”的复盘，不把原始聊天直接晋升到知识库。

归一化 manifest 字段，避免旧别名导致人工看似完成但最终验收失败：

```powershell
python scripts\normalize_case_manifest.py --manifest <RUN_DIR>\case_manifest.json --write
```

如果本次新增、复核或晋升联网典籍来源，把核验结果写到外部 run，不写回项目仓库；典籍入口进入 `source-register` 后，还要晋升到对应规则卡才能用于报告判断：

```powershell
python scripts\check_source_urls.py --type classical_text --evidence-mode online_public_entry --output <RUN_DIR>\runtime\source_liveness.json --json
```

项目卫生检查：

```powershell
python scripts\audit_project_hygiene.py
python scripts\audit_source_register.py
python scripts\audit_source_documentation.py
python scripts\audit_knowledge_base.py
python scripts\audit_promotion_manifest.py
```

一键轻量验收：

```powershell
.\verify.cmd
```

推荐验收：

```powershell
python scripts\build_fact_archive.py <RUN_DIR>\data\<case>-combo.json --output <RUN_DIR>\data\<case>-facts.md --manifest <RUN_DIR>\case_manifest.json
python scripts\validate_longform_report.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --profile reader-rich
python scripts\audit_longform_consistency.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --strict
python scripts\audit_longform_consistency.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --strict --compare-recent 2 --current-run-dir <RUN_DIR>
python scripts\validate_longform_report.py <RUN_DIR>\drafts\<case>-concise-report.md --facts-json <RUN_DIR>\data\<case>-combo.json --profile reader-concise
python scripts\audit_longform_consistency.py <RUN_DIR>\drafts\<case>-concise-report.md --facts-json <RUN_DIR>\data\<case>-combo.json
python scripts\audit_birth_time_sensitivity.py --solar <yyyy-mm-dd> --time <hh:mm> --gender <男|女> --latitude <lat> --longitude <lng> --true-solar --output <RUN_DIR>\data\<case>-time-sensitivity.json
python scripts\package_reader_delivery.py <RUN_DIR>\drafts\<case>-longform.md --output-dir <RUN_DIR>\delivery --basename <读者文件名>-丰富版 --avoid-locked --json --manifest <RUN_DIR>\case_manifest.json --artifact-prefix rich
python scripts\package_reader_delivery.py <RUN_DIR>\drafts\<case>-concise-report.md --output-dir <RUN_DIR>\delivery --basename <读者文件名>简洁版 --no-subtitle --avoid-locked --json --manifest <RUN_DIR>\case_manifest.json --artifact-prefix concise
python scripts\package_mobile_html.py <RUN_DIR>\delivery\<读者文件名>-丰富版.md --output <RUN_DIR>\delivery\<读者文件名>-丰富版-手机阅读.html --manifest <RUN_DIR>\case_manifest.json --artifact-key rich_mobile_html
python scripts\package_mobile_html.py <RUN_DIR>\delivery\<读者文件名>简洁版.md --output <RUN_DIR>\delivery\<读者文件名>简洁版-手机阅读.html --manifest <RUN_DIR>\case_manifest.json --artifact-key concise_mobile_html
python scripts\normalize_case_manifest.py --manifest <RUN_DIR>\case_manifest.json --write
python scripts\finalize_case.py --manifest <RUN_DIR>\case_manifest.json --normalize-manifest --write-status
```

合盘 run 使用同一个 `finalize_case.py`，但验收项来自 relationship manifest；不要为了合盘新增临时 gate，也不要把单盘必需的 `combo`、`concise` 误当成合盘必交付。

交付后如有可沉淀反馈，先生成外部候选复盘，不要直接写入全局知识库：

```powershell
python scripts\create_case_retrospective_candidate.py --manifest <RUN_DIR>\case_manifest.json --slug reader-hook --title "去隐私复盘标题" --domain writing --evidence-summary "只写抽象证据" --target-artifact knowledge/writing/reader-rich-report.md
```

人工确认后再晋升：

```powershell
python scripts\promote_case_retrospective.py --candidate <RUN_DIR>\retrospectives\CR-YYYYMMDD-reader-hook.candidate.json --approved-by EDY
```

## Rebuild

安装计算依赖：

```powershell
python -m pip install -r scripts\requirements.txt
```

每个 case 都在外部 workspace 重新生成结构化数据，不在项目 README 固化任何出生资料：

```powershell
python scripts\create_case_workspace.py --case-id <case_id> --reader-name <name>
python scripts\build_knowledge_context.py --manifest <RUN_DIR>\case_manifest.json --module combo
python scripts\create_retrospective_intake.py --manifest <RUN_DIR>\case_manifest.json
python scripts\xuanxue_console.py bazi --solar <yyyy-mm-dd> --time <hh:mm> --gender <男|女> --birthplace <birthplace> --longitude <lng> --tz-offset 8 --true-solar --as-of <yyyy-mm-dd> --flow-window 10 > <RUN_DIR>\data\<case>-bazi.json
python scripts\xuanxue_console.py ziwei --solar <yyyy-mm-dd> --hour-index <0-12> --gender <男|女> --as-of <yyyy-mm-dd> > <RUN_DIR>\data\<case>-ziwei.json
python scripts\xuanxue_console.py western --solar <yyyy-mm-dd> --time <hh:mm> --tz-offset 8 --latitude <lat> --longitude <lng> > <RUN_DIR>\data\<case>-western.json
python scripts\xuanxue_console.py combo --solar <yyyy-mm-dd> --time <hh:mm> --gender <男|女> --birthplace <birthplace> --longitude <lng> --tz-offset 8 --true-solar --hour-index <0-12> --as-of <yyyy-mm-dd> --flow-window 10 --western --latitude <lat> > <RUN_DIR>\data\<case>-combo.json
python scripts\build_fact_archive.py <RUN_DIR>\data\<case>-combo.json --output <RUN_DIR>\data\<case>-facts.md --manifest <RUN_DIR>\case_manifest.json
```

合盘重建不沿用旧合盘稿，先从两个单盘 manifest 新建 relationship run：

```powershell
python scripts\create_relationship_workspace.py --case-id <relationship_case_id> --reader-name <甲与乙> --person-a-manifest <A_RUN>\case_manifest.json --person-b-manifest <B_RUN>\case_manifest.json --person-a-label <甲> --person-b-label <乙> --relationship-status <已知关系> --distance-status <已知距离状态>
```

旧样例若需要重新导出 PDF，请先在外部 workspace 中指定 `<RUN_DIR>`，不要写回项目仓库：

```powershell
python scripts\export_longform_documents.py <RUN_DIR>\<case>-longform.md --docx <RUN_DIR>\delivery\<case>-longform.docx --pdf <RUN_DIR>\delivery\<case>-longform.pdf --subtitle 综合命盘长文报告
```

如果当前 Python 没有 `reportlab` / `python-docx` / `pypdf`，可使用 Codex bundled Python，路径见 Codex workspace dependencies。

## Validate

基础验收。历史样例已经迁移到外部 archive；新 case 以 `reader-rich` 标准和 `判断型摘要` 为准：

```powershell
python scripts\build_fact_archive.py <RUN_DIR>\data\<case>-combo.json --output <RUN_DIR>\data\<case>-facts.md --manifest <RUN_DIR>\case_manifest.json
python -m unittest discover -s scripts -p "test_*.py"
python scripts\validate_longform_report.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --profile reader-rich
python scripts\audit_longform_consistency.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --strict --compare-recent 2 --current-run-dir <RUN_DIR>
python scripts\normalize_case_manifest.py --manifest <RUN_DIR>\case_manifest.json --write
python scripts\finalize_case.py --manifest <RUN_DIR>\case_manifest.json --normalize-manifest --write-status
```

`finalize_case.py` 会强制检查 `<RUN_DIR>\runtime\knowledge_context.json`、`<RUN_DIR>\runtime\retrospective_intake.json` 和 `<RUN_DIR>\calibration\retrospective-intake.md`，防止交付绕过知识库读取和复盘闭环。
最终验收必须在 rich/concise 打包并回写 manifest 后运行；否则会因为缺少 `concise_markdown` / `concise_pdf` 等必交付产物失败。

如果近期有相似读者版，长文一致性审计必须加 `--compare-recent 2 --current-run-dir <RUN_DIR>` 自动对比最近正式 `*-longform.md` 旧稿；也可以额外用 `--compare-article <OLD_REPORT.md>` 指定旧稿。它不是检查事实是否相似，而是检查“安全感、边界、作品化、预算合同、恢复机制、别人误读”等通用解释按钮是否跨 case 重复使用。

排盘 HTML 已降级为可选 debug 快照；默认不做浏览器渲染验收。只有本次显式生成 HTML 时才运行：

```powershell
npx --yes --package @playwright/cli playwright-cli -s=bazi_report_render_http run-code --filename <RUN_DIR>\playwright\render-check.js
```

## Reuse Standard

后续新 case 复用这个流程时，固定三层产物：

1. `<RUN_DIR>/data/<case>-combo.json`: 机器可复用结构化事实。
2. `<RUN_DIR>/data/<case>-facts.md`: 人读事实复查档案，降低后续复核路径。
3. `<RUN_DIR>/drafts/<case>-longform.md`: 可编辑长文源稿。
4. `<RUN_DIR>/drafts/<case>-concise-report.md`: 可编辑简洁版源稿。
5. `<RUN_DIR>/drafts/<case>-relationship-concise.md`: 可编辑合盘简洁版源稿；仅合盘 run 需要。
6. `<RUN_DIR>/delivery/`: 给普通读者看的干净交付目录，默认必交为丰富 PDF、丰富手机阅读、简洁 PDF 和简洁手机阅读；合盘简洁版同样默认交付 PDF 与手机阅读器。手机阅读 HTML 必须回写 `rich_mobile_html`、`concise_mobile_html`、`relationship_mobile_html` 或 `relationship_concise_mobile_html`。
7. `<RUN_DIR>/delivery/*.md|*.docx|*.zip`: 可选导出，只在编辑、归档或用户明确要求时使用，不作为默认读者交付标准。
8. `<RUN_DIR>/calibration/retrospective-intake.md`: 交付后反馈收集清单。
9. `<RUN_DIR>/calibration/dialogue/*.md`: 追加问题和读者反馈的人读复盘位，默认由 `create_followup_context.py` 生成。
10. `<RUN_DIR>/retrospectives/`: 去隐私候选复盘，只在人工批准后晋升为全局知识。
11. `<RUN_DIR>/runtime/knowledge_context.json`: 本次 case 实际使用的知识上下文清单。
12. `<RUN_DIR>/runtime/retrospective_intake.json`: 机器可读的复盘 intake 计划。
13. `<RUN_DIR>/runtime/followups/*.json`: 追加问题上下文清单，列出追问回答前必须读取的 facts 和知识库文件。
14. `<RUN_DIR>/runtime/source_liveness.json`: 本次联网来源核验快照；没有新增或复核来源时可不生成。

所有解释必须从 `<RUN_DIR>/data/*.json` 读取事实，不让模型手算四柱、大运、星曜、行星落座或宫位。

本项目为传统文化与自我观察参考，不替代医疗、法律、投资或人生重大决策。
