#!/usr/bin/env python3
"""Longform Markdown rendering helpers for xuanxue console reports."""

from __future__ import annotations

from typing import Any


def report_modules(report: dict[str, Any]) -> list[dict[str, Any]]:
    if report.get("module") == "combo":
        modules = report.get("facts", {}).get("modules", [])
        return modules if isinstance(modules, list) else []
    return [report]


def find_report_module(report: dict[str, Any], module_name: str) -> dict[str, Any] | None:
    for item in report_modules(report):
        if item.get("module") == module_name:
            return item
    return None


def short_join(values: list[str], limit: int = 6) -> str:
    cleaned = [str(value) for value in values if value]
    if not cleaned:
        return "待补"
    if len(cleaned) <= limit:
        return "、".join(cleaned)
    return "、".join(cleaned[:limit]) + "等"


def pillar_text(pillars: dict[str, Any]) -> str:
    return "、".join(str(pillars.get(key, "待补")) for key in ["year", "month", "day", "hour"])


def placement_lookup(placements: list[dict[str, Any]]) -> dict[str, str]:
    return {row.get("body", ""): f"{row.get('body', '')}{row.get('sign', '')}" for row in placements}


def render_longform_markdown(report: dict[str, Any], title: str = "") -> str:
    bazi_report = find_report_module(report, "bazi")
    ziwei_report = find_report_module(report, "ziwei")
    western_report = find_report_module(report, "western")
    bazi_facts = bazi_report.get("facts", {}) if bazi_report else {}
    ziwei_facts = ziwei_report.get("facts", {}) if ziwei_report else {}
    western_facts = western_report.get("facts", {}) if western_report else {}

    pillars = bazi_facts.get("pillars", {})
    flow = bazi_facts.get("flow", {})
    current_dayun = flow.get("current_dayun") or {}
    profiles = bazi_facts.get("profiles", {})
    ten_gods = profiles.get("ten_gods", {}).get("combined", {})
    elements = profiles.get("elements", {}).get("stems_plus_hidden", {})
    annual_flows = flow.get("annual_flows", [])
    dayun_rows = bazi_facts.get("dayun", [])

    current_decadal = ziwei_facts.get("current_decadal") or {}
    mutagens = ziwei_facts.get("year_mutagens", [])
    palaces = ziwei_facts.get("palaces", [])
    soul_palace = next((p for p in palaces if p.get("name") == "命宫"), {})
    spouse_palace = next((p for p in palaces if p.get("name") == "夫妻宫"), {})
    wealth_palace = next((p for p in palaces if p.get("name") == "财帛宫"), {})
    career_palace = next((p for p in palaces if p.get("name") == "官禄宫"), {})

    placements = western_facts.get("placements", [])
    placement_map = placement_lookup(placements)
    aspects = western_facts.get("aspects", [])
    moon_phase = western_facts.get("moon_phase", {})
    balance = western_facts.get("balance", {})
    houses = western_facts.get("houses", {}) or {}
    angles = houses.get("angles", {}) or {}
    ascendant = angles.get("ascendant", {}) or {}
    midheaven = angles.get("midheaven", {}) or {}
    mutagen_texts = [
        f"{row.get('star')}化{row.get('mutagen')}在{row.get('palace')}"
        for row in mutagens
        if row.get("star") and row.get("mutagen") and row.get("palace")
    ]
    aspect_texts = [
        f"{row.get('body_a')}{row.get('aspect')}{row.get('body_b')} orb {row.get('orb')}"
        for row in aspects[:6]
        if row.get("body_a") and row.get("aspect") and row.get("body_b")
    ]
    warnings = []
    for item in report_modules(report):
        warnings.extend(item.get("warnings", []))
        warnings.extend(item.get("uncertainties", []))

    title = title or "综合命盘长文初稿"
    solar = bazi_facts.get("solar") or report.get("input", {}).get("solar") or "待补"
    birth_time = report.get("input", {}).get("time") or (bazi_report.get("input", {}).get("time") if bazi_report else "")
    ascendant_text = f"，上升{ascendant.get('display')}" if ascendant.get("display") else ""
    midheaven_text = f"，天顶{midheaven.get('display')}" if midheaven.get("display") else ""
    western_scope = (
        "西占已补入出生地，可参考上升、轴线、整宫制和等宫制宫位；宫位不等同于 Placidus 等精密宫制。"
        if houses
        else "若缺出生地，西占不写上升、宫位、MC/IC 和宫主星。"
    )
    appearance_scope = (
        f"出生地已补入，上升{ascendant.get('sign', '')}和天顶{midheaven.get('sign', '')}可以用于第一印象、风格倾向和职业气质判断；但不要断定身高、脸型和具体五官。"
        if houses
        else "没有出生地时，西占上升和第一宫不能计算，所以不要断定身高、脸型和具体五官。可以从八字、紫微命宫和已知行星落座写外在氛围：偏干净、利落、有距离、有审视感，适合简洁、有线条、有质感的风格。"
    )
    lines = [
        f"# {title}",
        "",
        f"这篇长文先给判断，再用排盘事实做论据。出生信息按公历 `{solar}` `{birth_time or '待补'}` 读取，八字四柱为 `{pillar_text(pillars)}`，日主为 `{bazi_facts.get('day_master', '待补')}`。当前大运为 `{current_dayun.get('gan_zhi', '待补')}`，阶段大约是 `{current_dayun.get('start_year', '待补')}-{current_dayun.get('end_year', '待补')}`。紫微当前大限为 `{current_decadal.get('name', '待补')}`，西占核心落座包括 `{short_join([placement_map.get(name, '') for name in ['太阳', '月亮', '水星', '金星', '火星']])}`{ascendant_text}{midheaven_text}。",
        "",
        f"先说明边界：这是一篇文化与自我观察用途的长文初稿，不替代医学、法律、投资或人生重大决策。排盘事实只作为证据，文章要把证据翻译成小白能读、能校准、能行动的叙述。{western_scope}",
        "",
        "## 判断型摘要：这张盘一句话看懂",
        "",
        "这份长文的读法不是从术语开始，而是从核心矛盾开始：这个人更适合靠规则、专业、信誉和长期交付成事，但要避免只承压、不转化、只学习、不变现。换句话说，命盘里真正值得抓住的不是某个神秘标签，而是一条现实路线：先把能力打磨成标准，再把标准变成作品和收入。",
        "",
        "读者可以先用过去几年校准，再决定未来建议是否值得采纳。一个报告如果不能被真实经历验证，就只能算漂亮话；如果 2020、2024、2026 这些关键年份确实能对上环境变化、关系重谈、项目压力或财务复杂度，那么这条主线的可信度就会更高。",
        "",
        "## 术语翻译：这些词落到现实是什么",
        "",
        "`正官` 可以先理解为规则、责任、职位、名分、考核和外部标准；`印` 可以理解为学习、资质、方法、保护和系统化能力；`食伤` 是表达、作品、传播、复盘和把想法流动出去；`财星` 是客户、资源、收入、关系和现实交换；`七杀` 是竞争、压力、速度、挑战和被迫证明。长文后面的判断都会尽量把这些术语翻译成现实动作。",
        "",
        "所以，当文中说某个阶段官印重，并不是说你只能进体制或只能被规则压住，而是说你更容易在有标准、有授权、有验收的场景里发挥。当文中说需要补水，也不是让你迷信颜色或方位，而是强调表达、沟通、写作、产品化、公开作品和复盘机制。",
        "",
        "## 一、命理：先看这个人的底层发动机",
        "",
        f"命理部分先看日主和月令。这个盘的日主是 `{bazi_facts.get('day_master', '待补')}`，四柱是 `{pillar_text(pillars)}`。十神分布里比较醒目的部分是 `{short_join([f'{k}{v}' for k, v in ten_gods.items()])}`，五行分布里比较醒目的部分是 `{short_join([f'{k}{v}' for k, v in elements.items()])}`。这些不是形容词，而是后面推导性格、事业和关系的证据。",
        "",
        f"如果当前大运已经进入 `{current_dayun.get('gan_zhi', '待补')}`，它会把 `{current_dayun.get('ten_god_gan', '待补')}`、`{current_dayun.get('gan_wuxing', '待补')}`、`{current_dayun.get('zhi_wuxing', '待补')}` 的主题推到台前。普通人读这个，可以先理解成：这十年更强调边界、竞争、专业度、同辈关系和自我判断。真正好的机会，不是让你无限硬扛，而是让你把能力变成标准、流程、作品和价格。",
        "",
        "## 二、紫微：看他把人生重心放在哪里",
        "",
        f"紫微斗数里，命宫在 `{ziwei_facts.get('soul_palace_branch', '待补')}`，命宫主星可读作 `{short_join(soul_palace.get('major_stars', []))}`。身宫在 `{ziwei_facts.get('body_palace_branch', '待补')}`，当前大限落 `{current_decadal.get('name', '待补')}`，主星是 `{short_join(current_decadal.get('major_stars', []))}`。这说明当前阶段的重点不是只看外部成绩，还要看精神秩序、长期信誉、判断系统和内在稳定。",
        "",
        f"这一年四化信号可以先读成：{short_join(mutagen_texts, limit=8)}。四化不是单独断吉凶，而是告诉我们哪些宫位在动。若财帛、夫妻、父母、兄弟这些位置被触发，就要把钱、关系、背书、人际协作一起看。",
        "",
        "## 三、西洋占星：把命盘翻译成心理和表达语言",
        "",
        f"西占部分的核心落座是：{short_join([placement_map.get(name, '') for name in ['太阳', '月亮', '水星', '金星', '火星', '木星', '土星']], limit=10)}。元素分布为 `{balance.get('elements', {})}`，模式分布为 `{balance.get('modalities', {})}`。这部分更适合解释心理语言、关系需求、表达方式和压力反应。",
        "",
        (f"补入出生地后，上升为 `{ascendant.get('display')}`，天顶为 `{midheaven.get('display')}`。上升用于看第一印象、外在风格和进入世界的方式，天顶用于看职业形象、社会目标和被外界验收的方式。" if houses else "若后续补入出生地，西占还可以继续细化上升、轴线、宫位和宫主星。"),
        "",
        f"主要相位里，最靠前的几个是：{short_join(aspect_texts, limit=8)}。出生月相为 `{moon_phase.get('phase', '待补')}`，日月角距约 `{moon_phase.get('sun_moon_angle', '待补')}` 度。用小白语言说，这类结构通常不是完全松弛型，而是容易在责任、关系、表达和自我要求之间反复协调。",
        "",
        "## 四、三套体系合起来看：个性性格怎么推出来",
        "",
        "如果命理强调责任和结构，紫微强调判断和大限课题，西占又强调安全感、关系平衡和表达压力，那么你的性格就不能简单说成内向或外向。你更像是需要结构安全的人：规则清楚、责任清楚、权责清楚时，你会很能承担；环境混乱、要求模糊、角色不明时，你会明显被消耗。",
        "",
        "优点是学习能力、判断力、责任感、系统化能力和长期信誉。短板是容易想太多、输出慢、对不确定性敏感，或者把自己的需求藏在标准和沉默后面。要让这个盘发挥得好，关键不是继续堆更多知识，而是把知识变成作品、流程、报价、案例和可复用资产。",
        "",
        "## 五、别人眼里的你：第一印象比内心更冷静",
        "",
        "刚认识你的人，通常先感受到的是观察感和判断感。你不一定不说话，但不会轻易交底；不一定冷漠，但会先判断环境是否可靠。朋友会觉得你靠谱、能分析问题；合作方会觉得你不好糊弄；亲密关系里的人则可能需要更多具体回应。",
        "",
        "这一段写作时要落到场景：初识、熟悉、合作、亲密关系。读者最容易被这种描述抓住，因为它回答的是“别人到底怎么看我”。",
        "",
        "## 六、外貌与气质：写风格，不硬断五官",
        "",
        f"外貌气质只能谨慎写。{appearance_scope}",
        "",
        "如果命宫、日主和星盘都指向观察、判断、责任和安全感，那么第一印象就不该写成单纯热情甜美，而更像“可靠但不随便亲近，温和但有锋利感”。",
        "",
        "## 七、现实关系全景：感情、朋友、行业、家庭",
        "",
        "感情里，重点写你如何表达安全感、为什么容易用理性代替柔软、伴侣会怎样感受。朋友里，重点写你可靠但不无限兜底，也要写同辈竞争和分账边界。行业里，重点写你如何靠判断、信誉、方法论和作品被看见。家庭里，重点写印星带来的保护、标准、责任和压力。",
        "",
        "这一节要让普通读者觉得“这说的是现实生活里的一个人”，不要只写抽象标签。",
        "",
        "## 八、过去几年：用真实经历校准这份报告",
        "",
    ]
    if annual_flows:
        for row in annual_flows:
            lines.extend(
                [
                    f"### {row.get('year')} 年：{row.get('pillar')}，大运 {row.get('dayun', current_dayun.get('gan_zhi', ''))}",
                    "",
                    f"这一年可以作为校准点。盘面显示 `{row.get('pillar')}` 被当前大运 `{row.get('dayun', current_dayun.get('gan_zhi', ''))}` 承接，适合回看当年是否有学习、项目、关系、合作、财务或环境节奏的变化。若真实经历能对上，后面关于时间线的判断权重可以提高；若完全对不上，就要优先复核出生时间、出生地、真太阳时或排运口径。",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "过去几年建议至少校准 2020、2022、2023、2024、2025、2026。写作时每一年都按“盘面触发 -> 现实倾向 -> 校准问题”展开，不要直接说死事件。",
                "",
            ]
        )

    lines.extend(["## 九、未来几年：趋势不是预言，是准备清单", ""])
    for row in dayun_rows[:6]:
        if not row.get("gan_zhi"):
            continue
        lines.extend(
            [
                f"### {row.get('start_year')}-{row.get('end_year')}：{row.get('gan_zhi')} 运",
                "",
                f"这个阶段的十神是 `{row.get('ten_god_gan', '待补')}`，日主地势为 `{row.get('growth_by_day_master', '待补')}`，自坐为 `{row.get('self_sitting', '待补')}`。写未来趋势时，应把它翻译成事业、财富、爱情和精力管理的准备动作，而不是绝对事件。",
                "",
            ]
        )

    lines.extend(
        [
            "## 十、事业：把判断力变成可交付能力",
            "",
            f"事业要看八字的专业结构、紫微官禄宫 `{short_join(career_palace.get('major_stars', []))}`，以及西占里水星、火星的位置。更适合的路线通常是：复杂问题拆解、产品/策略/咨询、内容方法论、技术方案、运营管理、风控、数据分析和项目制交付。核心不是忙，而是把判断力变成标准、流程和作品。",
            "",
            "## 十一、财富：先清楚，再扩大",
            "",
            f"财富要看八字财星、紫微财帛宫 `{short_join(wealth_palace.get('major_stars', []))}`，以及现实中的报价、合同、回款和分账规则。对这类盘来说，财富更像专业复利，不像纯横财。越想赚钱，越要把规则写清楚。",
            "",
            "## 十二、爱情：关系里要把需求说出来",
            "",
            f"爱情要看八字财星/夫妻结构、紫微夫妻宫 `{short_join(spouse_palace.get('major_stars', []))}`，以及西占里的月亮、金星和火星。这个部分不要写成宿命判断，应该落到安全感、回应、沟通、时间安排、现实责任和边界上。",
            "",
            "## 十三、健康与精力：不做诊断，只看压力管理",
            "",
            "健康部分只谈精力和压力，不做医学诊断。若盘面火土重、责任重、相位压力强，就提醒睡眠、饮水、运动、规律作息、情绪出口和工作边界。真正的建议是不要长期硬扛，有不适要找专业医生。",
            "",
            "## 十四、人际合作：贵人、同侪和分工",
            "",
            "合作部分要同时看紫微贵人星、人际宫位、八字大运里的同侪竞争和现实合同。好的合作不是无条件相信，而是权责、预算、交付、验收和退出机制都清楚。熟人合作尤其要文档化。",
            "",
            "## 十五、学习成长：把输入变成输出",
            "",
            "如果命盘里印星明显，学习和吸收能力通常不差，真正的问题往往是输出慢。建议把每次学习绑定一个可交付物：文章、模板、案例、课程、咨询包、复盘或 SOP。对这类人来说，输出不是额外动作，而是打开格局的动作。",
            "",
            "## 十六、建议：后面应该怎么做",
            "",
            "第一，把专业能力产品化。第二，把合作和钱文档化。第三，固定公开输出。第四，关系里少用判断，多说需求。第五，给身体和情绪留出口。第六，用过去几个关键年份校准这份报告。",
            "",
            "最终结论可以写得很简单：先用规则和专业把自己打磨成器，再用表达、作品和产品化让价值流动出去。",
        ]
    )
    if warnings:
        lines.extend(["", "## 资料缺口与可信度", "", "这份初稿需要保留以下边界：", ""])
        for warning in dict.fromkeys(str(item) for item in warnings):
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"
