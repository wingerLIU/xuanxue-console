# Xuanxue Knowledge Base

这个目录只沉淀可复用知识，不放客户资料、截图、具体 case 长文、交付包或本机绝对路径。

## 分层

- `source-index.md`: 经典、现代资料和内部规则的来源索引；只记录来源、状态、适用范围和限制，不随意粘贴长篇原文。
- `sources/online-classics.md`: 联网核验过的典籍入口和使用边界。
- `sources/modern-references.md`: 现代参考来源，主要用于 MBTI、写作边界和误用风险。
- `sources/research-backlog.md`: 尚未晋升的典籍/资料缺口，防止把未核验来源误当依据。
- `knowledge_map.json`: 机器可读的模块到规则卡索引；新 case 可据此决定要读哪些知识文件。
- `bazi/`: 八字规则卡，包括格局、十神、五行、调候、冲合刑害、大运流年的解释边界。
- `ziwei/`: 紫微规则卡，包括命身、命财官迁、四化、大限和宫位解释边界。
- `western/`: 西占规则卡，包括行星、相位、宫位、上升/天顶和时间敏感项解释边界。
- `mbti/`: MBTI 行为语言规则卡；只作沟通和动机补充，不作命理证据。
- `liuyao/`: 六爻问事规则卡；用于具体问题，不覆盖出生盘。
- `xiaoliuren/`: 小六壬短期提示规则卡；只作弱信号和校准入口。
- `writing/`: 付费 reader-rich 报告与简洁版的摘要、口吻、可读性和禁用过程话规则。
- `rules/`: 跨体系推断合同、联网吸收、知识晋升、强断语限制和高风险领域边界。
- `promotion/`: 知识晋升 manifest，记录哪些规则卡已进入运行时知识库、来源是什么。
- `case-retrospectives/`: 去 case 化复盘。只有人工确认、可复用、无隐私的信息才能进入。

## 使用原则

1. 脚本事实优先：四柱、大运、星曜、行星落座必须来自结构化 JSON。
2. 经典只作规则来源，不冒充确定结论。
3. 每个非显然判断都要能归类为：`calculated_fact`、`classical_rule`、`modern_synthesis`、`case_calibration` 或 `practical_advice`。
4. 没有来源或校准的判断，要写成“倾向”“更像”“需要验证”，不能写成专业定论。
5. 复盘进入全局知识库前，必须去除客户身份、出生截图、具体路径和一次性交付内容。
6. 联网资料只能先进入候选来源和规则卡，不能直接进入客户报告。
7. 新 case 前运行 `scripts/audit_knowledge_base.py`，确保来源、规则卡和晋升清单没有断链。

## 当前规则卡

- `bazi/foundations.md`: 八字结构、月令、旺衰、调候和大运流年边界。
- `bazi/classical-anchors.md`: 从在线典籍入口提炼出的八字方法锚点。
- `bazi/shenfeng-anchors.md`: 《神峰通考》病药、盖头、动静等方法边界。
- `bazi/ten-gods.md`: 十神的现代现实翻译和常见组合写法。
- `bazi/structure-and-flow.md`: 地支关系、神煞和年份推演写法。
- `ziwei/foundations.md`: 命身、大限、四化和单星不单断原则。
- `ziwei/classical-anchors.md`: 从《紫微斗数全书》等入口提炼出的紫微方法锚点。
- `ziwei/palaces-stars-four-transformations.md`: 十二宫、星曜和四化的报告边界。
- `western/foundations.md`: 西占心理语言和时间敏感项边界。
- `western/classical-anchors.md`: Ptolemy / Lilly 等公版来源的术语边界。
- `western/planets-aspects-houses.md`: 行星、相位、宫位和专题对应。
- `mbti/behavior-language.md`: MBTI 作为行为语言层的使用边界。
- `liuyao/question-reading.md`: 六爻问事的证据层级和报告写法。
- `liuyao/classical-anchors.md`: 从《增删卜易》等入口提炼出的六爻方法锚点。
- `xiaoliuren/quick-timing.md`: 小六壬短期提示的弱信号边界。
- `writing/reader-rich-report.md`: 付费报告写法、第二人称、丰富版与简洁版规则。
