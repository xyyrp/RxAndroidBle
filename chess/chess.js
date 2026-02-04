const boardElement = document.getElementById("board");
const statusElement = document.getElementById("status");
const restartButton = document.getElementById("restart");

const pieceSymbols = {
  wp: "♙",
  wr: "♖",
  wn: "♘",
  wb: "♗",
  wq: "♕",
  wk: "♔",
  bp: "♟",
  br: "♜",
  bn: "♞",
  bb: "♝",
  bq: "♛",
  bk: "♚",
};

const pieceValues = {
  p: 1,
  n: 3,
  b: 3,
  r: 5,
  q: 9,
  k: 100,
};

let state = initializeGame();

function initializeGame() {
  return {
    board: createInitialBoard(),
    currentPlayer: "w",
    selected: null,
    legalMoves: [],
    status: "White to move.",
    gameOver: false,
  };
}

function createInitialBoard() {
  const emptyRow = Array(8).fill(null);
  return [
    ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
    Array(8).fill("bp"),
    [...emptyRow],
    [...emptyRow],
    [...emptyRow],
    [...emptyRow],
    Array(8).fill("wp"),
    ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"],
  ];
}

function renderBoard() {
  boardElement.innerHTML = "";
  for (let row = 0; row < 8; row += 1) {
    for (let col = 0; col < 8; col += 1) {
      const square = document.createElement("button");
      square.className = `square ${(row + col) % 2 === 0 ? "light" : "dark"}`;
      square.dataset.row = row;
      square.dataset.col = col;
      const piece = state.board[row][col];
      if (piece) {
        square.textContent = pieceSymbols[piece];
        square.setAttribute("aria-label", pieceLabel(piece, row, col));
      }
      if (state.selected && state.selected.row === row && state.selected.col === col) {
        square.classList.add("selected");
      }
      const move = state.legalMoves.find(
        (moveOption) => moveOption.to.row === row && moveOption.to.col === col
      );
      if (move) {
        square.classList.add(move.isCapture ? "capture" : "move");
      }
      square.addEventListener("click", onSquareClick);
      boardElement.appendChild(square);
    }
  }
  statusElement.textContent = state.status;
}

function pieceLabel(piece, row, col) {
  const color = piece[0] === "w" ? "White" : "Black";
  const typeMap = {
    p: "Pawn",
    r: "Rook",
    n: "Knight",
    b: "Bishop",
    q: "Queen",
    k: "King",
  };
  return `${color} ${typeMap[piece[1]]} on ${String.fromCharCode(65 + col)}${8 - row}`;
}

function onSquareClick(event) {
  if (state.gameOver || state.currentPlayer !== "w") {
    return;
  }
  const row = Number(event.currentTarget.dataset.row);
  const col = Number(event.currentTarget.dataset.col);
  const piece = state.board[row][col];

  if (state.selected) {
    const move = state.legalMoves.find(
      (moveOption) => moveOption.to.row === row && moveOption.to.col === col
    );
    if (move) {
      performMove(move);
      return;
    }
  }

  if (piece && piece[0] === "w") {
    state.selected = { row, col };
    state.legalMoves = getLegalMovesForSquare(state.board, row, col, "w");
  } else {
    state.selected = null;
    state.legalMoves = [];
  }
  renderBoard();
}

function performMove(move) {
  state.board = applyMove(state.board, move);
  state.selected = null;
  state.legalMoves = [];
  state.currentPlayer = state.currentPlayer === "w" ? "b" : "w";
  updateStatus();
  renderBoard();
  if (!state.gameOver && state.currentPlayer === "b") {
    window.setTimeout(makeAiMove, 500);
  }
}

function updateStatus() {
  const currentColorName = state.currentPlayer === "w" ? "White" : "Black";
  const opponentColor = state.currentPlayer === "w" ? "b" : "w";
  if (isKingInCheck(state.board, state.currentPlayer)) {
    if (getAllLegalMoves(state.board, state.currentPlayer).length === 0) {
      state.status = `Checkmate! ${opponentColor === "w" ? "White" : "Black"} wins.`;
      state.gameOver = true;
    } else {
      state.status = `${currentColorName} is in check.`;
    }
    return;
  }

  if (getAllLegalMoves(state.board, state.currentPlayer).length === 0) {
    state.status = "Stalemate!";
    state.gameOver = true;
    return;
  }

  state.status = `${currentColorName} to move.`;
}

function makeAiMove() {
  if (state.gameOver) {
    return;
  }
  const legalMoves = getAllLegalMoves(state.board, "b");
  if (legalMoves.length === 0) {
    updateStatus();
    renderBoard();
    return;
  }
  const scoredMoves = legalMoves.map((move) => {
    const nextBoard = applyMove(state.board, move);
    return {
      move,
      score: evaluateBoard(nextBoard),
    };
  });
  const bestScore = Math.min(...scoredMoves.map((entry) => entry.score));
  const bestMoves = scoredMoves.filter((entry) => entry.score === bestScore);
  const chosen = bestMoves[Math.floor(Math.random() * bestMoves.length)].move;
  performMove(chosen);
}

function evaluateBoard(board) {
  let score = 0;
  for (let row = 0; row < 8; row += 1) {
    for (let col = 0; col < 8; col += 1) {
      const piece = board[row][col];
      if (!piece) continue;
      const value = pieceValues[piece[1]];
      score += piece[0] === "w" ? value : -value;
    }
  }
  return score;
}

function getAllLegalMoves(board, color) {
  const moves = [];
  for (let row = 0; row < 8; row += 1) {
    for (let col = 0; col < 8; col += 1) {
      const piece = board[row][col];
      if (piece && piece[0] === color) {
        moves.push(...getLegalMovesForSquare(board, row, col, color));
      }
    }
  }
  return moves;
}

function getLegalMovesForSquare(board, row, col, color) {
  const piece = board[row][col];
  if (!piece) return [];
  const type = piece[1];
  const pseudoMoves = getPseudoMoves(board, row, col, color, type);
  return pseudoMoves.filter((move) => {
    const nextBoard = applyMove(board, move);
    return !isKingInCheck(nextBoard, color);
  });
}

function getPseudoMoves(board, row, col, color, type) {
  switch (type) {
    case "p":
      return getPawnMoves(board, row, col, color);
    case "r":
      return getSlidingMoves(board, row, col, color, [
        { row: 1, col: 0 },
        { row: -1, col: 0 },
        { row: 0, col: 1 },
        { row: 0, col: -1 },
      ]);
    case "b":
      return getSlidingMoves(board, row, col, color, [
        { row: 1, col: 1 },
        { row: 1, col: -1 },
        { row: -1, col: 1 },
        { row: -1, col: -1 },
      ]);
    case "q":
      return getSlidingMoves(board, row, col, color, [
        { row: 1, col: 0 },
        { row: -1, col: 0 },
        { row: 0, col: 1 },
        { row: 0, col: -1 },
        { row: 1, col: 1 },
        { row: 1, col: -1 },
        { row: -1, col: 1 },
        { row: -1, col: -1 },
      ]);
    case "n":
      return getKnightMoves(board, row, col, color);
    case "k":
      return getKingMoves(board, row, col, color);
    default:
      return [];
  }
}

function getPawnMoves(board, row, col, color) {
  const direction = color === "w" ? -1 : 1;
  const startRow = color === "w" ? 6 : 1;
  const moves = [];
  const forwardRow = row + direction;
  if (isOnBoard(forwardRow, col) && !board[forwardRow][col]) {
    moves.push(createMove(row, col, forwardRow, col));
    const doubleRow = row + 2 * direction;
    if (row === startRow && !board[doubleRow][col]) {
      moves.push(createMove(row, col, doubleRow, col));
    }
  }
  [-1, 1].forEach((colOffset) => {
    const targetRow = row + direction;
    const targetCol = col + colOffset;
    if (!isOnBoard(targetRow, targetCol)) return;
    const targetPiece = board[targetRow][targetCol];
    if (targetPiece && targetPiece[0] !== color) {
      moves.push(createMove(row, col, targetRow, targetCol, true));
    }
  });
  return moves;
}

function getKnightMoves(board, row, col, color) {
  const offsets = [
    { row: -2, col: -1 },
    { row: -2, col: 1 },
    { row: -1, col: -2 },
    { row: -1, col: 2 },
    { row: 1, col: -2 },
    { row: 1, col: 2 },
    { row: 2, col: -1 },
    { row: 2, col: 1 },
  ];
  return offsets
    .map((offset) => ({ row: row + offset.row, col: col + offset.col }))
    .filter((target) => isOnBoard(target.row, target.col))
    .filter((target) => !board[target.row][target.col] || board[target.row][target.col][0] !== color)
    .map((target) => createMove(row, col, target.row, target.col, !!board[target.row][target.col]));
}

function getKingMoves(board, row, col, color) {
  const moves = [];
  for (let rowOffset = -1; rowOffset <= 1; rowOffset += 1) {
    for (let colOffset = -1; colOffset <= 1; colOffset += 1) {
      if (rowOffset === 0 && colOffset === 0) continue;
      const targetRow = row + rowOffset;
      const targetCol = col + colOffset;
      if (!isOnBoard(targetRow, targetCol)) continue;
      const targetPiece = board[targetRow][targetCol];
      if (!targetPiece || targetPiece[0] !== color) {
        moves.push(createMove(row, col, targetRow, targetCol, !!targetPiece));
      }
    }
  }
  return moves;
}

function getSlidingMoves(board, row, col, color, directions) {
  const moves = [];
  directions.forEach((direction) => {
    let targetRow = row + direction.row;
    let targetCol = col + direction.col;
    while (isOnBoard(targetRow, targetCol)) {
      const targetPiece = board[targetRow][targetCol];
      if (!targetPiece) {
        moves.push(createMove(row, col, targetRow, targetCol));
      } else {
        if (targetPiece[0] !== color) {
          moves.push(createMove(row, col, targetRow, targetCol, true));
        }
        break;
      }
      targetRow += direction.row;
      targetCol += direction.col;
    }
  });
  return moves;
}

function createMove(fromRow, fromCol, toRow, toCol, isCapture = false) {
  return {
    from: { row: fromRow, col: fromCol },
    to: { row: toRow, col: toCol },
    isCapture,
  };
}

function applyMove(board, move) {
  const nextBoard = board.map((row) => [...row]);
  const piece = nextBoard[move.from.row][move.from.col];
  nextBoard[move.from.row][move.from.col] = null;
  let placedPiece = piece;
  if (piece && piece[1] === "p") {
    if (move.to.row === 0 || move.to.row === 7) {
      placedPiece = `${piece[0]}q`;
    }
  }
  nextBoard[move.to.row][move.to.col] = placedPiece;
  return nextBoard;
}

function isKingInCheck(board, color) {
  const kingPosition = findKing(board, color);
  if (!kingPosition) {
    return true;
  }
  return isSquareAttacked(board, kingPosition.row, kingPosition.col, color === "w" ? "b" : "w");
}

function findKing(board, color) {
  for (let row = 0; row < 8; row += 1) {
    for (let col = 0; col < 8; col += 1) {
      if (board[row][col] === `${color}k`) {
        return { row, col };
      }
    }
  }
  return null;
}

function isSquareAttacked(board, row, col, attackerColor) {
  const directions = [
    { row: 1, col: 0 },
    { row: -1, col: 0 },
    { row: 0, col: 1 },
    { row: 0, col: -1 },
    { row: 1, col: 1 },
    { row: 1, col: -1 },
    { row: -1, col: 1 },
    { row: -1, col: -1 },
  ];
  for (const direction of directions) {
    let targetRow = row + direction.row;
    let targetCol = col + direction.col;
    let steps = 1;
    while (isOnBoard(targetRow, targetCol)) {
      const piece = board[targetRow][targetCol];
      if (piece) {
        if (piece[0] === attackerColor) {
          const type = piece[1];
          if (
            (steps === 1 && type === "k") ||
            ((direction.row === 0 || direction.col === 0) && (type === "r" || type === "q")) ||
            (direction.row !== 0 && direction.col !== 0 && (type === "b" || type === "q"))
          ) {
            return true;
          }
        }
        break;
      }
      targetRow += direction.row;
      targetCol += direction.col;
      steps += 1;
    }
  }

  const knightOffsets = [
    { row: -2, col: -1 },
    { row: -2, col: 1 },
    { row: -1, col: -2 },
    { row: -1, col: 2 },
    { row: 1, col: -2 },
    { row: 1, col: 2 },
    { row: 2, col: -1 },
    { row: 2, col: 1 },
  ];
  for (const offset of knightOffsets) {
    const targetRow = row + offset.row;
    const targetCol = col + offset.col;
    if (!isOnBoard(targetRow, targetCol)) continue;
    const piece = board[targetRow][targetCol];
    if (piece === `${attackerColor}n`) {
      return true;
    }
  }

  const pawnDirection = attackerColor === "w" ? -1 : 1;
  const pawnRow = row + pawnDirection;
  for (const colOffset of [-1, 1]) {
    const targetCol = col + colOffset;
    if (isOnBoard(pawnRow, targetCol)) {
      if (board[pawnRow][targetCol] === `${attackerColor}p`) {
        return true;
      }
    }
  }

  return false;
}

function isOnBoard(row, col) {
  return row >= 0 && row < 8 && col >= 0 && col < 8;
}

restartButton.addEventListener("click", () => {
  state = initializeGame();
  updateStatus();
  renderBoard();
});

updateStatus();
renderBoard();
