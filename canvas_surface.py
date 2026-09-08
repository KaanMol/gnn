"""Canvas device: visible drawing marks and scoped pointer/keyboard controls.

This adapter exposes the drawing's text and geometry, not pixel recognition.
It does not expose candidates, constraints, a solution, or symbol meanings.
"""
import math


class BoardCanvas:
    actions = {"move": {"x": "number in [0,1)", "y": "number in [0,1)"},
               "click": {}, "key": {"key": "one digit, Backspace, or Delete"}}

    def __init__(self, board):
        self.board = board  # Resolve current environment, including resets.
        self.pointer = None
        self.feedback = None

    def observe(self):
        board = self.board()
        marks = [{"text": str(board.grid[r][c]) if board.grid[r][c] else "",
                  "x": (c + .5) / 9, "y": (r + .5) / 9,
                  "width": 1 / 9, "height": 1 / 9,
                  "color": "#28392f"}
                 for r in range(9) for c in range(9)]
        return {"format": "canvas.scene.v1", "marks": marks,
                "lines": [{"axis": axis, "position": i / 9, "width": 3 if i % 3 == 0 else 1}
                          for axis in ("x", "y") for i in range(10)],
                "pointer": self.pointer, "focus": board.selected is not None,
                "feedback": self.feedback}

    def act(self, action, arguments):
        if action not in self.actions or set(arguments) != set(self.actions[action]):
            raise ValueError("Use a registered canvas action and its declared arguments.")
        board = self.board()
        if action == "move":
            if any(type(arguments[k]) not in {int, float} or not math.isfinite(arguments[k])
                   or not 0 <= arguments[k] < 1 for k in ("x", "y")):
                raise ValueError("Pointer coordinates must be finite numbers from 0 to less than 1.")
            self.pointer = dict(arguments)
        elif action == "key" and arguments["key"] not in tuple("123456789") + ("Backspace", "Delete"):
            raise ValueError("Use one digit, Backspace, or Delete.")
        try:
            if action == "click":
                if self.pointer is None:
                    raise ValueError("Move the pointer before clicking.")
                board.select(int(self.pointer["y"] * 9), int(self.pointer["x"] * 9))
            elif action == "key":
                if board.selected is None:
                    raise ValueError("Click the canvas before typing.")
                value = 0 if arguments["key"] in {"Backspace", "Delete"} else int(arguments["key"])
                board.place(*board.selected, value)
            self.feedback = {"accepted": True, "action": action, "message": "Input accepted."}
        except ValueError as error:
            self.feedback = {"accepted": False, "action": action, "message": str(error)}
        return self.observe()
