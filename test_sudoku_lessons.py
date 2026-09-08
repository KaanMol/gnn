import copy
import json
import itertools
import tempfile
import unittest
from pathlib import Path

from graph_runtime import execute_graph, validate_graph
from interface import Session
from preview import Application


class NoModel:
    model = 'fixture'
    def translate(self, *args):
        raise AssertionError('Taught Sudoku must not call a language model')


def independent_valid(values):
    groups = [values[r*9:(r+1)*9] for r in range(9)]
    groups += [values[c::9] for c in range(9)]
    groups += [[values[r*9+c] for r in range(br, br+3) for c in range(bc, bc+3)]
               for br in (0,3,6) for bc in (0,3,6)]
    return all(set(group) == set(range(1,10)) for group in groups)


class SudokuLessonTests(unittest.TestCase):
    def setUp(self):
        self.s = Session()
        self.s.teach_sudoku_suite()

    def test_no_automatic_curriculum_or_solver_instruction(self):
        fresh = Session()
        self.assertIn('Teach that procedure', fresh.chat('Solve sudoku', NoModel()))
        fresh.chat('Teach sudoku: an empty cell with one candidate gets that digit', NoModel())
        self.assertNotIn('sudoku_solver', fresh.core.procedures)
        with self.assertRaisesRegex(ValueError, 'Unknown graph instruction'):
            validate_graph({'input_type':'Data', 'output_type':'Data', 'nodes':[
                {'id':'x', 'op':'input', 'inputs':[], 'type':'Data'},
                {'id':'answer', 'op':'csp_solve', 'inputs':['x'], 'type':'Data'}], 'output':'answer'})
        for name in ('candidates', 'constraint_problem', '_valid'):
            self.assertFalse(hasattr(fresh.sudoku, name))

    def test_taught_program_solves_default_and_random_puzzles(self):
        for seed in (None, 7, 11, 23):
            if seed is not None:
                self.s.sudoku.randomize(seed=seed, blanks=50)
            original = [v for row in self.s.sudoku.grid for v in row]
            run = self.s.run_sensor_graph('sudoku_observe_solve')
            self.assertTrue(run['result']['correct'], run['answer'])
            values = [v for row in self.s.sudoku.grid for v in row]
            self.assertTrue(independent_valid(values))
            self.assertTrue(all(not a or a == b for a,b in zip(original,values)))
            operations = {step['operation'] for step in run['trace']}
            self.assertTrue({'observe','act','solution','check_board'} <= operations)

    def test_forgetting_every_dependency_stops_before_any_action(self):
        before = copy.deepcopy(self.s.sudoku.grid)
        original = copy.deepcopy(self.s.core.procedures)
        for name in json.loads((Path(__file__).parent/'curriculum/sudoku.json').read_text()):
            if name == 'sudoku_goal_check':
                continue  # Bool checker is exercised through the generic goal runner.
            self.s.core.procedures = {n:e for n,e in original.items() if n != name}
            try:
                target = name if name in {'sudoku_observe_check','sudoku_observe_read','sudoku_query_candidates'} else 'sudoku_observe_solve'
                answer = self.s.run_sensor_graph(target)['answer']
            except ValueError as error:
                answer = str(error)
            self.assertIn(name, answer)
            self.assertEqual(self.s.sudoku.grid, before)
            self.assertEqual(self.s.sensors.events, [])

    def test_forgetting_survives_restart_and_unrelated_learning(self):
        self.s.forget_graph('finite_candidates')
        self.s.core.assert_fact('Mira','is','person',False,'teacher')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'memory.json'
            self.s.save(path)
            restored = Session.load(path)
            self.assertNotIn('finite_candidates', restored.core.procedures)
            self.assertIn('finite_candidates', restored.run_sensor_graph('sudoku_observe_solve')['answer'])
            restored.teach_sudoku_suite()
            self.assertTrue(restored.run_sensor_graph('sudoku_observe_solve')['result']['correct'])

    def test_check_reports_conflicts_without_changing_wrong_entries(self):
        self.s.sudoku.place(0, 0, 9)
        self.s.sudoku.place(0, 2, 9)
        before = copy.deepcopy(self.s.sudoku.grid)
        result = self.s.run_sensor_graph('sudoku_observe_check')['result']
        self.assertEqual(result['verdict'], 'incorrect')
        self.assertIn(list(range(9)), result['conflicts'])
        self.assertEqual(self.s.sudoku.grid, before)
        self.assertFalse(any(event['kind'] == 'action' for event in self.s.sensors.events))
        self.assertIn('no solution', self.s.run_sensor_graph('sudoku_observe_solve')['answer'])
        self.assertEqual(self.s.sudoku.grid, before)

    def test_full_invalid_is_not_correct_and_edits_clear_check(self):
        with tempfile.TemporaryDirectory() as folder:
            app = Application(NoModel(), Path(folder)/'memory.json')
            app.session = self.s
            self.s.sudoku.reset([[1]*9 for _ in range(9)])
            result = app.action({'action':'sudoku_check'})
            self.assertTrue(result['execution']['result']['filled'])
            self.assertFalse(result['execution']['result']['correct'])
            app.action({'action':'sudoku_place', 'row':0, 'col':0, 'value':2})
            self.assertIsNone(app.state()['sudoku_check'])
            self.assertEqual(self.s.sudoku.grid[0][0], 2)
            app.action({'action':'sudoku_clear'})
            self.assertEqual(self.s.sudoku.grid, [[0]*9 for _ in range(9)])
            self.assertEqual(app.action({'action':'sudoku_check'})['execution']['result']['verdict'], 'incomplete')

    def test_revising_rule_data_changes_the_checker(self):
        self.s.sudoku.reset([[0]*9 for _ in range(9)])
        self.s.sudoku.place(0,0,1); self.s.sudoku.place(0,1,1)
        self.assertFalse(self.s.run_sensor_graph('sudoku_observe_check')['result']['valid'])
        lesson = copy.deepcopy(self.s.core.procedures['sudoku_rules']['graph'])
        lesson['nodes'][1]['value']['groups'] = []
        self.s.teach_graph('sudoku_rules', lesson, replace=True)
        self.assertTrue(self.s.run_sensor_graph('sudoku_observe_check')['result']['valid'])

    def test_finite_search_on_unrelated_problem_matches_exhaustive_answers(self):
        graph = self.s.core.procedures['finite_search']['graph']
        for initial in itertools.product([0,1,2], repeat=3):
            expected = [v for v in itertools.permutations([1,2,3]) if all(not a or a==b for a,b in zip(initial,v))]
            result, _ = execute_graph(graph, {'symbols':[1,2,3], 'empty':0, 'groups':[[0,1,2]], 'values':list(initial)}, self.s.core.procedures, limit=100000)
            self.assertEqual(result['found'], bool(expected))
            if expected: self.assertIn(tuple(result['values']), expected)
        with self.assertRaisesRegex(ValueError, 'step budget'):
            execute_graph(graph, {'symbols':[1,2], 'empty':0, 'groups':[[0,1]], 'values':[0,0]}, self.s.core.procedures, limit=3)

    def test_taught_hidden_single_and_small_group_soundness(self):
        library = self.s.core.procedures
        problem = {'symbols':[1,2,3], 'empty':0, 'groups':[[0,1,2],[1,3],[2,3]], 'values':[0,0,0,1]}
        context = {'problem':problem, 'values':problem['values']}
        context['options'] = execute_graph(library['finite_options']['graph'], context, library, limit=100000)[0]
        hidden = execute_graph(library['finite_hidden_single']['graph'], context, library, limit=100000)[0]
        self.assertEqual(hidden, [{'index':0, 'options':[1], 'count':1, 'group':[0,1,2]}])
        context['problem']['groups'] = [[1,3],[2,3]]
        self.assertEqual(execute_graph(library['finite_hidden_single']['graph'], context, library, limit=100000)[0], [])

    def test_explicit_trace_does_not_bypass_data_limits(self):
        from graph_dsl import Graph
        g = Graph(); x = g.input
        for _ in range(65): x = g.record(nested=x)
        with self.assertRaisesRegex(ValueError, 'budget'):
            execute_graph(g.finish(x, trace_mode='explicit'), {})
