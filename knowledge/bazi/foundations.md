# Bazi Foundations

source_id: `SRC-BAZI-PROJECT-SYNTHESIS`

八字规则卡的作用，是把脚本 JSON 里的四柱、十神、五行、大运和流年，转成有边界的现代解释。

## BZ-F001 先看结构，不先看单点

- `rule`: 八字解读先看日主、月令、季节气势、透干藏干、地支关系和大运，再看神煞、纳音和单柱象意。
- `source`: `SRC-RUNTIME-LUNAR-PYTHON`, `SRC-BAZI-ZIPING-ZHENQUAN`, `SRC-BAZI-PROJECT-SYNTHESIS`
- `scope`: 出生盘结构、人格底色、事业/财富/关系的承载方式。
- `limits`: 不能只因某个神煞或某个十神就断具体事件。
- `modern_translation`: 先判断这个人靠什么系统运转，再判断哪个议题容易被触发。
- `report_usage`: 写“你不是单纯某种性格，而是某种结构在现实中反复工作”。

## BZ-F002 月令和季节是背景，不是唯一结论

- `rule`: 月令体现出生季节和主气，是判断旺衰、调候和格局的重要入口。
- `source`: `SRC-BAZI-ZIPING-ZHENQUAN`, `SRC-BAZI-QIONGTONG-BAOJIAN`
- `scope`: 五行气候、冷暖燥湿、资源/压力/表达的底色。
- `limits`: 月令不能单独决定人生层次；还要看透干、通根、组合、大运和现实校准。
- `modern_translation`: 月令像环境温度，决定什么能力更容易启动，什么能力需要额外补足。
- `report_usage`: 适合解释“为什么你在某类环境里更顺，在某类环境里更耗”。

## BZ-F003 旺衰不是五行计数游戏

- `rule`: 判断日主强弱不能只数五行个数，要看季节、通根、透干、组合、生克路径和大运配合。
- `source`: `SRC-BAZI-DITIAN-SUI`, `SRC-BAZI-PROJECT-SYNTHESIS`
- `scope`: 喜忌、用神、压力承载、行动方式。
- `limits`: 脚本里的五行数量只能作提示，不能直接推出喜忌。
- `modern_translation`: 能量不是数量，而是是否能被组织起来使用。
- `report_usage`: 写“这里的关键不是某元素多或少，而是能不能形成稳定工作链条”。

## BZ-F004 调候、扶抑、通关要分开

- `rule`: 调候看寒暖燥湿，扶抑看日主承载，通关看冲突能否转换成流动。
- `source`: `SRC-BAZI-QIONGTONG-BAOJIAN`, `SRC-BAZI-DITIAN-SUI`, `SRC-BAZI-PROJECT-SYNTHESIS`
- `scope`: 解释“为什么某类建议有效”：补表达、补规则、补资源、补行动或补边界。
- `limits`: 不把调候简化成颜色、方位或迷信物件。
- `modern_translation`: 调候是环境适配，扶抑是承载能力，通关是把冲突变成流程。
- `report_usage`: 事业建议里可落到流程、作品、沟通、复盘、授权、休息和风险边界。

## BZ-F005 大运流年是触发，不是宿命

- `rule`: 大运提供十年主题，流年提供年度触发；两者只能解释趋势和准备方向，不直接保证具体事件。
- `source`: `SRC-RUNTIME-LUNAR-PYTHON`, `SRC-BAZI-PROJECT-SYNTHESIS`
- `scope`: 过去校准、未来几年趋势、行动窗口。
- `limits`: 未经客户校准，不断“某年必然发财/结婚/出事”。
- `modern_translation`: 大运像长期任务，流年像当年的提醒和压力测试。
- `report_usage`: 用“盘面触发 -> 现实倾向 -> 可校准问题 -> 建议动作”写年份。
