"""Generic finite constraint-problem data and bounded propagation/search.

This module knows nothing about Sudoku. A problem is serializable data: named
variables, finite domains, and constraints. Domain adapters may produce that
data; the graph interpreter executes this generic machine.
"""
import copy


MAX_VARIABLES = 200
MAX_DOMAIN = 32
MAX_NODES = 100000
METHODS = {"singleton", "unit_unique"}


def validate(problem):
    if not isinstance(problem, dict):
        raise ValueError("A constraint problem must be an object.")
    variables, domains, constraints = problem.get("variables"), problem.get("domains"), problem.get("constraints")
    if not isinstance(variables, list) or not 1 <= len(variables) <= MAX_VARIABLES or any(not isinstance(v, str) or not v or len(v) > 100 for v in variables) or len(set(variables)) != len(variables):
        raise ValueError("A constraint problem needs unique variable names within its size limit.")
    if not isinstance(domains, dict) or set(domains) != set(variables):
        raise ValueError("Every constraint variable needs a finite domain.")
    for name in variables:
        domain = domains[name]
        if not isinstance(domain, list) or not 1 <= len(domain) <= MAX_DOMAIN or any(type(v) not in {int, str} for v in domain) or len(set(domain)) != len(domain):
            raise ValueError("Constraint domains must be finite, non-empty and bounded.")
    if not isinstance(constraints, list) or len(constraints) > MAX_VARIABLES * 4:
        raise ValueError("Too many constraints for this bounded interpreter.")
    for constraint in constraints:
        if not isinstance(constraint, dict) or constraint.get("kind") not in {"all_different", "equal", "not_equal"}:
            raise ValueError("Supported generic constraints are all_different, equal, and not_equal.")
        scope = constraint.get("scope", [])
        if not isinstance(scope, list) or not scope or any(not isinstance(var, str) or var not in variables for var in scope) or len(set(scope)) != len(scope):
            raise ValueError("Constraint scopes must name existing variables.")
        if constraint["kind"] in {"equal", "not_equal"} and len(scope) != 2:
            raise ValueError("Equal and not_equal constraints need two variables.")
    return problem


def _consistent(problem, assignment):
    for constraint in problem["constraints"]:
        scope = constraint["scope"]
        present = [assignment[var] for var in scope if var in assignment]
        kind = constraint["kind"]
        if kind == "all_different" and len(present) != len(set(map(repr, present))):
            return False
        if kind == "equal" and len(present) == 2 and present[0] != present[1]:
            return False
        if kind == "not_equal" and len(present) == 2 and present[0] == present[1]:
            return False
    return True


def solve(problem, methods=None, limit=MAX_NODES):
    """Return one solution and an explainable generic search trace."""
    validate(problem)
    methods = sorted(METHODS) if methods is None else methods
    if not isinstance(methods, list) or any(method not in METHODS for method in methods):
        raise ValueError("Unknown generic constraint inference method.")
    if not isinstance(limit, int) or not 1 <= limit <= MAX_NODES:
        raise ValueError("Constraint search step budget is out of bounds.")
    domains = {name: list(values) for name, values in problem["domains"].items()}
    assignment, trace, visited = {}, [], [0]

    def propagate(current, remaining):
        changed = True
        while changed:
            changed = False
            for constraint in problem["constraints"]:
                if constraint["kind"] != "all_different":
                    continue
                used = {repr(current[var]) for var in constraint["scope"] if var in current}
                for var in constraint["scope"]:
                    if var in current:
                        continue
                    filtered = [value for value in remaining[var] if repr(value) not in used]
                    if not filtered:
                        return None
                    if filtered != remaining[var]:
                        remaining[var] = filtered; changed = True
                    if "singleton" in methods and len(filtered) == 1:
                        current[var] = filtered[0]; changed = True
                        trace.append({"operation": "propagate", "result": f"{var} = {filtered[0]}"})
                        if not _consistent(problem, current):
                            return None
            if "unit_unique" in methods:
                for constraint in problem["constraints"]:
                    if constraint["kind"] != "all_different":
                        continue
                    used = {repr(current[var]) for var in constraint["scope"] if var in current}
                    candidates = {}
                    for var in constraint["scope"]:
                        if var not in current:
                            for value in remaining[var]:
                                if repr(value) not in used:
                                    candidates.setdefault(repr(value), []).append((var, value))
                    # A unique occurrence is forced only when all available
                    # values must be used. All-different alone permits unused
                    # values when there are more values than variables.
                    missing = [var for var in constraint["scope"] if var not in current]
                    if len(candidates) != len(missing):
                        continue
                    for matches in candidates.values():
                        if len(matches) == 1:
                            var, value = matches[0]
                            if var not in current:
                                current[var] = value
                                remaining[var] = [value]
                                changed = True
                                trace.append({"operation": "propagate", "result": f"{var} = {value}"})
                                if not _consistent(problem, current):
                                    return None
        return remaining

    def search(current, remaining):
        visited[0] += 1
        if visited[0] > limit:
            raise ValueError("Constraint search stopped at its step budget.")
        current, remaining = dict(current), copy.deepcopy(remaining)
        if not _consistent(problem, current):
            return None
        remaining = propagate(current, remaining)
        if remaining is None:
            return None
        missing = [var for var in problem["variables"] if var not in current]
        if not missing:
            return current
        variable = min(missing, key=lambda name: len(remaining[name]))
        for value in remaining[variable]:
            trace.append({"operation": "branch", "result": f"{variable} = {value}"})
            candidate = dict(current); candidate[variable] = value
            if _consistent(problem, candidate):
                result = search(candidate, remaining)
                if result is not None:
                    return result
            trace.append({"operation": "backtrack", "result": f"reject {variable} = {value}"})
        return None

    result = search(assignment, domains)
    if result is None:
        raise ValueError("The generic constraint problem has no solution within the search budget (visited " + str(visited[0]) + ").")
    return result, trace
