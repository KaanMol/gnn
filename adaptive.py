"""Inspectable concept induction from graph features and labeled examples."""
from itertools import combinations


class AdaptiveLearner:
    """Learn minimal consistent conjunctions in a finite hypothesis space.

    Hypotheses are recomputed from current evidence. Predictions never become
    graph facts or training labels automatically.
    """

    def __init__(self, graph):
        self.graph = graph
        self.examples = {}

    def teach(self, concept, entity, positive):
        if entity not in self.graph.entities:
            raise ValueError("Describe this entity in the graph before labeling it.")
        self.examples.setdefault(concept.lower(), {})[entity] = bool(positive)

    def features(self, entity, excluded):
        # Exclude the target and its subtypes to prevent direct label leakage.
        excluded_types = {excluded} | {a for a, b in self.graph.category.arrows() if b == excluded}
        result = set()
        for relation, subject, target in self.graph.facts:
            if subject != entity:
                continue
            if relation == "is":
                if target not in excluded_types:
                    result.add(("type", target))
            else:
                for rel, obj, kind in self.graph.facts:
                    if rel == "is" and obj == target and kind not in excluded_types:
                        result.add(("relation", relation, kind))
        return result

    def hypotheses(self, concept):
        concept = concept.lower()
        examples = self.examples.get(concept, {})
        positives = [self.features(e, concept) for e, label in examples.items() if label]
        negatives = [self.features(e, concept) for e, label in examples.items() if not label]
        if len(positives) < 2 or not negatives:
            return [], "Need at least two positive examples and one negative example."
        common = sorted(set.intersection(*positives))
        if len(common) > 40:
            return [], "Feature budget exceeded; narrow the example descriptions."
        hypotheses = []
        for size in range(1, min(3, len(common)) + 1):
            for terms in combinations(common, size):
                candidate = frozenset(terms)
                if any(h <= candidate for h in hypotheses):
                    continue
                if all(not candidate <= features for features in negatives):
                    hypotheses.append(candidate)
        if not hypotheses:
            return [], "No consistent rule in the current hypothesis space; earlier hypotheses are withdrawn."
        return hypotheses, "Provisional rules consistent with the supplied examples."

    @staticmethod
    def describe(hypothesis):
        return " AND ".join("is a " + f[1] if f[0] == "type"
                            else f[1] + " a " + f[2] for f in sorted(hypothesis))

    def inspect(self, concept):
        hypotheses, reason = self.hypotheses(concept)
        return reason + "".join("\n- " + self.describe(h) for h in hypotheses)

    def predict(self, concept, entity):
        if entity not in self.graph.entities:
            return "Unknown entity."
        hypotheses, reason = self.hypotheses(concept)
        if not hypotheses:
            return "Unknown. " + reason
        features = self.features(entity, concept.lower())
        matches = [h <= features for h in hypotheses]
        if all(matches):
            return "Provisional match: all current hypotheses match.\n" + self.inspect(concept)
        if any(matches):
            return "Uncertain: current hypotheses disagree. Supply a labeled example to distinguish them."
        return "No current hypothesis matches the observed features. Missing graph facts could change this."

