# 原神女角色外观词库：名称清单候选审查版

2026-09-27 一次性快照，调用 `__genshin_impact_girls__`。现有 [`wildcards/genshin_impact_girls.txt`](../wildcards/genshin_impact_girls.txt) 为 **106 条**逐图绑定的角色／形态，原首批 9 条全部保留；名称词库保持独立。

本轮查询名称词库的 116 个 Danbooru 角色 Wiki，得到 336 条 Appearance 记录：279 条 post 引用、48 条无标签 asset 引用、9 个没有 Appearance。对缺口做 70 次精确标签补查，并为旅行者 Lumine 补查到[日语官方账号的单人图](https://danbooru.donmai.us/posts/5310275)。最终 116 个候选中收录 106 个，排除 10 个：7 个没有对应的合格标签 post，3 个原始来源或可见标签证据不足。逐项原因见 [`audit.csv`](../curation/genshin-full-2026-09-27/audit.csv)。

名称清单的 101 条[游戏服装资料记录](https://github.com/theBowja/genshin-db)中，100 条进入外观词库；`lumine_(as_heaven_and_earth_are_made_anew)_(genshin_impact)` 目前没有可绑定的合格 post，按用户决定排除。其余 15 条名称来自旧外观稿，只有 6 条剧情人物／默认形态满足本轮证据条件。Pizza Hut、首尔咖啡店、周年宣传等作品外衣装不会因 Wiki 有图或旧稿曾收录就进入游戏服装词库。

每条收录行的角色、版权、`1girl`、`official_art` 与所选外观标签均在对应的同一 Danbooru post 中；基础角色的补查还排除同图带其他形态标签、多人图和客串角色。来源包括游戏素材标记、HoYoverse 官方账号和原神资料镜像。`@Genshin_7` 的官方身份另由 [HoYoWiki](https://wiki.hoyolab.com/pc/genshin/entry/37/) 交叉核对。社区标签和资料镜像仍可能出错；“收录”表示这轮证据足够生成词条，不等于已独立核对每件服装的首次实装日期。

[`inventory.csv`](../curation/genshin-full-2026-09-27/inventory.csv)、[`supplemental.csv`](../curation/genshin-full-2026-09-27/supplemental.csv)、[`review_queue.csv`](../curation/genshin-full-2026-09-27/review_queue.csv)、[`reviewed.csv`](../curation/genshin-full-2026-09-27/reviewed.csv)、[`audit.csv`](../curation/genshin-full-2026-09-27/audit.csv) 和 [`image_audit.csv`](../curation/genshin-full-2026-09-27/image_audit.csv) 保存候选、精确 post 来源与排除原因。只读取 JSON 文字标签，未下载图片。导出器 `--check` 通过 106/106 字节比对，固定 seed 本地展开通过；未在 ComfyUI 画布上重新出图。
