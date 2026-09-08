"""Legacy prose lesson records. Executable lessons are explicitly taught graph data."""


STRATEGIES = {
    "naked_single": "An empty cell with exactly one candidate gets that digit.",
    "hidden_single_row": "If a digit can go in only one empty cell in a row, place it.",
    "hidden_single_col": "If a digit can go in only one empty cell in a column, place it.",
    "hidden_single_box": "If a digit can go in only one empty cell in a 3x3 box, place it.",
}

def teach(library, text, source):
    lowered = " ".join(text.lower().replace("×", "x").split())
    if "one candidate" in lowered or "naked single" in lowered:
        key = "naked_single"
    elif "only one" in lowered and "row" in lowered:
        key = "hidden_single_row"
    elif "only one" in lowered and "column" in lowered:
        key = "hidden_single_col"
    elif "only one" in lowered and ("box" in lowered or "square" in lowered):
        key = "hidden_single_box"
    else:
        raise ValueError("Teach one supported strategy: naked single, or a digit that fits one cell in a row, column, or 3x3 box.")
    library[key] = {"description": STRATEGIES[key], "source": source}
    return "Learned Sudoku strategy: " + STRATEGIES[key]


def direct(text):
    from semantics import operation
    candidate = " ".join(text.strip().rstrip(".!?").split())
    lowered = candidate.lower()
    if lowered.startswith("teach sudoku:"):
        return {"operations": [operation("teach_sudoku", text=candidate.split(":", 1)[1].strip())]}
    if lowered in {"solve sudoku", "solve the sudoku", "solve this sudoku", "solve the sudoku board"}:
        return {"operations": [operation("sudoku_solve")]}
    if lowered in {"show sudoku lessons", "what sudoku strategies do you know", "show sudoku strategies"}:
        return {"operations": [operation("list_sudoku")]} 
    return None
