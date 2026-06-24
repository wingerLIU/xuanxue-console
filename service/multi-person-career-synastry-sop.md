# 多人事业合盘 SOP

本 SOP 用于三人及以上的事业合作、合伙创业、团队搭档和组织内关键人协同分析。它不是恋爱合盘的扩展稿，而是一个团队级判断流程：先保留每个人的单盘事实，再把两两关系事实作为协作证据，最后用现实角色、商业约束、城市选择和流年流月窗口做总评。

## 适用场景

- 三人及以上长期合作、合伙创业、项目搭档、组织核心小组。
- 已经有现实协作基础，需要判断能不能独立合伙、谁适合拍板、谁适合破局、谁适合稳定交付。
- 需要比较城市、行业路径、资源打法、未来 6-18 个月窗口。
- 用户明确要求命理开运化时，可以写命理辅助，但商业判断必须先行。

不适用：

- 只想看两个人的亲密关系或情感合盘，应使用 `templates/relationship-rich-template.md`。
- 缺少每个人基础出生资料时，不得强行写完整团队结论；只能写资料边界和补充清单。
- 重大投资、法律股权、医疗健康等问题只能给边界和沟通框架，不替代专业意见。

## 输入清单

- 每位成员的单盘 `case_manifest.json`，以及已生成的 `combo.json`、facts markdown。
- 成员关系：领导/平级/上下游/客户/资源方/执行方/外部合伙人。
- 决策结构：谁主要拍板，谁有否决权，谁负责钱、客户、产品、交付、运营、法务或资源。
- 合作年限和合作阶段：刚开始 / 1 年内 / 2-3 年 / 三四年及以上 / 已经多轮项目验证。
- 现实卡点：公司层资源、客户入口、资金、政策、产品成熟度、团队信任、城市、家庭迁移、个人精力。
- 可选 MBTI：只作行为语言，不作命理证据。
- 城市候选：至少写明候选城市、行业机会、客户资源、生活成本、团队可迁移性。
- 用户要求的时间窗口：年度、季度、流月、流日；若问具体开张、签约、搬迁，需要另起六爻/小六壬或明确起问时间。

## 运行结构

### 1. 锁定单人事实

每个人先按普通单盘流程生成结构化 facts。不要在多人合盘里手算四柱、紫微或西占，也不要从聊天记忆补事实。

必读：

- `<PERSON_RUN>/case_manifest.json`
- `<PERSON_RUN>/data/<case>-combo.json`
- `<PERSON_RUN>/data/<case>-facts.md`
- `<PERSON_RUN>/runtime/knowledge_context.json`

### 2. 生成两两 relationship run

多人合盘的命理底层仍然使用两两关系事实。三人团队需要 3 组 pair，四人团队需要 6 组 pair。新增成员时只补新增成员与既有成员的 pair，不重建全部旧 pair。

示例：

```powershell
python -X utf8 scripts\create_relationship_workspace.py `
  --person-a-manifest <A_RUN>\case_manifest.json `
  --person-b-manifest <B_RUN>\case_manifest.json `
  --person-a-label <A> `
  --person-b-label <B> `
  --relationship-status "事业合作/合伙候选/同事关系" `
  --distance-status "长期合作/同城协作/异地协作" `
  --person-a-mbti-type <MBTI> `
  --person-b-mbti-type <MBTI>
```

pair run 输出后必须读取：

- `<PAIR_RUN>/data/<case>-relationship.json`
- `<PAIR_RUN>/data/<case>-relationship-facts.md`
- `<PAIR_RUN>/runtime/relationship_workflow.json`

### 3. 建团队级 run

团队总评单独放一个外部 run，不把团队事实写回单人 run 或 pair run。

推荐目录结构：

```text
<RUN_DIR>/
  case_manifest.json
  data/
    team-source-summary.json
    team-flow-timing.json
    team-city-commercial-notes.md
  drafts/
    <case>-team-career-synastry.md
  calibration/
    dialogue/
      <date>-team-calibration.md
  delivery/
  runtime/
```

`team-source-summary.json` 至少记录：

- 成员清单与各自单盘 manifest。
- 两两 pair run manifest。
- 现实角色和决策结构。
- 已知合作年限、关键卡点和城市候选。
- 用户反馈中只能作为现实校准的内容，不能写成命理事实。

最小结构建议：

```json
{
  "schema_version": "0.1.0",
  "team_case_id": "<team-case-id>",
  "members": [
    {
      "label": "<成员称呼>",
      "role": "<现实职责>",
      "single_manifest": "<PERSON_RUN>/case_manifest.json",
      "facts_json": "<PERSON_RUN>/data/<case>-combo.json",
      "facts_markdown": "<PERSON_RUN>/data/<case>-facts.md"
    }
  ],
  "pair_relationship_runs": [
    {
      "pair": ["<成员A>", "<成员B>"],
      "relationship_manifest": "<PAIR_RUN>/case_manifest.json",
      "relationship_facts": "<PAIR_RUN>/data/<case>-relationship.json"
    }
  ],
  "business_context": {
    "decision_structure": "<谁拍板、谁否决、谁复盘>",
    "known_constraints": ["<公司层资源>", "<客户入口>", "<资金或交付卡点>"],
    "city_candidates": ["<城市A>", "<城市B>"],
    "time_window": "<年度/季度/月度窗口>"
  },
  "writing_boundaries": {
    "do_not_infer": ["<不能从现实反馈扩写成命理事实的内容>"],
    "reader_forbidden_phrases": ["你确认自己", "这一点与盘面吻合", "前稿判断相符"]
  }
}
```

### 4. 写团队级事实摘录

写读者正文前，先在 `data/team-source-summary.json` 或 `data/team-source-summary.md` 固化以下信息：

- 每个人的事业核心：日主、月令、十神结构、当前大运、紫微事业/命迁财相关宫位、西占事业/沟通/资源相关锚点。
- 每个 pair 的协作锚点：天干地支合冲刑害、当前大运/流年互动、西占沟通/价值/冲突锚点、MBTI 行为互译。
- 团队结构：拍板者、破局者、稳定交付者、客户入口、资源入口、流程冻结者。
- 风险结构：决策分散、资源不归位、边界不清、方案过多、执行责任不归属、钱账/客户/股权不清。
- 时间结构：年度大势、流月适合动作、流日只用于具体行动窗口，不替代商业条件。

### 5. 报告写作

使用 `templates/team-career-synastry-template.md`。正文默认第三人称或成员姓名，不用“你确认”“与盘面吻合”“前稿判断相符”等主观确认句。

报告必须覆盖：

- 总评：适不适合独立合伙、适合什么形态、不适合什么形态。
- 权力结构：谁拍板，谁建议，谁执行，谁负责复盘。
- 每个人的事业位置：优势、风险、适合岗位、不能承担的责任。
- 两两协作关系：互补点、误读点、需要冻结的规则。
- 公司层资源卡点：资源不足时如何试点，何时不宜硬上。
- 城市判断：先写商业逻辑，再写命理开运辅助；不可只用五行选城。
- 流年流月：把年度、季度、月度动作拆开；流日只作短窗口。
- 60-90 天试点：入口、客户、产品、交付、钱账、复盘标准。

### 6. 城市判断规则

城市选择先按商业排序：

- 客户和资源入口是否更近。
- 试点成本、人才、政策、供应链、行业生态是否匹配。
- 团队主要决策者和关键执行者是否能长期驻留。
- 是否能先用低成本项目验证，而不是直接重资产迁移。

命理辅助只写第二层：

- 五行气候、方位象意、个人大运喜忌、团队补位。
- 写成“更适合作为试点/资源口/品牌口/交付口”，不要写成绝对吉凶。
- 若商业判断和命理辅助冲突，正文以商业判断为先，并说明命理建议只用于布局、节奏和开运辅助。

### 7. 流年流月和流日

- 年度：判断是否适合启动、收缩、换城、谈判、签约、融资、招人。
- 流月：判断适合谈资源、定框架、试点上线、复盘修正、暂停观望。
- 流日：仅用于已经有明确事项时择行动窗口，例如签约、会谈、发布、搬迁；不得把流日写成无条件成功。
- 具体择日建议应记录起问时间、事项、地点、参与人和现实前置条件；资料不全时只给择日原则。

### 8. 读者正文禁用语

多人事业合盘尤其要避免把现实反馈写成命理背书。以下表达不得进入读者正文：

- “你确认自己……”
- “这一点与盘面吻合”
- “前稿判断相符”
- “已经被验证”
- “一定成功/一定失败”
- “只要按这个做就能成”
- 非恋爱关系中的身体吸引、私密生活和暧昧推断。

可用写法：

- “从结构看，更适合……”
- “现实角色显示，这个人更像……”
- “命盘与组织位置共同指向……”
- “如果公司层资源仍不落地，风险会集中在……”
- “商业上应先验证……，命理上更适合把……作为辅助布局。”

### 9. 打包与验收

团队总评仍使用通用打包脚本：

```powershell
python -X utf8 scripts\package_reader_delivery.py <RUN_DIR>\drafts\<case>-team-career-synastry.md `
  --output-dir <RUN_DIR>\delivery `
  --basename <团队名>多人事业合盘总评 `
  --subtitle 多人事业合作与独立合伙命理总评 `
  --manifest <RUN_DIR>\case_manifest.json `
  --artifact-prefix rich `
  --avoid-locked `
  --json
```

验收至少做：

- Markdown 和 PDF 都能检索到成员姓名、合作年限、城市候选、独立合伙总评。
- PDF 文本可用 `pypdf` 抽取。
- 读者正文不含禁用语。
- 城市章节存在商业判断和命理辅助两层。
- 时间章节区分年度、流月、流日。
- `final-delivery.md` 记录资料边界、用户校准、导出文件、验证结果和未做事项。
- `case_manifest.json` 至少记录 `team-source-summary.json`、团队总评源稿、PDF 交付件和验证状态；如果暂时复用 rich artifact keys，`final-delivery.md` 必须说明这是 team run 的团队总评，不是单盘 rich。
- 不把 team run 产物复制回项目仓库；真实团队资料、pair run 路径和报告正文都留在外部 run。

### 10. 新增成员时

新增第 N 人时按增量流程处理：

1. 先建新增成员单盘 run。
2. 生成新增成员与所有既有成员的 pair relationship run。
3. 更新团队 run 的 `team-source-summary.json`。
4. 重写团队角色矩阵、两两协作矩阵、城市/资源判断和流年流月窗口。
5. 保留旧报告为历史版本，不在旧交付稿上直接覆盖。
6. 重新打包并记录“本版新增成员”和“本版新增证据”。
