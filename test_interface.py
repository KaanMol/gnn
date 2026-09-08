import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from interface import LlamaCppLanguage, OllamaLanguage, OpenAILanguage, Session
from sensors import CanvasSurface, SensorHub


class InterfaceTests(unittest.TestCase):
    def test_language_context_does_not_include_the_board_observation(self):
        session = Session()
        with patch.object(session.sudoku, 'perception', side_effect=AssertionError('LLM was given raw board state')):
            context = session.context()
        self.assertEqual(context['sudoku']['surface'], 'canvas')
        self.assertIn('sudoku_describe', context['sudoku']['reading'])
        json.dumps(context)

    def test_llamacpp_discovers_and_translates(self):
        models = {"data": [{"id": "local-gemma.gguf"}]}
        reply = {"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps({"kind": "question", "content": "What is Mira?"})}}]}
        with patch("interface.urlopen", side_effect=[io.BytesIO(json.dumps(models).encode()),
                                                      io.BytesIO(json.dumps(reply).encode())]) as mock:
            translator = LlamaCppLanguage(base_url="http://127.0.0.1:8080/v1")
            result = translator.translate("Tell me about Mira", {})
        self.assertEqual(translator.model, "local-gemma.gguf")
        self.assertEqual(result["kind"], "question")
        request = mock.call_args[0][0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8080/v1/chat/completions")
        self.assertEqual(json.loads(request.data)["response_format"]["schema"]["required"], ["operations"])

    def test_llamacpp_rejects_truncated_translation(self):
        reply = {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}
        with patch("interface.urlopen", return_value=io.BytesIO(json.dumps(reply).encode())):
            with self.assertRaisesRegex(ValueError, "did not complete"):
                LlamaCppLanguage("gemma").translate("Hi", {})

    def test_ollama_discovers_gemma_and_translates_locally(self):
        tags = {"models": [{"name": "gemma-example:small"}]}
        reply = {"done": True, "message": {"content": json.dumps({"kind": "question", "content": "What is Mira?"})}}
        with patch("interface.urlopen", side_effect=[io.BytesIO(json.dumps(tags).encode()),
                                                      io.BytesIO(json.dumps(reply).encode())]) as mock:
            translator = OllamaLanguage()
            result = translator.translate("Tell me about Mira", {})
        self.assertEqual(translator.model, "gemma-example:small")
        self.assertEqual(result["kind"], "question")
        request = mock.call_args[0][0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(json.loads(request.data)["format"]["required"], ["operations"])

    def test_ollama_multiple_models_requires_selection(self):
        tags = {"models": [{"name": "gemma-a"}, {"name": "gemma-b"}]}
        with patch("interface.urlopen", return_value=io.BytesIO(json.dumps(tags).encode())):
            with self.assertRaisesRegex(ValueError, "Pass --model"):
                OllamaLanguage()

    def test_language_cannot_impersonate_sensor(self):
        session = Session()
        with self.assertRaises(ValueError):
            session.apply("I saw it roll", {"kind": "sensor", "content": "roll Amber yes"})
        self.assertEqual(session.sensors.events, [])
        self.assertEqual(session.explorer.episodes, [])

    def test_statements_keep_provenance_and_queries_use_core(self):
        session = Session()
        session.apply("Mira's a person", {"kind": "statement", "content": "Mira is a person."})
        answer = session.apply("Is Mira a gardener?", {"kind": "question", "content": "Is Mira a gardener?"})
        self.assertTrue(answer.startswith("Unknown"))
        self.assertEqual(session.language_records[0]["original"], "Mira's a person")
        self.assertEqual(session.sensors.events, [])

    def test_sensor_learning_and_persistence(self):
        session = Session()
        for _ in range(10):
            session.explore()
        session.apply("Name it", {"kind": "name", "content": "Call things that roll roller."})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            session.save(path)
            restored = Session.load(path)
            self.assertEqual(session.explorer.report(), restored.explorer.report())
            self.assertEqual(session.sensors.events, restored.sensors.events)
            self.assertEqual(restored.explorer.ask("Is Amber a roller?"), "yes")
            self.assertTrue(all(e["observed_at"] and e["source"] == "toy-world" for e in restored.sensors.events))

    def test_bad_sensor_does_not_change_beliefs(self):
        class BadSensor:
            def measure(self, action, entity):
                return "yes"
        session = Session()
        hub = SensorHub()
        hub.register("broken", BadSensor())
        with self.assertRaises(ValueError):
            hub.experiment("broken", "roll", "Amber", session.explorer)
        self.assertEqual(session.explorer.episodes, [])

    def test_reusable_surface_exposes_perception_and_actions(self):
        state = {"value": 0}
        surface = CanvasSurface(lambda: {"value": state["value"]},
                                {"increment": lambda args: {"value": state.__setitem__("value", state["value"] + int(args.get("amount", 1))) or state["value"]}})
        hub = SensorHub()
        hub.register_surface("test-canvas", surface)
        self.assertEqual(hub.perceive("test-canvas"), {"value": 0})
        self.assertEqual(hub.act("test-canvas", "increment", {"amount": 2}), {"value": 2})
        self.assertEqual(hub.perceive("test-canvas"), {"value": 2})
        self.assertEqual([event["kind"] for event in hub.events], ["perception", "action", "perception"])

    def test_sudoku_canvas_is_a_registered_surface(self):
        session = Session()
        perception = session.perceive("sudoku-canvas")
        self.assertEqual(perception["cells"][0]["value"], 5)
        session.act_sensor("sudoku-canvas", "select", {"row": 0, "col": 2})
        session.act_sensor("sudoku-canvas", "place", {"row": 0, "col": 2, "value": 4})
        self.assertEqual(session.sudoku.grid[0][2], 4)

    def test_api_request_and_response_without_network(self):
        data = {"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps({"kind": "question", "content": "What is Mira?"})}]}]}
        with patch("interface.urlopen", return_value=io.BytesIO(json.dumps(data).encode())) as mock:
            translator = OpenAILanguage("test-model", api_key="test-key")
            result = translator.translate("Tell me about Mira", {})
        self.assertEqual(result["kind"], "question")
        request = json.loads(mock.call_args[0][0].data)
        self.assertFalse(request["store"])
        self.assertTrue(request["text"]["format"]["strict"])


if __name__ == "__main__":
    unittest.main()
