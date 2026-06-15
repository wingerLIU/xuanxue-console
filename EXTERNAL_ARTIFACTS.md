# External Artifacts

项目仓库只保留通用代码、规则、模板、知识库和服务文档。客户输入、结构化 JSON、HTML、长文、DOCX/PDF/ZIP、Playwright 截图和运行日志都放在项目外。

## 默认外部根目录

```text
%USERPROFILE%\Documents\xuanxue_console_runs
```

也可以用环境变量覆盖：

```powershell
$env:XUANXUE_RUNS_ROOT = "D:\xuanxue_console_runs"
```

## 当前旧产物归档

本次从项目仓库迁出的旧产物位于：

```text
%USERPROFILE%\Documents\xuanxue_console_runs\archive\repo_cleanup_20260612_194441
```

包含：

- `reports`: 历史 case 报告、HTML、数据 JSON、DOCX/PDF/ZIP。
- `output`: 历史 Playwright 渲染检查输出。
- `.playwright-cli`: 本地 Playwright 临时目录。
- `scripts___pycache__`: Python 缓存。

## 新 case 标准路径

```text
<EXTERNAL_ROOT>\inputs\<case_id>
<EXTERNAL_ROOT>\runs\<case_id>\<run_id>\runtime
<EXTERNAL_ROOT>\runs\<case_id>\<run_id>\runtime\source_liveness.json
<EXTERNAL_ROOT>\runs\<case_id>\<run_id>\data
<EXTERNAL_ROOT>\runs\<case_id>\<run_id>\drafts
<EXTERNAL_ROOT>\runs\<case_id>\<run_id>\delivery
<EXTERNAL_ROOT>\runs\<case_id>\<run_id>\logs
```

创建：

```powershell
python scripts\create_case_workspace.py --case-id <case_id> --reader-name <name>
```

检查：

```powershell
python scripts\audit_project_hygiene.py
python scripts\audit_case_workspace.py --manifest <RUN_DIR>\case_manifest.json
```
