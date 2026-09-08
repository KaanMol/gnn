import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from date_tools import date_answer, parse_date
from graph_runtime import execute_graph
from interface import Session
from semantics import operation

GRAPH = json.loads(Path(__file__).with_name('examples').joinpath('age_years.graph.json').read_text())


class NoModel:
    def translate(self, *args):
        raise AssertionError('Explicit date requests should invoke a capability, not the model')


class DateToolTests(unittest.TestCase):
    def session(self):
        s = Session()
        s.apply('My name is Mira', {'operations': [operation('identify', 'Mira')]})
        s.apply('birth date', {'operations': [operation('assert', 'Mira', 'born on', '24th of February 2000')]})
        return s

    def clock(self, value):
        return patch('date_tools.call_tool', return_value={'date': value, 'timezone': 'test-zone',
                     'source': 'local-system-clock', 'observed_at': value + 'T12:00:00+02:00'})

    def test_requires_taught_logic_and_live_clock(self):
        s = self.session()
        self.assertIn("haven't learned", s.chat('How old am I?', NoModel()))
        s.teach_graph('age_years', GRAPH, 'Age lesson')
        for today, expected in [('2026-02-23',25), ('2026-02-24',26), ('2026-09-06',26), ('2027-02-23',26)]:
            with self.clock(today) as tool:
                answer = s.chat('How old am I?', NoModel())
                self.assertIn(f'Mira is {expected} years old.', answer)
                tool.assert_called_once_with('current_date')
                self.assertEqual(s.language_records[-1]['tool_runs'][0]['observation']['date'], today)
        self.assertNotIn(('age', 'Mira', '26'), s.core.facts)

    def test_rule_is_executed_from_memory_not_hidden_age_code(self):
        s = self.session()
        alternate = copy.deepcopy(GRAPH)
        alternate['output'] = 'year_difference'
        s.teach_graph('age_years', alternate)
        with self.clock('2026-02-23'):
            self.assertIn('Mira is 26 years old', s.chat('How old is Mira?', NoModel()))
        s.core.procedures['age_years']['graph'] = GRAPH
        with self.clock('2026-02-23'):
            self.assertIn('Mira is 25 years old', s.chat('How old is Mira?', NoModel()))

    def test_conflict_missing_invalid_and_future_dates(self):
        s = self.session()
        s.teach_graph('age_years', GRAPH)
        with self.clock('1999-01-01'):
            self.assertIn('future', s.chat('How old am I?', NoModel()))
        s.core.assert_fact('Mira', 'birth date', '2001-02-24', False, 'different birth date')
        self.assertIn('multiple birth dates', s.chat('How old am I?', NoModel()))
        s.core.assert_fact('Mira', 'born on', '24th of February 2000', True, 'conflict')
        self.assertIn('conflicting evidence', s.chat('How old am I?', NoModel()))
        self.assertIn("don't know", s.chat('How old is Unknown?', NoModel()))
        with self.assertRaises(ValueError): parse_date('02/03/2000')
        with self.assertRaises(ValueError): parse_date('30 February 2000')

    def test_leap_birthday_policy_and_persistence(self):
        with self.clock('2025-02-28'):
            self.assertEqual(execute_graph(GRAPH, [2000,2,29], Session().core.procedures)[0],24)
        with self.clock('2025-03-01'):
            self.assertEqual(execute_graph(GRAPH, [2000,2,29], Session().core.procedures)[0],25)
        s=self.session();s.teach_graph('age_years',GRAPH,'Explicit birthday lesson')
        with tempfile.TemporaryDirectory() as folder, self.clock('2026-09-06'):
            s.chat('How old am I?',NoModel())
            path=Path(folder)/'memory.json';s.save(path)
            with patch("date_tools.call_tool", side_effect=AssertionError("Replay must not invoke tools")):
                restored=Session.load(path)
            self.assertEqual(s.core.procedures,restored.core.procedures)
            self.assertEqual(s.language_records,restored.language_records)

    def test_today_is_api_read_and_birth_teaching(self):
        s=self.session()
        with self.clock('2030-01-02') as tool:
            self.assertIn('2030-01-02',s.chat("What's today's date?",NoModel()))
            tool.assert_called_once_with('current_date')
        s.chat('Ari was born on 5 June 1990',NoModel())
        self.assertIn(('birth date','Ari','1990-06-05'),s.core.facts)
        self.assertEqual(s.chat('How old is Ari?',NoModel()).count("haven't learned"),1)

    def test_new_birth_date_replaces_old_positive_date(self):
        s = Session(); s.speaker = "Kaan"
        s.core.assert_fact("Julia", "birth date", "2001-07-21", False, "old")
        answer = s.chat("Julia is born on the 20th of July 2001", NoModel())
        self.assertIn("2001-07-20", answer)
        self.assertIn(("birth date", "Julia", "2001-07-20"), s.core.facts)
        self.assertNotIn(("birth date", "Julia", "2001-07-21"), s.core.facts)
        self.assertEqual(len([r for r in s.language_records if "born" in r["original"]]), 1)


if __name__ == '__main__': unittest.main()
