#!/usr/bin/env python3
"""Single-file Chess with a basic AI opponent (Tkinter UI)."""
import tkinter as tk
from dataclasses import dataclass
from typing import List, Optional, Tuple

BOARD_SIZE = 8
SQUARE_SIZE = 64
WINDOW_SIZE = BOARD_SIZE * SQUARE_SIZE

WHITE_PIECES = set("PNBRQK")
BLACK_PIECES = set("pnbrqk")

PIECE_TO_SYMBOL = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",
    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
}

PIECE_VALUE = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 20000,
    "p": -100,
    "n": -320,
    "b": -330,
    "r": -500,
    "q": -900,
    "k": -20000,
}


@dataclass
class Move:
    fr: Tuple[int, int]
    to: Tuple[int, int]
    piece: str
    captured: Optional[str] = None
    promotion: Optional[str] = None
    is_castling: bool = False
    is_en_passant: bool = False


class ChessGame:
    def __init__(self) -> None:
        self.board = self._initial_board()
        self.white_to_move = True
        self.castling_rights = {
            "K": True,
            "Q": True,
            "k": True,
            "q": True,
        }
        self.en_passant_target: Optional[Tuple[int, int]] = None
        self.move_history: List[Move] = []

    def _initial_board(self) -> List[List[Optional[str]]]:
        return [
            list("rnbqkbnr"),
            list("pppppppp"),
            [None] * BOARD_SIZE,
            [None] * BOARD_SIZE,
            [None] * BOARD_SIZE,
            [None] * BOARD_SIZE,
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]

    def piece_at(self, row: int, col: int) -> Optional[str]:
        return self.board[row][col]

    def is_white(self, piece: str) -> bool:
        return piece in WHITE_PIECES

    def is_black(self, piece: str) -> bool:
        return piece in BLACK_PIECES

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def king_position(self, white: bool) -> Tuple[int, int]:
        target = "K" if white else "k"
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == target:
                    return (r, c)
        raise ValueError("King not found")

    def is_square_attacked(self, row: int, col: int, by_white: bool) -> bool:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if not piece:
                    continue
                if by_white and piece not in WHITE_PIECES:
                    continue
                if not by_white and piece not in BLACK_PIECES:
                    continue
                for move in self._pseudo_moves_for_piece(r, c, piece, attacks_only=True):
                    if move.to == (row, col):
                        return True
        return False

    def in_check(self, white: bool) -> bool:
        king_row, king_col = self.king_position(white)
        return self.is_square_attacked(king_row, king_col, by_white=not white)

    def legal_moves(self, white: bool) -> List[Move]:
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if not piece:
                    continue
                if white and piece not in WHITE_PIECES:
                    continue
                if not white and piece not in BLACK_PIECES:
                    continue
                for move in self._pseudo_moves_for_piece(r, c, piece):
                    self._make_move(move)
                    in_check = self.in_check(white)
                    self._undo_move()
                    if not in_check:
                        moves.append(move)
        return moves

    def _pseudo_moves_for_piece(
        self,
        row: int,
        col: int,
        piece: str,
        attacks_only: bool = False,
    ) -> List[Move]:
        moves: List[Move] = []
        direction = -1 if piece in WHITE_PIECES else 1

        def add_move(r: int, c: int, capture_only: bool = False) -> None:
            if not self.in_bounds(r, c):
                return
            target = self.board[r][c]
            if target is None and capture_only:
                return
            if target is not None:
                if self.is_white(piece) and self.is_white(target):
                    return
                if self.is_black(piece) and self.is_black(target):
                    return
            moves.append(Move(fr=(row, col), to=(r, c), piece=piece, captured=target))

        if piece.upper() == "P":
            start_row = 6 if piece == "P" else 1
            one_step = row + direction
            if self.in_bounds(one_step, col) and self.board[one_step][col] is None:
                if not attacks_only:
                    moves.append(Move(fr=(row, col), to=(one_step, col), piece=piece))
                    two_step = row + 2 * direction
                    if row == start_row and self.board[two_step][col] is None:
                        moves.append(
                            Move(fr=(row, col), to=(two_step, col), piece=piece)
                        )
            for dc in (-1, 1):
                capture_row = row + direction
                capture_col = col + dc
                if self.in_bounds(capture_row, capture_col):
                    target = self.board[capture_row][capture_col]
                    if target is not None and (
                        self.is_white(piece) != self.is_white(target)
                    ):
                        moves.append(
                            Move(
                                fr=(row, col),
                                to=(capture_row, capture_col),
                                piece=piece,
                                captured=target,
                            )
                        )
                    if self.en_passant_target == (capture_row, capture_col):
                        moves.append(
                            Move(
                                fr=(row, col),
                                to=(capture_row, capture_col),
                                piece=piece,
                                captured="p" if piece == "P" else "P",
                                is_en_passant=True,
                            )
                        )
        elif piece.upper() == "N":
            for dr, dc in (
                (2, 1),
                (2, -1),
                (-2, 1),
                (-2, -1),
                (1, 2),
                (1, -2),
                (-1, 2),
                (-1, -2),
            ):
                add_move(row + dr, col + dc)
        elif piece.upper() in {"B", "R", "Q"}:
            directions = []
            if piece.upper() in {"B", "Q"}:
                directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
            if piece.upper() in {"R", "Q"}:
                directions.extend([(1, 0), (-1, 0), (0, 1), (0, -1)])
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while self.in_bounds(r, c):
                    target = self.board[r][c]
                    if target is None:
                        moves.append(Move(fr=(row, col), to=(r, c), piece=piece))
                    else:
                        if self.is_white(piece) != self.is_white(target):
                            moves.append(
                                Move(
                                    fr=(row, col),
                                    to=(r, c),
                                    piece=piece,
                                    captured=target,
                                )
                            )
                        break
                    r += dr
                    c += dc
        elif piece.upper() == "K":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    add_move(row + dr, col + dc)
            if not attacks_only:
                moves.extend(self._castling_moves(row, col, piece))
        return moves

    def _castling_moves(self, row: int, col: int, piece: str) -> List[Move]:
        moves: List[Move] = []
        if self.in_check(self.is_white(piece)):
            return moves
        if piece == "K":
            if self.castling_rights["K"]:
                if (
                    self.board[7][5] is None
                    and self.board[7][6] is None
                    and not self.is_square_attacked(7, 5, by_white=False)
                    and not self.is_square_attacked(7, 6, by_white=False)
                ):
                    moves.append(
                        Move(
                            fr=(7, 4),
                            to=(7, 6),
                            piece=piece,
                            is_castling=True,
                        )
                    )
            if self.castling_rights["Q"]:
                if (
                    self.board[7][3] is None
                    and self.board[7][2] is None
                    and self.board[7][1] is None
                    and not self.is_square_attacked(7, 3, by_white=False)
                    and not self.is_square_attacked(7, 2, by_white=False)
                ):
                    moves.append(
                        Move(
                            fr=(7, 4),
                            to=(7, 2),
                            piece=piece,
                            is_castling=True,
                        )
                    )
        if piece == "k":
            if self.castling_rights["k"]:
                if (
                    self.board[0][5] is None
                    and self.board[0][6] is None
                    and not self.is_square_attacked(0, 5, by_white=True)
                    and not self.is_square_attacked(0, 6, by_white=True)
                ):
                    moves.append(
                        Move(
                            fr=(0, 4),
                            to=(0, 6),
                            piece=piece,
                            is_castling=True,
                        )
                    )
            if self.castling_rights["q"]:
                if (
                    self.board[0][3] is None
                    and self.board[0][2] is None
                    and self.board[0][1] is None
                    and not self.is_square_attacked(0, 3, by_white=True)
                    and not self.is_square_attacked(0, 2, by_white=True)
                ):
                    moves.append(
                        Move(
                            fr=(0, 4),
                            to=(0, 2),
                            piece=piece,
                            is_castling=True,
                        )
                    )
        return moves

    def _make_move(self, move: Move) -> None:
        fr_r, fr_c = move.fr
        to_r, to_c = move.to
        piece = move.piece
        captured = self.board[to_r][to_c]

        if move.is_en_passant:
            capture_row = fr_r
            self.board[capture_row][to_c] = None

        self.board[to_r][to_c] = piece
        self.board[fr_r][fr_c] = None

        if piece.upper() == "P" and (to_r == 0 or to_r == 7):
            move.promotion = "Q" if piece.isupper() else "q"
            self.board[to_r][to_c] = move.promotion

        if move.is_castling:
            if to_c == 6:
                rook_from = (to_r, 7)
                rook_to = (to_r, 5)
            else:
                rook_from = (to_r, 0)
                rook_to = (to_r, 3)
            rook_piece = self.board[rook_from[0]][rook_from[1]]
            self.board[rook_to[0]][rook_to[1]] = rook_piece
            self.board[rook_from[0]][rook_from[1]] = None

        move.captured = captured
        self._update_castling_rights(move)
        self._update_en_passant(move)
        self.move_history.append(move)
        self.white_to_move = not self.white_to_move

    def _update_castling_rights(self, move: Move) -> None:
        fr_r, fr_c = move.fr
        to_r, to_c = move.to
        piece = move.piece
        if piece == "K":
            self.castling_rights["K"] = False
            self.castling_rights["Q"] = False
        if piece == "k":
            self.castling_rights["k"] = False
            self.castling_rights["q"] = False
        if piece == "R" and fr_r == 7:
            if fr_c == 0:
                self.castling_rights["Q"] = False
            if fr_c == 7:
                self.castling_rights["K"] = False
        if piece == "r" and fr_r == 0:
            if fr_c == 0:
                self.castling_rights["q"] = False
            if fr_c == 7:
                self.castling_rights["k"] = False
        if move.captured == "R" and to_r == 7:
            if to_c == 0:
                self.castling_rights["Q"] = False
            if to_c == 7:
                self.castling_rights["K"] = False
        if move.captured == "r" and to_r == 0:
            if to_c == 0:
                self.castling_rights["q"] = False
            if to_c == 7:
                self.castling_rights["k"] = False

    def _update_en_passant(self, move: Move) -> None:
        self.en_passant_target = None
        fr_r, fr_c = move.fr
        to_r, to_c = move.to
        if move.piece.upper() == "P" and abs(to_r - fr_r) == 2:
            middle_row = (fr_r + to_r) // 2
            self.en_passant_target = (middle_row, fr_c)

    def _undo_move(self) -> None:
        if not self.move_history:
            return
        move = self.move_history.pop()
        fr_r, fr_c = move.fr
        to_r, to_c = move.to
        piece = move.piece

        self.board[fr_r][fr_c] = piece
        self.board[to_r][to_c] = move.captured

        if move.is_en_passant:
            capture_row = fr_r
            self.board[capture_row][to_c] = "p" if piece == "P" else "P"
            self.board[to_r][to_c] = None

        if move.is_castling:
            if to_c == 6:
                rook_from = (to_r, 7)
                rook_to = (to_r, 5)
            else:
                rook_from = (to_r, 0)
                rook_to = (to_r, 3)
            rook_piece = self.board[rook_to[0]][rook_to[1]]
            self.board[rook_from[0]][rook_from[1]] = rook_piece
            self.board[rook_to[0]][rook_to[1]] = None

        if move.promotion:
            self.board[fr_r][fr_c] = "P" if piece.isupper() else "p"

        self.white_to_move = not self.white_to_move
        self._recompute_state()

    def _recompute_state(self) -> None:
        self.castling_rights = {"K": True, "Q": True, "k": True, "q": True}
        self.en_passant_target = None
        saved_history = list(self.move_history)
        self.move_history = []
        self.board = self._initial_board()
        self.white_to_move = True
        for move in saved_history:
            self._make_move(move)


class ChessAI:
    def __init__(self, depth: int = 2) -> None:
        self.depth = depth

    def choose_move(self, game: ChessGame) -> Optional[Move]:
        best_score = float("inf")
        best_move = None
        for move in game.legal_moves(white=False):
            game._make_move(move)
            score = self._minimax(game, self.depth - 1, True, float("-inf"), float("inf"))
            game._undo_move()
            if score < best_score:
                best_score = score
                best_move = move
        return best_move

    def _evaluate(self, game: ChessGame) -> int:
        score = 0
        for row in game.board:
            for piece in row:
                if piece:
                    score += PIECE_VALUE[piece]
        return score

    def _minimax(
        self, game: ChessGame, depth: int, maximizing: bool, alpha: float, beta: float
    ) -> int:
        if depth == 0:
            return self._evaluate(game)
        white = maximizing
        moves = game.legal_moves(white=white)
        if not moves:
            if game.in_check(white):
                return -99999 if maximizing else 99999
            return 0
        if maximizing:
            max_eval = float("-inf")
            for move in moves:
                game._make_move(move)
                eval_score = self._minimax(game, depth - 1, False, alpha, beta)
                game._undo_move()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return int(max_eval)
        min_eval = float("inf")
        for move in moves:
            game._make_move(move)
            eval_score = self._minimax(game, depth - 1, True, alpha, beta)
            game._undo_move()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return int(min_eval)


class ChessUI:
    def __init__(self) -> None:
        self.game = ChessGame()
        self.ai = ChessAI(depth=2)
        self.selected: Optional[Tuple[int, int]] = None
        self.legal_for_selected: List[Move] = []
        self.status_text = "White to move"

        self.root = tk.Tk()
        self.root.title("Chess vs AI")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_SIZE,
            height=WINDOW_SIZE,
            highlightthickness=0,
        )
        self.canvas.pack()
        self.status_label = tk.Label(self.root, text=self.status_text, font=("Arial", 12))
        self.status_label.pack(pady=6)

        self.canvas.bind("<Button-1>", self.on_click)
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        colors = ("#f0d9b5", "#b58863")
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = colors[(r + c) % 2]
                x1 = c * SQUARE_SIZE
                y1 = r * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
        if self.selected:
            self._highlight_square(*self.selected, "#f5f669")
            for move in self.legal_for_selected:
                self._highlight_square(*move.to, "#8fd18f")
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.game.board[r][c]
                if piece:
                    x = c * SQUARE_SIZE + SQUARE_SIZE // 2
                    y = r * SQUARE_SIZE + SQUARE_SIZE // 2
                    self.canvas.create_text(
                        x,
                        y,
                        text=PIECE_TO_SYMBOL[piece],
                        font=("Arial", 32),
                    )
        self.status_label.config(text=self.status_text)

    def _highlight_square(self, row: int, col: int, color: str) -> None:
        x1 = col * SQUARE_SIZE
        y1 = row * SQUARE_SIZE
        x2 = x1 + SQUARE_SIZE
        y2 = y1 + SQUARE_SIZE
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3)

    def on_click(self, event: tk.Event) -> None:
        if not self.game.white_to_move:
            return
        row = event.y // SQUARE_SIZE
        col = event.x // SQUARE_SIZE
        if not self.game.in_bounds(row, col):
            return
        piece = self.game.board[row][col]
        if self.selected:
            for move in self.legal_for_selected:
                if move.to == (row, col):
                    self.game._make_move(move)
                    self.selected = None
                    self.legal_for_selected = []
                    self._after_player_move()
                    return
            self.selected = None
            self.legal_for_selected = []
        if piece and piece in WHITE_PIECES:
            self.selected = (row, col)
            self.legal_for_selected = [
                move
                for move in self.game.legal_moves(white=True)
                if move.fr == (row, col)
            ]
        self.draw()

    def _after_player_move(self) -> None:
        self._update_status()
        self.draw()
        self.root.after(200, self._ai_move)

    def _ai_move(self) -> None:
        if self.game.white_to_move:
            return
        move = self.ai.choose_move(self.game)
        if move:
            self.game._make_move(move)
        self._update_status()
        self.draw()

    def _update_status(self) -> None:
        white_moves = self.game.legal_moves(white=True)
        black_moves = self.game.legal_moves(white=False)
        if self.game.white_to_move:
            if not white_moves:
                if self.game.in_check(True):
                    self.status_text = "Checkmate! Black wins."
                else:
                    self.status_text = "Stalemate."
            else:
                self.status_text = "White to move"
        else:
            if not black_moves:
                if self.game.in_check(False):
                    self.status_text = "Checkmate! White wins."
                else:
                    self.status_text = "Stalemate."
            else:
                self.status_text = "Black to move (AI)"

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    ui = ChessUI()
    ui.run()


if __name__ == "__main__":
    main()
