# 2026-06-12 收口复盘

## 已验证能力

- 已能从截图或结构化输入生成 Bazi、Ziwei、Western、MBTI 的 JSON 事实。
- 已能生成 reader-rich 长文，并打包 PDF、手机阅读器；MD/DOCX/ZIP 只作为内部源稿、编辑或按需导出。
- 已有 `validate_longform_report.py` 检查章节、长度、事实和过程痕迹。
- 已有 `finalize_case.py` 检查 manifest、事实档案、长文、PDF、数据文件。
- 已补 `audit_case_isolation.py`，用于检查新报告是否混入旧 case 独有事实。

## 本轮暴露的问题

- 默认 Python 缺 `python-docx`，打包需要 fallback 到 Codex bundled Python。
- manifest 的精确 marker 一开始比正文更严格，导致最终验收卡在 `狮子27.73`、`金牛24.90`。
- 两个同类测试盘出现相近结构时，读者会自然感觉相似；以后必须主动解释相似原因和差异点。
- 排盘 HTML 偏后台 JSON 复核页，已降级为可选 debug；默认用 `data/<case>-combo.json` 和 `data/<case>-facts.md` 做事实复查。
- README 仍以旧样例为主，流程说明入口需要单独放到 `service/`。

## 已做优化

- 新增流程化文档：
  - `service/README.md`
  - `service/client-intake-form.md`
  - `service/production-sop.md`
  - `service/quality-gate.md`
  - `service/cost-accounting-notes.md`
- 新增串案检查脚本：
  - `scripts/audit_case_isolation.py`
- 明确输出风险边界：
  - 传统文化与自我观察参考。
  - 不替代医疗、法律、投资、婚恋决定。
  - 不用恐吓话术引导付费。

## 下一步建议

1. 已补 `normalize_case_manifest.py` 和 manifest artifact 合同；后续继续做 `case_id` 生成和更完整的 manifest scaffold。
2. 继续优化 `data/<case>-facts.md` 的事实复查密度，避免为了核对字段重跑排盘。
3. 增加 `service/sample-sales-copy.md`，沉淀微信介绍话术和朋友圈样例。
4. 记录每单真实耗时与返工原因，用 `price / human cost / compute` 三行核算判断利润。
5. 用 10-20 个样本内测：重点看客户最爱截图的段落、最常追问的问题、最容易引起误解的表述。

## 2026-06-13 追加收口

### 新增已验证能力

- 合盘已从“在旧稿上改”改为独立 workflow：先用两个单盘 manifest 建立 relationship run，再生成 `relationship` facts、事实复查档案、知识上下文和复盘 intake。
- 合盘 facts 现在必须包含 `relationship_mode` 和 `relationship_life_domains`；现实专题覆盖事业/合作、家庭/生活承载、财富/资源投入、健康/精力照顾、亲近/私密边界。
- 合盘 rich 报告不再固定某个案例评级；固定的是 22 个章节主题，冒号后的金句必须按本盘事实改写。
- 合盘追问已纳入专门上下文：`create_followup_context.py` 必须读取 relationship facts、relationship knowledge module、relationship mode 和 life domains，不能只靠旧文章继续发挥。
- 完整交付默认包含简洁版：单盘和合盘都保留源稿，但对外默认交付丰富 PDF、丰富手机阅读、简洁 PDF 和简洁手机阅读；MD/DOCX/ZIP 不再列为默认读者交付。
- 手机阅读器已统一为暖纸、深字、少色、无卡片、仿宋/宋体优先、单列滚动；标题在冒号后自然分行，不在逗号处硬断；正文重点只用 700 字重加粗，不加底纹或荧光笔。
- 阅读器自动补重点时只补短白话结论句，优先从第二段以后或章节收束句里选，不抢每章第一段。
- `finalize_case.py` 已能按 manifest 区分单盘和合盘验收：单盘验 rich、concise、两个手机 HTML；合盘验 relationship facts、合盘事实档案、rich 手机 HTML、合盘简洁版 PDF 和手机阅读器。
- `create_retrospective_intake.py` 已能列出 run-local 候选复盘、ready 状态、批量 dry-run/promote 命令、覆盖预览和最小人工审批建议。

### 当前已跑通的代表性 case

- 单盘：A/B 去标识化样例 run 均已有结构化 facts 和交付基础。
- 合盘：去标识化 relationship run 已完成 rich、合盘简洁版、手机阅读 HTML 和 finalize。
- 当前合盘 run 的 4 个 run-local 候选复盘均可 dry-run promote；其中最小审批建议是先批 2 条，可关闭 `writing`、`relationship` 和全局 `ANY` 复盘门槛。

### 仍然未完成的硬门槛

- 全局 `knowledge/case-retrospectives/` 仍为 0 个 curated retrospective。
- `audit_knowledge_coverage.py` 因此仍输出 `goal_complete=false`。
- 这不是代码失败，而是治理边界：只有去隐私、人工确认过的候选复盘才能晋升；未获批准前不能用候选复盘假装完成。

### 后续真正要做的事

1. 人工复核当前合盘 run 的 4 个候选复盘；如果认可，先批准最小集合里的 2 条，再跑 `promote_case_retrospective.py`、`audit_case_retrospectives.py` 和 `audit_knowledge_coverage.py`。
2. 继续收集真实读者反馈，尤其是八字、紫微、西占、六爻各自至少 2 条 curated retrospective；否则知识覆盖审计不会关闭这些域。
3. 新 case 交付后不要只看报告是否好看，还要问“哪段准、哪段不准、为什么误读、怎么改”，并把去隐私结论沉淀成 run-local candidate。
4. 如果再次出现“像旧稿、太像模板、找茬感、手机不好读”，优先写入 `<RUN_DIR>/calibration/dialogue`，再决定是否生成候选复盘；不要直接改全局规则。
