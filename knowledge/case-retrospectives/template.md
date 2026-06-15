# Case Retrospective Template

这个模板给人工复盘使用。提交前必须删掉所有客户可识别信息；如果不确定能否去隐私，就不要进入知识库。

## 基本信息

- `id`: `CR-YYYYMMDD-短描述`
- `status`: `candidate`
- `human_approved`: `false`
- `approved_by`: ``
- `domains`: `bazi` / `ziwei` / `western` / `mbti` / `liuyao` / `xiaoliuren` / `writing` / `relationship` / `source_register` / `quality` / `case_retrospectives` / `completeness`
- `target_artifacts`: 规则卡 / 写作模板 / 校验脚本 / 服务 SOP / 风险边界

## 去隐私摘要

只写抽象事实，不写姓名、出生资料、截图路径、城市、公司、私密经历或报告原文。

```text
某类客户在阅读长文时，对某一类表达更容易产生信任、误读或困惑。
```

## 可复用机制

```text
这个复盘真正要沉淀的机制是什么？
它适用于哪类盘面、哪类报告段落、哪类客户问题？
```

## 反例和限制

```text
什么时候不能套用？
什么情况下这个经验会误导？
是否只是写作偏好，而不是命理规则？
```

## 推荐改动

```text
要改哪个文件？
要新增什么校验？
要修改什么报告写法？
```

## JSON 结构示例

```json
{
  "schema_version": "0.1.0",
  "id": "CR-YYYYMMDD-example",
  "title": "去隐私复盘标题",
  "status": "candidate",
  "human_approved": false,
  "approved_by": "",
  "privacy": {
    "deidentified": true,
    "contains_birth_data": false,
    "contains_client_name": false,
    "contains_local_paths": false,
    "contains_delivery_text": false
  },
  "source_case": {
    "case_type": "bazi-longform",
    "date_bucket": "2026-Q2",
    "raw_material_location": "external-only"
  },
  "evidence_summary": "只写抽象证据，不写客户原文。",
  "domains": [
    "writing"
  ],
  "target_artifacts": [
    "knowledge/writing/reader-rich-report.md"
  ],
  "promotions": [
    {
      "artifact": "knowledge/writing/reader-rich-report.md",
      "change_type": "writing_rule",
      "summary": "把过程语言改成读者可执行动作。"
    }
  ],
  "counterexamples": [
    "如果用户明确要技术复盘，不能过度隐藏术语。"
  ],
  "limits": [
    "这是写作经验，不是命理规则。"
  ]
}
```

## 工具生成

先用 intake 工具生成反馈问题和建议落点：

```powershell
python -B -X utf8 scripts\create_retrospective_intake.py --manifest <RUN_DIR>\case_manifest.json
```

优先用工具生成候选 JSON，避免手写时带入本机路径、出生资料或客户原文：

```powershell
python -B -X utf8 scripts\create_case_retrospective_candidate.py --manifest <RUN_DIR>\case_manifest.json --slug reader-hook --title "去隐私复盘标题" --domain writing --evidence-summary "只写抽象证据" --target-artifact knowledge/writing/reader-rich-report.md
```

候选文件会保存在 `<RUN_DIR>\retrospectives\`，并保持 `human_approved=false`。只有人工确认后，才能运行：

```powershell
python -B -X utf8 scripts\promote_case_retrospective.py --candidate <candidate.json> --approved-by EDY
```

晋升后默认状态为 `curated`。`candidate` 不进入全局知识库，也不计入 completion。
