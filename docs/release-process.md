# Release Process

这个项目不需要复杂发布流程。每次准备公开更新时，按下面顺序做即可。

## Before Release

1. 确认仓库没有真实 case、截图、PDF、HTML、ZIP、run-local JSON 或本机路径。
2. 更新 [CHANGELOG.md](../CHANGELOG.md)，把 `Unreleased` 里的内容归到新版本。
3. 必要时更新 [VERSION](../VERSION)。
4. 运行：

```powershell
.\verify.cmd
```

5. 确认 GitHub Actions 通过。

## Version Rule

- `0.x`: 仍是实验阶段，工作流和模板可能调整。
- `PATCH`: 文档、测试、兼容性、小修。
- `MINOR`: 新增脚本、模板、知识库模块、报告形态或质量闸门。
- `MAJOR`: 默认交付契约、manifest 结构或主要工作流发生不兼容变化。

## Tag

确认通过后，可以打一个轻量 tag：

```powershell
git tag v0.1.0
git push origin v0.1.0
```

真实案例、展示图和交付物不跟随 release 进入主仓库。
