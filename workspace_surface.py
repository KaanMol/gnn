"""Raw local memory I/O. Programs supply paths, interpretation and operation order."""
import copy
from graph_runtime import validate_graph, bounded_data
from foundation import data


def key_value(value):
    return tuple(key_value(v) for v in value) if isinstance(value, list) else value


class WorkspaceSurface:
    actions = {'read': {'namespace': 'text', 'key': 'text or tuple-shaped list'},
               'keys': {'namespace': 'text'},
               'entries': {'namespace': 'text'},
               'write': {'namespace': 'text', 'key': 'text or tuple-shaped list', 'value': 'data'},
               'delete': {'namespace': 'text', 'key': 'text or tuple-shaped list'}}

    def __init__(self, store):
        self.store = store

    def observe(self):
        namespaces = [r[0] for r in self.store.connection.execute('SELECT DISTINCT namespace FROM roots ORDER BY namespace')]
        return {'format': 'workspace.v1', 'namespaces': namespaces, 'actions': self.actions}

    def act(self, action, arguments):
        if action not in self.actions or set(arguments) != set(self.actions[action]):
            raise ValueError('Use a registered workspace operation and its declared arguments.')
        namespace = arguments['namespace']
        if not isinstance(namespace, str) or len(namespace) > 120:
            raise ValueError('Namespace must be bounded text.')
        mapping = self.store.map(namespace)
        if action == 'keys':
            return bounded_data(data(list(mapping)))
        if action == 'entries':
            return bounded_data(data([{'key': key, 'value': value} for key, value in mapping.items()]))
        key = key_value(arguments['key'])
        if action == 'read':
            return bounded_data(data(mapping[key]))
        # Historical evidence belongs to the observation system, not to skills.
        if not namespace.startswith(('knowledge.', 'skills.', 'session.')):
            raise ValueError('This port can modify knowledge, skills and session settings; observation history is append-only.')
        with self.store.transaction():
            before = copy.deepcopy(mapping.get(key))
            if action == 'write':
                value = bounded_data(arguments['value'])
                if namespace == 'knowledge.procedures':
                    from procedures import procedure_name
                    if procedure_name(key) != key or not isinstance(value, dict) or 'graph' not in value:
                        raise ValueError('A procedure write needs a valid name and graph record.')
                    validate_graph(value['graph'], {**self.store.map('knowledge.procedures'), key: value})
                mapping[key] = value
            else:
                del mapping[key]
        return {'namespace': namespace, 'key': data(key), 'before': data(before),
                'after': data(mapping.get(key)), 'accepted': True}
