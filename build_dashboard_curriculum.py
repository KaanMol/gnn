"""Authoring only: graph lessons own dashboard content, schedules and dispatch."""
import copy
from graph_dsl import G


def build(library):
    suite = {}
    def save(name, g, output, description):
        suite[name] = {'graph': g.finish(output, trace_mode='explicit', description=description),
                       'source': 'Explicit dashboard teaching: ' + description}
    def read(g, namespace, key):
        return g.op('act', g.input, g.record(namespace=g.data(namespace), key=key), surface='workspace', action='read')
    def write(g, namespace, key, value):
        return g.op('act', g.input, g.record(namespace=g.data(namespace), key=key, value=value), surface='workspace', action='write')
    def attempt_read(g, namespace, key):
        body = G(); r = read(body, namespace, body.input)
        return g.op('attempt', key, body=body.finish(r))
    def interval(g, value):
        valid = g.both(g.op('is_integer', g.num(value), kind='Bool'), g.both(g.inverse(g.lt(value, g.data(60))), g.inverse(g.lt(g.data(31536000), value))))
        return g.op('require', valid, value, message='Choose a whole refresh interval between 60 seconds and one year.')
    def identifier(g, value):
        return g.op('lower', value)

    g = G(); key = identifier(g, g.get(g.input, 'id')); seconds = interval(g, g.get(g.input, 'refresh_seconds'))
    method = g.get(g.input, 'method'); definition = read(g, 'knowledge.procedures', method)
    method = g.op('require', g.has(definition, g.data('graph')), method, message='Teach that procedure before adding it to the dashboard.')
    old = attempt_read(g, 'skills.dashboard', key); empty = g.data(None)
    prior = g.choose(g.boolean(g.get(old, 'ok')), g.get(old, 'result'), empty)
    same = g.choose(g.eq(prior, empty), g.eq(key, empty), g.both(g.eq(g.get(prior, 'method'), method), g.eq(g.get(prior, 'argument'), g.get(g.input, 'argument'))), kind='Bool')
    now = g.get(g.op('observe', g.input, surface='clock'), 'unix_seconds')
    key = g.op('require', g.nonempty(g.op('characters', key)), key, message='Give the card a nonempty name.')
    card = g.record(id=key, title=g.get(g.input, 'title'), method=method, argument=g.get(g.input, 'argument'),
                    refresh_seconds=seconds, enabled=g.data(True), next_at=now, last_attempt=g.data(None), error=g.data(''),
                    result=g.choose(same, g.get(prior, 'result'), empty), last_success=g.choose(same, g.get(prior, 'last_success'), empty))
    saved = write(g, 'skills.dashboard', key, card)
    focus = write(g, 'skills.dashboard_state', g.data('last_id'), g.get(saved, 'after', 'id'))
    save('dashboard_add', g, g.record(text=g.textcat(g.data('Added '), g.get(saved, 'after', 'title'), g.data(' to the Dashboard. It refreshes while the server is running.')), id=g.get(focus, 'after')), 'Persist a card invoking an existing taught procedure. Store its input and refresh interval; preserve matching successful content when reconfiguring it. First refresh is due immediately.')

    g = G(); key = identifier(g, g.get(g.input, 'id')); card = read(g, 'skills.dashboard', key)
    body = G(); invoked = body.op('invoke', body.get(body.input, 'method'), body.get(body.input, 'argument'))
    attempt = g.op('attempt', card, body=body.finish(invoked)); ok = g.boolean(g.get(attempt, 'ok'))
    # Completion time depends on the invocation, avoiding immediate catch-up loops after slow calls.
    now = g.get(g.op('observe', attempt, surface='clock'), 'unix_seconds')
    value = g.put(card, 'result', g.choose(ok, g.get(attempt, 'result'), g.get(card, 'result')))
    value = g.put(value, 'last_success', g.choose(ok, now, g.get(card, 'last_success')))
    value = g.put(value, 'last_attempt', now)
    value = g.put(value, 'error', g.choose(ok, g.data(''), g.get(attempt, 'error')))
    delay = g.get(card, 'refresh_seconds'); delay = g.choose(g.both(g.inverse(ok), g.lt(delay, g.data(300))), g.data(300), delay)
    value = g.put(value, 'next_at', g.calc('add', now, delay))
    saved = write(g, 'skills.dashboard', key, value)
    save('dashboard_refresh', g, g.record(text=g.data(''), card=g.get(saved, 'after')), 'Invoke the stored card procedure and save its result. On failure keep the last successful content with an error and retry no faster than five minutes. Refreshes are silent in chat.')

    g = G(); key = identifier(g, g.get(g.input, 'id')); card = read(g, 'skills.dashboard', key)
    seconds = interval(g, g.get(g.input, 'refresh_seconds')); now = g.get(g.op('observe', g.input, surface='clock'), 'unix_seconds')
    updated = g.put(g.put(card, 'refresh_seconds', seconds), 'next_at', g.calc('add', now, seconds))
    saved = write(g, 'skills.dashboard', key, updated)
    save('dashboard_interval', g, g.record(text=g.textcat(g.data('Updated the refresh schedule for '), g.get(saved, 'after', 'title'), g.data('.')), card=g.get(saved, 'after')), 'Change a card schedule without discarding its content or resuming a paused card.')
    g = G(); key = read(g, 'skills.dashboard_state', g.data('last_id'))
    save('dashboard_interval_last', g, g.call('dashboard_interval', g.record(id=key, refresh_seconds=g.get(g.input, 'refresh_seconds'))), 'Resolve “it” in a refresh request to the most recently added dashboard card.')

    g = G(); key = identifier(g, g.get(g.input, 'id')); card = read(g, 'skills.dashboard', key)
    updated = g.put(card, 'enabled', g.get(g.input, 'enabled'))
    saved = write(g, 'skills.dashboard', key, updated)
    save('dashboard_enabled', g, g.record(text=g.data('Updated dashboard refresh setting.'), card=g.get(saved, 'after')), 'Pause or resume automatic refresh without deleting the last result.')
    g = G(); removed = g.op('act', g.input, g.record(namespace=g.data('skills.dashboard'), key=identifier(g, g.get(g.input, 'id'))), surface='workspace', action='delete')
    save('dashboard_remove', g, g.record(text=g.data('Removed that dashboard card.'), change=removed), 'Remove a card and its refresh schedule. The underlying skill stays in memory.')

    due = G(); card = due.get(due.input, 'item', 'value')
    ready = due.both(due.boolean(due.get(card, 'enabled')), due.inverse(due.lt(due.get(due.input, 'context'), due.get(card, 'next_at'))))
    g = G(); cards = g.op('act', g.input, g.record(namespace=g.data('skills.dashboard')), surface='workspace', action='entries')
    ready_cards = g.map(cards, due.finish(ready, 'Bool'), g.get(g.input, 'now'), filter=True)
    # Oldest deadline first avoids starving later cards behind a slow earlier card.
    # General runtime sort orders records by a named field; sort via next_at wrapper below.
    row = G(); wrapped = row.record(next_at=row.get(row.input, 'value', 'next_at'), id=row.get(row.input, 'value', 'id'))
    ordered = g.op('sort', g.map(ready_cards, row.finish(wrapped)), key='next_at')
    chosen = g.get(ordered, 0)
    result = g.call('dashboard_refresh', g.record(id=g.get(chosen, 'id')))
    save('dashboard_tick', g, g.choose(g.boolean(g.get(g.input, 'waiting')), g.data(None), g.choose(g.nonempty(ready_cards), result, g.data(None))), 'On each timer signal refresh at most one due card, oldest deadline first. Defer during a pending dialogue. Deadlines remain in graph memory across restarts.')
    base = 'background_tick_before_dashboard'; suite[base] = copy.deepcopy(library.get(base, library['background_tick']))
    g = G(); old = g.call(base, g.input); current = g.call('dashboard_tick', g.put(g.input, 'previous', old))
    save('background_tick', g, g.choose(g.eq(current, g.data(None)), old, old), 'Run existing background routines and one due dashboard card. Dashboard results are stored in cards, not announced on every refresh.')

    g = G(); clock = g.op('observe', g.input, surface='clock')
    save('dashboard_date', g, g.record(value=g.get(clock, 'date'), text=g.data('Local date'), unit=g.get(clock, 'timezone')), 'Read the date and timezone from the generic clock interface for a dashboard card.')

    # Weather is a recipe using an explicitly chosen page, not a native weather adapter.
    g = G(); seconds = interval(g, g.get(g.input, 'refresh_seconds'))
    favorite = attempt_read(g, 'skills.web_favorites', g.data('weather'))
    add = g.call('dashboard_add', g.record(id=g.data('weather'), title=g.data("Today's weather"), method=g.data('web_weather_read'), argument=g.record(url=g.get(favorite, 'result', 'url')), refresh_seconds=seconds))
    ask = g.call('dialogue_ask', g.record(text=g.data('Which weather page should this card refresh? Paste its public URL. The current reader understands wttr.in pages. Reply cancel to stop.'), resume=g.data('dashboard_weather_reply'), state=g.record(refresh_seconds=seconds)))
    save('dashboard_weather', g, g.choose(g.boolean(g.get(favorite, 'ok')), add, ask), 'Create a weather card from the explicitly saved weather favorite, or ask for a page. Carry the requested refresh interval through the clarification.')
    g = G(); text = g.get(g.input, 'input')
    add = g.call('dashboard_add', g.record(id=g.data('weather'), title=g.data("Today's weather"), method=g.data('web_weather_read'), argument=g.record(url=text), refresh_seconds=g.get(g.input, 'state', 'refresh_seconds')))
    save('dashboard_weather_reply', g, g.choose(g.eq(g.op('lower', text), g.data('cancel')), g.record(text=g.data('Cancelled adding the weather card.')), add), 'Bind the supplied page URL to the card. If its layout cannot be read, the card shows an error rather than inventing weather.')

    # Explicit reusable language patterns are taught graphs; Gemma remains fallback.
    g = G(); text = g.op('lower', g.get(g.input, 'text'))
    for before, after in [('’', "'"), ('?', ''), ('.', ''), (' to my dashboard', ''), (' to the dashboard', ''), (' and refresh it', ''), (', refresh it', ''), (' refresh it', '')]:
        text = g.op('replace_text', text, g.data(before), g.data(after))
    parts = g.op('split_text', text, g.data(' every ')); subject = g.get(parts, 0)
    units = G(); pieces = units.op('split_text', units.input, units.data(' ')); amount = units.op('as_data', units.num(units.get(pieces, 0))); unit = units.get(pieces, 1)
    multiplier = units.choose(units.op('contains', units.data(['second', 'seconds']), unit, kind='Bool'), units.data(1), units.choose(units.op('contains', units.data(['minute', 'minutes']), unit, kind='Bool'), units.data(60), units.choose(units.op('contains', units.data(['hour', 'hours']), unit, kind='Bool'), units.data(3600), units.data(0))))
    seconds = units.calc('multiply', amount, multiplier)
    save('dashboard_duration', units, interval(units, seconds), 'Interpret N seconds, N minutes or N hours using taught arithmetic and constrain automatic refresh intervals.')
    seconds = g.choose(g.eq(g.length(parts), g.data(2)), g.call('dashboard_duration', g.get(parts, 1)), g.data(3600))
    weather = g.op('contains', g.data(["add today's weather", 'add todays weather', 'add weather', 'show weather on my dashboard']), subject, kind='Bool')
    follow = g.op('contains', g.data(['refresh it', 'refresh weather', 'refresh the weather']), subject, kind='Bool')
    request = g.record(kind=g.data('graph_run'), name=g.data('dashboard_weather'), argument=g.record(refresh_seconds=seconds))
    change = g.record(kind=g.data('graph_run'), name=g.choose(g.eq(subject, g.data('refresh it')), g.data('dashboard_interval_last'), g.data('dashboard_interval')), argument=g.record(id=g.data('weather'), refresh_seconds=seconds))
    result = g.choose(weather, request, g.choose(g.both(follow, g.eq(g.length(parts), g.data(2))), change, g.data(None)))
    save('dashboard_interpret', g, result, 'Recognize adding weather to the dashboard with an optional refresh interval, and follow-up refresh requests. Other skills can be added using the generic card interface.')
    base = 'behavior_interpret_before_dashboard'; suite[base] = copy.deepcopy(library.get(base, library['behavior_interpret']))
    g = G(); found = g.call('dashboard_interpret', g.input)
    save('behavior_interpret', g, g.choose(g.eq(found, g.data(None)), g.call(base, g.input), found), 'Try taught dashboard language patterns, then preserve the previous conversation interpreter.')
    return suite
