# 碧蓝航线女角色外观词库：名称清单候选审查版

2026-09-27 一次性快照，调用 `__azur_lane_girls__`。现有 [`wildcards/azur_lane_girls.txt`](../wildcards/azur_lane_girls.txt) 为 **1,889 条**角色／官方游戏形态；此前 8 条首批均保留。`*_girls_name.txt` 名称词库仍独立存在。

本轮从现有 **2,613** 条名称候选中的 892 个舰船基础名出发，查询 Danbooru 角色 Wiki 的 `Appearance`。得到 2,406 条引用：2,141 条 post 引用、40 条无 post 标签的 asset 引用、183 个 Wiki 缺失、42 个没有 Appearance；post 去重为 2,111 张。再对缺口做 594 次精确标签搜索，最终对 2,613 个名称候选逐项审查：**1,889 收录，724 排除**。排除原因是 570 条仅有官方皮肤名称而无可绑定的标签图片、112 条没有对应的合格标签 post、42 条原始来源或可见标签证据不足。详见 [`audit.csv`](../curation/azur-lane-full-2026-09-27/audit.csv)。

收录行中有 13 条官方游戏皮肤尚无独立 Danbooru 形态标签：仅在舰船 Wiki 明确列出同名服装、该图片 post 有舰船基础标签、并能对上 2026-09-26 抓取的[舰船与皮肤表](https://github.com/Fernando2603/AzurLane/blob/main/ship_skin.json)时，使用官方名称构造触发词。其余无标签皮肤不猜测外观。**本轮只读取 Wiki 与 post JSON 的文字标签和来源字段，没有下载图片文件。**

## 归属与来源

每条收录行绑定一个具体 Danbooru post；脚本逐项检查 `azur_lane`、`1girl`、`official_art`、对应角色／形态标签和所选 general tags。标签搜索结果若混入其他舰船身份、玩偶或画中画，而本角色 Wiki 没有相应外观指向，则不把图中服装错配给客串者。11 个 post 同时支持两个词条，均可对上同一游戏皮肤 ID，属于原舰与 II 型共用的服装资源；构建脚本对此断言。

来源级别为 Danbooru 的 `game_asset` 标签、发行方账号、游戏文件来源文字，或 Wiki 所指的资源镜像。很多原始 `source` 指向 `azurlane.koumakan.jp`，该站当前页面可用性不稳定；这些链接只作历史图片出处，**不作为独立的实装证明**。作品内身份主要以 2026-09-26 的舰船／皮肤游戏数据快照交叉核对。6 个仅来自旧词库的名字另作核对：5 个可在该游戏数据中找到舰船／皮肤 ID；TB 的作品内身份可由[官方维护公告](https://azurlane.yo-star.com/news/2024/02/05/maintenance-notice-2-6-12-a-m-utc-7-2/)确认。旧首批 Enterprise 默认图的画师来源作为一条有记录的沿用例外。

程序只能验证标签与所选 post 对应、游戏数据含有名称；社区 Wiki、Danbooru 标签或游戏数据镜像仍可能出错。本版覆盖的是**现有名称词库的候选审查**，不保证游戏所有女性 NPC 与官方形态已被这些来源枚举，也不逐条证明首次实装日期。无来源项按用户决定从外观词库排除，保留在审计表供查询。

## 文件与验证

- [`inventory.csv`](../curation/azur-lane-full-2026-09-27/inventory.csv)、[`supplemental.csv`](../curation/azur-lane-full-2026-09-27/supplemental.csv)：Wiki 引用与精确标签补查的文字证据。
- [`review_queue.csv`](../curation/azur-lane-full-2026-09-27/review_queue.csv)、[`audit.csv`](../curation/azur-lane-full-2026-09-27/audit.csv)、[`image_audit.csv`](../curation/azur-lane-full-2026-09-27/image_audit.csv)：逐形态与逐引用的选择、排除原因。
- [`reviewed.csv`](../curation/azur-lane-full-2026-09-27/reviewed.csv)：最终 1,889 条词条的精确 post URL；同目录脚本保存生成规则，节点运行时不联网。

已通过导出器 `--check` 的 1,889/1,889 字节比对和固定 seed 的本地展开。未在运行中的 ComfyUI 画布上重新出图。
