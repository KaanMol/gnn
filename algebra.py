"""Syntax and presentation adapter for the taught algebra graph curriculum.

This module does not normalize polynomials, factor, isolate variables or search
roots. Those operations run as stored programs in the general graph interpreter.
"""
import re
import json
from fractions import Fraction

from arithmetic import number_text
from graph_runtime import execute_graph
from math_lessons import parse, symbols


def syntax(expression, equation=False):
    normalized = expression.strip().replace('−', '-').replace('×', '*')
    if re.search(r'\d(?:\.\d*)?[eE][+-]?\d', normalized):
        raise ValueError('Use ordinary numbers or fractions, without scientific notation.')
    normalized = re.sub(r'\b([a-zA-Z])(\d+)\b', r'\1^\2', normalized)
    normalized = re.sub(r'(\d)\s*(?=[a-zA-Z(])', r'\1*', normalized)
    normalized = re.sub(r'\b([a-zA-Z])(\d+)\b', r'\1^\2', normalized)
    normalized = re.sub(r'\)\s*(?=[a-zA-Z0-9(])', ')*', normalized)
    normalized = re.sub(r'\b([a-zA-Z])\s*\(', r'\1*(', normalized)
    term = parse(normalized)
    if equation != (term[0] == '='):
        raise ValueError('Give an equation such as 3*(x+2)=15.' if equation else 'Simplify one expression, without an equals sign.')
    names = symbols(term)
    if len(names) > 1:
        raise ValueError('These algebra lessons cover one unknown at a time. Systems and multivariable algebra need further lessons.')
    tokens = []
    def flatten(current):
        leaf = current[0] in {'symbol', 'number'}
        children = [] if leaf else [flatten(child) for child in current[1:]]
        index = len(tokens)
        tokens.append({'op': current[0], 'args': children, 'value': current[1] if leaf else None})
        return index
    flatten(term)
    return normalized, next(iter(names), 'x'), {'tokens': tokens}


def polynomial_text(coefficients, variable):
    """Print the coefficients returned by a stored graph, without solving."""
    parts = []
    for exponent in range(len(coefficients)-1, -1, -1):
        coefficient = Fraction(coefficients[exponent])
        if not coefficient:
            continue
        magnitude = abs(coefficient)
        if exponent:
            factor = variable + (f'^{exponent}' if exponent > 1 else '')
            term = factor if magnitude == 1 else f'{number_text(magnitude)}*{factor}'
        else:
            term = number_text(magnitude)
        prefix = (' - ' if coefficient < 0 else ' + ') if parts else ('-' if coefficient < 0 else '')
        parts.append(prefix + term)
    return ''.join(parts) or '0'


def root_text(root):
    if isinstance(root, dict) and root.get('kind') == 'radical':
        sign = '+' if root['sign'] == 1 else '-'
        return f"({root['numerator']} {sign} sqrt({root['radicand']})) / ({root['denominator']})"
    return number_text(Fraction(root))


def run(expression, library, solving=True):
    normalized, variable, argument = syntax(expression, equation=solving)
    name = 'algebra_solve' if solving else 'algebra_normalize'
    if name not in library:
        raise ValueError('Missing taught procedure: ' + name)
    result, trace = execute_graph(library[name]['graph'], argument, library, limit=3000000)
    if solving:
        if result['identity']:
            answer = f'Every real value of {variable} satisfies this equation.'
        elif not result['roots']:
            answer = ('No real solutions.' if result['complete'] else
                      'Not fully solved: the taught methods did not resolve this polynomial. This does not mean it has no solutions.')
        else:
            rendered = [root_text(root) for root in result['roots']]
            unique = list(dict.fromkeys(rendered))
            answer = '; '.join(f'{variable} = {root}' + (f' (multiplicity {rendered.count(root)})' if rendered.count(root) > 1 else '') for root in unique)
            if not result['complete']:
                answer += '\nPartial answer: additional roots may remain.'
        answer += '\nInterpreted equation: ' + normalized
        answer += '\nCollected equation: ' + polynomial_text(result['polynomial'], variable) + ' = 0'
        if not result['complete']:
            answer += '\nUnresolved factor: ' + polynomial_text(result['residual'], variable)
    else:
        answer = polynomial_text(result, variable) + '\nInterpreted expression: ' + normalized
    lines = []
    for step in trace:
        op = step['operation']
        if op in {'algebra_result', 'execution_cache'}:
            continue
        # These are the actual emit records of taught instructions, not an
        # explanation invented by a language model after returning an answer.
        result_text = step['result'] if isinstance(step['result'], str) else json.dumps(step['result'], default=str)
        lines.append(op.replace('_', ' ') + ' → ' + result_text)
    answer += '\nExecuted taught algebra procedures' + (' (over real numbers)' if solving else '') + '.'
    if lines:
        answer += '\nSteps:\n' + '\n'.join(lines[:80])
        if len(lines) > 80:
            answer += '\n… Full execution trace is stored with this response.'
    return answer, {'procedure': name, 'input': normalized, 'result': result, 'trace': trace}
