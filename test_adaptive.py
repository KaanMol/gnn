import tempfile
import unittest
from pathlib import Path

from adaptive import AdaptiveLearner
from meaning import MeaningSystem


class AdaptiveTests(unittest.TestCase):
    def setUp(self):
        self.graph = MeaningSystem()
        self.learner = AdaptiveLearner(self.graph)
        self.graph.learner = self.learner
        for statement in ["Fern is a plant.", "Mira is a person.", "Theo is a person.",
                          "Alex is a person.", "Rin is a person.", "Mira grows Fern.",
                          "Theo grows Fern.", "Rin grows Fern."]:
            self.graph.tell(statement)
        self.learner.teach("gardener", "Mira", True)
        self.learner.teach("gardener", "Theo", True)
        self.learner.teach("gardener", "Alex", False)

    def test_induces_and_predicts_unseen_example_without_asserting(self):
        self.assertIn("grows a plant", self.learner.inspect("gardener"))
        self.assertTrue(self.learner.predict("gardener", "Rin").startswith("Provisional match"))
        self.assertNotIn(("is", "Rin", "gardener"), self.graph.facts)

    def test_counterexample_withdraws_then_new_evidence_refines(self):
        self.learner.teach("gardener", "Rin", False)
        self.assertIn("withdrawn", self.learner.inspect("gardener"))
        for statement in ["Mira is a professional.", "Theo is a professional.",
                          "Alex is a professional."]:
            self.graph.tell(statement)
        hypotheses, _ = self.learner.hypotheses("gardener")
        self.assertEqual(hypotheses, [frozenset({("type", "professional"),
                                               ("relation", "grows", "plant")})])

    def test_correcting_label_restores_hypothesis(self):
        self.learner.teach("gardener", "Rin", False)
        self.learner.teach("gardener", "Rin", True)
        self.assertIn("grows a plant", self.learner.inspect("gardener"))

    def test_labels_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            self.graph.save(path)
            restored = MeaningSystem.load(path)
        self.assertEqual(restored.learner.inspect("gardener"), self.learner.inspect("gardener"))

    def test_insufficient_evidence_abstains(self):
        self.assertTrue(self.learner.predict("pilot", "Mira").startswith("Unknown"))


if __name__ == "__main__":
    unittest.main()
