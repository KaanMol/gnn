"""Author the full Sudoku lesson package. Never imported by the application.

The generated JSON is taught explicitly and stored in the graph database.
Removing a stored lesson cannot trigger this authoring script or reload it.
"""
import json
from pathlib import Path
from graph_dsl import Graph, G


def build():
    suite = {}
    def save(name, g, out, kind='Data', **metadata):
        suite[name] = {'graph': g.finish(out, kind, **metadata),
                       'source': 'Explicit full Sudoku curriculum: ' + name}

    g = Graph()
    table = g.data({'': 0, **{str(i): i for i in range(1, 10)}})
    save('sudoku_symbol', g, g.op('lookup', table, g.input))

    groups = [[r*9+c for c in range(9)] for r in range(9)]
    groups += [[r*9+c for r in range(9)] for c in range(9)]
    groups += [[r*9+c for r in range(br, br+3) for c in range(bc, bc+3)]
               for br in (0, 3, 6) for bc in (0, 3, 6)]
    g = Graph()
    save('sudoku_rules', g, g.data({'groups': groups, 'symbols': list(range(1, 10)), 'empty': 0}),
         description='Nine distinct digits in every row, column, and box; blank is 0. Groups refer to marks ordered by y then x.')

    b = Graph(); read = b.call('sudoku_symbol', b.get(b.input, 'text'))
    g = Graph(); marks = g.get(g.input, 'marks')
    ordered = g.op('sort', g.op('sort', marks, key='x'), key='y')
    count_ok = g.op('equal', g.size(ordered), g.number(81), kind='Bool')
    checked = g.op('require', count_ok, ordered, message='The taught board reader expects 81 marks.')
    save('sudoku_read', g, g.map(checked, b.finish(read)))

    # Every group's assigned values must be distinct; all values must either
    # belong to the taught alphabet or equal the taught empty marker.
    take = Graph(); selected = take.op('item', take.get(take.input, 'context'), take.get(take.input, 'item'))
    nonempty = Graph(); keep = nonempty.op('not', nonempty.eq(nonempty.get(nonempty.input, 'item'), nonempty.get(nonempty.input, 'context')), kind='Bool')
    unit = Graph(); ctx = unit.get(unit.input, 'context')
    numbers = unit.map(unit.get(unit.input, 'item'), take.finish(selected), unit.get(ctx, 'values'))
    assigned = unit.map(numbers, nonempty.finish(keep, 'Bool'), unit.get(ctx, 'empty'), filter=True)
    valid = unit.op('equal', unit.size(assigned), unit.size(unit.op('unique', assigned)), kind='Bool')
    member = Graph(); mctx = member.get(member.input, 'context'); mv = member.get(member.input, 'item')
    permitted = member.op('or', member.eq(mv, member.get(mctx, 'empty')),
                          member.op('contains', member.get(mctx, 'symbols'), mv, kind='Bool'), kind='Bool')
    g = Graph(); problem = g.get(g.input, 'problem'); values = g.get(g.input, 'values')
    flags = g.map(g.get(problem, 'groups'), unit.finish(unit.op('bool_data', valid)),
                  g.record(values=values, empty=g.get(problem, 'empty')))
    allowed = g.map(values, member.finish(member.op('bool_data', permitted)), problem)
    bad = g.op('contains', g.op('concat', flags, allowed), g.data(False), kind='Bool')
    save('finite_valid', g, g.op('not', bad, kind='Bool'), 'Bool')

    # Candidate calculation is graph data: select groups containing an index,
    # read their values, and subtract those values from the taught alphabet.
    scope = Graph(); contains = scope.op('contains', scope.get(scope.input, 'item'), scope.get(scope.input, 'context'), kind='Bool')
    g = Graph(); problem = g.get(g.input, 'problem')
    related = g.map(g.get(problem, 'groups'), scope.finish(contains, 'Bool'), g.get(g.input, 'index'), filter=True)
    peers = g.op('unique', g.op('flatten', related))
    used = g.map(peers, take.finish(selected), g.get(g.input, 'values'))
    save('finite_candidates', g, g.op('difference', g.get(problem, 'symbols'), used))

    empty = Graph(); ctx = empty.get(empty.input, 'context')
    value = empty.op('item', empty.get(ctx, 'values'), empty.get(empty.input, 'item'))
    check = empty.eq(value, empty.get(ctx, 'problem', 'empty'))
    option = Graph(); ctx = option.get(option.input, 'context'); idx = option.get(option.input, 'item')
    candidates = option.call('finite_candidates', option.record(problem=option.get(ctx, 'problem'), values=option.get(ctx, 'values'), index=idx))
    entry = option.record(index=idx, options=candidates, count=option.op('as_data', option.size(candidates)))
    g = Graph(); values = g.get(g.input, 'values')
    indices = g.map(g.op('indices', values), empty.finish(check, 'Bool'), g.input, filter=True)
    options = g.map(indices, option.finish(entry), g.input)
    save('finite_options', g, g.op('sort', options, key='count'))

    # A singleton is a deduction; larger candidate sets require a choice.
    g = Graph(); best = g.op('item', g.input, g.data(0))
    single = g.eq(g.get(best, 'count'), g.data(1))
    save('finite_naked_single', g, g.choose(single, g.op('data_list', best), g.data([])))

    # Hidden singles: in a full-alphabet all-different group, an unused symbol
    # with exactly one possible position is forced. This inference is not sound
    # for smaller groups, so the equal-cardinality condition is explicit.
    fit = Graph(); ctx = fit.get(fit.input, 'context'); item = fit.get(fit.input, 'item')
    fits = fit.op('and', fit.op('contains', fit.get(ctx, 'group'), fit.get(item, 'index'), kind='Bool'),
                  fit.op('contains', fit.get(item, 'options'), fit.get(ctx, 'symbol'), kind='Bool'), kind='Bool')
    digit = Graph(); ctx = digit.get(digit.input, 'context'); symbol = digit.get(digit.input, 'item')
    possible = digit.map(digit.get(ctx, 'options'), fit.finish(fits, 'Bool'),
                         digit.record(group=digit.get(ctx, 'group'), symbol=symbol), filter=True)
    alone = digit.op('equal', digit.size(possible), digit.number(1), kind='Bool')
    forced = digit.record(index=digit.get(digit.op('item', possible, digit.data(0)), 'index'),
                           options=digit.op('data_list', symbol), count=digit.data(1), group=digit.get(ctx, 'group'))
    item_result = digit.choose(alone, digit.op('data_list', forced), digit.data([]))
    group = Graph(); ctx = group.get(group.input, 'context'); scope_value = group.get(group.input, 'item')
    symbols = group.get(ctx, 'problem', 'symbols')
    used = group.map(scope_value, take.finish(selected), group.get(ctx, 'values'))
    missing = group.op('difference', symbols, used)
    cardinality = group.op('equal', group.size(scope_value), group.size(symbols), kind='Bool')
    group_result = group.op('flatten', group.map(missing, digit.finish(item_result),
                           group.record(options=group.get(ctx, 'options'), group=scope_value)))
    g = Graph()
    hidden = g.op('flatten', g.map(g.get(g.input, 'problem', 'groups'),
                                   group.finish(group.choose(cardinality, group_result, group.data([]))), g.input))
    save('finite_hidden_single', g, hidden)

    g = Graph(); options = g.get(g.input, 'options'); best = g.op('item', options, g.data(0))
    naked = g.call('finite_naked_single', options)
    hidden = g.call('finite_hidden_single', g.input)
    hidden_best = g.op('item', hidden, g.data(0))
    decision = g.choose(g.nonempty(naked), g.op('emit', best, best, label='naked_single'),
                 g.choose(g.nonempty(hidden), g.op('emit', hidden_best, hidden_best, label='hidden_single'),
                          g.op('emit', best, best, label='branch')))
    save('finite_decision', g, g.choose(g.eq(g.get(best, 'count'), g.data(0)),
                                       g.op('emit', best, best, label='dead_end'), decision))

    # Explicit stack search. Singleton candidates naturally make one successor;
    # multiple candidates branch. Failed states are discarded (backtracking).
    extend = Graph(); ctx = extend.get(extend.input, 'context')
    next_values = extend.op('set_item', extend.get(ctx, 'values'), extend.get(ctx, 'index'), extend.get(extend.input, 'item'))
    guard = Graph()
    again = guard.op('and', guard.nonempty(guard.get(guard.input, 'pending')),
                     guard.op('not', guard.op('as_bool', guard.get(guard.input, 'found'), kind='Bool'), kind='Bool'), kind='Bool')
    body = Graph(); state = body.input; pending = body.get(state, 'pending'); problem = body.get(state, 'problem')
    values = body.op('item', pending, body.data(-1)); rest = body.op('slice', pending, stop=-1)
    context = body.record(problem=problem, values=values)
    valid = body.call('finite_valid', context, 'Bool')
    options = body.call('finite_options', context)
    complete = body.op('not', body.nonempty(options), kind='Bool')
    solved = body.record(problem=problem, pending=rest, found=body.data(True), values=values)
    best = body.call('finite_decision', body.record(problem=problem, values=values, options=options))
    candidates = body.get(best, 'options')
    choices = body.map(candidates, extend.finish(next_values), body.record(values=values, index=body.get(best, 'index')))
    frontier = body.op('concat', rest, choices)
    continuing = body.record(problem=problem, pending=frontier, found=body.data(False), values=values)
    rejected = body.record(problem=problem, pending=rest, found=body.data(False), values=values)
    # Explicit explanations survive even when low-level tracing is suppressed.
    branch = body.op('emit', continuing, best, label='expand_candidates')
    failed = body.op('emit', rejected, values, label='reject_state')
    success = body.op('emit', solved, values, label='solution')
    updated = body.choose(valid, body.choose(complete, success, branch), failed)
    g = Graph(); problem = g.input
    initial = g.record(problem=problem, pending=g.op('data_list', g.get(problem, 'values')), found=g.data(False), values=g.get(problem, 'values'))
    loop = g.op('while', initial, guard=guard.finish(again, 'Bool'), body=body.finish(updated))
    save('finite_search', g, g.record(found=g.get(loop, 'found'), values=g.get(loop, 'values')), trace_mode='explicit')

    g = Graph(); rules = g.call('sudoku_rules', g.input); values = g.call('sudoku_read', g.input)
    problem = g.record(values=values, groups=g.get(rules, 'groups'), symbols=g.get(rules, 'symbols'), empty=g.get(rules, 'empty'))
    save('sudoku_problem', g, problem)

    # Checking is a separate taught procedure, with no device effects. Return
    # conflicting groups as evidence, and distinguish full from partial input.
    unit = Graph(); ctx = unit.get(unit.input, 'context'); members = unit.get(unit.input, 'item')
    vals = unit.map(members, take.finish(selected), unit.get(ctx, 'values'))
    assigned = unit.map(vals, nonempty.finish(keep, 'Bool'), unit.get(ctx, 'empty'), filter=True)
    unequal = unit.op('not', unit.op('equal', unit.size(assigned), unit.size(unit.op('unique', assigned)), kind='Bool'), kind='Bool')
    g = Graph(); problem = g.call('sudoku_problem', g.input); values = g.get(problem, 'values')
    conflicts = g.map(g.get(problem, 'groups'), unit.finish(unequal, 'Bool'), problem, filter=True)
    valid = g.call('finite_valid', g.record(problem=problem, values=values), 'Bool')
    filled = g.op('not', g.op('contains', values, g.get(problem, 'empty'), kind='Bool'), kind='Bool')
    correct = g.op('and', valid, filled, kind='Bool')
    verdict = g.choose(valid, g.choose(filled, g.data('correct'), g.data('incomplete')), g.data('incorrect'))
    report = g.record(verdict=verdict, valid=g.op('bool_data', valid), filled=g.op('bool_data', filled),
                      correct=g.op('bool_data', correct), conflicts=conflicts)
    save('sudoku_check', g, g.op('emit', report, report, label='check_board'), trace_mode='explicit')

    g = Graph(); problem = g.call('sudoku_problem', g.input)
    result = g.call('finite_search', problem)
    valid = g.op('as_bool', g.get(result, 'found'), kind='Bool')
    save('sudoku_solver', g, g.op('require', valid, g.get(result, 'values'), message='The taught search found no solution for these entries. Correct or clear a value and try again.'), trace_mode='explicit',
         description='Read taught symbols; obtain taught groups and alphabet; execute stored candidate and stack-search programs.')

    # Input procedure is itself a taught sequence of the primitive controls.
    suite['sudoku_input'] = {'graph': json.loads((Path(__file__).parent / 'examples/type_at.graph.json').read_text()),
                              'source': 'Explicit Sudoku input lesson: move, click, type, observe feedback'}
    write = Graph(); ctx = write.get(write.input, 'context'); index = write.get(write.input, 'item')
    mark = write.op('item', write.get(ctx, 'marks'), index)
    value = write.op('item', write.get(ctx, 'values'), index)
    original = write.call('sudoku_symbol', write.get(mark, 'text'))
    key = write.op('text', value)
    feedback = write.call('sudoku_input', write.record(x=write.get(mark, 'x'), y=write.get(mark, 'y'), key=key))
    accepted = write.op('as_bool', write.get(feedback, 'accepted'), kind='Bool')
    checked = write.op('require', accepted, feedback)
    action = write.choose(write.eq(original, value), write.data({'unchanged': True}), checked)
    g = Graph(); marks = g.op('sort', g.op('sort', g.get(g.input, 'marks'), key='x'), key='y')
    values = g.call('sudoku_solver', g.input)
    results = g.map(g.op('indices', values), write.finish(action), g.record(marks=marks, values=values))
    save('sudoku_do', g, results, trace_mode='explicit', description='Solve through stored programs and enter changed symbols using the taught input sequence.')

    # The entire observe/reason/act/observe/check cycle is executable data too.
    for name, target in [('sudoku_observe_check', 'sudoku_check'), ('sudoku_observe_solve', 'sudoku_do')]:
        g = Graph(); scene = g.op('observe', g.input, surface='canvas')
        outcome = g.call(target, scene)
        if target == 'sudoku_do':
            fresh = g.op('observe', outcome, surface='canvas')
            outcome = g.call('sudoku_check', fresh)
        save(name, g, outcome, trace_mode='explicit')
    g=G(); scene=g.op('observe',g.input,surface='canvas')
    save('sudoku_observe_read',g,g.call('sudoku_read',scene),trace_mode='explicit')
    g=G(); scene=g.op('observe',g.input,surface='canvas'); problem=g.call('sudoku_problem',scene)
    index=g.calc('add',g.calc('multiply',g.get(g.input,'row'),g.data(9)),g.get(g.input,'col'))
    values=g.op('set_item',g.get(problem,'values'),index,g.get(problem,'empty'))
    save('sudoku_query_candidates',g,g.call('finite_candidates',g.record(problem=problem,values=values,index=index)),trace_mode='explicit',description='Read the canvas, convert a zero-based row/column to an index, temporarily clear that value, and compute allowed symbols from the taught constraints.')
    suite['sudoku_observe_solve']['graph']['skill']={'requires':['sudoku_canvas'],'provides':['filled_sudoku_canvas']}
    suite['sudoku_observe_solve']['graph']['description']='Solve the visible Sudoku using taught reasoning and canvas input methods, then check the board.'
    g=G(); scene=g.op('observe',g.input,surface='canvas'); report=g.call('sudoku_check',scene)
    save('sudoku_goal_check',g,g.boolean(g.get(report,'correct')),'Bool',trace_mode='explicit',description='Observe the board again and check correctness using the taught Sudoku rules.')
    return suite


if __name__ == '__main__':
    path = Path(__file__).parent / 'curriculum' / 'sudoku.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(build(), indent=2) + '\n')
    print(path)
