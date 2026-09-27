# wild-card

独立的 ComfyUI wildcard 节点。`Wild Card Prompt` 在节点文本框中接收 wildcard prompt，显示展开结果，并只输出一个 populated prompt `STRING`。不需要 model 或 clip 输入。

## 使用

将仓库放在 `ComfyUI/custom_nodes/wild-card`，重启 ComfyUI，在 `wild-card` 分类下添加 `Wild Card Prompt`。输入 `a {red|blue} __flower__` 之类的文本，连接右侧 `populated_prompt` 到需要字符串的节点。

- `populate`：每次排队时展开原始提示词，并更新只读预览。
- `fixed`：忽略原始提示词，使用可编辑的预览文本。
- `reproduce`：使用预览文本一次，然后恢复 `populate`。保存的工作流会保留当次结果。
- `seed`：相同种子与相同词库得到相同结果；“生成后控制”由 ComfyUI 提供。

支持 Impact Pack 的 `{a|b}`、权重、多选及 `__name__` 等 wildcard 语法。本仓库的 `wildcards/` 包含原有的 `color`、`flower`、`jewel`、`jima`、`samples/flower`。绝区零外观词库使用 `__zenless_girls__`，有 37 条默认及官方服装形态，来源与未收录项见[采集记录](docs/zenless-girls-2026-09-27.md)。蔚蓝档案 `__blue_archive_girls__` 已扩充至 339 条，见[候选审查记录](docs/blue-archive-girls-2026-09-27.md)。碧蓝航线 `__azur_lane_girls__` 已扩充至 1,889 条，见[候选审查记录](docs/azur-lane-girls-2026-09-27.md)。原神 `__genshin_impact_girls__` 已扩充至 106 条，见[候选审查记录](docs/genshin-girls-2026-09-27.md)。星穹铁道 `__honkai_star_rail_girls__` 已扩充至 62 条，见[候选审查记录](docs/star-rail-girls-2026-09-27.md)。明日方舟 `__arknights_girls__` 已扩充至 421 条，见[候选审查记录](docs/arknights-girls-2026-09-27.md)。《明日方舟：终末地》 `__endfield_girls__` 已收录名称清单的 27 条，见[候选审查记录](docs/endfield-girls-2026-09-27.md)。Fate/Grand Order `__fate_grand_order_girls__` 已扩充至 236 条，见[候选审查记录](docs/fgo-girls-2026-09-27.md)。VOCALOID `__vocaloid_girls__` 已扩充至 33 条，见[候选审查记录](docs/vocaloid-girls-2026-09-27.md)。东方仍是首批，调用名、覆盖缺口和来源见[九部作品首批采集记录](docs/nine-franchise-girls-2026-09-27.md)。旧版十份 `*_women.txt` 已移至 `archive/legacy-wildcards/` 供对照。本机相邻 Impact Pack 目录可能仍有同名旧版；请使用新的 `*_girls` 名称获取新版。

十套独立的[作品女角色名称词库](docs/name-packs-2026-09-26.md)使用 `__作品名_girls_name__`，每次只输出一个 `角色名, 作品名`，例如 `__blue_archive_girls_name__` 或 `__zenless_zone_zero_girls_name__`。它们是截至 2026-09-26 的一次性数据快照，不需要节点在运行时联网。逐行来源、官方名称回退项与覆盖边界见链接中的说明。

节点先读取相邻的 `ComfyUI-Impact-Pack/wildcards` 和它配置的 `custom_wildcards`，再读取本仓库的 `wildcards`、`custom_wildcards`。后面的同名词条覆盖前面的；所以本仓库自带词库可以在未安装 Impact Pack 时独立使用。修改词库文件后，下次运行会重新读取。

## 角色词库制作

十套旧版词库的质量改进设计、审计勘误、场景推演和迁移验收标准见[角色词库 v2 方案](docs/character-curation-v2.md)。现有 `*_girls` 外观词库采用后续确定的 Wiki 分形态流程；旧版自动产出和统计见[归档说明](docs/character-packs.md)。

项目内的 Claude Code skill [curate-character-wildcards](.claude/skills/curate-character-wildcards/SKILL.md) 已改为 Danbooru 角色 Wiki 的 `Appearance` 分形态采集流程：逐图绑定外观标签、保留审查表，再从 CSV 导出并验证。需要制作或审查新的外观词库时，可以在 Claude Code 中调用 `/curate-character-wildcards`。

## 来源与许可

展开算法改编自 [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) 的 `modules/impact/wildcards.py`，自带词库复制自同项目的 `wildcards/`（本地版本提交 `429d0159`）。因此本项目按 [GPLv3](LICENSE) 发布。`AGENTS.md` 是项目级 AI 协作提示词，不参与节点运行。
