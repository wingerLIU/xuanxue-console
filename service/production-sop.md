# 生产 SOP

## 0. 建 case

- `case_id` 用稳定英文短名：`<name>-<yyyy-mm-dd>`。
- 读者文件名用中文：`<昵称>命盘长文分析-丰富版`。
- 项目仓库不放客户输入和运行产物；先用 `scripts/create_case_workspace.py` 创建外部 workspace。
- 输入进入 `<EXTERNAL_ROOT>/inputs/<case_id>`；运行产物进入 `<EXTERNAL_ROOT>/runs/<case_id>/<run_id>`。
- 复盘候选进入 `<RUN_DIR>/retrospectives`，未人工确认前不进入全局知识库。
- 追加问题和读者反馈先进入 `<RUN_DIR>/calibration/dialogue`，作为 run-local 对话复盘；未经去隐私和人工确认，不进入全局知识库。
- 不覆盖旧 case；发现同名时新建新的 `run_id`。

```powershell
python -X utf8 scripts\create_case_workspace.py --case-id <case_id> --reader-name <昵称>
python -X utf8 scripts\build_knowledge_context.py --manifest <RUN_DIR>\case_manifest.json --module combo
python -X utf8 scripts\create_retrospective_intake.py --manifest <RUN_DIR>\case_manifest.json
python -X utf8 scripts\audit_project_hygiene.py
python -X utf8 scripts\audit_source_register.py
python -X utf8 scripts\audit_source_documentation.py
python -X utf8 scripts\audit_knowledge_base.py
```

`knowledge_context.json` 不是形式文件，结构由 `schemas/knowledge_context.schema.json` 约束。开写前要看其中的 `knowledge_files`、`source_entries`、`goal_completion_blockers`、`retrospective_requirements`、`retrospective_collection_plan` 和 `suggested_target_artifacts`。`retrospective_intake.json` 必须保留机器可读 `domain_question_bank`，结构由 `schemas/retrospective_intake.schema.json` 约束，让后续工具能按未满足领域追问，而不是只读旧报告正文猜测。`retrospective-intake.md` 是交付后反馈收集清单，优先按它收集可去隐私复盘证据，并把新典籍或客户反馈落到明确规则卡。

运行 contract 以 `scripts/case_manifest_contract.py` 为准。除非出现硬错误或用户明确批准，不新增 gate 脚本；先复用 `finalize_case.py`、`audit_longform_consistency.py`、`create_followup_context.py` 和 `create_retrospective_intake.py`。2026-07-31 后，新 run 不再依赖 legacy artifact alias，旧别名只用于修复历史 run。

如本次新增、复核或晋升联网典籍来源，同时生成外部来源核验快照：

```powershell
python -X utf8 scripts\check_source_urls.py --type classical_text --evidence-mode online_public_entry --output <RUN_DIR>\runtime\source_liveness.json --json
```

## 1. 资料锁定

先从客户表或截图锁定：

- 公历/农历、日期、时间、性别。
- 出生地、现居地、时区。
- 是否启用真太阳时。
- MBTI 可选，只作行为语言，不作命理证据。
- 出生分钟默认不视为精确；除非客户明确说明来自出生证明、医院记录或其他可核验证据，否则按 B/C 级近似时间处理。

资料不确定时，在 manifest 和正文边界里说明，不要偷偷补成确定。

## 2. 依赖检查

```powershell
python -X utf8 scripts\xuanxue_console.py doctor
```

如果默认 Python 缺 `python-docx`、`reportlab` 或 `pypdf`，导出文档时使用 Codex bundled Python。

## 3. 结构化排盘

示例命令：

```powershell
python -X utf8 scripts\xuanxue_console.py bazi --solar <yyyy-mm-dd> --time <hh:mm> --gender <男|女> --name <name> --birthplace <birthplace> --longitude <lng> --tz-offset 8 --true-solar --as-of 2026-06-12 --flow-window 10 > <RUN_DIR>\data\<case>-bazi.json
python -X utf8 scripts\xuanxue_console.py ziwei --solar <yyyy-mm-dd> --hour-index <0-12> --gender <男|女> --as-of 2026-06-12 > <RUN_DIR>\data\<case>-ziwei.json
python -X utf8 scripts\xuanxue_console.py western --solar <yyyy-mm-dd> --time <hh:mm> --tz-offset 8 --latitude <lat> --longitude <lng> > <RUN_DIR>\data\<case>-western.json
python -X utf8 scripts\xuanxue_console.py mbti --type <MBTI> > <RUN_DIR>\data\<case>-mbti.json
python -X utf8 scripts\xuanxue_console.py combo --solar <yyyy-mm-dd> --time <hh:mm> --gender <男|女> --name <name> --birthplace <birthplace> --longitude <lng> --tz-offset 8 --true-solar --hour-index <0-12> --as-of 2026-06-12 --flow-window 10 --western --latitude <lat> --mbti-type <MBTI> > <RUN_DIR>\data\<case>-combo.json
python -X utf8 scripts\build_fact_archive.py <RUN_DIR>\data\<case>-combo.json --output <RUN_DIR>\data\<case>-facts.md --manifest <RUN_DIR>\case_manifest.json
```

关键要求：排盘事实只从 JSON 读，不手算四柱、大运、星曜、行星落座或宫位。
事实复查优先看 `<RUN_DIR>\data\<case>-facts.md`，它由 JSON 直接生成，只作为内部复核索引；需要精确字段时回到 `<RUN_DIR>\data\<case>-combo.json`，不重复推算。

## 3.1 知识库读取

正式解读前至少读取：

- `<RUN_DIR>/runtime/knowledge_context.json`
- `knowledge/source-index.md`
- `knowledge/rules/inference-contract.md`
- `knowledge/bazi/foundations.md`、`knowledge/bazi/ten-gods.md`、`knowledge/bazi/structure-and-flow.md`
- `knowledge/ziwei/foundations.md`、`knowledge/ziwei/palaces-stars-four-transformations.md`
- `knowledge/western/foundations.md`、`knowledge/western/planets-aspects-houses.md`
- 如使用 MBTI：`knowledge/mbti/behavior-language.md`
- 如使用六爻：`knowledge/liuyao/question-reading.md`
- 如使用小六壬：`knowledge/xiaoliuren/quick-timing.md`
- `knowledge/writing/reader-rich-report.md`
- `templates/concise-report-template.md`

联网资料不得直接写进报告；必须先走 `knowledge/rules/research-and-promotion.md` 的晋升流程。

## 3.2 追加问题上下文

读者交付后提出追加问题时，不要只围绕旧长文延伸。先生成 run-local 追问上下文：

```powershell
python -X utf8 scripts\create_followup_context.py --manifest <RUN_DIR>\case_manifest.json --question "<追问原文>"
```

回答前读取生成的 `<RUN_DIR>\runtime\followups\*.json`，并逐项读取其中的 `facts_json`、`knowledge_context` 和 `required_knowledge_files`。旧报告正文只作为表达上下文，不能单独作为新结论来源。
脚本会按已有 facts 和追问关键词推断模块：单盘会回到 combo/module facts，多人事业 run 会带出 `team_source_summary`、`team_flow_timing_json` 和两两 relationship facts；方位、风水、城市、工位、居住或开运追问会要求 `fengshui` knowledge module。如果脚本提示 `knowledge_context missing requested module: fengshui` 或 `team_career`，先重跑 `build_knowledge_context.py` 补模块，不要绕过上下文直接答。
脚本会同步生成 `<RUN_DIR>\calibration\dialogue\*.md`，用于记录追问原文、必读证据、回答口径和后续复盘；回答后如用户反馈“太中庸、太冲、像旧稿”，先写回这份 note，再决定是否生成去隐私候选复盘。

追问回答的结构固定为：

- 先给明确结论：这个问题更像什么，不像什么；不要先铺流程。
- 标出判断级别：强 / 中 / 弱。证据够就直接排优先级，证据不够就说明为什么降级。
- 再说明这次追问主要落在哪些证据层：`calculated_fact`、`classical_rule`、`modern_synthesis`、`case_calibration` 或 `practical_advice`。
- 最后给边界和校准：哪些是命盘事实支持的，哪些只是现实建议，哪些需要后续反馈确认。
- 如果追问是新的具体事项或短期时机，不强行从本命盘旧正文推断；改为补问六爻/小六壬所需的问题、起卦方式和时间。

## 3.3 时间敏感性检查

默认出生分钟不精确，所以新 case 原则上都跑一次时间敏感性检查；当时间靠近时辰边界、真太阳时校正可能跨时辰，或西占上升/天顶对报告很关键时，必须重点写入正文第 03/04 章：

```powershell
python -X utf8 scripts\audit_birth_time_sensitivity.py --solar <yyyy-mm-dd> --time <hh:mm> --gender <男|女> --birthplace <birthplace> --latitude <lat> --longitude <lng> --tz-offset 8 --true-solar --as-of 2026-06-12 --output <RUN_DIR>\data\<case>-time-sensitivity.json
```

如果敏感性检查显示八字四柱、紫微命身或西占上升/天顶变化，正文第 03/04 章必须写清楚：稳定项正常解释，敏感项只写倾向和校准问题。

## 3.4 流年、流月和流日时间建议

单盘或合盘里可以做时间相关建议，但必须分层：

- 大运：十年主题和长期能力建设。
- 流年：年度主题、准备方向、适合扩张还是收口。
- 流月：未来 3-18 个月的行动节奏，例如谈资源、定框架、发布、复盘、修正或观望。
- 流日：仅用于已经有明确事项后的短窗口，例如签约、会谈、发布、搬迁、面试；不能替代现实准备。

交付格式固定为：

```text
时间层级：
盘面触发：
适合动作：
前置条件：
避坑提醒：
复盘指标：
```

如果用户只问“什么时候发财/脱单/翻身”，先改问具体事项和现实进度；如果事项短、窗口近、需要判断成败或对方反馈，优先补六爻/小六壬资料，不从本命盘旧正文硬推。时间建议不承诺结果，只给节奏、准备和风险管理。

### flow_timing_report

当用户需要未来 30 天、60 天、两个月或指定起止日期的流月流日行动表，使用固定能力 `flow_timing_report`。它不是丰富版里的一个段落，而是单独交付的行动节奏 HTML。

推荐命令：

```powershell
python -X utf8 scripts\build_flow_timing_report.py --facts-json <RUN_DIR>\data\<case>-combo.json --start <yyyy-mm-dd> --days 45 --reader-name <昵称> --case-keyword <关键词1> --case-keyword <关键词2> --case-keyword <关键词3> --case-keyword <关键词4> --case-keyword <关键词5> --output-md <RUN_DIR>\drafts\<case>-flow-timing.md --output-html <RUN_DIR>\delivery\<昵称>-流月流日行动节奏.html --json-output <RUN_DIR>\data\<case>-flow-timing.json
python -X utf8 scripts\validate_flow_timing_report.py <RUN_DIR>\drafts\<case>-flow-timing.md --case-keyword <关键词1> --case-keyword <关键词2> --case-keyword <关键词3> --case-keyword <关键词4> --case-keyword <关键词5> --min-days 30
python -X utf8 scripts\validate_flow_timing_report.py <RUN_DIR>\delivery\<昵称>-流月流日行动节奏.html --case-keyword <关键词1> --case-keyword <关键词2> --case-keyword <关键词3> --case-keyword <关键词4> --case-keyword <关键词5> --min-days 30
```

报告必须先列本 case 指纹，再写每日动作。对 liujiang 这类项目经营场景，关键词应落到 OPC、Liujiang OS、Agent 项目包、团队训练、报价、合作、回款、ROI、对上汇报、不替别人兜底和小闭环试运行；其他人必须换成自己的真实场景。生成后如果每日表只剩“注意沟通、适合推进、谨慎合作”，直接判失败。

## 3.5 多人事业合盘

三人及以上的事业合作、合伙创业或组织关键人协同分析，使用 `service/multi-person-career-synastry-sop.md`，不要把双人 relationship 稿直接扩写成多人结论。

核心流程：

- 每个人先完成单盘 facts。
- 每两个人生成独立 relationship run，三人团队需要 3 组 pair，四人团队需要 6 组 pair。
- 团队总评另建团队级外部 run，集中保存 `team-source-summary.json`、现实角色校准、城市商业判断和流年流月窗口。
- 正文使用 `templates/team-career-synastry-template.md`，默认面向事业协作，不写恋爱/私密语言。
- 城市、合伙、投入和迁移判断必须商业优先、命理开运辅助；如果两者冲突，以商业条件为主。
- 读者正文不得出现“你确认自己……”“这一点与盘面吻合”“前稿判断相符”等主观确认句。
- 新增成员时只补新增成员的单盘 facts 和其与既有成员的 pair relationship facts，再更新团队矩阵和交付版本。

## 3.6 方位、空间和开运辅助

只有当用户明确关心城市、方位、办公位置、居住环境或开运辅助时，才在 knowledge context 里加入 `fengshui`：

```powershell
python -X utf8 scripts\build_knowledge_context.py --manifest <RUN_DIR>\case_manifest.json --module combo --module fengshui
python -X utf8 scripts\build_knowledge_context.py --manifest <TEAM_RUN_DIR>\case_manifest.json --module team_career --module relationship --module fengshui --module writing
```

读取 `knowledge/fengshui/README.md` 后再写建议。没有现场勘测、罗盘坐向、户型图和长期执行反馈时，只能写低风险、可撤回、可观察的空间建议；不能写“必发财”“必破财”“某方一定有灾”这类传统风水强断。城市选择仍然先看客户、成本、行业、家庭生活和现金流，命理象意只作辅助。

风水方位交付必须留下可复盘口径：本次证据等级、建议类型、低成本试法、观察周期和可观察指标。读者后续反馈时，先用 `create_followup_context.py` 生成追问上下文，再把反馈写入 `<RUN_DIR>\calibration\dialogue\*.md`。只有反馈已经去隐私、能说明执行变化和降级边界，并经过人工确认，才用 `create_case_retrospective_candidate.py --domain fengshui --target-artifact knowledge/fengshui/README.md` 生成候选复盘；不要把单次“感觉有效”晋升成通用风水规则。

## 4. 长文写作

先生成脚本草稿作为证据：

```powershell
python -X utf8 scripts\xuanxue_console.py longform --input-json <RUN_DIR>\data\<case>-combo.json --output <RUN_DIR>\drafts\<case>-longform-draft.md --title <昵称>命盘长文初稿
```

正式读者版人工重写或深度润色，保存为：

```text
<RUN_DIR>/drafts/<case>-longform.md
```

丰富版是完整流程的默认测试目标，不因为资料只含八字、只含流盘截图、缺紫微或缺西占而自动跳过。资料不足时，写“单体系丰富版”或“可用体系丰富版”，把缺失模块放进边界和校准问题；只有用户明确说“只要简洁版/短版”，或没有任何可用结构化 facts，才停止丰富版。

正文要求：

- 有 `判断型摘要`、`先看结论`、`基础排盘信息`、`现实关系全景`、`过去几年`、`未来几年`、`事业`、`财富`、`爱情`、`健康`、`人际合作`、`学习成长`、`校准问题`。
- 第 01 章先写论点，不先写资料：用“直接判断 -> 现实场景 -> 为什么重要 -> 技术证据预告 -> 读者怎么用”的结构，让客户先看到价值，再看到论据。
- 开写前先列 6-10 个本 case 指纹：四柱/月令/当前大运、紫微命身/四化、西占个人行星/相位、时间敏感项、已知现实问题，以及最不像上一份报告的地方。第 01/02 章至少落入 5 个指纹；“需要被理解、边界感、安全感、不适合被消耗、不太会表达、稳定地爱”不能脱离证据做主轴。
- 采用“证据约束下的锋利判断”：客观不是中庸；证据同向时直接写强弱、优先级和排除项，证据不足时才降级为倾向或校准问题。
- 18000-24000 字符为默认目标；低于 18000 默认不交付，除非用户明确要短版。
- 必须使用 `templates/longform-analysis-template.md` 的固定 16 个 H2 大章和必要 H3，不自由增删或改名。
- 每个核心判断都要落到现实场景；至少 8 处明确写出“白话场景”或“情景推演”。
- 事业、财富、爱情、健康/精力、人际合作、学习成长六个专题都要写“本人会怎样表现 / 别人可能会怎样误读 / 风险在于什么 / 更好的做法是什么”。
- 少写车轱辘话；每段至少新增一个判断、证据、场景、风险、行动或校准入口。
- 不写脚本路径、JSON 路径、执行命令、坐标来源和内部验收说明。

## 5. 验收

```powershell
python -X utf8 scripts\validate_longform_report.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --profile reader-rich
python -X utf8 scripts\audit_longform_consistency.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --strict
python -X utf8 scripts\audit_longform_consistency.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --strict --compare-recent 2 --current-run-dir <RUN_DIR>
python -X utf8 scripts\audit_longform_consistency.py <RUN_DIR>\drafts\<case>-concise-report.md --facts-json <RUN_DIR>\data\<case>-combo.json
python -X utf8 scripts\audit_knowledge_base.py
python -X utf8 -m py_compile scripts\audit_birth_time_sensitivity.py
python -X utf8 scripts\audit_case_isolation.py <RUN_DIR>\drafts\<case>-longform.md --facts-json <RUN_DIR>\data\<case>-combo.json --other-facts-json <OLD_RUN_DIR>\data\<old-case>-combo.json
python -m unittest discover -s scripts -p "test_*.py"
```

若有多个旧 case，就重复传入多个 `--other-facts-json`。

如果读者版和最近旧稿体感相似，先用 `audit_longform_consistency.py --compare-recent 2 --current-run-dir <RUN_DIR>` 自动对比正式旧稿；也可手动补 `--compare-article <OLD_REPORT.md>`。它抓的是跨报告表达漂移：同一批通用主题簇反复解释不同命盘。strict 失败时，优先重写第 01/02 章和六大专题建议，不要只替换姓名和事实锚点。

## 6. 打包

```powershell
python -X utf8 scripts\package_reader_delivery.py <RUN_DIR>\drafts\<case>-longform.md --output-dir <RUN_DIR>\delivery --basename <昵称>命盘长文分析-丰富版 --avoid-locked --json --manifest <RUN_DIR>\case_manifest.json --artifact-prefix rich
python -X utf8 scripts\package_reader_delivery.py <RUN_DIR>\drafts\<case>-concise-report.md --output-dir <RUN_DIR>\delivery --basename <昵称>命盘简洁版 --subtitle 星命人格简洁版报告 --avoid-locked --json --manifest <RUN_DIR>\case_manifest.json --artifact-prefix concise
python -X utf8 scripts\package_mobile_html.py <RUN_DIR>\delivery\<昵称>命盘长文分析-丰富版.md --output <RUN_DIR>\delivery\<昵称>命盘长文分析-丰富版-手机阅读.html --manifest <RUN_DIR>\case_manifest.json --artifact-key rich_mobile_html
python -X utf8 scripts\package_mobile_html.py <RUN_DIR>\delivery\<昵称>命盘简洁版.md --output <RUN_DIR>\delivery\<昵称>命盘简洁版-手机阅读.html --manifest <RUN_DIR>\case_manifest.json --artifact-key concise_mobile_html
```

手机阅读 HTML 默认按暖黄纸感、仿宋/宋体优先、单列滚动处理；它不是网页活动页，不加粘性目录、进度条或视觉组件。单盘完整交付同时生成丰富版和简洁版两个手机阅读入口。

如果默认 Python 缺导出依赖，改用 bundled Python。

## 7. manifest 与最终验收

每个 case 必须有：

- `<RUN_DIR>/case_manifest.json`
- `<RUN_DIR>/final-delivery.md`
- `<RUN_DIR>/data/<case>-combo.json`
- `<RUN_DIR>/data/<case>-facts.md`
- `<RUN_DIR>/delivery/<昵称>命盘长文分析-丰富版.pdf`
- `<RUN_DIR>/delivery/<昵称>命盘长文分析-丰富版-手机阅读.html`
- `<RUN_DIR>/delivery/<昵称>命盘简洁版.pdf`
- `<RUN_DIR>/delivery/<昵称>命盘简洁版-手机阅读.html`
- `<RUN_DIR>/runtime/knowledge_context.json`
- `<RUN_DIR>/runtime/retrospective_intake.json`
- `<RUN_DIR>/calibration/retrospective-intake.md`
- 如本次处理追加问题：`<RUN_DIR>/calibration/dialogue/*.md`
- 如本次使用联网来源晋升：`<RUN_DIR>/runtime/source_liveness.json`

最终验收：

```powershell
python -X utf8 scripts\normalize_case_manifest.py --manifest <RUN_DIR>\case_manifest.json --write
python -X utf8 scripts\finalize_case.py --manifest <RUN_DIR>\case_manifest.json --min-longform-chars 18000 --normalize-manifest --write-status
```

`finalize_case.py` 会把 `knowledge_context.json`、`retrospective_intake.json` 和 `retrospective-intake.md` 当成硬门槛；缺失时不允许最终验收通过。
最终 `status.stage` 只以 `finalize_case.py --write-status` 写入为准；不要手工把未通过验收的 run 标成 `delivered` 或 `finalized`。

如果 `pypdf` 只在 bundled Python 里可用，用 bundled Python 跑最终验收。

## 8. 交付后复盘

只有当用户给出可沉淀反馈、校准结果或明确修改意见时，才生成候选复盘。候选复盘保存到外部 run 目录：

复盘优先收集真实反馈：哪段准、哪段不准、为什么误读、应该怎么改。没有去隐私案例证据时，不把感觉直接晋升成新规则；先记录为待验证假设或反例。

先查看：

```powershell
Get-Content -Raw -Encoding UTF8 <RUN_DIR>\calibration\retrospective-intake.md
```

```powershell
python -X utf8 scripts\create_case_retrospective_candidate.py --manifest <RUN_DIR>\case_manifest.json --slug reader-hook --title "去隐私复盘标题" --domain writing --evidence-summary "只写抽象证据" --target-artifact knowledge/writing/reader-rich-report.md
```

没有人工批准前，候选复盘不得复制进 `knowledge/case-retrospectives/`。人工确认后：

```powershell
python -X utf8 scripts\promote_case_retrospective.py --candidate <RUN_DIR>\retrospectives\CR-YYYYMMDD-reader-hook.candidate.json --approved-by EDY
```

晋升后必须再次运行：

```powershell
python -X utf8 scripts\audit_case_retrospectives.py
python -X utf8 scripts\audit_knowledge_coverage.py
```

`audit_knowledge_coverage.py` 会输出 `run_local_candidate_summary`，用于提示外部 run 里已有的 ready 候选、blocked 候选修复计划和它们可能关闭的未满足门槛。`create_retrospective_intake.py` 也会把同样的 blocked 修复优先级写入 run-local `run_local_repair_priority_queue`，方便先补最能推进全局缺口的真实反馈。这个摘要只是人工审批队列，不把候选当成 curated 复盘，也不关闭 `goal_complete`。
