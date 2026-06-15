# 合盘简洁版模板

这个模板用于关系合盘的快速阅读版本，不替代 `templates/relationship-rich-template.md`。它默认第三人称，适合双方都可能阅读，也适合手机转发。

## 用途

- 给已经有 rich 合盘事实和长文的 run 生成简洁版。
- 目标是 6500-9500 字符，读完成本低，但仍然保留八字、西占、MBTI、现实关系状态和未来节奏的关键锚点。
- 不写脚本路径、JSON 路径、执行命令、截图来源、内部验收或“本报告按照”这类过程文字。
- 不把合盘写成找问题清单；先写牵引力、互补价值和可经营处，再写磨合点和具体做法。

## 推荐结构

### 合盘总评

先给一句明确评级，必须保留双方对象和合盘属性，例如：

```text
<甲>与<乙>合盘：强牵引互补缘，越懂越入心
```

这只是示例，不是所有合盘的固定标题。冒号后的评级金句必须根据本组事实改写，既要积极可读，也不能把张力硬写成同一种“强牵引”。

写 3-5 段：这段关系最抓人的地方、为什么容易入心、现实里最需要承接什么。

### 牵引与互补

按 `relationship_mode` 写牵引与互补：`romantic_language_supported=true` 时可以写身体吸引、聊天火花、审美/情绪/判断的互补；合作、朋友、同事或未知关系只写亲近感、信任感、互动距离和协同气质。术语只作短锚点，例如日主合冲生克、金星火星、月亮互动、MBTI 语言差异。

### 容易误读的地方

写 3-4 个真实相处场景：距离状态、回复速度、确认感、表达方式、主动与回应。标题和段落不要写成“虽然但是”的压力感。

### 事业、家庭、财富与精力

每个方向 1-2 段即可。只写合作可能、家庭感、见面成本/资源投入、作息压力和恢复方式；不要断定一定共事、一定结婚、一定家庭介入或具体金钱安排。

### 未来两到五年

按阶段写，不做绝对事件。重点是关系主题、现实议题、可经营动作。

### 最后给双方的话

结尾要有建设性关系评语：这段关系值得如何经营，彼此最该珍惜什么，最该少用什么方式消耗对方。

## 写作规则

- 正文默认第三人称，用 facts 里的双方标签称呼，不写“你和<对方>”“你们”。
- 每节至少 1 句可加粗的白话结论，粗体只标读者该记住的判断、场景或动作，不加粗术语清单。
- 加粗不要全部放在每节第一句。
- 至少 5 个白话场景或情景推演，但不要机械编号。
- 白话场景要分布在多个章节，不能集中在开头凑数；简洁版默认至少 2 个章节要出现真实情境。
- 不写“本章/下面会/新增模块/如前所述/验证器/用于测试”等过程或编辑话术。
- 小标题不要写成“需要/必须/不能/不要/避免/警惕/压力”式提醒句；标题先给关系画像，提醒放正文。
- 事业、家庭、财富、精力和亲近/私密相关段落优先读取 `relationship_life_domains`，正文只写允许范围，不推断具体行为、金额、家庭态度、医疗诊断或现实绑定。
- 亲近/私密章节按 `relationship_mode` 分级：`romantic_language_supported=true` 时可以写身体吸引、调情节奏、想靠近、见面后的氛围、安全感和回应感；非恋爱关系只写亲近感、互动距离、信任边界和安全感；不写具体行为细节或频率。
- 现实输入只使用已知关系状态和距离状态，不补线下频率、同居、婚姻、家庭介入、冲突史或稳定程度。
- 结尾保留传统文化与自我观察边界，不替代医疗、法律、投资或重大关系决定。

## 打包命名

源稿：

```text
<RUN_DIR>/drafts/<case>-relationship-concise.md
```

读者交付：

```text
<RUN_DIR>/delivery/<双方名>合盘简洁版.pdf
<RUN_DIR>/delivery/<双方名>合盘简洁版-手机阅读.html
```

manifest 中源稿使用 `relationship_concise_source_markdown`；默认读者交付使用 `relationship_concise_pdf` 和 `relationship_concise_mobile_html`。Markdown/DOCX/ZIP 可按需导出，但不作为默认交付失败项。

推荐命令：

```powershell
python scripts/package_reader_delivery.py <RUN_DIR>\drafts\<case>-relationship-concise.md --output-dir <RUN_DIR>\delivery --basename <双方名>合盘简洁版 --no-subtitle --avoid-locked --json --manifest <RUN_DIR>\case_manifest.json --artifact-prefix relationship_concise
python scripts/package_mobile_html.py <RUN_DIR>\delivery\<双方名>合盘简洁版.md --output <RUN_DIR>\delivery\<双方名>合盘简洁版-手机阅读.html --manifest <RUN_DIR>\case_manifest.json --artifact-key relationship_concise_mobile_html
```
