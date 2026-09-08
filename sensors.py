"""Adapters deliver attributed observations; language proposals cannot emit them.

The small ``Surface`` protocol is the reusable boundary for future sensors:
the environment exposes a structured perception and accepts named actions with
structured arguments. The symbolic system stores the resulting observations,
but it cannot invent a sensor result from language alone.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class Observation:
    event_id: str
    source: str
    observed_at: str
    entity: str
    action: str
    outcome: bool


class ActionSensor(Protocol):
    def measure(self, action: str, entity: str) -> bool:
        ...


class Surface(Protocol):
    def observe(self):
        ...

    def act(self, action: str, arguments: dict):
        ...


def _bounded_json(value, depth=0, budget=None):
    """Accept only bounded, JSON-shaped sensor data."""
    budget = [20000] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0:
        raise ValueError("Sensor data exceeds its item budget.")
    if depth > 8:
        raise ValueError("Sensor data is nested too deeply.")
    if type(value) is str and len(value) > 16000:
        raise ValueError("Sensor text exceeds its size budget.")
    if type(value) is float and not math.isfinite(value):
        raise ValueError("Sensor numbers must be finite.")
    if type(value) is int and value.bit_length() > 2048:
        raise ValueError("Sensor number exceeds its size budget.")
    if value is None or type(value) in {str, int, float, bool}:
        return value
    if isinstance(value, list) and len(value) <= 500:
        return [_bounded_json(item, depth + 1, budget) for item in value]
    if isinstance(value, dict) and len(value) <= 200 and all(isinstance(key, str) for key in value):
        return {key: _bounded_json(item, depth + 1, budget) for key, item in value.items()}
    raise ValueError("Sensor data must be bounded JSON-shaped data.")


class CanvasSurface:
    """Reusable adapter for a visible/input canvas.

    A domain canvas supplies one observer and a dictionary of named action
    handlers. The surface itself does not know Sudoku, mouse coordinates, or
    keyboard semantics; those are implemented by the registered environment.
    """

    def __init__(self, observer, actions):
        if not callable(observer) or not (callable(actions) or (isinstance(actions, dict) and actions)):
            raise ValueError("A canvas surface needs an observer and actions.")
        if isinstance(actions, dict) and any(not isinstance(name, str) or not callable(handler) for name, handler in actions.items()):
            raise ValueError("Canvas actions must be named callables.")
        self._observer = observer
        self._actions = dict(actions) if isinstance(actions, dict) else None
        self._dispatcher = actions if callable(actions) else None

    def observe(self):
        return _bounded_json(self._observer())

    def act(self, action, arguments):
        if not isinstance(arguments, dict):
            raise ValueError("Canvas action arguments must be an object.")
        if self._dispatcher is not None:
            return _bounded_json(self._dispatcher(action, dict(arguments)))
        if action not in self._actions:
            raise ValueError("Unknown canvas action. Available actions: " + ", ".join(sorted(self._actions)))
        return _bounded_json(self._actions[action](dict(arguments)))


class ToyWorldSensor:
    def __init__(self, world):
        self.world = world

    def measure(self, action, entity):
        return self.world.act(action, entity)


class ClockSurface:
    def observe(self):
        from date_tools import call_tool
        import time
        return {**call_tool('current_date'), 'unix_seconds': int(time.time())}

    def act(self, action, arguments):
        raise ValueError('The local clock is read-only.')


class SensorHub:
    def __init__(self, store=None):
        self.store = store
        self.adapters = {}
        self.surfaces = {}
        self.events = store.sequence('experience.sensors') if store is not None else []

    def register(self, source, adapter):
        if not source or source in self.adapters or source in self.surfaces:
            raise ValueError("Sensor source must be nonempty and unique.")
        self.adapters[source] = adapter

    def register_surface(self, source, surface):
        if not source or source in self.surfaces or source in self.adapters:
            raise ValueError("Sensor source must be nonempty and unique.")
        if not hasattr(surface, "observe") or not hasattr(surface, "act"):
            raise ValueError("A surface must expose observe and act.")
        self.surfaces[source] = surface

    def perceive(self, source):
        if source not in self.surfaces:
            raise ValueError("Unknown perception source.")
        from graph_runtime import bounded_data
        payload = bounded_data(self.surfaces[source].observe())
        self.events.append({"event_id": str(uuid4()), "source": source,
                            "observed_at": datetime.now(timezone.utc).isoformat(),
                            "kind": "perception", "payload": payload})
        return payload

    def act(self, source, action, arguments=None):
        if source not in self.surfaces:
            raise ValueError("Unknown action surface.")
        from graph_runtime import bounded_data
        arguments = {} if arguments is None else bounded_data(arguments)
        if not isinstance(arguments, dict):
            raise ValueError("Action arguments must be an object.")
        payload = bounded_data(self.surfaces[source].act(action, arguments))
        self.events.append({"event_id": str(uuid4()), "source": source,
                            "observed_at": datetime.now(timezone.utc).isoformat(),
                            "kind": "action", "action": action,
                            "arguments": arguments, "payload": payload})
        return payload

    def experiment(self, source, action, entity, explorer):
        if source not in self.adapters:
            raise ValueError("Unknown sensor source.")
        if action not in explorer.actions or entity not in explorer.observations:
            raise ValueError("Unknown action or entity.")
        outcome = self.adapters[source].measure(action, entity)
        if type(outcome) is not bool:
            raise ValueError("This action sensor must return a boolean outcome.")
        event = Observation(str(uuid4()), source, datetime.now(timezone.utc).isoformat(),
                            entity, action, outcome)
        result = explorer.record(action, entity, outcome)
        self.events.append(asdict(event))
        return result
