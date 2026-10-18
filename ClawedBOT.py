"""Clawed: a time-limited Boop searcher.

Clawed copies the board into flat lists once per turn, then runs
iterative-deepening negamax with alpha-beta pruning and a transposition
table on that copy. It never touches the Board object it is given, and its
own copy of the rules is checked against rules.py by test_clawed.py.
"""

import time

from bot import BoopBot
from rules import get_lines


WIN = 1_000_000
LINES = get_lines()

# Every line through each cell, so threat checks only look where they need to.
LINES_THROUGH = [[line for line in LINES if cell in line] for cell in range(36)]

# For each cell: (neighbour, landing cell or -1 for off the board).
NEIGHBOURS = []
for _cell in range(36):
    _row, _col = divmod(_cell, 6)
    _pairs = []
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr == 0 and _dc == 0:
                continue
            _nr, _nc = _row + _dr, _col + _dc
            if not (0 <= _nr <= 5 and 0 <= _nc <= 5):
                continue
            _lr, _lc = _row + 2 * _dr, _col + 2 * _dc
            _land = _lr * 6 + _lc if 0 <= _lr <= 5 and 0 <= _lc <= 5 else -1
            _pairs.append((_nr * 6 + _nc, _land))
    NEIGHBOURS.append(tuple(_pairs))

# Central squares are safer: a piece there cannot be booped off in one push.
CENTRALITY = [min(c // 6, 5 - c // 6) + min(c % 6, 5 - c % 6) for c in range(36)]
# Try central squares first; good moves early means more pruning.
CELL_ORDER = sorted(range(36), key=lambda c: -CENTRALITY[c])


class _OutOfTime(Exception):
    pass


class Clawed(BoopBot):
    """Searches as deep as it can within a time budget per decision."""

    def __init__(self, time_limit=1.0, max_depth=12):
        """time_limit is seconds per decision; max_depth caps the search.

        With time_limit=None the bot searches exactly max_depth plies and is
        fully deterministic, which is what the tests use.
        """
        if time_limit is not None and (
            isinstance(time_limit, bool)
            or not isinstance(time_limit, (int, float))
            or time_limit <= 0
        ):
            raise ValueError("time_limit must be a positive number or None.")
        if isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 1:
            raise ValueError("max_depth must be a positive integer.")
        self.time_limit = time_limit
        self.max_depth = max_depth
        self._deadline = None
        self._table = {}
        self._nodes = 0

    # ----- the BoopBot interface -------------------------------------------

    def give_move(self, moves, board, player):
        if not moves:
            raise ValueError("Clawed needs at least one legal move.")
        cells, hands = _flatten(board)

        def children():
            for move in moves:
                yield move, self._after_move(cells, hands, move, player)

        return self._choose(children, player, default=moves[0])

    def give_grow(self, grows, board, player):
        if not grows:
            raise ValueError("Clawed needs at least one legal growth.")
        cells, hands = _flatten(board)

        def children():
            for grow in grows:
                next_cells, next_hands = _grow(cells, hands, grow)
                yield grow, [(0, next_cells, next_hands)]

        return self._choose(children, player, default=grows[0])

    # ----- search ------------------------------------------------------------

    def _choose(self, children, player, default):
        """Iterative deepening over root choices; keeps the last full result."""
        self._deadline = (
            None if self.time_limit is None
            else time.perf_counter() + self.time_limit
        )
        self._table = {}
        self._nodes = 0

        roots = list(children())
        # Take a win on the spot; nothing deeper can beat it.
        for choice, outcomes in roots:
            if any(winner == player for winner, _, _ in outcomes):
                return choice

        best = default
        for depth in range(1, self.max_depth + 1):
            try:
                scored = []
                alpha = -WIN - 1
                for choice, outcomes in roots:
                    score = self._outcome_value(outcomes, player, depth - 1, alpha, WIN + 1)
                    scored.append((score, choice, outcomes))
                    alpha = max(alpha, score)
            except _OutOfTime:
                break
            # Stable sort: best first, ties keep the previous depth's order.
            scored.sort(key=lambda item: -item[0])
            roots = [(choice, outcomes) for _, choice, outcomes in scored]
            best = roots[0][0]
            if abs(scored[0][0]) >= WIN - 100:
                break  # forced result found; deeper search cannot change it
        return best

    def _outcome_value(self, outcomes, player, depth, alpha, beta):
        """Best value for `player` among the growth choices of one move."""
        best = -WIN - 1
        for winner, cells, hands in outcomes:
            if winner:
                score = WIN if winner == player else -WIN
            else:
                score = -self._negamax(cells, hands, 3 - player, depth, -beta, -alpha)
            if score > best:
                best = score
                alpha = max(alpha, score)
        return best

    def _negamax(self, cells, hands, player, depth, alpha, beta):
        self._nodes += 1
        if self._deadline is not None and not (self._nodes & 255):
            if time.perf_counter() > self._deadline:
                raise _OutOfTime

        if depth == 0:
            return _evaluate(cells, hands, player)

        key = (tuple(cells), tuple(hands), player)
        entry = self._table.get(key)
        first = None
        if entry is not None:
            entry_depth, flag, value, first = entry
            if entry_depth >= depth:
                if flag == 0:
                    return value
                if flag < 0 and value <= alpha:
                    return value
                if flag > 0 and value >= beta:
                    return value

        start_alpha = alpha
        best = -WIN - 1
        best_move = None
        for move in _ordered_moves(cells, hands, player, first):
            outcomes = self._after_move(cells, hands, move, player)
            score = self._outcome_value(outcomes, player, depth - 1, alpha, beta)
            # Prefer quicker wins and slower losses.
            if score > WIN - 1000:
                score -= 1
            elif score < -WIN + 1000:
                score += 1
            if score > best:
                best = score
                best_move = move
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        break

        if best_move is None:
            # Nothing in hand to place: main.py scores this as a draw.
            return 0

        flag = 0
        if best <= start_alpha:
            flag = -1
        elif best >= beta:
            flag = 1
        self._table[key] = (depth, flag, best, best_move)
        return best

    @staticmethod
    def _after_move(cells, hands, move, player):
        """All (winner, cells, hands) results of a move, one per growth choice.

        A growth choice is either graduating a line of kittens or, when the
        mover's hand is empty and there is no line, a forced retirement.
        """
        next_cells, next_hands = _play(cells, hands, move)
        winner = _winner(next_cells)
        if winner:
            return [(winner, next_cells, next_hands)]
        grows = _own_grows(next_cells, next_hands, player)
        if not grows:
            return [(0, next_cells, next_hands)]
        results = []
        for grow in grows:
            grown_cells, grown_hands = _grow(next_cells, next_hands, grow)
            results.append((0, grown_cells, grown_hands))
        return results


# ----- a flat copy of rules.py -----------------------------------------------
# hands is [blue kittens, blue cats, orange kittens, orange cats].

def _flatten(board):
    cells = [piece for row in board.board for piece in row]
    hands = [board.hands[0][0], board.hands[0][1], board.hands[1][0], board.hands[1][1]]
    return cells, hands


def _legal_moves(cells, hands, player):
    """Placements only; an empty hand has none (rules.py raises instead)."""
    sign = -1 if player == 1 else 1
    base = 0 if player == 1 else 2
    kittens, cats = hands[base], hands[base + 1]
    moves = []
    for cell in CELL_ORDER:
        if cells[cell] == 0:
            if cats:
                moves.append((2 * sign, cell))
            if kittens:
                moves.append((sign, cell))
    return moves


def _ordered_moves(cells, hands, player, first):
    moves = _legal_moves(cells, hands, player)
    if first is not None and first in moves:
        moves.remove(first)
        moves.insert(0, first)
    return moves


def _play(cells, hands, move):
    piece, cell = move
    cells = cells[:]
    hands = hands[:]
    cells[cell] = piece
    hands[(0 if piece < 0 else 2) + abs(piece) - 1] -= 1
    size = abs(piece)
    for neighbour, land in NEIGHBOURS[cell]:
        other = cells[neighbour]
        if other == 0 or size < abs(other):
            continue
        if land < 0:
            hands[(0 if other < 0 else 2) + abs(other) - 1] += 1
            cells[neighbour] = 0
        elif cells[land] == 0:
            cells[land] = other
            cells[neighbour] = 0
    return cells, hands


def _winner(cells):
    """Same answer, in the same order, as Board.is_terminal."""
    for a, b, c in LINES:
        piece = cells[a]
        if (piece == 2 or piece == -2) and cells[b] == piece and cells[c] == piece:
            return 1 if piece < 0 else 2
    if cells.count(-2) == 8:
        return 1
    if cells.count(2) == 8:
        return 2
    return 0


def _own_grows(cells, hands, player):
    """The mover's growth choices, in the same form and order as main.py."""
    kitten = -1 if player == 1 else 1
    lines = [("grow", line) for line in LINES
             if cells[line[0]] == kitten and cells[line[1]] == kitten
             and cells[line[2]] == kitten]
    if lines:
        return lines
    base = 0 if player == 1 else 2
    if hands[base] + hands[base + 1]:
        return []
    return [("remove", cell) for cell in range(36) if cells[cell] == kitten]


def _grow(cells, hands, grow):
    """Graduate a line, or retire one kitten; either way, cats go to hand."""
    kind, where = grow
    cells = cells[:]
    hands = hands[:]
    for cell in (where if kind == "grow" else (where,)):
        hands[1 if cells[cell] < 0 else 3] += 1
        cells[cell] = 0
    return cells, hands


# ----- evaluation ------------------------------------------------------------

def _side_score(cells, hands, player):
    sign = -1 if player == 1 else 1
    cat, kitten = 2 * sign, sign
    base = 0 if player == 1 else 2

    # Every cat owned is permanent progress; kittens on board can still grow.
    score = 120 * hands[base + 1]
    board_cats = 0
    for cell in range(36):
        piece = cells[cell]
        if piece == cat:
            board_cats += 1
            score += 130 + 6 * CENTRALITY[cell]
        elif piece == kitten:
            score += 8 + 3 * CENTRALITY[cell]

    for a, b, c in LINES:
        cats = kittens = 0
        for piece in (cells[a], cells[b], cells[c]):
            if piece == cat:
                cats += 1
            elif piece == kitten:
                kittens += 1
            elif piece != 0:
                break
        else:
            if cats == 2 and kittens == 0:
                score += 45
            elif kittens == 2 and cats == 0:
                score += 14
            elif cats == 2 and kittens == 1:
                score += 20  # one boop or removal away from a cat line
            elif cats == 1 and kittens == 0:
                score += 3

    # Close to the eight-cats-on-board win.
    if board_cats >= 6:
        score += 40 * (board_cats - 5)
    return score


def _can_win_now(cells, hands, player):
    """Exact one-move win check, run only when a win looks possible."""
    base = 0 if player == 1 else 2
    if not hands[base + 1]:
        return False
    cat = -2 if player == 1 else 2
    if cells.count(cat) < 7:
        hopeful = False
        for a, b, c in LINES:
            trio = (cells[a], cells[b], cells[c])
            if trio.count(cat) >= 2:
                hopeful = True
                break
        if not hopeful:
            return False
    for cell in range(36):
        if cells[cell] == 0:
            next_cells, _ = _play(cells, hands, (cat, cell))
            if _winner(next_cells) == player:
                return True
    return False


def _evaluate(cells, hands, player):
    """Score for the player about to move."""
    if _can_win_now(cells, hands, player):
        return WIN - 500
    return (_side_score(cells, hands, player)
            - _side_score(cells, hands, 3 - player) + 10)
