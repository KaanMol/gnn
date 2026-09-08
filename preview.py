"""Local teaching preview using the existing Goud desktop Gemma runtime."""
import argparse
import json
import threading
from uuid import uuid4
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, urlencode

from goud_runtime import GoudRuntime
from interface import LlamaCppLanguage, Session
from knowledge import fact_text
from graph_view import snapshot
from graph_store import plain, database_path
from sudoku import SudokuBoard
import sudoku_lessons


ROOT = Path(__file__).resolve().parent


def record_url(namespace, key):
    return '/api/record?' + urlencode({'namespace': namespace, 'key': json.dumps(key)})


def trace_preview(trace):
    """Small visible trace; the complete immutable evidence remains accessible."""
    fields = ('node', 'path', 'operation', 'surface', 'action', 'event_id')
    return [{**{key: step[key] for key in fields if key in step},
             'result': str(step.get('result', ''))[:500]} for step in trace]


def language_preview(records):
    rows = list(records)
    result = []
    for index, record in enumerate(rows):
        row = {key: record[key] for key in ('source', 'original', 'answer', 'interpretation') if key in record}
        for field in ('original', 'answer', 'interpretation'):
            if isinstance(row.get(field), str) and len(row[field]) > 6000:
                row[field] = row[field][:6000] + '\n… Open the full stored record to read the rest.'
                row['truncated'] = True
        translation = record.get('translation', {})
        row['translation'] = {key: translation[key] for key in ('kind', 'content') if key in translation}
        row['record_url'] = record_url('experience.language', index)
        # The graph viewer displays recent executions. Older traces and all
        # teaching payloads are available on demand instead of on every reply.
        if index >= len(rows) - 20:
            row['trace'] = trace_preview(record.get('trace', []))
            row['tool_runs'] = [{'procedure': run.get('procedure'), 'trace': trace_preview(run.get('trace', [])),
                                 'record_url': row['record_url']} for run in record.get('tool_runs', [])]
        result.append(row)
    return result


def run_preview(key, record):
    return {**{name: record[name] for name in ('procedure', 'status', 'error') if name in record},
            'trace': trace_preview(record.get('trace', [])), 'record_url': record_url('skills.runs', key)}


class Application:
    def __init__(self, translator, memory):
        self.translator = translator
        self.memory = memory
        self.session = Session.load(memory)
        startup = self.session.store.map('session.behavior').get('startup')
        if startup:
            import foundation
            try:
                foundation.run(self.session.core.procedures, startup, None, self.session.sensors)
            except (ValueError, KeyError, OSError) as error:
                self.session.store.map('session.behavior')['last_error'] = str(error)
        self.lock = threading.RLock()
        self.last_check = None
        self._state_views = {}
        self._last_view = None

    def state(self, since=None):
        with self.lock:
            explorer = self.session.explorer
            report = explorer.report().splitlines()
            snapshot = plain({"model": self.translator.model, "connected": True,
                    "storage": {"kind": "graph-database", "path": str(database_path(self.memory).resolve())},
                    "language": language_preview(self.session.language_records),
                    "experiments": explorer.episodes,
                    "facts": [list(f) for f in sorted(self.session.core.facts)],
                    "memory_items": (["Your name: " + self.session.speaker] if self.session.speaker else [])
                    + [fact_text(f, negative) for f, negative in self.session.core.assertions]
                    + [f"Every {a} is a {b}." for a, b in self.session.core.subtypes]
                    + [self.session.core.definition_text(c) for c in self.session.core.rules]
                    + ["Math lesson: " + rule for rule in self.session.core.math_lessons],
                    "relationship_rules": [f"If A {r} B, then B {r} A." for r in self.session.core.symmetric],
                    "assistant_name": self.session.assistant_name,
                    "language_mode": self.session.store.map('session.language').get('mode', 'hybrid'),
                    "grammar_count": len(self.session.store.map('skills.language_patterns')),
                    "web_page": self.session.web.observation(),
                    "web_favorites": list(self.session.store.map("skills.web_favorites").values()),
                    "affect": self.session.store.map("skills.affect").get("current"),
                    "subroutines": list(self.session.store.map("skills.subroutines").values()),
                    "dashboard": list(self.session.store.map("skills.dashboard").values()),
                    "tasks": list(self.session.store.map("skills.tasks").values()),
                    "behavior_error": self.session.store.map("session.behavior").get("last_error"),
                    "sudoku": self.session.sudoku.perception(),
                    "sudoku_lessons": {name: entry["description"] for name, entry in self.session.core.sudoku_lessons.items()},
                    "sudoku_graph": self.session.core.procedures.get('sudoku_solver', {}).get('graph'),
                    "sudoku_check": self.last_check,
                    "surfaces": {"canvas": {"actions": self.session.canvas.actions,
                                             "perception": "Visible text marks, positions, lines, pointer, input feedback. Structured scene; no pixel recognition."}},
                    "sensory_events": [e for e in self.session.sensors.events if e.get("source") == "canvas"][-12:],
                    "canvas_device": {"pointer": self.session.canvas.pointer, "feedback": self.session.canvas.feedback},
                    "procedures": self.session.core.procedures,
                    "skills": self.session.skills.catalog(),
                    "runs": [run_preview(key, run) for key, run in list(self.session.store.map('skills.runs').items())[-10:]],
                    "goals": list(self.session.store.map('skills.goals').values()),
                    "reasoning_error": self.session.core.reasoning_error,
                    "hypotheses": [{**{k: row.get(k) for k in ('id','kind','label','status','decision','rule')},
                        'evidence': {**{k: row.get('evidence',{}).get(k) for k in ('support_count','unknown_count','eligible')},
                                     **{k: row.get('evidence',{}).get(k,[])[:4] for k in ('support','counterexamples','contested','unknown')}},
                        'record_url': record_url('knowledge.hypotheses', key)}
                        for key, row in self.session.core.hypotheses.items()],
                    "waiting": self.session.store.map('interaction.state').get('waiting'),
                    "words": explorer.words, "objects": explorer.observations,
                    "rules": {a: [report[i]] for i, a in enumerate(explorer.actions)},
                    "next": explorer.choose()})
            previous = self._state_views.get(since) if isinstance(since, str) else None
            if self._last_view and self._state_views[self._last_view] == snapshot:
                version = self._last_view
            else:
                version = uuid4().hex
                self._state_views[version] = snapshot
                self._last_view = version
                if len(self._state_views) > 8:
                    del self._state_views[next(iter(self._state_views))]
            if previous is None:
                return {**snapshot, 'state_version': version}
            changes = {key: value for key, value in snapshot.items() if previous.get(key) != value}
            if 'language' in changes:
                changes['language_patch'] = {'length': len(snapshot['language']), 'items': [
                    {'index': i, 'value': row} for i, row in enumerate(snapshot['language'])
                    if i >= len(previous['language']) or previous['language'][i] != row]}
                del changes['language']
            return {**changes, 'partial': True, 'state_version': version}

    def record(self, namespace, key):
        if namespace == 'knowledge.hypotheses' and isinstance(key,list) and len(key)<=8 and all(isinstance(k,str) for k in key):
            key = tuple(key)
        if namespace not in {'experience.language', 'skills.runs', 'skills.goals', 'skills.sequences', 'knowledge.hypotheses'} or type(key) not in {str, int, tuple}:
            raise ValueError('Choose a stored conversation, skill run or goal record.')
        with self.lock:
            return plain(self.session.store.map(namespace)[key])

    def action(self, body):
        with self.lock:
            execution = None
            if body.get('action') not in {'sudoku_select', 'sudoku_check', 'sense'}:
                self.last_check = None
            if body.get("action") == "chat":
                message = body.get("message")
                if not isinstance(message, str) or not message.strip() or len(message) > 2000:
                    raise ValueError("Enter a message of up to 2,000 characters.")
                answer = self.session.chat(message, self.translator)
            elif body.get('action') == 'create_task':
                from persistent_tasks import create
                answer = create(self.session, body.get('request'), self.translator, body.get('steps'))
            elif body.get('action') == 'cancel_wait':
                self.session.store.map('interaction.state').pop('waiting',None)
                answer = 'Waiting request cancelled.'
            elif body.get('action') == 'teach_conversation':
                answer = self.session.teach_conversation()
            elif body.get('action') == 'teach_foundations':
                answer = self.session.teach_foundations()
            elif body.get('action') == 'teach_graph_package':
                answer = self.session.teach_graph_package(body.get('entries'), 'Lesson package supplied through the teaching panel')
            elif body.get('action') == 'run_skill':
                answer, execution = self.session.run_skill(body.get('name',''), body.get('argument'))
            elif body.get('action') == 'javascript_run':
                from javascript import run_source
                execution = run_source(self.session, body.get('source'), body.get('input'),
                                       'input' in body, 'JavaScript playground:\n' + str(body.get('source')))
                answer = 'Executed source through stored graph reader, compiler, and evaluator.'
            elif body.get('action') == 'achieve_goal':
                answer, execution = self.session.achieve_goal(body.get('goal'))
            elif body.get("action") in {"explore", "explore_all"}:
                results = []
                for _ in range(10 if body["action"] == "explore_all" else 1):
                    if self.session.explorer.choose() is None:
                        break
                    results.append(self.session.explore())
                answer = f"Completed {len(results)} experiment(s)."
            elif body.get("action") == "teach_graph":
                if type(body.get("replace", False)) is not bool:
                    raise ValueError("replace must be true or false.")
                answer = self.session.teach_graph(body.get("name", ""), body.get("graph"), replace=body.get("replace", False))
            elif body.get("action") == "forget_graph":
                answer = self.session.forget_graph(body.get("name", ""))
            elif body.get("action") == "run_sensor_graph":
                execution = self.session.run_sensor_graph(body.get("name", ""), body.get("argument"))
                answer = execution["answer"]
            elif body.get("action") == "sense":
                execution = {"result": self.session.perceive("canvas"), "trace": []}
                answer = "Observed the canvas. These are visible marks and input feedback, before taught interpretation."
            elif body.get("action") == "sudoku_reset":
                self.session.act_sensor("sudoku-canvas", "reset")
                answer = "Reset the Sudoku canvas to its teaching puzzle."
            elif body.get('action') == 'sudoku_clear':
                self.session.sudoku.reset([[0] * 9 for _ in range(9)])
                answer = 'Empty board. Every cell accepts 1–9; checking is separate.'
            elif body.get('action') == 'teach_sudoku_suite':
                answer = self.session.teach_sudoku_suite()
            elif body.get('action') in {'sudoku_check', 'sudoku_solve'}:
                name = 'sudoku_observe_check' if body['action'] == 'sudoku_check' else 'sudoku_observe_solve'
                execution = self.session.run_sensor_graph(name)
                self.last_check = execution['result']
                report = self.last_check
                if report is None:
                    answer = execution['answer']
                elif report['correct']:
                    answer = 'Correct: all cells are filled and satisfy the taught row, column and box rules.'
                elif not report['valid']:
                    answer = f"Incorrect: {len(report['conflicts'])} row, column or box group(s) violate the taught rules. Your entries are unchanged."
                else:
                    answer = 'Incomplete: no rule conflicts found so far. This does not establish that the remaining cells can be solved.'
            elif body.get("action") == "sudoku_randomize":
                blanks = int(body.get("blanks", 45))
                chosen = SudokuBoard()
                chosen.randomize(blanks=blanks)
                self.session.sudoku = chosen
                answer = "Generated a valid randomized Sudoku puzzle. Uniqueness is not guaranteed."
            elif body.get("action") == "sudoku_select":
                perception = self.session.act_sensor("sudoku-canvas", "select", {"row": int(body.get("row")), "col": int(body.get("col"))})
                answer = f"Selected cell ({int(body['row']) + 1},{int(body['col']) + 1}). Enter any digit from 1–9."
            elif body.get("action") == "sudoku_place":
                perception = self.session.act_sensor("sudoku-canvas", "place", {"row": int(body.get("row")), "col": int(body.get("col")), "value": int(body.get("value"))})
                answer = 'Input saved. Use Check board when you want to check the rules.'
            else:
                raise ValueError("Unknown action.")
            self.session.save(self.memory)
            result = {"answer": answer, "state": self.state(body.get('state_version'))}
            if execution is not None:
                result["execution"] = execution
            return result


def handler_for(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def respond(self, status, body, mime="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body if isinstance(body, bytes) else json.dumps(body).encode())

        def do_GET(self):
            if self.path == "/":
                self.respond(200, (ROOT / "preview.html").read_bytes(), "text/html; charset=utf-8")
            elif self.path in {"/sensory.js", "/sensory.css", '/sudoku-ui.js', '/graph-ui.js', '/javascript-ui.js', '/javascript-ui.css', '/workspace-ui.js', '/workspace-ui.css', '/web-ui.js', '/dashboard-ui.js', '/language-ui.js', '/tasks-ui.js'}:
                self.respond(200, (ROOT / self.path[1:]).read_bytes(),
                             "text/javascript; charset=utf-8" if self.path.endswith(".js") else "text/css; charset=utf-8")
            elif urlsplit(self.path).path == "/api/state":
                self.respond(200, app.state(parse_qs(urlsplit(self.path).query).get("since", [None])[0]))
            elif urlsplit(self.path).path == '/api/record':
                try:
                    query = parse_qs(urlsplit(self.path).query)
                    self.respond(200, app.record(query['namespace'][0], json.loads(query['key'][0])))
                except (ValueError, KeyError, TypeError):
                    self.respond(404, {'error': 'Stored record not found'})
            elif urlsplit(self.path).path == "/api/graph":
                with app.lock:
                    namespace = parse_qs(urlsplit(self.path).query).get('namespace', [None])[0]
                    self.respond(200, snapshot(app.session, namespace))
            elif urlsplit(self.path).path == '/api/web-image':
                if app.session.web.shot.exists():
                    self.respond(200, app.session.web.shot.read_bytes(), 'image/png')
                else:
                    self.respond(404, {'error':'No page opened'})
            elif self.path == "/api/example-graph":
                self.respond(200, json.loads((ROOT / "examples/factorial.graph.json").read_text()))
            elif self.path == '/api/lessons/temperature_skills':
                self.respond(200, json.loads((ROOT / 'examples/temperature.skills.json').read_text()))
            elif self.path in {"/api/lessons/read_marks", "/api/lessons/type_at"}:
                name = self.path.rsplit("/", 1)[1]
                self.respond(200, {"name": name, "graph": json.loads((ROOT / "examples" / (name + ".graph.json")).read_text())})
            else:
                self.respond(404, {"error": "Not found"})

        def do_POST(self):
            origin = self.headers.get("Origin")
            allowed = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
            if origin is not None and origin not in allowed:
                return self.respond(403, {"error": "Use this preview's own page."})
            if self.path != "/api/action" or self.headers.get("Content-Type") != "application/json":
                return self.respond(400, {"error": "Expected a JSON action."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length < 1000000:
                    raise ValueError("Invalid request size.")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Expected an action object.")
                result = app.action(body)
                self.respond(200, result)
            except (ValueError, OSError, KeyError) as error:
                self.respond(400, {"error": str(error)})
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--memory", type=Path, default=ROOT / "preview-memory.json")
    parser.add_argument("--base-url", help="Attach directly to an already-running llama.cpp server")
    parser.add_argument("--model", default="gemma-4-E2B-it-Q4_K_M.gguf")
    args = parser.parse_args()
    runtime = GoudRuntime()
    try:
        print("Connecting to the desktop app's Gemma runtime…", flush=True)
        if args.base_url:
            url, model = args.base_url.rstrip("/"), args.model
        else:
            url, model = runtime.connect()
        app = Application(LlamaCppLanguage(model, url), args.memory)
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(app))
        print(f"Gemma connected: {model}\nPreview: http://127.0.0.1:{args.port}", flush=True)
        stop = threading.Event()
        def background_loop():
            import behavior
            while not stop.wait(5):
                # Queue behind an active request instead of starving under
                # several tabs polling on the same five-second cadence.
                app.lock.acquire()
                if stop.is_set():
                    app.lock.release()
                    break
                try:
                    behavior.tick(app.session)
                except (ValueError, KeyError, OSError) as error:
                    app.session.store.map('session.behavior')['last_error'] = str(error)
                finally:
                    app.lock.release()
        worker = threading.Thread(target=background_loop, daemon=True)
        worker.start()
        try:
            server.serve_forever()
        finally:
            stop.set()
            server.server_close()
    except KeyboardInterrupt:
        pass
    finally:
        runtime.close()


if __name__ == "__main__":
    main()
