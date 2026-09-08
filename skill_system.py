"""Generic invocation and persistence for taught skills and goal programs.

Search, composition order and interface use are learned procedures. This module
connects their ports, validates execution boundaries and records actual outcomes.
"""
import copy
from uuid import uuid4

import foundation
from graph_runtime import validate_graph, interface_binding, NUMERIC_OPERATIONS, ExecutionCache


def preflight(name, library, path=(), heights=None):
    heights = {} if heights is None else heights
    if name not in library:
        raise ValueError('Missing taught procedure: ' + name)
    if name in path or len(path) > 20:
        raise ValueError('Recursive procedure calls are not supported.')
    if name in heights:
        if len(path) + heights[name] > 21:
            raise ValueError('Procedure call depth exceeded.')
        return heights[name]
    graph = library[name]['graph']
    validate_graph(graph, library)
    dependencies = set()
    def visit(graph):
        if graph['input_type'] in {'Number','List[Number]'} or any(n['op'] in {'literal','as_number','as_numbers'} for n in graph['nodes']):
            dependencies.add(interface_binding('parse',library))
        for node in graph['nodes']:
            if node['op'] in {'call', 'tool'} | NUMERIC_OPERATIONS:
                target = node['name'] if node['op'] == 'call' else interface_binding(node['name'] if node['op']=='tool' else node['op'], library)
                dependencies.add(target)
            for field in ('body', 'guard'):
                if field in node:
                    visit(node[field])
    visit(graph)
    height = 1 + max((preflight(target, library, path + (name,), heights) for target in dependencies), default=0)
    if len(path) + height > 21:
        raise ValueError('Procedure call depth exceeded.')
    heights[name] = height
    return height


class SkillSystem:
    def __init__(self, store, sensors):
        self.store, self.sensors = store, sensors
        self.execution_cache = ExecutionCache()

    @property
    def library(self):
        return self.store.map('knowledge.procedures')

    def catalog(self):
        result = []
        for name, entry in self.library.items():
            contract = entry['graph'].get('skill')
            if contract is not None:
                result.append({'name': name, 'requires': contract['requires'], 'provides': contract['provides'],
                               'deletes': contract.get('deletes', []), 'description': entry['graph'].get('description', '')})
        return result

    def run(self, name, argument):
        # The actual trace and device evidence are retained even when a later
        # instruction fails. This does not pretend physical inputs roll back.
        identifier = str(uuid4())
        record = {'kind': 'skill', 'procedure': name, 'input': copy.deepcopy(argument), 'status': 'running',
                  'program_roots': self.library._rows()}
        self.store.map('skills.runs')[identifier] = record
        try:
            result, trace = foundation.run(self.library, name, argument, self.sensors, execution_cache=self.execution_cache)
        except (ValueError, KeyError) as error:
            record.update(status='failed', error=str(error), trace=getattr(error,'graph_trace',[]))
            self.store.map('skills.runs')[identifier] = record
            raise
        record.update(status='executed', result=foundation.data(result), trace=trace)
        self.store.map('skills.runs')[identifier] = record
        return {'id': identifier, **record}

    def achieve(self, request):
        if not isinstance(request, dict) or not {'have', 'want', 'input'} <= set(request) or set(request) - {'have','want','input','check'}:
            raise ValueError('A goal needs have, want and input; check may name a taught outcome verifier.')
        for field in ('have','want'):
            if not isinstance(request[field], list) or len(request[field]) > 30 or any(not isinstance(v,str) or len(v)>100 for v in request[field]):
                raise ValueError('Goal tags must be a list of up to 30 short names.')
        if not request['want']:
            raise ValueError('Name at least one wanted outcome.')
        checker = request.get('check')
        if checker is not None and (not isinstance(checker,str) or checker not in self.library or self.library[checker]['graph']['output_type'] != 'Bool'):
            raise ValueError('The outcome checker must name a taught program returning Bool.')
        identifier = str(uuid4())
        goal = {'request': copy.deepcopy(request), 'status': 'planning', 'program_roots': self.library._rows()}
        self.store.map('skills.goals')[identifier] = goal
        try:
            plan, search_trace = foundation.run(self.library, 'plan_search', {
                'have': request['have'], 'wanted': request['want'], 'actions': self.catalog()})
            goal.update(plan=plan, search_trace=search_trace)
            if not plan['found']:
                goal['status'] = 'missing_knowledge'
                return {'id': identifier, **goal}
            library = self.library.to_dict()
            # Check the entire selected plan before any device action.
            for name in plan['plan'] + ['plan_execute'] + ([checker] if checker else []):
                preflight(name, library)
            result, trace = foundation.run(library, 'plan_execute', {'plan': plan['plan'], 'input': request['input']}, self.sensors)
            goal.update(result=result, trace=trace, status='executed_unverified')
            if checker:
                verified, check_trace = foundation.run(library, checker, result, self.sensors)
                goal.update(status='verified' if verified else 'check_failed', verification={'procedure': checker, 'passed': verified, 'trace': check_trace})
            return {'id': identifier, **goal}
        except (ValueError, KeyError) as error:
            goal.update(status='failed', error=str(error), trace=getattr(error,'graph_trace',[]))
            raise
        finally:
            self.store.map('skills.goals')[identifier] = goal
