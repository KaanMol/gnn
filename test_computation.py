import tempfile
import unittest
from pathlib import Path

from arithmetic import calculate as raw_calculate, count
from graph_runtime import compose, execute_graph as raw_execute_graph, identity, validate_graph
from interface import Session
from procedures import compile_graph
from semantics import operation


# Explicitly supply the arithmetic lessons this computation fixture was taught.
import foundation
NUMBER_LESSONS = foundation.curriculum()
def execute_graph(graph, argument=None, library=None, **kwargs):
    return raw_execute_graph(graph, argument, NUMBER_LESSONS if library is None else library, **kwargs)
def calculate(expression, library=None):
    return raw_calculate(expression, NUMBER_LESSONS if library is None else library)


def factorial_graph():
    def n(i, op, inputs=(), kind="Number", **kw):
        return dict(id=i, op=op, inputs=list(inputs), type=kind, **kw)
    def graph(nodes, output, source="Number", target="Number"):
        return dict(nodes=nodes, output=output, input_type=source, output_type=target)
    common = [n("s", "input", kind="List[Number]"), n("zero", "literal", value="0"),
              n("one", "literal", value="1"), n("remaining", "at", ("s", "zero"))]
    guard = graph(common + [n("test", "less", ("one", "remaining"), "Bool")], "test", "List[Number]", "Bool")
    body = graph(common + [n("acc", "at", ("s", "one")), n("next", "subtract", ("remaining", "one")),
                           n("product", "multiply", ("acc", "remaining")),
                           n("updated", "list", ("next", "product"), "List[Number]")], "updated", "List[Number]", "List[Number]")
    return graph([n("x", "input"), n("zero", "literal", value="0"), n("one", "literal", value="1"),
                  n("integer", "is_integer", ("x",), "Bool"), n("negative", "less", ("x", "zero"), "Bool"),
                  n("nonnegative", "not", ("negative",), "Bool"), n("valid", "and", ("integer", "nonnegative"), "Bool"),
                  n("checked", "require", ("valid", "x")), n("state", "list", ("checked", "one"), "List[Number]"),
                  n("loop", "while", ("state",), "List[Number]", guard=guard, body=body),
                  n("result", "at", ("loop", "one"))], "result")


class ComputationTests(unittest.TestCase):
    def test_exact_arithmetic_precedence_and_failures(self):
        self.assertTrue(calculate("0.1 + 0.2").startswith("0.1 + 0.2 = 0.3"))
        self.assertTrue(calculate("(12 + 3) * 4").startswith("(12 + 3) * 4 = 60"))
        self.assertIn("= 1/3", calculate("1 / 3"))
        for bad in ["1/0", "2**1000", "__import__('os')", "1//2", "1e999999"]:
            with self.assertRaises(ValueError):
                calculate(bad)

    def test_taught_procedures_and_composition_persist(self):
        s = Session()
        for item in [operation("define_procedure", "double", text="x * 2"),
                     operation("define_procedure", "increment", text="x + 1"),
                     operation("compose_procedure", "double_then_increment", "double", "increment")]:
            s.apply("teaching", {"operations": [item]})
        self.assertIn("= 43", s.apply("run", {"operations": [operation("run_procedure", "double_then_increment", text="21")]}))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            s.save(path)
            restored = Session.load(path)
        self.assertEqual(s.core.procedures, restored.core.procedures)

    def test_graph_loop_executes_algorithm_without_algorithm_handler(self):
        graph = factorial_graph()
        result, trace = execute_graph(graph, 6)
        self.assertEqual(result, 720)
        self.assertTrue(any(step["operation"] == "while" for step in trace))
        self.assertEqual(execute_graph(graph, 0)[0], 1)
        for invalid in (-1, "1/2"):
            with self.assertRaisesRegex(ValueError, "precondition"):
                execute_graph(graph, invalid)
        with self.assertRaisesRegex(ValueError, "budget"):
            execute_graph(graph, 6, limit=10)

    def test_typed_composition_identity_and_associativity(self):
        f, g, h = [compile_graph(e, True) for e in ("x * 2", "x + 3", "x * x")]
        left, right = compose(compose(f, g), h), compose(f, compose(g, h))
        for x in (-2, 0, 7):
            self.assertEqual(execute_graph(left, x)[0], execute_graph(right, x)[0])
            self.assertEqual(execute_graph(compose(identity("Number"), f), x)[0], execute_graph(f, x)[0])
            self.assertEqual(execute_graph(compose(f, identity("Number")), x)[0], execute_graph(f, x)[0])
        with self.assertRaisesRegex(ValueError, "compose"):
            compose(f, identity("Bool"))

    def test_type_errors_and_lazy_branch(self):
        graph = {"input_type": "Number", "output_type": "Number", "output": "answer", "nodes": [
            {"id": "x", "op": "input", "inputs": [], "type": "Number"},
            {"id": "zero", "op": "literal", "value": "0", "inputs": [], "type": "Number"},
            {"id": "test", "op": "equal", "inputs": ["x", "zero"], "type": "Bool"},
            {"id": "bad", "op": "divide", "inputs": ["x", "zero"], "type": "Number"},
            {"id": "answer", "op": "choose", "inputs": ["test", "zero", "bad"], "type": "Number"}]}
        self.assertEqual(execute_graph(graph, 0)[0], 0)
        graph["nodes"][-1]["inputs"][0] = "x"
        with self.assertRaisesRegex(ValueError, "Type mismatch"):
            validate_graph(graph)

    def test_counting_and_fast_path_dont_need_llm(self):
        class NoModel:
            def translate(self, *args):
                raise AssertionError("Numeric request called the LLM")
        s = Session()
        self.assertIn("= 42", s.chat("What is 6 * 7?", NoModel()))
        s.apply("teach", {"operations": [operation("define_procedure", "double", text="x * 2")]})
        self.assertIn("= 42", s.chat("Double 21", NoModel()))
        self.assertIn("= 42", s.chat("double(21)", NoModel()))
        self.assertIn("5, 4, 3, 2", s.chat("Count from 5 to 2", NoModel()))
        s.apply("facts", {"operations": [operation("assert", "Mira", "is", "person")]})
        self.assertIn("1 known", count(operation("count", "person", "known"), s.core, s.explorer))

    def test_graph_teaching_survives_restart(self):
        s = Session()
        s.teach_graph("factorial", factorial_graph())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            s.save(path)
            restored = Session.load(path)
            self.assertIn("= 120", restored.apply("run", {"operations": [operation("run_procedure", "factorial", text="5")]}))


if __name__ == "__main__":
    unittest.main()
