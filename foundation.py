"""Explicit foundation teaching and invocation; never a native reasoning fallback."""
import json
from fractions import Fraction
from pathlib import Path

from graph_store import GraphStore
from graph_runtime import execute_graph, validate_graph


def curriculum():
    root = Path(__file__).parent / 'curriculum'
    entries = json.loads((root / 'numbers.json').read_text())
    entries.update(json.loads((root / 'foundation.json').read_text()))
    entries.update(json.loads((root / 'learning.json').read_text()))
    entries.update(json.loads((root / 'meaning.json').read_text()))
    return entries


def new_learning_store():
    """A new notebook is supplied with an inspectable, removable starter lesson."""
    store = GraphStore()
    entries = curriculum()
    for entry in entries.values():
        validate_graph(entry['graph'], entries)
    with store.transaction():
        store.map('knowledge.procedures').update(entries)
        store.map('session.settings')['foundation_teaching'] = {
            'source': 'Starter curriculum supplied when this notebook was created',
            'lessons': list(entries), 'version': 1}
    return store


def run(library, name, argument, sensors=None, execution_cache=None):
    if name not in library:
        raise ValueError('Missing taught procedure: ' + name)
    # Resource allowance is graph metadata, independent of the procedure's
    # subject. A bounded override lets longer generic graph programs run.
    budget = library[name]['graph'].get('execution_budget', 3000000)
    if type(budget) is not int or not 1 <= budget <= 10000000:
        raise ValueError('Graph execution budget must be an integer from 1 to 10,000,000.')
    return execute_graph(library[name]['graph'], argument, library, limit=budget, sensors=sensors, execution_cache=execution_cache)


def data(value):
    """Serialization bridge for legacy tuple-keyed records; assigns no meanings."""
    def scalar(item):
        if isinstance(item, Fraction):
            return int(item) if item.denominator == 1 else str(item)
        raise TypeError('Unsupported interface value: ' + type(item).__name__)
    return json.loads(json.dumps(value, default=scalar))


def missing_method(error):
    return str(error).startswith(('Missing taught procedure:', 'Missing or ambiguous taught interface binding:'))
