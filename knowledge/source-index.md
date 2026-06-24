# Source Index

这个文件是知识库的来源地图。它只记录来源、状态、适用范围和边界，不粘贴大段原文，也不存客户案例。

## 状态说明

- `candidate`: 候选来源，尚未转成规则卡；只能启发，不直接支撑强判断。
- `curated`: 已转成局部规则卡；可以支撑“倾向/结构性判断”，但仍需边界说明。
- `verified`: 已经有稳定规则、反例和案例校准；可以支撑较强判断。
- `deprecated`: 不再作为默认依据。

## 使用层级

1. `calculation_runtime`: 排盘和天文/历法计算来源。
2. `classical_text`: 传统经典或流派材料。
3. `modern_reference`: 现代整理、教材、心理语言或咨询写法。
4. `project_rule`: 本项目沉淀出的写作、校验和风险控制规则。
5. `case_retrospective`: 去隐私、人工确认后的案例复盘。

任何付费报告里的判断，都不能只写“书上说”。必须落到：脚本事实、规则卡、适用范围、限制条件和现实翻译。

联网核验过的典籍入口统一登记在 `knowledge/sources/online-classics.md`。机器可读来源对象统一登记在 `knowledge/sources/source-register.json`。`source-index.md` 负责来源 ID 和使用边界；`online-classics.md` 负责具体 URL、核验状态和待补缺口；`source-register.json` 负责让脚本检查每个来源是否有类型、状态、证据模式、入口、限制和晋升目标。

## 计算运行时来源

| source_id | 来源 | 状态 | 适用范围 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-RUNTIME-LUNAR-PYTHON` | `lunar-python` | curated | 公历/农历转换、干支、十神、纳音、大运等八字结构化事实 | 依赖库版本和输入精度；节气/真太阳时边界案例需额外披露不确定性 |
| `SRC-RUNTIME-IZTRO-PY` | `iztro-py` | curated | 紫微命盘、宫位、星曜、四化、大限粗定位 | 大限定位按脚本口径，不等同人工流派精断 |
| `SRC-RUNTIME-EPHEM` | `ephem` | curated | 西洋占星行星落座、上升/天顶、基础天文位置 | 宫位和轴线对出生时间/地点敏感；未给经纬度时不得写死 |

## 八字来源

| source_id | 来源 | 状态 | 适用范围 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-BAZI-ZIPING-ZHENQUAN` | 《子平真诠》 | candidate | 格局、月令、成败层次、用神意识 | 已登记公开扫描和 ctext 入口；不直接照搬古文断语，需转成现代场景和校准问题 |
| `SRC-BAZI-DITIAN-SUI` | 《滴天髓》 | candidate | 五行气势、寒暖燥湿、格局精神 | 适合提炼原则，不适合单句硬断人生事件 |
| `SRC-BAZI-QIONGTONG-BAOJIAN` | 《穷通宝鉴》 | candidate | 调候、月令气候、寒暖燥湿 | 只能作为调候参考，不覆盖完整命局结构 |
| `SRC-BAZI-SANMING-TONGHUI` | 《三命通会》 | candidate | 神煞、格局、古法材料汇编 | 信息杂，需标注流派差异；神煞不得覆盖主结构 |
| `SRC-BAZI-YUANHAI-ZIPING` | 《渊海子平》 | candidate | 十神、格局、神煞早期框架 | 需与现代案例校准，避免恐吓式断语 |
| `SRC-BAZI-SHENFENG-TONGKAO` | 《神峰通考》 | curated | 病药、格局取用、组合判断 | 已拆成方法卡；仍不得复制古籍断语或脱离脚本事实强断 |
| `SRC-BAZI-PROJECT-SYNTHESIS` | 本项目八字规则卡 | curated | 十神现实翻译、结构读法、流年写作边界 | 属于现代综合，不冒充经典原文 |

## 紫微来源

| source_id | 来源 | 状态 | 适用范围 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-ZIWEI-DOUSHU-QUANSHU` | 《紫微斗数全书》 | candidate | 星曜、宫位、格局基础 | 已登记 Wikisource 与日本国立公文书馆影像入口；单星单宫不得直接定吉凶 |
| `SRC-ZIWEI-DOUSHU-QUANJI` | 《紫微斗数全集》 | candidate | 星曜组合、四化材料、版本流变 | 已找到学术书目和馆藏目录线索，未找到稳定公开全文；不得支撑强判断 |
| `SRC-ZIWEI-FU-TEXTS` | 太微赋、骨髓赋等赋文 | candidate | 星曜象意和格局语言 | 只能作象意来源，需现代化解释 |
| `SRC-ZIWEI-PROJECT-SYNTHESIS` | 本项目紫微规则卡 | curated | 命身、宫位、四化、大限的报告读法 | 属于现代综合，不做单星宿命判断 |

## 西洋占星来源

| source_id | 来源 | 状态 | 适用范围 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-WESTERN-PTOLEMY-TETRABIBLOS` | Ptolemy, `Tetrabiblos` | candidate | 古典占星基础框架、行星性质 | 不直接套古典宿命断法 |
| `SRC-WESTERN-LILLY-CHRISTIAN-ASTROLOGY` | William Lilly, `Christian Astrology` | candidate | 宫位、行星力量、卜卦传统 | 用于术语理解，不替代本项目出生盘文本 |
| `SRC-WESTERN-MODERN-PSYCHOLOGICAL` | 现代心理占星资料 | curated | 心理语言、关系表达、自我观察 | 只作象征性自我反思和咨询语言，不作为科学人格测评 |
| `SRC-WESTERN-SCIENTIFIC-BOUNDARY` | 现代科学边界资料 | curated | 西占预测力、人格测量和科学性边界 | 只用于限制用途，不用于生成占星判断 |
| `SRC-WESTERN-PROJECT-SYNTHESIS` | 本项目西占规则卡 | curated | 行星/宫位/相位的现实语言和时间敏感边界 | 只作心理与表达层补充，不覆盖八字/紫微事实 |

## MBTI 来源

| source_id | 来源 | 状态 | 适用范围 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-MBTI-MODERN-TYPOLOGY` | Myers-Briggs 官方偏好说明与现代人格类型资料 | curated | 偏好语言、沟通风格、决策倾向 | 只作行为偏好，不作为命理证据、能力测量或诊断 |
| `SRC-MBTI-CRITICAL-BOUNDARY` | MBTI 独立边界资料 | candidate | 可靠性、预测力和误用风险边界 | 只用于限制用途，不用于生成性格断语 |
| `SRC-MBTI-PROJECT-SYNTHESIS` | 本项目 MBTI 行为语言规则卡 | curated | 把 MBTI 用作报告里的表达/沟通/动机补充层 | 不能覆盖脚本命盘事实；用户未提供类型时不脑补 |

## 六爻与小六壬来源

| source_id | 来源 | 状态 | 适用范围 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-LIUYAO-YIJING` | 《易经》及卦爻基础传统 | candidate | 卦象、爻位、阴阳变化的基础语言 | 不直接复制古辞作现代结论 |
| `SRC-LIUYAO-ZENGSHAN-BU` | 《增删卜易》 | candidate | 用神、世应、动变、六亲等传统六爻判断材料 | 流派细节需人工复核；脚本只输出骨架 |
| `SRC-LIUYAO-BUSHI-ZHENGZONG` | 《卜筮正宗》 | candidate | 用神、原神、忌神、仇神、飞伏、旬空月破和十八论 | 公开入口可核验，但页面校对边界需保留；只能支撑问事结构，不支撑古文式硬断 |
| `SRC-LIUYAO-HUOZHULIN` | 《火珠林》 | candidate | 以钱代蓍、纳甲、火珠林法源流和六爻术语 | 只作源流和术语材料；古代社会语境断语不得直接进入现代报告 |
| `SRC-LIUYAO-PROJECT-SYNTHESIS` | 本项目六爻问事规则卡 | curated | 把六爻用于具体问题的短期趋势和校准 | 只能回答当前问题，不覆盖出生盘 |
| `SRC-XIAOLIUREN-DUONENG-BISHI` | 《多能鄙事》卷八“小六壬课” | candidate | 小六壬作为古籍目录中独立课法的存在性入口 | 现有公开页主要提供目录/图像入口，不直接提炼细断规则 |
| `SRC-XIAOLIUREN-XIEJI-BIANFANG` | 《钦定协纪辨方书》小六壬/六曜源流线索 | candidate | 留连、赤口、小吉等择日式源流校验 | 只作源流和边界，不等同本项目起课细断 |
| `SRC-XIAOLIUREN-TRADITION` | 小六壬民间起课传统 | candidate | 短期时机、状态和轻量提示 | 作为传统统称使用；强于无来源印象，但仍是弱信号体系 |
| `SRC-XIAOLIUREN-PROJECT-SYNTHESIS` | 本项目小六壬规则卡 | curated | 快速问事、当天/短期状态提示 | 仅作弱信号，优先级低于六爻和出生盘 |

## 写作和服务来源

| source_id | 来源 | 状态 | 适用范围 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-PROJECT-INTERPRETATION-GUIDE` | `references/interpretation-guide.md` | curated | 报告结构、证据链、语气、高风险边界 | 项目方法，不是命理经典 |
| `SRC-PROJECT-LONGFORM-TEMPLATE` | `templates/longform-analysis-template.md`; `templates/concise-report-template.md`; `scripts/validate_longform_report.py` | curated | reader-rich 付费报告结构、简洁版结构和机器校验 | 控制交付形态，不产生命理事实 |
| `SRC-PROJECT-QUALITY-GATE` | `service/quality-gate.md`; `scripts/build_fact_archive.py`; `scripts/finalize_case.py`; `scripts/validate_longform_report.py`; `scripts/audit_longform_consistency.py` | curated | 交付前检查、事实复查档案、runtime knowledge context、串案风险、高风险边界 | 质量控制，不产生命理事实 |
| `SRC-PROJECT-WRITING-SYNTHESIS` | `knowledge/writing/reader-rich-report.md`; `templates/concise-report-template.md`; `scripts/validate_longform_report.py` | curated | 付费报告的读者口吻、摘要、场景、简洁版和可读性 | 写作规则必须服务证据，不替代证据 |
| `SRC-PROJECT-TEAM-CAREER-SYNTHESIS` | `knowledge/team-career/README.md`; `service/multi-person-career-synastry-sop.md`; `templates/team-career-synastry-template.md` | curated | 多人事业合盘的团队级 run、商业结构、城市判断、流年流月和复盘采集边界 | 团队判断必须先落到单盘 facts、两两 relationship facts 和现实商业资料，不产生命理事实 |
| `SRC-PROJECT-FENGSHUI-DIRECTION-SYNTHESIS` | `knowledge/fengshui/README.md`; `service/client-intake-form.md`; `templates/longform-analysis-template.md`; `templates/concise-report-template.md` | curated | 方位、空间、城市、居住、办公和轻量开运建议的资料收集、报告结构和使用边界 | 没有现场勘测、罗盘坐向、户型图和长期反馈时，只能作为低风险空间建议和校准问题 |
| `SRC-PROJECT-CASE-RETROSPECTIVE-PROTOCOL` | `knowledge/case-retrospectives/promotion-protocol.md`; `schemas/case_retrospective.schema.json`; `schemas/retrospective_intake.schema.json`; `scripts/create_retrospective_intake.py`; `scripts/create_case_retrospective_candidate.py`; `scripts/promote_case_retrospective.py`; `scripts/audit_case_retrospectives.py` | curated | 案例复盘去隐私、反馈 intake、反例、人工确认和晋升流程 | 只规定自进化流程，不直接产生命理判断 |
| `SRC-PROJECT-CASE-RETROSPECTIVE` | `knowledge/case-retrospectives/` | candidate | 可复用经验、常见误读、客户反馈校准 | 必须去隐私且人工确认后才可晋升 |
| `SRC-PROJECT-COMPLETENESS-AUDIT` | `knowledge/completeness/coverage-matrix.json`; `scripts/audit_source_documentation.py` | curated | 覆盖度、阻塞项、联网资料准入和 goal_complete 判断 | 只做审计和状态控制，不产生命理判断 |
| `SRC-PROJECT-SOURCE-REGISTER` | `knowledge/sources/source-register.json`; `scripts/audit_source_documentation.py` | curated | 每个来源的类型、状态、证据模式、入口、边界、晋升目标和可选联网核验快照 | provenance 控制，不证明具体规则已被案例验证；`source_liveness.json` 只放外部 run |
| `SRC-PROJECT-KNOWLEDGE-CONTEXT` | `scripts/build_knowledge_context.py`; `scripts/create_followup_context.py`; `scripts/create_retrospective_intake.py`; `schemas/retrospective_intake.schema.json`; `knowledge/completeness/retrospective-requirements.json` | curated | 按模块生成本次 case 必读知识文件、来源、blocker、追问上下文、复盘采集计划、机器可读追问库、建议 `target_artifacts` 和外部反馈 intake | 运行上下文控制，不产生命理判断 |

## 联网吸收原则

联网只用于“资料吸收”“典籍核验”和“来源校验”，不得在单个客户报告正文里临时边搜边断。

可接受路径：

1. 外部资料进入研究暂存或人工笔记。
2. 记录来源、摘录范围、可信度和适用边界。
3. 提炼成规则卡。
4. 写入 `knowledge/promotion/knowledge_promotion_manifest.json`。
5. 写入或更新 `knowledge/sources/source-register.json`。
6. 通过 `scripts/audit_source_register.py`。
7. 通过 `scripts/audit_knowledge_base.py`。
8. 通过 `scripts/audit_knowledge_coverage.py`，确认它不会制造未标注的覆盖度幻觉。
9. 之后才能作为报告推断依据。

不接受路径：

- 随机网页直接进入客户报告。
- 没有来源 ID 的断言进入全局知识库。
- 案例原文、截图、出生资料或本机路径进入全局知识库。
