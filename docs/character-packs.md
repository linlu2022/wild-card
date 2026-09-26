# 作品女角色词库

2026-09-26 后续审计发现身份、形态和证据不足等问题；请结合[质量改进方案与审计勘误](character-curation-v2.md)阅读下表。表中的来源计数不代表所有词条已经逐图核验。原绝区零词库也包含在该方案的审计范围内。

以下九套词库于 2026-09-26 从 Danbooru 角色标签和作品版权标签整理。表中 `官图` 是采集程序使用带有 `official_art` 且版权匹配的图片所生成的条目数；程序按角色标签、名称前缀或共现比例判断主体关系，这些关系与图片的官方来源尚未逐条核实。`回退` 是官图样本不足时，使用程序判断为单主体的普通作品所生成的条目数。两类来源都不能单靠这些统计证明身份和外观正确。

| 作品 | wildcard 用法 | 条目 | 官图 | 回退 |
| --- | --- | ---: | ---: | ---: |
| 蔚蓝档案 | `__blue_archive_women__` | 292 | 210 | 82 |
| 碧蓝航线 | `__azur_lane_women__` | 464 | 295 | 169 |
| 原神 | `__genshin_impact_women__` | 109 | 84 | 25 |
| 崩坏：星穹铁道 | `__honkai_star_rail_women__` | 77 | 60 | 17 |
| 明日方舟 | `__arknights_women__` | 328 | 161 | 167 |
| 明日方舟：终末地 | `__endfield_women__` | 27 | 23 | 4 |
| Fate/Grand Order | `__fate_grand_order_women__` | 322 | 190 | 132 |
| VOCALOID | `__vocaloid_women__` | 66 | 34 | 30 + 2 继承 |
| 东方 Project | `__touhou_women__` | 141 | 124 | 17 |

每行格式为 `版权标签, 角色标签, 1girl, 外观标签…`。Fate 按用户选择仅含 Fate/Grand Order；VOCALOID 按声库角色及其形态筛选，不收歌曲原创人物。明日方舟词库排除带有 `arknights:_endfield` 的作品，终末地独立筛选。终末地同一人物多名时优先使用[官方角色名单](https://endfield.gryphline.com/en-us/operator)上的名字。VOCALOID 角色范围参考[官方声库列表](https://www.vocaloid.com/en/anniversary/voicebank/)。

这批每套最多检查 500 个高关联候选，低频角色和官图证据不足的角色未保证覆盖。自动筛选结果经过异常复核；未逐张人工核验全部图片。宠物、召唤物、外作联动人物和重复身份的具体剔除项记录在[审定配置](../curation/character-packs-2026-09-26.json)。`magical_mirai_miku` 和 `racing_miku` 缺少可隔离的单主体图，显式继承初音未来的稳定外观标签；服装细节未添加。65 行里同时出现的多个颜色标签在无双色标记时保留频率较高的一项，具体移除项写入生成时的 `review_summary.json`。

生成脚本与流程见[项目 skill](../.claude/skills/curate-character-wildcards/SKILL.md)。审定 CSV、逐角色审计 JSON 和 API 缓存保存在本次生成时指定的外部数据目录，未打包进运行时节点。
