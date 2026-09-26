"""A standalone ComfyUI node for Impact Pack compatible wildcard prompts."""

import logging

from server import PromptServer

from . import wildcard_engine


class WildCardPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "wildcard_prompt": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "Wildcard prompt to expand."}),
            "populated_prompt": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "Preview of the expanded prompt. Editable in fixed and reproduce modes."}),
            "mode": (["populate", "fixed", "reproduce"], {"default": "populate", "tooltip":
                "populate: Expand wildcard_prompt for each queued run.\n"
                "fixed: Use populated_prompt instead of wildcard_prompt.\n"
                "reproduce: Use populated_prompt once, then return to populate."}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                            "control_after_generate": True, "tooltip": "Random seed used for wildcard expansion."}),
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("populated_prompt",)
    FUNCTION = "run"
    CATEGORY = "wild-card"
    DESCRIPTION = "Expand an Impact Pack compatible wildcard prompt and output the resulting STRING."
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return repr(wildcard_engine.refresh_wildcards())

    def run(self, wildcard_prompt, populated_prompt, mode, seed):
        source = wildcard_prompt if mode == "populate" else populated_prompt
        result = wildcard_engine.expand(source, seed)
        return {"ui": {"populated_prompt": [result]}, "result": (result,)}


NODE_CLASS_MAPPINGS = {"WildCardPrompt": WildCardPrompt}
NODE_DISPLAY_NAME_MAPPINGS = {"WildCardPrompt": "Wild Card Prompt"}
WEB_DIRECTORY = "js"


def _on_prompt(json_data):
    prompt = json_data.get("prompt", {})
    workflow = json_data.get("extra_data", {}).get("extra_pnginfo", {}).get("workflow", {})
    workflow_nodes = {str(node.get("id")): node for node in workflow.get("nodes", [])}

    for node_id, node in prompt.items():
        if node.get("class_type") != "WildCardPrompt":
            continue
        inputs = node["inputs"]
        mode = inputs.get("mode", "populate")
        if mode == "populate":
            try:
                result = wildcard_engine.expand(inputs["wildcard_prompt"], inputs["seed"])
            except Exception:
                logging.exception("[wild-card] Could not populate node %s before queuing", node_id)
                continue
            inputs["populated_prompt"] = result
            inputs["mode"] = "reproduce"
            PromptServer.instance.send_sync("wild-card-preview", {"node_id": node_id, "text": result})

            saved = workflow_nodes.get(str(node_id))
            if saved and len(saved.get("widgets_values", [])) >= 3:
                saved["widgets_values"][1] = result
                saved["widgets_values"][2] = "reproduce"

        if inputs.get("mode") == "reproduce":
            PromptServer.instance.send_sync("wild-card-mode", {"node_id": node_id, "mode": "populate"})

    return json_data


PromptServer.instance.add_on_prompt_handler(_on_prompt)
