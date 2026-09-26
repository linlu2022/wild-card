import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function findWidget(node, name) {
    return node.widgets?.find((widget) => widget.name === name);
}

function updateReadOnly(node) {
    const preview = findWidget(node, "populated_prompt");
    const mode = findWidget(node, "mode");
    if (preview?.inputEl && mode) {
        preview.inputEl.readOnly = mode.value === "populate";
        preview.inputEl.placeholder = "Populated Prompt (generated automatically)";
    }
}

api.addEventListener("wild-card-preview", ({ detail }) => {
    const node = app.graph?.getNodeById(Number(detail.node_id));
    const preview = node && findWidget(node, "populated_prompt");
    if (preview) {
        preview.value = detail.text;
        node.setDirtyCanvas(true, true);
    }
});

api.addEventListener("wild-card-mode", ({ detail }) => {
    const node = app.graph?.getNodeById(Number(detail.node_id));
    const mode = node && findWidget(node, "mode");
    if (mode) {
        mode.value = detail.mode;
        updateReadOnly(node);
    }
});

app.registerExtension({
    name: "wild-card.prompt",
    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "WildCardPrompt") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            const input = findWidget(this, "wildcard_prompt");
            if (input?.inputEl) input.inputEl.placeholder = "Wildcard Prompt (user input)";
            const mode = findWidget(this, "mode");
            if (mode) {
                const callback = mode.callback;
                mode.callback = (...args) => {
                    callback?.apply(mode, args);
                    updateReadOnly(this);
                };
            }
            updateReadOnly(this);
            return result;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = onConfigure?.apply(this, arguments);
            updateReadOnly(this);
            return result;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (output) {
            const result = onExecuted?.apply(this, arguments);
            const preview = findWidget(this, "populated_prompt");
            if (preview && output?.populated_prompt?.length) {
                preview.value = output.populated_prompt[0];
            }
            return result;
        };
    },
});
