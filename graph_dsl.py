"""Authoring convenience for JSON lessons; not used by graph execution."""


class Graph:
    def __init__(self, input_type='Data'):
        self.nodes = []
        self.input_type = input_type
        self.input = self.op('input', kind=input_type)

    def op(self, operation, *inputs, kind='Data', **fields):
        identifier = 'n' + str(len(self.nodes))
        self.nodes.append(dict(id=identifier, op=operation, inputs=list(inputs), type=kind, **fields))
        return identifier

    def data(self, value): return self.op('data_literal', value=value)
    def number(self, value): return self.op('literal', kind='Number', value=str(value))
    def get(self, value, *path): return self.op('get', value, path=list(path))
    def record(self, **fields): return self.op('record', *fields.values(), keys=list(fields))
    def call(self, name, value, kind='Data'): return self.op('call', value, kind=kind, name=name)
    def eq(self, a, b): return self.op('data_equal', a, b, kind='Bool')
    def size(self, value): return self.op('size', value, kind='Number')
    def nonempty(self, value): return self.op('less', self.number(0), self.size(value), kind='Bool')
    def choose(self, test, yes, no, kind='Data'): return self.op('choose', test, yes, no, kind=kind)
    def map(self, values, body, context=None, filter=False):
        return self.op('filter' if filter else 'map', values, *([] if context is None else [context]), body=body)
    def finish(self, output, kind='Data', **metadata):
        return dict(input_type=self.input_type, output_type=kind, nodes=self.nodes, output=output, **metadata)


class G(Graph):
    """Authoring notation only; emits portable graph records."""
    def num(self, v): return self.op('as_number', v, kind='Number')
    def calc(self, op, *args): return self.op('as_data', self.op(op, *(self.num(a) for a in args), kind='Number'))
    def lt(self, a, b): return self.op('less', self.num(a), self.num(b), kind='Bool')
    def both(self, a, b): return self.op('and', a, b, kind='Bool')
    def either(self, a, b): return self.op('or', a, b, kind='Bool')
    def inverse(self, a): return self.op('not', a, kind='Bool')
    def boolean(self, a): return self.op('as_bool', a, kind='Bool')
    def datum(self, a): return self.op('bool_data', a)
    def length(self, a): return self.op('as_data', self.size(a))
    def item(self, a, i): return self.op('item', a, i)
    def append(self, a, v): return self.op('concat', a, self.op('data_list', v))
    def loop(self, initial, guard, body): return self.op('while', initial, guard=guard, body=body)
    def put(self, a, key, v): return self.op('set_item', a, self.data(key), v)
    def has(self, a, key): return self.op('has_key', a, key, kind='Bool')
    def textcat(self, *parts): return self.op('join_text', self.op('data_list', *parts), self.data(''))
