"""Optional LLM language interface to the symbolic learner and toy sensors."""
import argparse
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from meaning import MeaningSystem, parse
from playground import Explorer, ToyWorld
from sensors import CanvasSurface, SensorHub, ToyWorldSensor, ClockSurface


from semantics import SCHEMA, INSTRUCTIONS, LOCAL_INSTRUCTIONS, validate, operation, is_question
from knowledge import Knowledge, label, fact_text
from graph_store import GraphStore, atomic_graph, database_path
import copy
from arithmetic import calculate, count, direct_math, direct_procedure, number_text
import date_tools
from date_tools import date_answer, direct_date
from location_language import direct_location
import procedures
import math_lessons
from graph_runtime import compose, execute_graph, validate_graph
from sudoku import SudokuBoard
from canvas_surface import BoardCanvas
import sudoku_lessons
import foundation
from skill_system import SkillSystem
from workspace_surface import WorkspaceSurface
from dialogue_surface import DialogueSurface

READ_OPERATIONS = {"sudoku_solve", "list_sudoku", "sudoku_describe", "sudoku_candidates", "solve_math", "rewrite_math", "list_math", "find", "current_date", "date_procedure", "query", "describe", "world_query", "calculate", "count", "run_procedure", "clarify", "plan_task"}


class OpenAILanguage:
    def __init__(self, model, api_key=None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.model or not self.api_key:
            raise ValueError("Configure OPENAI_API_KEY and pass --model (or set OPENAI_MODEL).")

    def translate(self, utterance, context):
        body = {"model": self.model, "store": False, "instructions": INSTRUCTIONS,
                "input": json.dumps({"utterance": utterance, "vocabulary": context}),
                "text": {"format": {"type": "json_schema", "name": "language_operation",
                                    "strict": True, "schema": SCHEMA}}}
        request = Request("https://api.openai.com/v1/responses", data=json.dumps(body).encode(),
                          headers={"Authorization": "Bearer " + self.api_key,
                                   "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=45) as response:
                data = json.load(response)
        except HTTPError as error:
            raise ValueError(f"Language API returned HTTP {error.code}; check credentials, model access, and quota.") from None
        except URLError:
            raise ValueError("Language API could not be reached.") from None
        if data.get("status") != "completed":
            raise ValueError("Language API did not complete the translation.")
        content = [part for item in data.get("output", []) if item.get("type") == "message"
                   for part in item.get("content", [])]
        if any(part.get("type") == "refusal" for part in content):
            return {"operations": [operation("clarify", text="The language interface declined this translation.")]}
        texts = [part["text"] for part in content if part.get("type") == "output_text"]
        if len(texts) != 1:
            raise ValueError("Expected one structured language translation.")
        return json.loads(texts[0])


class OllamaLanguage:
    def __init__(self, model=None, base_url="http://127.0.0.1:11434"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        if not self.model:
            data = self._request("/api/tags")
            gemma = [m["name"] for m in data.get("models", []) if "gemma" in m.get("name", "").lower()]
            if len(gemma) != 1:
                available = ", ".join(m["name"] for m in data.get("models", [])) or "none"
                raise ValueError("Pass --model with your Gemma model name. Installed models: " + available)
            self.model = gemma[0]

    def _request(self, path, body=None):
        request = Request(self.base_url + path,
                          data=None if body is None else json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=45) as response:
                return json.load(response)
        except HTTPError as error:
            raise ValueError(f"Ollama returned HTTP {error.code}; check the model name and server configuration.") from None
        except URLError:
            raise ValueError("Cannot reach Ollama at " + self.base_url +
                             ". Start Ollama or specify --base-url.") from None

    def translate(self, utterance, context):
        data = self._request("/api/chat", {
            "model": self.model, "stream": False, "format": SCHEMA,
            "options": {"temperature": 0},
            "messages": [{"role": "system", "content": INSTRUCTIONS},
                         {"role": "user", "content": json.dumps({"utterance": utterance, "vocabulary": context})}],
        })
        if not data.get("done") or data.get("done_reason") == "length":
            raise ValueError("Ollama did not complete the translation.")
        content = data.get("message", {}).get("content")
        if not isinstance(content, str):
            raise ValueError("Ollama returned no translation.")
        return json.loads(content)


class LlamaCppLanguage:
    def __init__(self, model=None, base_url="http://127.0.0.1:8080"):
        self.base_url = base_url.rstrip("/").removesuffix("/v1")
        self.model = model
        if not model:
            models = self._request("/v1/models").get("data", [])
            if len(models) != 1:
                raise ValueError("Pass --model with the served Gemma model ID from /v1/models.")
            self.model = models[0]["id"]

    def _request(self, path, body=None):
        request = Request(self.base_url + path,
                          data=None if body is None else json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=45) as response:
                return json.load(response)
        except HTTPError as error:
            raise ValueError(f"llama.cpp returned HTTP {error.code}; check model and schema support.") from None
        except URLError:
            raise ValueError("Cannot reach llama.cpp at " + self.base_url +
                             ". Start llama-server with Gemma or specify --base-url.") from None

    def _fit_messages(self, utterance, context, instructions, output_tokens, window):
        # A translation needs a little vocabulary, not executable lessons or the
        # full notebook. Rank optional entries; never truncate the user's message.
        recent = context.get('recent_user_messages', [])[-2:]
        terms = set(re.findall(r'\w+', utterance.lower()))
        recent_terms = set(re.findall(r'\w+', ' '.join(recent).lower()))
        def score(value):
            words = set(re.findall(r'\w+', json.dumps(value, ensure_ascii=False).lower()))
            return len(words & terms) * 10 + len(words & recent_terms)
        essential = {k: context[k] for k in ('speaker', 'addressee') if k in context}
        entries = []
        for key in ('reference_scopes', 'recent_user_messages', 'facts', 'negative_facts',
                    'entities', 'concepts', 'symmetric_relations', 'procedures', 'skills',
                    'world_objects', 'taught_words'):
            value = recent if key == 'recent_user_messages' else context.get(key, [])
            rows = list(value.items()) if isinstance(value, dict) else list(value)
            for index, row in enumerate(rows):
                relevance = score(row)
                if key == 'recent_user_messages': relevance += 5 + index
                if key == 'reference_scopes': relevance += 4
                entries.append((relevance, key, row, isinstance(value, dict)))
        entries.sort(key=lambda row: row[0], reverse=True)
        retained = []
        # A small initial cap keeps tokenization cheap; the real model tokenizer
        # below is the final authority, including the model's chat template.
        for row in entries:
            if len(json.dumps(retained, ensure_ascii=False)) + len(json.dumps(row, ensure_ascii=False)) <= 2400:
                retained.append(row)
        initial_context = list(retained)
        while True:
            vocabulary = dict(essential)
            for _, key, row, mapping in retained:
                if mapping: vocabulary.setdefault(key, {})[row[0]] = row[1]
                else: vocabulary.setdefault(key, []).append(row)
            # Relevance sorting must not reverse the conversation chronology.
            if 'recent_user_messages' in vocabulary:
                vocabulary['recent_user_messages'] = [v for v in recent if v in vocabulary['recent_user_messages']]
            messages = [{'role':'system', 'content':instructions + '\nVocabulary: ' + json.dumps(vocabulary, ensure_ascii=False, separators=(',', ':'))},
                        {'role':'user', 'content':utterance}]
            prompt = self._request('/apply-template', {'messages':messages, 'chat_template_kwargs':{'enable_thinking':False}})['prompt']
            tokens = self._request('/tokenize', {'content':prompt, 'add_special':False, 'parse_special':True})['tokens']
            if len(tokens) + output_tokens + 64 <= window:
                self.last_prompt_tokens = len(tokens)
                return messages
            if not retained:
                if instructions.startswith(INSTRUCTIONS) and INSTRUCTIONS != LOCAL_INSTRUCTIONS:
                    instructions = LOCAL_INSTRUCTIONS + instructions[len(INSTRUCTIONS):]
                    retained = list(initial_context)
                    continue
                raise ValueError('That message is too large for Gemma’s current context. Please split it into smaller parts; nothing was learned.')
            retained = retained[:len(retained)//2]

    def translate(self, utterance, context):
        # Put the current utterance last; context is vocabulary, not instructions
        # or additional claims to execute.
        question = is_question(utterance)
        math_lesson = not question and bool(re.search(r"\b(number|expression|anything)\b", utterance, re.I) and
                                           re.search(r"\b(adding|multiplying|subtracting|dividing|power|equals|unchanged)\b", utterance, re.I))
        instructions = INSTRUCTIONS
        if context.get('_request_policy'):
            instructions += '\n' + context['_request_policy']
        schema = copy.deepcopy(SCHEMA)
        if math_lesson:
            schema["properties"]["operations"]["items"]["properties"]["op"]["enum"] = ["teach_math", "clarify"]
            instructions = ("Translate the user's explicit mathematical lesson into one rewrite rule. "
                            "Return JSON operations. Each operation has op, subject, relation, object, negative, conditions, text. "
                            "For teach_math: text is ONLY the LEFT symbolic expression; object is ONLY the RIGHT symbolic expression. "
                            "subject and relation empty; negative false; conditions empty array. "
                            "Use x,y as placeholders; operators + - * / ^. No prose in expressions. "
                            "Example: Adding zero to a number leaves it unchanged -> text: x + 0, object: x. "
                            "Example: Multiplying a number by one gives that number -> text: x * 1, object: x. "
                            "Do not invent additional laws. If conditional or ambiguous, use clarify with text explaining what is missing. "
                            "No evaluation, no answer, just translate the supplied rule.")
            context = {}
        if question:
            schema["properties"]["operations"]["items"]["properties"]["op"]["enum"] = sorted(READ_OPERATIONS)
            schema["properties"]["operations"]["items"]["properties"]["conditions"]["maxItems"] = 0
        return self._translate_json(utterance, context, instructions, schema)

    def translate_sequence(self, utterance, context, instructions, schema):
        return self._translate_json(utterance, context, instructions, schema)

    def _translate_json(self, utterance, context, instructions, schema):
        window = self._request('/props').get('default_generation_settings', {}).get('n_ctx')
        if type(window) is not int or window <= 0:
            raise ValueError('Cannot determine Gemma’s context capacity. Your message has not been applied.')
        request = {
            "model": self.model, "stream": False, "temperature": 0,
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_object", "schema": schema},
        }
        for output_tokens in (1200, 1800):
            request['max_tokens'] = output_tokens
            request['messages'] = self._fit_messages(utterance, context, instructions, output_tokens, window)
            data = self._request('/v1/chat/completions', request)
            choices = data.get('choices', [])
            self.last_translation = {'usage':data.get('usage'), 'finish_reason':choices[0].get('finish_reason') if len(choices)==1 else None,
                                     'prompt_tokens':self.last_prompt_tokens, 'reserved_output_tokens':output_tokens}
            if len(choices) != 1:
                raise ValueError('Gemma returned an unexpected number of translations. Your message has not been applied.')
            if choices[0].get('finish_reason') == 'length':
                continue  # Retry translation only; partial operations never execute.
            if choices[0].get('finish_reason') != 'stop':
                raise ValueError('Gemma stopped before completing the translation. Your message has not been applied; please retry.')
            content = choices[0].get('message', {}).get('content')
            if not isinstance(content, str):
                raise ValueError('Gemma returned no translation. Your message has not been applied.')
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                raise ValueError('Gemma returned an incomplete translation. Your message has not been applied; please retry.') from None
        raise ValueError('Gemma could not finish translating this message after retrying. Please split it into smaller parts; nothing was learned.')


class Session:
    def __init__(self, store=None):
        self.store = store if store is not None else foundation.new_learning_store()
        self.settings = self.store.map('session.settings')
        self.core = Knowledge(self.store)
        self.sudoku = SudokuBoard()
        world = ToyWorld()
        self.explorer = Explorer(world.observe(), world.actions, self.store)
        self.sensors = SensorHub(self.store)
        self.sensors.register("toy-world", ToyWorldSensor(world))
        self.sensors.register_surface("sudoku-canvas", CanvasSurface(
            lambda: self.sudoku.perception(), self._sudoku_canvas_action))
        self.canvas = BoardCanvas(lambda: self.sudoku)
        self.sensors.register_surface("canvas", self.canvas)
        self.workspace = WorkspaceSurface(self.store)
        self.sensors.register_surface('workspace', self.workspace)
        self.sensors.register_surface('clock', ClockSurface())
        self.sensors.register_surface('dialogue', DialogueSurface(self.store))
        from rendered_web_surface import RenderedWebSurface
        self.web = RenderedWebSurface(self.store)
        self.sensors.register_surface('web', self.web)
        basic_ports = SensorHub(self.store)
        for name in ('canvas', 'workspace', 'clock', 'dialogue', 'web'):
            basic_ports.register_surface(name, self.sensors.surfaces[name])
        self.skills = SkillSystem(self.store, basic_ports)
        self.language_records = self.store.sequence('experience.language')
        # Routing history is separate from capability: forgetting the graph
        # must report a missing lesson instead of falling back to legacy rules.
        self._restore_canvas()

    @property
    def speaker(self):
        return self.settings.get('speaker')

    @speaker.setter
    def speaker(self, value):
        self.settings['speaker'] = value

    @property
    def assistant_name(self):
        return self.settings.get('assistant_name', 'Seed')

    @assistant_name.setter
    def assistant_name(self, value):
        self.settings['assistant_name'] = value

    @property
    def algebra_taught(self):
        return self.settings.get('algebra_taught', False)

    @algebra_taught.setter
    def algebra_taught(self, value):
        self.settings['algebra_taught'] = value

    def _restore_canvas(self):
        canvas = self.store.map('environment.state').get('canvas')
        if canvas is not None:
            self.sudoku.reset(canvas['grid'])
            self.sudoku.givens = SudokuBoard(canvas['givens']).grid
            self.sudoku.selected = copy.deepcopy(canvas.get('selected'))
            self.sudoku.recent = copy.deepcopy(canvas.get('recent'))
            self.canvas.pointer = copy.deepcopy(canvas.get('pointer'))
            self.canvas.feedback = copy.deepcopy(canvas.get('feedback'))

    def _sudoku_canvas_action(self, action, arguments):
        """Environment adapter for the reusable canvas sensor boundary."""
        if action == "select":
            return self.sudoku.select(int(arguments.get("row")), int(arguments.get("col")))
        if action == "place":
            return self.sudoku.place(int(arguments.get("row")), int(arguments.get("col")), int(arguments.get("value")))
        if action == "reset":
            self.sudoku.reset()
            return self.sudoku.perception()
        if action == "randomize":
            return self.sudoku.randomize(seed=arguments.get("seed"), blanks=int(arguments.get("blanks", 45)))
        raise ValueError("Unknown Sudoku canvas action.")

    def perceive(self, source):
        return self.sensors.perceive(source)

    def act_sensor(self, source, action, arguments=None):
        return self.sensors.act(source, action, arguments)

    def context(self):
        return {"speaker": self.speaker, "addressee": self.assistant_name,
                '_request_policy': self.core.invoke('natural_request_policy', None) if 'natural_request_policy' in self.core.procedures else '',
                "reference_scopes": [{k: row[k] for k in ('name','scope')} for row in self.core.invoke('meaning_policy',None).get('source_scopes',[])] if 'meaning_policy' in self.core.procedures else [],
                "dialogue_roles": {"I/me/my in user messages": self.speaker, "you/your in user messages": self.assistant_name + " (assistant)"}, "entities": sorted(self.core.entities)[:40],
                "concepts": sorted(self.core.category.objects)[:30],
                "facts": [list(f) for f in list(self.core.facts)[-24:]],
                "negative_facts": [list(f) for f in list(self.core.negatives)[-12:]],
                "definitions": {c: self.core.definition_text(c) for c in list(self.core.rules)[-5:]},
                "symmetric_relations": list(self.core.symmetric),
                "procedures": {name: entry["graph"].get("expression", "typed graph") for name, entry in self.core.procedures.items() if not entry['graph'].get('internal')},
                "skills": self.skills.catalog(),
                "recent_user_messages": [r["original"] for r in self.language_records
                                         if r.get('source') == 'user-via-language-interface'][-3:],
                "world_objects": sorted(self.explorer.observations),
                "math_lessons": list(self.core.math_lessons),
                "taught_words": dict(self.explorer.words),
                "sudoku": {"surface": "canvas", "reading": "sudoku_describe runs the taught board-reading procedure",
                           "solving": "sudoku_solve runs the taught solver"},
                "sudoku_lessons": {name: entry["description"] for name, entry in self.core.sudoku_lessons.items()},
                "capabilities": {"current_date": "Live local clock tool: today, today\'s date, current date. Never use a stored date as today."}}

    def apply(self, utterance, proposal):
        if isinstance(proposal, dict) and proposal.get('kind') == 'graph_package':
            return self.teach_graph_package(proposal['entries'], utterance)
        if isinstance(proposal, dict) and proposal.get("kind") == "graph_forget":
            return self.forget_graph(proposal["name"])
        if isinstance(proposal, dict) and proposal.get("kind") == "graph_run":
            return None  # Stored results are history; never replay device actions.
        if isinstance(proposal, dict) and proposal.get("kind") == "graph_definition":
            return self.teach_graph(proposal["name"], proposal["graph"], utterance, replace=proposal.get("replace", False))
        if isinstance(proposal, dict) and "operations" in proposal:
            return self.apply_structured(utterance, proposal)
        # Replay legacy notebooks only; current model responses use typed operations.
        if not isinstance(proposal, dict) or set(proposal) != {"kind", "content"}:
            raise ValueError("Invalid language operation.")
        kind, content = proposal["kind"], proposal["content"]
        if not isinstance(content, str) or not content.strip() or len(content) > 2000:
            raise ValueError("Invalid operation content.")
        if kind == "statement":
            parse(content)
            answer = self.core.tell(content)
            answer += " [User assertion via LLM translation; not sensor-verified.]"
        elif kind == "question":
            answer = self.core.ask(content)
        elif kind == "name":
            self.explorer.name(content)
            answer = "Learned a word for an action outcome."
        elif kind == "world_question":
            answer = "Provisional world prediction: " + self.explorer.ask(content)
        elif kind == "clarify":
            answer = content
        else:
            raise ValueError("Language operation is not allowed.")
        self.language_records.append({"source": "user-via-language-interface", "original": utterance,
                                      "translation": dict(proposal), "answer": answer})
        return answer

    @atomic_graph
    def teach_graph(self, name, graph, source="Procedure supplied through graph editor", replace=False):
        name = procedures.procedure_name(name)
        if name in self.core.procedures and not replace:
            raise ValueError("That procedure name already exists. Use a new name for this graph.")
        validate_graph(graph, self.core.procedures)
        proposed = {**self.core.procedures, name: {"graph": graph, "source": source}}
        # Other lessons may deliberately have forgotten dependencies. Restoring
        # one must remain possible without re-teaching the entire library.
        validate_graph(graph, proposed)
        self.core.procedures[name] = {"graph": copy.deepcopy(graph), "source": source}
        if name == 'algebra_solve':
            self.algebra_taught = True
        answer = f"Learned executable graph '{name}': {graph['input_type']} → {graph['output_type']}."
        self.language_records.append({"source": "user-graph-editor", "original": source,
                                      "translation": {"kind": "graph_definition", "name": name, "graph": copy.deepcopy(graph), "replace": replace},
                                      "interpretation": answer, "answer": answer})
        return answer

    @atomic_graph
    def forget_graph(self, name):
        name = procedures.procedure_name(name)
        if name not in self.core.procedures:
            raise ValueError("That procedure has not been taught.")
        del self.core.procedures[name]
        answer = "Forgot executable procedure: " + name + ". Calls to it now require teaching it again."
        self.language_records.append({"source": "user-graph-editor", "original": "Forget procedure " + name,
                                      "translation": {"kind": "graph_forget", "name": name},
                                      "answer": answer, "interpretation": answer})
        return answer

    @atomic_graph
    def teach_graph_package(self, entries, source='Explicit full Sudoku curriculum'):
        if not isinstance(entries, dict) or not 1 <= len(entries) <= 200:
            raise ValueError('A lesson package needs one to 200 named procedures.')
        proposed = {**self.core.procedures, **copy.deepcopy(entries)}
        for name, entry in entries.items():
            if procedures.procedure_name(name) != name or not isinstance(entry, dict):
                raise ValueError('Invalid named lesson.')
            validate_graph(entry.get('graph'), proposed)
        self.core.procedures.update(copy.deepcopy(entries))
        if 'algebra_solve' in entries:
            self.algebra_taught = True
        answer = f'Taught {len(entries)} executable lessons: ' + ', '.join(entries) + '.'
        self.language_records.append({'source': 'teacher-graph-package', 'original': source,
            'translation': {'kind': 'graph_package', 'entries': copy.deepcopy(entries)},
            'answer': answer, 'interpretation': answer})
        return answer

    def teach_sudoku_suite(self):
        # Read the curriculum only in response to explicit teaching, never on
        # solve, check, unrelated learning, or startup after a lesson was removed.
        entries = json.loads((Path(__file__).parent / 'curriculum/sudoku.json').read_text())
        return self.teach_graph_package(entries)

    def teach_algebra_suite(self):
        entries = json.loads((Path(__file__).parent / 'curriculum/algebra.json').read_text())
        return self.teach_graph_package(entries, 'Explicit general algebra curriculum')

    def teach_foundations(self):
        answer = self.teach_graph_package(foundation.curriculum(), 'Explicit teaching of general reasoning and interface-use methods')
        self.core.rebuild()
        return answer

    def teach_conversation(self):
        entries = json.loads((Path(__file__).parent / 'curriculum/conversation.json').read_text())
        return self.teach_graph_package(entries, 'Explicit question, wait and introductory algebra teaching policies')

    def run_skill(self, name, argument=None, original=None):
        run = self.skills.run(procedures.procedure_name(name), argument)
        answer = run['result']['text'] if isinstance(run['result'],dict) and isinstance(run['result'].get('text'),str) else 'Executed taught skill ' + name + ':\n' + json.dumps(run['result'], ensure_ascii=False)
        self.language_records.append({'source': 'user-skill-request', 'original': original or 'Run skill ' + name,
            'translation': {'kind': 'graph_run', 'name': name}, 'answer': answer,
            'interpretation': 'Execute a stored graph through the generic skill interface', 'tool_runs': [run]})
        return answer, run

    def achieve_goal(self, request, original=None):
        run = self.skills.achieve(request)
        if run['status'] == 'missing_knowledge':
            answer = 'I could not find a plan using the taught skill contracts within the taught search limits.'
        else:
            answer = 'Plan: ' + (' → '.join(run['plan']['plan']) or 'No transformation needed')
            answer += '\nResult: ' + json.dumps(run.get('result'), ensure_ascii=False)
            answer += '\n' + {'verified': 'Passed the taught outcome check.', 'check_failed': 'The taught outcome check failed.',
                                'executed_unverified': 'Executed; supply a taught check to verify the outcome.'}[run['status']]
        self.language_records.append({'source': 'user-goal-request', 'original': original or 'Goal: ' + json.dumps(request),
            'translation': {'kind': 'graph_run', 'name': 'plan_search'}, 'answer': answer,
            'interpretation': 'Plan and execute using taught programs; keep goal, plan and outcome in graph memory', 'tool_runs': [run]})
        return answer, run

    def run_sensor_graph(self, name, argument=None, library=None):
        library = self.core.procedures if library is None else library
        name = procedures.procedure_name(name)
        if name not in library:
            raise ValueError("Teach that procedure before running it: " + name)
        graph = library[name]["graph"]
        if graph["input_type"] != "Data" or graph["output_type"] != "Data":
            raise ValueError("The sensory runner accepts Data → Data procedures.")
        # Only the basic canvas device is available to this execution context.
        # Rich Sudoku candidates/constraints cannot leak through legacy adapters.
        hub = SensorHub()
        hub.register_surface("canvas", self.canvas)
        start = len(hub.events)
        try:
            result, trace = execute_graph(graph, argument, library, limit=3000000, sensors=hub)
            rendered = str(result) if not isinstance(result, (dict, list)) else json.dumps(result)
            answer = "Executed taught procedure " + name + ".\n" + rendered[:2000]
        except ValueError as error:
            result, trace = None, getattr(error, 'graph_trace', [])
            answer = "Procedure stopped: " + str(error)
            if len(hub.events) > start:
                answer += " Completed device actions remain in the experience history."
        finally:
            self.sensors.events.extend(hub.events)
        self.language_records.append({"source": "user-canvas-procedure", "original": "Run " + name,
                                      "translation": {"kind": "graph_run", "name": name},
                                      "answer": answer, "interpretation": "Execute stored sensory procedure",
                                      "trace": trace})
        return {"answer": answer, "result": result, "trace": trace}

    def apply_structured(self, utterance, proposal):
        operations = validate(proposal)
        if any(op['op'] in {'run_skill', 'achieve_goal'} for op in operations):
            if len(operations) != 1:
                raise ValueError('Run a skill or goal as its own request.')
            item = operations[0]
            argument = json.loads(item['text'])
            return (self.run_skill(item['subject'], argument, utterance) if item['op'] == 'run_skill'
                    else self.achieve_goal(argument, utterance))[0]
        # Stage the whole message: a bad second operation must not leave a partial correction.
        core = copy.deepcopy(self.core)
        try:
            return self._apply_structured(utterance, proposal, operations, core)
        finally:
            core.store.close()

    def _apply_structured(self, utterance, proposal, operations, core):
        before_assertions = dict(core.assertions)
        words = dict(self.explorer.words)
        speaker = self.speaker
        assistant_name = self.assistant_name
        answers, summaries, tool_runs = [], [], []
        lookup_requests = []
        for item in operations:
            taught_references = 'dialogue_resolve_operation' in core.procedures
            if taught_references:
                item = core.invoke('dialogue_resolve_operation', {
                    'operation': item,
                    'context': {'speaker': speaker, 'addressee': assistant_name}})
            kind = item["op"]
            subject, relation, obj = item["subject"], item["relation"], item["object"]
            negative = item["negative"]
            if not taught_references and subject.strip().lower() in {"you", "yourself", "assistant", "addressee"}:
                subject = assistant_name
            if not taught_references and subject.strip().lower() in {"i", "me", "myself", "speaker"}:
                if not speaker:
                    raise ValueError("What name should I remember you by?")
                subject = speaker
            elif not taught_references and speaker and subject.casefold() == speaker.casefold():
                subject = speaker
            if not taught_references and kind in {"assert", "retract", "query", "find"} and relation != "is" and obj.strip().lower() in {"you", "yourself", "assistant", "addressee"}:
                obj = assistant_name
            if not taught_references and kind in {"assert", "retract", "query", "find"} and relation != "is" and obj.strip().lower() in {"i", "me", "myself", "speaker"}:
                if not speaker:
                    raise ValueError("What name should I use for you in that relationship?")
                obj = speaker
            if kind == "teach_sudoku":
                answer = sudoku_lessons.teach(core.sudoku_lessons, item["text"], utterance)
                summary = "Store a teacher-supplied Sudoku strategy"
            elif kind == "list_sudoku":
                answer = "\n".join(name + ": " + entry["description"] for name, entry in core.sudoku_lessons.items()) or "No Sudoku strategies have been taught yet."
                summary = "Recall Sudoku strategies"
            elif kind == "sudoku_solve":
                run = self.run_sensor_graph('sudoku_observe_solve', library=core.procedures)
                answer = run['answer']
                if isinstance(run['result'], dict) and run['result'].get('correct'):
                    answer = 'Solved Sudoku by executing the taught graph programs and canvas controls.'
                    steps = [step['operation'] + ' → ' + step['result'] for step in run['trace']
                             if step['operation'] not in {'observe', 'act', 'expand_candidates'}]
                    answer += '\nTaught reasoning trace:\n' + '\n'.join(steps[:120])
                tool_runs.append(run)
                summary = 'Execute stored Sudoku observe / solve / input / check programs'
            elif kind == "sudoku_describe":
                run = self.run_sensor_graph('sudoku_observe_read', library=core.procedures)
                tool_runs.append(run)
                answer = run['answer']
                summary = 'Execute taught canvas reading and symbol interpretation'
            elif kind == "sudoku_candidates":
                try:
                    row, col = int(subject), int(relation)
                except ValueError:
                    raise ValueError("Give a Sudoku row and column from 0 to 8.") from None
                if not 0 <= row < 9 or not 0 <= col < 9:
                    raise ValueError('Give a Sudoku row and column from 0 to 8.')
                run = self.run_sensor_graph('sudoku_query_candidates', {'row': row, 'col': col}, core.procedures)
                tool_runs.append(run)
                answer = run['answer']
                summary = f'Execute taught candidate query for ({row},{col})'
            elif kind == "separate_person_city":
                result = core.separate_person_city(subject, utterance)
                answer = result['text']
                summary = 'Saved separate person and city references: ' + subject
                tool_runs.append(core.executions['meaning_separate_person_city'])
            elif kind == "rename_assistant":
                result = core.rename_entity(assistant_name, subject, utterance)
                assistant_name = label(result['name'])
                answer = summary = result['text']
                tool_runs.append(core.executions['meaning_rename_reference'])
            elif kind == "teach_math":
                answer = math_lessons.teach(core.math_lessons, item["text"], obj, utterance)
                summary = "Store a teacher-supplied symbolic rewrite"
            elif kind == "solve_math":
                if self.algebra_taught:
                    import algebra
                    answer, run = algebra.run(item['text'], core.procedures)
                    tool_runs.append(run)
                    summary = 'Execute taught algebra procedures: ' + item['text']
                else:
                    answer = math_lessons.solve(item["text"], core.math_lessons)
                    summary = "Solve by applying taught rules: " + item["text"]
            elif kind == "rewrite_math":
                if self.algebra_taught and not re.match(r'^\s*rewrite\b', utterance, re.I):
                    import algebra
                    answer, run = algebra.run(item['text'], core.procedures, solving=False)
                    tool_runs.append(run)
                    summary = 'Normalize with taught polynomial operations: ' + item['text']
                else:
                    answer = math_lessons.rewrite(item["text"], core.math_lessons)
                    summary = "Rewrite using taught math lessons: " + item["text"]
            elif kind == "list_math":
                answer = "\n".join(name + "\nTaught by: " + entry["source"] for name, entry in core.math_lessons.items()) or "No math rewrite lessons yet."
                summary = "Recall math lessons"
            elif kind == "forget_math":
                key = math_lessons.show(math_lessons.parse(item["text"])) + " → " + math_lessons.show(math_lessons.parse(obj))
                if key not in core.math_lessons:
                    raise ValueError("I haven't learned that exact math rule.")
                del core.math_lessons[key]
                answer = summary = "Forgot math rule: " + key
            elif kind == "current_date":
                observation = core.invoke('clock_observe', None)
                answer = f"Today is {observation['date']} ({observation['timezone']}, local system clock)."
                summary = "Execute taught clock interface procedure"
                tool_runs.append({"tool": "current_date", "observation": observation})
            elif kind == "date_procedure" or (kind == "describe" and relation == "age"):
                answer, run = date_answer(core, subject, relation if kind == "date_procedure" else "age_years")
                tool_runs.append(run)
                summary = "Execute taught date procedure: " + run["procedure"]
            elif kind == "calculate":
                answer = calculate(item["text"], core.procedures)
                summary = "Execute arithmetic graph: " + item["text"]
            elif kind == "count":
                answer = count(item, core, self.explorer)
                summary = "Count " + relation + ": " + (subject + " " + obj).strip()
            elif kind in {"define_procedure", "redefine_procedure"}:
                name, graph = procedures.define(core.procedures, subject, item["text"], utterance, replace=kind == "redefine_procedure")
                answer = f"Learned executable procedure: {name}(x) = {graph['expression']}.\nStored as {len(graph['nodes'])} typed graph nodes."
                summary = name + ": Number → Number"
            elif kind == "compose_procedure":
                name, first, second = map(procedures.procedure_name, (subject, relation, obj))
                if name in core.procedures or first not in core.procedures or second not in core.procedures:
                    raise ValueError("Use a new procedure name and two already-learned procedures.")
                graph = compose(core.procedures[first]["graph"], core.procedures[second]["graph"], core.procedures)
                graph["expression"] = f"{second}({first}(x))"
                core.procedures[name] = {"graph": graph, "source": utterance}
                answer = summary = f"Learned {name}: run {first}, then {second}. This stores a snapshot of their composed graphs."
            elif kind == "run_procedure":
                name = procedures.procedure_name(subject)
                if name not in core.procedures:
                    raise ValueError(f"I haven't learned '{name}' yet. What steps should it perform?")
                argument, _ = procedures.execute(procedures.compile_graph(item["text"], library=core.procedures), library=core.procedures)
                result, trace = procedures.execute(core.procedures[name]["graph"], argument, core.procedures)
                answer = f"{name}({number_text(argument)}) = {number_text(result)}\nSteps:\n" + "\n".join(trace)
                summary = "Execute learned graph: " + name
            elif kind == "assert":
                if not negative:
                    replaced = core.invoke('memory_superseded', {
                        'assertions': [{'fact': list(f), 'negative': n} for f,n in core.assertions],
                        'new': {'subject': subject, 'relation': relation, 'object': obj}})
                    for old in replaced:
                        del core.assertions[(tuple(old), False)]
                answer = core.assert_fact(subject, relation, obj, negative, utterance)
                summary = fact_text(core.triple(subject, relation, obj), negative)
            elif kind == "retract":
                answer = core.retract(subject, relation, obj, negative)
                summary = "Remove: " + fact_text(core.triple(subject, relation, obj), negative)
            elif kind == "subtype":
                sub, parent = label(subject).lower(), label(obj).lower()
                core.subtypes[(sub, parent)] = utterance
                core.rebuild()
                answer = summary = f"Every {sub} is a {parent}."
            elif kind in {"symmetric", "forget_symmetry"}:
                answer = summary = core.symmetry(relation, utterance, remove=kind == "forget_symmetry")
            elif kind in {"define", "redefine"}:
                conditions = list(item["conditions"])
                if obj:
                    if relation != "is":
                        raise ValueError("What broader type does that concept belong to?")
                    base = {"relation": "is", "object": obj, "target_type": False}
                    if base not in conditions:
                        conditions.insert(0, base)
                answer = core.define(subject, conditions, utterance, replace=kind == "redefine")
                summary = core.definition_text(subject.strip().lower())
            elif kind == "find":
                answer = core.find(relation, obj, subject)
                summary = "Find subjects: ? " + relation + " " + obj + (" / type " + subject if subject else "")
            elif kind == "query":
                answer = core.query(subject, relation, obj, negative)
                if 'knowledge_lookup_response' in core.procedures:
                    argument = {**core.evidence(), 'fact': list(core.triple(subject, relation, obj)),
                                'negative': negative, 'answer': answer}
                    lookup_requests.append((len(answers), argument))
                summary = "Check: " + fact_text(core.triple(subject, relation, obj), negative)
            elif kind == "describe":
                # 'What is X?' is a description request, not an is-only filter.
                relation = "" if relation == "is" else relation
                procedure_key = subject.strip().lower().replace(" ", "_")
                answer = (procedures.describe(procedure_key, core.procedures[procedure_key])
                          if procedure_key in core.procedures else core.describe(subject, relation))
                if core.entity(subject).casefold() == assistant_name.casefold() and not relation:
                    if 'dialogue_self_description' in core.procedures:
                        answer = core.invoke('dialogue_self_description', {
                            'name': assistant_name, 'description': answer})
                    else:
                        answer = "I am " + assistant_name + ".\n" + answer
                summary = f"Recall {core.entity(subject)}" + (f" / {relation}" if relation else "")
                if procedure_key not in core.procedures:
                    run = core.executions.get('knowledge_describe', {})
                    result = run.get('result', {})
                    if run.get('input', {}).get('subject') == core.entity(subject) and isinstance(result, dict) and result.get('method'):
                        tool_runs.append(run)
                        summary = 'Execute taught answer method: ' + result['method']
            elif kind == "identify":
                speaker = label(subject)
                answer = f"I'll remember you as {speaker}."
                summary = "Your name: " + speaker
            elif kind == "name":
                if relation not in self.explorer.actions:
                    raise ValueError("Which toy action should that word refer to: rolling or floating?")
                word = label(subject).lower()
                words[word] = relation
                answer = summary = f"A {word} is something that succeeds at the {relation} experiment."
            elif kind == "world_query":
                entity = next((e for e in self.explorer.observations if e.casefold() == subject.casefold()), None)
                word = obj.strip().lower()
                if entity is None or word not in words:
                    raise ValueError("Which visible object and taught action-word should I check?")
                answer = "Provisional world prediction: " + self.explorer.predict(words[word], entity)
                summary = f"Check whether {entity} is a {word}."
            else:
                answer = (core.invoke('dialogue_clarification_response', item['text'])
                          if 'dialogue_clarification_response' in core.procedures else
                          "I couldn't resolve that meaning into a supported operation, so I haven't changed memory.")
                summary = "Clarification — memory unchanged."
            answers.append(answer)
            summaries.append(summary)
        with self.store.transaction():
            for index, argument in lookup_requests:
                result, trace = foundation.run(core.procedures, 'knowledge_lookup_response', argument, self.sensors)
                answers[index] = result['text']
                tool_runs.append({'procedure': 'knowledge_lookup_response', 'trace': trace, 'result': result})
            answer = "\n".join(answers)
            self.core.adopt(core)
            if dict(core.assertions) != before_assertions and 'learning_cycle' in self.core.procedures:
                changed = [list(fact) for (fact, negative), source in core.assertions.items()
                           if before_assertions.get((fact, negative)) != source]
                result, trace = foundation.run(self.core.procedures, 'learning_cycle',
                                              {'changed': changed, 'ask': True}, self.sensors)
                tool_runs.append({'procedure': 'learning_cycle', 'trace': trace, 'result': result})
                if result.get('text'):
                    answer += '\n\n' + result['text']
            self.speaker, self.assistant_name, self.explorer.words = speaker, assistant_name, words
            self.language_records.append({"source": "user-via-language-interface", "original": utterance,
                                      "translation": copy.deepcopy(proposal), "interpretation": "\n".join(summaries),
                                      "answer": answer, "tool_runs": copy.deepcopy(tool_runs)})
        return answer

    def chat(self, utterance, translator):
        # A generic mode boundary also covers sequence continuations that use
        # the translator directly. It contains no language recognition rules.
        if self.store.map('session.language').get('mode', 'hybrid') == 'symbolic':
            session = self
            class GraphOnlyLanguage:
                model = 'taught-grammar'
                def translate(self, text, context):
                    return session.core.invoke('language_unknown', {'text': text})
            translator = GraphOnlyLanguage()
        import behavior
        start = len(self.language_records)
        try:
            # Active dialogue continuations retain priority over new hooks.
            proposal = (None if self.store.map('interaction.state').get('waiting') else
                        behavior.interpret(self, utterance))
            if proposal is not None:
                if proposal.get('kind') != 'graph_run':
                    raise ValueError('A behavior interpreter must return a graph invocation.')
                answer = self.run_skill(proposal['name'], proposal.get('argument'), utterance)[0]
            else:
                answer = self._chat(utterance, translator)
        except (ValueError, OSError) as error:
            behavior.after_turn(self, utterance, '', {}, str(error))
            raise
        record = self.language_records[-1] if len(self.language_records) > start else {}
        return behavior.after_turn(self, utterance, answer, record)

    def _chat(self, utterance, translator):
        pending = self.store.map('interaction.state').get('waiting')
        if pending is not None:
            # The host only delivers input to the continuation selected by the
            # stored program. The continuation decides how to interpret it.
            answer, run = self.run_skill(pending['resume'], {'state':pending['state'],'input':utterance}, utterance)
            current = self.store.map('interaction.state').get('waiting')
            if current is not None and current['id']==pending['id']:
                del self.store.map('interaction.state')['waiting']
            # A stored continuation can explicitly return text to the language
            # interface. This adapter assigns no domain meaning to that text.
            result = run.get('result')
            if isinstance(result, dict) and isinstance(result.get('sequence_input'), str):
                from sequences import handle
                return handle(self, result['sequence_input'], translator, force=True)
            if isinstance(result, dict) and isinstance(result.get('language_input'), str):
                return self.chat(result['language_input'], translator)
            return answer
        if 'task_detect' in self.core.procedures:
            task_request = foundation.run(self.core.procedures, 'task_detect', utterance)[0]
            if task_request is not None:
                from persistent_tasks import create
                return create(self, task_request, translator)
        from sequences import handle as sequence_request
        sequence_answer = sequence_request(self, utterance, translator)
        if sequence_answer is not None:
            return sequence_answer
        tutorial = re.fullmatch(r'\s*(?:teach me|explain)\s+algebra[.!?]?\s*',utterance,re.I)
        if tutorial:
            return self.run_skill('tutor_start', {'topic':'algebra'},utterance)[0]
        if utterance.strip().rstrip('.!?').casefold() in {'teach me javascript','teach me programming','explain programming','explain javascript'}:
            _, run = self.run_skill('programming_overview', None, utterance)
            answer = '\n'.join(row['concept'] + ': ' + row['meaning'] for row in run['result'])
            record = dict(self.language_records[-1]); record['answer'] = answer
            self.language_records[-1] = record
            return answer
        from javascript import handle as javascript_request
        programming_start = len(self.language_records)
        javascript_answer = javascript_request(self, utterance)
        if javascript_answer is not None:
            if len(self.language_records) > programming_start:
                record = dict(self.language_records[-1]); record['answer'] = javascript_answer
                self.language_records[-1] = record
            else:
                self.language_records.append({'source':'programming-interface','original':utterance,
                    'translation':{'kind':'graph_run','name':'js_choose_program'},'answer':javascript_answer})
            return javascript_answer
        if utterance.strip().rstrip('.!?').casefold() == 'teach conversation methods':
            return self.teach_conversation()
        if utterance.strip().rstrip('.!?').casefold() in {'look for patterns', 'review patterns', 'what patterns have you noticed'}:
            return self.run_skill('learning_cycle', {'changed': None, 'ask': True}, utterance)[0]
        if utterance.strip().rstrip('.!?').casefold() in {'teach foundations', 'teach foundational methods'}:
            return self.teach_foundations()
        run = re.fullmatch(r'\s*run skill\s+([a-zA-Z][a-zA-Z0-9_]*)\s*:\s*(.+)', utterance, re.S | re.I)
        if run:
            return self.run_skill(run[1], json.loads(run[2]), utterance)[0]
        goal = re.fullmatch(r'\s*goal\s*:\s*(\{.*\})\s*', utterance, re.S | re.I)
        if goal:
            return self.achieve_goal(json.loads(goal[1]), utterance)[0]
        if utterance.strip().rstrip('.!?').casefold() in {'teach algebra', 'teach algebra curriculum', 'teach general algebra'}:
            return self.teach_algebra_suite()
        identity = None
        question = utterance.strip().rstrip(".!?").lower().replace("’", "'")
        rename = re.fullmatch(r"your (?:new )?name is(?: now)? (.+)", utterance.strip().rstrip(".!?"), re.I)
        if rename:
            identity = {"operations": [operation("rename_assistant", rename[1])]}
        elif question in {"what do you see on the sudoku board", "read the sudoku board", "what is on the sudoku board"}:
            identity = {"operations": [operation("sudoku_describe")]}
        elif question in {"who are you", "what are you", "what is your name", "what's your name", "tell me about yourself"}:
            identity = {"operations": [operation("describe", "assistant")]}
        elif question in {"who am i", "what is my name", "what's my name", "tell me about myself"}:
            identity = {"operations": [operation("describe", "speaker")]}
        with self.store.transaction():
            taught = (self.core.invoke('language_interpret', {'text':utterance, 'speaker':self.speaker, 'addressee':self.assistant_name})
                      if 'language_interpret' in self.core.procedures else None)
            correction = (self.core.invoke('meaning_correction_interpret', {'text': utterance})
                          if 'meaning_correction_interpret' in self.core.procedures else None)
            algebra_request = (self.core.invoke('algebra_request_interpret', utterance)
                               if 'algebra_request_interpret' in self.core.procedures else None)
            grammar = (foundation.run(self.core.procedures, 'language_parse', {'text': utterance}, self.sensors)[0]
                       if 'language_parse' in self.core.procedures else None)
        proposal = algebra_request or correction or taught or identity or grammar or sudoku_lessons.direct(utterance) or math_lessons.direct_math_lesson(utterance) or direct_location(utterance, self.core.entities) or direct_date(utterance, self.core.procedures) or direct_math(utterance) or direct_procedure(utterance, self.core.procedures)
        if proposal is None:
            if self.store.map('session.language').get('mode', 'hybrid') == 'symbolic':
                return self.run_skill('language_unknown_response', {'text': utterance}, utterance)[0]
            proposal = translator.translate(utterance, self.context())
        try:
            # Legacy adapters can still be replayed via apply, but live translations
            # must use the new schema and cannot send raw sentences for execution.
            operations = validate(proposal)
            if any(item['op'] == 'plan_task' for item in operations):
                if len(operations) != 1:
                    raise ValueError('Please clarify whether this is one task or separate requests.')
                from persistent_tasks import create
                return create(self, utterance, translator)
            if is_question(utterance) and any(item["op"] not in READ_OPERATIONS for item in operations):
                raise ValueError("I understood that as a question, so I haven't changed memory. What would you like me to check?")
            return self.apply_structured(utterance, proposal)
        except ValueError as error:
            # Report the actual failed operation's error, not a model-authored
            # success statement. Staged changes have already been rolled back.
            answer = str(error)
            self.language_records.append({'source': 'user-via-language-interface',
                'original': utterance, 'translation': {'operations': [operation('clarify', text=answer)]},
                'interpretation': 'Clarification — memory unchanged.', 'answer': answer})
            return answer

    def explore(self):
        choice = self.explorer.choose()
        if choice is None:
            return "No distinguishing experiment remains."
        action, entity = choice
        return self.sensors.experiment("toy-world", action, entity, self.explorer)

    def save(self, path):
        self.store.map('environment.state')['canvas'] = {
            'grid': self.sudoku.grid, 'givens': self.sudoku.givens,
            'selected': self.sudoku.selected, 'recent': self.sudoku.recent,
            'pointer': self.canvas.pointer, 'feedback': self.canvas.feedback}
        return self.store.save(path)

    @classmethod
    def load(cls, path):
        database = database_path(path)
        if database.exists():
            # The graph is authoritative. Never replay history or load a static
            # curriculum to fill gaps in an existing database.
            return cls(GraphStore(database))
        session = cls()
        if Path(path).exists():
            data = json.loads(Path(path).read_text())
            for event in data["sensors"]:
                if event.get("source") == "toy-world":
                    session.explorer.record(event["action"], event["entity"], event["outcome"])
                session.sensors.events.append(event)
            for record in data["language"]:
                proposal = record["translation"]
                if "operations" in proposal:
                    # Queries already have historical answers and observations.
                    # Replay only writes; never re-read today's clock on load.
                    writes = [item for item in proposal["operations"] if item["op"] not in READ_OPERATIONS]
                    if writes:
                        session.apply(record["original"], {"operations": writes})
                else:
                    session.apply(record["original"], proposal)
                if "operations" not in record["translation"] and record["original"].strip().rstrip(".").lower().startswith("i am "):
                    name = record["original"].strip().rstrip(".")[5:]
                    if name in session.core.entities:
                        session.speaker = name
            # Keep original historical answers, which can differ from today's beliefs.
            session.language_records.replace(data["language"])
            if 'canvas' in data:
                canvas = data['canvas']
                session.sudoku.reset(canvas['grid'])
                session.sudoku.givens = SudokuBoard(canvas['givens']).grid
                session.sudoku.selected = canvas.get('selected')
                session.sudoku.recent = canvas.get('recent')
            # Old notebooks saved the board but omitted the device cursor. Its
            # last attributed canvas observation preserves that device state.
            for event in reversed(data['sensors']):
                payload = event.get('payload', {})
                if event.get('source') == 'canvas' and isinstance(payload, dict) and payload.get('format') == 'canvas.scene.v1':
                    session.canvas.pointer = copy.deepcopy(payload.get('pointer'))
                    session.canvas.feedback = copy.deepcopy(payload.get('feedback'))
                    break
            session.settings['migration'] = {'source': str(Path(path).resolve()), 'format': 'legacy-notebook-v1'}
            session.save(path)
        return session


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("llamacpp", "ollama", "openai"), default="llamacpp")
    parser.add_argument("--model", help="Exact served model ID; discovers a single served model if omitted")
    parser.add_argument("--base-url", help="Local server root URL; defaults to llama.cpp port 8080")
    parser.add_argument("--memory", type=Path, default=Path("interface-memory.json"))
    parser.add_argument("--demo", action="store_true", help="Offline sensor + fixed translation demo; no LLM call")
    args = parser.parse_args()
    if args.demo:
        session = Session()
        for _ in range(10):
            print(session.explore())
        print(session.apply("Let's call things that roll rollers.",
                            {"kind": "name", "content": "Call things that roll roller."}))
        print(session.apply("Would Amber be one?", {"kind": "world_question", "content": "Is Amber a roller?"}))
        print("Offline demonstration: translations above are fixed examples, not LLM output.")
        return
    try:
        if args.provider == "llamacpp":
            translator = LlamaCppLanguage(args.model, args.base_url or "http://127.0.0.1:8080")
        elif args.provider == "ollama":
            translator = OllamaLanguage(args.model, args.base_url or "http://127.0.0.1:11434")
        else:
            translator = OpenAILanguage(args.model or os.environ.get("OPENAI_MODEL"))
        session = Session.load(args.memory)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")
    print("Language interface. /explore runs one toy experiment; /beliefs inspects rules; /quit exits.")
    print(f"Language model: {translator.model} via {args.provider}.")
    print("Utterances and vocabulary go to the selected server. Statements are stored as user assertions.")
    while True:
        try:
            utterance = input("> ").strip()
            if utterance == "/quit":
                break
            if not utterance:
                continue
            if utterance == "/explore":
                print(session.explore())
            elif utterance == "/beliefs":
                print(session.explorer.report())
            else:
                print(session.chat(utterance, translator))
                print("Interpreted as:", session.language_records[-1].get("interpretation", ""))
            session.save(args.memory)
        except (ValueError, OSError) as error:
            print(error)
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    main()
