"""Authoritative, typed graph storage using Python's embedded SQLite engine.

Every container is a node with ordered edges to its keys and values. Named roots
select current knowledge; historical records may retain older, inactive nodes.
No procedure or evidence object is stored as an opaque JSON document.
"""
import copy
import hashlib
import json
import sqlite3
import threading
from collections.abc import Mapping, MutableMapping, MutableSequence
from contextlib import contextmanager
from fractions import Fraction
from functools import wraps
from pathlib import Path
from uuid import uuid4


SCHEMA = 1


def atomic_graph(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.store.transaction():
            return method(self, *args, **kwargs)
    return wrapped


def database_path(path):
    path = Path(path)
    return path if path.suffix in {'.sqlite3', '.sqlite', '.db'} else path.with_suffix('.graph.sqlite3')


def plain(value):
    if isinstance(value, GraphMap):
        return value.to_dict()
    if isinstance(value, GraphSequence):
        return list(value)
    if isinstance(value, dict):
        return {plain(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(plain(v) for v in value)
    return value


class GraphStore:
    def __init__(self, path=None):
        self.path = Path(path).resolve() if path else None
        self.lock = threading.RLock()
        self.connection = sqlite3.connect(str(self.path) if self.path else ':memory:',
                                          isolation_level=None, check_same_thread=False)
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('PRAGMA synchronous=FULL')
        version = self.connection.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, SCHEMA):
            self.connection.close()
            raise ValueError('Unsupported graph database version; memory was not changed.')
        if version == 0:
            tables = self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if tables:
                self.connection.close()
                raise ValueError('This is not a Seed graph database.')
            self.connection.executescript('''
                CREATE TABLE nodes(id TEXT PRIMARY KEY, kind TEXT NOT NULL, atom TEXT);
                CREATE TABLE edges(source TEXT NOT NULL REFERENCES nodes(id), position INTEGER NOT NULL,
                    key_node TEXT REFERENCES nodes(id), target TEXT NOT NULL REFERENCES nodes(id),
                    PRIMARY KEY(source,position));
                CREATE TABLE roots(namespace TEXT NOT NULL, key_node TEXT NOT NULL REFERENCES nodes(id),
                    value_node TEXT NOT NULL REFERENCES nodes(id), position INTEGER NOT NULL,
                    PRIMARY KEY(namespace,key_node));
                CREATE INDEX root_order ON roots(namespace,position);
                PRAGMA user_version=1;
            ''')
        self._cache = {}
        self._depth = 0

    @contextmanager
    def transaction(self):
        with self.lock:
            depth = self._depth
            self.connection.execute('BEGIN IMMEDIATE' if depth == 0 else 'SAVEPOINT nested_' + str(depth))
            self._depth += 1
            try:
                yield self
            except BaseException:
                self.connection.execute('ROLLBACK' if depth == 0 else 'ROLLBACK TO nested_' + str(depth))
                if depth:
                    self.connection.execute('RELEASE nested_' + str(depth))
                self._cache.clear()
                raise
            else:
                self.connection.execute('COMMIT' if depth == 0 else 'RELEASE nested_' + str(depth))
            finally:
                self._depth -= 1

    def _encode(self, value, persist=True):
        children, atom = [], None
        if isinstance(value, Mapping):
            kind = 'record'
            children = [(self._encode(k, persist), self._encode(v, persist)) for k, v in value.items()]
        elif isinstance(value, (list, tuple, GraphSequence)):
            kind = 'tuple' if isinstance(value, tuple) else 'list'
            children = [(None, self._encode(v, persist)) for v in value]
        elif isinstance(value, Fraction):
            kind, atom = 'rational', str(value)
        elif value is None or type(value) in (bool, int, float, str):
            kind = 'null' if value is None else type(value).__name__
            atom = json.dumps(value, ensure_ascii=False, allow_nan=False)
        else:
            raise ValueError('Unsupported graph value: ' + type(value).__name__)
        identifier = hashlib.sha256(json.dumps([kind, atom, children], ensure_ascii=False,
                                               separators=(',', ':')).encode()).hexdigest()
        if persist and identifier not in self._cache:
            inserted = self.connection.execute('INSERT OR IGNORE INTO nodes VALUES (?,?,?)',
                                               (identifier, kind, atom)).rowcount
            if inserted and children:
                self.connection.executemany('INSERT INTO edges VALUES (?,?,?,?)',
                    [(identifier, i, key, target) for i, (key, target) in enumerate(children)])
            # Only decoded nodes are cached; cache membership must never stand in
            # for persistence of a node after rolling back a transaction.
        return identifier

    def _decode(self, identifier):
        if identifier in self._cache:
            return self._cache[identifier]
        row = self.connection.execute('SELECT kind,atom FROM nodes WHERE id=?', (identifier,)).fetchone()
        if row is None:
            raise ValueError('Graph database has a missing node.')
        kind, atom = row
        if kind in ('record', 'tuple', 'list'):
            children = self.connection.execute('SELECT key_node,target FROM edges WHERE source=? ORDER BY position',
                                               (identifier,)).fetchall()
            if kind == 'record':
                result = {self._decode(k): self._decode(v) for k, v in children}
            else:
                result = [self._decode(v) for _, v in children]
                if kind == 'tuple':
                    result = tuple(result)
        else:
            result = Fraction(atom) if kind == 'rational' else json.loads(atom)
        self._cache[identifier] = result
        return result

    def map(self, namespace):
        return GraphMap(self, namespace)

    def sequence(self, namespace):
        return GraphSequence(self, namespace)

    def clone_namespaces(self, names):
        target = GraphStore()
        with self.lock:
            if self._depth:
                # SQLite backup cannot copy its own open write transaction.
                with target.transaction():
                    for namespace in names:
                        target.map(namespace).replace(self.map(namespace).to_dict())
            else:
                # Copy immutable storage pages instead of decoding, copying and
                # re-encoding every instruction and evidence tree in Python.
                self.connection.backup(target.connection)
                placeholders = ','.join('?' for _ in names)
                with target.transaction():
                    target.connection.execute('DELETE FROM roots WHERE namespace NOT IN (' + placeholders + ')', tuple(names))
        return target

    def save(self, path):
        """Bind new stores atomically; bound stores already commit each mutation."""
        path = database_path(path).resolve()
        with self.lock:
            if self.path == path:
                return path
            if self._depth:
                raise ValueError('Commit the graph transaction before saving a copy.')
            temporary = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
            try:
                target = sqlite3.connect(str(temporary))
                try:
                    self.connection.backup(target)
                finally:
                    target.close()
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
            # Keep the same store and views while switching to the durable file.
            self.connection.close()
            self.connection = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
            self.connection.execute('PRAGMA foreign_keys=ON')
            self.connection.execute('PRAGMA synchronous=FULL')
            self.path = path
        return path

    def inspect(self, namespace=None):
        """Return stored IDs and edges reachable from current selected roots."""
        with self.lock:
            where, args = (' WHERE namespace=?', (namespace,)) if namespace else ('', ())
            roots = self.connection.execute('SELECT namespace,key_node,value_node,position FROM roots' + where +
                                            ' ORDER BY namespace,position', args).fetchall()
            reachable, pending, edges = set(), [n for r in roots for n in r[1:3]], []
            while pending:
                node = pending.pop()
                if node in reachable:
                    continue
                reachable.add(node)
                for position, key, target in self.connection.execute(
                        'SELECT position,key_node,target FROM edges WHERE source=? ORDER BY position', (node,)):
                    edges.append({'source': node, 'position': position, 'key': key, 'target': target})
                    pending.append(target)
                    if key:
                        pending.append(key)
            nodes = []
            for identifier in sorted(reachable):
                kind, atom = self.connection.execute('SELECT kind,atom FROM nodes WHERE id=?', (identifier,)).fetchone()
                nodes.append({'id': identifier, 'kind': kind, 'atom': atom})
            return {'schema': 'seed.graph-database.v1', 'storage': 'sqlite', 'path': str(self.path) if self.path else None,
                    'roots': [{'namespace': n, 'key': k, 'value': v, 'position': p,
                               'name': str(self._decode(k))} for n, k, v, p in roots],
                    'nodes': nodes, 'edges': edges}

    def close(self):
        self.connection.close()


class GraphSnapshot(Mapping):
    """Fixed root references; copy values only when execution requests them."""
    def __init__(self, mapping):
        self.store = mapping.store
        with self.store.lock:
            self.roots = {self.store._decode(k): v for k, v in mapping._rows()}
        self._values = {}
        self.bindings = None
        self.fingerprint_data = sorted(self.roots.items(), key=lambda pair: str(pair[0]))

    def __contains__(self, key): return key in self.roots
    def __len__(self): return len(self.roots)
    def __iter__(self): return iter(self.roots)
    def __getitem__(self, key):
        if key not in self._values:
            with self.store.lock:
                self._values[key] = copy.deepcopy(self.store._decode(self.roots[key]))
        return self._values[key]

    def interface_names(self, name):
        if self.bindings is None:
            self.bindings = {}
            with self.store.lock:
                for key, root in self.roots.items():
                    interface = self.store._decode(root).get('graph', {}).get('interface')
                    for value in interface if isinstance(interface, list) else [interface]:
                        if isinstance(value, str): self.bindings.setdefault(value, []).append(key)
        return self.bindings.get(name, [])


class GraphMap(MutableMapping):
    def __init__(self, store, namespace):
        self.store, self.namespace = store, namespace

    def _rows(self):
        with self.store.lock:
            return self.store.connection.execute(
                'SELECT key_node,value_node FROM roots WHERE namespace=? ORDER BY position', (self.namespace,)).fetchall()

    def __len__(self):
        with self.store.lock:
            return self.store.connection.execute('SELECT count(*) FROM roots WHERE namespace=?', (self.namespace,)).fetchone()[0]

    def __iter__(self):
        with self.store.lock:
            return iter([self.store._decode(k) for k, _ in self._rows()])

    def __getitem__(self, key):
        with self.store.lock:
            kid = self.store._encode(key, persist=False)
            row = self.store.connection.execute('SELECT value_node FROM roots WHERE namespace=? AND key_node=?',
                                                 (self.namespace, kid)).fetchone()
            if row is None:
                raise KeyError(key)
            identifier = [row[0]]
            value = copy.deepcopy(self.store._decode(identifier[0]))
        root = []

        def changed():
            with self.store.transaction():
                current = self.store.connection.execute('SELECT value_node FROM roots WHERE namespace=? AND key_node=?',
                                                         (self.namespace, kid)).fetchone()
                if current is None or current[0] != identifier[0]:
                    raise ValueError('This graph record changed; read it again before editing.')
                self[key] = root[0]
                identifier[0] = self.store._encode(root[0])

        root.append(_tracked(value, changed))
        return root[0]

    def __contains__(self, key):
        with self.store.lock:
            kid = self.store._encode(key, persist=False)
            return self.store.connection.execute('SELECT 1 FROM roots WHERE namespace=? AND key_node=?',
                                                 (self.namespace, kid)).fetchone() is not None

    def __setitem__(self, key, value):
        with self.store.transaction():
            kid, vid = self.store._encode(key), self.store._encode(value)
            self.store.connection.execute('''INSERT INTO roots VALUES (?,?,?,
                (SELECT coalesce(max(position)+1,0) FROM roots WHERE namespace=?))
                ON CONFLICT(namespace,key_node) DO UPDATE SET value_node=excluded.value_node''',
                (self.namespace, kid, vid, self.namespace))

    def __delitem__(self, key):
        with self.store.transaction():
            kid = self.store._encode(key)
            if not self.store.connection.execute('DELETE FROM roots WHERE namespace=? AND key_node=?',
                                                  (self.namespace, kid)).rowcount:
                raise KeyError(key)

    def clear(self):
        with self.store.transaction():
            self.store.connection.execute('DELETE FROM roots WHERE namespace=?', (self.namespace,))

    def replace(self, values):
        values = dict(values)
        with self.store.transaction():
            for key in list(self):
                if key not in values:
                    del self[key]
            self.update(values)

    def to_dict(self):
        with self.store.lock:
            return {copy.deepcopy(self.store._decode(k)): copy.deepcopy(self.store._decode(v)) for k, v in self._rows()}

    def __deepcopy__(self, memo):
        return self.to_dict()

    def __repr__(self):
        return repr(self.to_dict())


class GraphSequence(MutableSequence):
    def __init__(self, store, namespace):
        self.store, self.namespace = store, namespace
        self.entries = store.map(namespace)

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self.entries[i] for i in range(*index.indices(len(self))) ]
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError(index)
        return self.entries[index]

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            values = list(self)
            values[index] = value
            self.replace(values)
        else:
            self[index]  # Check bounds, including negative indices.
            self.entries[index if index >= 0 else len(self) + index] = value

    def __delitem__(self, index):
        values = list(self)
        del values[index]
        self.replace(values)

    def insert(self, index, value):
        values = list(self)
        values.insert(index, value)
        self.replace(values)

    def append(self, value):
        with self.store.transaction():
            self.entries[len(self)] = value

    def replace(self, values):
        self.entries.replace(dict(enumerate(values)))

    def __iter__(self):
        return iter(self.entries.to_dict().values())

    def __eq__(self, other):
        return list(self) == list(other)

    def __deepcopy__(self, memo):
        return list(self)

    def __repr__(self):
        return repr(list(self))


def _tracked(value, changed):
    if isinstance(value, dict):
        result = _TrackedDict({k: _tracked(v, changed) for k, v in value.items()})
    elif isinstance(value, list):
        result = _TrackedList(_tracked(v, changed) for v in value)
    elif isinstance(value, tuple):
        return tuple(_tracked(v, changed) for v in value)
    else:
        return value
    result.changed = changed
    return result


class _TrackedDict(dict):
    def __deepcopy__(self, memo):
        return copy.deepcopy(dict(self), memo)

    def __setitem__(self, key, value):
        super().__setitem__(key, _tracked(value, self.changed))
        self.changed()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.changed()

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            dict.__setitem__(self, k, _tracked(v, self.changed))
        self.changed()

    def clear(self):
        super().clear()
        self.changed()

    def pop(self, key, *default):
        value = super().pop(key, *default)
        self.changed()
        return value

    def popitem(self):
        value = super().popitem()
        self.changed()
        return value

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]


class _TrackedList(list):
    def __deepcopy__(self, memo):
        return copy.deepcopy(list(self), memo)

    def __setitem__(self, index, value):
        value = [_tracked(v, self.changed) for v in value] if isinstance(index, slice) else _tracked(value, self.changed)
        super().__setitem__(index, value)
        self.changed()

    def __delitem__(self, index):
        super().__delitem__(index)
        self.changed()

    def append(self, value):
        super().append(_tracked(value, self.changed))
        self.changed()

    def extend(self, values):
        super().extend(_tracked(v, self.changed) for v in values)
        self.changed()

    def insert(self, index, value):
        super().insert(index, _tracked(value, self.changed))
        self.changed()

    def pop(self, index=-1):
        value = super().pop(index)
        self.changed()
        return value

    def remove(self, value):
        super().remove(value)
        self.changed()

    def clear(self):
        super().clear()
        self.changed()

    def reverse(self):
        super().reverse()
        self.changed()

    def sort(self, *args, **kwargs):
        super().sort(*args, **kwargs)
        self.changed()

    def __iadd__(self, values):
        self.extend(values)
        return self

    def __imul__(self, count):
        super().__imul__(count)
        self.changed()
        return self
