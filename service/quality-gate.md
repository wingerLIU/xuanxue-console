# 质量闸门

## 闸门冻结

- 除非出现硬错误或用户明确批准，不新增 gate 脚本。
- runtime contract 统一由 `scripts/case_manifest_contract.py` 维护；最终验收复用 `finalize_case.py`，长文事实一致性复用 `audit_longform_consistency.py`，追加问题复用 `create_followup_context.py`，复盘采集复用 `create_retrospective_intake.py`。
- 2026-07-31 后，新 run 必须使用 canonical manifest keys；legacy artifact alias 只用于历史 run 修复。
- 新规则必须来自去隐私真实复盘或明确反例；没有案例证据时，只记录为待验证假设。

## 输入闸门

- 出生日期、时间、性别、出生地已锁定。
- 已创建外部 case workspace；客户输入位于 `<EXTERNAL_ROOT>/inputs/<case_id>`，运行产物位于 `<RUN_DIR>`。
- 项目仓库内不得出现客户截图、输入资料、结构化 JSON、HTML、PDF、DOCX、ZIP 或 run-local manifest。
- `scripts/audit_knowledge_base.py` 通过；知识来源、规则卡和晋升清单没有断链。
- 出生分钟默认按不精确处理；只有出生证明/医院记录等可核验证据才标 A 级。
- 正文和 manifest 都写明时间可信度等级；整点/半点时间默认按近似时间，不自动当成精确分钟。
- 真太阳时是否启用已说明。
- MBTI 只作为行为语言，不当命理证据。
- 截图或客户表路径只放 manifest，不放读者正文。
- `scripts/audit_project_hygiene.py` 通过。

## 计算闸门

- `doctor` 通过。
- Bazi、Ziwei、Western、MBTI、Combo JSON 均生成。
- `<RUN_DIR>/data/<case>-facts.md` 已由 `scripts/build_fact_archive.py` 从 combo JSON 生成，用于快速复核，不作为读者交付。
- 四柱、大运、紫微命宫、西占核心落座与截图或输入互相核对。
- 不由模型手算四柱、大运、星曜、宫位。

## 长文闸门

- 丰富版是默认主交付；不能因为只拿到八字/流盘截图、缺紫微或缺西占，就改成交付简洁版。
- 资料缺模块时，丰富版仍要覆盖可用 facts，并把缺失体系写成边界、待补资料或校准问题。
- 只有用户明确要求“只要简洁版/短版”，或本次没有任何可用结构化 facts，才允许跳过丰富版；否则 `finalize_case.py` 必须失败。
- reader-rich 固定 16 个 H2 大章和必要 H3 完整，顺序和标题必须一致。
- 长文核心判断能落到 `calculated_fact`、知识库规则卡、现代综合、校准问题或现实建议；不能只靠模型记忆。
- 第 01 章必须是“判断型摘要”：先给有记忆点的断言，再写现实场景、核心矛盾、证据预告和可执行价值；不得用截图说明、基准盘说明或出生资料列表开头。
- 默认采用“证据约束下的锋利判断”：证据同向时要直接给结论、强弱和排除项；不得为了显得客观把每个问题写成两边都可以。
- 读者版默认使用第二人称“你”；除非客户明确要求第三方视角，不用“他/她”作为全文主语。
- 正文不得出现“这一章不再解释”“客户可以执行”“下面每一条都对应”“前文的命盘结构”等交付方过程话。
- 长度不低于 18000 字符，默认目标 18000-24000 字符。
- 至少 8 处明确写出“白话场景”或“情景推演”。
- 每个核心判断有事实依据和现实场景。
- 每段应提供新信息，避免同一观点反复换词堆字。
- 事业、财富、爱情、健康/精力、人际合作、学习成长六个专题都包含“表现、误读、风险、做法”。
- `audit_longform_consistency.py --strict` 通过：硬事实与 JSON 一致，无强断语/高风险断语，过去年份和未来年份都有固定推演字段。
- 若近 1-2 份旧稿可用，`audit_longform_consistency.py --strict --compare-recent 2 --current-run-dir <RUN_DIR>` 通过；也可额外指定 `--compare-article <OLD_REPORT.md>`。若提示 `template drift`，说明报告在用同一组通用解释按钮，必须重写第 01/02 章和六大专题建议。
- `audit_birth_time_sensitivity.py` 默认已生成报告，正文第 03/04 章明确稳定项和敏感项。
- 过去几年按 `盘面触发 -> 现实倾向 -> 校准问题` 写。
- 未来几年写趋势和准备，不写绝对预言。
- 健康只写作息、压力、精力管理和就医意识。
- 财富只写预算、合同、回款、风险边界，不写投资承诺。
- 感情只写沟通、边界、节奏和现实安排。

## 串案闸门

- 对比至少 1-2 个最近旧 case，跑 `audit_case_isolation.py`。
- 手工检查旧 case 的四柱、当前大运、紫微命宫、西占太阳/月亮/上升/天顶是否混入。
- 如果两个 case 很像，最终交付说明里要能解释“为什么像”和“哪里不同”。

## 交付闸门

- 丰富版 PDF 和丰富版手机阅读器都存在，并且位于 `<RUN_DIR>/delivery`；简洁版不能替代丰富版。
- 简洁版 PDF 和简洁版手机阅读器默认也存在；除非用户明确只要丰富版，否则不得省略。
- 简洁版正文不出现“小红书”“情绪价值”“真实感增强”等内部讨论词，不出现脚本路径、JSON 路径、命令、截图路径或内部验收说明。
- 简洁版需通过 `audit_longform_consistency.py` 非 strict 口径；硬事实失败必须修复。
- 手机阅读 HTML 默认生成丰富版和简洁版两个入口，文件名分别对应 `*-丰富版-手机阅读.html` 与 `*简洁版-手机阅读.html`；必须包含移动端 viewport，采用暖黄纸感、仿宋/宋体优先的阅读字体、单列滚动，且不加载外部资源。
- PDF 页数大于 0，且能提取到预期中文标记。
- MD/DOCX/ZIP 如按需导出，只能包含读者可见文件，不包含 JSON、manifest、截图原路径或命令日志；它们不作为默认交付必检项。
- manifest 记录输入口径、命令、产物、验证结果和已知边界。
- manifest 记录 `artifacts.fact_archive_markdown` 和 `artifacts.data.combo`；`main_html` 只是可选 debug artifact，不是交付硬门槛。
- `scripts/audit_case_workspace.py --manifest <RUN_DIR>/case_manifest.json` 通过。
- `scripts/normalize_case_manifest.py --manifest <RUN_DIR>/case_manifest.json --write` 已运行，artifact 字段使用 canonical 命名。
- `finalize_case.py --write-status` 通过；`status.stage=finalized` 只能由该命令写入。

## 追加问题闸门

- 回答已交付报告的追加问题前，必须先运行 `scripts/create_followup_context.py --manifest <RUN_DIR>/case_manifest.json --question "<追问原文>"`。
- `<RUN_DIR>/runtime/followups/*.json` 必须 `passed=true`，并列出至少一个 `facts_json` 和一组 `required_knowledge_files`。
- `<RUN_DIR>/calibration/dialogue/*.md` 应同步存在，用于保存追问原文、必读证据、回答口径和后续复盘位。
- 追问回答不能只引用旧长文、简洁版或上一轮聊天；旧报告正文只能作为 `context_only` 的表达上下文。
- 追问回答先给明确结论和判断级别，再给证据层、边界和校准问题；证据不足时说明降级原因，而不是写成温吞中和。
- 新判断必须重新落到结构化 facts、知识库规则卡、现代综合、案例校准或现实建议之一；证据不足时写成倾向和校准问题。
- 如果追问变成新的具体事项、短期时机或决策问题，不从本命盘旧正文硬推；先补问六爻/小六壬所需信息或说明无法判断。

## 商业风险闸门

- 不预测死亡。
- 不诊断疾病。
- 不给投资买卖点。
- 不替客户做结婚、离婚、诉讼、辞职等重大决定。
- 不用恐吓话术引导复购。
- 不公开客户隐私；公开样例必须去标识化。
