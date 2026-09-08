"""Structured symbolic memory with explicit negation and retractable assertions."""
from meaning import ConceptCategory, LanguageError, MeaningSystem, parse
from graph_store import GraphStore, atomic_graph
import foundation


def stored_map(name):
    return property(lambda self: self.store.map(self.prefix + '.' + name),
                    lambda self, value: self.store.map(self.prefix + '.' + name).replace(value))


def derived_map(name):
    def read(self):
        self._ensure_current()
        return self.store.map(self.prefix + '.' + name)
    return property(read, lambda self, value: self.store.map(self.prefix + '.' + name).replace(value))


def label(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 160:
        raise LanguageError("Please give that person, thing, or property a short, explicit name.")
    return " ".join(value.split())


def fact_text(fact, negative=False):
    relation, subject, obj = fact
    if relation == "is":
        return f"{subject} is {'not ' if negative else ''}a {obj}."
    if relation == "age":
        return f"{subject} is {'not ' if negative else ''}{obj} years old."
    if relation == 'described as':
        return f"{subject} is {'not ' if negative else ''}described as {obj}."
    if negative:
        return f"{subject} does not {relation} {obj}."
    verb = {"like": "likes", "live in": "lives in", "grow": "grows", "have": "has",
            "own": "owns", "work at": "works at", "teach": "teaches"}.get(relation, relation)
    return f"{subject} {verb} {obj}."


class Knowledge(MeaningSystem):
    fields = ('assertions', 'facts', 'negatives', 'subtypes', 'rules', 'symmetric',
              'procedures', 'sudoku_lessons', 'math_lessons', 'definitions', 'executions', 'hypotheses')
    assertions = stored_map('assertions')
    facts = derived_map('facts')
    negatives = derived_map('negatives')
    subtypes = stored_map('subtypes')
    rules = stored_map('rules')
    symmetric = stored_map('symmetric')
    procedures = property(lambda self: self.store.map('knowledge.procedures'),
                          lambda self, value: self.store.map('knowledge.procedures').replace(value))
    sudoku_lessons = stored_map('sudoku_lessons')
    math_lessons = stored_map('math_lessons')
    definitions = stored_map('definitions')
    executions = stored_map('executions')
    hypotheses = stored_map('hypotheses')

    def __init__(self, store=None, prefix='knowledge'):
        self.store = store if store is not None else foundation.new_learning_store()
        self.prefix = prefix
        self.statements = self.store.sequence(prefix + '.statements')
        self.rebuild()

    def _source_signature(self):
        return tuple(tuple(self.store.map(self.prefix + '.' + name)._rows())
                     for name in ('assertions', 'subtypes', 'rules', 'symmetric', 'hypotheses')) + (tuple(self.procedures._rows()),)

    def _ensure_current(self):
        if not getattr(self, '_rebuilding', False) and self._source_signature() != self._source_version:
            self.rebuild()

    @property
    def entities(self):
        self._ensure_current()
        return self._entities

    @entities.setter
    def entities(self, value):
        self._entities = value

    @property
    def category(self):
        self._ensure_current()
        return self._category

    @category.setter
    def category(self, value):
        self._category = value

    def __deepcopy__(self, memo):
        self._ensure_current()
        namespaces = [self.prefix + '.' + name for name in self.fields + ('statements',)]
        if 'knowledge.procedures' not in namespaces:
            namespaces.append('knowledge.procedures')
        other = object.__new__(Knowledge)
        other.store = self.store.clone_namespaces(namespaces)
        other.prefix = self.prefix
        other.statements = other.store.sequence(self.prefix + '.statements')
        other._copy_materialized_state(self)
        return other

    def _copy_materialized_state(self, other):
        """Reuse proven results only alongside their exact source roots."""
        if self._source_signature() != other._source_version:
            self.rebuild()
            return
        self._entities = set(other._entities)
        self._category = TaughtCategory(self, other._category.objects,
            [{'sub': a, 'parent': b} for a, b in other._category.generators])
        self.reasoning_error = other.reasoning_error
        self.last_trace = getattr(other, 'last_trace', [])
        self._source_version = self._source_signature()

    def invoke(self, name, argument):
        result, self.last_trace = foundation.run(self.procedures, name, argument)
        self.executions[name] = {'procedure': name, 'input': argument, 'result': result,
                                 'trace': self.last_trace, 'program_roots': self.procedures._rows()}
        return result

    def evidence(self):
        def rows(mapping):
            return [{'fact': list(f), 'source': source, 'premises': [list(p) for p in premises]}
                    for f, (source, premises) in mapping.items()]
        return {'facts': rows(self.facts), 'negatives': rows(self.negatives)}

    def adopt(self, other):
        """Commit staged knowledge without detaching history or sensor views."""
        other._ensure_current()
        with self.store.transaction():
            for name in self.fields:
                # Access storage views directly. Derived-property getters here
                # would rebuild half-committed knowledge for a second time.
                namespace = 'knowledge.procedures' if name == 'procedures' else self.prefix + '.' + name
                destination, source = self.store.map(namespace), other.store.map(namespace)
                if destination._rows() != source._rows():
                    destination.replace(source.to_dict())
            self.statements.replace(other.statements)
            self._copy_materialized_state(other)

    def entity(self, name):
        name = label(name)
        if 'meaning_reference' in self.procedures:
            name = self.invoke('meaning_reference', name)
        return next((e for e in self.entities if e.casefold() == name.casefold()), name)

    @atomic_graph
    def rename_entity(self, old, new, source):
        """Persist the policy revision computed by the taught name-change method."""
        result = self.invoke('meaning_rename_reference', {
            'old': label(old), 'new': label(new), 'source': source,
            'entities': sorted(self.entities)})
        entry = result['entry']
        foundation.validate_graph(entry['graph'], self.procedures)
        self.procedures['meaning_reference_policy'] = entry
        self.rebuild()
        if self.reasoning_error:
            raise LanguageError(self.reasoning_error)
        return result

    @atomic_graph
    def separate_person_city(self, name, source):
        rows = [{'fact': list(f), 'negative': negative, 'source': evidence}
                for (f, negative), evidence in self.assertions.items()]
        result = self.invoke('meaning_separate_person_city',
                             {'name': label(name), 'assertions': rows, 'source': source})
        entry = result['entry']
        foundation.validate_graph(entry['graph'], self.procedures)
        self.procedures['meaning_policy'] = entry
        self.rebuild()
        if self.reasoning_error:
            raise LanguageError(self.reasoning_error)
        return result

    def triple(self, subject, relation, obj):
        relation = label(relation).lower()
        obj = label(obj).lower() if relation == "is" else self.entity(obj)
        fact = (relation, self.entity(subject), obj)
        if 'meaning_fact' in self.procedures:
            fact = tuple(self.invoke('meaning_fact',list(fact)))
        return fact

    @atomic_graph
    def assert_fact(self, subject, relation, obj, negative, source):
        fact = self.triple(subject, relation, obj)
        if 'meaning_fact_reference_question' in self.procedures:
            question = self.invoke('meaning_fact_reference_question', list(fact))
            if question:
                raise LanguageError(question)
        self.assertions[(fact, negative)] = source
        self.rebuild()
        if fact in self.facts and fact in self.negatives:
            return "I now have conflicting evidence about " + fact_text(fact) + " Please correct the claim that is wrong."
        return "Learned: " + fact_text(fact, negative)

    @atomic_graph
    def retract(self, subject, relation, obj, negative):
        fact = self.triple(subject, relation, obj)
        keys = [(fact, negative)] if (fact, negative) in self.assertions else []
        if 'meaning_retraction_keys' in self.procedures:
            raw = [{'fact':list(f),'negative':n,'source':s} for (f,n),s in self.assertions.items()]
            keys = [(tuple(f),n) for f,n in self.invoke('meaning_retraction_keys',{'assertions':raw,'fact':list(fact),'negative':negative})]
        if not keys:
            if fact in (self.negatives if negative else self.facts):
                raise LanguageError("That conclusion follows from other knowledge. Which supporting fact or definition should I correct?")
            raise LanguageError("I couldn't find that exact assertion to remove. Which stored claim did you mean?")
        for key in keys:
            del self.assertions[key]
        self.rebuild()
        result = "Removed: " + fact_text(fact, negative)
        if fact in (self.negatives if negative else self.facts):
            result += " It still follows from other knowledge."
        return result

    @atomic_graph
    def define(self, concept, conditions, source, replace=False):
        concept = label(concept).lower()
        if not isinstance(conditions, list) or not 1 <= len(conditions) <= 6:
            raise LanguageError("Describe the concept using one to six properties or relationships.")
        compiled = []
        for condition in conditions:
            if not isinstance(condition, dict) or set(condition) != {"relation", "object", "target_type"}:
                raise LanguageError("I couldn't identify the conditions of that definition. What must an example satisfy?")
            relation = label(condition["relation"]).lower()
            if type(condition["target_type"]) is not bool:
                raise LanguageError("Is that condition about a particular object or a type of object?")
            obj = label(condition["object"])
            if relation == "is" or condition["target_type"]:
                obj = obj.lower()
            else:
                obj = self.entity(obj)
            compiled.append((relation, obj, condition["target_type"]))
        if concept in self.rules and self.rules[concept][0] != compiled and not replace:
            raise LanguageError(f"I already have a definition of {concept}. Do you want to replace it?")
        if replace and concept not in self.rules:
            raise LanguageError(f"I don't yet have a definition of {concept} to replace. What should it mean?")
        self.rules[concept] = (compiled, source)
        self.rebuild()
        return ("Updated definition: " if replace else "Learned definition: ") + self.definition_text(concept)

    def definition_text(self, concept):
        conditions = self.rules[concept][0]
        terms = [f"is a {obj}" if relation == "is" else
                 f"{relation} {'a ' if target_type else ''}{obj}"
                 for relation, obj, target_type in conditions]
        return concept + " means something that " + " and ".join(terms) + "."

    def rebuild(self):
        with self.store.transaction():
            self._rebuilding = True
            try:
                self._rebuild()
                self._source_version = self._source_signature()
            finally:
                self._rebuilding = False

    def _rebuild(self):
        assertions = [{'fact': list(fact), 'negative': negative, 'source': source}
                      for (fact, negative), source in self.assertions.items()]
        argument = {'assertions': assertions,
                    'hypotheses': list(self.hypotheses.values()),
                    'subtypes': [{'sub': a, 'parent': b, 'source': source} for (a, b), source in self.subtypes.items()],
                    'symmetric': [{'relation': r, 'source': source} for r, source in self.symmetric.items()],
                    'definitions': [{'concept': c, 'conditions': foundation.data(conditions), 'source': source}
                                    for c, (conditions, source) in self.rules.items()]}
        try:
            result = self.invoke('knowledge_rebuild', argument)
            self.reasoning_error = None
        except ValueError as error:
            if not foundation.missing_method(error):
                raise
            # Without inference lessons, expose the directly stored assertions.
            # Never retain stale deductions or regenerate an absent method.
            result = {'facts': [], 'negatives': [], 'entities': [], 'concepts': [], 'generators': []}
            for record in assertions:
                result['negatives' if record['negative'] else 'facts'].append(
                    {'fact': record['fact'], 'source': record['source'], 'premises': []})
            self.reasoning_error = str(error)
        self.facts = {tuple(r['fact']): (r['source'], tuple(tuple(p) for p in r['premises'])) for r in result['facts']}
        self.negatives = {tuple(r['fact']): (r['source'], tuple(tuple(p) for p in r['premises'])) for r in result['negatives']}
        self.entities = set(result['entities'])
        self.category = TaughtCategory(self, result['concepts'], result['generators'])

    @atomic_graph
    def symmetry(self, relation, source, remove=False):
        relation = label(relation).lower()
        if relation == "is":
            raise LanguageError("Type membership is not a relationship between two entities. Which relationship should be mutual?")
        if remove:
            if relation not in self.symmetric:
                raise LanguageError("I haven't learned that mutual-relationship rule yet.")
            del self.symmetric[relation]
            answer = f"Removed the rule that {relation} is mutual."
        else:
            self.symmetric[relation] = source
            answer = f"Learned rule: if A {relation} B, then B {relation} A."
        self.rebuild()
        return answer

    def query(self, subject, relation, obj, negative=False):
        fact = self.triple(subject, relation, obj)
        if 'meaning_fact_reference_question' in self.procedures:
            question = self.invoke('meaning_fact_reference_question', list(fact))
            if question:
                return question
        if 'meaning_reference_question' in self.procedures:
            question = self.invoke('meaning_reference_question',fact[1])
            if question:
                return question
        status = self.invoke('knowledge_query', {**self.evidence(), 'fact': list(fact), 'negative': negative})
        if status == 'conflict':
            return "Conflicting evidence: I have support for both " + fact_text(fact) + " and its negation."
        if status == 'unknown':
            return "Unknown: I haven't learned enough to answer that."
        answer = "Yes." if status == 'yes' else "No."
        proof = self.negatives[fact][0] if fact in self.negatives else "\n".join(self.explain(fact))
        return answer + "\nBased on: " + proof

    def explain(self, fact, depth=0):
        rows = self.invoke('knowledge_explain', {**self.evidence(), 'fact': list(fact)})
        return ['  ' * (depth + row['depth']) + row['source'] for row in rows]

    def find(self, relation, obj, concept=""):
        relation, obj = label(relation).lower(), self.entity(obj)
        concept = concept.strip().lower()
        result = self.invoke('knowledge_find', {**self.evidence(), 'relation': relation, 'object': obj, 'concept': concept})
        matches = [fact_text(tuple(f)) for f in result['matches']]
        conflicts = [f[1] for f in result['conflicts']]
        answer = "\n".join(matches) if matches else "I haven't learned matching relationships yet."
        if conflicts:
            answer += "\nConflicting evidence excluded: " + ", ".join(conflicts) + "."
        return answer

    def describe(self, subject, relation=""):
        subject = self.entity(subject)
        if 'meaning_reference_question' in self.procedures:
            question = self.invoke('meaning_reference_question',subject)
            if question:
                return question
        relation = relation.strip().lower()
        if subject.lower() in self.rules and not relation:
            return self.definition_text(subject.lower())
        result = self.invoke('knowledge_describe', {**self.evidence(), 'subject': subject, 'relation': relation})
        if isinstance(result.get('text'), str):
            return result['text']
        rows = [fact_text(tuple(r['fact'])) for r in result['facts']]
        rows += [fact_text(tuple(r['fact']), True) for r in result['negatives']]
        if not rows and not relation:
            rows = [f"Every {a} is a {b}." for a, b in self.category.arrows() if a == subject.lower() and a != b]
        return "\n".join(rows) if rows else "I haven't learned that yet. You can teach me."

    @atomic_graph
    def tell(self, statement):
        # Legacy saved notebooks and the old CLI only. New language operations
        # call assert_fact/define/query directly and never round-trip through text.
        kind, args = parse(statement)
        if kind == "instance":
            answer = self.assert_fact(args[0], "is", args[1], False, statement)
        elif kind == "relation":
            answer = self.assert_fact(args[0], args[1], args[2], False, statement)
        elif kind == "subtype":
            self.subtypes[args] = statement
            self.rebuild()
            answer = "Learned: " + statement
        else:
            concept, base, relation, target = args
            answer = self.define(concept, [{"relation": "is", "object": base, "target_type": False},
                                           {"relation": relation, "object": target, "target_type": True}], statement)
        self.statements.append(statement)
        return answer

    def ask(self, question):
        # Legacy questions remain replayable; structured queries use query/describe.
        import re
        text = question.strip().rstrip("?")
        match = re.fullmatch(r"What is an? (\w+)", text)
        if match:
            return self.describe(match[1])
        match = re.fullmatch(r"(?:Is|Why is) ([A-Z]\w*) an? (\w+)", text)
        if match:
            return self.query(match[1], "is", match[2])
        match = re.fullmatch(r"What is ([A-Z]\w*)", text)
        if match:
            return self.describe(match[1])
        return super().ask(question)


class TaughtCategory(ConceptCategory):
    """Presentation of the graph's inclusion relation, with taught closure."""
    def __init__(self, knowledge, objects, generators):
        self.knowledge = knowledge
        self.objects = set(objects)
        self.generators = {(r['sub'], r['parent']) for r in generators}
        self.objects.update(v for pair in self.generators for v in pair)

    def arrows(self):
        result = self.knowledge.invoke('relation_closure', {'objects': sorted(self.objects), 'edges': [list(e) for e in sorted(self.generators)]})
        return {tuple(pair) for pair in result}
