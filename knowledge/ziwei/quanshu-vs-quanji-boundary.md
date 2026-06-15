# Ziwei Quanshu Vs Quanji Boundary

source_id: `SRC-ZIWEI-PROJECT-SYNTHESIS`
external_sources: `SRC-ZIWEI-DOUSHU-QUANSHU`, `SRC-ZIWEI-DOUSHU-QUANJI`, `SRC-ZIWEI-FU-TEXTS`

这个文件处理《紫微斗数全书》和《紫微斗数全集》的使用边界。当前项目可以使用《紫微斗数全书》和赋文入口提炼方法锚点；《紫微斗数全集》只作为馆藏与版本流变线索，不作为客户报告正文判断依据。

## ZW-QJ001 全书可用，全集不可强用

- `source`: `SRC-ZIWEI-DOUSHU-QUANSHU`, `SRC-ZIWEI-FU-TEXTS`, `SRC-ZIWEI-DOUSHU-QUANJI`
- `rule`: 《紫微斗数全书》有稳定公开入口，可作为已登记典籍来源；《紫微斗数全集》目前只有书目、版本考辨和馆藏目录线索。
- `scope`: 紫微典籍来源选择、星曜象意、宫位解释、版本流变说明。
- `limits`: 未找到稳定公开全文前，不能把《全集》里的任何单句当作项目规则。
- `modern_translation`: 有目录线索不等于有可用正文；可证明“这本书存在”，不等于可证明“某条断语可靠”。
- `report_usage`: 付费报告里如需传统依据，优先用《全书》与已整理赋文，不写“全集说”。

## ZW-QJ002 付费、网盘、Scribd、论坛和博客摘段不晋升

- `source`: `SRC-ZIWEI-DOUSHU-QUANJI`
- `rule`: 搜到的付费资源页、百度网盘、Scribd、论坛压缩包、博客摘段和商品页不能作为运行时知识来源。
- `scope`: 联网资料吸收、来源登记、规则卡晋升。
- `limits`: 可以作为“待核验线索”记录，不能复制正文，不能拆规则，不能支撑强判断。
- `modern_translation`: 来源不可控时，即使内容看起来像古籍，也不能进入付费报告的证据链。
- `report_usage`: 如果客户问为什么不用《全集》，说明项目只使用可核验来源，避免把不可追溯材料写成权威。

## ZW-QJ003 馆藏目录只支持版本边界

- `source`: `SRC-ZIWEI-DOUSHU-QUANJI`
- `rule`: 東洋文庫、KOSTMA 等馆藏目录可以证明题名、藏地、形态和部分版本信息，但不提供完整可用文本。
- `scope`: 研究 backlog、来源索引、非晋升边界。
- `limits`: 馆藏目录不等于全文开放；不能据此扩写星曜组合规则。
- `modern_translation`: 它是“这本书在哪、是什么形态”的证据，不是“书里怎么断”的证据。
- `report_usage`: 只在内部 source register / backlog 中出现，不在客户长文正文里展开。

## 晋升条件

《紫微斗数全集》要进入规则卡，必须满足至少一个条件：

1. 稳定公开全文入口。
2. 公开馆藏扫描或馆方授权影像。
3. 可核验版本的实体扫描，并且不违反版权/授权边界。

满足后仍需：

- 登记具体 URL / 馆藏号 / 版本信息。
- 只摘方法，不复制大段原文。
- 加入反例和现代化报告写法。
- 通过 `scripts/audit_knowledge_base.py`。
