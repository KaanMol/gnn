import tempfile
import unittest
from pathlib import Path

from meaning import ConceptCategory, DEMO, LanguageError, MeaningSystem


class MeaningTests(unittest.TestCase):
    def test_learns_definition_and_generalizes(self):
        system = MeaningSystem()
        for statement in DEMO:
            system.tell(statement)
        self.assertTrue(system.ask("Is Mira a gardener?").startswith("Yes."))
        system.tell("Theo is a person.")
        system.tell("Theo grows Fern.")
        self.assertTrue(system.ask("Is Theo a gardener?").startswith("Yes."))
        self.assertIn("Fern is a rose.", system.ask("Why is Theo a gardener?"))

    def test_unknown_and_missing_constraint(self):
        system = MeaningSystem()
        for statement in DEMO[:-1]:
            system.tell(statement)
        system.tell("Mira grows Rock.")
        self.assertTrue(system.ask("Is Mira a gardener?").startswith("Unknown"))
        system.tell("Rock is a plant.")
        self.assertTrue(system.ask("Is Mira a gardener?").startswith("Yes."))

    def test_order_independence_and_cycles(self):
        system = MeaningSystem()
        for statement in reversed(DEMO):
            system.tell(statement)
        system.tell("A plant is a rose.")
        self.assertTrue(system.ask("Is Mira a gardener?").startswith("Yes."))

    def test_rejects_unsupported_and_redefinition_without_mutation(self):
        system = MeaningSystem()
        system.tell(DEMO[0])
        before = list(system.statements)
        for bad in ["Mira is not a person.", "Mira might grow a plant.",
                    "A gardener is a robot who grows a plant."]:
            with self.assertRaises(LanguageError):
                system.tell(bad)
            self.assertEqual(before, system.statements)

    def test_persistence(self):
        system = MeaningSystem()
        for statement in DEMO:
            system.tell(statement)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            system.save(path)
            restored = MeaningSystem.load(path)
        self.assertEqual(system.ask("Is Mira a gardener?"), restored.ask("Is Mira a gardener?"))

    def test_category_laws(self):
        category = ConceptCategory()
        for pair in [("rose", "plant"), ("plant", "organism"), ("organism", "thing")]:
            category.add(*pair)
        f, g, h = ("rose", "plant"), ("plant", "organism"), ("organism", "thing")
        self.assertEqual(category.compose(("rose", "rose"), f), f)
        self.assertEqual(category.compose(f, ("plant", "plant")), f)
        self.assertEqual(category.compose(category.compose(f, g), h),
                         category.compose(f, category.compose(g, h)))
        with self.assertRaises(ValueError):
            category.compose(g, f)


if __name__ == "__main__":
    unittest.main()
