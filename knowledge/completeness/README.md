# Knowledge Completeness

这个目录只做一件事：判断知识库“能不能被宣称为完整”。它不产生命理断语，也不存客户案例。

## 目标

`coverage-matrix.json` 是机器可审计的覆盖度矩阵。它把每个模块拆成三层状态：

- `runtime_curated`: 已经能服务日常报告，但仍需按来源边界写。
- `source_boundary_curated`: 找到了来源或版本线索，但只能作为边界，不支撑强判断。
- `protocol_curated_no_entries`: 流程已经建立，但还没有真实、去隐私、人工确认的案例复盘。

## goal_complete 规则

项目不能只因为资料目录很多就宣称完成。`goal_complete` 只有在这些条件同时满足时才可以为 `true`：

- `scripts/audit_project_hygiene.py` 通过，证明项目内没有客户输出物和运行产物。
- `scripts/audit_knowledge_base.py` 通过，证明知识库文件、来源 ID、promotion manifest 和隐私禁区都合格。
- `scripts/audit_source_documentation.py` 通过，证明机器注册表里的网络来源在人读来源文档中有对应入口、边界说明和 URL 对照。
- `scripts/audit_promotion_manifest.py` 通过，证明每个晋升条目都有合法路径、来源 ID、批准状态和说明。
- `scripts/audit_rule_cards.py` 通过，证明运行时规则卡有 source_id、已登记来源和结构化规则字段。
- `scripts/audit_case_retrospectives.py` 通过，证明案例复盘层没有泄露隐私。
- `scripts/audit_knowledge_coverage.py` 通过，证明覆盖度矩阵本身可读、可追踪。
- `retrospective-requirements.json` 中的复盘数量和状态门槛满足；候选复盘不计入完成度。
- `coverage-matrix.json` 里没有 `blocks_goal_completion=true` 的 blocker。

当前阶段允许联网找典籍，但联网资料只能先进 `source register` 或 `research backlog`，再被提炼成规则卡；不能在单个付费报告里临时边搜边断。

## 阻塞项

目前最关键的阻塞项不是典籍入口，而是真实案例复盘：还没有任何经过人工确认、去隐私、可复盘的 case retrospective JSON。这个阻塞项存在时，项目可以用于新 case 生产，但不能宣称“知识库已经完整完成”。

## 复盘门槛

`retrospective-requirements.json` 记录每个阻塞项对应的最小证据。当前默认要求：

- `bazi`、`ziwei`、`western`、`liuyao`、`writing` 各至少 2 条 `curated` 或 `verified` 的人工批准复盘。
- 全局复盘层至少 1 条 `curated` 或 `verified` 的人工批准复盘。
- `candidate` 不计入完成度；它只能说明有候选材料，还不能关闭 blocker。

`audit_knowledge_coverage.py` 会输出 `retrospective_requirements` 和 `next_actions`。如果有人手动删掉 blocker，但对应复盘数量不达标，审计会失败；如果 blocker 未满足，`next_actions` 只给出 run-local 候选复盘、dry-run 晋升、人工批准和复审命令模板，不会自动制造复盘或把 candidate 算入完成度。
