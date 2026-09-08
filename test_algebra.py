import copy
import json
import math
import random
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

import algebra
from graph_runtime import execute_graph, validate_graph
from interface import Session


class NoModel:
    model = 'fixture'
    def translate(self, *args):
        raise AssertionError('Algebra execution called the language model')


def multiply(a, b):
    coefficients = [Fraction(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b): coefficients[i+j] += x*y
    return coefficients


def expanded(roots, scale=1):
    p = [Fraction(scale)]
    for root in roots: p = multiply(p, [-Fraction(root), Fraction(1)])
    return p


def expression(p, variable='x'):
    return '+'.join(f'({c})*{variable}^{i}' for i,c in enumerate(p))


def evaluate(coefficients, root):
    return sum(Fraction(c)*root**i for i,c in enumerate(coefficients))


class AlgebraTests(unittest.TestCase):
    def setUp(self):
        self.s = Session()
        self.s.teach_algebra_suite()
        self.library = self.s.core.procedures

    def solve(self, text):
        answer, run = algebra.run(text, self.library)
        return run['result'], answer, run['trace']

    def test_reported_nested_equation_and_named_solve_request(self):
        from build_algebra_request_curriculum import build
        self.s.teach_graph_package(build(), 'Equation request regression fixture')
        equation = '3(2x - 5) - 4(x + 2) = 5x - (x - 7)'
        for prefix in ('solve x:', 'solve for x:', 'Solve:'):
            answer = self.s.chat(prefix + equation, NoModel())
            self.assertIn('x = -15', answer)
            self.assertIn('-2*x - 30 = 0', answer)
        self.assertEqual(3*(2*(-15)-5)-4*(-15+2),5*(-15)-(-15-7))

    def test_distribution_collection_and_both_sides(self):
        self.assertEqual(algebra.run('(x+3)(x-2)', self.library, False)[1]['result'], [-6,1,1])
        self.assertEqual(algebra.run('3x+2(x-1)-x', self.library, False)[1]['result'], [-2,4])
        result, answer, trace = self.solve('3(2x-5)=4x+7')
        self.assertEqual(result['roots'], [11])
        self.assertIn('2*x - 22 = 0', answer)
        self.assertTrue({'distribute_and_collect','collect_like_terms','isolate_linear_variable'} <= {e['operation'] for e in trace})
        self.assertEqual(self.s.core.math_lessons, {})

    def test_unseen_linear_equations_with_exact_fraction_answers(self):
        rng = random.Random(19)
        for _ in range(35):
            a,b,c,d = [rng.randrange(-12,13) for _ in range(4)]
            result, _, _ = self.solve(f'{a}*z+({b})={c}*z+({d})')
            if a != c:
                self.assertEqual([Fraction(r) for r in result['roots']], [Fraction(d-b,a-c)])
            else:
                self.assertEqual(result['identity'], b==d)
                self.assertEqual(result['roots'], [])
        self.assertEqual(self.solve('0.5x=0.1')[0]['roots'], ['0.2'])
        self.assertEqual(self.solve('(x+1)/3=2/7')[0]['roots'], ['-1/7'])

    def test_general_factorization_of_expanded_polynomials(self):
        for roots,scale in [([22]*6,1),([-3]*5,7),([11]*4,-2),([0]*7,1),
                            ([Fraction(3,2),Fraction(-4),Fraction(2,3)],6),([-7,2,4,9],1)]:
            polynomial = expanded(roots,scale)
            result, _, trace = self.solve(expression(polynomial)+'=0')
            self.assertTrue(result['complete'])
            self.assertEqual(sorted(map(Fraction,result['roots'])), sorted(map(Fraction,roots)))
            for r in result['roots']: self.assertEqual(evaluate(polynomial,Fraction(r)),0)
            self.assertTrue(any(step['operation']=='factor_by_zero_remainder' for step in trace))
        # No expression-specific identity is present anywhere in the library.
        def literals(graph):
            for node in graph['nodes']:
                if node['op']=='data_literal': yield node['value']
                for name in ('body','guard'):
                    if name in node: yield from literals(node[name])
        for entry in self.library.values():
            for value in literals(entry['graph']): self.assertNotIn(value,[22,132,7260,113379904])

    def test_nearby_polynomial_does_not_receive_canned_root(self):
        polynomial = expanded([22]*6); polynomial[0] += 1
        result, answer, _ = self.solve(expression(polynomial)+'=0')
        self.assertFalse(result['complete'])
        self.assertEqual(result['roots'], [])
        self.assertNotIn('x = 22', answer)
        self.assertNotIn('No real solutions.',answer)

    def test_quadratic_real_domain_and_exact_radicals(self):
        result,_,_=self.solve('x^2-5x+6=0')
        self.assertEqual(set(result['roots']),{2,3})
        self.assertIn('multiplicity 2',self.solve('x^2-4x+4=0')[1])
        self.assertIn('No real solutions',self.solve('x^2+1=0')[1])
        for a,b,c in [(1,0,-2),(3,2,-7),(-2,3,4)]:
            result,answer,_=self.solve(f'{a}*x^2+({b})*x+({c})=0')
            self.assertTrue(result['complete'])
            for root in result['roots']:
                if isinstance(root,dict):
                    x=(float(root['numerator'])+root['sign']*math.sqrt(float(root['radicand'])))/float(root['denominator'])
                else: x=float(Fraction(root))
                self.assertAlmostEqual(a*x*x+b*x+c,0,places=10)
            self.assertIn('sqrt(',answer)

    def test_identity_contradiction_and_unsupported_domains(self):
        self.assertTrue(self.solve('2(x+3)=2x+6')[0]['identity'])
        self.assertIn('No real solutions',self.solve('0*x=5')[1])
        self.assertTrue(self.solve('0*x=0')[0]['identity'])
        for equation, error in [('x/x=1','Division by an expression'), ('1/0=0','Division by zero'),
                                ('x^-1=2','nonnegative integer'),('x^13=0','stored limit'),
                                ('x+y=1','one unknown'),('x^x=2','exponent')]:
            with self.assertRaisesRegex(ValueError,error): self.solve(equation)
        self.assertFalse(self.solve('x^3-2=0')[0]['complete'])
        self.assertIn('Not fully solved',self.solve('x^3-2=0')[1])
        partial = self.solve('(x-3)*(x^3-2)=0')
        self.assertEqual(partial[0]['roots'],[3])
        self.assertFalse(partial[0]['complete'])
        self.assertIn('Partial answer',partial[1])

    def test_each_dependency_is_required_and_no_native_fallback_exists(self):
        original = copy.deepcopy(self.library)
        for name in json.loads((Path(__file__).parent/'curriculum/algebra.json').read_text()):
            reduced = {n:e for n,e in original.items() if n != name}
            with self.assertRaisesRegex(ValueError,name): algebra.run('5*x=20',reduced)
        self.s.chat('Teach math: a*x=b => x=b/a',NoModel())
        for name in list(self.library): self.s.forget_graph(name)
        self.assertIn('Missing taught procedure: algebra_solve',self.s.chat('Solve: 5x=20',NoModel()))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'memory.json';self.s.save(path)
            restored=Session.load(path)
            self.assertTrue(restored.algebra_taught)
            self.assertEqual(restored.core.procedures,{})
            self.assertIn('Missing taught procedure: algebra_solve',restored.chat('Solve: 5x=20',NoModel()))

    def test_graph_revision_changes_behavior_and_survives_restart(self):
        policy=copy.deepcopy(self.library['algebra_policy']['graph'])
        policy['nodes'][1]['value']['max_exponent']=3
        self.s.teach_graph('algebra_policy',policy,replace=True)
        with self.assertRaisesRegex(ValueError,'stored limit'): self.solve('x^4=0')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'memory.json';self.s.save(path)
            restored=Session.load(path)
            self.assertEqual(restored.core.procedures,self.library)
            self.assertIn('stored limit',restored.chat('Solve: x^4=0',NoModel()))
            self.assertIn('x = 4',restored.chat('Solve: 5x=20',NoModel()))

    def test_explicit_rewrite_keeps_its_separate_taught_rule_workflow(self):
        self.s.chat('Teach math: u*u => u^2',NoModel())
        answer = self.s.chat('Rewrite y*y',NoModel())
        self.assertIn('[lesson:',answer)
        simplified = self.s.chat('Simplify y*y',NoModel())
        self.assertTrue(simplified.startswith('y^2'))
        self.assertIn('taught algebra procedures',simplified)

    def test_generic_rational_primitives_and_integer_square_root(self):
        for value in [0,1,2,4,15,16,1001,10**15+5]:
            result,_=execute_graph(self.library['integer_sqrt']['graph'],value,self.library,limit=100000)
            self.assertEqual(result,math.isqrt(value))
        self.assertEqual(execute_graph(self.library['rational_sqrt']['graph'],'9/16',self.library,limit=100000)[0],{'exact':True,'value':'0.75'})
        from graph_dsl import Graph
        for operation,expected in [('floor',-2),('numerator',-7),('denominator',4)]:
            g=Graph('Number');output=g.op(operation,g.input,kind='Number')
            self.assertEqual(execute_graph(g.finish(output,'Number'),'-7/4')[0],expected)

    def test_expansion_matches_independent_product_coefficients(self):
        rng=random.Random(7)
        for _ in range(12):
            a,b,c,d=[rng.randrange(-8,9) for _ in range(4)]
            text=f'({a}*x+({b}))*({c}*x+({d}))'
            result=algebra.run(text,self.library,False)[1]['result']
            expected=multiply([b,a],[d,c])
            while len(expected)>1 and expected[-1]==0:expected.pop()
            self.assertEqual(list(map(Fraction,result)),expected)
