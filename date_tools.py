"""Read-only environment tools and bindings for stored date procedures.

Clock acquisition is infrastructure. Interpretation, bindings and age arithmetic are taught graphs.
"""
from datetime import date, datetime
import re

from graph_runtime import execute_graph
import foundation
from arithmetic import number_text
from semantics import operation


def current_date():
    now = datetime.now().astimezone()
    return {"date": now.date().isoformat(), "timezone": str(now.tzinfo),
            "observed_at": now.isoformat(), "source": "local-system-clock"}


TOOLS = {"current_date": {"description": "Read today's local calendar date and observation time.",
                          "read_only": True, "output_type": "List[Number]", "call": current_date}}


def call_tool(name):
    if name not in TOOLS:
        raise ValueError("Unknown environment tool.")
    return TOOLS[name]["call"]()


def parse_date(value, library=None):
    parts, _ = foundation.run(library or {}, 'calendar_parse', value)
    return date(*parts)  # Host date object is only the public formatting adapter.


def date_answer(core, subject, procedure="age_years"):
    birth_record = core.invoke('calendar_find_birth', {
        'subject': subject, 'facts': [list(f) for f in core.facts],
        'negatives': [list(f) for f in core.negatives]})
    birth = birth_record['parts']
    if procedure not in core.procedures:
        raise ValueError(f"I have the birth date, but haven't learned the '{procedure}' procedure yet.")
    graph = core.procedures[procedure]["graph"]
    bindings = graph.get('input_fields')
    if not isinstance(bindings, list) or not bindings:
        raise ValueError('This procedure needs explicit birth date-part input_fields.')
    inputs = core.invoke('calendar_bind_input', {'parts': birth, 'fields': bindings})
    result, trace = execute_graph(graph, inputs, core.procedures)
    observation = next((step["observation"] for step in trace if step["operation"] == "current_date" and step.get("observation")), None)
    if observation is None:
        raise ValueError("The taught age procedure must obtain today through the current_date tool.")
    today = core.invoke('calendar_parse', observation['date'])
    if core.invoke('calendar_before', {'a': today, 'b': birth}):
        raise ValueError("That birth date is in the future. Please check it.")
    if graph["output_type"] != "Number":
        raise ValueError("The selected date procedure must return a number.")
    birth_text = core.invoke('calendar_format', birth)
    answer = (f"{subject} is {number_text(result)} years old.\n"
              f"Birth date from memory: {birth_text}.\n"
              f"Today: {observation['date']} ({observation['timezone']}, local clock).\n"
              f"Executed taught procedure: {procedure}.\nSteps:\n" +
              "\n".join(f"{step['node']}: {step['operation']} → {step['result']}" for step in trace))
    return answer, {"tool": "current_date", "observation": observation,
                    "procedure": procedure, "graph": graph,
                    "inputs": dict(zip(bindings, inputs)), "birth_facts": birth_record['facts'], "trace": trace}


def direct_date(text, library=None):
    candidate = text.strip().rstrip(".!?")
    if re.fullmatch(r"(?:what(?: is|'s) (?:today(?:'s date)?|the (?:current )?date)|what date is (?:it|today)|today's date)", candidate, re.I):
        return {"operations": [operation("current_date")]}
    match = re.fullmatch(r"(?:how old (?:am (I)|is (.+))|what(?: is|'s) (my age|.+?'s age))", candidate, re.I)
    if match:
        subject = "speaker" if match[1] or (match[3] or "").lower() == "my age" else (match[2] or match[3][:-6])
        if subject.strip().lower() in {"she", "he", "they", "her", "him", "it"}:
            return None  # Let the language interface resolve conversational reference.
        return {"operations": [operation("date_procedure", subject, "age_years")]}
    match = re.fullmatch(r"(I was|I am|.+? was|.+? is) born on (.+)", candidate, re.I)
    if match:
        subject = "speaker" if match[1].lower() in {"i was", "i am"} else match[1].rsplit(" ", 1)[0]
        try:
            birth = parse_date(match[2], library)
        except ValueError as error:
            return {"operations": [operation("clarify", text=str(error))]}
        return {"operations": [operation("assert", subject, "birth date", birth.isoformat())]}
    return None
