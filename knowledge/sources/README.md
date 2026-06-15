# Sources Layer

这个目录是知识库的来源层，不是客户报告素材库。

## 文件分工

- `source-register.json`: 机器可读的总注册表。每个 `SRC-*` 必须有类型、状态、证据模式、入口、边界和晋升目标。
- `online-classics.md`: 人读的典籍联网核验记录，适合写清楚“找到了什么、哪里不稳、不能怎么用”。
- `modern-references.md`: MBTI、西占心理语言、科学边界等现代资料入口。
- `research-backlog.md`: 找到线索但暂不晋升的资料、版本问题和待核验事项。

## 联网核验

默认 `verify.ps1` 不联网。原因很简单：客户交付前的稳定验证不能被外部网站超时、重定向或临时故障拖垮。

当要新增或晋升典籍时，使用手动核验：

```powershell
python -B -X utf8 scripts\check_source_urls.py --source-id SRC-BAZI-DITIAN-SUI
python -B -X utf8 scripts\check_source_urls.py --type classical_text --evidence-mode online_public_entry
python -B -X utf8 scripts\check_source_urls.py --domain bazi --type classical_text
python -B -X utf8 scripts\check_source_urls.py --max-sources 5
```

如果这次核验会支撑一个新 case 或知识晋升，写出外部快照：

```powershell
python -B -X utf8 scripts\check_source_urls.py --type classical_text --evidence-mode online_public_entry --output <RUN_DIR>\runtime\source_liveness.json --json
```

`--output` 不能指向项目仓库内部；核验快照属于运行证据，不属于全局知识库正文。

如果只是检查注册表结构，不联网：

```powershell
python -B -X utf8 scripts\check_source_urls.py --dry-run
python -B -X utf8 scripts\audit_source_register.py
python -B -X utf8 scripts\audit_source_documentation.py
python -B -X utf8 scripts\audit_promotion_manifest.py
```

## 晋升边界

联网找到 URL 不等于能写进付费报告。必须先满足：

1. `source-register.json` 有来源对象。
2. `online-classics.md` 或 `modern-references.md` 有人读说明。
3. 明确 `target_artifacts`，知道这条来源要进入规则卡、研究 backlog、来源索引还是校验脚本。
4. `knowledge/promotion/knowledge_promotion_manifest.json` 有晋升记录。
5. 对应规则卡写清楚 `used_for` 和 `limits`。
6. `audit_source_register.py`、`audit_source_documentation.py`、`audit_knowledge_base.py`、`audit_knowledge_coverage.py` 都通过。

没有进入规则卡的网页内容，只能作为研究线索，不能支撑客户报告里的强判断。
