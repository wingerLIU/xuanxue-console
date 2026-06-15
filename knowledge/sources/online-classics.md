# Online Classics Source Register

last_checked: `2026-06-12`

这个文件记录联网核验过的典籍入口。它不是客户报告素材库；报告不能直接复制网页文字，只能引用已整理进规则卡的原则。

## 使用规则

- 优先使用公开、可核验、可长期访问的入口，例如 Wikisource、Project Gutenberg、Internet Archive、Wikimedia Commons、馆藏机构数字档案。
- 机器核验优先登记 HTML 文件页、书目页或影像页；大体量 PDF 直链可以作为人工附属证据，但不优先作为必检 URL。
- 典籍状态默认仍为 `candidate`，除非已经被整理为规则卡并通过审计。
- 如果页面提示“未校对”“来源可靠性不明”，必须在 `limits` 中保留边界。
- 不把单句古文直接当现代判断；必须转成“适用范围 + 限制 + 现代翻译 + 报告写法”。

## 八字

| source_id | 在线入口 | 核验结果 | 可提炼主题 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-BAZI-ZIPING-ZHENQUAN` | Wikimedia Commons PDF: https://upload.wikimedia.org/wikipedia/commons/f/fe/NLC416-11jh010455-35296_%E5%AD%90%E5%B9%B3%E7%9C%9F%E8%A9%AE.pdf ; ctext: https://ctext.org/wiki.pl?if=gb&res=631975 | 找到《子平真诠》公开扫描入口和 ctext 条目；Wikisource 搜索结果易混到非命理《真诠》 | 月令、格局、用神、相神、成败层次 | PDF 和 ctext 仍需人工校对版本；不直接用搜索结果标题，不复制古文断语 |
| `SRC-BAZI-DITIAN-SUI` | Wikisource: https://zh.wikisource.org/wiki/%E6%BB%B4%E5%A4%A9%E9%AB%93 ; `滴天髓阐微`: https://zh.wikisource.org/wiki/%E6%BB%B4%E5%A4%A9%E9%AB%93%E9%97%A1%E5%BE%AE | 找到正文和阐微入口 | 三元、五行气势、天干性质、顺逆、寒暖燥湿 | 适合原则提炼，不做单句硬断 |
| `SRC-BAZI-QIONGTONG-BAOJIAN` | Wikisource: https://zh.wikisource.org/wiki/%E7%A9%B7%E9%80%9A%E5%AE%9D%E9%89%B4 | 找到正文入口 | 五行总论、月令调候、寒暖燥湿 | 调候参考，不覆盖完整命局结构 |
| `SRC-BAZI-SANMING-TONGHUI` | Wikisource: https://zh.wikisource.org/zh-hans/%E4%B8%89%E5%91%BD%E9%80%9A%E6%9C%83 | 找到总入口和分卷 | 十神、格局、神煞、古法汇编 | 资料杂，流派差异大；神煞只作辅助 |
| `SRC-BAZI-YUANHAI-ZIPING` | Wikisource: https://zh.wikisource.org/wiki/%E6%B7%B5%E6%B5%B7%E5%AD%90%E5%B9%B3 | 找到目录入口 | 日为主、月令、太岁、大运、格局早期框架 | 古法和今法差异大；不直接照搬断语 |
| `SRC-BAZI-SHENFENG-TONGKAO` | Wikimedia Commons PDF: https://upload.wikimedia.org/wikipedia/commons/4/4c/NLC416-13jh001619-43305_%E7%A5%9E%E5%B3%B0%E9%80%9A%E8%80%83.pdf ; ctext: https://ctext.org/wiki.pl?chapter=739505&if=gb&remap=gb | 找到公开扫描；ctext 文本入口可能触发人机验证 | 病药、格局取用、组合判断、枯旺四病等 | 已拆成方法规则卡；只提炼推理框架，不复制断语 |

## 紫微斗数

| source_id | 在线入口 | 核验结果 | 可提炼主题 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-ZIWEI-DOUSHU-QUANSHU` | Wikisource: https://zh.wikisource.org/wiki/%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8%E5%85%A8%E6%9B%B8 ; 日本国立公文书馆影像: https://www.digital.archives.go.jp/img/4468520 | 找到总入口和馆藏影像；国立公文书馆条目标出《新鋟希夷陳先生紫微斗数全書》公开影像 | 太微赋、诸星问答、安身命、十二宫、行限 | 古文吉凶语气强，报告必须现代化；影像用于校验版本和目录，不直接复制断语 |
| `SRC-ZIWEI-FU-TEXTS` | `紫微斗数全书/全览`: https://zh.wikisource.org/wiki/%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8%E5%85%A8%E6%9B%B8/%E5%85%A8%E8%A6%BD | 找到太微赋、骨髓赋等内容入口 | 先命身、再格局、再限运；不一例而断 | 只能作象意和方法原则，不复制宿命断语 |
| `SRC-ZIWEI-DOUSHU-QUANJI` | 学术书目线索：成大中文学报 PDF https://chinese.ncku.edu.tw/var/file/142/1142/img/4253/7502.pdf ; Airiti 参考文献页 https://www.airitilibrary.com/Article/Detail/P20170720001-202112-202202230007-202202230007-33-74 ; 東洋文庫漢籍検索结果 https://www.toyo-bunko.org/open/KansekiQueryResult.php?ORDERBY1=&UNIT=20&andor=1&iPage=3743&iTotal=80861&navizonestart=375&searchtype=keyword&sw1= ; KOSTMA 搜索结果 https://kostma.aks.ac.kr/dataSearch/dataSearchList.aspx?cateQ=aksBook&curPage=704&pageSize=20&query=&sType=&sort=aks_%EA%B8%B0%EB%B3%B8_%EC%9E%91%EC%84%B1%EC%8B%9C%EA%B8%B0_s | 找到《新刊希夷陈先生紫微斗数全集》等书目、版本考辨和馆藏目录线索，未找到稳定公开全文 | 版本流变、序文真伪、与《全书》的先后关系 | 只能作为研究 backlog 和非晋升边界，不进入报告强判断；付费、网盘、Scribd、论坛压缩包、博客摘段类页面不晋升 |

## 六爻

| source_id | 在线入口 | 核验结果 | 可提炼主题 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-LIUYAO-ZENGSHAN-BU` | Wikisource: https://zh.wikisource.org/wiki/%E5%A2%9E%E5%88%AA%E5%8D%9C%E6%98%93 | 找到总入口；页面提示部分排版/校对边界 | 用神、元神、忌神、仇神、动变、旺衰 | 流派细节需复核；脚本输出只是骨架 |
| `SRC-LIUYAO-BUSHI-ZHENGZONG` | Wikisource: https://zh.wikisource.org/zh-hant/%E5%8D%9C%E7%AD%AE%E6%AD%A3%E5%AE%97%EF%BC%88%E6%B2%B3%E6%BD%9E%E6%AD%A6%E5%AD%90%E9%BE%84%E6%A0%A1%E6%9C%AC%EF%BC%89 ; ctext: https://ctext.org/wiki.pl?chapter=889452&if=gb | 找到总入口、卷目和 ctext 条目；Wikisource 页面有校对可靠性提示 | 用神、原神、忌神、仇神、飞伏、旬空月破、十八论、诸占分类 | 只能提炼问事方法和术语边界；不把古代诸占断语直接转成现代结论 |
| `SRC-LIUYAO-HUOZHULIN` | Wikisource: https://zh.wikisource.org/wiki/%E7%81%AB%E7%8F%A0%E6%9E%97 | 找到公开文本入口，适合作为火珠林法和纳甲筮法的源流入口 | 以钱代蓍、纳甲、六亲、六神、火珠林法源流 | 古代婚姻、疾病、性别等断语不可直接进入报告；只作术语和源流材料 |
| `SRC-LIUYAO-YIJING` | Wikisource `周易`: https://zh.wikisource.org/zh-hans/%E5%91%A8%E6%98%93 ; `周易正义`: https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%AD%A3%E7%BE%A9 | 找到稳定入口 | 卦爻基础语言、阴阳变化、易传解释传统 | 不直接复制卦辞断现代事项；六爻实务仍以具体问事规则为准 |

## 小六壬

| source_id | 在线入口 | 核验结果 | 可提炼主题 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-XIAOLIUREN-DUONENG-BISHI` | Wikisource `多能鄙事/卷之八`: https://zh.wikisource.org/zh-hans/%E5%A4%9A%E8%83%BD%E9%84%99%E4%BA%8B/%E5%8D%B7%E4%B9%8B%E5%85%AB | 目录明确列出“小六壬课”，正文内容多以图像/扫描呈现 | 小六壬作为轻量课法的古籍入口 | 只登记存在性和目录层级；不从图像页强提细断规则 |
| `SRC-XIAOLIUREN-XIEJI-BIANFANG` | Wikisource `欽定協紀辨方書`: https://zh.wikisource.org/wiki/%E6%AC%BD%E5%AE%9A%E5%8D%94%E7%B4%80%E8%BE%A8%E6%96%B9%E6%9B%B8_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29 ; Wikimedia Commons scan: https://upload.wikimedia.org/wikipedia/commons/0/04/NLC892-GBZX0301011955-284762_%E6%AC%BD%E5%AE%9A%E5%8D%94%E7%B4%80%E8%BE%A8%E6%96%B9%E6%9B%B8_%E4%B8%89%E5%8D%81%E5%85%AD%E5%8D%B7_%E7%AC%AC1%E5%86%8A.pdf | 找到公开总入口和扫描件线索，扫描检索提示“乃俗传小六壬之留连赤口日”等源流信息 | 留连、赤口、小吉等短期择日/状态词的源流边界 | 只作源流线索；现代道传课、商品页、网盘资料不晋升 |

## 西洋占星

| source_id | 在线入口 | 核验结果 | 可提炼主题 | 使用边界 |
| --- | --- | --- | --- | --- |
| `SRC-WESTERN-PTOLEMY-TETRABIBLOS` | Project Gutenberg: https://www.gutenberg.org/ebooks/70850 ; LacusCurtius guide: https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Ptolemy/Tetrabiblos/home.html | 找到公版电子书和版本说明 | 古典占星框架、行星性质、四元素/天气式思路 | 不直接套古典宿命判断 |
| `SRC-WESTERN-LILLY-CHRISTIAN-ASTROLOGY` | Wikisource: https://en.wikisource.org/wiki/Christian_Astrology ; Internet Archive scan: https://archive.org/details/b30338724 | 找到文本和扫描入口 | 宫位、行星力量、卜卦和本命传统 | 用于术语理解，不替代本项目出生盘文本 |
| `SRC-WESTERN-MODERN-PSYCHOLOGICAL` | 已迁移至 `knowledge/sources/modern-references.md` | 现代资料不放在典籍表里 | 心理语言、咨询表达 | 只作现代综合和边界说明 |

## 下一步可继续核验

- 《紫微斗数全集》稳定公开全文入口；当前只有学术书目与馆藏目录，不晋升正文依据。
- 小六壬现代“道传”体系、手抄本和商品页资料暂不晋升；除非找到可核验版本和清晰授权。
- MBTI 官方或学术边界来源。
