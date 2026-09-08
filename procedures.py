"""Inspectable Number -> Number computation graphs and a bounded interpreter."""
import ast
import re
from fractions import Fraction


SIGNATURES = {"add": 2, "subtract": 2, "multiply": 2, "divide": 2, "power": 2, "negate": 1, "call": 1}


def procedure_name(name):
    name = re.sub(r"\s+", "_", name.strip().lower())
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", name) or name == "x":
        raise ValueError("Give the procedure a short name made of letters, numbers, or underscores.")
    return name


def compile_graph(expression, parameter=False, library=None):
    library = library or {}
    expression = expression.strip().replace("×", "*").replace("÷", "/").replace("−", "-").replace("^", "**")
    if not expression or len(expression) > 250 or not re.fullmatch(r"[a-zA-Z0-9_\s.+*/(),-]+", expression):
        raise ValueError("Use numbers, x for the input, arithmetic operators, or a learned procedure such as double(x).")
    if any(len(n) > 64 for n in re.findall(r"\d+", expression)):
        raise ValueError("That number is too large for this notebook.")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError):
        raise ValueError("Please check the numbers and parentheses in that procedure.") from None
    if len(list(ast.walk(tree))) > 100:
        raise ValueError("Please split that into smaller procedures.")
    nodes = []

    def add(op, args=(), **fields):
        node = {"id": f"n{len(nodes)}", "op": op, "inputs": list(args), "type": "Number", **fields}
        nodes.append(node)
        return node["id"]

    def build(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            literal = ast.get_source_segment(expression, node)
            if not re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)", literal):
                raise ValueError("Use ordinary decimal numbers, without scientific notation.")
            return add("literal", value=literal)
        if isinstance(node, ast.Name) and node.id == "x" and parameter:
            return add("input", name="x")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            child = build(node.operand)
            return child if isinstance(node.op, ast.UAdd) else add("negate", (child,))
        operations = {ast.Add: "add", ast.Sub: "subtract", ast.Mult: "multiply", ast.Div: "divide", ast.Pow: "power"}
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            return add(operations[type(node.op)], (build(node.left), build(node.right)))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1 and not node.keywords:
            name = procedure_name(node.func.id)
            if name not in library:
                raise ValueError(f"I haven't learned the procedure '{name}' yet.")
            return add("call", (build(node.args[0]),), name=name)
        raise ValueError("I can represent arithmetic procedures with one numeric input x. That expression uses an unsupported step.")
    output = build(tree.body)
    return {"input_type": "Number" if parameter else "Unit", "output_type": "Number",
            "expression": expression, "nodes": nodes, "output": output}


def define(library, name, expression, source, replace=False):
    name = procedure_name(name)
    if name in library and not replace:
        raise ValueError(f"I already know '{name}'. Say you want to redefine it to change its procedure.")
    if replace and name not in library:
        raise ValueError(f"I haven't learned '{name}' yet. Define it first.")
    graph = compile_graph(expression, parameter=True, library=library)
    candidate = dict(library)
    candidate[name] = {"graph": graph, "source": source}

    visited = set()
    def visit(current, path):
        if current in path:
            raise ValueError("That would make a recursive procedure. This interpreter currently supports acyclic calls only.")
        if current in visited:
            return
        visited.add(current)
        for node in candidate[current]["graph"]["nodes"]:
            if node["op"] == "call":
                visit(node["name"], path | {current})
    for current in candidate:
        visit(current, set())
    library[name] = candidate[name]
    return name, graph


def execute(graph, argument=None, library=None):
    from graph_runtime import execute_graph
    value, trace = execute_graph(graph, argument, library)
    return value, [entry["operation"] + " → " + entry["result"] for entry in trace]


def describe(name, entry):
    graph = entry["graph"]
    lines = [f"{name}(x) = {graph.get('expression', 'stored graph')}",
             f"Type: {graph['input_type']} → {graph['output_type']}", "Stored steps:"]
    for node in graph["nodes"]:
        args = ", ".join(node["inputs"])
        detail = node.get("value", node.get("name", args))
        lines.append(f"{node['id']}: {node['op']}({detail}) → {node['type']}")
    return "\n".join(lines + ["Output: " + graph["output"]])
