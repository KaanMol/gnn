"""Guard against duplicate inference and preserve semantics of the speedups."""
import copy
import unittest
from unittest.mock import patch

import foundation
from graph_dsl import G
from graph_runtime import execute_graph
from graph_store import GraphStore
from interface import Session
from knowledge import Knowledge
from semantics import operation


class TeachingPerformanceTests(unittest.TestCase):
    def test_one_rebuild_for_one_new_fact_and_none_for_staging_or_commit(self):
        s = Session()
        self.addCleanup(s.store.close)
        original = Knowledge._rebuild
        calls = []
        def counted(core):
            calls.append(core.prefix)
            return original(core)
        with patch.object(Knowledge, '_rebuild', counted):
            s.apply_structured('new fact', {'operations': [operation('assert', 'Mira', 'is', 'person')]})
        self.assertEqual(calls, ['knowledge'])
        self.assertIn(('is', 'Mira', 'person'), s.core.facts)
        self.assertIs(s.core.category.knowledge, s.core)

    def test_staging_uses_same_source_roots_and_cannot_mutate_live_values(self):
        s = Session()
        self.addCleanup(s.store.close)
        s.core.assert_fact('Mira', 'knows', 'Lio', False, 'teacher')
        s.core.symmetry('knows', 'mutual')
        staged = copy.deepcopy(s.core)
        self.addCleanup(staged.store.close)
        self.assertEqual(staged._source_version, s.core._source_version)
        staged.retract('Mira', 'knows', 'Lio', False)
        self.assertIn(('knows', 'Lio', 'Mira'), s.core.facts)
        self.assertNotIn(('knows', 'Lio', 'Mira'), staged.facts)
        s.core.adopt(staged)
        self.assertNotIn(('knows', 'Lio', 'Mira'), s.core.facts)
        del s.core.procedures['horn_join']
        changed = copy.deepcopy(s.core)
        self.addCleanup(changed.store.close)
        self.assertIn('horn_join', changed.reasoning_error)

    def test_page_clone_keeps_requested_roots_and_handles_open_transactions(self):
        source = GraphStore()
        self.addCleanup(source.close)
        source.map('keep')['item'] = {'values': [1, 2]}
        source.map('omit')['private'] = 'not a staging root'
        for transactional in [False, True]:
            def clone():
                target = source.clone_namespaces(['keep'])
                self.addCleanup(target.close)
                self.assertEqual(dict(target.map('omit')), {})
                self.assertEqual(target.map('keep')['item'], {'values': [1, 2]})
                target.map('keep')['item']['values'][0] = 99
                self.assertEqual(source.map('keep')['item']['values'], [1, 2])
            if transactional:
                with source.transaction(): clone()
            else: clone()

    def test_candidate_narrowing_preserves_variable_relations_and_shared_bindings(self):
        lib = foundation.curriculum()
        facts = [['likes','A','B'], ['likes','B','C'], ['knows','A','D'], ['likes','D','D']]
        def join(patterns):
            arg = {'patterns': patterns, 'facts': [{'fact': f, 'source': 'teacher', 'premises': []} for f in facts]}
            return execute_graph(lib['horn_join']['graph'], arg, lib)[0]
        self.assertEqual(join([['likes',{'var':'x'},{'var':'x'}]])[0]['bindings'], {'x':'D'})
        self.assertEqual([r['bindings'] for r in join([[{'var':'relation'},'A',{'var':'target'}]])],
                         [{'relation':'likes','target':'B'}, {'relation':'knows','target':'D'}])
        results = join([['likes','A',{'var':'middle'}],['likes',{'var':'middle'},{'var':'end'}]])
        self.assertEqual(results, [{'bindings':{'middle':'B','end':'C'},'premises':facts[:2]}])
        self.assertEqual(join([['absent',{'var':'x'},{'var':'y'}]]), [])

    def test_literal_reuse_does_not_leak_values_across_executions(self):
        g = G()
        graph = g.finish(g.data({'table': {'a': [1, 2, 3]}}))
        first, _ = execute_graph(graph)
        first['table']['a'].append(99)
        second, _ = execute_graph(graph)
        self.assertEqual(second, {'table': {'a': [1, 2, 3]}})
        huge = copy.deepcopy(graph)
        huge['nodes'][1]['value'] = [None] * 2001
        with self.assertRaisesRegex(ValueError, 'budget|bounded'):
            execute_graph(huge)


if __name__ == '__main__':
    unittest.main()
