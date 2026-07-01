# 流月流日行动节奏报告模板

source_id: `SRC-PROJECT-FLOW-TIMING-TEMPLATE`

> 用途：把八字 `--as-of` 能算出的流年、流月、流日，转成未来 30 天、60 天、两个月或指定日期段的每日行动报告。主交付是 HTML，Markdown 作为源稿和审稿稿。

## 核心定位

`flow_timing_report` 不是“流月流日解释”，而是“每天能看一眼的行动节奏表”。

它必须回答：

```text
今天就看这件事。
```

不要把报告写成命理术语说明，也不要把每日建议写成换个人也能用的抽象标签。

## 固定结构

### 一句话总判断

用 1-3 句写清这个时间段的主轴。必须同时落到：

- 当前大运/流年/流月差异。
- 本 case 的现实场景。
- 这段时间最该做和最不该做的动作。

示例方向：

```text
这 45 天不是让你扩大摊子，而是把已经开口的合作、报价、责任和小闭环压成可执行条款。
```

### 未来几段流月差异

不要写“都要注意合作、注意沟通”。每个流月必须回答：

- 这个月和上个月哪里不同。
- 适合哪类动作。
- 不适合哪类动作。
- 这个 case 应该落到哪个现实场景。

示例：

```text
- 甲午尾段：别在火气里认领新锅；先把已经在跑的闭环收住。
- 乙未月：把人情、钱、责任翻译成条款；熟人合作不能只靠感觉。
- 丙申月：只跑小闭环，不搞大改革；用试运行数据换下一步授权。
```

### 重点日期

挑出 5-12 个重点日。每个重点日写：

```text
日期：
流月/流日：
今天就看这件事：
现实动作：
避坑：
```

### 每日表

每日表至少包含：

| 日期 | 流月 | 流日 | 今天就看这件事 | 现实动作 | 盘面触发 |
| --- | --- | --- | --- | --- | --- |

每天都要有动作，不要只写“注意”“适合”“谨慎”。

可以写：

- 别在火气里认领新锅。
- 把人情翻译成条款。
- 只跑小闭环，不搞大改革。
- 高冲突日，只谈事实。
- 谈钱谈资源，别谈感觉。
- 不要在群里临时拍大板。
- 没讲清的，不进执行月。

不要写：

- 结构排雷。
- 资源谈判。
- 压力落地。
- 注意沟通。
- 适合推进。
- 谨慎合作。

## Case 指纹

开写前先列出至少 5 个 case-specific 指纹。它们必须自然进入总判断、流月差异、重点日期和每日表。

例如 liujiang：

- OPC
- Liujiang OS
- Agent 项目包
- 团队训练
- 报价、合作、回款、ROI
- 对上汇报
- 不替别人兜底
- 小闭环试运行

如果换成另一个人也成立，判定失败。

## 使用边界

- 流年和流月写节奏，不写绝对结果。
- 流日只用于已有明确事项的短窗口，不替代现实准备。
- 不写“大桃花、大机会、大贵人、大转折”这类泛化刺激词。
- 不替代医疗、法律、投资、婚恋或重大人生决定。
- 出生时间、真太阳时、时辰边界不稳时，流月流日只写倾向和待校准。

## 验收

推荐命令：

```powershell
python scripts\build_flow_timing_report.py --facts-json <RUN_DIR>\data\<case>-combo.json --start 2026-07-02 --days 45 --case-keyword OPC --case-keyword 小闭环 --case-keyword 报价 --case-keyword 对上汇报 --case-keyword Agent项目包 --output-md <RUN_DIR>\drafts\<case>-flow-timing.md --output-html <RUN_DIR>\delivery\<case>-flow-timing.html
python scripts\validate_flow_timing_report.py <RUN_DIR>\drafts\<case>-flow-timing.md --case-keyword OPC --case-keyword 小闭环 --case-keyword 报价 --case-keyword 对上汇报 --case-keyword Agent项目包
python scripts\validate_flow_timing_report.py <RUN_DIR>\delivery\<case>-flow-timing.html --case-keyword OPC --case-keyword 小闭环 --case-keyword 报价 --case-keyword 对上汇报 --case-keyword Agent项目包
```

验收重点：

- 每天都有“今天就看这件事”和“现实动作”。
- 随机抽 10 天，不能换个人也能用。
- 至少命中 5 个 case-specific 词；如果用户只提供少于 5 个，先补问背景。
- 不出现“结构排雷、资源谈判、压力落地、注意沟通、适合推进、谨慎合作”等抽象标签。
- 不出现“大桃花、大机会、大贵人、大转折”等泛化刺激词。
