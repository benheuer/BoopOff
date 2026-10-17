"""CatGPT: a Boop bot with a configurable search depth.

This file uses only Python's standard library and the existing game files.
The important idea is: try our moves, then check what the opponent could do.
"""

import copy

from bot import BoopBot
from rules import IllegalMove, get_lines, to_coord


# Winning must be worth much more than any normal board position.
WIN_SCORE = 1_000_000

# These are all the possible three-in-a-row lines on the board.
LINES = get_lines()


class CatGPT(BoopBot):
    """Choose moves by looking ahead a configurable number of turns."""

    def __init__(self, search_depth=2):
        """Set how many player turns to look ahead, including our first move.

        Depth 1 checks our move, depth 2 also checks the opponent's reply,
        and depth 3 also checks our next move. Larger depths take more time.
        """
        if (
            not isinstance(search_depth, int)
            or isinstance(search_depth, bool)
            or search_depth < 1
        ):
            raise ValueError("search_depth must be a positive integer.")

        self.search_depth = search_depth

    def give_move(self, moves, board, player):
        """Return one of the legal moves supplied by the game."""
        if not moves:
            raise ValueError("CatGPT needs at least one legal move.")

        best_move = moves[0]
        best_score = float("-inf")

        for move in moves:
            # A move can lead to several boards if we have growth choices.
            possible_boards = self._finish_move(board, move, player)

            for next_board in possible_boards:
                score = self._search(
                    next_board,
                    turns_left=self.search_depth - 1,
                    next_player=3 - player,
                    our_player=player,
                    lower_bound=best_score,
                    upper_bound=float("inf"),
                )

                if score > best_score:
                    best_score = score
                    best_move = move

        return best_move

    def give_grow(self, grows, board, player):
        """Choose a line of kittens to grow, or one kitten to retire."""
        if not grows:
            raise ValueError("CatGPT needs at least one legal growth.")

        best_grow = grows[0]
        best_score = float("-inf")

        for grow in grows:
            # Work on a copy so we do not change the real game board.
            next_board = copy.deepcopy(board)
            next_board.grow(grow)

            score = self._search(
                next_board,
                turns_left=self.search_depth - 1,
                next_player=3 - player,
                our_player=player,
                lower_bound=best_score,
                upper_bound=float("inf"),
            )

            if score > best_score:
                best_score = score
                best_grow = grow

        return best_grow

    def _search(self, board, turns_left, next_player, our_player,
                lower_bound, upper_bound):
        """Look ahead by calling this method again with one fewer turn.

        We choose high scores on our turns. The opponent chooses low scores.
        The two bounds let us skip choices that cannot change the decision.
        """
        if board.is_terminal():
            return self._score_position(board, our_player)

        try:
            moves = board.get_legals(next_player)
        except IllegalMove:
            # The runner ends an unplayable turn as a draw. Check this even
            # at the search limit, before estimating a nonterminal position.
            return 0

        if turns_left == 0 or not moves:
            return self._score_position(board, our_player)

        our_turn = next_player == our_player
        best_score = float("-inf") if our_turn else float("inf")

        for move in moves:
            possible_boards = self._finish_move(board, move, next_player)

            for next_board in possible_boards:
                score = self._search(
                    next_board,
                    turns_left=turns_left - 1,
                    next_player=3 - next_player,
                    our_player=our_player,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                )

                if our_turn:
                    best_score = max(best_score, score)
                    lower_bound = max(lower_bound, best_score)
                else:
                    best_score = min(best_score, score)
                    upper_bound = min(upper_bound, best_score)

                # Our best alternative is already at least as good as the
                # opponent will allow here, so checking more cannot help.
                if lower_bound >= upper_bound:
                    return best_score

        return best_score

    def _finish_move(self, board, move, player):
        """Finish a placement, then apply one growth or retirement if needed."""
        next_board = copy.deepcopy(board)
        next_board.play(move)

        # The game checks for a winner before anyone grows kittens.
        if next_board.is_terminal():
            return [next_board]

        # get_grows() includes both players' choices. Only the mover acts,
        # and a line of three kittens takes priority over retiring one kitten.
        kitten = -1 if player == 1 else 1
        line_growths = []
        retirements = []

        for choice in next_board.get_grows():
            kind, where = choice
            if kind == "grow":
                index = where[0]
            else:
                index = where
            row, column = to_coord(index)

            if next_board.board[row][column] != kitten:
                continue
            if kind == "grow":
                line_growths.append(choice)
            else:
                retirements.append(choice)

        if line_growths:
            growth_choices = line_growths
        else:
            growth_choices = retirements
        if not growth_choices:
            return [next_board]

        possible_boards = []

        # Apply one growth or retirement, trying each choice on its own copy.
        for grow in growth_choices:
            grown_board = copy.deepcopy(next_board)
            grown_board.grow(grow)
            possible_boards.append(grown_board)

        return possible_boards

    def _score_position(self, board, player):
        """Give a board a number: larger numbers are better for our player."""
        winner = board.is_terminal()

        if winner == player:
            return WIN_SCORE
        if winner != 0:
            return -WIN_SCORE

        our_score = self._score_for_player(board, player)
        opponent_score = self._score_for_player(board, 3 - player)
        return our_score - opponent_score

    def _score_for_player(self, board, player):
        """Add points for cats, central pieces, and promising pairs."""
        kitten = -1 if player == 1 else 1
        cat = 2 * kitten

        # Cats in hand can be played later. Kittens can become more cats.
        score = 180 * board.hands[player - 1][1]

        for row in range(6):
            for column in range(6):
                piece = board.board[row][column]

                if piece == cat:
                    score += 190
                elif piece == kitten:
                    score += 6
                else:
                    continue

                # Central squares are farther from edges that pieces fall off.
                distance_from_edges = min(row, 5 - row) + min(column, 5 - column)
                score += 2 * distance_from_edges

        for line in LINES:
            cat_count = 0
            kitten_count = 0
            has_opponent_piece = False

            for index in line:
                row, column = to_coord(index)
                piece = board.board[row][column]

                if piece == cat:
                    cat_count += 1
                elif piece == kitten:
                    kitten_count += 1
                elif piece != 0:
                    has_opponent_piece = True

            # A blocked line is less promising than an open one.
            if has_opponent_piece:
                continue

            if cat_count == 2 and kitten_count == 0:
                score += 36
            elif kitten_count == 2 and cat_count == 0:
                score += 12
            elif cat_count == 1 and kitten_count == 0:
                score += 3

        return score
