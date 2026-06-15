# Evaluation Roadmap

这个项目现在不是 benchmark 仓库。它的主线是 Codex Skill、结构化排盘、读者报告、追问和去隐私复盘。

但如果长期要判断它有没有变好，不能只靠“感觉更准”或“这次写得顺”。后续评测可以分成四层，先文档化，再决定要不要做脚本。

## Related Work

[MingLi-Bench](https://github.com/DestinyLinker/MingLi-Bench) 把全球算命师大赛题目整理成八字和紫微斗数选择题 benchmark，并用预计算命盘把“排盘准确性”和“推理能力”拆开。它的技术报告 [Tianfu Agent](https://destinylinker.github.io/MingLi-Bench/) 也明确强调确定性计算工具、规则化推理经验和生成式叙事能力的结合。

本项目借鉴这个方向，但不复刻它的形态：

- MingLi-Bench 更适合评估封闭选择题推理能力。
- `xuanxue-console` 更关注开放式读者交付、追问上下文、隐私边界和真实反馈复盘。
- 如果未来做 benchmark，应作为旁路评测层，不应挤占默认交付流程。

## Layer 1: Calculation Facts

目标：确认模型没有手算，结构化事实来自脚本。

可评估项：

- 八字四柱、流年、大运、十神、纳音等字段是否稳定。
- 紫微十二宫、主星、四化、大限等字段是否能从 JSON 回溯。
- 西占、六爻、小六壬、MBTI 等模块是否明确标注输入、边界和 warnings。
- 出生时间、真太阳时、时辰边界等敏感项是否进入 `uncertainties`。

当前依赖：

- `scripts/xuanxue_console.py`
- `scripts/build_fact_archive.py`
- `scripts/audit_birth_time_sensitivity.py`
- `case_manifest.json`

## Layer 2: Report Consistency

目标：报告正文不能脱离 facts，也不能把内部流程写给读者。

可评估项：

- 正文结论是否能回到结构化 facts、知识库规则卡或现实校准问题。
- 是否出现脚本路径、JSON 路径、命令、坐标口径等内部过程词。
- 是否存在跨 case 重复话术，例如“不会表达边界”“恢复机制”“作品化”等无证据套话。
- 强判断、倾向判断和校准问题是否分级清楚。

当前依赖：

- `scripts/validate_longform_report.py`
- `scripts/audit_longform_consistency.py`
- `scripts/validate_relationship_report.py`
- `knowledge/writing/reader-rich-report.md`

## Layer 3: Follow-Up Grounding

目标：追问不能只靠旧文章揣测，必须重新回到 run-local facts 和知识上下文。

可评估项：

- 每次追问是否生成并读取 `runtime/followups/*.json`。
- 回答是否引用本次 facts、required knowledge files 和 dialogue note。
- 合盘追问是否读取 relationship facts、relationship mode 和 life domains。
- 追问后的新反馈是否进入 `<RUN_DIR>/calibration/dialogue/`。

当前依赖：

- `scripts/create_followup_context.py`
- `scripts/build_knowledge_context.py`
- `<RUN_DIR>/calibration/dialogue/`

## Layer 4: Human Feedback Retrospectives

目标：知识库越来越像命理解释知识库，而不是写作约束库。

可评估项：

- 哪段准、哪段不准、为什么误读、怎么改，是否被去隐私保存。
- 反馈是否明确覆盖 `bazi`、`ziwei`、`western`、`liuyao`、`relationship` 或 `writing`。
- 没有人工确认的反馈是否仍停留在外部 run。
- 晋升后的规则是否能被后续报告复用，而不是只增加泛化口吻。

当前依赖：

- `scripts/create_retrospective_intake.py`
- `scripts/create_case_retrospective_candidate.py`
- `scripts/promote_case_retrospective.py`
- `scripts/audit_case_retrospectives.py`
- `scripts/audit_knowledge_coverage.py`

## Judgment Strength

报告里的判断建议显式分级：

- **强判断**：至少两层证据同向，且没有明显反例；可以写“更像 A，不是 B”。
- **中等倾向**：有主要证据，但存在出生时间、体系冲突或现实信息不足；写成“更偏向 A，但需要用某个现实问题校准”。
- **校准问题**：命理信号存在，但还不能落成结论；写成可验证问题。
- **不应断**：涉及医疗、法律、投资、重大婚恋决定，或证据不足；只写边界和现实建议。

这不是为了变中庸，而是让锋利有证据、边界有原因、反馈有入口。

## Near-Term Rule

下一阶段不急着新增评测脚本。优先复用现有 validator、audit 和 follow-up context，把真实 run 的反馈沉淀出来。等至少有若干去隐私复盘后，再考虑做小型内部评测集。
