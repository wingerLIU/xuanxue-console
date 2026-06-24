# Case Retrospective Promotion Protocol

source_id: `SRC-PROJECT-CASE-RETROSPECTIVE-PROTOCOL`

案例复盘是本项目的自进化层，但它也是最容易串案和污染知识库的地方。复盘只能保存去隐私后的“可复用判断机制”，不能保存客户资料、截图、报告正文、交付包、本机路径或原始聊天内容。

## 晋升门槛

一个复盘条目必须同时满足：

1. `human_approved=true`，并说明是谁在业务上确认了这个复盘可以沉淀。
2. 已去除姓名、昵称、出生年月日时、出生地细节、截图路径、客户行业细节和私密经历。
3. 有明确 `target_artifacts`，说明它要改进哪类对象：规则卡、写作模板、校验脚本、服务 SOP 或风险边界。
4. 有明确 `domains`，说明它覆盖的是 `bazi`、`ziwei`、`western`、`liuyao`、`relationship`、`team_career`、`fengshui`、`writing` 等哪个知识域，便于 coverage 层判断缺口是否被真实复盘支持。
5. 有 `counterexamples` 或 `limits`，说明这个经验什么时候不适用。
6. 有 `evidence_summary`，但只能写抽象证据，不写原始案例事实。
7. 对 `bazi`、`ziwei`、`western`、`mbti`、`liuyao`、`xiaoliuren`、`relationship`、`team_career`、`fengshui`、`writing` 这类会影响判断或表达的领域，候选 JSON 必须写 `domain_evidence`：每个 domain 至少包含 `evidence_anchor`、`observed_feedback`、`promotion_limit`。
8. 通过 `scripts/audit_case_retrospectives.py`。

## 状态定义

- `candidate`: 去隐私复盘已写好，但尚未改动任何运行时规则。
- `curated`: 已经改进某个规则、模板、脚本或 SOP，并登记在 promotion manifest。
- `verified`: 至少两个以上去隐私复盘或明确反例支持，并经过人工复核；当前项目默认不轻易使用。

`candidate` 只能保存在外部 run 目录。进入 `knowledge/case-retrospectives/` 的条目必须是 `curated` 或 `verified`，否则不能计入 completion，也会被审计拦住。

## 禁止晋升

- 只来自一次客户反馈、没有反例。
- 只是“这篇文章客户喜欢”，没有说明具体机制。
- 包含客户时间、地点、姓名、截图、本机路径、报告正文片段。
- 把个案命盘结论变成通用命理规则。
- 为了增加专业感而补写不存在的反馈。

## 可晋升方向

- 写作模板：摘要怎么更像付费报告，行动建议如何减少过程话。
- 规则卡：某个命理判断在哪些现实场景更容易误读。
- 合盘/团队：关系张力、合伙分工、城市商业判断或新增成员影响是否被现实反馈验证。
- 风水方位：空间、城市、座位、居住或开运建议执行后是否可观察，哪些必须降级。
- 校验脚本：新增过程语言、强断语、路径泄漏、客户信息泄漏的检查。
- 服务 SOP：新 case 输入输出边界、复盘提交流程、人工确认节点。

## 领域证据门槛

人工审批时不要只看“客户觉得准”。每条复盘必须说明它到底验证了哪一层判断，以及哪一层不能推广。

| domains | 可以算作有效证据 | 不能算作有效证据 |
| --- | --- | --- |
| `bazi` | 现实反馈能对应到日主强弱、月令、十神、格局、调候、大运或流年中的具体一层，并说明原判断准在哪里、误在哪里。 | 只说“性格像”“挺准的”，但没有指出哪条八字证据被验证或推翻。 |
| `ziwei` | 反馈能对应到宫位、主星、四化、大限或流年触发，并说明是宫位主题准、星曜语言过强，还是时辰/大限边界需要校准。 | 只把紫微当成情绪描述，或没有区分命宫、官禄、财帛、夫妻、迁移等宫位来源。 |
| `western` | 反馈能对应到落座、相位、宫位、上升/天顶、关系轴线或时间敏感项，并说明哪段有特异性、哪段像泛心理语言。 | 只说“心理描述像”，但没有说明具体西占锚点，或出生时间不稳却强行验证宫位。 |
| `liuyao` | 有明确问题、起卦时间/方式、判断窗口和后续真实结果，能回看用神、世应、动爻、月日、旬空或六亲权重。 | 没有结果反馈，或把短期问事扩写成长期命运判断。 |
| `relationship` | 关系反馈能对应到吸引、互补、误读、事业/家庭/财富/精力/亲近边界中的具体生活域，并说明是否误把现实细节写成命理事实。 | 只说“关系很像”，但没有说明哪一个生活域需要改写。 |
| `team_career` | 团队反馈能对应到角色落地、权责机制、钱账边界、客户入口、城市商业变量或新增成员影响，并区分商业现实和命理象意。 | 只说“团队判断准”，但没有说明是分工、城市、资源、现金流还是人际权力结构被验证。 |
| `fengshui` | 有执行动作、观察周期、实际变化和可能驱动，能说明建议来自环境调整、生活习惯、商业资源还是方位象意，并写清降级边界。 | 只说“换了方向感觉好了”，但没有观察指标、执行成本或现实驱动说明。 |
| `writing` | 能指出哪类表达更像模板、太中庸、太冲、太流程感，或哪种结构让读者更愿意读、能转发、能执行。 | 只说“文笔好/不好”，但没有对应到报告结构、标题、摘要、行动建议或交付形态。 |

跨域复盘可以同时选择多个 domains，但每个 domain 都要满足对应证据门槛。证据只够写作反馈时，就只选 `writing` 或 `quality`，不要为了关闭 blocker 顺手加 `bazi`、`ziwei`、`western`、`liuyao`、`team_career` 或 `fengshui`。

`domain_evidence` 是机器可读的审批自查字段，不替代人工判断。它只回答三件事：这条证据锚在哪个判断层，观察到了什么反馈，以及它不能推广到哪里。缺少这个字段时，`create_retrospective_intake.py` 和 `audit_knowledge_coverage.py` 会把候选列入待补证据，而不是 ready 队列。

## 最小复盘流程

`schemas/knowledge_context.schema.json` 约束 run-local `runtime/knowledge_context.json`，确保每次分析都有可复查的知识文件、来源、blocker 和复盘计划；`schemas/retrospective_intake.schema.json` 约束 run-local `runtime/retrospective_intake.json`，确保反馈采集计划和 `domain_question_bank` 可被后续工具读取；`schemas/case_retrospective.schema.json` 约束最终可晋升的去隐私复盘条目。三者都只是结构契约，不替代人工确认。

```text
读者反馈或交付后校准
-> create_retrospective_intake.py 生成反馈收集清单
-> 去隐私摘要
-> 写反例/限制
-> 指定要改进的 artifact
-> 在外部 run 目录生成 candidate JSON
-> 人工确认 human_approved=true
-> promote_case_retrospective.py 写入全局知识库
-> audit_case_retrospectives.py 通过
-> 改动对应知识卡/模板/脚本
-> 写入 promotion manifest
```

## 推荐命令

先生成外部反馈 intake，用 `knowledge_context` 里的复盘计划和 `target_artifacts` 指导收集：

```powershell
python -B -X utf8 scripts\create_retrospective_intake.py --manifest <RUN_DIR>\case_manifest.json
```

候选生成必须在外部 run 目录完成，默认 `human_approved=false`：

```powershell
python -B -X utf8 scripts\create_case_retrospective_candidate.py --manifest <RUN_DIR>\case_manifest.json --slug reader-hook --title "去隐私复盘标题" --evidence-summary "只写抽象证据" --domain-evidence "writing|读者指出某类标题太像流程说明|改成先下结论后更愿意继续读|只适用于读者交付稿，不适用于工程复盘" --target-artifact knowledge/writing/reader-rich-report.md --counterexample "不适用于技术复盘型客户" --limit "这是写作机制，不是命理规则"
```

`--domain` 可以显式指定；如果不写，工具会尽量从 `target_artifact` 推断。例如 `knowledge/bazi/...` 会推断为 `bazi`，`knowledge/writing/...` 会推断为 `writing`。无法推断时必须手动传入。

人工确认后再晋升：

```powershell
python -B -X utf8 scripts\promote_case_retrospective.py --candidate <RUN_DIR>\retrospectives\CR-YYYYMMDD-reader-hook.candidate.json --approved-by EDY
```

默认晋升为 `curated`。只有已经有多个复盘、反例和人工复核支持时，才显式加 `--status verified`。

不要手动把外部 candidate 复制进 `knowledge/case-retrospectives/`。这样容易绕过 `human_approved`、隐私扫描和审计回滚。
