import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from graph_dsl import G
from interface import Session


class NoModel:
    def translate(self, *args):
        raise AssertionError('A taught conversation must not ask Gemma for an answer')


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.s = Session()
        self.s.teach_algebra_suite()
        self.s.teach_conversation()
        self.addCleanup(self.s.store.close)

    def chat(self, text):
        return self.s.chat(text, NoModel())

    def waiting(self):
        return self.s.store.map('interaction.state').get('waiting')

    def test_teaches_checks_retries_and_finishes_without_model(self):
        self.assertIn('5*x=20 → x = 4', self.chat('teach me algebra'))
        self.assertEqual(self.waiting()['resume'], 'tutor_reply')
        self.assertIn('Try again', self.chat('5'))
        self.assertIn('3*x=12', self.chat('help'))
        self.assertIn('could not check', self.chat('x=x=4'))
        self.assertIn('Undo addition', self.chat('x=4'))
        self.assertIn('Collect terms', self.chat('6'))
        self.assertIn('finished this taught introduction', self.chat('4'))
        self.assertIsNone(self.waiting())
        traces = [step for run in self.s.store.map('skills.runs').values() for step in run['trace']]
        self.assertTrue(any(step['operation']=='tutor_check_answer' for step in traces))
        self.assertTrue(any(step.get('surface')=='dialogue' and step.get('action')=='ask' for step in traces))

    def test_course_can_change_to_unseen_exercise_without_hardcoded_answer(self):
        course = copy.deepcopy(self.s.core.procedures['course_algebra']['graph'])
        # Syntax generation is test/teacher tooling. The live tutor consumes it.
        from algebra import syntax
        lesson = course['nodes'][1]['value'][0]
        lesson.update(quiz='7*x=63', quiz_input=syntax('7*x=63', True)[2])
        self.s.teach_graph('course_algebra', course, replace=True)
        self.assertIn('7*x=63', self.chat('explain algebra'))
        self.assertIn('Try again', self.chat('4'))
        self.assertIn('Correct', self.chat('9'))

    def test_missing_math_asks_for_teaching_and_retry_uses_restored_method(self):
        old = copy.deepcopy(self.s.core.procedures['uint_add'])
        self.s.forget_graph('uint_add')
        self.assertIn('I am stuck', self.chat('teach me algebra'))
        self.assertEqual(self.waiting()['state']['mode'], 'blocked')
        self.s.core.procedures['uint_add'] = old
        self.assertIn('Your turn: 3*x=12', self.chat('retry'))
        self.assertIn('Stopped', self.chat('stop'))
        self.assertIsNone(self.waiting())

    def test_wait_and_continue_survive_restart_without_replaying_action(self):
        s = self.s
        self.chat('teach me algebra')
        request_id = self.waiting()['id']
        events = list(s.sensors.events)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'notebook.sqlite3'
            s.save(path)
            with patch.object(Session, 'teach_conversation', side_effect=AssertionError('Automatic reteaching')):
                restored = Session.load(path)
            try:
                self.assertEqual(restored.store.map('interaction.state')['waiting']['id'], request_id)
                self.assertEqual(list(restored.sensors.events), events)
                self.assertIn('Correct', restored.chat('4', NoModel()))
            finally:
                restored.store.close()

    def test_arbitrary_wait_continuation_and_forgetting_it(self):
        s = self.s
        g = G()
        text = g.textcat(g.get(g.input, 'state', 'prefix'), g.get(g.input, 'input'))
        s.teach_graph('echo_reply', g.finish(g.call('dialogue_say', g.record(text=text))))
        s.run_skill('dialogue_wait', {'resume':'echo_reply','state':{'prefix':'Received: '}})
        self.assertEqual(self.waiting()['text'], '')
        self.assertEqual(self.chat('abc'), 'Received: abc')
        self.assertIsNone(self.waiting())
        self.chat('teach me algebra')
        s.forget_graph('tutor_reply')
        with self.assertRaisesRegex(ValueError, 'tutor_reply'):
            self.chat('4')
        self.assertIsNotNone(self.waiting())

    def test_attempt_preserves_effects_and_does_not_reset_budget(self):
        g = G()
        said = g.call('dialogue_say', g.record(text=g.data('Before failure')))
        bad = g.op('invoke', g.data('missing_method'), said)
        outer = G()
        self.s.teach_graph('try_action', outer.finish(outer.op('attempt', outer.input, body=g.finish(bad))))
        result = self.s.skills.run('try_action', None)['result']
        self.assertFalse(result['ok'])
        self.assertIn('missing_method', result['error'])
        self.assertEqual(self.s.store.sequence('interaction.messages')[-1]['text'], 'Before failure')
        from graph_runtime import execute_graph
        with self.assertRaisesRegex(ValueError, 'budget'):
            execute_graph(self.s.core.procedures['try_action']['graph'], None, self.s.core.procedures,
                          limit=1, sensors=self.s.skills.sensors)


if __name__ == '__main__':
    unittest.main()
