"""Integration checks for authoritative graph memory and one-time migration."""
import copy
import json
import sqlite3
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from graph_runtime import execute_graph
from graph_store import GraphStore, database_path
from graph_view import snapshot
from interface import Session
from semantics import operation


class NoModel:
    def translate(self, *args):
        raise AssertionError('This check must not use the language model')


def constant(value):
    return {'input_type': 'Unit', 'output_type': 'Number', 'nodes': [
        {'id': 'answer', 'op': 'literal', 'type': 'Number', 'inputs': [], 'value': value}], 'output': 'answer'}


class GraphStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'memory.json'

    def session(self):
        s = Session.load(self.path)
        self.addCleanup(s.store.close)
        return s

    def test_typed_nodes_edges_and_read_only_lookup(self):
        store = GraphStore()
        self.addCleanup(store.close)
        value = {'graph': constant(4), 'proof': (('is', 'Mira', 'person'),), 'exact': Fraction(2, 3)}
        key = (('is', 'Mira', 'person'), False)
        store.map('test')[key] = value
        before = store.connection.total_changes
        self.assertEqual(store.map('test')[key], value)
        self.assertNotIn('absent', store.map('test'))
        self.assertEqual(store.connection.total_changes, before)
        graph = store.inspect('test')
        self.assertEqual(graph['schema'], 'seed.graph-database.v1')
        self.assertTrue(graph['edges'])
        root_id = graph['roots'][0]['value']
        self.assertEqual(store.connection.execute('SELECT kind,atom FROM nodes WHERE id=?', (root_id,)).fetchone(), ('record', None))
        for kind, atom in store.connection.execute('SELECT kind,atom FROM nodes'):
            if kind in ('record', 'list', 'tuple'):
                self.assertIsNone(atom)
        store.save(self.path)
        loaded = GraphStore(database_path(self.path))
        self.addCleanup(loaded.close)
        self.assertEqual(loaded.map('test')[key], value)

    def test_nested_updates_commit_and_stale_views_cannot_restore_deleted_roots(self):
        s = self.session()
        s.teach_graph('answer', constant(4))
        s.save(self.path)
        s.core.procedures['answer']['graph']['nodes'][0]['value'] = 9
        r = self.session()
        self.assertEqual(execute_graph(r.core.procedures['answer']['graph'], library=r.core.procedures)[0], 9)
        old = s.core.procedures['answer']
        s.forget_graph('answer')
        with self.assertRaisesRegex(ValueError, 'changed'):
            old['graph']['nodes'][0]['value'] = 3
        self.assertNotIn('answer', r.core.procedures)
        self.assertTrue(any(e['translation'].get('kind') == 'graph_definition' for e in r.language_records))

    def test_rollback_does_not_leave_nodes_or_mutate_current_knowledge(self):
        s = self.session()
        s.teach_graph('answer', constant(4))
        before = snapshot(s)
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            with s.store.transaction():
                s.core.procedures['answer']['graph']['nodes'][0]['value'] = 999
                s.settings['unsupported'] = object()
        self.assertEqual(snapshot(s), before)
        # Encoding the same value again after rollback must create real nodes.
        s.core.procedures['answer']['graph']['nodes'][0]['value'] = 999
        self.assertEqual(execute_graph(s.core.procedures['answer']['graph'], library=s.core.procedures)[0], 999)
        assertions = copy.deepcopy(s.core.assertions)
        records = copy.deepcopy(s.language_records)
        with self.assertRaises(ValueError):
            s.apply('bad correction', {'operations': [
                operation('assert', 'Mira', 'is', 'person'),
                operation('retract', 'Unknown', 'is', 'person')]})
        self.assertEqual(s.core.assertions, assertions)
        self.assertEqual(s.language_records, records)

    def test_current_roots_are_authoritative_for_live_queries_and_restart(self):
        s = self.session()
        s.apply('Mira is a person', {'operations': [operation('assert', 'Mira', 'is', 'person')]})
        s.save(self.path)
        # Edit through a second graph connection, not by replaying a message.
        other = GraphStore(database_path(self.path))
        self.addCleanup(other.close)
        other.map('knowledge.assertions').clear()
        self.assertNotIn('Mira', s.core.entities)
        self.assertTrue(s.core.query('Mira', 'is', 'person').startswith('Unknown'))
        with patch.object(Session, 'apply', side_effect=AssertionError('History replayed')):
            restored = self.session()
        self.assertEqual(restored.core.assertions, {})
        self.assertEqual(len(restored.language_records), 1)

    def test_one_store_for_identity_world_lessons_proofs_history_and_sensors(self):
        s = self.session()
        for view in (s.core.procedures, s.core.assertions, s.core.math_lessons,
                     s.core.sudoku_lessons, s.core.facts, s.language_records,
                     s.explorer.words, s.explorer.episodes, s.explorer.graph.facts,
                     s.explorer.space, s.sensors.events, s.settings):
            self.assertIs(view.store, s.store)
        s.speaker, s.assistant_name = 'Kaan', 'Nex'
        s.explore()
        s.explorer.name('Call things that roll roller.')
        s.apply('dating', {'operations': [operation('assert', 'Julia', 'dating', 'Kaan')]})
        s.core.symmetry('dating', 'mutual relationship')
        s.act_sensor('canvas', 'move', {'x': .5, 'y': .5})
        s.act_sensor('canvas', 'click')
        s.act_sensor('canvas', 'key', {'key': '9'})
        s.save(self.path)
        r = self.session()
        self.assertEqual((r.speaker, r.assistant_name), ('Kaan', 'Nex'))
        self.assertEqual(s.sensors.events, r.sensors.events)
        self.assertEqual(s.explorer.report(), r.explorer.report())
        self.assertEqual(s.explorer.graph.facts, r.explorer.graph.facts)
        self.assertEqual(r.core.facts[('dating', 'Kaan', 'Julia')][1], (('dating', 'Julia', 'Kaan'),))
        self.assertEqual(r.sudoku.grid[4][4], 9)
        self.assertEqual(r.canvas.pointer, {'x': .5, 'y': .5})
        self.assertEqual(r.canvas.feedback, s.canvas.feedback)

    def test_legacy_import_preserves_history_and_never_repeats_it(self):
        original = Session()
        self.addCleanup(original.store.close)
        original.speaker = 'Mira'
        original.apply('Mira is a person.', {'kind': 'statement', 'content': 'Mira is a person.'})
        original.teach_graph('answer', constant(4))
        original.forget_graph('answer')
        original.explore()
        original.act_sensor('canvas', 'move', {'x': .1, 'y': .2})
        data = {'language': list(original.language_records), 'sensors': list(original.sensors.events),
                'canvas': {'grid': original.sudoku.grid, 'givens': original.sudoku.givens, 'selected': [1, 2], 'recent': None}}
        self.path.write_text(json.dumps(data))
        legacy = self.path.read_bytes()
        with patch('sensors.SensorHub.act', side_effect=AssertionError('Replayed device action')):
            migrated = self.session()
        self.assertEqual(migrated.language_records, original.language_records)
        self.assertEqual(migrated.sensors.events, original.sensors.events)
        self.assertEqual(migrated.core.facts, original.core.facts)
        self.assertEqual(migrated.explorer.episodes, original.explorer.episodes)
        self.assertNotIn('answer', migrated.core.procedures)
        self.assertEqual(migrated.sudoku.selected, [1, 2])
        self.assertEqual(migrated.canvas.pointer, original.canvas.pointer)
        self.assertEqual(migrated.canvas.feedback, original.canvas.feedback)
        self.assertEqual(self.path.read_bytes(), legacy)
        # An obsolete or broken JSON backup cannot change the active database.
        self.path.write_text('THIS IS NOT A NOTEBOOK ANYMORE')
        with patch.object(Session, 'apply', side_effect=AssertionError('History replayed')):
            restored = self.session()
        self.assertEqual(restored.language_records, original.language_records)
        self.assertNotIn('answer', restored.core.procedures)
        self.path.unlink()
        self.assertEqual(self.session().core.facts, original.core.facts)

    def test_migration_failure_does_not_publish_half_a_database(self):
        self.path.write_text(json.dumps({'sensors': [], 'language': [
            {'original': 'bad', 'translation': {'kind': 'unsupported', 'content': 'failure'}}]}))
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            Session.load(self.path)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(database_path(self.path).exists())

    def test_newer_or_corrupt_database_never_falls_back_to_notebook(self):
        s = self.session()
        s.save(self.path)
        self.path.write_text(json.dumps({'language': [], 'sensors': []}))
        connection = sqlite3.connect(str(database_path(self.path)))
        connection.execute('PRAGMA user_version=999')
        connection.close()
        with self.assertRaisesRegex(ValueError, 'Unsupported graph database version'):
            Session.load(self.path)

    def test_curricula_run_from_database_and_forgotten_dependencies_stay_missing(self):
        s = self.session()
        s.teach_algebra_suite()
        s.teach_sudoku_suite()
        s.save(self.path)
        with patch.object(Path, 'read_text', side_effect=AssertionError('Loaded a curriculum or notebook')):
            r = self.session()
            self.assertIn('x = 4', r.chat('Solve: 5x=20', NoModel()))
            check = r.run_sensor_graph('sudoku_observe_check')
            self.assertIsNotNone(check['result'])
            self.assertIn('valid', check['result'])
        s.forget_graph('poly_multiply')
        s.forget_graph('sudoku_symbol')
        with patch.object(Session, 'apply', side_effect=AssertionError('Replayed teaching')):
            r = self.session()
        self.assertIn('Missing taught procedure: poly_multiply', r.chat('Solve: 5x=20', NoModel()))
        board, events = copy.deepcopy(r.sudoku.grid), len(r.sensors.events)
        self.assertIn('Missing taught procedure: sudoku_symbol', r.run_sensor_graph('sudoku_observe_solve')['answer'])
        self.assertEqual(r.sudoku.grid, board)
        self.assertEqual(len(r.sensors.events), events)


if __name__ == '__main__':
    unittest.main()
