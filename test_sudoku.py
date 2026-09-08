import unittest
from interface import Session
from sudoku import SudokuBoard


class NoModel:
    def translate(self, *args):
        raise AssertionError("Explicit Sudoku perception should not call Gemma")


class SudokuTests(unittest.TestCase):
    def test_perception_has_input_state_without_hints(self):
        board = SudokuBoard()
        p = board.perception()
        self.assertEqual(len(p["cells"]), 81)
        self.assertEqual(p["cells"][0], {"row": 0, "col": 0, "value": 5, "given": True})
        self.assertNotIn('candidates', p['cells'][2])
        self.assertNotIn('valid', p)
        self.assertNotIn('complete', p)

    def test_mouse_selection_and_keyboard_like_input(self):
        board = SudokuBoard()
        board.select(0, 2)
        board.place(0, 2, 4)
        self.assertEqual(board.grid[0][2], 4)
        board.place(0, 3, 4)
        board.place(0, 0, 4)
        self.assertEqual(board.grid[0][:4], [4, 3, 4, 4])
        board.place(0, 2, 0)
        self.assertEqual(board.grid[0][2], 0)

    def test_session_exposes_read_only_perception(self):
        session = Session()
        missing = session.chat("What do you see on the Sudoku board?", NoModel())
        self.assertIn('sudoku_observe_read', missing)
        session.teach_sudoku_suite()
        answer = session.chat("What do you see on the Sudoku board?", NoModel())
        self.assertIn("sudoku_observe_read", answer)
        self.assertIn("[5, 3, 0, 0, 7", answer)
        self.assertEqual(session.sudoku.grid[0][0], 5)

    def test_canvas_state_does_not_change_symbolic_memory(self):
        session = Session()
        before = dict(session.core.facts)
        session.sudoku.select(0, 2)
        session.sudoku.place(0, 2, 4)
        self.assertEqual(before, session.core.facts)

    def test_randomized_board_starting_values_remain_editable(self):
        board = SudokuBoard()
        board.randomize(seed=7, blanks=45)
        self.assertEqual(sum(value == 0 for row in board.grid for value in row), 45)
        given = next((r, c) for r in range(9) for c in range(9) if board.givens[r][c])
        board.place(given[0], given[1], 0)
        self.assertEqual(board.grid[given[0]][given[1]], 0)


if __name__ == "__main__":
    unittest.main()
