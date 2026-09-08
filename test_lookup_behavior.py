"""Lookup semantics must come from removable lessons, with real proof witnesses."""
import copy
import tempfile
import sqlite3
from pathlib import Path
import unittest
from unittest.mock import patch

from interface import Session
from knowledge import Knowledge
from semantics import operation


class LookupBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.k = Knowledge()
        self.addCleanup(self.k.store.close)

    def policy(self, **changes):
        entry = copy.deepcopy(self.k.procedures['knowledge_lookup_policy'])
        node = next(n for n in entry['graph']['nodes'] if n['id'] == entry['graph']['output'])
        node['value'].update(changes)
        self.k.procedures['knowledge_lookup_policy'] = entry

    def teach(self, subject, relation, obj, negative=False):
        return self.k.assert_fact(subject, relation, obj, negative, f'Teacher: {subject} / {relation} / {obj}')

    def test_unseen_entities_use_naming_evidence_in_both_directions(self):
        self.teach('Homo sapiens', 'ncbi common name', 'human')
        self.teach('Bryan', 'is', 'human')
        answer = self.k.query('Bryan', 'is', 'Homo sapiens')
        self.assertTrue(answer.startswith('Yes.'))
        self.assertIn('Teacher: Homo sapiens', answer)
        self.assertIn('Teacher: Bryan', answer)
        self.assertEqual(set(self.k.facts['is','Bryan','homo sapiens'][1]),
            {('is','Bryan','human'), ('ncbi common name','Homo sapiens','human')})
        self.teach('Mus musculus', 'ncbi common name', 'house mouse')
        self.teach('Pip', 'is', 'mus musculus')
        self.assertTrue(self.k.query('Pip', 'is', 'house mouse').startswith('Yes.'))
        self.teach('Lumi', 'is', 'house mouse')
        self.assertTrue(self.k.query('Lumi', 'is', 'mus musculus').startswith('Yes.'))

    def test_shared_neighbors_do_not_imply_equivalence(self):
        self.teach('Homo sapiens', 'studies', 'human')
        self.teach('Bryan', 'is', 'human')
        self.assertTrue(self.k.query('Bryan', 'is', 'homo sapiens').startswith('Unknown'))
        self.policy(name_relations=['studies'])
        self.assertTrue(self.k.query('Bryan', 'is', 'homo sapiens').startswith('Yes'))
        self.policy(name_relations=[])
        self.assertNotIn(('is','Bryan','homo sapiens'), self.k.facts)

    def test_ambiguity_and_contradicted_names_do_not_guess(self):
        self.teach('Species alpha', 'concept name', 'mouse')
        self.teach('Species beta', 'concept name', 'mouse')
        self.teach('Pip', 'is', 'mouse')
        for name in ['species alpha', 'species beta']:
            self.assertTrue(self.k.query('Pip', 'is', name).startswith('Unknown'))
        self.k.retract('Species beta', 'concept name', 'mouse', False)
        self.assertTrue(self.k.query('Pip', 'is', 'species alpha').startswith('Yes'))
        self.teach('Species alpha', 'concept name', 'mouse', negative=True)
        self.assertTrue(self.k.query('Pip', 'is', 'species alpha').startswith('Unknown'))
        self.k.retract('Species alpha', 'concept name', 'mouse', True)
        self.assertTrue(self.k.query('Pip', 'is', 'species alpha').startswith('Yes'))

    def test_alias_negation_and_conflict_are_preserved(self):
        self.teach('Homo sapiens', 'ncbi common name', 'human')
        self.teach('Rover', 'is', 'human', negative=True)
        self.assertTrue(self.k.query('Rover', 'is', 'homo sapiens').startswith('No'))
        self.teach('Rover', 'is', 'homo sapiens')
        for name in ['human','homo sapiens']:
            self.assertTrue(self.k.query('Rover', 'is', name).startswith('Conflicting'))
        self.assertTrue(self.k.query('Stranger', 'is', 'human').startswith('Unknown'))

    def test_spelling_requires_explicit_teaching_and_can_be_forgotten(self):
        self.teach('Homo sapiens', 'ncbi common name', 'human')
        self.teach('Bryan', 'is', 'human')
        self.assertTrue(self.k.query('Bryan', 'is', 'homo sapien').startswith('Unknown'))
        self.policy(spelling_variants=[{'variant':'homo sapien','canonical':'homo sapiens',
                                       'source':'Explicit spelling lesson from teacher'}])
        self.assertIn('Explicit spelling lesson', self.k.query('Bryan', 'is', 'homo sapien'))
        self.policy(spelling_variants=[])
        self.assertTrue(self.k.query('Bryan', 'is', 'homo sapien').startswith('Unknown'))
        del self.k.procedures['knowledge_name_rules']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'memory.sqlite3'
            with sqlite3.connect(path) as destination:
                self.k.store.connection.backup(destination)
            from graph_store import GraphStore
            with patch('foundation.curriculum', side_effect=AssertionError('Must not reload lessons')):
                restored = Knowledge(GraphStore(path))
                try:
                    self.assertNotIn(('is','Bryan','homo sapiens'), restored.facts)
                    self.assertIn(('is','Bryan','human'), restored.facts)
                    self.assertIn('knowledge_name_rules', restored.reasoning_error)
                finally:
                    restored.store.close()

    def test_general_rule_joins_new_relations_and_retracts(self):
        rule = {'when': [['inside', {'var':'a'}, {'var':'b'}], ['inside', {'var':'b'}, {'var':'c'}]],
                'then': ['inside', {'var':'a'}, {'var':'c'}], 'source': 'Teacher: containment composes'}
        self.policy(rules=[rule])
        self.teach('Coin', 'inside', 'Box')
        self.teach('Box', 'inside', 'Room')
        self.assertTrue(self.k.query('Coin','inside','Room').startswith('Yes'))
        self.assertIn('Teacher: containment composes', self.k.query('Coin','inside','Room'))
        self.k.retract('Box','inside','Room',False)
        self.assertTrue(self.k.query('Coin','inside','Room').startswith('Unknown'))
        self.teach('Box','inside','Room')
        self.policy(rules=[])
        self.assertTrue(self.k.query('Coin','inside','Room').startswith('Unknown'))

    def test_unknown_can_ask_without_learning_and_handoff_a_precise_reply(self):
        s = Session(store=self.k.store)
        before = dict(s.core.assertions)
        answer = s.apply_structured('Is Mira a gardener?', {'operations':[operation('query','Mira','is','gardener')]})
        self.assertIn('Can you explain', answer)
        self.assertEqual(dict(s.core.assertions), before)
        self.assertEqual(s.store.map('interaction.state')['waiting']['resume'], 'knowledge_lookup_reply')
        class NoModel:
            def translate(self, *args): raise AssertionError('No translation needed')
        self.assertIn('whole statement', s.chat('yes', NoModel()))
        self.assertEqual(dict(s.core.assertions), before)
        class TeacherLanguage:
            def translate(self, text, context):
                return {'operations':[operation('assert','Mira','is','gardener')]}
        self.assertIn('Learned: Mira is a gardener', s.chat('Mira is a gardener', TeacherLanguage()))
        self.assertIsNone(s.store.map('interaction.state').get('waiting'))

    def test_asking_policy_can_be_revised(self):
        self.policy(ask_when_unknown=False)
        s = Session(store=self.k.store)
        answer = s.apply_structured('Is Mira a gardener?', {'operations':[operation('query','Mira','is','gardener')]})
        self.assertTrue(answer.startswith('Unknown'))
        self.assertIsNone(s.store.map('interaction.state').get('waiting'))


if __name__ == '__main__': unittest.main()
