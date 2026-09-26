# wild-card

独立的 ComfyUI wildcard 节点。`Wild Card Prompt` 在节点文本框中接收 wildcard prompt，显示展开结果，并只输出一个 populated prompt `STRING`。不需要 model 或 clip 输入。

## 使用

将仓库放在 `ComfyUI/custom_nodes/wild-card`，重启 ComfyUI，在 `wild-card` 分类下添加 `Wild Card Prompt`。输入 `a {red|blue} __flower__` 之类的文本，连接右侧 `populated_prompt` 到需要字符串的节点。

- `populate`：每次排队时展开原始提示词，并更新只读预览。
- `fixed`：忽略原始提示词，使用可编辑的预览文本。
- `reproduce`：使用预览文本一次，然后恢复 `populate`。保存的工作流会保留当次结果。
- `seed`：相同种子与相同词库得到相同结果；“生成后控制”由 ComfyUI 提供。

支持 Impact Pack 的 `{a|b}`、权重、多选及 `__name__` 等 wildcard 语法。本仓库的 `wildcards/` 已包含从 Impact Pack 复制的 7 个词库：`color`、`flower`、`jewel`、`jima`、`position`、`samples/flower`、`zenless_women`。

节点先读取相邻的 `ComfyUI-Impact-Pack/wildcards` 和它配置的 `custom_wildcards`，再读取本仓库的 `wildcards`、`custom_wildcards`。后面的同名词条覆盖前面的；所以本仓库自带词库可以在未安装 Impact Pack 时独立使用。修改词库文件后，下次运行会重新读取。

## 来源与许可

展开算法改编自 [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) 的 `modules/impact/wildcards.py`，自带词库复制自同项目的 `wildcards/`（本地版本提交 `429d0159`）。因此本项目按 [GPLv3](LICENSE) 发布。`AGENTS.md` 是项目级 AI 协作提示词，不参与节点运行。
