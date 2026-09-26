import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_node():
    events = []
    server = types.SimpleNamespace(
        send_sync=lambda event, value: events.append((event, value)),
        add_on_prompt_handler=lambda handler: setattr(server, "handler", handler),
    )
    sys.modules["server"] = types.SimpleNamespace(PromptServer=types.SimpleNamespace(instance=server))
    spec = importlib.util.spec_from_file_location("wild_card", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    module = importlib.util.module_from_spec(spec)
    sys.modules["wild_card"] = module
    spec.loader.exec_module(module)
    return module, server, events


class WildCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module, cls.server, cls.events = load_node()

    def test_word_files_yaml_and_seed(self):
        engine = self.module.wildcard_engine
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "color.txt").write_text("red\nblue\n", encoding="utf-8")
            (root / "flowers.yaml").write_text("flower:\n  warm: [rose, tulip]\n", encoding="utf-8")
            original_roots = engine._wildcard_roots
            try:
                engine._wildcard_roots = lambda: [root]
                engine._signature = None
                first = engine.expand("a __color__ __flower/warm__ {small|large}", 42)
                self.assertEqual(first, engine.expand("a __color__ __flower/warm__ {small|large}", 42))
                self.assertNotIn("__", first)
                (root / "color.txt").write_text("green\n", encoding="utf-8")
                self.assertEqual(engine.expand("__color__", 42), "green")
            finally:
                engine._wildcard_roots = original_roots
                engine._signature = None

    def test_preview_and_reproduce(self):
        node = self.module.WildCardPrompt()
        self.assertTrue(node.OUTPUT_NODE)
        self.assertEqual(node.run("{red|blue}", "manual", "fixed", 0)["result"], ("manual",))
        data = {
            "prompt": {"7": {"class_type": "WildCardPrompt", "inputs": {
                "wildcard_prompt": "{red|blue}", "populated_prompt": "", "mode": "populate", "seed": 8,
            }}},
            "extra_data": {"extra_pnginfo": {"workflow": {"nodes": [{"id": 7, "widgets_values": ["{red|blue}", "", "populate", 8]}]}}},
        }
        self.server.handler(data)
        inputs = data["prompt"]["7"]["inputs"]
        preview = inputs["populated_prompt"]
        self.assertIn(preview, ("red", "blue"))
        self.assertEqual(inputs["mode"], "reproduce")
        self.assertEqual(node.run(**inputs)["result"], (preview,))
        self.assertEqual(data["extra_data"]["extra_pnginfo"]["workflow"]["nodes"][0]["widgets_values"][1:3], [preview, "reproduce"])
        self.assertIn(("wild-card-preview", {"node_id": "7", "text": preview}), self.events)


if __name__ == "__main__":
    unittest.main()
