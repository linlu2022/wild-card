# 蔚蓝档案女角色外观词库：全量候选审查版

2026-09-27 一次性审查快照，调用 `__blue_archive_girls__`。在原首批 11 条的基础上，现有 [`wildcards/blue_archive_girls.txt`](../wildcards/blue_archive_girls.txt) 收录 **339 条**逐图绑定的角色／形态：其中 269 条可对上此前 [SchaleDB 已实装学生快照](name-packs-2026-09-26.md)的记录，70 条为有作品图片证据的剧情人物或剧情／非可玩装束。仅根据角色标签不能推断同一人物已有的所有官方装束都已入库。

本轮逐一查询现有 328 行名称词库对应的 Danbooru Wiki，得到 709 条 `Appearance` 引用（563 条 post 引用、132 条 asset 引用、14 条缺失或空 Appearance；post 去重后 474 张，asset 去重后 107 张）。对最初找不到合格 post 的 53 个名称标签，再按精确标签查询；对疑似误配到宣传／变体图片的标签补查 72 次。最后形成 **390 个不同的角色／形态标签**审查项：339 收录，27 个作品外联动造型排除，14 个无可核对标签 post 排除，10 个来源或作品内形态证据不足排除。名称词库中 309/328 个标签进入外观词库；另外收录 30 个名称词库未列出的、有证据的剧情形态。原名称词库仍独立保留。

这项“全量”指**对现有名称词库和它们的 Wiki Appearance 候选完成逐项审查**，并按本轮证据门槛决定收录或排除；它不保证 Danbooru Wiki 已枚举截至 2026 年 8 月的每一位女性和每一套官方衣装。用户已决定：只有图片素材、找不到可核对 post 标签的形态，不人工猜测外观，直接从外观词库排除。`asset`、Wiki 缺口与外部联动项保留在审查资料中，便于核对“为什么没有这条”。

## 判定方式

每条收录行都绑定一个[具体 Danbooru post](https://danbooru.donmai.us/posts/11460939)，而不是将同一人物不同图片的标签合并。脚本检查该图的 `blue_archive`、`1girl`、`official_art`、精确角色／形态标签及每个所选 general tag。图片还需有游戏素材、发行方图片或可回访的游戏资料镜像；一条 [Asuna 校服](https://bluearchive.wiki/wiki/Asuna_(School_Uniform))的原图来自画师账号，另以已实装学生记录和角色页面交叉核对，作为明确记录的例外。六个 YouTube 帖子链接实际显示为 Blue Archive 官方账号，标题核对记录在 `verified_youtube.csv`。联动广告、J League、Mom's Touch、Muninsa 和 Flowery Charms 等作品外造型不会因 Wiki 收录或标记 `official_art` 就进入词库。

自动标签建议只从**该图**选发色、眼色、光环、物种特征、服装和配饰，去掉姿势、构图、背景、表情和身体尺寸。原首批 11 条若使用相同图片，沿用已手工审定的标签。标签成员关系能用程序验证，Danbooru 社区对图片和“官方”身份的标注仍可能出错；程序也不能独立证明每件剧情装束的首次游戏登场日期。未在运行中的 ComfyUI 画布上重新出图。

## 文件与复现

- [`inventory.csv`](../curation/blue-archive-full-2026-09-27/inventory.csv)：328 个 Wiki 的 Appearance 原始证据；`supplemental.csv`、`rescue.csv` 为精确标签补查记录。
- [`review_queue.csv`](../curation/blue-archive-full-2026-09-27/review_queue.csv)、[`audit.csv`](../curation/blue-archive-full-2026-09-27/audit.csv)：390 个形态的候选图片、来源级别与逐项收录／排除原因。
- [`reviewed.csv`](../curation/blue-archive-full-2026-09-27/reviewed.csv)：339 条最终词条与各自精确 post URL；`collect_supplemental.py`、`prepare_review.py`、`build.py` 保存一次性制作逻辑，运行节点时不联网。

已通过 CSV 导出器 `--check` 的 339/339 字节比对、固定 seed 本地展开与现有节点测试。旧版自动外观词库仍保存在 [`archive/legacy-wildcards/blue_archive_women.txt`](../archive/legacy-wildcards/blue_archive_women.txt)，没有与新版混用。
