# Xuanxue Console

[![verify](https://github.com/wingerLIU/xuanxue-console/actions/workflows/verify.yml/badge.svg)](https://github.com/wingerLIU/xuanxue-console/actions/workflows/verify.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

`xuanxue-console` 是一个 Codex Skill 项目，也是一个本地运行的玄学排盘与长文生成实验。

它的核心思路很简单：**排盘交给脚本，解释交给 Codex，事实和反馈都留痕**。八字、紫微斗数、西洋占星、MBTI、六爻、小六壬等信息会先变成可复查的 JSON / Markdown，再用于生成更像人读文章的分析文本。

这个项目更适合学习、研究、个人实验和 Codex Skill 工作流参考，不鼓励直接包装成付费算命产品或批量商业服务。

## What It Does

- 生成八字、紫微斗数、西洋占星、MBTI、六爻、小六壬等结构化结果。
- 把排盘结果保存成可复查的 facts，方便后续追问，不需要每次重新手算。
- 支持单盘、合盘、丰富版、简洁版等长文生成流程。
- 用知识库、模板和质量检查减少“凭感觉写”“串案”“车轱辘话”。
- 把真实反馈先做去隐私复盘，再决定是否进入知识库。

## Quick Start

```powershell
python -m pip install -r scripts\requirements.txt

python scripts\xuanxue_console.py bazi --solar 1991-08-15 --time 01:30 --gender 男 --as-of 2026-06-12

python scripts\xuanxue_console.py western --solar 1991-08-15 --time 01:30 --tz-offset 8

python scripts\xuanxue_console.py combo --solar 1991-08-15 --time 01:30 --gender 男 --western
```

如果你把它当 Codex Skill 使用，优先看 [SKILL.md](SKILL.md)。用户只需要用自然语言说明想看什么，并提供必要信息；Codex 负责调用脚本、读取知识库、生成解释。

## Install As A Codex Skill

```powershell
git clone https://github.com/wingerLIU/xuanxue-console.git $env:USERPROFILE\.codex\skills\xuanxue-console
```

也可以 clone 到任意目录后，把整个项目目录复制到 `%USERPROFILE%\.codex\skills\xuanxue-console`。

## How Reports Are Written

这个 Skill 默认追求的是“能读、能复查、能改进”，不是把玄学术语堆满一篇文章。

- 先说人话结论，再解释命理依据。
- 有证据就说清楚倾向，不把每个问题都写成两边都可以。
- 四柱、大运、紫微、西占和卦象都由脚本生成，模型不手算。
- 脚本路径、JSON 路径、坐标口径、验证命令等内部过程不写进正文。
- 出生时间不确定时，会把稳定项和敏感项分开写。
- 合盘会新建独立 relationship run，不直接在旧稿上续写。
- 反馈先做去隐私复盘，确认有复用价值后再进入知识库。

手机阅读版也尽量克制：暖纸、深字、少色、无卡片，重点只用加粗，不做花哨高亮。

## Project Position

这个项目开源出来主要是为了学习交流和个人研究。它参考、学习了很多公开项目和资料的思路，因此不希望被简单换壳、批量包装成商业算命服务。

你可以 fork、研究、改造、自己玩，也欢迎提出 issue 或 PR。若要做公开展示、二次发布或商业化尝试，请认真处理来源、隐私、客户边界和内容风险，不要把它当成可以直接卖给用户的成品系统。

## Privacy Boundary

这个仓库可以公开分享，但不展示真实 case。

- 仓库内只保留通用代码、规则卡、模板、测试 fixture、流程文档和去隐私机制复盘。
- 真实客户资料、出生信息、原始对话、报告正文、截图、PDF、HTML、ZIP 和 run-local JSON 不进入仓库。
- 去隐私复盘只保留可复用机制，不保留客户姓名、生日、城市、本机路径或交付原文。
- 展示图、报告截图和样例成果应放在单独的 showcase/export 目录或独立仓库中，发布前再人工确认隐私边界。

## Repo Map

- [SKILL.md](SKILL.md): Codex Skill 入口和完整 agent 工作流。
- [scripts/](scripts/): 排盘、长文生成、打包、校验和复盘脚本。
- [knowledge/](knowledge/): 来源索引、规则卡、推断合同和写作规则。
- [templates/](templates/): 单盘、合盘、丰富版和简洁版模板。
- [service/](service/): 流程笔记、资料表、SOP、质量闸门和成本核算笔记。
- [EXTERNAL_ARTIFACTS.md](EXTERNAL_ARTIFACTS.md): 为什么真实 run 和交付物必须放在仓库外部。
- [CONTRIBUTING.md](CONTRIBUTING.md): 贡献方式、隐私边界和不应提交的内容。
- [CHANGELOG.md](CHANGELOG.md): 公开版本和重要更新记录。
- [docs/release-process.md](docs/release-process.md): 轻量发布流程。
- [docs/showcase.md](docs/showcase.md): 公开展示图和样例截图的边界建议。
- [.github/workflows/verify.yml](.github/workflows/verify.yml): GitHub Actions 验证流程。

## Validate

```powershell
.\verify.cmd
```

这个命令会跑项目卫生检查、来源/知识库审计、复盘审计和单元测试。

## Contact

如果你想交流这个项目、聊 Codex Skill、AI 工作流或玄学知识库建设，可以加微信：

```text
a249256088
```

## Author

LiuJiang

## Disclaimer

本项目用于传统文化、自我观察和 AI 工作流研究，不替代医疗、法律、投资、婚恋决定或人生重大决策。

License: MIT
