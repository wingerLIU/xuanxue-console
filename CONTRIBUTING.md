# Contributing

欢迎交流、提 issue 或 PR。这个仓库更像一个 Codex Skill 实验台：把排盘、事实留痕、知识库、长文生成和复盘流程拆清楚，而不是一个可直接拿去售卖的算命产品。

## What To Contribute

- 修 bug、补测试、改善脚本稳定性。
- 改 README、模板、规则卡和流程文档，让它更容易读懂。
- 增加去隐私后的机制复盘：哪类判断准、哪类误读、为什么、下次怎么校准。
- 优化隐私边界、run 外置、manifest、quality gate 和交付检查。

## What Not To Commit

- 真实姓名、生日、出生城市、联系方式、原始对话和客户资料。
- 真实报告正文、截图、PDF、DOCX、HTML、ZIP、图片或 run-local JSON。
- 本机绝对路径、`.env`、API key、缓存、`__pycache__`。
- 未经确认的“案例结论”或可反推出当事人的复盘。

## Before A PR

```powershell
.\verify.cmd
```

如果你新增知识库规则，请优先说明它来自哪次去隐私反馈，而不是只增加写作口径。

## Updating Versions

公开更新前请补 [CHANGELOG.md](CHANGELOG.md)。如果这次变化会影响使用方式、输出契约或默认交付流程，也同步更新 [VERSION](VERSION) 和 [docs/release-process.md](docs/release-process.md)。

## Project Position

代码采用 MIT License。项目作者不鼓励把它简单换壳、批量包装成商业算命服务；如果你要公开展示、二次发布或商业化尝试，请先认真处理来源、隐私、客户边界和内容风险。
