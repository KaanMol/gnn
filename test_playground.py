import tempfile
import unittest
from pathlib import Path

from playground import Explorer, ToyWorld


class PlaygroundTests(unittest.TestCase):
    def test_explores_and_predicts_untried_objects(self):
        world = ToyWorld()
        explorer = Explorer(world.observe(), world.actions)
        self.assertEqual(explorer.predict("roll", "Amber"), "uncertain")
        for _ in range(20):
            if explorer.step(world) is None:
                break
        self.assertLess(len(explorer.episodes), len(world.observe()) * len(world.actions))
        for action in world.actions:
            for entity in world.observe():
                self.assertEqual(explorer.predict(action, entity), "yes" if world.act(action, entity) else "no")
        self.assertIn((("shape", "sphere"),), explorer.hypotheses("roll"))
        self.assertIn((("material", "wood"),), explorer.hypotheses("float"))

    def test_observation_interface_has_no_outcomes(self):
        world = ToyWorld()
        observations = world.observe()
        self.assertTrue(all(set(f) == {"shape", "material", "color"} for f in observations.values()))
        observations["Amber"]["shape"] = "cube"
        self.assertTrue(world.act("roll", "Amber"))

    def test_changed_outcomes_trigger_revision_and_relearning(self):
        world = ToyWorld()
        explorer = Explorer(world.observe(), world.actions)
        while explorer.step(world) is not None:
            pass
        old_count = len(explorer.episodes)
        result = explorer.record("roll", "Amber", False)
        self.assertTrue(result["revised"])
        self.assertEqual(len(explorer.episodes), old_count + 1)
        for entity, features in world.observe().items():
            explorer.record("roll", entity, features["shape"] == "cube")
        self.assertEqual(explorer.predict("roll", "Amber"), "no")
        self.assertEqual(explorer.predict("roll", "Birch"), "yes")
        self.assertEqual(explorer.predict("float", "Amber"), "yes")

    def test_naming_memory_and_evidence_graph(self):
        world = ToyWorld()
        explorer = Explorer(world.observe(), world.actions)
        while explorer.step(world) is not None:
            pass
        explorer.name("Call things that roll roller.")
        self.assertEqual(explorer.ask("Is Amber a roller?"), "yes")
        self.assertIn(("is", "Episode1", "experience"), explorer.graph.facts)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            explorer.save(path)
            restored = Explorer.load(path)
            self.assertEqual(explorer.episodes, restored.episodes)
            self.assertEqual(explorer.report(), restored.report())
            self.assertEqual(restored.ask("Is Amber a roller?"), "yes")


if __name__ == "__main__":
    unittest.main()
