"""Language/transport boundary for sequences executed by taught graph programs."""
import json
import re
from uuid import uuid4

import foundation
from graph_runtime import bounded_data
from skill_system import preflight


def schema(methods):
    return {'type': 'object', 'additionalProperties': False,
            'required': ['steps', 'clarification'], 'properties': {
                'clarification': {'type': 'string'},
                'steps': {'type': 'array', 'maxItems': 8, 'items': {
                    'type': 'object', 'additionalProperties': False,
                    'required': ['id', 'method', 'argument_json'],
                    'properties': {'id': {'type': 'string'},
                                   'method': {'type': 'string', 'enum': methods},
                                   'argument_json': {'type': 'string'}}}}}}


def catalog(session):
    rows = [{'name': name, 'graph': {key: value for key, value in entry['graph'].items()
                                    if key in ('input_type', 'output_type', 'internal', 'sequence_input', 'skill', 'description')}}
            for name, entry in session.core.procedures.items()]
    return foundation.run(session.core.procedures, 'sequence_catalog', rows)[0]


def decode(proposal):
    """Validate transport structure; the graph validates step dependencies."""
    if not isinstance(proposal, dict) or set(proposal) != {'steps', 'clarification'}:
        raise ValueError('Please give the steps and explain which earlier result each step should use.')
    if not isinstance(proposal['clarification'], str) or len(proposal['clarification']) > 2000:
        raise ValueError('Please give a shorter clarification for these steps.')
    rows = proposal['steps']
    if not isinstance(rows, list) or len(rows) > 8:
        raise ValueError('Please split the sequence into at most eight steps.')
    result = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'method', 'argument_json'}:
            raise ValueError('Each step needs a name, a taught method and an input.')
        if any(not isinstance(row[k], str) for k in row):
            raise ValueError('A step name, method name and encoded input must be text.')
        if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]{0,39}', row['id']) or len(row['method']) > 60:
            raise ValueError('Please use short distinct step names.')
        if len(row['argument_json']) > 6000:
            raise ValueError('Please give a smaller input for that step.')
        try:
            argument = bounded_data(json.loads(row['argument_json']))
        except (ValueError, RecursionError):
            raise ValueError('I could not represent a step’s input. What value or earlier result should it use?') from None
        result.append({'id': row['id'], 'method': row['method'], 'argument': argument})
    return result


def handle(session, utterance, translator, force=False):
    library = session.core.procedures
    if not force:
        if 'sequence_detect' not in library or not foundation.run(library, 'sequence_detect', utterance)[0]:
            return None
    if 'sequence_interpret' in library:
        interpreted, _ = foundation.run(library, 'sequence_interpret', utterance)
        if interpreted is not None:
            proposal = {'clarification': '', 'steps': [
                {'id': step['id'], 'method': step['method'], 'argument_json': json.dumps(step['argument'])}
                for step in interpreted]}
            return execute(session, utterance, proposal)
    rows = catalog(session)
    methods = [row['name'] for row in rows]
    policy, _ = foundation.run(library, 'sequence_policy', None)
    planning_instructions = (foundation.run(library, 'task_plan_policy', None)[0]
                             if 'task_plan_policy' in library else policy['instructions'])
    context = {'speaker': session.speaker, 'addressee': session.assistant_name,
               'procedures': {row['name']: {'input': row['graph'].get('sequence_input', row['graph']['input_type']),
                                           'output': row['graph']['output_type'],
                                           'meaning': row['graph'].get('description', '')[:145]}
                              for row in rows}}
    if not hasattr(translator, 'translate_sequence'):
        raise ValueError('This language interface does not support linked-command translation yet.')
    proposal = translator.translate_sequence(utterance, context, planning_instructions, schema(methods))
    return execute(session, utterance, proposal, methods)


def execute(session, utterance, proposal, methods=None):
    methods = methods if methods is not None else [row['name'] for row in catalog(session)]
    library = session.core.procedures.to_dict()
    bindings = {'speaker': session.speaker, 'assistant': session.assistant_name}
    steps = []
    try:
        steps = decode(proposal)
        if not proposal['clarification'].strip() and any(step['method']=='task_input' for step in steps):
            from persistent_tasks import create
            return create(session, utterance, None, steps)
        if proposal['clarification'].strip():
            raise ValueError(proposal['clarification'].strip())
        foundation.run(library, 'sequence_prepare', {'steps': steps, 'bindings': bindings, 'methods': methods})
        # Static dependency checking applies to the whole plan before its first
        # device operation. Dynamic references remain the graph's responsibility.
        for name in [step['method'] for step in steps] + ['sequence_execute']:
            preflight(name, library)
    except ValueError as error:
        needs_initial, _ = foundation.run(library, 'sequence_needs_initial', steps)
        question = "What starting value should I use for ‘that’?" if needs_initial else str(error)
        return session.run_skill('sequence_question', {'original': utterance, 'question': question, 'steps': steps}, utterance)[0]

    session.core._ensure_current()
    identifier = str(uuid4())
    record = {'original': utterance, 'translation': proposal, 'steps': steps,
              'status': 'running', 'program_roots': session.core.procedures._rows()}
    session.store.map('skills.sequences')[identifier] = record
    try:
        # Use the checked snapshot for every step; lesson edits during execution
        # cannot change the remaining plan's meaning.
        result, trace = foundation.run(library, 'sequence_execute', {'steps': steps, 'bindings': bindings}, session.sensors)
    except (ValueError, KeyError) as error:
        record.update(status='failed', error=str(error), trace=getattr(error, 'graph_trace', []))
        session.store.map('skills.sequences')[identifier] = record
        raise
    record.update(status=result['status'], result=foundation.data(result), trace=trace)
    if result['status'] == 'completed' and isinstance(result['result'], (dict, list)):
        # Presentation of an already computed value; the host does not choose
        # sequence steps, infer fields or perform any arithmetic here.
        result['text'] = 'Result: ' + json.dumps(foundation.data(result['result']), ensure_ascii=False) + '\n' + result['text'].partition('\n')[2]
        record['result'] = foundation.data(result)
    session.store.map('skills.sequences')[identifier] = record
    run = {'id': identifier, 'procedure': 'sequence_execute', **record}
    session.language_records.append({'source': 'user-sequence-request', 'original': utterance,
        'translation': {'kind': 'sequence', 'steps': steps}, 'answer': result['text'],
        'interpretation': 'Linked steps: ' + ' → '.join(step['method'] for step in steps), 'tool_runs': [run]})
    return result['text']
