# 绝区零女角色外观词库：首批

2026-09-27 一次性采集快照。调用 `__zenless_girls__`，每次随机输出一条 `zenless_zone_zero, 角色／服装标签, 1girl, 外观标签…`。文件为 [`wildcards/zenless_girls.txt`](../wildcards/zenless_girls.txt)，本批 17 位角色、37 个独立形态。它是首批，不代表绝区零所有女性角色或所有官方服装已经覆盖。

本仓库旧版 68 行 [`zenless_women.txt`](../archive/legacy-wildcards/zenless_women.txt) 已移出运行时 `wildcards/`，仅供对照；已知的 Anastella 玩偶误收不会进入新版。本批不从旧版继承外观标签。本机相邻 Impact Pack 的 `wildcards/zenless_women.txt` 与归档文件散列相同，兼容加载仍能读到旧名称；新版专用名称为 `__zenless_girls__`。

## 来源与取舍

入口为 [Danbooru 绝区零角色索引](https://danbooru.donmai.us/wiki_pages/list_of_zenless_zone_zero_characters)和各角色 Wiki 页的 `Appearance` 清单。以[薇薇安 Wiki](https://danbooru.donmai.us/wiki_pages/vivian_banshee)为例，它分别给默认造型和 `Iris of the Shore` 皮肤一个图片编号；[默认图片](https://danbooru.donmai.us/posts/9196669)与[皮肤图片](https://danbooru.donmai.us/posts/10146034)分别提供角色、作品、外观标签。具体服装 Wiki 页还标记它是官方替换服装。所选 37 张图片中，36 张的 `source` 指向 `wiki.hoyolab.com`，Nicole 默认装的 `source` 指向第三方镜像中的官方角色立绘；后者的原始发布链路未独立核验。

从既有 69 条绝区零名称候选查询 Wiki，得到 99 个 Appearance 引用，去重后为 79 个 post、6 个 asset。首批收录 37 个 post；另外 33 个 post 留待后续主体／形态核查或因首批范围暂缓，5 个 post 的来源需要复核，4 个 post 不足以证明单一女性主体，6 个 asset 没有可直接读取的 post 标签。逐项状态见 [`audit.csv`](../curation/zenless-appearance-2026-09-27/audit.csv)。`deferred` 表示未进入本批，不表示角色或服装无效。

每条收录记录都要求对应 post 含 `zenless_zone_zero`、`1girl`、`official_art` 和所用的精确角色／形态标签；每个输出的外观标签也必须出现在该 post 的 general tags 中。保留发色、眼睛、物种特征、服装和配饰等可见外观；去掉构图、动作、背景、表情、画质、来源元数据和同图中的伴随物标签。`official_art` 与 Wiki 的“官方服装”说明本身仍是社区标注，不能单独证明游戏内实装。这里通过角色 Wiki 的 Appearance 分形态入口和图像来源交叉约束，但没有逐张核验原始游戏客户端画面，也没有为每件服装找到独立官方实装公告。

特意保留同一人物不同形态的区别。例如[薇薇安默认装](https://danbooru.donmai.us/posts/9196669)输出 `white_dress`、`black_skirt`，[Iris of the Shore](https://danbooru.donmai.us/posts/10146034)输出 `frilled_one-piece_swimsuit`。外观冲突不跨形态平均。截图里红框所示的 `solo`、`transparent_background`、`full_body` 不写入词条。

## 可复现资料与限制

- [`inventory.csv`](../curation/zenless-appearance-2026-09-27/inventory.csv)：Wiki Appearance 图片、原始标签和来源元数据，共 99 条引用。
- [`reviewed.csv`](../curation/zenless-appearance-2026-09-27/reviewed.csv)：37 个输出词条的审定 CSV，URL 精确指向对应 post。
- [`collect.py`](../curation/zenless-appearance-2026-09-27/collect.py)与 [`build.py`](../curation/zenless-appearance-2026-09-27/build.py)：一次性采集及人工选定标签的导出记录；词库运行时不调用网络。

这些记录可核对“标签是否来自指定图片”，但不能把 Danbooru 社区标签的正确率或完整性视为已验证。尤其是同图有宠物、玩偶、衣服图案里的其他角色时，只采用能明确归给主体的标签。Wiki 采用 `asset` 而无 post 标签的形态，以及尚未确认属于游戏内服装的联动宣传形态，均暂缓。Danbooru 角色标签里的圆括号按原样保留；若下游 CLIP 将圆括号解析为权重，需要在接入编码器前按该编码器的规则转义。

导出后用 CSV 校验器逐行回比，37/37 一致；本地节点词库加载与固定 seed（11、22、37）展开成功。`python -m unittest discover -s tests -v` 的现有 2 项测试通过。未在运行中的 ComfyUI 画布上重新出图，也未验证模型是否稳定识别每个冷门形态。
