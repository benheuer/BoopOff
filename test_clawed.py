"""Tests for Clawed. Run them with: python3 -m unittest test_clawed

There are two kinds of test here:

- Rules tests check that Clawed's own copy of the rules (in ClawedBOT.py)
  always agrees with the real rules in rules.py and main.py. Clawed bases
  every decision on its copy, so if the two disagreed, it would be
  planning for a different game than the one it is playing.
- Tactics tests set up a small position where there is one clearly right
  answer, such as taking a win or blocking one, and check that Clawed
  finds it. Each runs once as blue and once as orange, since the colours
  use opposite signs and a bug often shows up in only one of them.

These tests use fixed() rather than Clawed() so that the search depth, and
so the answer, is the same every time, however fast the computer is.
"""

import copy
import random
import unittest

from bot import BoopBot
from main import BOTS, own_grows
from ClawedBOT import Clawed, _flatten, _grow, _legal_moves, _own_grows, _play, _winner
from rules import Board, IllegalMove


def position(pieces=(), hands=None):
    """Build a Board from (row, col, piece) triples; every other square is empty."""
    cells = [[0] * 6 for _ in range(6)]
    for row, col, piece in pieces:
        cells[row][col] = piece
    return Board(cells, hands if hands is not None else [[8, 0], [8, 0]])


def can_win_next(board, player):
    """Can `player` win this turn? Checked by trying every move with rules.py."""
    for move in board.get_legals(player):
        state = copy.deepcopy(board)
        state.play(move)
        if state.is_terminal() == player:
            return True
    return False


def fixed(depth=2):
    """A deterministic Clawed that searches exactly `depth` plies."""
    return Clawed(time_limit=None, max_depth=depth)


class ClawedTests(unittest.TestCase):
    def test_registered_as_a_boop_bot(self):
        self.assertIsInstance(Clawed(), BoopBot)
        self.assertIs(BOTS["Clawed"], Clawed)

    def test_internal_rules_match_rules_py(self):
        # Play 200 random games, and after every step compare Clawed's
        # version of the board with the real one.
        rng = random.Random(0)
        for _ in range(200):
            board = Board([[0] * 6 for _ in range(6)], [[8, 0], [8, 0]])
            player = 1
            for _ in range(150):
                cells, hands = _flatten(board)
                try:
                    legals = board.get_legals(player)
                except IllegalMove:
                    self.assertEqual(_legal_moves(cells, hands, player), [])
                    break
                self.assertEqual(sorted(legals), sorted(_legal_moves(cells, hands, player)))
                move = rng.choice(legals)
                board.play(move)
                cells, hands = _play(cells, hands, move)
                self.assertEqual((cells, hands), _flatten(board))
                self.assertEqual(_winner(cells), board.is_terminal())
                if board.is_terminal():
                    break
                grows = own_grows(board, player)
                self.assertEqual(grows, _own_grows(cells, hands, player))
                if grows:
                    grow = rng.choice(grows)
                    board.grow(grow)
                    self.assertEqual(_grow(cells, hands, grow), _flatten(board))
                player = 3 - player

    def test_opening_is_legal_deterministic_and_does_not_mutate_inputs(self):
        for player in (1, 2):
            with self.subTest(player=player):
                board = position()
                moves = board.get_legals(player)
                before = copy.deepcopy((board.board, board.hands, moves))
                move = fixed().give_move(moves, board, player)
                self.assertIn(move, moves)
                self.assertEqual(move, fixed().give_move(moves, board, player))
                self.assertEqual((board.board, board.hands, moves), before)

    def test_timed_search_returns_a_legal_move(self):
        board = position()
        moves = board.get_legals(1)
        self.assertIn(Clawed(time_limit=0.05).give_move(moves, board, 1), moves)

    def test_takes_immediate_cat_line_win_for_both_colors(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                hands = [[8, 0], [8, 0]]
                hands[player - 1] = [4, 1]
                board = position([(2, 0, sign), (2, 1, 2 * sign), (2, 2, 2 * sign)], hands)
                move = fixed().give_move(board.get_legals(player), board, player)
                board.play(move)
                self.assertEqual(board.is_terminal(), player)

    def test_blocks_an_opponent_win_for_both_colors(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                opponent = 3 - player
                hands = [[7, 1], [7, 1]]
                hands[opponent - 1] = [4, 1]
                board = position([(2, 0, -sign), (2, 1, -2 * sign), (2, 2, -2 * sign)], hands)
                self.assertTrue(can_win_next(board, opponent))
                move = fixed().give_move(board.get_legals(player), board, player)
                board.play(move)
                self.assertFalse(can_win_next(board, opponent))

    def test_wins_by_deploying_eighth_cat(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                hands = [[8, 0], [8, 0]]
                hands[player - 1] = [0, 1]
                coords = [(0, 0), (0, 2), (0, 4), (2, 0), (2, 2), (2, 4), (4, 1)]
                board = position([(r, c, 2 * sign) for r, c in coords], hands)
                move = fixed().give_move(board.get_legals(player), board, player)
                board.play(move)
                self.assertEqual(board.is_terminal(), player)

    def test_growth_keeps_the_kitten_blocking_an_opponent_cat_line(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                hands = [[4, 1], [4, 1]]
                hands[player - 1] = [4, 0]
                board = position(
                    [(2, col, sign) for col in range(4)] +
                    [(3, 3, -2 * sign), (4, 3, -2 * sign), (5, 3, -sign)],
                    hands,
                )
                grows = own_grows(board, player)
                self.assertEqual(len(grows), 2)
                before = copy.deepcopy((board.board, board.hands, grows))
                grow = fixed().give_grow(grows, board, player)
                self.assertEqual(grow, ("grow", (12, 13, 14)))
                self.assertEqual((board.board, board.hands, grows), before)
                board.grow(grow)
                self.assertFalse(can_win_next(board, 3 - player))

    def test_retires_a_kitten_when_the_last_piece_leaves_hand(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                hands = [[8, 0], [8, 0]]
                hands[player - 1] = [1, 0]
                coords = [(0, 0), (0, 2), (0, 4), (2, 0), (2, 2), (2, 4), (4, 1)]
                board = position([(r, c, sign) for r, c in coords], hands)
                move = fixed().give_move(board.get_legals(player), board, player)
                board.play(move)
                grows = own_grows(board, player)
                self.assertTrue(grows)
                before = copy.deepcopy((board.board, board.hands, grows))
                grow = fixed().give_grow(grows, board, player)
                self.assertIn(grow, grows)
                self.assertEqual((board.board, board.hands, grows), before)
                if grow[0] == "remove":
                    board.grow(grow)
                    self.assertEqual(board.hands[player - 1], [0, 1])

    def test_mixed_line_of_kittens_and_cats_graduates(self):
        for player, sign in ((1, -1), (2, 1)):
            with self.subTest(player=player):
                board = position([(2, 1, sign), (2, 2, 2 * sign), (2, 3, sign)],
                                 [[5, 0], [5, 0]])
                grows = own_grows(board, player)
                self.assertEqual(grows, [("grow", (13, 14, 15))])
                self.assertEqual(_own_grows(*_flatten(board), player), grows)
                cells, hands = _grow(*_flatten(board), grows[0])
                board.grow(grows[0])
                self.assertEqual((cells, hands), _flatten(board))
                self.assertEqual(board.hands[player - 1], [5, 3])

    def test_empty_hand_scores_as_a_draw(self):
        board = position([(0, 0, -1)], [[0, 0], [7, 0]])
        self.assertEqual(fixed()._negamax(*_flatten(board), 1, 2, -10**9, 10**9), 0)

    def test_constructor_validates_arguments(self):
        for kwargs in ({"time_limit": 0}, {"time_limit": -1}, {"time_limit": "1"},
                       {"time_limit": True}, {"max_depth": 0}, {"max_depth": 1.5},
                       {"max_depth": True}):
            with self.subTest(**kwargs):
                with self.assertRaises(ValueError):
                    Clawed(**kwargs)

    def test_empty_choices_have_clear_errors(self):
        board = position()
        with self.assertRaises(ValueError):
            Clawed().give_move([], board, 1)
        with self.assertRaises(ValueError):
            Clawed().give_grow([], board, 1)


if __name__ == "__main__":
    unittest.main()
