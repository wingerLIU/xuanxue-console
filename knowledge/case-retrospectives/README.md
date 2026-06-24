# Case Retrospectives

这里保存去 case 化的复盘，不保存客户长文、出生资料、截图、交付包或本机绝对路径。

复盘进入本目录前必须满足：

- `human_approved=true`
- `domains` 非空，写清这个复盘覆盖的知识域，例如 `bazi`、`ziwei`、`western`、`liuyao`、`relationship`、`team_career`、`fengshui`、`writing` 或 `quality`。
- 判断和表达类领域要有 `domain_evidence`，写清证据锚点、可观察反馈和推广边界；缺这个字段的候选只能待补证据，不能算 ready。
- 已去除客户姓名、截图、出生地细节和私密经历。
- 写清它要提升的对象：写作模板、知识规则、校验脚本、服务 SOP 或风险边界。
- 至少包含一个反例或限制，避免把一次经验误升为通用规则。

## 文件

- `promotion-protocol.md`: 复盘进入知识库的晋升流程和禁止事项。
- `template.md`: 人工填写用的去隐私复盘模板。
- `*.json`: 机器可审计复盘条目，必须是 `curated` 或 `verified`，并通过 `scripts/audit_case_retrospectives.py`。

## 工具入口

交付后先生成或查看外部反馈收集清单：

```powershell
python -B -X utf8 scripts\create_retrospective_intake.py --manifest <RUN_DIR>\case_manifest.json
```

候选复盘先放外部 run 目录，不直接进入知识库：

```powershell
python -B -X utf8 scripts\create_case_retrospective_candidate.py --manifest <RUN_DIR>\case_manifest.json --slug reader-hook --title "去隐私标题" --domain writing --evidence-summary "抽象证据" --domain-evidence "writing|读者指出某类表达太像流程|改成先结论后证据后更愿意读|只适用于读者交付稿" --target-artifact knowledge/writing/reader-rich-report.md
```

人工确认后再晋升：

```powershell
python -B -X utf8 scripts\promote_case_retrospective.py --candidate <RUN_DIR>\retrospectives\CR-YYYYMMDD-slug.candidate.json --approved-by EDY
```

晋升脚本会把 `human_approved` 改为 `true`，写入本目录，并立即运行 `scripts/audit_case_retrospectives.py`。审计失败时会回滚，不留下半成品。

默认晋升状态是 `curated`。`candidate` 只允许留在外部 run 目录，不允许手动复制进本目录。

## 当前状态

当前已有少量 `writing` / `relationship` curated 复盘；八字、紫微、西占、六爻、多人事业合盘和风水方位仍缺真实去隐私反馈。没有人工确认前，不要为了填充知识库而制造案例。
