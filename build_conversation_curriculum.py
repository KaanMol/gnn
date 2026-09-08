"""Author dialogue policies as portable graph lessons; never imported at runtime."""
import json
from pathlib import Path

from algebra import syntax
from graph_dsl import G


def build():
    suite = {}

    def save(name, g, out, description):
        suite[name] = {'graph': g.finish(out, trace_mode='explicit', description=description),
                       'source': 'Explicit conversation teaching: ' + description}

    for action in ('say', 'ask', 'wait'):
        g = G()
        save('dialogue_' + action, g, g.op('act', g.input, g.input, surface='dialogue', action=action),
             {'say': 'Display supplied text through the dialogue port.',
              'ask': 'Ask supplied text and retain the taught continuation name and state for the next input.',
              'wait': 'Retain a continuation and state, without asking a question, until input arrives.'}[action])

    lessons = []
    for title, explanation, hint, example, quiz in [
        ('Undo multiplication',
         'An equation says two expressions have the same value. To keep that equality, do the same operation to both sides. If a nonzero coefficient multiplies x, divide both sides by it.',
         'Divide both sides by the coefficient multiplying x.', '5*x=20', '3*x=12'),
        ('Undo addition',
         'To isolate x when a number is added to it, subtract that number from both sides. Adding and subtracting the same number are inverse operations.',
         'Subtract the number added to x from both sides.', 'x+7=12', 'x+9=15'),
        ('Collect terms',
         'Distribute multiplication across parentheses, collect like terms, and move variable terms to one side using the same operation on both sides. Then isolate x.',
         'Expand the parentheses first, subtract x from both sides, then remove the constant.',
         '3*(2*x-5)=4*x+7', '2*(x+3)=x+10')]:
        lessons.append({'title': title, 'explanation': explanation, 'hint': hint,
                        'example': example, 'example_input': syntax(example, True)[2],
                        'quiz': quiz, 'quiz_input': syntax(quiz, True)[2], 'method': 'algebra_solve'})
    g = G()
    save('course_algebra', g, g.data(lessons),
         'A teacher-authored introduction to linear equations, with explanations and exercises. Answers are computed by the current stored solver, not supplied here.')
    g = G()
    save('tutor_catalog', g, g.data({'algebra': 'course_algebra'}), 'Map a requested subject to its taught course.')

    # Run an example or exercise through its named stored method. A failure is
    # ordinary data for the caller's taught policy, not a native tutor fallback.
    body = G()
    result = body.op('invoke', body.get(body.input, 'method'), body.get(body.input, 'argument'))
    roots = body.get(result, 'roots')
    single = body.both(body.inverse(body.eq(roots, body.data([]))), body.eq(body.op('slice', roots, start=1), body.data([])))
    valid = body.both(body.boolean(body.get(result, 'complete')), single)
    result = body.op('require', valid, result,
                     message='This course needs a complete solution with one root from its taught method.')
    result = body.op('emit', result, body.record(input=body.get(body.input, 'argument'), result=result),
                     label='tutor_worked_solution')
    g = G()
    save('tutor_solve', g, g.op('attempt', g.input, body=body.finish(result)),
         'Execute the selected solver and retain its evidence. Return an explicit failure if the method is missing or cannot completely solve a course exercise.')

    g = G()
    prompt = g.textcat(g.data('I am stuck: '), g.get(g.input, 'error'),
                      g.data('\nCan you supply or repair that lesson? Then reply retry. You can also say stop.'))
    state = g.record(remaining=g.get(g.input, 'remaining'), prefix=g.data(''), mode=g.data('blocked'))
    save('tutor_stuck', g, g.call('dialogue_ask', g.record(text=prompt, resume=g.data('tutor_reply'), state=state)),
         'When a required method fails, ask for teaching and retain the unfinished course; never invent an answer.')

    g = G()
    remaining = g.get(g.input, 'remaining')
    lesson = g.item(remaining, g.data(0))
    solution = g.call('tutor_solve', g.record(method=g.get(lesson, 'method'), argument=g.get(lesson, 'example_input')))
    root = g.op('text', g.item(g.get(solution, 'result', 'roots'), g.data(0)))
    text = g.textcat(g.get(g.input, 'prefix'), g.get(lesson, 'title'), g.data('\n'), g.get(lesson, 'explanation'),
                     g.data('\nWorked example: '), g.get(lesson, 'example'), g.data(' → x = '), root,
                     g.data('\nThe example was executed with the current stored algebra lessons.'),
                     g.data('\nYour turn: '), g.get(lesson, 'quiz'),
                     g.data('\nWhat is x? Reply with a number, x=number, help, or stop.'))
    ask = g.call('dialogue_ask', g.record(text=text, resume=g.data('tutor_reply'),
                 state=g.record(remaining=remaining, prefix=g.data(''), mode=g.data('quiz'))))
    stuck = g.call('tutor_stuck', g.record(remaining=remaining, error=g.get(solution, 'error')))
    complete = g.call('dialogue_say', g.record(text=g.textcat(g.get(g.input, 'prefix'),
         g.data('You finished this taught introduction: undo multiplication, undo addition, and collect terms. This is a short linear-equation course; more topics need more teaching lessons.'))))
    out = g.choose(g.eq(remaining, g.data([])), complete, g.choose(g.boolean(g.get(solution, 'ok')), ask, stuck))
    save('tutor_question', g, out, 'Choose the next course example, execute its solver, explain the supplied principle and ask an exercise; stop at the end or ask for missing knowledge.')

    body = G()
    text = body.op('lower', body.get(body.input, 'input'))
    text = body.op('replace_text', text, body.data(' '), body.data(''))
    parts = body.op('split_text', text, body.data('='))
    two_parts = body.both(body.inverse(body.eq(body.op('slice', parts, start=1), body.data([]))),
                           body.eq(body.op('slice', parts, start=2), body.data([])))
    is_assignment = body.both(two_parts, body.eq(body.item(parts, body.data(0)), body.data('x')))
    answer = body.choose(is_assignment, body.item(parts, body.data(1)), text)
    answer = body.op('invoke', body.data('number_parse'), answer)
    state = body.get(body.input, 'state')
    lesson = body.item(body.get(state, 'remaining'), body.data(0))
    solution = body.op('invoke', body.get(lesson, 'method'), body.get(lesson, 'quiz_input'))
    roots = body.get(solution, 'roots')
    single = body.both(body.inverse(body.eq(roots, body.data([]))), body.eq(body.op('slice', roots, start=1), body.data([])))
    valid = body.both(body.boolean(body.get(solution, 'complete')), single)
    solution = body.op('require', valid, solution, message='The taught method did not produce one complete exercise answer.')
    correct = body.op('invoke', body.data('number_equal'), body.record(a=answer, b=body.op('text', body.item(body.get(solution, 'roots'), body.data(0)))))
    result = body.record(correct=correct, solution=solution, answer=answer)
    result = body.op('emit', result, result, label='tutor_check_answer')
    g = G()
    save('tutor_check', g, g.op('attempt', g.input, body=body.finish(result)),
         'Interpret the reply using taught numeric parsing, solve the current exercise, and compare through taught equality; retain the actual check evidence.')

    g = G()
    s = g.get(g.input, 'state'); remaining = g.get(s, 'remaining')
    lesson = g.item(remaining, g.data(0))
    reply = g.op('lower', g.op('replace_text', g.get(g.input, 'input'), g.data(' '), g.data('')))
    stop = g.op('contains', g.data(['stop', 'cancel', 'quit']), reply, kind='Bool')
    help_ = g.op('contains', g.data(['help', 'why', 'hint']), reply, kind='Bool')
    checked = g.call('tutor_check', g.input)
    retry_text = g.textcat(g.data('Try again. '), g.get(lesson, 'hint'), g.data('\n'), g.get(lesson, 'quiz'),
                           g.data('\nWhat is x? You can also say help or stop.'))
    retry = g.call('dialogue_ask', g.record(text=retry_text, resume=g.data('tutor_reply'), state=s))
    help_text = g.textcat(g.get(lesson, 'explanation'), g.data('\n'), g.get(lesson, 'hint'), g.data('\nYour turn: '),
                          g.get(lesson, 'quiz'))
    help_result = g.call('dialogue_ask', g.record(text=help_text, resume=g.data('tutor_reply'), state=s))
    invalid = g.call('dialogue_ask', g.record(text=g.textcat(g.data('I could not check that reply: '), g.get(checked, 'error'),
                  g.data('\nGive a number or x=number. If a lesson is missing, teach it and retry. You can also say stop.')),
                  resume=g.data('tutor_reply'), state=s))
    advance = g.call('tutor_question', g.record(remaining=g.op('slice', remaining, start=1), prefix=g.data('Correct.\n\n')))
    feedback = g.choose(g.boolean(g.get(checked, 'ok')),
                        g.choose(g.boolean(g.get(checked, 'result', 'correct')), advance, retry), invalid)
    blocked = g.eq(g.get(s, 'mode'), g.data('blocked'))
    resumed = g.call('tutor_question', s)
    stopped = g.call('dialogue_say', g.record(text=g.data('Stopped the lesson. Ask “teach me algebra” to start again.')))
    out = g.choose(stop, stopped, g.choose(blocked, resumed, g.choose(help_, help_result, feedback)))
    save('tutor_reply', g, out, 'Interpret stop/help/retry, check an answer, choose feedback and advance or ask again. All these choices and the next continuation are taught instructions.')

    g = G()
    course_name = g.item(g.call('tutor_catalog', g.input), g.get(g.input, 'topic'))
    course = g.op('invoke', course_name, g.data(None))
    save('tutor_start', g, g.call('tutor_question', g.record(remaining=course, prefix=g.data(''))),
         'Find the requested taught course and start its question/answer policy. New courses can reuse this behavior.')
    return suite


if __name__ == '__main__':
    destination = Path(__file__).parent / 'curriculum' / 'conversation.json'
    destination.write_text(json.dumps(build(), indent=2) + '\n')
