# 作品女角色名称词库：一次性快照

生成日期：2026-09-26。范围为十个已约定作品；Fate 仅 Fate/Grand Order；VOCALOID 包含初音、镜音、巡音等声库角色。按任一官方服务器已推出的内容收录。文件放在 `wildcards/`，每行严格为 `角色名, 作品名`，没有 `1girl` 和外观描述。角色名优先采用 Danbooru 角色标签；官方记录已有服装而 Danbooru 暂无独立标签时，使用官方名称构造词条，逐行在 [manifest.csv](../curation/name-packs-2026-09-26/manifest.csv) 的 `is_danbooru_tag=False` 标明。

这是可使用的**名称词库快照**，不是十个作品所有女性、NPC 和官方服装的完整证明。原有外观词库没有在本次重新做逐形态核验；名称词库从旧稿继承的行也继承这一限制。`report.json` 保存来源 URL、抓取时间、SHA-256、逐作品数量和数据无法自动匹配的数量。API 原始响应缓存在系统临时目录，不随节点安装包发布。

| 作品 | 新名称词库 | 条目 | 相对旧外观词库净增 | 仅官方名称、非 Danbooru 标签 |
| --- | --- | ---: | ---: | ---: |
| 绝区零 | `__zenless_zone_zero_girls_name__` | 69 | 1（同时删除已知误收 1 条） | 1 |
| 蔚蓝档案 | `__blue_archive_girls_name__` | 328 | 36（同时删除已知误收 1 条） | 5 |
| 碧蓝航线 | `__azur_lane_girls_name__` | 2,613 | 2,149 | 583 |
| 原神 | `__genshin_impact_girls_name__` | 116 | 7 | 0 |
| 崩坏：星穹铁道 | `__honkai_star_rail_girls_name__` | 79 | 2 | 0 |
| 明日方舟 | `__arknights_girls_name__` | 602 | 274 | 66 |
| 明日方舟：终末地 | `__endfield_girls_name__` | 27 | 0 | 0 |
| Fate/Grand Order | `__fate_grand_order_girls_name__` | 430 | 108 | 50 |
| VOCALOID | `__vocaloid_girls_name__` | 66 | 0 | 0 |
| 东方 Project | `__touhou_girls_name__` | 141 | 0 | 0 |
| **合计** | | **4,471** | **2,577（含两条误收移除）** | **705** |

## 采用的当前数据

| 来源 | 本次用途与实测覆盖 | 时间证据与限制 |
| --- | --- | --- |
| [Danbooru 标签 API](https://danbooru.donmai.us/wiki_pages/help:api) | 为作品表中的角色／皮肤名称找已有角色标签；碧蓝航线 `_(azur_lane)` 共抓到 2,820 个标签，Fate `_(fate)` 4,280 个，均逐页抓到末页。 | 2026-09-26 实时抓取。标签存在不等于角色性别、作品内出现、形态官方实装；因此不能单独决定收录。后缀检索也漏掉没有作品后缀的标签，由旧词库和游戏数据补足。 |
| [SchaleDB 当前学生表](https://schaledb.com/data/en/students.min.json)、[配置](https://schaledb.com/data/config.min.json) | 277 个 `IsReleased` 条目；272 条有现成或已收录的 Danbooru 标签，5 条仅能用官方名称。 | 网站配置 `build=1790381049`，即 2026-09-26 UTC；[旧 GitHub 仓库](https://github.com/SchaleDB/SchaleDB) 已归档，不能代替当前网站数据。只覆盖学生表，不覆盖全部剧情 NPC 和纯剧情服装。 |
| [碧蓝航线舰船与皮肤表](https://github.com/Fernando2603/AzurLane/blob/main/ship_skin.json) | 889 个舰船实体、2,598 个外观记录；2,013 条记录可对上 Danbooru 标签，585 条以官方皮肤名回退。 | 数据仓库 2026-09-25 有更新；游戏数据镜像列出外观，但没有本次要求的逐皮肤首次上架日期字段。不同 ID 共用同一外观名会合并成一行。 |
| [原神服装资料](https://github.com/theBowja/genshin-db)、[服装 API](https://genshin-db-api.vercel.app/api/v5/outfits?query=names&matchCategories=true&verboseCategories=true) | 当前 API 返回 152 个默认与变体外观；以旧词库已知女性为身份闸门，匹配 101 条官方记录并新增 7 个 Danbooru 服装标签。 | 资料库标注已更新至 7.1；它是玩家整理的游戏数据，不包含全部剧情 NPC 的所有换装。 |
| [星铁人物数据](https://github.com/Mar-7th/StarRailRes)、[三月七服装公告](https://www.hoyolab.com/article/36260996)、[卡斯托里斯服装公告](https://www.hoyolab.com/article/44742273) | 人物数据仓库更新至 2026-08-29；另外依据官方公告新增 `Nascent Spring` 与 `Gossamer Flutter` 的现有 Danbooru 标签。 | 人物资料不是完整皮肤目录，其他服装仍依赖旧词库。 |
| [明日方舟 CN 游戏数据](https://github.com/ArknightsAssets/ArknightsGamedata/tree/master/cn/gamedata/excel)、[EN 游戏数据](https://github.com/ArknightsAssets/ArknightsGamedata/tree/master/en/gamedata/excel) | 对旧词库中的已知女性角色，以角色 ID 匹配 `charSkins`；匹配 666 个皮肤记录，其中 67 条用官方皮肤名回退。 | 镜像提交时间为 2026-09-24，英文表与 CN 版本不同步。1,077 个 CN 皮肤记录缺少可关联的英文身份，另有 573 条在已有女性名单之外；这些数量不能直接解释为漏收女性或漏收皮肤。 |
| [Atlas Academy FGO API](https://api.atlasacademy.io/docs)、[版本信息](https://api.atlasacademy.io/info) | JP 表中 293 个 `genderFemale` Servant 记录；226 条可用现成或旧词库标签，67 条用官方英文名回退。 | `/info` 于本次抓取时显示 JP 数据时间戳为 2026-09-25 UTC。该表主要覆盖 Servant，不能代表所有女性剧情 NPC；部分官方译名与 Danbooru 正名仍需别名映射。 |
| [绝区零 3.2 官方公告](https://zenless.hoyoverse.com/en-us/news/166023?mhy_auth_required=true)、[官方衣装活动](https://zenless.hoyoverse.com/m/en-us/news/166191) | 已核对 2026-09 的 Claret 与三套 Angels of Delusion 衣装；Aria 新增一个现成标签，Nangong Yu 衣装用官方名回退，Sunna 的衣装在旧稿已收录。 | 这两则公告不是全量人物／皮肤数据接口。 |
| [终末地官方干员列表](https://endfield.gryphline.com/en-us/operator) | 页面现列 33 个干员槽位（男／女管理员分别计数）；旧稿保留 27 个女性角色／NPC 标签。 | 页面没有完整 NPC／衣装结构化数据；本次未自动把全部列表推断为女性。 |
| [VOCALOID 官方声库](https://www.vocaloid.com/en/voicebank-01/)、[初音 V6 公告](https://www.vocaloid.com/en/news/news_34/) | 当前声库目录与 2026-04 已发布的初音 V6 可核对；该标签已在旧稿。 | “官方服装”横跨不同厂商、演唱会、联动和年份，官网没有统一的可枚举服装接口；66 行仍是旧稿覆盖。 |
| [东方 2026 官方重制作品](https://www.nintendo.com/us/store/products/touhou-koumakyou-new-classic-the-embodiment-of-scarlet-devil-switch-2/) | 确认作品在 2026-09 仍有官方发行；141 行保持旧稿。 | 发行页面不是整个东方正典的人物／衣装目录，未据此宣称全覆盖。 |

## 不能由这次自动收集证明的事项

1. **完整率**：NPC、剧情中的短暂换装、不同服务器的首次上架时间，十作没有同一种公开结构化字段。上述当前数据满足“来源不旧于 2026-07”的最低要求，但不能推出“每位女性、每套官方衣装都已收全”。
2. **模型识别率**：`is_danbooru_tag=False` 的 705 行是官方名称构造词条，没有 Danbooru 独立角色标签。它们用于覆盖官方名录，不保证模型能画出相应服装。
3. **旧稿误收**：已知的绝区零玩偶 `anastella_(zenless_zone_zero)` 与蔚蓝档案 Boss `binah_(blue_archive)` 从新名称词库排除。其余旧稿仍未逐人、逐形态核对正典身份；本次也未修改原 `*_women.txt` 外观词库。
4. **提示词解析**：名字中的括号可能被某些 ComfyUI 文本编码器当作权重语法。本项目节点负责展开字符串，不负责对下游编码器转义；能否保持字面量取决于所连编码器。

## 生成与核查

本次命令：`python curation/name-packs-2026-09-26/build.py --include-untagged`。它是一次性快照脚本，不计划自动维护。生成时合并了 9 个已知同形态标签拼写重复项，记录在 `report.json`。逐行来源见 [manifest.csv](../curation/name-packs-2026-09-26/manifest.csv)，API 散列与统计见 [report.json](../curation/name-packs-2026-09-26/report.json)。
