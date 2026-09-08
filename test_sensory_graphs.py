import itertools
import json
import tempfile
import unittest
from pathlib import Path

from canvas_surface import BoardCanvas
from graph_runtime import execute_graph as raw_execute_graph
from interface import Session
from preview import Application
from sensors import CanvasSurface, SensorHub
from sudoku import SudokuBoard


ROOT = Path(__file__).parent


import foundation
NUMBER_LESSONS = foundation.curriculum()
def execute_graph(graph, argument=None, library=None, **kwargs):
    return raw_execute_graph(graph, argument, NUMBER_LESSONS if library is None else library, **kwargs)


def lesson(name):
    return json.loads((ROOT / 'examples' / (name + '.graph.json')).read_text())


class SensoryGraphTests(unittest.TestCase):
    def test_raw_scene_has_no_solver_facts(self):
        scene = BoardCanvas(SudokuBoard).observe()
        self.assertEqual(len(scene['marks']), 81)
        self.assertEqual(scene['marks'][0]['text'], '5')
        for forbidden in ('candidates', 'given', 'constraints', 'solution', 'row', 'col', 'value'):
            self.assertNotIn('"' + forbidden + '":', json.dumps(scene))

    def test_same_reader_handles_unrelated_surface_and_revised_meanings(self):
        hub = SensorHub()
        hub.register_surface('canvas', CanvasSurface(lambda: {'marks': [{'text': 'warm'}, {'text': 'cool'}]},
                                                     {'noop': lambda args: None}))
        graph = lesson('read_marks')
        table = graph['nodes'][3]['body']['nodes'][2]
        with self.assertRaisesRegex(ValueError, 'No taught interpretation'):
            execute_graph(graph, sensors=hub)
        table['value'] = {'warm': 1, 'cool': 0}
        self.assertEqual(execute_graph(graph, sensors=hub)[0], [1, 0])
        table['value']['cool'] = -1
        self.assertEqual(execute_graph(graph, sensors=hub)[0], [1, -1])
        with self.assertRaisesRegex(ValueError, 'Unknown perception source'):
            execute_graph(graph)

    def test_action_order_and_environment_feedback(self):
        session = Session()
        session.teach_graph('type_at', lesson('type_at'))
        result = session.run_sensor_graph('type_at', {'x': 2.5/9, 'y': .5/9, 'key': '4'})
        self.assertTrue(result['result']['accepted'])
        self.assertEqual(session.sudoku.grid[0][2], 4)
        self.assertEqual([event.get('action', 'observe') for event in session.sensors.events],
                         ['move', 'click', 'key', 'observe'])
        result = session.run_sensor_graph('type_at', {'x': .5/9, 'y': .5/9, 'key': '4'})
        self.assertTrue(result['result']['accepted'])
        self.assertEqual(session.sudoku.grid[0][0], 4)

    def test_failed_run_keeps_prior_action_evidence(self):
        session = Session()
        session.teach_graph('type_at', lesson('type_at'))
        result = session.run_sensor_graph('type_at', {'x': .5/9, 'y': .5/9, 'key': 'unavailable'})
        self.assertIn('Procedure stopped', result['answer'])
        self.assertIn('Completed device actions', result['answer'])
        self.assertEqual(len(session.sensors.events), 2)
        self.assertEqual(session.sudoku.selected, [0, 0])

    def test_graph_cannot_access_rich_legacy_board_adapter(self):
        session = Session()
        graph = lesson('read_marks')
        graph['nodes'][1]['surface'] = 'sudoku-canvas'
        session.teach_graph('read_marks', graph)
        self.assertIn('Unknown perception source', session.run_sensor_graph('read_marks')['answer'])

    def test_persistence_revision_and_forgetting_do_not_replay_inputs(self):
        session = Session()
        graph = lesson('read_marks')
        session.teach_graph('read_marks', graph)
        graph['nodes'][3]['body']['nodes'][2]['value']['5'] = 55
        session.teach_graph('read_marks', graph, replace=True)
        self.assertEqual(session.run_sensor_graph('read_marks')['result'][0], 55)
        session.teach_graph('type_at', lesson('type_at'))
        session.run_sensor_graph('type_at', {'x': 2.5/9, 'y': .5/9, 'key': '4'})
        session.forget_graph('type_at')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'memory.json'
            session.save(path)
            restored = Session.load(path)
            self.assertEqual(restored.sudoku.grid[0][2], 4)  # restore state, never replay actions
            self.assertNotIn('type_at', restored.core.procedures)
            self.assertEqual(session.sensors.events, restored.sensors.events)
            self.assertEqual(restored.run_sensor_graph('read_marks')['result'][0], 55)
            with self.assertRaisesRegex(ValueError, 'Teach that procedure'):
                restored.run_sensor_graph('type_at')

    def test_preview_teach_run_forget(self):
        class Translator:
            model = 'fixture'
        with tempfile.TemporaryDirectory() as directory:
            app = Application(Translator(), Path(directory) / 'memory.json')
            self.assertNotIn('read_marks', app.session.core.procedures)
            app.action({'action': 'teach_graph', 'name': 'read_marks', 'graph': lesson('read_marks')})
            result = app.action({'action': 'run_sensor_graph', 'name': 'read_marks'})
            self.assertEqual(result['execution']['result'][:3], [5, 3, 0])
            self.assertTrue(result['state']['sensory_events'])
            app.action({'action': 'forget_graph', 'name': 'read_marks'})
            with self.assertRaises(ValueError):
                app.action({'action': 'run_sensor_graph', 'name': 'read_marks'})

    def test_invalid_coordinate_and_data_do_not_act(self):
        session = Session()
        for value in (float('nan'), 1, -1, True):
            with self.assertRaises(ValueError):
                session.sensors.act('canvas', 'move', {'x': value, 'y': .5})
        self.assertIsNone(session.canvas.pointer)
        self.assertEqual(session.sensors.events, [])
