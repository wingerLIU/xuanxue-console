# Research And Promotion Policy

这个项目允许联网和外部资料吸收，但必须先进入知识治理流程，不能直接污染客户报告。

## 两层知识结构

1. `knowledge/`: 运行时可用的全局知识库，只放通用规则、来源索引、写作规范和已去隐私复盘。
2. 外部 run 目录：每个客户 case 的输入、排盘 JSON、草稿、交付包、校准记录和 run-local retrospective。

全局知识库不能存客户资料；外部 run 不能反向定义全局规则，除非经过人工确认和晋升。

## 联网资料进入流程

1. 记录来源：标题、作者/机构、URL 或出版信息、访问日期、资料类型。
2. 标注状态：默认 `candidate`，不能直接支撑强判断。
3. 确认落点：先指定 `target_artifacts`，例如 `knowledge/bazi/classical-anchors.md`、`knowledge/ziwei/classical-anchors.md` 或 `knowledge/sources/research-backlog.md`。
4. 提炼规则：只抽象可复用规则，不复制大段原文。
5. 写清边界：适用范围、常见误判、不得使用的场景。
6. 登记晋升：更新 `knowledge/promotion/knowledge_promotion_manifest.json`。
7. 通过检查：运行 `scripts/audit_knowledge_base.py`。

## 联网来源优先级

新增典籍来源时按这个顺序找：

1. 公共图书馆、国家档案馆、大学或研究机构的数字馆藏。
2. Wikisource、Chinese Text Project、Project Gutenberg、Internet Archive、Wikimedia Commons 等可长期复核入口。
3. 有作者、版本、出版信息和上下文的学术论文、书目或馆藏目录。
4. 个人站、公众号、论坛、网盘、下载站、Scribd、商品页只作线索，默认不得晋升。

联网搜索可以帮助找到入口，但不能替代版本校对、边界说明和规则卡晋升。

## 晋升条件

进入运行时规则卡至少需要：

- `source_id` 已在 `knowledge/source-index.md` 登记。
- 有明确 `scope` 和 `limits`。
- 能说明如何从象意翻译成现代现实语言。
- 不含客户身份、截图、出生资料、本机路径或交付稿。
- 若来自 case retrospective，必须 `human_approved=true`。

## 资料类型处理

- 经典文本：可以作为术语和原则来源，但不能把古文宿命断语直接搬进现代报告。
- 现代教材：可以帮助组织语言和反例，但必须标注为现代综合。
- 网络文章：默认只作候选；没有作者、出处、流派和上下文时不得晋升。
- 客户反馈：只能去隐私后作为“校准经验”，不能把单个客户经历当普遍规则。

## 报告使用规则

正式报告使用知识库时，只使用已登记的规则卡和脚本事实。若某个判断只来自临时搜索或模型记忆，必须降级为“可校准倾向”，或不写。

## 维护节奏

- 新 case 前：运行 `scripts/audit_project_hygiene.py` 和 `scripts/audit_knowledge_base.py`。
- 新 case 后：只在外部 run 写 retrospective。
- 多个 case 重复出现同一问题：提炼候选规则，等待人工确认后晋升。
