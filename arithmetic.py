"""Bounded exact arithmetic and counting. Never evaluates Python code."""
import json
import re
from fractions import Fraction

from semantics import operation


def number_text(value):
    if value.denominator == 1:
        return str(value.numerator)
    remainder = value.denominator
    twos = fives = 0
    while remainder % 2 == 0:
        twos += 1
        remainder //= 2
    while remainder % 5 == 0:
        fives += 1
        remainder //= 5
    places = max(twos, fives)
    if remainder == 1 and places <= 80:
        digits = str(abs(value.numerator) * 2 ** (places - twos) * 5 ** (places - fives)).zfill(places + 1)
        return ("-" if value < 0 else "") + digits[:-places] + "." + digits[-places:]
    return str(value)


def calculate(expression, library=None):
    from procedures import compile_graph, execute
    graph = compile_graph(expression, library=library)
    result, steps = execute(graph, library=library)
    return graph["expression"].replace("**", "^") + " = " + number_text(result) + ("\nSteps:\n" + "\n".join(steps) if steps else "")


def count(item, core, explorer):
    mode = item["relation"]
    if mode == "sequence":
        try:
            start, end = int(item["subject"]), int(item["object"])
        except ValueError:
            raise ValueError("What whole numbers should I start and stop at?") from None
        if abs(end - start) >= 200 or max(abs(start), abs(end)) > 10 ** 12:
            raise ValueError("I can list up to 200 consecutive numbers, with endpoints within one trillion.")
        numbers = core.invoke('count_sequence', {'start': start, 'end': end})
        return ", ".join(map(str, numbers)) + f"\n{core.invoke('count_items', numbers)} numbers, including both endpoints."
    if mode == "items":
        try:
            items = json.loads(item["text"])
        except ValueError:
            raise ValueError("Which items should I count? Please give me a list.") from None
        if not isinstance(items, list) or len(items) > 200 or any(not isinstance(x, str) for x in items):
            raise ValueError("Please give me a list of up to 200 named items.")
        return f"{core.invoke('count_items', items)} items." + ("\n" + "; ".join(f"{i + 1}. {x}" for i, x in enumerate(items)) if items else "")
    if mode == "known":
        concept = item["subject"].strip().lower()
        if not concept:
            raise ValueError("What type of thing should I count in memory?")
        selected = core.invoke('count_known', {**core.evidence(), 'concept': concept})
        matches, conflicts = selected['matches'], selected['conflicts']
        return (f"{core.invoke('count_items', matches)} known members of '{concept}' in this notebook."
                + ("\n" + ", ".join(matches) if matches else "")
                + (f"\nExcluded {core.invoke('count_items', conflicts)} with conflicting membership evidence." if conflicts else "")
                + "\nThis counts stored evidence, not everything that exists.")
    if mode == "world":
        return f"{core.invoke('count_items', list(explorer.observations))} objects in the toy world.\n" + ", ".join(explorer.observations)
    raise ValueError("Should I count a number sequence, listed items, a type in memory, or the toy-world objects?")


def direct_math(text):
    """Fast path for explicit numeric requests, without model interpretation."""
    candidate = text.strip().rstrip("?!. ")
    candidate = re.sub(r"^(?:what is|what's|calculate|compute)\s+", "", candidate, flags=re.I)
    if re.search(r"\d", candidate) and re.fullmatch(r"[\d\s.+*/()^×÷−-]+", candidate):
        return {"operations": [operation("calculate", text=candidate)]}
    match = re.fullmatch(r"count (?:from (-?\d+) )?(?:to|up to) (-?\d+)", text.strip().rstrip(".!?"), flags=re.I)
    if match:
        return {"operations": [operation("count", match[1] or "1", "sequence", match[2])]}
    return None


def direct_procedure(text, library):
    candidate = text.strip().rstrip(".!?")
    for name in library:
        match = re.fullmatch(r"(?:run |apply )?" + re.escape(name) + r"(?:\s+(?:on |to )?(.+)|\((.+)\))", candidate, flags=re.I)
        if match:
            argument = match[1] or match[2]
            if re.fullmatch(r"[\d\s.+*/()^×÷−-]+", argument):
                return {"operations": [operation("run_procedure", name, text=argument)]}
    match = re.fullmatch(r"create (\w+) by running (\w+) then (\w+)", candidate, flags=re.I)
    if match and match[2].lower() in library and match[3].lower() in library:
        return {"operations": [operation("compose_procedure", match[1], match[2].lower(), match[3].lower())]}
    return None
