import math
import unittest
from interface import Session
class NoModel:
    def translate(self, *args):
        raise AssertionError('Explicit math should not call the model')

POLYNOMIAL = 'x^6 - 132*x^5 + 7260*x^4 - 212960*x^3 + 3513840*x^2 - 30921792*x + 113379904'
COMPACT = 'x6 - 132x5 +7260x4 - 212960x3 + 3513840x2 - 30921792x + 113379904 = 0'
LESSONS = [f'Teach math: {POLYNOMIAL} => (x - 22)^6',
           'Teach math: u^6 = 0 => u = 0',
           'Teach math: u - a = 0 => u = a']

class EquationLessonTests(unittest.TestCase):
    def test_worked_factorization_is_exact(self):
        self.assertEqual([math.comb(6,k)*(-22)**k for k in range(7)],
                         [1,-132,7260,-212960,3513840,-30921792,113379904])

    def test_no_solver_without_lessons_then_three_taught_steps(self):
        s=Session();t=NoModel()
        self.assertIn('Not solved',s.chat('Solve: '+COMPACT,t))
        for lesson in LESSONS:
            self.assertIn('Learned math rewrite',s.chat(lesson,t))
        answer=s.chat('Solve: '+COMPACT,t)
        self.assertIn('(x = 22)',answer)
        self.assertIn('Variable isolated',answer)
        self.assertEqual(answer.count('[lesson:'),3)
        self.assertIn('(y = 9)',s.chat('Solve: y - 9 = 0',t))
        self.assertIn('(y = 0)',s.chat('Solve: y^6 = 0',t))
        self.assertIn('Not solved',s.chat('Solve: x^2 - 4 = 0',t))

    def test_similar_polynomial_is_not_given_canned_answer(self):
        s=Session();t=NoModel()
        for lesson in LESSONS:s.chat(lesson,t)
        answer=s.chat('Solve: '+COMPACT.replace('113379904','113379905'),t)
        self.assertIn('Not solved',answer)
        self.assertNotIn('(x = 22)',answer)
        s.chat('Forget math: u^6 = 0 => u = 0',t)
        self.assertIn('Not solved',s.chat('Solve: '+COMPACT,t))

    def test_equations_cannot_be_inserted_into_expression_rules(self):
        s=Session()
        self.assertIn('equation lesson',s.chat('Teach math: x + 0 => x = 0',NoModel()))
        self.assertIn('one unknown',s.chat('Solve: x + y = 0',NoModel()))

if __name__=='__main__':unittest.main()
