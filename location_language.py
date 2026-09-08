"""Explicit language-interface templates, not learned geographic knowledge."""
import re
from semantics import operation


def direct_location(text, entities=()):
    candidate = re.sub(r'^(?:so,?\s+)', '', text.strip(), flags=re.I).rstrip('.!?')
    # Only a single affirmative type-and-location clause. Anything more complex
    # goes through contextual translation; never flatten negation or modality.
    match = re.fullmatch(r'(.+?) is an? ([a-zA-Z-]+) (?:in|on) (.+)', candidate)
    if match and not re.search(r'\b(if|not|maybe|possibly|probably|and|or|said|says|would|could)\b|["“”]', candidate, re.I):
        subject, kind, target = match.groups()
        if not subject[0].isupper() or not (target[0].isupper() or target.startswith('the ')):
            return None
        operations = [operation('assert', subject, 'is', kind.lower())]
        typed = re.fullmatch(r'the ([a-zA-Z-]+) ([A-Z].+)', target)
        if typed:
            target_kind, target = typed.groups()
            operations.append(operation('assert', target, 'is', target_kind.lower()))
        operations.append(operation('assert', subject, 'located in', target))
        return {'operations': operations}
    match = re.fullmatch(r'(?:what|which) places are (?:located )?in (.+)', candidate, re.I)
    if match:
        target = match[1]
        # A unique one-character omission is a visible spelling resolution only.
        exact = next((e for e in entities if e.casefold() == target.casefold()), None)
        options = [e for e in entities if len(e) == len(target) + 1 and
                   any(e[:i].casefold() + e[i+1:].casefold() == target.casefold() for i in range(len(e)))]
        target = exact or (options[0] if len(options) == 1 else target)
        return {'operations': [operation('find', relation='located in', obj=target)]}
    return None
