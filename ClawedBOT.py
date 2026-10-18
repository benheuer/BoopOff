"""Clawed: a Boop bot that thinks ahead.

Written by Claude, hence the name.

HOW CLAWED THINKS, IN FIVE IDEAS
================================

1. Look ahead ("search").
   To choose a move, Clawed imagines making each legal move, then imagines
   every reply the opponent could make, then every answer to that, and so on.
   Drawn out, this makes a "game tree": the current board is the root, and
   each move is a branch leading to a new board. One step down the tree (one
   player's turn) is called a "ply".

2. Assume the opponent is smart ("minimax").
   When Clawed imagines the opponent's turn, it assumes the opponent picks
   the move that is worst for Clawed. So a move is only as good as the
   opponent's best reply lets it be. We maximise our score on our turns and
   the opponent minimises it on theirs, hence the name "minimax".

   Clawed uses a common shortcut called "negamax": a score that is +50 for
   me is -50 for you. So instead of writing separate code for "my turn" and
   "your turn", one function always asks "how good is this for the player
   about to move?", and flips the sign of the answer whenever the turn
   passes to the other player.

3. Guess when you can't see the end ("evaluation").
   The full game tree is far too big to search, so Clawed stops after a few
   plies and estimates who is ahead using a scoring formula (_evaluate,
   near the bottom of this file). It counts cats, rewards pieces near the
   centre, and rewards lines that are close to winning or graduating.

4. Skip branches that can't matter ("alpha-beta pruning").
   Suppose one of our moves is already known to score 30. While checking a
   second move, we find an opponent reply that leaves us at 10. We can stop
   checking the second move right there: the opponent will make our result
   10 or worse, and we already have 30, so we'd never pick it. "alpha" is
   the score we are already guaranteed, and "beta" is the most the opponent
   will allow. Whenever alpha reaches beta, the rest of that branch is
   skipped. The answer is identical to searching everything, just faster.

5. Go deeper while there's time ("iterative deepening").
   Clawed searches 1 ply ahead, then 2, then 3, and so on, until its time
   runs out. If time runs out halfway through a depth, it uses the best move
   from the last depth it finished. Each pass also sorts the moves best
   first, so the next, deeper pass looks at the promising moves first, which
   makes pruning (idea 4) skip far more.

   Clawed also keeps a "memo table" (self._table) of boards it has already
   scored. Different move orders often reach the same board, and looking
   the score up is much faster than working it out again.

HOW THE BOARD IS STORED
=======================
rules.py stores the board as six rows of six. Searching makes copies of the
board millions of times, so Clawed uses simpler, faster-to-copy lists:

  cells: one list of 36 numbers, read left to right, top row first, so the
         square at (row, col) is cells[row * 6 + col]. The numbers mean the
         same as in rules.py: 0 empty, 1 orange kitten, 2 orange cat,
         -1 blue kitten, -2 blue cat.
  hands: one list of 4 numbers:
         [blue kittens, blue cats, orange kittens, orange cats].

Player 1 is blue (negative pieces) and player 2 is orange (positive pieces).
In several places, "sign" is -1 for blue and +1 for orange, so a piece
belongs to a player when piece * sign > 0.

Clawed has its own copy of the game rules for these lists (the "rules
copy" section below). test_clawed.py plays thousands of random moves to
check that it always agrees with rules.py.
"""

import time

from bot import BoopBot
from rules import get_lines


# A win is worth far more than any normal position, so the search always
# prefers a win over any material advantage.
WIN = 1_000_000

# All 80 three-in-a-row lines on the board, as triples of cell numbers.
LINES = get_lines()


def _build_neighbours():
    """For each square, list its neighbours and where a boop would push them.

    The answer for square s is a list of (neighbour, landing) pairs. A piece
    placed on s pushes its neighbour one step further in the same direction,
    onto the landing square. If that step would leave the board, landing is
    -1, which means the neighbour falls off. Working this out once, up front,
    saves doing the row and column arithmetic on every boop.
    """
    neighbours = []
    for cell in range(36):
        row, col = divmod(cell, 6)
        pairs = []
        for row_step in (-1, 0, 1):
            for col_step in (-1, 0, 1):
                if row_step == 0 and col_step == 0:
                    continue  # that's the square itself, not a neighbour
                next_row, next_col = row + row_step, col + col_step
                if not (0 <= next_row <= 5 and 0 <= next_col <= 5):
                    continue  # no neighbour in this direction
                land_row, land_col = row + 2 * row_step, col + 2 * col_step
                if 0 <= land_row <= 5 and 0 <= land_col <= 5:
                    landing = land_row * 6 + land_col
                else:
                    landing = -1
                pairs.append((next_row * 6 + next_col, landing))
        neighbours.append(tuple(pairs))
    return neighbours


NEIGHBOURS = _build_neighbours()

# How many steps each square is from the edge, counting rows and columns:
# 0 in a corner, up to 4 in the middle. A piece in the middle can't be
# booped off the board in a single push.
CENTRALITY = [min(c // 6, 5 - c // 6) + min(c % 6, 5 - c % 6) for c in range(36)]

# Squares from the middle outward. Moves are tried in this order because
# central moves are usually better, and trying good moves first helps
# alpha-beta skip more.
CELL_ORDER = sorted(range(36), key=lambda c: -CENTRALITY[c])


class _OutOfTime(Exception):
    """Raised deep inside the search to stop it when the time is up."""


class Clawed(BoopBot):
    """Searches as many turns ahead as it can within a time limit."""

    def __init__(self, time_limit=1.0, max_depth=12):
        """Set how long Clawed may think, and how deep it may look.

        time_limit is the number of seconds per decision. max_depth is the
        most plies Clawed will ever search, even with time to spare.

        With time_limit=None, Clawed searches exactly max_depth plies every
        time. It then always picks the same move for the same board, which
        is what the tests need.
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

        # Working state for one decision; _choose resets these each time.
        self._deadline = None  # the clock time at which to stop thinking
        self._table = {}       # memo table: board -> what we learned about it
        self._nodes = 0        # how many boards we've looked at

    # ----- what main.py calls -------------------------------------------------

    def give_move(self, moves, board, player):
        """Pick a placement from `moves`, the legal moves main.py offers."""
        if not moves:
            raise ValueError("Clawed needs at least one legal move.")
        cells, hands = _flatten(board)

        # For each move, every board it could lead to. A move can lead to
        # more than one board when it makes us choose a line to graduate.
        def choices():
            for move in moves:
                yield move, self._after_move(cells, hands, move, player)

        return self._choose(choices, player, default=moves[0])

    def give_grow(self, grows, board, player):
        """Pick which line to graduate, or which kitten to retire."""
        if not grows:
            raise ValueError("Clawed needs at least one legal growth.")
        cells, hands = _flatten(board)

        # Each growth choice leads to exactly one board, and nobody has won.
        def choices():
            for grow in grows:
                next_cells, next_hands = _grow(cells, hands, grow)
                yield grow, [(0, next_cells, next_hands)]

        return self._choose(choices, player, default=grows[0])

    # ----- the search -----------------------------------------------------------

    def _choose(self, choices, player, default):
        """Iterative deepening (idea 5): search deeper until time runs out.

        `choices` lists each option we could pick, along with the boards it
        leads to. Returns the option that scored best at the deepest search
        we finished.
        """
        if self.time_limit is None:
            self._deadline = None
        else:
            self._deadline = time.perf_counter() + self.time_limit
        self._table = {}
        self._nodes = 0

        options = list(choices())

        # If an option wins on the spot, take it. Nothing can beat a win.
        for option, outcomes in options:
            if any(winner == player for winner, _, _ in outcomes):
                return option

        best = default
        for depth in range(1, self.max_depth + 1):
            try:
                scored = []
                alpha = -WIN - 1  # best score found so far at this depth
                for option, outcomes in options:
                    score = self._best_outcome(outcomes, player, depth - 1, alpha, WIN + 1)
                    scored.append((score, option, outcomes))
                    alpha = max(alpha, score)
            except _OutOfTime:
                break  # keep the answer from the last depth we finished

            # Best options first, ready for the next, deeper pass. Python's
            # sort keeps tied options in their old order.
            scored.sort(key=lambda item: -item[0])
            options = [(option, outcomes) for _, option, outcomes in scored]
            best = options[0][0]

            # A score this close to WIN means we found a forced win (or
            # loss). Searching deeper won't change that.
            if abs(scored[0][0]) >= WIN - 100:
                break
        return best

    def _best_outcome(self, outcomes, player, depth, alpha, beta):
        """Score one move for `player`, who just made it.

        `outcomes` holds the boards the move can lead to: usually one, or
        several when the move lets us pick a line to graduate. We get to pick,
        so the move is worth its best outcome. Each outcome is a tuple
        (winner, cells, hands), where winner is 0 if nobody has won yet.
        """
        best = -WIN - 1
        for winner, cells, hands in outcomes:
            if winner:
                score = WIN if winner == player else -WIN
            else:
                # Now it is the opponent's turn. Their score is the opposite
                # of ours, so we flip the sign of their answer, and flip and
                # swap the alpha-beta window to match (idea 2's negamax).
                score = -self._negamax(cells, hands, 3 - player, depth, -beta, -alpha)
            if score > best:
                best = score
                alpha = max(alpha, score)
        return best

    def _negamax(self, cells, hands, player, depth, alpha, beta):
        """How good is this board for `player`, who is about to move?

        Searches `depth` more plies (ideas 1 to 4), and returns a score from
        `player`'s point of view: positive is good for them.

        alpha and beta form the window from idea 4. alpha is what `player`
        is already guaranteed elsewhere in the tree, and beta is the most the
        opponent will allow. Once a move here reaches beta, the opponent
        would never let the game reach this board, so we stop early.
        """
        # Check the clock every 256 boards. Checking every time would slow
        # the search down.
        self._nodes += 1
        if self._deadline is not None and self._nodes % 256 == 0:
            if time.perf_counter() > self._deadline:
                raise _OutOfTime

        # Out of depth: estimate instead of searching further (idea 3).
        if depth == 0:
            return _evaluate(cells, hands, player)

        # Have we scored this exact board before (idea 5's memo table)?
        # Each entry is (depth searched, kind of score, score, best move).
        # The kind of score is:
        #    0  the exact score
        #   -1  "at most this": every move failed to beat alpha
        #   +1  "at least this": we stopped early because a move reached beta
        # An entry is only trusted when it searched at least as deep as we
        # would now. Even when it isn't trusted, its best move is a good
        # one to try first.
        key = (tuple(cells), tuple(hands), player)
        entry = self._table.get(key)
        try_first = None
        if entry is not None:
            entry_depth, kind, value, try_first = entry
            if entry_depth >= depth:
                if kind == 0:
                    return value
                if kind < 0 and value <= alpha:
                    return value
                if kind > 0 and value >= beta:
                    return value

        alpha_at_start = alpha
        best = -WIN - 1
        best_move = None
        for move in _ordered_moves(cells, hands, player, try_first):
            outcomes = self._after_move(cells, hands, move, player)
            score = self._best_outcome(outcomes, player, depth - 1, alpha, beta)

            # Shrink win and loss scores a little with every ply, so a win in
            # 2 scores higher than a win in 4, and a loss in 4 scores higher
            # than a loss in 2. Clawed wins quickly and loses slowly.
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
                        break  # pruned (idea 4): the opponent won't allow this

        if best_move is None:
            # No pieces in hand, so no legal moves. main.py calls this a draw.
            return 0

        # Remember what we learned for next time.
        if best <= alpha_at_start:
            kind = -1
        elif best >= beta:
            kind = 1
        else:
            kind = 0
        self._table[key] = (depth, kind, best, best_move)
        return best

    @staticmethod
    def _after_move(cells, hands, move, player):
        """Every board a move can lead to, once the whole turn is over.

        A turn is: place a piece (which boops its neighbours), check for a
        win, then make one growth choice if there is one. The growth choice
        is either graduating a line of three of our pieces, or, when our hand
        is empty and there is no such line, retiring one kitten. Returns a
        list of (winner, cells, hands), one for each growth choice.
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


# ----- the rules copy -------------------------------------------------------
# The same rules as rules.py and main.py, using the cells and hands lists
# from the top of this file. Each function returns new lists rather than
# changing the ones it is given, so the search can try a move without having
# to undo it afterwards.

def _flatten(board):
    """Turn a rules.py Board into our cells and hands lists."""
    cells = [piece for row in board.board for piece in row]
    hands = [board.hands[0][0], board.hands[0][1], board.hands[1][0], board.hands[1][1]]
    return cells, hands


def _legal_moves(cells, hands, player):
    """Every placement `player` can make, central squares first.

    A move is (piece, cell), the same as in rules.py. With an empty hand
    there are none; rules.py raises IllegalMove in that case instead.
    """
    sign = -1 if player == 1 else 1
    hand = 0 if player == 1 else 2  # where this player's counts start in hands
    kittens, cats = hands[hand], hands[hand + 1]
    moves = []
    for cell in CELL_ORDER:
        if cells[cell] == 0:
            if cats:
                moves.append((2 * sign, cell))
            if kittens:
                moves.append((sign, cell))
    return moves


def _ordered_moves(cells, hands, player, try_first):
    """The legal moves, with `try_first` moved to the front if it's one."""
    moves = _legal_moves(cells, hands, player)
    if try_first is not None and try_first in moves:
        moves.remove(try_first)
        moves.insert(0, try_first)
    return moves


def _play(cells, hands, move):
    """Place a piece and boop its neighbours, the same as Board.play."""
    piece, cell = move
    cells = cells[:]  # [:] copies the list
    hands = hands[:]
    cells[cell] = piece
    # Take the piece out of the mover's hand. Its slot in hands is
    # 0 or 1 for blue, 2 or 3 for orange (kittens first, then cats).
    hands[(0 if piece < 0 else 2) + abs(piece) - 1] -= 1

    size = abs(piece)  # 1 for a kitten, 2 for a cat
    for neighbour, landing in NEIGHBOURS[cell]:
        other = cells[neighbour]
        if other == 0 or size < abs(other):
            continue  # empty square, or a kitten trying to push a cat
        if landing < 0:
            # Pushed off the board: the piece goes back to its owner's hand.
            hands[(0 if other < 0 else 2) + abs(other) - 1] += 1
            cells[neighbour] = 0
        elif cells[landing] == 0:
            cells[landing] = other
            cells[neighbour] = 0
        # Otherwise the landing square is taken, so the piece stays put.
    return cells, hands


def _winner(cells):
    """1 if blue has won, 2 if orange has, 0 if nobody has.

    A win is three cats of one colour in a line, or all eight of a player's
    cats on the board. Lines are checked in the same order as
    Board.is_terminal, so on the rare board where both players have a line,
    we agree with rules.py about who won.
    """
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
    """The growth choices main.py would offer `player` after their move.

    Any line of three of the player's own pieces (kittens and cats, mixed in
    any way) can graduate. Only if there is no such line, and the player's
    hand is empty, must they retire one kitten instead. Choices look like
    ("grow", (a, b, c)) or ("remove", cell), in the same order as main.py.
    """
    sign = -1 if player == 1 else 1
    lines = [("grow", line) for line in LINES
             if cells[line[0]] * sign > 0 and cells[line[1]] * sign > 0
             and cells[line[2]] * sign > 0]
    if lines:
        return lines
    hand = 0 if player == 1 else 2
    if hands[hand] + hands[hand + 1]:
        return []  # pieces still in hand, so nothing to do
    kitten = sign
    return [("remove", cell) for cell in range(36) if cells[cell] == kitten]


def _grow(cells, hands, grow):
    """Apply one growth choice. Every piece removed goes to hand as a cat."""
    kind, where = grow
    cells = cells[:]
    hands = hands[:]
    removed = where if kind == "grow" else (where,)  # three squares, or one
    for cell in removed:
        hands[1 if cells[cell] < 0 else 3] += 1  # slot 1 is blue cats, 3 orange
        cells[cell] = 0
    return cells, hands


# ----- scoring a board (idea 3) ----------------------------------------------
# These numbers were picked by hand and then checked by playing Clawed
# against the other bots. They aren't magic: changing them changes Clawed's
# style.

def _side_score(cells, hands, player):
    """Points for how well `player` is doing, ignoring the opponent."""
    sign = -1 if player == 1 else 1
    cat, kitten = 2 * sign, sign
    hand = 0 if player == 1 else 2

    # Cats are what wins, and every cat a player gets is theirs for good,
    # so each cat in hand is worth a lot.
    score = 120 * hands[hand + 1]

    # Pieces on the board: cats count more than kittens, and both count
    # more in the middle, where they are harder to push off.
    board_cats = 0
    for cell in range(36):
        piece = cells[cell]
        if piece == cat:
            board_cats += 1
            score += 130 + 6 * CENTRALITY[cell]
        elif piece == kitten:
            score += 8 + 3 * CENTRALITY[cell]

    # Lines that are filling up with our pieces. A line with any opponent
    # piece in it is blocked, and scores nothing.
    for a, b, c in LINES:
        cats = kittens = 0
        for piece in (cells[a], cells[b], cells[c]):
            if piece == cat:
                cats += 1
            elif piece == kitten:
                kittens += 1
            elif piece != 0:
                break  # an opponent's piece: this line is blocked
        else:
            # Python runs this "else" only if the loop above did not break.
            if cats == 2 and kittens == 0:
                score += 45  # one more cat here wins the game
            elif cats + kittens == 2:
                score += 14  # one more piece here graduates the line
            elif cats + kittens == 3:
                score += 20  # graduates on our next move unless broken up
            elif cats == 1 and kittens == 0:
                score += 3

    # Getting close to the other way to win: all eight cats on the board.
    if board_cats >= 6:
        score += 40 * (board_cats - 5)
    return score


def _can_win_now(cells, hands, player):
    """Can `player`, who is about to move, win with their very next placement?

    This is checked when the search runs out of depth, so Clawed doesn't
    mistake a board where the opponent is about to win for a good one.
    Trying every placement is slow, so it first does a quick check and only
    tries them all when a win looks possible.
    """
    hand = 0 if player == 1 else 2
    if not hands[hand + 1]:
        return False  # both ways to win need a cat to place
    cat = -2 if player == 1 else 2

    # Quick check: most wins come from a line that already has two of our
    # cats in it, or from having seven cats on the board already. This is a
    # shortcut, not a rule: a placement that boops a cat into line can
    # occasionally win without either. Missing that rare case only makes
    # the estimate slightly less accurate; the search still finds those
    # wins when it has depth to spare.
    if cells.count(cat) < 7:
        if not any((cells[a], cells[b], cells[c]).count(cat) >= 2 for a, b, c in LINES):
            return False

    # A win looks possible, so try placing a cat on every empty square.
    for cell in range(36):
        if cells[cell] == 0:
            next_cells, _ = _play(cells, hands, (cat, cell))
            if _winner(next_cells) == player:
                return True
    return False


def _evaluate(cells, hands, player):
    """Estimate how good a board is for `player`, who is about to move.

    It's our points minus the opponent's points, plus a small bonus because
    moving next is an advantage. If `player` can win right away, the board
    is scored as almost a win.
    """
    if _can_win_now(cells, hands, player):
        return WIN - 500
    return (_side_score(cells, hands, player)
            - _side_score(cells, hands, 3 - player) + 10)
