# 九部作品女角色外观词库：首批

**后续进展：**蔚蓝档案已从本页的 11 条首批扩充到 [339 条审查版](blue-archive-girls-2026-09-27.md)，碧蓝航线已从 8 条扩充到 [1,889 条审查版](azur-lane-girls-2026-09-27.md)，原神已从 9 条扩充到 [106 条审查版](genshin-girls-2026-09-27.md)，星穹铁道已从 16 条扩充到 [63 条审查版](star-rail-girls-2026-09-27.md)，明日方舟已从 16 条扩充到 [421 条审查版](arknights-girls-2026-09-27.md)，终末地已从 11 条扩充到 [27 条审查版](endfield-girls-2026-09-27.md)。FGO 已从 11 条扩充到 [236 条审查版](fgo-girls-2026-09-27.md)。下表保留首批采集时的历史数量。

2026-09-27 的一次性快照。新增 `wildcards/<作品>_girls.txt` 九份，共 **100 条形态词条**。调用方式如 `__blue_archive_girls__`；每次随机输出一行 `作品标签, Danbooru 角色／形态标签, 1girl, 该形态图片中的外观标签…`。本批是有证据的**小批量样本**，绝不表示作品角色、服装或 2026 年 8 月前的实装内容已经全面覆盖。原有名称词库 `<作品>_girls_name.txt` 仍可用于覆盖更多角色名称。

| 作品／调用名 | 首批形态 | 已涉及角色 Wiki／首批检查 | 名称词库总行数 | 首批检查但未收录的角色 Wiki |
| --- | ---: | ---: | ---: | --- |
| 蔚蓝档案 `blue_archive_girls` | 11 | 6/10 | 328 | Mika、Toki、Ako、Iroha |
| 碧蓝航线 `azur_lane_girls` | 8 | 4/5 | 2,613 | Atago |
| 原神 `genshin_impact_girls` | 9 | 6/10 | 116 | Raiden Shogun、Navia、Arlecchino、Hu Tao |
| 崩坏：星穹铁道 `honkai_star_rail_girls` | 16 | 9/10 | 79 | Kafka（默认图片为多人图） |
| 明日方舟 `arknights_girls` | 16 | 8/8 | 602 | 无；其余 594 个名称未进入这轮 Wiki 检查 |
| 明日方舟：终末地 `endfield_girls` | 11 | 11/27 | 27 | Arcane、Ardelia、Fluorite、Gilberta、Laevatain、Liino、M3、Mi Fu、Nefarith、Purrchena、Rossi、Si、Snowshine、Tangtang、Typhoeus、Zhuang Fangyi |
| Fate/Grand Order `fate_grand_order_girls` | 11 | 6/8 | 430 | Artoria、Nero |
| VOCALOID `vocaloid_girls` | 14 | 7/9 | 66 | Kagamine Rin、Gumi |
| 东方 `touhou_girls` | 4 | 4/10 | 141 | Sakuya、Remilia、Youmu、Yuyuko、Patchouli、Yukari |

“首批检查”只指本轮取了对应角色 Wiki 的 Appearance 图片清单；没有检查的其余名称词库条目同样**未覆盖**。即使“已涉及角色”，其其他服装也可能未收录。终末地这轮检查了现有 27 个名称。FGO 只接受 `fate/grand_order` 版权标签。VOCALOID 词条采用官方声库形象，包含 Crypton NT 这类同角色产品形象；它不以“游戏内皮肤”为范围。东方的四条中有三条来自正作《兽王园》角色图，一条 Flandre 来自获得授权的《Touhou Spell Carnival》；两个作品层次在来源记录中保留。

## 证据与取舍

入口是每个角色的 [Danbooru Wiki](https://danbooru.donmai.us/wiki_pages) 的 `Appearance` 清单，再打开该清单**精确链接的 post**。例如 [Aris 冬装](https://danbooru.donmai.us/posts/11460939)与[默认装](https://danbooru.donmai.us/posts/4447168)分别提供不同的角色形态标签和外观标签。输出的每一行要求具体 post 同时包含相应版权标签、`1girl`、`official_art` 和所选精确角色／形态标签；所有外观标签逐个与该 post 的 general tags 对照。角色表和服装 Wiki 的文字、图片来源一起辅助判断是否为作品内官方形象；联动宣传、演唱会、咖啡店与粉丝设计没有因为被列入 `Appearance` 就自动纳入。多人物图片与缺少 post 标签的 `asset` 暂缓。

证据强度因作品而异。终末地 11 条来源都指向官方 `endfield.hypergryph.com`；碧蓝航线主要来自游戏资源镜像 `azurlane.koumakan.jp`；明日方舟主要来自 Aceship／PRTS 游戏资源镜像；FGO 多数来自 Atlas Academy 的游戏素材镜像；星穹铁道多数是 Danbooru 标记为 `game_asset` 的客户端相对路径，不能直接从公开网址回访；原神 3 张所选默认图没有原始 `source`，另有 Wiki 镜像图片。这里的程序核对只保证**标签出处**，不等于逐件服装已用官方公告或客户端独立确认实装日期。尤其是 2026 年 8 月的完整覆盖，不应从这份首批词库推断。

逐项材料在 [`curation/wiki-appearance-2026-09-27`](../curation/wiki-appearance-2026-09-27/)：九份 `*_inventory.csv` 保留 Wiki 图片和 post 原始标签，九份 `*_reviewed.csv` 是最终选定标签与精确 post 链接，九份 `*_audit.csv` 对每个候选记录收录或暂缓原因，`build.py` 记录人工选择并断言标签成员关系。`targets.json` 保存本批检查的角色范围。`asset` 没有可用 post general tags；“暂缓”不等于确认角色或形态无效。部分未选图片是尚未审查到的官方形态，部分可能是作品外宣传，这两者都需要另作判断。

旧版自动产出的九份 `*_women.txt` 归档在 [`archive/legacy-wildcards`](../archive/legacy-wildcards/) 下供对照，不再作为本仓库运行时词库。它们的外观描述没有并入新版。相邻 Impact Pack 可能另有同名词库；这次仅管理本仓库目录。使用新版时请调用新的 `*_girls` 名称。

## 验证边界

所有词库由相应 `reviewed.csv` 导出为 UTF-8 无 BOM、LF 换行；程序检查版权、角色／形态、`1girl`、`official_art` 与逐图外观标签的成员关系，校验同一词库无重复角色形态标签。随后用导出器 `--check` 比对字节，并用本地 wildcard 引擎固定 seed 展开。此检查不能判断画师是否准确画出原游戏服装，也不能证明模型能识别冷门形态。未在 ComfyUI 画布上重新出图。
