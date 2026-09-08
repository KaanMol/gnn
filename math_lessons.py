"""Teacher-supplied symbolic rewrite rules. No algebra identities are built in."""
import ast
import re
from fractions import Fraction
import foundation


def parse(text):
    if '=' in text:
        parts = text.split('=')
        if len(parts) != 2 or not all(part.strip() for part in parts):
            raise ValueError('Use one equation with exactly one equals sign.')
        return ('=', parse(parts[0]), parse(parts[1]))
    text = text.strip().replace('^', '**').replace('×', '*').replace('−', '-')
    if len(text) > 400 or any(len(n) > 40 for n in re.findall(r'\d+', text)):
        raise ValueError('Please use a smaller symbolic expression.')
    try:
        tree = ast.parse(text, mode='eval')
    except (SyntaxError, RecursionError):
        raise ValueError('Use explicit symbols: x^2, 3*x, +, -, *, / and parentheses.') from None
    if len(list(ast.walk(tree))) > 100:
        raise ValueError('Please split the expression into smaller steps.')
    ops = {ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/', ast.Pow: '^'}
    def build(n):
        if isinstance(n, ast.Name) and re.fullmatch('[a-zA-Z][a-zA-Z0-9_]*', n.id):
            return ('symbol', n.id)
        if isinstance(n, ast.Constant) and type(n.value) in {int, float}:
            literal = ast.get_source_segment(text, n)
            if not re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)', literal):
                raise ValueError('Use ordinary numeric literals, without scientific notation.')
            return ('number', str(Fraction(literal)))
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            return (ops[type(n.op)], build(n.left), build(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return ('negate', build(n.operand))
        raise ValueError('This symbolic lesson supports integer literals, symbols and arithmetic operators only.')
    return build(tree.body)


def show(term):
    if term[0] in {'symbol', 'number'}: return term[1]
    if term[0] == 'negate': return '-(' + show(term[1]) + ')'
    return '(' + show(term[1]) + ' ' + term[0] + ' ' + show(term[2]) + ')'


def symbols(term):
    if term[0] == 'symbol': return {term[1]}
    if term[0] == 'number': return set()
    return set().union(*(symbols(child) for child in term[1:]))


def teach(library, left, right, source):
    lhs, rhs = parse(left), parse(right)
    methods = _methods(library)
    foundation.run(methods, 'math_rule_check', foundation.data({'left': lhs, 'right': rhs}))
    key = show(lhs) + ' → ' + show(rhs)
    library[key] = {'left': left, 'right': right, 'source': source}
    return ('Learned math rewrite: ' + key + '.\nLetters in the lesson are placeholders for expressions. '
            'This is a teacher-supplied rule, not a verified mathematical theorem.')


def _methods(library, methods=None):
    if methods is not None:
        return methods
    if hasattr(library, 'store'):
        return library.store.map('knowledge.procedures')
    raise ValueError('Missing taught procedure: math_rewrite (supply the taught procedure library)')


def rewrite(expression, library, solving=False, methods=None):
    methods = _methods(library, methods)
    rules = []
    for name, rule in library.items():
        left, _ = foundation.run(methods, 'math_pattern', foundation.data(parse(rule['left'])))
        right, _ = foundation.run(methods, 'math_pattern', foundation.data(parse(rule['right'])))
        rules.append({'name': name, 'left': left, 'right': right})
    report, _ = foundation.run(methods, 'math_rewrite', {'tree': foundation.data(parse(expression)), 'rules': rules})
    trace = [show(r['before']) + ' → ' + show(r['after']) + ' [lesson: ' + r['rule'] + ']' for r in report['trace']]
    endings = {'repeat': 'Stopped: the taught rules would repeat a previous expression.',
               'size_limit': 'Stopped at the expression-size limit.', 'step_limit': 'Stopped at the 40-step limit.'}
    ending = endings.get(report['status'])
    if ending is None:
        ending = 'No further taught rule applies.' if trace else 'No taught rule applies. Teach me a matching rule first.'
        if solving:
            ending = ('Variable isolated using teacher-supplied rules; this depends on those lessons being valid.'
                      if report['isolated'] else 'Not solved: no further taught rule applies.')
    return '\n'.join([show(report['expression']), *trace, ending])


def direct_math_lesson(text):
    from semantics import operation
    candidate = text.strip().rstrip('.?!')
    equation_lesson = re.fullmatch(r'(?:teach(?: math)?|math rule|learn math)\s*:\s*(.+?)\s*(?:=>|→)\s*(.+)', candidate, re.I)
    if equation_lesson:
        return {'operations': [operation('teach_math', obj=equation_lesson[2], text=equation_lesson[1])]}
    solve = re.fullmatch(r'solve\s*:\s*(.+)', candidate, re.I)
    if solve:
        return {'operations': [operation('solve_math', text=solve[1])]}
    match_rule = re.fullmatch(r'(?:teach(?: math)?|math rule|learn math)\s*:\s*(.+?)\s*(?:=>|→|equals|=)\s*(.+)', candidate, re.I)
    if match_rule:
        return {'operations': [operation('teach_math', obj=match_rule[2], text=match_rule[1])]}
    simplify = re.fullmatch(r'(?:simplify|rewrite)\s+(.+)', candidate, re.I)
    if simplify:
        return {'operations': [operation('rewrite_math', text=simplify[1])]}
    if candidate.lower() in {'show math rules', 'what math rules do you know', 'show math lessons'}:
        return {'operations': [operation('list_math')]}
    forget_equation = re.fullmatch(r'forget math\s*:\s*(.+?)\s*(?:=>|→)\s*(.+)', candidate, re.I)
    if forget_equation:
        return {'operations': [operation('forget_math', obj=forget_equation[2], text=forget_equation[1])]}
    forget = re.fullmatch(r'forget math\s*:\s*(.+?)\s*(?:=>|→|=)\s*(.+)', candidate, re.I)
    if forget:
        return {'operations': [operation('forget_math', obj=forget[2], text=forget[1])]}
    return None


def solve(expression, library):
    # An explicit Solve command accepts conventional compact single-letter
    # polynomial notation. This is interface syntax, not a learned identity.
    normalized = expression.replace('−', '-')
    normalized = re.sub(r'\b([a-zA-Z])(\d+)\b', r'\1^\2', normalized)
    normalized = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', normalized)
    # Handle powers attached to coefficients, e.g. 132x5 -> 132*x^5.
    normalized = re.sub(r'\b([a-zA-Z])(\d+)\b', r'\1^\2', normalized)
    term = parse(normalized)
    if term[0] != '=':
        raise ValueError('Give an equation with an equals sign, such as x - 3 = 0.')
    if len(symbols(term)) != 1:
        raise ValueError('This solving workflow requires an equation with exactly one unknown symbol.')
    return 'Interpreted equation: ' + normalized + '\n' + rewrite(normalized, library, solving=True)
