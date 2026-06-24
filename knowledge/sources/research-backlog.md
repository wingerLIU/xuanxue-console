# Research Backlog

last_updated: `2026-06-24`

这个文件记录尚未晋升为运行时知识的典籍/资料缺口。这里的条目不能支撑客户报告强判断。

## 状态口径

- `catalog_found_no_public_fulltext`: 仍是主动研究缺口。只找到目录、书目或馆藏线索，未找到稳定公开全文或可信公开影像。
- `source_found_curated_methods`: 已找到公开入口，并已拆出方法卡；继续留在这里，是因为还缺去隐私案例、反例和人工校准，不能升成 `verified`。
- `source_found_curated_boundary`: 已找到来源线索或边界资料，并已写入规则卡或来源说明；继续留在这里，是为了提醒它只能作弱边界，不能扩成强判断。
- `tradition_placeholder` 类来源必须在这里保留边界说明；它强于凭印象写，但弱于可核验典籍或案例复盘。

看审计结果时，优先看 `active_backlog_source_ids`。`tracked_backlog_source_ids` 表示“已登记、已说明边界，但仍需案例或更强来源后才能升级”。

## RB-001 神峰通考规则卡深加工

- `source_id`: `SRC-BAZI-SHENFENG-TONGKAO`
- `status`: `source_found_curated_methods`
- `needed_for`: 病药、格局取用、组合判断。
- `current_state`: 已找到 Wikimedia Commons PDF；ctext 文本入口可能触发人机验证。已补 `shenfeng-anchors.md` 和 `shenfeng-methods.md`，可用于病药、盖头截脚、动静触发、枯旺损益的现代报告推理。
- `promotion_condition`: 若要升到 `verified`，还需要去隐私案例复盘、反例和人工校准记录；当前只能支撑结构性倾向，不支撑强断语。

## RB-002 紫微斗数全集稳定公开全文

- `source_id`: `SRC-ZIWEI-DOUSHU-QUANJI`
- `status`: `catalog_found_no_public_fulltext`
- `needed_for`: 星曜组合、四化材料、流派差异对照。
- `current_state`: 找到成大中文学报/Airiti 对《紫微斗数全集》版本与书目的引用，東洋文庫/KOSTMA 可证馆藏目录；另找到日本国立公文书馆《新鋟希夷陳先生紫微斗数全書》影像入口，已作为 `SRC-ZIWEI-DOUSHU-QUANSHU` 补充来源。2026-06-24 复查公开入口，仍未找到可长期访问、可公开核验的《全集》全文；私人整理站、商品页、Scribd、网盘和论坛压缩包仍不作为机器注册主来源。
- `latest_recheck`: 2026-06-24 只确认“未找到可晋升公开全文”，不新增 source-register URL，不拆新规则卡。
- `promotion_condition`: 只有找到稳定公开全文、可信公开扫描或馆方授权影像后，才能更新 source register 并拆规则卡；当前只能进入 `quanshu-vs-quanji-boundary.md` 作非晋升边界。

## RB-003 小六壬可靠古籍来源

- `source_id`: `SRC-XIAOLIUREN-TRADITION`, `SRC-XIAOLIUREN-DUONENG-BISHI`, `SRC-XIAOLIUREN-XIEJI-BIANFANG`
- `status`: `source_found_curated_boundary`
- `needed_for`: 小六壬源流、宫位/课法差异、传统断法边界。
- `current_state`: 已登记《多能鄙事》卷八“小六壬课”目录入口，以及《钦定协纪辨方书》/扫描件中小六壬、留连、赤口、小吉等源流线索；现代课程页、商品页、网盘和 Scribd 不晋升。
- `promotion_condition`: 当前只能支撑“弱信号、短期提示、不得重大决策”的边界。若要细化六宫断法、道传体系或课例，需要另找可核验版本并拆成规则卡。

## RB-004 MBTI 来源边界

- `source_id`: `SRC-MBTI-MODERN-TYPOLOGY`
- `status`: `source_found_curated_boundary`
- `needed_for`: MBTI 作为行为语言层的边界和免责声明。
- `current_state`: 已登记 Myers-Briggs 官方偏好说明和 NCBI/官方用途边界入口。
- `promotion_condition`: 后续若强化 MBTI，只能补行为偏好和误用边界，不补测试题、不做诊断、不做职业/婚恋预测。
