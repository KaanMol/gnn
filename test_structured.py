import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from interface import Session
from semantics import operation


class StructuredTests(unittest.TestCase):
    def setUp(self):
        self.session = Session()

    def apply(self, *ops):
        return self.session.apply("test evidence", {"operations": list(ops)})

    def test_multiword_entities_and_properties_bypass_sentence_parser(self):
        with patch("knowledge.parse", side_effect=AssertionError("Legacy parser called")):
            self.apply(operation("assert", "Mary Jane", "live in", "New York"),
                       operation("assert", "Mary Jane", "age", "32"),
                       operation("assert", "Mary Jane", "like", "green tea"))
            self.assertIn("New York", self.apply(operation("describe", "Mary Jane", "live in")))
            self.assertTrue(self.apply(operation("query", "mary jane", "age", "32")).startswith("Yes"))

    def test_correction_retracts_obsolete_inference(self):
        self.apply(operation("assert", "Mira", "is", "person"),
                   operation("assert", "Fern", "is", "plant"),
                   operation("assert", "Mira", "grow", "Fern"),
                   operation("define", "gardener", conditions=[
                       {"relation": "is", "object": "person", "target_type": False},
                       {"relation": "grow", "object": "plant", "target_type": True}]))
        self.assertTrue(self.apply(operation("query", "Mira", "is", "gardener")).startswith("Yes"))
        self.apply(operation("retract", "Fern", "is", "plant"),
                   operation("assert", "Fern", "is", "sculpture"))
        self.assertTrue(self.apply(operation("query", "Mira", "is", "gardener")).startswith("Unknown"))

    def test_invalid_batch_does_not_partly_retract(self):
        self.apply(operation("assert", "Kaan", "age", "30"))
        with self.assertRaises(ValueError):
            self.apply(operation("retract", "Kaan", "age", "30"),
                       operation("define", "invalid", conditions=[]))
        self.assertIn(("age", "Kaan", "30"), self.session.core.facts)

    def test_negation_conflict_and_correction(self):
        self.apply(operation("assert", "Mira", "like", "coffee", negative=True))
        self.assertTrue(self.apply(operation("query", "Mira", "like", "coffee")).startswith("No"))
        self.apply(operation("assert", "Mira", "like", "coffee"))
        self.assertIn("Conflicting", self.apply(operation("query", "Mira", "like", "coffee")))
        self.apply(operation("retract", "Mira", "like", "coffee", negative=True))
        self.assertTrue(self.apply(operation("query", "Mira", "like", "coffee")).startswith("Yes"))

    def test_redefinition_updates_derived_facts(self):
        condition = lambda obj: [{"relation": "is", "object": obj, "target_type": False}]
        self.apply(operation("assert", "Mira", "is", "person"),
                   operation("define", "helper", conditions=condition("person")))
        self.assertIn(("is", "Mira", "helper"), self.session.core.facts)
        self.apply(operation("redefine", "helper", conditions=condition("robot")))
        self.assertNotIn(("is", "Mira", "helper"), self.session.core.facts)

    def test_clarification_never_changes_facts_and_rejects_legacy_live_output(self):
        class BadTranslator:
            def translate(self, utterance, context):
                return {"kind": "statement", "content": "Mira is a person."}
        answer = self.session.chat("What if Mira is a person?", BadTranslator())
        self.assertIn("meaning", answer)
        self.assertEqual(self.session.core.facts, {})
        self.assertEqual(self.session.language_records[-1]["translation"]["operations"][0]["op"], "clarify")

    def test_question_cannot_write_even_if_translator_proposes_assertion(self):
        class BadTranslator:
            def translate(self, utterance, context):
                return {"operations": [operation("assert", "Mira", "is", "person")]}
        self.assertIn("haven't changed memory", self.session.chat("Is Mira a person?", BadTranslator()))
        self.assertEqual(self.session.core.facts, {})

    def test_definition_preserves_base_type_field(self):
        self.apply(operation("define", "gardener", "is", "person", conditions=[
            {"relation": "grow", "object": "plant", "target_type": True}]))
        self.apply(operation("assert", "Robot", "grow", "Fern"), operation("assert", "Fern", "is", "plant"))
        self.assertNotIn(("is", "Robot", "gardener"), self.session.core.facts)
        self.apply(operation("assert", "Mira", "is", "gardener"))
        self.assertIn(("is", "Mira", "person"), self.session.core.facts)

    def test_possessive_relationship_keeps_speaker_and_is_describable(self):
        self.apply(operation("identify", "Alex"), operation("assert", "Maya", "girlfriend of", "speaker"))
        self.assertIn(("girlfriend of", "Maya", "Alex"), self.session.core.facts)
        self.assertIn("Alex", self.apply(operation("describe", "Maya", "is")))

    def test_taught_symmetry_derives_reverse_and_explains(self):
        self.apply(operation("assert", "Julia", "is dating", "Kaan"))
        self.assertTrue(self.apply(operation("query", "Kaan", "is dating", "Julia")).startswith("Unknown"))
        self.apply(operation("symmetric", relation="is dating"))
        self.assertTrue(self.apply(operation("query", "Kaan", "is dating", "Julia")).startswith("Yes"))
        self.assertEqual(self.session.core.facts[("is dating", "Kaan", "Julia")][1],
                         (("is dating", "Julia", "Kaan"),))
        self.apply(operation("forget_symmetry", relation="is dating"))
        self.assertNotIn(("is dating", "Kaan", "Julia"), self.session.core.facts)
        self.assertIn(("is dating", "Julia", "Kaan"), self.session.core.facts)

    def test_symmetric_fact_correction_removes_reverse(self):
        self.apply(operation("symmetric", relation="next to"), operation("assert", "Oak", "next to", "Birch"))
        self.apply(operation("retract", "Oak", "next to", "Birch"))
        self.assertNotIn(("next to", "Birch", "Oak"), self.session.core.facts)

    def test_find_incoming_edges_filters_type_and_conflicting_evidence(self):
        self.apply(operation("assert", "Dordrecht", "is", "city"),
                   operation("assert", "Dordrecht", "located in", "The Netherlands"),
                   operation("assert", "Krimpen aan den Ijssel", "is", "town"),
                   operation("assert", "Krimpen aan den Ijssel", "located in", "The Netherlands"),
                   operation("assert", "Kaan", "live in", "The Netherlands"))
        before = dict(self.session.core.facts)
        answer = self.apply(operation("find", relation="located in", obj="the netherlands"))
        self.assertIn("Dordrecht", answer)
        self.assertIn("Krimpen aan den Ijssel", answer)
        self.assertNotIn("Kaan", answer)
        self.assertEqual(before, self.session.core.facts)
        answer = self.apply(operation("find", "town", "located in", "The Netherlands"))
        self.assertNotIn("Dordrecht", answer)
        self.assertIn("Krimpen aan den Ijssel", answer)
        self.apply(operation("assert", "Dordrecht", "located in", "The Netherlands", negative=True))
        answer = self.apply(operation("find", relation="located in", obj="The Netherlands"))
        self.assertIn("Conflicting evidence excluded: Dordrecht", answer)

    def test_explicit_location_clauses_preserve_both_facts(self):
        class NoModel:
            def translate(self, *args):
                raise AssertionError("Explicit location clause should not need Gemma")
        for text in ["Dordrecht is a city in The Netherlands", "The Netherlands is a country in Europe",
                     "Europe is a continent on the planet Earth", "Krimpen aan den Ijssel is a town in The Netherlands"]:
            self.session.chat(text, NoModel())
        self.assertIn(("located in", "The Netherlands", "Europe"), self.session.core.facts)
        self.assertIn(("located in", "Europe", "Earth"), self.session.core.facts)
        self.assertIn(("is", "Earth", "planet"), self.session.core.facts)
        answer = self.session.chat("So, what places are in The Netherland?", NoModel())
        self.assertIn("Dordrecht", answer)
        self.assertIn("Krimpen aan den Ijssel", answer)
        from location_language import direct_location
        for text in ["If Dordrecht is a city in Europe", "Dordrecht is not a city in Europe",
                     "Dordrecht is a city in Europe or Asia", "Maybe Dordrecht is a city in Europe"]:
            self.assertIsNone(direct_location(text))

    def test_dialogue_roles_distinguish_user_and_assistant(self):
        class NoModel:
            def translate(self, *args): raise AssertionError("Identity has explicit dialogue roles")
        self.apply(operation("identify", "Kaan"), operation("assert", "Kaan", "live in", "Dordrecht"))
        before = dict(self.session.core.facts)
        answer = self.session.chat("Who are you?", NoModel())
        self.assertIn("I am Seed", answer)
        self.assertNotIn("Dordrecht", answer)
        self.assertIn("Dordrecht", self.session.chat("Who am I?", NoModel()))
        self.assertEqual(before, self.session.core.facts)
        self.apply(operation("assert", "speaker", "talk to", "you"))
        self.assertIn(("talk to", "Kaan", "Seed"), self.session.core.facts)
        self.assertEqual(self.session.context()["addressee"], "Seed")
        anonymous = Session()
        self.assertIn("I am Seed", anonymous.chat("What's your name?", NoModel()))
        self.assertIn("What name", anonymous.chat("Who am I?", NoModel()))

    def test_age_pronoun_reaches_contextual_translation(self):
        self.apply(operation("assert", "Julia", "birth date", "2001-07-21"))
        seen = []
        class Translator:
            def translate(self, utterance, context):
                seen.append(context)
                return {"operations": [operation("date_procedure", "Julia", "age_years")]}
        answer = self.session.chat("How old is she?", Translator())
        self.assertEqual(len(seen), 1)
        self.assertIn("haven't learned", answer)
        self.assertNotIn("she's", answer)

    def test_speaker_and_corrections_persist(self):
        self.apply(operation("identify", "Mary Jane"), operation("assert", "speaker", "age", "30"))
        self.apply(operation("retract", "Mary Jane", "age", "30"), operation("assert", "Mary Jane", "age", "31"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            self.session.save(path)
            restored = Session.load(path)
        self.assertEqual(restored.speaker, "Mary Jane")
        self.assertEqual(restored.core.facts, self.session.core.facts)
        self.assertNotIn(("age", "Mary Jane", "30"), restored.core.facts)


if __name__ == "__main__":
    unittest.main()
