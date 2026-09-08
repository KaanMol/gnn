"""Teacher-supplied symbolic rewrite rules. No algebra identities are built in."""
import ast
import re
from fractions import Fraction


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
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return ('number', str(n.value))
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
    if lhs[0] == 'symbol':
        raise ValueError('Give the rule a structured left side, such as x + 0, rather than matching everything.')
    if symbols(rhs) - symbols(lhs):
        raise ValueError('Every placeholder on the right must appear on the left.')
    if (lhs[0] == '=') != (rhs[0] == '='):
        raise ValueError('An equation lesson must transform one equation into another equation.')
    if lhs == rhs:
        raise ValueError('That rule would leave the expression unchanged.')
    key = show(lhs) + ' → ' + show(rhs)
    library[key] = {'left': left, 'right': right, 'source': source}
    return ('Learned math rewrite: ' + key + '.\nLetters in the lesson are placeholders for expressions. '
            'This is a teacher-supplied rule, not a verified mathematical theorem.')


def match(pattern, value, bindings):
    if pattern[0] == 'symbol':
        name = pattern[1]
        if name in bindings: return bindings[name] == value
        bindings[name] = value
        return True
    if pattern[0] != value[0]: return False
    if pattern[0] == 'number': return pattern == value
    return all(match(p, v, bindings) for p, v in zip(pattern[1:], value[1:]))


def substitute(term, bindings):
    if term[0] == 'symbol': return bindings[term[1]]
    if term[0] == 'number': return term
    return (term[0], *(substitute(child, bindings) for child in term[1:]))


def rewrite(expression, library, solving=False):
    current = parse(expression)
    rules = [(name, parse(rule['left']), parse(rule['right'])) for name, rule in library.items()]
    trace, seen = [], {current}
    def once(term):
        # Exact evaluation of a fully numeric subexpression is the engine's
        # arithmetic primitive; the algebraic transformation remains taught.
        if term[0] in {'+', '-', '*', '/', '^'} and all(child[0] == 'number' for child in term[1:]):
            a, b = (Fraction(child[1]) for child in term[1:])
            if term[0] == '+': value = a + b
            elif term[0] == '-': value = a - b
            elif term[0] == '*': value = a * b
            elif term[0] == '/':
                if b == 0: raise ValueError('Division by zero is undefined.')
                value = a / b
            else:
                if b.denominator != 1 or abs(b) > 100: return term, None
                value = a ** int(b)
            return ('number', str(value.numerator) if value.denominator == 1 else str(value)), 'arithmetic evaluation'
        for name, left, right in rules:
            bindings = {}
            if match(left, term, bindings):
                result = substitute(right, bindings)
                if result != term: return result, name
        if term[0] not in {'symbol', 'number'}:
            for index, child in enumerate(term[1:], 1):
                changed, name = once(child)
                if name:
                    parts = list(term); parts[index] = changed
                    return tuple(parts), name
        return term, None
    for _ in range(40):
        result, name = once(current)
        if not name:
            ending = 'No further taught rule applies.' if trace else 'No taught rule applies. Teach me a matching rule first.'
            if solving:
                isolated = (current[0] == '=' and current[1][0] == 'symbol' and
                            current[1][1] not in symbols(current[2]))
                ending = ('Variable isolated using teacher-supplied rules; this depends on those lessons being valid.'
                          if isolated else 'Not solved: no further taught rule applies.')
            return '\n'.join([show(current), *trace, ending])
        if result in seen:
            return '\n'.join([show(current), *trace, 'Stopped: the taught rules would repeat a previous expression.'])
        if len(show(result)) > 4000:
            return '\n'.join([show(current), *trace, 'Stopped at the expression-size limit.'])
        trace.append(show(current) + ' → ' + show(result) + ' [lesson: ' + name + ']')
        current = result; seen.add(current)
    return '\n'.join([show(current), *trace, 'Stopped at the 40-step limit.'])


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
