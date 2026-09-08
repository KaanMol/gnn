"""Learn action outcomes through experiments in a small symbolic world."""
import argparse
import json
import re
from pathlib import Path

from knowledge import Knowledge, stored_map
from graph_store import GraphStore, atomic_graph, database_path
import foundation


class ToyWorld:
    """The environment owns physical rules; observations expose only features."""
    actions = ("roll", "float")

    def __init__(self):
        self._objects = {
            "Amber": {"shape": "sphere", "material": "wood", "color": "red"},
            "Birch": {"shape": "cube", "material": "wood", "color": "blue"},
            "Copper": {"shape": "sphere", "material": "metal", "color": "blue"},
            "Dune": {"shape": "cube", "material": "metal", "color": "red"},
            "Elm": {"shape": "sphere", "material": "wood", "color": "blue"},
            "Flint": {"shape": "cube", "material": "wood", "color": "red"},
            "Granite": {"shape": "sphere", "material": "metal", "color": "red"},
            "Hazel": {"shape": "cube", "material": "metal", "color": "blue"},
        }

    def observe(self):
        return {name: dict(features) for name, features in self._objects.items()}

    def act(self, action, entity):
        if action not in self.actions:
            raise ValueError("Available actions: roll, float")
        features = self._objects[entity]
        # Simplified simulator laws, not claims about real-world physics.
        return features["shape"] == "sphere" if action == "roll" else features["material"] == "wood"


class Explorer:
    observations = stored_map('observations')
    starts = stored_map('starts')
    words = stored_map('words')

    @property
    def actions(self):
        return self.store.map(self.prefix + '.settings')['actions']

    def __init__(self, observations, actions, store=None):
        self.store = store if store is not None else foundation.new_learning_store()
        self.prefix = 'world'
        self.episodes = self.store.sequence('world.episodes')
        self.space = self.store.sequence('world.hypothesis_space')
        self.graph = Knowledge(self.store, 'world.knowledge')
        settings = self.store.map('world.settings')
        if settings.get('initialized'):
            return
        self.observations = {name: dict(features) for name, features in observations.items()}
        settings['actions'] = tuple(actions)
        self.starts = {action: 0 for action in actions}
        # Ground the supplied observation schema in one transaction; inference
        # runs once after the complete batch of attributed input records arrives.
        records = {}
        for entity, features in self.observations.items():
            records[(("is", entity, "object"), False)] = f"{entity} is an object."
            for attribute, value in features.items():
                obj = attribute.title() + value.title()
                records[(("has", entity, obj), False)] = f"{entity} has {obj}."
        with self.store.transaction():
            self.graph.assertions.update(records)
            self.graph.statements.extend(records.values())
            self.graph.rebuild()
        self.space.replace(self.invoke('world_hypothesis_space', dict(self.observations)))
        settings['initialized'] = True

    def invoke(self, name, argument):
        result, self.last_trace = foundation.run(self.store.map('knowledge.procedures'), name, foundation.data(argument))
        self.store.map('world.executions')[name] = {'procedure': name, 'input': foundation.data(argument),
                                                  'result': result, 'trace': self.last_trace}
        return result

    def _arguments(self, action, entity=None):
        result = {'action': action, 'start': self.starts[action], 'episodes': list(self.episodes), 'space': list(self.space)}
        if entity is not None:
            result.update(entity=entity, features=dict(self.observations[entity]))
        return result

    def matches(self, hypothesis, features):
        return self.invoke('world_matches', {'hypothesis': hypothesis, 'features': features})

    def hypotheses(self, action):
        try:
            return [None if h is None else tuple(tuple(pair) for pair in h)
                    for h in self.invoke('world_hypotheses', self._arguments(action))]
        except ValueError as error:
            if not foundation.missing_method(error): raise
            return []

    def predict(self, action, entity):
        return self.invoke('world_predict', self._arguments(action, entity))

    def choose(self):
        try:
            result = self.invoke('world_choose_experiment', {'observations': dict(self.observations),
                'actions': list(self.actions), 'episodes': list(self.episodes), 'space': list(self.space), 'starts': dict(self.starts)})
            return tuple(result) if result else None
        except ValueError as error:
            if not foundation.missing_method(error): raise
            return None

    @atomic_graph
    def record(self, action, entity, outcome):
        if action not in self.actions or entity not in self.observations or type(outcome) is not bool:
            raise ValueError("An experience requires a known action, object, and boolean outcome.")
        result = self.invoke('world_update', {**self._arguments(action, entity), 'outcome': outcome})
        prediction, revised = result['prediction'], result['revised']
        self.episodes.append(result['episode'])
        self.starts[action] = result['start']
        index = len(self.episodes)
        self.graph.tell(f"Episode{index} is an experience.")
        self.graph.tell(f"Episode{index} concerns {entity}.")
        self.graph.tell(f"Episode{index} performs {action.title()}.")
        self.graph.tell(f"Episode{index} reports {'Success' if outcome else 'Failure'}.")
        return {"action": action, "entity": entity, "prediction": prediction,
                "outcome": outcome, "revised": revised}

    def step(self, environment):
        choice = self.choose()
        if choice is None:
            return None
        action, entity = choice
        return self.record(action, entity, environment.act(action, entity))

    def name(self, sentence):
        match = re.fullmatch(r"Call things that (\w+) (\w+)\.?", sentence.strip())
        if not match or match[1] not in self.actions:
            raise ValueError("Try: Call things that roll rollers.")
        self.words[match[2].lower()] = match[1]

    def ask(self, sentence):
        match = re.fullmatch(r"Is (\w+) a (\w+)\?", sentence.strip())
        if not match or match[1] not in self.observations or match[2].lower() not in self.words:
            raise ValueError("Use a known object and an exact taught word: Is Amber a roller?")
        return self.predict(self.words[match[2].lower()], match[1])

    def report(self):
        lines = []
        for action in self.actions:
            hypotheses = self.hypotheses(action)
            descriptions = ["never" if h is None else "always" if not h else
                            " and ".join(f"{k}={v}" for k, v in h) for h in hypotheses]
            lines.append(f"{action}: {len(hypotheses)} candidate rule(s): " + "; ".join(descriptions[:8]))
        choice = self.choose()
        lines.append(f"Next question: Will {choice[1]} {choice[0]}?" if choice else
                     "No distinguishing experiment remains among the visible objects. This is not proof of a universal rule.")
        return "\n".join(lines)

    def save(self, path):
        return self.store.save(path)

    @classmethod
    def load(cls, path):
        database = database_path(path)
        if database.exists():
            return cls({}, (), GraphStore(database))
        data = json.loads(Path(path).read_text())
        explorer = cls(data["observations"], data["actions"])
        for episode in data["episodes"]:
            if episode["features"] != explorer.observations[episode["entity"]]:
                raise ValueError("Changing object features are not supported in saved sessions yet.")
            explorer.record(episode["action"], episode["entity"], episode["outcome"])
        explorer.words = data["words"]
        explorer.save(path)
        return explorer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--memory", type=Path, default=Path("playground-memory.json"))
    args = parser.parse_args()
    world = ToyWorld()
    explorer = Explorer.load(args.memory) if not args.demo and (args.memory.exists() or database_path(args.memory).exists()) else Explorer(world.observe(), world.actions)
    if explorer.observations != world.observe() or explorer.actions != world.actions:
        raise ValueError("Saved observations do not match this world. Choose a new memory path.")
    if args.demo:
        for _ in range(20):
            result = explorer.step(world)
            if result is None:
                break
            print(json.dumps(result))
        explorer.name("Call things that roll roller.")
        print(explorer.report())
        print("Is Amber a roller? " + explorer.ask("Is Amber a roller?"))
        return
    print("Commands: look, explore, run, beliefs, try roll Amber, quit")
    print("Teach: Call things that roll roller.  Ask: Is Amber a roller?")
    while True:
        try:
            line = input("> ").strip()
            if line == "quit":
                break
            if line == "look":
                print(json.dumps(dict(explorer.observations), indent=2))
            elif line in {"explore", "run"}:
                for _ in range(1 if line == "explore" else 20):
                    result = explorer.step(world)
                    if result is None:
                        print("No distinguishing experiment remains. Use 'try' to retest an outcome.")
                        break
                    print(json.dumps(result))
            elif line == "beliefs":
                print(explorer.report())
            elif line.startswith("try "):
                parts = line.split()
                if len(parts) != 3:
                    raise ValueError("Use: try roll Amber")
                print(json.dumps(explorer.record(parts[1], parts[2], world.act(parts[1], parts[2]))))
            elif line.startswith("Call "):
                explorer.name(line)
                print("Word connected to an observed action outcome.")
            elif line.endswith("?"):
                print(explorer.ask(line))
            else:
                print("Use look, explore, run, beliefs, try ACTION OBJECT, or quit.")
            explorer.save(args.memory)
        except (ValueError, KeyError) as error:
            print("Cannot process:", str(error))
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    main()
