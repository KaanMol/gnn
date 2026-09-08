"""A bounded interpreter for typed, serializable computation graphs.

Graphs are executable data. Edges connect typed ports; choose is lazy and while
executes explicit guard/body graphs. The interpreter never executes host code.
"""
import copy
import re
import hashlib
import json
from collections import OrderedDict
from fractions import Fraction
from typing import NamedTuple


class ExecutionCache:
    """Bounded, instance-owned cache for explicitly marked pure procedures."""
    def __init__(self, max_bytes=16000000, max_entries=1024, optimize=True):
        if any(type(v) is not int or v <= 0 for v in (max_bytes, max_entries)):
            raise ValueError('Cache bounds must be positive integers.')
        self.max_bytes, self.max_entries = max_bytes, max_entries
        self.fingerprint = None
        self.values = OrderedDict()
        self.bytes = 0
        self.plans = OrderedDict()
        self.plan_bytes = 0
        self.sections = {}
        self.optimize = bool(optimize)

    @staticmethod
    def plan_key(graph):
        encoded = json.dumps(graph, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        return hashlib.sha256(encoded).hexdigest(), len(encoded)

    def layout(self, graph):
        """Only graph-requested sections persist. Cold layouts stay local."""
        key, _ = self.plan_key(graph)
        if key in self.plans:
            return self.plans[key][0], True
        return prepare_layout(graph, self.optimize), False

    def prepare(self, library):
        # Conservatively invalidate on ANY procedure change, including implicit
        # numeric bindings. Never retain a stale library snapshot.
        encoded = json.dumps(getattr(library, 'fingerprint_data', library), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        fingerprint = hashlib.sha256(encoded).digest()
        if fingerprint != self.fingerprint:
            self.values.clear(); self.bytes = 0
            self.fingerprint = fingerprint

    def get(self, key):
        if key not in self.values:
            return None
        self.values.move_to_end(key)
        value, size, cost = self.values[key]
        return copy.deepcopy(value), cost

    def put(self, key, value, cost):
        size = len(key[1]) + len(json.dumps(value, ensure_ascii=True, allow_nan=False))
        if size > self.max_bytes:
            return
        if key in self.values:
            self.bytes -= self.values.pop(key)[1]
        while self.values and (len(self.values) >= self.max_entries or self.bytes + size > self.max_bytes):
            self.bytes -= self.values.popitem(last=False)[1][1]
        self.values[key] = (copy.deepcopy(value), size, cost)
        self.bytes += size


class EngineSurface:
    """Generic RAM mechanism; graph procedures select sections and actions."""
    def __init__(self, cache, library):
        self.cache, self.library = cache, library

    def closure(self, name):
        plans, visited = {}, set()
        def visit(graph):
            key, size = self.cache.plan_key(graph)
            if key in plans:
                return
            plans[key] = (graph, size)
            names = set()
            if graph['input_type'] in {'Number', 'List[Number]'} or any(n['op'] in {'literal', 'as_number', 'as_numbers'} for n in graph['nodes']):
                names.add(interface_binding('parse', self.library))
            for node in graph['nodes']:
                op = node['op']
                if op in {'call', 'tool'} | NUMERIC_OPERATIONS:
                    names.add(node['name'] if op == 'call' else interface_binding(node['name'] if op == 'tool' else op, self.library))
                for field in ('body', 'guard'):
                    if field in node:
                        visit(node[field])
            for target in names:
                procedure(target)
        def procedure(target):
            if target in visited:
                return
            visited.add(target)
            if target not in self.library:
                raise ValueError('Missing taught procedure: ' + target)
            visit(self.library[target]['graph'])
        procedure(name)
        return plans

    def observe(self):
        return {'format': 'graph-register-bytecode', 'version': BYTECODE_VERSION,
                'sections': list(self.cache.sections), 'plans': len(self.cache.plans),
                'serialized_bytes': self.cache.plan_bytes, 'max_bytes': self.cache.max_bytes,
                'max_entries': self.cache.max_entries}

    def act(self, action, arguments):
        name = arguments.get('section')
        if not isinstance(name, str):
            raise ValueError('Engine section must be a procedure name.')
        cache = self.cache
        if action == 'status':
            current = set(self.closure(name))
            return {'section': name, 'warm': current == cache.sections.get(name)}
        if action == 'release':
            cache.sections.pop(name, None)
        elif action == 'prepare':
            requested = self.closure(name)
            retained = set().union(*(keys for section, keys in cache.sections.items() if section != name))
            combined = retained | set(requested)
            size = sum(requested[k][1] if k in requested else cache.plans[k][1] for k in combined)
            if len(combined) > cache.max_entries or size > cache.max_bytes:
                return {'section': name, 'accepted': False, 'reason': 'capacity'}
            # Build before committing, so failures cannot leave a partial section.
            additions = {k: (prepare_layout(g, cache.optimize), size) for k, (g, size) in requested.items() if k not in cache.plans}
            cache.plans.update(additions)
            cache.sections[name] = set(requested)
        else:
            raise ValueError('Unknown engine action: ' + action)
        retained = set().union(*cache.sections.values())
        for key in list(cache.plans):
            if key not in retained:
                del cache.plans[key]
        cache.plan_bytes = sum(size for _, size in cache.plans.values())
        return {'section': name, 'accepted': True, **self.observe()}


# Versioned, subject-independent register bytecode. Stored lessons remain JSON.
BYTECODE_VERSION = 1
OP_NAMES = ('act', 'add', 'and', 'append', 'as_bool', 'as_data', 'as_number', 'as_numbers', 'at', 'attempt', 'bool_data', 'call', 'characters', 'choose', 'concat', 'contains', 'data_equal', 'data_list', 'data_literal', 'denominator', 'difference', 'divide', 'emit', 'equal', 'filter', 'flatten', 'floor', 'get', 'has_key', 'indices', 'input', 'invoke', 'is_integer', 'item', 'join_text', 'keys', 'kind_of', 'length', 'less', 'list', 'literal', 'lookup', 'lower', 'map', 'multiply', 'negate', 'not', 'numerator', 'observe', 'or', 'power', 'range', 'record', 'replace_text', 'require', 'reverse', 'set_item', 'size', 'slice', 'sort', 'split_text', 'subtract', 'text', 'tool', 'unique', 'while')
(OP_ACT, OP_ADD, OP_AND, OP_APPEND, OP_AS_BOOL, OP_AS_DATA, OP_AS_NUMBER, OP_AS_NUMBERS, OP_AT, OP_ATTEMPT, OP_BOOL_DATA, OP_CALL, OP_CHARACTERS, OP_CHOOSE, OP_CONCAT, OP_CONTAINS, OP_DATA_EQUAL, OP_DATA_LIST, OP_DATA_LITERAL, OP_DENOMINATOR, OP_DIFFERENCE, OP_DIVIDE, OP_EMIT, OP_EQUAL, OP_FILTER, OP_FLATTEN, OP_FLOOR, OP_GET, OP_HAS_KEY, OP_INDICES, OP_INPUT, OP_INVOKE, OP_IS_INTEGER, OP_ITEM, OP_JOIN_TEXT, OP_KEYS, OP_KIND_OF, OP_LENGTH, OP_LESS, OP_LIST, OP_LITERAL, OP_LOOKUP, OP_LOWER, OP_MAP, OP_MULTIPLY, OP_NEGATE, OP_NOT, OP_NUMERATOR, OP_OBSERVE, OP_OR, OP_POWER, OP_RANGE, OP_RECORD, OP_REPLACE_TEXT, OP_REQUIRE, OP_REVERSE, OP_SET_ITEM, OP_SIZE, OP_SLICE, OP_SORT, OP_SPLIT_TEXT, OP_SUBTRACT, OP_TEXT, OP_TOOL, OP_UNIQUE, OP_WHILE) = range(len(OP_NAMES))
OP_CODES = {name: code for code, name in enumerate(OP_NAMES)}
NUMERIC_OPCODES = {OP_CODES[name] for name in ('add','subtract','multiply','divide','power','negate','less','equal','is_integer','floor','numerator','denominator','size','length','range','indices')}

class Instruction(NamedTuple):
    opcode: int
    inputs: tuple
    kind: str
    source_id: str
    fields: dict


class PreparedPlan(NamedTuple):
    nodes: tuple
    output: int
    check_data: tuple


def prepare_layout(graph, optimize=True):
    # Detach nested bodies and literal values from mutable caller-owned data.
    # A saved plan must survive edits and undo without changing underneath us.
    nodes = [dict(node) for node in copy.deepcopy(graph['nodes'])]
    indices = {n['id']: i for i, n in enumerate(nodes)}
    for node in nodes:
        node['inputs'] = [indices[x] for x in node['inputs']]
    # These operations return validated immutable data or a bounded subset.
    # The proof is derived from engine operations, never lesson annotations.
    # Constructors and external inputs retain full aggregate validation.
    preserves_bounds = {'get', 'item', 'lookup', 'choose', 'require',
                        'data_literal', 'bool_data', 'call', 'slice', 'reverse'}
    checks = tuple(not optimize or n['op'] not in preserves_bounds for n in nodes)
    instructions = tuple(Instruction(OP_CODES[n['op']], tuple(n['inputs']), n['type'], n['id'],
                                    {k:v for k,v in n.items() if k not in {'op','inputs','type','id'}})
                         for n in nodes)
    return PreparedPlan(instructions, indices[graph['output']], checks)


TYPES = {"Number", "Bool", "List[Number]", "Unit", "Data"}


def bounded_number(value):
    if type(value) is bool:
        raise ValueError("A boolean is not a Number.")
    if isinstance(value, str):
        if len(value) > 140 or not re.fullmatch(r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:/\d+)?", value) or any(len(d) > 64 for d in re.findall(r"\d+", value)):
            raise ValueError("Use bounded ordinary numeric literals, without scientific notation.")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError("Invalid numeric value.") from None
    if max(result.numerator.bit_length(), result.denominator.bit_length()) > 2048:
        raise ValueError("Numeric value exceeds the size budget.")
    return result
PORTS = {
    "add": (["Number", "Number"], "Number"), "subtract": (["Number", "Number"], "Number"),
    "multiply": (["Number", "Number"], "Number"), "divide": (["Number", "Number"], "Number"),
    "power": (["Number", "Number"], "Number"), "negate": (["Number"], "Number"),
    "less": (["Number", "Number"], "Bool"), "equal": (["Number", "Number"], "Bool"),
    "length": (["List[Number]"], "Number"), "at": (["List[Number]", "Number"], "Number"),
    "append": (["List[Number]", "Number"], "List[Number]"),
    "range": (["Number", "Number"], "List[Number]"),
    "is_integer": (["Number"], "Bool"), "not": (["Bool"], "Bool"), "and": (["Bool", "Bool"], "Bool"), "or": (["Bool", "Bool"], "Bool"),
    "floor": (["Number"], "Number"), "numerator": (["Number"], "Number"), "denominator": (["Number"], "Number"),
}


def interface_binding(name, library):
    matches = library.interface_names(name) if hasattr(library, 'interface_names') else [key for key, entry in library.items() if (entry['graph'].get('interface') == name or (isinstance(entry['graph'].get('interface'), list) and name in entry['graph']['interface']))]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous taught interface binding: ' + str(name))
    return matches[0]

NUMERIC_OPERATIONS = {'add', 'subtract', 'multiply', 'divide', 'power', 'negate',
    'less', 'equal', 'is_integer', 'floor', 'numerator', 'denominator', 'size', 'length', 'range', 'indices'}

MAX_GRAPH_NODES = 500


def validate_graph(graph, library=None, depth=0):
    library = library or {}
    if depth > 12 or not isinstance(graph, dict) or graph.get("input_type") not in TYPES or graph.get("output_type") not in TYPES:
        raise ValueError("Invalid graph signature or nesting depth.")
    contract = graph.get('skill')
    if contract is not None:
        if not isinstance(contract,dict) or not {'requires','provides'} <= set(contract) or set(contract)-{'requires','provides','deletes'}:
            raise ValueError('A skill contract needs requires and provides tag lists, with optional deletes.')
        for tags in contract.values():
            if not isinstance(tags,list) or len(tags)>30 or any(not isinstance(v,str) or not v or len(v)>100 for v in tags):
                raise ValueError('Skill tags must be bounded, nonempty text labels.')
    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_GRAPH_NODES:
        raise ValueError(f"A graph needs between one and {MAX_GRAPH_NODES} nodes.")
    outputs = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or node["id"] in outputs:
            raise ValueError("Graph nodes require unique string IDs.")
        op, args, result = node.get("op"), node.get("inputs"), node.get("type")
        if not isinstance(args, list) or any(not isinstance(a, str) or a not in outputs for a in args):
            raise ValueError("Edges must reference earlier nodes; graph cycles are not allowed.")
        actual = [outputs[a] for a in args]
        if op == "input":
            expected, return_type = [], graph["input_type"]
        elif op == "literal":
            expected, return_type = [], "Number"
            value = str(node.get("value", ""))
            if len(value) > 80:
                raise ValueError("Numeric literal too large.")
            bounded_number(value)
        elif op == "tool":
            name = interface_binding(node.get('name'), library)
            expected, return_type = [], library[name]['graph']['output_type']
        elif op == "data_literal":
            expected, return_type = [], "Data"
            normalize(node.get("value"), "Data")
        elif op == "get":
            expected, return_type = ["Data"], "Data"
            keys = node.get("path")
            if not isinstance(keys, list) or not keys or len(keys) > 8 or any(type(k) not in {str, int} for k in keys):
                raise ValueError("A field path needs one to eight string keys or integer indices.")
        elif op == "lookup":
            expected, return_type = ["Data", "Data"], "Data"
        elif op == "item":
            expected, return_type = ["Data", "Data"], "Data"
        elif op == "set_item":
            expected, return_type = ["Data", "Data", "Data"], "Data"
        elif op in {'kind_of', 'keys', 'reverse', 'lower', 'characters'}:
            expected, return_type = ['Data'], 'Data'
        elif op in {'join_text', 'split_text'}:
            expected, return_type = ['Data', 'Data'], 'Data'
        elif op == 'replace_text':
            expected, return_type = ['Data','Data','Data'], 'Data'
        elif op == 'as_numbers':
            expected, return_type = ['Data'], 'List[Number]'
        elif op == 'has_key':
            expected, return_type = ['Data', 'Data'], 'Bool'
        elif op == 'invoke':
            expected, return_type = ['Data', 'Data'], 'Data'
        elif op in {"concat", "difference"}:
            expected, return_type = ["Data", "Data"], "Data"
        elif op == "emit":
            expected, return_type = ["Data", "Data"], "Data"
        elif op in {"unique", "flatten", "slice", "sort", "text"}:
            expected, return_type = ["Data"], "Data"
            if op == "slice" and any(node.get(k) is not None and type(node[k]) is not int for k in ("start", "stop")):
                raise ValueError("Slice bounds must be integers.")
            if op == "sort" and not isinstance(node.get("key"), str):
                raise ValueError("Sort must name a record field.")
        elif op == "contains":
            expected, return_type = ["Data", "Data"], "Bool"
        elif op == "size":
            expected, return_type = ["Data"], "Number"
        elif op == "indices":
            expected, return_type = ["Data"], "Data"
        elif op == "data_list":
            expected, return_type = ["Data"] * len(args), "Data"
        elif op == "as_bool":
            expected, return_type = ["Data"], "Bool"
        elif op == "bool_data":
            expected, return_type = ["Bool"], "Data"
        elif op == "record":
            expected, return_type = ["Data"] * len(args), "Data"
            keys = node.get("keys")
            if not isinstance(keys, list) or len(keys) != len(args) or any(not isinstance(k, str) for k in keys) or len(set(keys)) != len(keys):
                raise ValueError("Record keys must uniquely name each input.")
        elif op in {"map", "filter"}:
            if len(args) not in {1, 2}:
                raise ValueError("Map/filter expects a collection and optional context.")
            expected, return_type = ["Data"] * len(args), "Data"
            validate_graph(node.get("body"), library, depth + 1)
            if node["body"]["input_type"] != "Data" or node["body"]["output_type"] != ("Bool" if op == "filter" else "Data"):
                raise ValueError("Collection body has an incompatible signature.")
        elif op == "data_equal":
            expected, return_type = ["Data", "Data"], "Bool"
        elif op == "as_number":
            expected, return_type = ["Data"], "Number"
        elif op == "as_data":
            expected, return_type = ["Number"], "Data"
        elif op in {"observe", "act"}:
            expected, return_type = (["Data"] if op == "observe" else ["Data", "Data"]), "Data"
            if not isinstance(node.get("surface"), str) or not node["surface"]:
                raise ValueError("Sensor nodes must name a surface.")
            if op == "act" and (not isinstance(node.get("action"), str) or not node["action"]):
                raise ValueError("An action node must name an input control.")
        elif op == "list":
            expected, return_type = ["Number"] * len(args), "List[Number]"
        elif op == "choose":
            expected, return_type = ["Bool", result, result], result
        elif op == "require":
            expected, return_type = ["Bool", result], result
        elif op == 'attempt':
            expected, return_type = ['Data'], 'Data'
            validate_graph(node.get('body'),library,depth+1)
            if node['body']['input_type']!='Data' or node['body']['output_type']!='Data':
                raise ValueError('An attempted program needs Data input and output.')
        elif op == "while":
            expected, return_type = [result], result
            for field, output in (("guard", "Bool"), ("body", result)):
                nested = node.get(field)
                validate_graph(nested, library, depth + 1)
                if nested["input_type"] != result or nested["output_type"] != output:
                    raise ValueError("Loop guard/body signatures do not match the state type.")
        elif op == "call":
            target = library.get(node.get("name"), {}).get("graph")
            if target is None:
                raise ValueError("Missing taught procedure: " + str(node.get("name")))
            expected, return_type = [target["input_type"]], target["output_type"]
        elif op in PORTS:
            expected, return_type = PORTS[op]
        else:
            raise ValueError("Unknown graph instruction: " + str(op))
        if result not in TYPES or actual != expected or result != return_type:
            raise ValueError(f"Type mismatch at {node['id']}: {op} expects {expected} → {return_type}.")
        outputs[node["id"]] = result
    if outputs.get(graph.get("output")) != graph["output_type"]:
        raise ValueError("The output port does not match the graph signature.")
    return graph


def normalize(value, kind):
    if kind == "Data":
        return bounded_data(value)
    if kind == "Unit" and value is None:
        return None
    if kind == "Number" and type(value) in {str, int, Fraction}:
        return bounded_number(value)
    if kind == "Bool" and type(value) is bool:
        return value
    if kind == "List[Number]" and isinstance(value, list) and len(value) <= 200:
        return [normalize(x, "Number") for x in value]
    raise ValueError("The input value does not match type " + kind)


def bounded_data(value, depth=0, budget=None):
    """Bounded JSON values for programs; sensor drivers enforce their own bounds."""
    budget = [100000] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0 or depth > 64:
        raise ValueError('Data exceeds its item or nesting budget.')
    if isinstance(value, list) and len(value) <= 2000:
        return [bounded_data(v, depth+1, budget) for v in value]
    if isinstance(value, dict) and len(value) <= 2000 and all(type(k) is str for k in value):
        return {k: bounded_data(v, depth+1, budget) for k,v in value.items()}
    from sensors import _bounded_json
    return _bounded_json(value)


def execute_graph(graph, argument=None, library=None, limit=100000, sensors=None, execution_cache=None, meter=None):
    from collections import OrderedDict
    from sensors import _bounded_json
    from arithmetic import number_text
    from graph_store import GraphMap, GraphSnapshot
    # One consistent database snapshot per execution. No cached lesson library
    # survives the run, so deleted or edited roots affect the next invocation.
    if isinstance(library, GraphMap):
        library = GraphSnapshot(library)
    library = library or {}
    resolved_bindings = {}
    def binding(name):
        if not execution_cache.optimize:
            return interface_binding(name, library)
        if name not in resolved_bindings:
            resolved_bindings[name] = interface_binding(name, library)
        return resolved_bindings[name]
    if execution_cache is None:
        execution_cache = ExecutionCache()
    if sensors is None:
        from sensors import SensorHub, ClockSurface
        sensors = SensorHub()
        sensors.register_surface('clock', ClockSurface())
    # Check the whole dependency closure before any effect. Forgetting even a
    # late input lesson must fail before an earlier action can run.
    validated = set()
    def preflight(current, chain=()):
        if len(chain) > 20:
            raise ValueError('Procedure call depth exceeded.')
        validate_graph(current, library)
        if current['input_type'] in {'Number','List[Number]'} or any(n['op'] in {'literal','as_number','as_numbers'} for n in current['nodes']):
            name = binding('parse')
            if name not in validated:
                preflight(library[name]['graph'], chain+(name,))
                validated.add(name)
        for node in current['nodes']:
            if node['op'] in {'call','tool'} | NUMERIC_OPERATIONS:
                name = node['name'] if node['op']=='call' else binding(node['name'] if node['op']=='tool' else node['op'])
                if name in chain:
                    raise ValueError('Recursive procedure calls are not supported.')
                if name not in validated:
                    preflight(library[name]['graph'], chain + (name,))
                    validated.add(name)
            for field in ('body', 'guard'):
                if field in node:
                    preflight(node[field], chain)
    preflight(graph)
    if execution_cache is not None:
        execution_cache.prepare(library)
        sensors.surfaces['engine'] = EngineSurface(execution_cache, library)
    trace, remaining = [], [limit]
    memo, purity, bindings, numeric_usage = {}, {}, {}, {}
    cache_usage = {'hits': 0, 'misses': 0, 'procedures': {},
                   'prepared_plan_hits': 0, 'prepared_plan_misses': 0}
    def pure(name, path=()):
        if name in purity: return purity[name]
        if name in path: return False
        def walk(program):
            for node in program['nodes']:
                if node['op'] in {'observe','act','tool','invoke','emit'}: return False
                if node['op'] in {'literal','as_number','as_numbers'}:
                    parser = interface_binding('parse', library)
                    if parser != name and not pure(parser, path+(name,)): return False
                if node['op']=='call' and not pure(node['name'], path+(name,)): return False
                if node['op'] in NUMERIC_OPERATIONS and not pure(binding(node['op']), path+(name,)): return False
                if any(not walk(node[field]) for field in ('body','guard') if field in node): return False
            return True
        purity[name] = walk(library[name]['graph'])
        return purity[name]
    def program(name, argument, path):
        if name in path: raise ValueError('Recursive procedure calls are not supported.')
        target = library[name]['graph']
        key = None
        cross_key = None
        if execution_cache is not None and target.get('cache_across_runs') and target['input_type'] == 'Data' and target['output_type'] == 'Data' and pure(name):
            cross_key = (name, json.dumps(argument, sort_keys=True, separators=(',', ':'), allow_nan=False))
            cached = execution_cache.get(cross_key)
            if cached is not None:
                value, cost = cached
                # A warm cache must not bypass a caller's resource allowance.
                remaining[0] -= cost
                if remaining[0] < 0:
                    raise ValueError('Cached procedure exceeds the step budget.')
                cache_usage['hits'] += 1
                cache_usage['procedures'][name] = cache_usage['procedures'].get(name, 0) + 1
                return value
            cache_usage['misses'] += 1
        if target.get('memoize') and pure(name):
            key = (name, json.dumps(argument, sort_keys=True, default=str))
            if key in memo: return memo[key]
        before = remaining[0]
        result = run(target, argument, path+(name,))
        if cross_key is not None:
            execution_cache.put(cross_key, result, before - remaining[0])
        if key is not None and len(memo)<20000: memo[key] = result
        return result
    def typed(value, kind, path=()):
        if kind=='Number':
            if type(value) is bool: raise ValueError('A boolean is not a Number.')
            return bounded_number(program(binding('parse'),str(value),path))
        if kind=='List[Number]':
            if not isinstance(value,list) or len(value)>200: raise ValueError('A numeric list has at most 200 entries.')
            return [typed(v,'Number',path) for v in value]
        return normalize(value,kind)
    def numeric(operation, args, path):
        import foundation
        if operation not in bindings: bindings[operation] = binding(operation)
        name = bindings[operation]
        numeric_usage.setdefault(operation, {'procedure':name,'calls':0})['calls'] += 1
        if operation in {'size', 'indices'} and execution_cache.optimize:
            # These ports already contain validated immutable Data. Passing
            # it to a graph does not require a JSON serialization round trip.
            argument = args[0]
        elif operation in {'size','length','indices'}: argument = foundation.data(args[0])
        elif len(args)==1: argument = str(args[0])
        else: argument = {'a':str(args[0]),'b':str(args[1])}
        result = program(name,argument,path)
        if operation in {'less','equal','is_integer'}:
            if type(result) is not bool: raise ValueError('The taught numerical comparison must return Bool.')
            return result
        if operation=='indices': return [int(v) for v in result]
        if operation=='range': return normalize(result,'List[Number]')
        return bounded_number(result)

    io_remaining = 1000
    explicit_trace = graph.get("trace_mode") == "explicit"
    # Values are immutable inside the interpreter. Cache their structural
    # bounds, retaining references to avoid Python id reuse. Trace settings
    # never disable resource limits. Keep the cache itself bounded.
    shapes = OrderedDict()
    literals = {}
    layouts = {}
    absent = object()
    scalars = set()
    def check_data(value):
        cached = shapes.get(id(value))
        if cached is not None and cached[0] is value:
            shapes.move_to_end(id(value))
            return cached[1:]
        if type(value) in {list, dict}:
            if len(value) > 2000:
                raise ValueError('Data collection exceeds its size budget.')
            if type(value) is dict and any(type(k) is not str for k in value):
                raise ValueError('Data record keys must be text.')
            parts = [check_data(v) for v in (value.values() if type(value) is dict else value)]
            count, depth = 1 + sum(p[0] for p in parts), 1 + max((p[1] for p in parts), default=-1)
            if count > 100000 or depth > 64:
                raise ValueError('Data exceeds its item or nesting budget.')
            if len(shapes) >= 10000:
                shapes.popitem(last=False)
            shapes[id(value)] = (value, count, depth)
            return count, depth
        if type(value) not in {str, int, float, bool, type(None)}:
            _bounded_json(value)
            return 1, 0
        scalar_key = (type(value), value)
        if scalar_key not in scalars:
            _bounded_json(value)
            if len(scalars) < 4096:
                scalars.add(scalar_key)
        return 1, 0

    def show(value):
        if isinstance(value, Fraction):
            return number_text(value)
        if isinstance(value, dict):
            if "variables" in value and "domains" in value and "constraints" in value:
                return f"CSP({len(value['variables'])} variables, {len(value['constraints'])} constraints)"
            return str(value)[:300]
        if isinstance(value, list):
            return "[" + ", ".join(show(v) for v in value) + "]"
        return str(value)

    def run(current, arg, path, suppress_trace=False):
        suppress_trace = suppress_trace or explicit_trace or current.get("trace_mode") == "explicit"
        if len(path) > 20:
            raise ValueError("Procedure call depth exceeded.")
        # Reuse prepared instructions across inputs and runs, including loop
        # bodies. Content hashes rebuild changed rules; original IDs stay in
        # traces. The per-run identity map avoids hashing on every iteration.
        if id(current) not in layouts:
            if execution_cache is None:
                layouts[id(current)] = prepare_layout(current)
            else:
                layout, hit = execution_cache.layout(current)
                layouts[id(current)] = layout
                cache_usage['prepared_plan_hits' if hit else 'prepared_plan_misses'] += 1
        nodes, output_index, data_checks = layouts[id(current)]
        values = [absent] * len(nodes)

        def visit(instruction_index):
            nonlocal io_remaining
            if values[instruction_index] is not absent:
                return values[instruction_index]
            remaining[0] -= 1
            if remaining[0] < 0:
                raise ValueError("Execution stopped at its step budget.")
            instruction = nodes[instruction_index]
            node = instruction.fields
            node_id = instruction.source_id
            op = instruction.opcode
            if op == OP_INPUT:
                value = arg
            elif op == OP_LITERAL:
                value = typed(node["value"], "Number", path)
            elif op == OP_DATA_LITERAL:
                # Literals and intermediate Data are immutable during a run.
                # Copy/validate a literal once, even when a loop or many calls
                # revisit it. In particular, large taught tables stay shared.
                if id(node) not in literals:
                    literals[id(node)] = normalize(node.get("value"), "Data")
                value = literals[id(node)]
            elif op in {OP_OBSERVE, OP_ACT}:
                if sensors is None:
                    raise ValueError("Run this procedure through the canvas controls to enable sensory access.")
                visit(instruction.inputs[0])  # Explicit sequence dependency for effects.
                io_remaining -= 1
                if io_remaining < 0:
                    raise ValueError('Execution stopped at its device-operation budget.')
                if op == OP_OBSERVE:
                    value = sensors.perceive(node["surface"])
                else:
                    arguments = visit(instruction.inputs[1])
                    value = sensors.act(node["surface"], node["action"], arguments)
                event = sensors.events[-1]
                trace.append({"node": node_id, "path": list(path), "operation": OP_NAMES[op],
                              "surface": node["surface"], "action": node.get("action"),
                              "event_id": event["event_id"], "result": str(value.get("feedback")) if isinstance(value, dict) else show(value)})
            elif op == OP_TOOL:
                target = binding(node['name'])
                start_event = len(sensors.events)
                value = run(library[target]['graph'], None, path + (target,))
                observation = sensors.events[-1]['payload'] if len(sensors.events)>start_event else None
                trace.append({"node": node_id, "path": list(path), "operation": node["name"],
                              "result": show(value), "observation": observation})
            elif op == OP_CHOOSE:
                condition = visit(instruction.inputs[0])
                value = visit(instruction.inputs[1 if condition else 2])
            elif op == OP_REQUIRE:
                if not visit(instruction.inputs[0]):
                    raise ValueError(str(node.get('message', 'Procedure input does not satisfy its stored precondition.'))[:500])
                value = visit(instruction.inputs[1])
            elif op == OP_ATTEMPT:
                argument = visit(instruction.inputs[0])
                try:
                    result = run(node['body'],argument,path+('attempt',),suppress_trace)
                    value = {'ok':True,'result':result}
                except (ValueError,KeyError) as error:
                    value = {'ok':False,'error':str(error)}
            elif op == OP_WHILE:
                value = visit(instruction.inputs[0])
                while run(node["guard"], value, path + ("guard",), suppress_trace):
                    remaining[0] -= 1
                    if remaining[0] < 0:
                        raise ValueError("Loop stopped at its step budget.")
                    value = run(node["body"], value, path + ("body",), suppress_trace)
            else:
                args = [visit(i) for i in instruction.inputs]
                if op == OP_CALL:
                    name = node["name"]
                    if name in path:
                        raise ValueError("Recursive procedure calls are not supported.")
                    target = library[name]["graph"]
                    value = program(name, args[0], path)
                elif op == OP_INVOKE:
                    name, argument = args
                    if not isinstance(name, str) or name not in library:
                        raise ValueError('Missing taught procedure: ' + str(name))
                    if name in path:
                        raise ValueError('Recursive procedure calls are not supported.')
                    target = library[name]['graph']
                    preflight(target, path + (name,))
                    result = program(name, typed(argument, target['input_type'], path), path)
                    if target['output_type'] == 'Number':
                        value = int(result) if result.denominator == 1 else number_text(result)
                    elif target['output_type'] == 'List[Number]':
                        value = [int(v) if v.denominator == 1 else number_text(v) for v in result]
                    else:
                        value = result
                elif op == OP_GET:
                    value = args[0]
                    for key in node["path"]:
                        if isinstance(value, dict) and isinstance(key, str) and key in value:
                            value = value[key]
                        elif isinstance(value, list) and type(key) is int and 0 <= key < len(value):
                            value = value[key]
                        else:
                            raise ValueError("No observed field at " + str(node["path"]) + ".")
                elif op == OP_LOOKUP:
                    table, key = args
                    if not isinstance(table, dict) or not isinstance(key, str) or key not in table:
                        raise ValueError("No taught interpretation for symbol: " + str(key))
                    value = table[key]
                elif op == OP_ITEM:
                    container, key = args
                    if isinstance(container, list) and type(key) is int and -len(container) <= key < len(container):
                        value = container[key]
                    elif isinstance(container, dict) and isinstance(key, str) and key in container:
                        value = container[key]
                    else:
                        raise ValueError("Collection key is absent or out of bounds.")
                elif op == OP_SET_ITEM:
                    container, key, replacement = args
                    if isinstance(container, list) and type(key) is int and 0 <= key < len(container):
                        value = list(container); value[key] = replacement
                    elif isinstance(container, dict) and isinstance(key, str):
                        value = dict(container); value[key] = replacement
                    else:
                        raise ValueError("Cannot update that collection key.")
                elif op == OP_KIND_OF:
                    value = {dict:'record', list:'list', str:'text', int:'number', float:'number', bool:'bool', type(None):'null'}[type(args[0])]
                elif op == OP_HAS_KEY:
                    value = isinstance(args[0], dict) and isinstance(args[1], str) and args[1] in args[0]
                elif op == OP_KEYS:
                    if not isinstance(args[0], dict): raise ValueError('Keys requires a record.')
                    value = list(args[0])
                elif op == OP_REVERSE:
                    if not isinstance(args[0], list): raise ValueError('Reverse requires a list.')
                    value = list(reversed(args[0]))
                elif op in {OP_LOWER, OP_CHARACTERS}:
                    if not isinstance(args[0], str): raise ValueError('Text operation requires text.')
                    value = args[0].casefold() if op == OP_LOWER else list(args[0])
                elif op == OP_JOIN_TEXT:
                    if not isinstance(args[0], list) or any(not isinstance(v,str) for v in args[0]) or not isinstance(args[1],str):
                        raise ValueError('Join requires text values and a separator.')
                    value = args[1].join(args[0])
                elif op == OP_SPLIT_TEXT:
                    if not all(isinstance(v,str) for v in args) or not args[1]: raise ValueError('Split requires text and a nonempty separator.')
                    value = args[0].split(args[1])
                elif op == OP_REPLACE_TEXT:
                    if not all(isinstance(v,str) for v in args) or not args[1]: raise ValueError('Replace requires text and a nonempty search string.')
                    value = args[0].replace(args[1],args[2])
                elif op == OP_AS_NUMBERS:
                    value = typed(args[0], 'List[Number]', path)
                elif op in {OP_CONCAT, OP_DIFFERENCE, OP_CONTAINS}:
                    if not isinstance(args[0], list):
                        raise ValueError("Collection operation requires a list.")
                    if op == OP_CONTAINS:
                        value = args[1] in args[0]
                    else:
                        if not isinstance(args[1], list):
                            raise ValueError("Collection operation requires two lists.")
                        value = args[0] + args[1] if op == OP_CONCAT else [v for v in args[0] if v not in args[1]]
                elif op in {OP_UNIQUE, OP_FLATTEN, OP_SLICE, OP_SORT, OP_INDICES}:
                    if not isinstance(args[0], list):
                        raise ValueError("Collection operation requires a list.")
                    if op == OP_UNIQUE:
                        value = []
                        for entry in args[0]:
                            if entry not in value: value.append(entry)
                    elif op == OP_FLATTEN:
                        if any(not isinstance(entry, list) for entry in args[0]):
                            raise ValueError("Flatten requires a list of lists.")
                        value = [item for entry in args[0] for item in entry]
                    elif op == OP_INDICES:
                        value = numeric(OP_NAMES[op], args, path)
                    elif op == OP_SLICE:
                        value = args[0][node.get("start"):node.get("stop")]
                    else:
                        key = node["key"]
                        if any(not isinstance(entry, dict) or key not in entry for entry in args[0]):
                            raise ValueError("Sort key is missing from a record.")
                        try: value = sorted(args[0], key=lambda entry: entry[key])
                        except TypeError: raise ValueError("Sort values have incompatible types.") from None
                elif op == OP_SIZE:
                    if not isinstance(args[0], (list, dict, str)):
                        raise ValueError("Size requires a collection or text.")
                    value = numeric(OP_NAMES[op], args, path)
                elif op == OP_DATA_LIST:
                    value = args
                elif op == OP_AS_BOOL:
                    value = normalize(args[0], "Bool")
                elif op == OP_BOOL_DATA:
                    value = args[0]
                elif op == OP_EMIT:
                    value = args[0]
                    if len(trace) < 2000:
                        trace.append({"node": node_id, "path": list(path), "operation": node.get("label", "emit"), "result": show(args[1]), 'evidence': args[1]})
                elif op == OP_TEXT:
                    if type(args[0]) not in {str, int, float, bool}:
                        raise ValueError("Text conversion needs a scalar value.")
                    value = str(args[0])
                elif op == OP_RECORD:
                    value = dict(zip(node["keys"], args))
                elif op in {OP_MAP, OP_FILTER}:
                    if not isinstance(args[0], list) or len(args[0]) > 2000:
                        raise ValueError("Map/filter needs a list of at most 2000 values.")
                    value = []
                    for entry in args[0]:
                        mapped = run(node["body"], {"item": entry, "context": args[1]} if len(args) == 2 else entry, path + (node_id,), suppress_trace)
                        if op == OP_MAP:
                            value.append(mapped)
                        elif mapped:
                            value.append(entry)
                elif op == OP_DATA_EQUAL:
                    value = type(args[0]) is type(args[1]) and args[0] == args[1]
                elif op == OP_AS_NUMBER:
                    value = typed(args[0], "Number", path)
                elif op == OP_AS_DATA:
                    value = int(args[0]) if args[0].denominator == 1 else number_text(args[0])
                elif op == OP_LIST:
                    value = args
                elif op in NUMERIC_OPCODES:
                    value = numeric(OP_NAMES[op], args, path)
                elif op == OP_NOT:
                    value = not args[0]
                elif op == OP_AND:
                    value = args[0] and args[1]
                elif op == OP_OR:
                    value = args[0] or args[1]
                elif op == OP_LENGTH:
                    value = numeric(OP_NAMES[op], args, path)
                elif op == OP_AT:
                    if args[1].denominator != 1 or not 0 <= args[1] < len(args[0]):
                        raise ValueError("List index is outside the available entries.")
                    value = args[0][int(args[1])]
                elif op == OP_APPEND:
                    value = args[0] + [args[1]]
                else:
                    raise ValueError("Unsupported instruction.")
            if isinstance(value, Fraction) and max(value.numerator.bit_length(), value.denominator.bit_length()) > 2048:
                raise ValueError("Numeric result exceeds the size budget.")
            if isinstance(value, list) and len(value) > (2000 if instruction.kind == 'Data' else 200):
                raise ValueError("List result exceeds the size budget.")
            if instruction.kind == "Data" and data_checks[instruction_index]:
                check_data(value)
            values[instruction_index] = value
            if not suppress_trace and len(trace) < 2000 and op not in {OP_INPUT, OP_LITERAL, OP_DATA_LITERAL, OP_TOOL, OP_OBSERVE, OP_ACT, OP_EMIT}:
                trace.append({"node": node_id, "path": list(path), "operation": node.get("name", OP_NAMES[op]), "result": show(value)})
            return value
        return visit(output_index)
    try:
        result = run(graph, typed(argument, graph["input_type"]), ())
    except (ValueError, KeyError) as error:
        error.graph_trace = copy.deepcopy(trace)
        raise
    finally:
        if meter is not None:
            meter.update(logical_steps=min(limit, max(0, limit - remaining[0])),
                         budget_exhausted=remaining[0] < 0)
    if numeric_usage:
        trace.append({'node':graph['output'],'operation':'taught_arithmetic','result':'Executed stored arithmetic bindings','evidence':numeric_usage})
    if execution_cache is not None:
        trace.append({'node':graph['output'],'operation':'execution_cache','result':cache_usage})
    return result, trace


def identity(kind):
    return {"input_type": kind, "output_type": kind,
            "nodes": [{"id": "x", "op": "input", "inputs": [], "type": kind}], "output": "x"}


def compose(first, second, library=None):
    validate_graph(first, library)
    validate_graph(second, library)
    if first["output_type"] != second["input_type"]:
        raise ValueError("The procedures' output and input types do not compose.")
    nodes, mapping = [], {}
    for graph, prefix in ((first, "a_"), (second, "b_")):
        for node in graph["nodes"]:
            if prefix == "b_" and node["op"] == "input":
                mapping[prefix + node["id"]] = mapping["a_" + first["output"]]
                continue
            clone = copy.deepcopy(node)
            clone["id"] = prefix + node["id"]
            clone["inputs"] = [mapping[prefix + i] for i in node["inputs"]]
            mapping[prefix + node["id"]] = clone["id"]
            nodes.append(clone)
    return validate_graph({"input_type": first["input_type"], "output_type": second["output_type"],
                           "nodes": nodes, "output": mapping["b_" + second["output"]]}, library)
