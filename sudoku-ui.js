const sudokuCanvas = $('sudoku-canvas');
const sudokuCtx = sudokuCanvas.getContext('2d');
let sudokuState = null, boardQueue = Promise.resolve(), boardWorking = false;
function drawSudoku(s) {
  if (!s) return;
  sudokuState = s;
  const d = sudokuCanvas.width / 9;
  sudokuCtx.clearRect(0, 0, 450, 450);
  sudokuCtx.fillStyle = '#fffefa'; sudokuCtx.fillRect(0, 0, 450, 450);
  for (const cell of s.cells) {
    const {row, col, value} = cell;
    if (s.selected && s.selected[0] === row && s.selected[1] === col) {
      sudokuCtx.fillStyle = '#e1edb5'; sudokuCtx.fillRect(col*d+1, row*d+1, d-2, d-2);
    }
    if (value) {
      sudokuCtx.fillStyle = '#28392f'; sudokuCtx.font = '500 26px Avenir Next';
      sudokuCtx.textAlign = 'center'; sudokuCtx.textBaseline = 'middle';
      sudokuCtx.fillText(value, col*d+d/2, row*d+d/2);
    }
  }
  for (let i=0; i<=9; i++) {
    sudokuCtx.beginPath(); sudokuCtx.lineWidth = i%3 === 0 ? 3 : 1;
    sudokuCtx.strokeStyle = '#28392f'; sudokuCtx.moveTo(i*d, 0); sudokuCtx.lineTo(i*d, 450);
    sudokuCtx.moveTo(0, i*d); sudokuCtx.lineTo(450, i*d); sudokuCtx.stroke();
  }
  $('sudoku-selected').textContent = s.selected ? `Row ${s.selected[0]+1}, column ${s.selected[1]+1}` : 'Select a cell';
}
function sudokuAction(action, row, col, value) {
  if (busy && !boardWorking) return;
  // Keep fast clicks and keystrokes in order; capture their target at enqueue.
  boardQueue = boardQueue.then(async () => {
    busy = true; boardWorking = true;
    document.querySelectorAll('button').forEach(b => b.disabled = true);
    $('sudoku-status').textContent = action === 'sudoku_solve' ? 'Running the taught lessons…' : 'Saving…';
    try {
      const res = await fetch('/api/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action,row,col,value,state_version:stateVersion})});
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'The request failed.');
      render(data.state);
      $('sudoku-status').textContent = data.answer;
      if (data.execution) {
        $('sudoku-trace').textContent = JSON.stringify(data.execution.trace, null, 2);
        $('sudoku-result').textContent = JSON.stringify(data.execution.result, null, 2);
      }
    } catch(error) { $('sudoku-status').textContent = error.message; }
    finally {
      busy = false; boardWorking = false;
      document.querySelectorAll('button').forEach(b => b.disabled = false);
    }
  });
  return boardQueue;
}
function enterDigit(value) {
  if (!sudokuState?.selected) { $('sudoku-status').textContent = 'Select a cell first.'; return; }
  sudokuAction('sudoku_place', ...sudokuState.selected, value);
}
sudokuCanvas.onclick = event => {
  if (!sudokuState || (busy && !boardWorking)) return;
  const box = sudokuCanvas.getBoundingClientRect();
  const col = Math.min(8, Math.max(0, Math.floor((event.clientX-box.left)/box.width*9)));
  const row = Math.min(8, Math.max(0, Math.floor((event.clientY-box.top)/box.height*9)));
  sudokuState.selected = [row,col]; drawSudoku(sudokuState); sudokuCanvas.focus();
  sudokuAction('sudoku_select', row, col);
};
sudokuCanvas.onkeydown = event => {
  if (!sudokuState?.selected) return;
  if (/^[1-9]$/.test(event.key)) { event.preventDefault(); enterDigit(Number(event.key)); }
  else if (['Backspace','Delete','0'].includes(event.key)) { event.preventDefault(); enterDigit(0); }
  else if (event.key.startsWith('Arrow')) {
    event.preventDefault();
    let [row,col] = sudokuState.selected;
    row = Math.max(0, Math.min(8, row + (event.key === 'ArrowDown' ? 1 : event.key === 'ArrowUp' ? -1 : 0)));
    col = Math.max(0, Math.min(8, col + (event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0)));
    sudokuState.selected = [row,col]; drawSudoku(sudokuState); sudokuAction('sudoku_select',row,col);
  }
};
for (let digit=1; digit<=9; digit++) {
  const button = el('button','secondary',String(digit));
  button.setAttribute('aria-label','Enter '+digit);
  button.onclick = () => { enterDigit(digit); sudokuCanvas.focus(); };
  $('sudoku-keypad').append(button);
}
$('sudoku-erase').onclick = () => { enterDigit(0); sudokuCanvas.focus(); };
for (const action of ['reset','randomize','clear','check','solve']) $('sudoku-'+action).onclick = () => sudokuAction('sudoku_'+action);
$('sudoku-teach').onclick = () => sudokuAction('teach_sudoku_suite');
$('sudoku-read').onclick = () => act('chat','What do you see on the Sudoku board?');
const baseRender = render;
render = function(state) {
  baseRender(state); drawSudoku(state.sudoku);
  $('sudoku-check-status').textContent = state.sudoku_check ? 'Last check: '+state.sudoku_check.verdict : 'Not checked';
  if (!state.sudoku_check) {
    $('sudoku-result').textContent = 'No current check. Editing or revising a lesson clears the previous verdict.';
    $('sudoku-trace').textContent = '';
  }
};
