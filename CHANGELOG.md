# Changelog

本文件记录公开仓库层面的重要变化。格式尽量接近 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，版本号遵循轻量语义化版本：

- `MAJOR`: 工作流或输出契约有明显不兼容变化。
- `MINOR`: 新增能力、模板、规则卡、质量检查或交付形态。
- `PATCH`: 修 bug、文档、测试、兼容性和小幅整理。

## Unreleased

### Added

- 新增多人事业合盘流程和模板：`service/multi-person-career-synastry-sop.md`、`templates/team-career-synastry-template.md`。
- 客户资料表、生产 SOP、SKILL 和 README 增加多人事业合盘入口，明确单盘 facts、两两 relationship facts、团队级 run、城市商业判断和流年流月窗口。

### Changed

- README 增加项目动机：把玄学视为古代世界模型，把大模型视为现代世界模型，主线是可复查、可反馈的解释实验。
- README 增加 MingLi-Bench / Tianfu Agent 相关工作说明，并补充判断强度分级。
- 新增 `docs/evaluation-roadmap.md`，记录后续评测路线：事实计算、报告一致性、追问 grounding 和真实反馈复盘。

## 0.1.0 - 2026-06-15

### Added

- 公开仓库 README、隐私边界、贡献说明和展示边界。
- GitHub Actions `verify` 工作流，push / PR 自动运行项目验证。
- Codex Skill 安装说明和作者署名。

### Changed

- README 从内部流程说明收敛为公开项目介绍。
- 项目定位明确为学习交流、个人实验和 Codex Skill 工作流参考，不鼓励直接商业换壳。
- 报告写作标准改成更容易读懂的“人话版”说明。

### Fixed

- PDF 导出字体不再硬依赖本机中文字体；GitHub runner 缺少 `simfang.ttf` / `simhei.ttf` 时会使用 ReportLab 内置 CJK 字体兜底。
- GitHub Actions 临时目录口径固定，避免 Windows runner 短路径导致测试不稳定。
