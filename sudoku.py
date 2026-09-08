"""A small, inspectable Sudoku canvas environment.

The board is an environment: perception returns cell coordinates and values,
mouse selects a cell, and keyboard input writes a digit. Every cell is editable.
The environment does not check Sudoku rules or supply candidate hints.
"""
import copy
import random


DEFAULT = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


class SudokuBoard:
    def __init__(self, puzzle=None):
        self.reset(puzzle or DEFAULT)

    def reset(self, puzzle=None):
        puzzle = puzzle or DEFAULT
        if len(puzzle) != 9 or any(len(row) != 9 for row in puzzle):
            raise ValueError("A Sudoku board must have nine rows of nine cells.")
        if any(type(value) is not int or not 0 <= value <= 9 for row in puzzle for value in row):
            raise ValueError("Sudoku cells must be integers from 0 to 9; 0 means empty.")
        self.givens = copy.deepcopy(puzzle)
        self.grid = copy.deepcopy(puzzle)
        self.selected = None
        self.recent = None

    def randomize(self, seed=None, blanks=45):
        """Create a valid randomized puzzle from a shuffled complete grid.

        This generates environment input only; it does not solve the puzzle.
        ``blanks`` is bounded so the canvas remains usable.
        """
        if type(blanks) is not int or not 20 <= blanks <= 60:
            raise ValueError("A randomized Sudoku needs between 20 and 60 empty cells.")
        rng = random.Random(seed)
        base = [[(r * 3 + r // 3 + c) % 9 + 1 for c in range(9)] for r in range(9)]
        bands = [list(range(i, i + 3)) for i in (0, 3, 6)]
        rng.shuffle(bands)
        rows = [row for band in bands for row in (rng.sample(band, 3))]
        stacks = [list(range(i, i + 3)) for i in (0, 3, 6)]
        rng.shuffle(stacks)
        cols = [col for stack in stacks for col in rng.sample(stack, 3)]
        digits = list(range(1, 10)); rng.shuffle(digits)
        complete = [[digits[base[r][c] - 1] for c in cols] for r in rows]
        puzzle = copy.deepcopy(complete)
        for row, col in rng.sample([(r, c) for r in range(9) for c in range(9)], blanks):
            puzzle[row][col] = 0
        self.reset(puzzle)
        return self.perception()

    def select(self, row, col):
        if not 0 <= row < 9 or not 0 <= col < 9:
            raise ValueError("Sudoku coordinates must be between 0 and 8.")
        self.selected = [row, col]
        return self.perception()

    def place(self, row, col, value):
        if not 0 <= row < 9 or not 0 <= col < 9:
            raise ValueError("Sudoku coordinates must be between 0 and 8.")
        if type(value) is not int or not 0 <= value <= 9:
            raise ValueError("Enter a Sudoku digit from 1 to 9, or 0 to clear a cell.")
        self.grid[row][col] = value
        self.selected = [row, col]
        self.recent = {"row": row, "col": col, "value": value, "accepted": True}
        return self.perception()

    def perception(self):
        cells = []
        for row in range(9):
            for col in range(9):
                cells.append({"row": row, "col": col, "value": self.grid[row][col],
                              "given": bool(self.givens[row][col])})
        return {"rows": 9, "cols": 9, "cells": cells, "selected": self.selected,
                "recent": self.recent,
                "input": {"mouse": "select(row,col)", "keyboard": "digit 1-9 or Backspace"}}
