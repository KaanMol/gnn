import copy
from fractions import Fraction
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import foundation
from graph_runtime import execute_graph, NUMERIC_OPERATIONS
from interface import Session
from procedures import compile_graph


class NumberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=foundation.curriculum()

    def calculate(self,text,library=None):
        return execute_graph(compile_graph(text),library=self.library if library is None else library)[0]

    def test_numeric_lessons_contain_no_numeric_instructions(self):
        package=json.loads((Path(__file__).parent/'curriculum/numbers.json').read_text())
        def inspect(g):
            self.assertEqual(g['input_type'],'Data')
            for n in g['nodes']:
                self.assertNotIn(n['op'],NUMERIC_OPERATIONS|{'literal','as_number','as_numbers'})
                for field in ('body','guard'):
                    if field in n: inspect(n[field])
        for entry in package.values():inspect(entry['graph'])

    def test_independent_rational_reference_on_unseen_operands(self):
        rng=random.Random(41027)
        for _ in range(18):
            a=Fraction(rng.randrange(-80,81),rng.randrange(1,16));b=Fraction(rng.randrange(-80,81),rng.randrange(1,16))
            for op,expected in [('add',a+b),('subtract',a-b),('multiply',a*b)]+([('divide',a/b)] if b else []):
                result,_=execute_graph(self.library['number_'+op]['graph'],{'a':str(a),'b':str(b)},self.library)
                self.assertEqual(Fraction(result),expected,(op,a,b))
            for op,expected in [('less',a<b),('equal',a==b)]:
                result,_=execute_graph(self.library['number_'+op]['graph'],{'a':str(a),'b':str(b)},self.library)
                self.assertIs(result,expected)

    def test_signs_zero_decimals_powers_and_failures(self):
        for text,expected in [('0.1+0.2',Fraction(3,10)),('-5+5',0),('-5*-2',10),('(-2/3)^-3',Fraction(-27,8)),('22^6',113379904),('0^0',1)]:
            self.assertEqual(self.calculate(text),expected)
        for text in ['1/0','0^-1','2^101','2^(1/2)']:
            with self.assertRaises(ValueError):self.calculate(text)
        self.assertEqual(execute_graph(self.library['number_floor']['graph'],'-7/3',self.library)[0],'-3')
        self.assertEqual(execute_graph(self.library['quantity_symbol']['graph'],'3',self.library)[0],[None,None,None])

    def test_no_default_native_arithmetic_and_deleted_binding_fails(self):
        with self.assertRaisesRegex(ValueError,'binding'):self.calculate('1+2',{})
        library=copy.deepcopy(self.library);del library['uint_add']
        with self.assertRaisesRegex(ValueError,'uint_add'):self.calculate('1+2',library)

    def test_revised_table_changes_result_without_stale_memo(self):
        self.assertEqual(self.calculate('2+3'),5)
        library=copy.deepcopy(self.library)
        library['number_symbols']['graph']['nodes'][1]['value']['add']['230']={'digit':'9','carry':'0'}
        self.assertEqual(self.calculate('2+3',library),9)
        self.assertEqual(self.calculate('2+3'),5)

    def test_forgotten_arithmetic_stays_missing_after_restart(self):
        s=Session();s.forget_graph('uint_add')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'memory.json';s.save(path)
            with patch('foundation.curriculum',side_effect=AssertionError('Reloaded arithmetic lessons')):
                restored=Session.load(path)
                try:
                    self.assertNotIn('uint_add',restored.core.procedures)
                    with self.assertRaisesRegex(ValueError,'uint_add'):self.calculate('3+4',restored.core.procedures)
                finally:restored.store.close()
        s.store.close()


if __name__=='__main__':unittest.main()
